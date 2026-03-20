from pathlib import Path
from app.db import get_connection

def create_tables():
    project_root = Path(__file__).resolve().parent.parent
    schema_path = project_root / "sql" / "schema.sql"
    sql_text = schema_path.read_text(encoding="utf-8")

    statements = [s.strip() for s in sql_text.split(";") if s.strip()]

    conn = get_connection()
    cur = conn.cursor()

    try:
        for stmt in statements:
            cur.execute(stmt)
        conn.commit()
        print("OK: Tables created successfully.")
    except Exception as e:
        conn.rollback()
        print(f"Error creating tables: ", e)
        raise
    finally:
        cur.close()
        conn.close()