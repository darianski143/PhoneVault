import os
import mariadb
from dotenv import load_dotenv

load_dotenv()

def get_connection():
    """
    Establishes a connection to the MariaDB database
    using environment variables for configuration.
    """
    conn = mariadb.connect(
        host = os.getenv("DB_HOST", "127.0.0.1"),
        port = int(os.getenv("DB_PORT", "3306")),
        user = os.getenv("DB_USER", "root"),
        password = os.getenv("DB_PASSWORD", "7355608"),
        database = os.getenv("DB_NAME", "phonevault")
    )
    return conn

def run_select(sql, params=()):
    """
    Executes a SELECT query and returns the fetched rows.
    """
    conn = get_connection()
    cur = conn.cursor()
    cur.execute(sql, params)
    rows = cur.fetchall()
    cur.close()
    conn.close()
    return rows

def run_execute(sql, params=()):
    """
    Executes an INSERT, UPDATE, or DELETE query
    and returns the number of affected rows.
    """
    conn = get_connection()
    cur = conn.cursor()
    cur.execute(sql, params)
    conn.commit()
    affected = cur.rowcount
    cur.close()
    conn.close()
    return affected