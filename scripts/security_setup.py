import os
import mariadb
import bcrypt
from cryptography.fernet import Fernet


DB_HOST = os.getenv("PHONEVAULT_DB_HOST", "127.0.0.1")
DB_PORT = int(os.getenv("PHONEVAULT_DB_PORT", "3308"))
DB_NAME = os.getenv("PHONEVAULT_DB_NAME", "phonevault")
ROOT_USER = os.getenv("PHONEVAULT_DB_USER", "root")
ROOT_PASS = os.getenv("PHONEVAULT_DB_PASS")

if not ROOT_PASS:
    raise ValueError("PHONEVAULT_DB_PASS is not set in environment variables.")


FERNET_KEY = os.getenv("PHONEVAULT_FERNET_KEY")
if not FERNET_KEY:
    print("[WARNING] PHONEVAULT_FERNET_KEY is not set. Using a local demo key for laboratory execution.")
    FERNET_KEY = "MDEyMzQ1Njc4OWFiY2RlZjAxMjM0NTY3ODlhYmNkZWY="

fernet = Fernet(FERNET_KEY.encode())


def get_root_connection():
    return mariadb.connect(
        host=DB_HOST,
        port=DB_PORT,
        user=ROOT_USER,
        password=ROOT_PASS,
        database=DB_NAME
    )


def hash_password(plain: str) -> str:
    return bcrypt.hashpw(
        plain.encode(),
        bcrypt.gensalt()
    ).decode()


def encrypt_value(value: str) -> str:
    return fernet.encrypt(value.encode()).decode()


def create_db_users():
    conn = get_root_connection()
    cur = conn.cursor()

    db_users = [
        ("manager", "manager123", "ALL PRIVILEGES"),
        ("insert_user", "insert123", "SELECT, INSERT"),
        ("update_user", "update123", "SELECT, INSERT, UPDATE"),
        ("delete_user", "delete123", "SELECT, DELETE")
    ]

    for username, password, privileges in db_users:
        try:
            cur.execute(f"DROP USER IF EXISTS '{username}'@'%'")
            cur.execute(f"CREATE USER '{username}'@'%' IDENTIFIED BY '{password}'")
            cur.execute(f"GRANT {privileges} ON {DB_NAME}.* TO '{username}'@'%'")
            print(f"[OK] Created DB user: {username}")
        except Exception as e:
            print(f"[ERROR] {username}: {e}")

    cur.execute("FLUSH PRIVILEGES")
    conn.commit()
    conn.close()


def encrypt_customer_passwords():
    conn = get_root_connection()
    cur = conn.cursor()

    cur.execute("SELECT id, password_hash FROM customers")
    rows = cur.fetchall()

    for customer_id, password_value in rows:
        if password_value and not str(password_value).startswith("$2b$"):
            hashed = hash_password(str(password_value))
            cur.execute(
                "UPDATE customers SET password_hash=? WHERE id=?",
                (hashed, customer_id)
            )
            print(f"[UPDATED] Customer ID {customer_id} password encrypted")

    conn.commit()
    conn.close()


def encrypt_customer_phone_numbers():
    conn = get_root_connection()
    cur = conn.cursor()

    cur.execute("SELECT id, phone_number FROM customers")
    rows = cur.fetchall()

    for customer_id, phone_number in rows:
        if phone_number and not str(phone_number).startswith("gAAAAA"):
            encrypted_phone = encrypt_value(str(phone_number))
            cur.execute(
                "UPDATE customers SET phone_number=? WHERE id=?",
                (encrypted_phone, customer_id)
            )
            print(f"[UPDATED] Customer ID {customer_id} phone number encrypted")

    conn.commit()
    conn.close()


def main():
    print("\n=== CREATE DB USERS + GRANT ===")
    create_db_users()

    print("\n=== ENCRYPT CUSTOMER PASSWORDS ===")
    encrypt_customer_passwords()

    print("\n=== ENCRYPT CUSTOMER PHONE NUMBERS ===")
    encrypt_customer_phone_numbers()

    print("\n=== SECURITY SETUP COMPLETED ===")


if __name__ == "__main__":
    main()