import json
from pathlib import Path
from app.db import run_select

sql = """
SELECT
    b.brand_name,
    COUNT(p.id) AS phones_count,
    AVG(p.price) AS avg_price
FROM brands b
LEFT JOIN phones p ON p.brand_id = b.id
GROUP BY b.id, b.brand_name
ORDER BY phones_count DESC, avg_price DESC;
"""

rows = run_select(sql)

data = []
for r in rows:
    data.append({
        "brand_name": r[0],
        "phones_count": int(r[1]) if r[1] is not None else 0,
        "avg_price": float(r[2]) if r[2] is not None else 0.0
    })

out_path = Path("outputs") / "brands_phone_stats.json"
out_path.parent.mkdir(exist_ok=True)

out_path.write_text(
    json.dumps(data, indent=2, ensure_ascii=False),
    encoding="utf-8"
)

print(f"JSON salvat: {out_path}")