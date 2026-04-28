import csv
from pathlib import Path

from app.db import get_connection

ALLOWED_TABLES = {
    "brands",
    "stores",
    "customers",
    "phones",
    "specifications",
    "sales",
    "customer_log",
    "sale_orders",
    "sale_order_items",
}

AUTO_SKIP_COLS = {"id", "created_at"}

def get_table_columns(cur, table: str) -> set[str]:
    cur.execute(f"DESCRIBE {table};")
    return {row[0] for row in cur.fetchall()}

def import_table_from_csv(table: str, csv_path: Path, truncate_first: bool = False):
    table = table.strip()

    if table not in ALLOWED_TABLES:
        raise ValueError(f"Tabel invalid. Alege din {sorted(ALLOWED_TABLES)}")

    if not csv_path.exists():
        raise FileNotFoundError(f"Nu exista CSV: {csv_path}")

    conn = get_connection()
    cur = conn.cursor()

    inserted = 0
    skipped = 0

    try:
        table_cols = get_table_columns(cur, table)

        with csv_path.open("r", encoding="utf-8", newline="") as f:
            reader = csv.DictReader(f)

            if not reader.fieldnames:
                raise ValueError("CSV invalid: lipseste header-ul.")

            cols = []

            for c in reader.fieldnames:
                c = c.strip()

                if c in AUTO_SKIP_COLS:
                    continue

                if c in table_cols:
                    cols.append(c)

            if not cols:
                raise ValueError("Nu am coloane importabile. Header-ul nu corespunde tabelului.")

            placeholders = ", ".join(["%s"] * len(cols))
            col_list = ", ".join(cols)
            sql = f"INSERT INTO {table} ({col_list}) VALUES ({placeholders});"

            conn.begin()

            if truncate_first:
                cur.execute("SET FOREIGN_KEY_CHECKS=0;")
                cur.execute(f"TRUNCATE TABLE {table};")
                cur.execute("SET FOREIGN_KEY_CHECKS=1;")

            for i, row in enumerate(reader, start=2):
                values = []
                empty_row = True

                for c in cols:
                    val = row.get(c)

                    if val is None:
                        val = ""

                    val = val.strip()

                    if val != "":
                        empty_row = False

                    values.append(val if val != "" else None)

                if empty_row:
                    skipped += 1
                    continue

                cur.execute(sql, tuple(values))
                inserted += 1

            conn.commit()
            print(f"IMPORT OK -> table={table} inserted={inserted} skipped={skipped}")

    except Exception as e:
        conn.rollback()
        print("IMPORT FAIL -> rollback. Eroare:", e)
        raise

    finally:
        cur.close()
        conn.close()

if __name__ == "__main__":
    project_root = Path(__file__).resolve().parent.parent

    table = input(f"Tabel ({', '.join(sorted(ALLOWED_TABLES))}): ").strip()
    csv_path_input = input("CSV path (ex. exports/phones.csv): ").strip()
    truncate = input("TRUNCATE inainte? (y/n): ").strip().lower() == "y"

    csv_path = Path(csv_path_input)

    if not csv_path.is_absolute():
        csv_path = project_root / csv_path

    import_table_from_csv(table, csv_path, truncate)