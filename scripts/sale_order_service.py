import json
from app.db import get_connection, run_select


def create_sale_order():
    store = run_select("SELECT id FROM stores LIMIT 1;")
    customer = run_select("SELECT id FROM customers LIMIT 1;")
    phones = run_select("SELECT model_name, stock FROM phones WHERE stock > 0 LIMIT 2;")

    if not store or not customer or not phones:
        print("Nu exista suficiente date pentru test.")
        return

    store_id = store[0][0]
    customer_id = customer[0][0]

    items = []
    for model_name, stock in phones:
        quantity = 1 if stock >= 1 else 0
        if quantity > 0:
            items.append({"model_name": model_name, "quantity": quantity})

    if not items:
        print("Nu exista telefoane cu stoc disponibil pentru test.")
        return

    items_json = json.dumps(items)

    conn = get_connection()
    cur = conn.cursor()

    try:
        cur.execute(
            "CALL create_sale_order(%s, %s, CURDATE(), %s)",
            (store_id, customer_id, items_json)
        )

        result = cur.fetchone()
        sale_order_id = result[0] if result else None

        while cur.nextset():
            pass

        conn.commit()

        print(f"Sale order creat cu ID: {sale_order_id}")

        verification_query = """
        SELECT
            so.id AS sale_order_id,
            so.sale_date,
            c.first_name,
            c.last_name,
            s.store_name,
            p.model_name,
            soi.quantity,
            soi.unit_price,
            soi.line_total
        FROM sale_orders so
        JOIN customers c ON c.id = so.customer_id
        JOIN stores s ON s.id = so.store_id
        JOIN sale_order_items soi ON soi.sale_order_id = so.id
        JOIN phones p ON p.id = soi.phone_id
        WHERE so.id = %s
        ORDER BY p.model_name;
        """

        cur.execute(verification_query, (sale_order_id,))
        rows = cur.fetchall()

        print("\nVerificare inserare:")
        for row in rows:
            print(row)

    except Exception as e:
        conn.rollback()
        print("Eroare la apelarea procedurii:", e)
    finally:
        cur.close()
        conn.close()


if __name__ == "__main__":
    create_sale_order()