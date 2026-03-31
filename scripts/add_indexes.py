import time
from app.db import run_execute


def apply_indexes():
    print("=== APLICARE INDEXURI PHONEVAULT ===")

    index_queries = [
        "CREATE INDEX IF NOT EXISTS idx_brands_brand_name ON brands(brand_name);",
        "CREATE INDEX IF NOT EXISTS idx_phones_model_name ON phones(model_name);",
        "CREATE INDEX IF NOT EXISTS idx_phones_brand_id ON phones(brand_id);",
        "CREATE INDEX IF NOT EXISTS idx_sales_customer_id ON sales(customer_id);",
        "CREATE INDEX IF NOT EXISTS idx_sales_phone_id ON sales(phone_id);",
        "CREATE INDEX IF NOT EXISTS idx_sales_store_id ON sales(store_id);",
    ]

    for query in index_queries:
        print(f"Rulam: {query}")
        try:
            start_time = time.time()
            run_execute(query)
            end_time = time.time()
            duration = (end_time - start_time) * 1000
            print(f"Succes. Durata creare index: {duration:.2f} ms\n")
        except Exception as e:
            print(f"Eroare la crearea indexului: {e}\n")

    print("Indexurile au fost aplicate cu succes.")


if __name__ == "__main__":
    apply_indexes()