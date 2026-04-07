from pathlib import Path

from app.db import get_connection


def _execute_simple_sql_file(cur, file_path: Path):
    sql_text = file_path.read_text(encoding="utf-8")
    statements = [s.strip() for s in sql_text.split(";") if s.strip()]

    for stmt in statements:
        cur.execute(stmt)


def _execute_block_sql_file(cur, file_path: Path, separator: str):
    if not file_path.exists():
        return False

    sql_text = file_path.read_text(encoding="utf-8")
    blocks = [block.strip() for block in sql_text.split(separator) if block.strip()]

    for block in blocks:
        upper_block = block.upper()
        create_proc_pos = upper_block.find("CREATE PROCEDURE")
        create_trigger_pos = upper_block.find("CREATE TRIGGER")

        create_pos_candidates = [pos for pos in (create_proc_pos, create_trigger_pos) if pos != -1]

        if create_pos_candidates:
            create_pos = min(create_pos_candidates)
            prefix = block[:create_pos].strip()
            ddl_statement = block[create_pos:].strip()

            if prefix:
                prefix_statements = [s.strip() for s in prefix.split(";") if s.strip()]
                for stmt in prefix_statements:
                    cur.execute(stmt)

            if ddl_statement:
                cur.execute(ddl_statement)
        else:
            cur.execute(block)

    return True


def create_tables():
    project_root = Path(__file__).resolve().parent.parent
    schema_path = project_root / "sql" / "schema.sql"
    triggers_path = project_root / "sql" / "triggers.sql"
    procedures_path = project_root / "sql" / "procedures.sql"



    conn = get_connection()
    cur = conn.cursor()

    try:
        _execute_simple_sql_file(cur, schema_path)
        print("OK: Tables created successfully.")

        if _execute_block_sql_file(cur, procedures_path, "-- PROC_END"):
            print("OK: Procedures created successfully.")

        if _execute_block_sql_file(cur, triggers_path, "-- TRIGGER_END"):
            print("OK: Triggers created successfully.")

        conn.commit()
    except Exception as e:
        conn.rollback()
        print("Error creating tables/triggers/procedures:", e)
        raise
    finally:
        cur.close()
        conn.close()


if __name__ == "__main__":
    create_tables()