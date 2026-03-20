from scripts.create_tables import create_tables

def init_db():
    print("Se creeaza tabelele...")
    create_tables()
    print("schema.sql aplicata")

if __name__ == "__main__":
    init_db()