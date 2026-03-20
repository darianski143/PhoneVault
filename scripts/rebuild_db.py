from app.db import run_execute
from scripts.create_tables import create_tables

print("Stergem tabelele existente (daca exista)")

run_execute("DROP TABLE IF EXISTS customer_log;")
run_execute("DROP TABLE IF EXISTS sales;")
run_execute("DROP TABLE IF EXISTS specifications;")
run_execute("DROP TABLE IF EXISTS phones;")
run_execute("DROP TABLE IF EXISTS customers;")
run_execute("DROP TABLE IF EXISTS stores;")
run_execute("DROP TABLE IF EXISTS brands;")

print("Creez tabelele din schema sql...")
create_tables()

print("Rebuild gata!")