import json
import csv
import matplotlib.pyplot as plt
from pathlib import Path
from decimal import Decimal
from datetime import datetime

from reportlab.platypus import (
    SimpleDocTemplate,
    Paragraph,
    Spacer,
    Image,
    Table,
    TableStyle
)
from reportlab.lib import colors
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.pagesizes import A4
from reportlab.lib.units import inch

from app.db import run_select


OUT_DIR = Path("outputs")
OUT_DIR.mkdir(exist_ok=True)

LOGO_PATH = Path("scripts/logo_fiir.jpg")


def normalize(value):
    if isinstance(value, Decimal):
        x = float(value)
        return int(x) if x.is_integer() else x
    return value


REPORTS = {
    "top_telefoane_vandute": {
        "title": "Top telefoane vandute",
        "description": (
            "Raportul analizeaza telefoanele vandute in aplicatia PhoneVault. "
            "Datele sunt preluate din tabelele sales, phones si brands, "
            "iar rezultatele sunt ordonate descrescator dupa cantitatea totala vanduta."
        ),
        "sql": """
            SELECT
                CONCAT('T', p.id) AS phone_code,
                CONCAT(b.brand_name, ' ', p.model_name) AS phone_name,
                SUM(s.quantity_sold) AS total_quantity,
                SUM(s.total_amount) AS total_revenue
            FROM sales s
            JOIN phones p ON p.id = s.phone_id
            JOIN brands b ON b.id = p.brand_id
            GROUP BY p.id, b.brand_name, p.model_name
            ORDER BY total_quantity DESC
        """,
        "columns": [
            ("phone_code", "Cod"),
            ("phone_name", "Telefon"),
            ("total_quantity", "Cantitate vanduta"),
            ("total_revenue", "Venit total")
        ],
        "chart": {
            "label_key": "phone_name",
            "value_key": "total_quantity",
            "x_label": "Cantitate vanduta",
            "y_label": "Telefon",
            "title": "Top telefoane vandute",
            "limit": 15,
            "type": "horizontal_bar"
        }
    },
    "venituri_pe_magazin": {
        "title": "Venituri pe magazin",
        "description": (
            "Raportul analizeaza performanta magazinelor PhoneVault. "
            "Datele sunt preluate din tabelele sales si stores, "
            "iar veniturile sunt calculate prin insumarea valorilor total_amount."
        ),
        "sql": """
            SELECT
                st.store_name,
                st.city,
                COUNT(s.id) AS total_orders,
                SUM(s.quantity_sold) AS total_items,
                SUM(s.total_amount) AS total_revenue
            FROM sales s
            JOIN stores st ON st.id = s.store_id
            GROUP BY st.id, st.store_name, st.city
            ORDER BY total_revenue DESC
        """,
        "columns": [
            ("store_name", "Magazin"),
            ("city", "Oras"),
            ("total_orders", "Comenzi"),
            ("total_items", "Produse vandute"),
            ("total_revenue", "Venit total")
        ],
        "chart": {
            "x_key": "store_name",
            "y_key": "total_revenue",
            "x_label": "Magazin",
            "y_label": "Venit total",
            "title": "Venituri pe magazin"
        }
    }
}


def get_paths(report_key):
    base_name = report_key
    return {
        "csv": OUT_DIR / f"{base_name}.csv",
        "json": OUT_DIR / f"{base_name}.json",
        "chart": OUT_DIR / f"{base_name}_chart.png",
        "pdf": OUT_DIR / f"{base_name}.pdf"
    }


def fetch_data(report_config):
    rows = run_select(report_config["sql"])
    keys = [column_key for column_key, _ in report_config["columns"]]

    data = []
    for row in rows:
        item = {}
        for index, key in enumerate(keys):
            item[key] = normalize(row[index])
        data.append(item)

    return data


def export_csv(data, report_config, csv_path):
    fieldnames = [column_key for column_key, _ in report_config["columns"]]

    with open(csv_path, "w", newline="", encoding="utf-8") as file:
        writer = csv.DictWriter(file, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(data)


def export_json(data, report_config, json_path):
    content = {
        "generated_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "report_title": report_config["title"],
        "data": data
    }

    with open(json_path, "w", encoding="utf-8") as file:
        json.dump(content, file, indent=2, ensure_ascii=False)


def generate_chart(data, report_config, chart_path):
    chart_config = report_config["chart"]
    limit = chart_config.get("limit")
    chart_data = data if limit is None else data[:limit]

    if chart_config.get("type") == "horizontal_bar":
        labels = [str(item[chart_config["label_key"]]) for item in chart_data]
        values = [item[chart_config["value_key"]] for item in chart_data]

        labels.reverse()
        values.reverse()

        fig_height = max(5, len(labels) * 0.35)
        fig, ax = plt.subplots(figsize=(10, fig_height))
        ax.barh(labels, values)
        ax.set_title(chart_config["title"])
        ax.set_xlabel(chart_config["x_label"])
        ax.set_ylabel(chart_config["y_label"])
        ax.tick_params(axis="y", labelsize=8)
        fig.tight_layout()
    else:
        names = [str(item[chart_config["x_key"]]) for item in chart_data]
        values = [item[chart_config["y_key"]] for item in chart_data]

        fig, ax = plt.subplots(figsize=(10, 5))
        ax.bar(names, values)
        ax.set_title(chart_config["title"])
        ax.set_xlabel(chart_config["x_label"])
        ax.set_ylabel(chart_config["y_label"])
        ax.tick_params(axis="x", rotation=0)
        fig.tight_layout()

    plt.savefig(str(chart_path), dpi=150)
    plt.close()


def generate_pdf(data, report_config, paths):
    doc = SimpleDocTemplate(str(paths["pdf"]), pagesize=A4)
    elements = []

    styles = getSampleStyleSheet()
    title_style = ParagraphStyle(
        name="PhoneVaultTitle",
        parent=styles["Heading1"],
        fontSize=18,
        spaceAfter=18
    )
    normal_style = styles["Normal"]

    if LOGO_PATH.exists():
        logo = Image(str(LOGO_PATH), width=1.3 * inch, height=1.3 * inch)
        elements.append(logo)
        elements.append(Spacer(1, 15))

    elements.append(Paragraph("PhoneVault - Raport Business Intelligence", title_style))
    elements.append(Spacer(1, 8))

    elements.append(Paragraph(report_config["title"], styles["Heading2"]))
    elements.append(Spacer(1, 12))

    intro_text = (
        f"{report_config['description']} "
        f"Raport generat la data: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}."
    )
    elements.append(Paragraph(intro_text, normal_style))
    elements.append(Spacer(1, 18))

    headers = [label for _, label in report_config["columns"]]
    keys = [key for key, _ in report_config["columns"]]

    table_data = [headers]
    for item in data:
        table_data.append([item[key] for key in keys])

    max_pdf_rows = report_config.get("pdf_table_limit", 20)
    if len(table_data) > max_pdf_rows + 1:
        table_data = table_data[:max_pdf_rows + 1]

    available_width = 500
    col_width = available_width / len(headers)

    table = Table(table_data, colWidths=[col_width] * len(headers))
    table.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#2c3e50")),
        ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
        ("GRID", (0, 0), (-1, -1), 0.5, colors.grey),
        ("ALIGN", (1, 1), (-1, -1), "CENTER"),
        ("BACKGROUND", (0, 1), (-1, -1), colors.HexColor("#ecf0f1")),
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
    ]))

    elements.append(table)
    elements.append(Spacer(1, 24))

    if paths["chart"].exists():
        chart_width = 6.4 * inch
        chart_height = 5.0 * inch if report_config["chart"].get("type") == "horizontal_bar" else 3.6 * inch
        chart = Image(str(paths["chart"]), width=chart_width, height=chart_height)
        elements.append(chart)

    doc.build(elements)


def generate_report(report_key, report_config):
    paths = get_paths(report_key)
    data = fetch_data(report_config)

    if not data:
        print(f"Nu există date pentru raportul: {report_config['title']}")
        return

    export_csv(data, report_config, paths["csv"])
    export_json(data, report_config, paths["json"])
    generate_chart(data, report_config, paths["chart"])
    generate_pdf(data, report_config, paths)

    print(f"Raport generat: {report_config['title']}")
    print(f"CSV: {paths['csv']}")
    print(f"JSON: {paths['json']}")
    print(f"Grafic: {paths['chart']}")
    print(f"PDF: {paths['pdf']}")


def main():
    for report_key, report_config in REPORTS.items():
        generate_report(report_key, report_config)


if __name__ == "__main__":
    main()
