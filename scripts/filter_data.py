import json
from pathlib import Path
from app.db import run_select

MIN_UNITS = 5

sql = """
SELECT
    b.brand_name,
    p.model_name,
    COALESCE(SUM(s.quantity_sold), 0) AS total_units_sold
FROM phones p
JOIN brands b ON b.id = p.brand_id
LEFT JOIN sales s ON s.phone_id = p.id
GROUP BY p.id, b.brand_name, p.model_name
HAVING COALESCE(SUM(s.quantity_sold), 0) >= %s
ORDER BY total_units_sold DESC, b.brand_name ASC, p.model_name ASC;
"""

rows = run_select(sql, (MIN_UNITS,))

data = []
for r in rows:
    data.append({
        "brand_name": r[0],
        "model_name": r[1],
        "total_units_sold": int(r[2]) if r[2] is not None else 0
    })

out_path = Path("outputs") / "phones_sales_filtered.json"
out_path.parent.mkdir(exist_ok=True)

out_path.write_text(
    json.dumps({
        "min_units": MIN_UNITS,
        "results": data
    }, indent=2, ensure_ascii=False),
    encoding="utf-8"
)

print(f"JSON salvat: {out_path}")