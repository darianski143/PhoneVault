from pathlib import Path
from app.db import get_connection


def create_tables():
    project_root = Path(__file__).resolve().parent.parent
    schema_path = project_root / "sql" / "schema.sql"
    triggers_path = project_root / "sql" / "triggers.sql"

    schema_text = schema_path.read_text(encoding="utf-8")
    statements = [s.strip() for s in schema_text.split(";") if s.strip()]

    conn = get_connection()
    cur = conn.cursor()

    try:
        for stmt in statements:
            cur.execute(stmt)
        print("OK: Tables created successfully.")

        if triggers_path.exists():
            triggers_text = triggers_path.read_text(encoding="utf-8")
            trigger_blocks = [
                block.strip()
                for block in triggers_text.split("-- TRIGGER_END")
                if block.strip()
            ]

            for block in trigger_blocks:
                cur.execute(block)
            print("OK: Triggers created successfully.")

        conn.commit()
    except Exception as e:
        conn.rollback()
        print("Error creating tables/triggers:", e)
        raise
    finally:
        cur.close()
        conn.close()


if __name__ == "__main__":
    create_tables()