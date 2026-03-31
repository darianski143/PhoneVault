from app.db import run_execute, run_select

print("=== TEST TRIGGERS PHONEVAULT ===")

phone = run_select(
    "SELECT id, stock, price FROM phones WHERE stock > 0 LIMIT 1;"
)[0]
phone_id = phone[0]
stock = int(phone[1])
price = float(phone[2])

store_id = run_select("SELECT id FROM stores LIMIT 1;")[0][0]
customer_id = run_select("SELECT id FROM customers LIMIT 1;")[0][0]

valid_quantity = 1
valid_total_amount = round(price * valid_quantity, 2)
invalid_stock_quantity = stock + 1
invalid_stock_total_amount = round(price * invalid_stock_quantity, 2)

print("\n1. Test vanzare valida (quantity_sold = 1)")
try:
    run_execute(
        """
        INSERT INTO sales (phone_id, store_id, customer_id, sale_date, quantity_sold, total_amount)
        VALUES (%s, %s, %s, CURDATE(), %s, %s);
        """,
        (phone_id, store_id, customer_id, valid_quantity, valid_total_amount)
    )
    print("OK: Inserarea valida a reusit.")
except Exception as e:
    print("Eroare neasteptata:", e)

print("\n2. Test vanzare invalida (quantity_sold = -2)")
try:
    run_execute(
        """
        INSERT INTO sales (phone_id, store_id, customer_id, sale_date, quantity_sold, total_amount)
        VALUES (%s, %s, %s, CURDATE(), %s, %s);
        """,
        (phone_id, store_id, customer_id, -2, 1000.00)
    )
    print("EROARE: Inserarea invalida a trecut, triggerul nu functioneaza.")
except Exception as e:
    print("OK: Inserarea invalida a fost blocata de trigger.")
    print("Mesaj DB:", e)

print("\n3. Test vanzare cu stoc insuficient")
try:
    run_execute(
        """
        INSERT INTO sales (phone_id, store_id, customer_id, sale_date, quantity_sold, total_amount)
        VALUES (%s, %s, %s, CURDATE(), %s, %s);
        """,
        (phone_id, store_id, customer_id, invalid_stock_quantity, invalid_stock_total_amount)
    )
    print("EROARE: Inserarea cu stoc insuficient a trecut.")
except Exception as e:
    print("OK: Inserarea cu stoc insuficient a fost blocata.")
    print("Mesaj DB:", e)

print("\n4. Test trigger AFTER UPDATE pe customers")
try:
    run_execute(
        "UPDATE customers SET first_name = %s WHERE id = %s;",
        ("ClientTest", customer_id)
    )
    print("OK: Clientul a fost actualizat.")
except Exception as e:
    print("Eroare la update:", e)

print("\n5. Verificare customer_log")
logs = run_select("SELECT action FROM customer_log ORDER BY id DESC LIMIT 5;")
for log in logs:
    print("-", log[0])

print("\n=== TEST FINALIZAT ===")