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

def export_table(table: str):
    table = table.strip()

    if table not in ALLOWED_TABLES:
        raise ValueError(f"Table invalid. Alege din {sorted(ALLOWED_TABLES)}")

    project_root = Path(__file__).resolve().parent.parent
    out_dir = project_root / "exports"
    out_dir.mkdir(parents=True, exist_ok=True)

    out_path = out_dir / f"{table}.csv"

    conn = get_connection()
    cur = conn.cursor()

    try:
        cur.execute(f"SELECT * FROM {table};")
        rows = cur.fetchall()
        cols = [d[0] for d in cur.description]

        with out_path.open("w", encoding="utf-8", newline="") as f:
            writer = csv.writer(f)
            writer.writerow(cols)
            writer.writerows(rows)

        print(f"EXPORT OK -> {out_path} rows={len(rows)}")

    finally:
        cur.close()
        conn.close()

if __name__ == "__main__":
    table = input(f"Tabel ({', '.join(sorted(ALLOWED_TABLES))}): ").strip()
    export_table(table)