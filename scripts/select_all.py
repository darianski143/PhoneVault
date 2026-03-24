import json
from pathlib import Path
from app.db import run_select

sql = """
SELECT
    p.id,
    b.brand_name,
    p.model_name,
    COALESCE(SUM(s.quantity_sold), 0) AS total_units_sold
FROM phones p
JOIN brands b ON b.id = p.brand_id
LEFT JOIN sales s ON s.phone_id = p.id
GROUP BY p.id, b.brand_name, p.model_name
ORDER BY total_units_sold DESC, b.brand_name ASC, p.model_name ASC;
"""

rows = run_select(sql)

data = []
for r in rows:
    data.append({
        "id": r[0],
        "brand_name": r[1],
        "model_name": r[2],
        "total_units_sold": int(r[3]) if r[3] is not None else 0
    })

out_path = Path("outputs") / "phones_sales_summary.json"
out_path.parent.mkdir(exist_ok=True)

out_path.write_text(
    json.dumps(data, indent=2, ensure_ascii=False),
    encoding="utf-8"
)

print(f"JSON salvat: {out_path}")