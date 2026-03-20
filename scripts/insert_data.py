import random
from faker import Faker
from app.db import run_execute, run_select

fake = Faker()

NUM_BRANDS = 8
NUM_STORES = 5
NUM_CUSTOMERS = 80
NUM_PHONES = 120
NUM_SALES = 400
NUM_LOGS = 150

print("Pornim generarea datelor pentru PhoneVault...")

# -------------------------
# 1. BRANDS
# -------------------------
print("Inseram branduri...")

brand_names = [
    "Apple",
    "Samsung",
    "Xiaomi",
    "Huawei",
    "Nokia",
    "Motorola",
    "OnePlus",
    "Google"
]

for brand_name in brand_names[:NUM_BRANDS]:
    run_execute(
        "INSERT INTO brands (brand_name, country) VALUES (%s, %s);",
        (brand_name, fake.country())
    )

# -------------------------
# 2. STORES
# -------------------------
print("Inseram magazine...")

for i in range(NUM_STORES):
    store_name = f"PhoneVault Store {i + 1}"
    city = fake.city()

    run_execute(
        "INSERT INTO stores (store_name, city) VALUES (%s, %s);",
        (store_name, city)
    )

# -------------------------
# 3. CUSTOMERS
# -------------------------
print("Inseram clienti...")

run_execute(
    "INSERT INTO customers (first_name, last_name, email, phone_number) VALUES (%s, %s, %s, %s);",
    ("Admin", "Client", "admin@phonevault.ro", "0700000000")
)

for i in range(NUM_CUSTOMERS):
    first_name = fake.first_name()
    last_name = fake.last_name()
    email = f"{fake.user_name()}{random.randint(1, 9999)}@mail.com"
    phone = f"07{random.randint(10000000, 99999999)}"

    run_execute(
        "INSERT INTO customers (first_name, last_name, email, phone_number) VALUES (%s, %s, %s, %s);",
        (first_name, last_name, email, phone)
    )

# -------------------------
# 4. PHONES
# -------------------------
print("Inseram telefoane...")

brands = run_select("SELECT id FROM brands;")
brand_ids = [row[0] for row in brands]

model_prefixes = [
    "Galaxy", "iPhone", "Redmi", "P", "Moto", "Nord", "Pixel", "Lumia"
]

for i in range(NUM_PHONES):
    brand_id = random.choice(brand_ids)
    model_name = f"{random.choice(model_prefixes)} {random.randint(1, 30)}"
    launch_year = random.randint(2019, 2025)
    price = round(random.uniform(800, 7000), 2)
    stock = random.randint(5, 50)

    run_execute(
        """
        INSERT INTO phones (brand_id, model_name, launch_year, stock, price)
        VALUES (%s, %s, %s, %s, %s);
        """,
        (brand_id, model_name, launch_year, stock, price)
    )

# -------------------------
# 5. SPECIFICATIONS
# -------------------------
print("Inseram specificatii...")

phones = run_select("SELECT id FROM phones;")
phone_ids = [row[0] for row in phones]

processors = [
    "Snapdragon 8 Gen 2",
    "Snapdragon 7 Gen 1",
    "Apple A16 Bionic",
    "Apple A17 Pro",
    "Dimensity 9200",
    "Exynos 2200"
]

for phone_id in phone_ids:
    os_name = random.choice(["Android", "iOS"])
    processor = random.choice(processors)
    ram_gb = random.choice([4, 6, 8, 12, 16])
    storage_gb = random.choice([64, 128, 256, 512])
    camera_mp = random.choice([12, 48, 50, 64, 108])
    battery_mah = random.randint(3000, 6000)
    screen_size = round(random.uniform(5.8, 6.9), 2)

    run_execute(
        """
        INSERT INTO specifications
        (phone_id, os, processor, ram_gb, storage_gb, camera_mp, battery_mah, screen_size)
        VALUES (%s, %s, %s, %s, %s, %s, %s, %s);
        """,
        (phone_id, os_name, processor, ram_gb, storage_gb, camera_mp, battery_mah, screen_size)
    )

# -------------------------
# 6. SALES
# -------------------------
print("Inseram vanzari fara sa depasim stocul...")

stores = run_select("SELECT id FROM stores;")
customers = run_select("SELECT id FROM customers;")
phones_data = run_select("SELECT id, price, stock FROM phones;")

store_ids = [row[0] for row in stores]
customer_ids = [row[0] for row in customers]

stock_tracker = {}
price_tracker = {}

for phone_id, price, stock in phones_data:
    stock_tracker[phone_id] = stock
    price_tracker[phone_id] = float(price)

for _ in range(NUM_SALES):
    valid_phone_ids = [pid for pid, stk in stock_tracker.items() if stk > 0]

    if not valid_phone_ids:
        break

    phone_id = random.choice(valid_phone_ids)
    current_stock = stock_tracker[phone_id]

    quantity_sold = random.randint(1, min(3, current_stock))
    stock_tracker[phone_id] -= quantity_sold

    store_id = random.choice(store_ids)
    customer_id = random.choice(customer_ids)
    sale_date = fake.date_between(start_date="-2y", end_date="today")
    total_amount = round(price_tracker[phone_id] * quantity_sold, 2)

    run_execute(
        """
        INSERT INTO sales (phone_id, store_id, customer_id, sale_date, quantity_sold, total_amount)
        VALUES (%s, %s, %s, %s, %s, %s);
        """,
        (phone_id, store_id, customer_id, sale_date, quantity_sold, total_amount)
    )

# actualizam stocul ramas in tabelul phones
for phone_id, remaining_stock in stock_tracker.items():
    run_execute(
        "UPDATE phones SET stock = %s WHERE id = %s;",
        (remaining_stock, phone_id)
    )

# -------------------------
# 7. CUSTOMER LOG
# -------------------------
print("Inseram loguri clienti...")

actions = [
    "LOGIN",
    "LOGOUT",
    "VIEW_PHONE",
    "BUY_PHONE",
    "UPDATE_PROFILE"
]

for _ in range(NUM_LOGS):
    customer_id = random.choice(customer_ids)
    action = random.choice(actions)

    run_execute(
        "INSERT INTO customer_log (customer_id, action) VALUES (%s, %s);",
        (customer_id, action)
    )

print("Date generate corect pentru PhoneVault.")