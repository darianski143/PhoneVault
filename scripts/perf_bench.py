import time
import statistics
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np

from app.db import run_select, run_execute

RUNS = 50
OUTPUT_DIR = Path(__file__).parent / "outputs"
OUTPUT_DIR.mkdir(exist_ok=True)

REPORT_FILE = OUTPUT_DIR / "performance_report.txt"
CHART_FILE = OUTPUT_DIR / "performance_chart.png"

TEST_QUERIES = [
    {
        "name": "Brands by brand_name",
        "sql": "SELECT * FROM brands WHERE brand_name = %s;",
        "params": ("Samsung",),
    },
    {
        "name": "Phones by model_name",
        "sql": "SELECT * FROM phones WHERE model_name = %s;",
        "params": ("Galaxy S23",),
    },
    {
        "name": "Sales by customer_id",
        "sql": "SELECT * FROM sales WHERE customer_id = %s;",
        "params": (1,),
    },
    {
        "name": "Sales by phone_id",
        "sql": "SELECT * FROM sales WHERE phone_id = %s;",
        "params": (1,),
    },
]

INDEX_SQL = [
    "CREATE INDEX IF NOT EXISTS idx_brands_brand_name ON brands(brand_name);",
    "CREATE INDEX IF NOT EXISTS idx_phones_model_name ON phones(model_name);",
    "CREATE INDEX IF NOT EXISTS idx_phones_brand_id ON phones(brand_id);",
    "CREATE INDEX IF NOT EXISTS idx_sales_customer_id ON sales(customer_id);",
    "CREATE INDEX IF NOT EXISTS idx_sales_phone_id ON sales(phone_id);",
    "CREATE INDEX IF NOT EXISTS idx_sales_store_id ON sales(store_id);",
]


def benchmark_query(sql: str, params, runs: int):
    times = []
    for _ in range(runs):
        start = time.perf_counter()
        run_select(sql, params)
        end = time.perf_counter()
        times.append((end - start) * 1000)
    return times



def summarize(times):
    avg = statistics.mean(times)
    mn = min(times)
    mx = max(times)
    std = statistics.stdev(times) if len(times) > 1 else 0.0
    return avg, mn, mx, std



def run_suite(label: str):
    results = {}
    for q in TEST_QUERIES:
        times = benchmark_query(q["sql"], q["params"], RUNS)
        avg, mn, mx, std = summarize(times)
        results[q["name"]] = {"avg": avg, "min": mn, "max": mx, "std": std}
        print(f"[{label}] {q['name']} -> avg {avg:.2f} ms")
    return results



def apply_indexes():
    for stmt in INDEX_SQL:
        run_execute(stmt)



def pct_change(before, after):
    if before <= 0:
        return 0.0
    return ((before - after) / before) * 100.0



def generate_chart(before_results, after_results):
    labels = list(before_results.keys())
    before_means = [before_results[name]["avg"] for name in labels]
    after_means = [after_results[name]["avg"] for name in labels]

    x = np.arange(len(labels))
    width = 0.35

    fig, ax = plt.subplots(figsize=(10, 6))

    rects1 = ax.bar(x - width / 2, before_means, width, label="Inainte de index")
    rects2 = ax.bar(x + width / 2, after_means, width, label="Dupa index")

    ax.set_ylabel("Timp mediu (ms)")
    ax.set_title("Impactul indexarii asupra performantei query-urilor - PhoneVault")
    ax.set_xticks(x)
    ax.set_xticklabels(labels)
    ax.legend()
    ax.grid(axis="y", linestyle="--", alpha=0.7)

    ax.bar_label(rects1, padding=3, fmt="%.2f")
    ax.bar_label(rects2, padding=3, fmt="%.2f")

    fig.tight_layout()
    plt.savefig(CHART_FILE)
    print(f"Grafic salvat in: {CHART_FILE}")
    plt.show()



def main():
    lines = []
    lines.append("=== ANALIZA PERFORMANTA SQL PHONEVAULT (BEFORE vs AFTER) ===\n")
    lines.append(f"Rulari per query: {RUNS}\n")

    print("Rulam testele initiale...")
    before = run_suite("BEFORE")

    print("\nAplicam indexurile...")
    apply_indexes()

    print("\nRulam testele dupa optimizare...")
    after = run_suite("AFTER")

    for name, m in before.items():
        lines.append(
            f"{name} (BEFORE) -> AVG: {m['avg']:.2f} ms | MIN: {m['min']:.2f} | MAX: {m['max']:.2f} | STD: {m['std']:.2f}"
        )

    lines.append("-" * 40)

    for name, m in after.items():
        improvement = pct_change(before[name]["avg"], m["avg"])
        lines.append(
            f"{name} (AFTER) -> AVG: {m['avg']:.2f} ms | Improvement: {improvement:.1f}%"
        )

    REPORT_FILE.write_text("\n".join(lines), encoding="utf-8")
    print(f"\nRaport text salvat in: {REPORT_FILE}")

    generate_chart(before, after)


if __name__ == "__main__":
    main()