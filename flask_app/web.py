import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from flask import Flask, render_template, request, redirect, url_for, flash, abort
from app.db import run_select, run_execute

app = Flask(__name__)
app.secret_key = "dev-secret"


CRUD_CONFIG = {
    "brands": {
        "pk": "id",
        "title": "Brands",
        "create_fields": ["brand_name", "country"],
        "update_fields": ["brand_name", "country"],
        "list_fields": ["id", "brand_name", "country"],
        "default_sort": "id DESC",
        "children": [
            {"table": "phones", "fk": "brand_id"},
        ],
    },
    "stores": {
        "pk": "id",
        "title": "Stores",
        "create_fields": ["store_name", "city"],
        "update_fields": ["store_name", "city"],
        "list_fields": ["id", "store_name", "city"],
        "default_sort": "id DESC",
        "children": [
            {"table": "sale_orders", "fk": "store_id"},
        ],
    },
    "customers": {
        "pk": "id",
        "title": "Customers",
        "create_fields": ["first_name", "last_name", "email", "phone_number"],
        "update_fields": ["first_name", "last_name", "email", "phone_number"],
        "list_fields": ["id", "first_name", "last_name", "email", "phone_number"],
        "default_sort": "id DESC",
        "children": [
            {"table": "sale_orders", "fk": "customer_id"},
        ],
    },
    "phones": {
        "pk": "id",
        "title": "Phones",
        "create_fields": ["brand_id", "model_name", "launch_year", "stock", "price"],
        "update_fields": ["brand_id", "model_name", "launch_year", "stock", "price"],
        "list_fields": ["id", "brand_id", "model_name", "launch_year", "stock", "price"],
        "default_sort": "id DESC",
        "fk_dropdowns": {
            "brand_id": ("brands", "id", "brand_name"),
        },
        "children": [
            {"table": "sale_order_items", "fk": "phone_id"},
        ],
    },
    "sale_orders": {
        "pk": "id",
        "title": "Sale Orders",
        "create_fields": ["store_id", "customer_id", "sale_date"],
        "update_fields": ["store_id", "customer_id", "sale_date"],
        "list_fields": ["id", "store_id", "customer_id", "sale_date"],
        "default_sort": "id DESC",
        "children": [
            {"table": "sale_order_items", "fk": "sale_order_id"},
        ],
        "fk_dropdowns": {
            "store_id": ("stores", "id", "store_name"),
            "customer_id": ("customers", "id", "email"),
        },
    },
    "sale_order_items": {
        "pk": "id",
        "title": "Sale Order Items",
        "create_fields": ["sale_order_id", "phone_id", "quantity", "unit_price", "line_total"],
        "update_fields": ["sale_order_id", "phone_id", "quantity", "unit_price", "line_total"],
        "list_fields": ["id", "sale_order_id", "phone_id", "quantity", "unit_price", "line_total"],
        "default_sort": "id DESC",
        "fk_dropdowns": {
            "sale_order_id": ("sale_orders", "id", "id"),
            "phone_id": ("phones", "id", "model_name"),
        },
    },
}


def ensure_table_allowed(table):
    if table not in CRUD_CONFIG:
        abort(404)
    return CRUD_CONFIG[table]


def database_is_ready():
    try:
        run_select("SELECT 1 FROM brands LIMIT 1;")
        return True
    except Exception:
        return False


def validate_field_name(table, field):
    cfg = ensure_table_allowed(table)
    allowed_fields = set(cfg["list_fields"]) | set(cfg["create_fields"]) | set(cfg["update_fields"]) | {cfg["pk"]}
    if field not in allowed_fields:
        raise ValueError(f"Camp invalid pentru tabelul {table}: {field}")
    return field


def record_exists(table, field, value):
    ensure_table_allowed(table)
    validate_field_name(table, field)
    q = f"SELECT 1 FROM {table} WHERE {field}=%s LIMIT 1;"
    return bool(run_select(q, (value,)))


def fetch_list(table):
    cfg = ensure_table_allowed(table)
    pk = cfg["pk"]
    cols = cfg["list_fields"]
    if cols[0] != pk:
        cols = [pk] + [c for c in cols if c != pk]
    q = f"SELECT {', '.join(cols)} FROM {table} ORDER BY {cfg.get('default_sort', pk + ' DESC')};"
    rows = run_select(q)
    return cols, rows


def fetch_by_id(table, rec_id):
    cfg = ensure_table_allowed(table)
    pk = cfg["pk"]
    cols = list(dict.fromkeys([pk] + cfg["list_fields"] + cfg["create_fields"] + cfg["update_fields"]))
    q = f"SELECT {', '.join(cols)} FROM {table} WHERE {pk}=%s LIMIT 1;"
    rows = run_select(q, (rec_id,))
    return cols, (rows[0] if rows else None)


def build_fk_options(cfg):
    options = {}
    for field, spec in cfg.get("fk_dropdowns", {}).items():
        parent_table, parent_pk, label_col = spec
        rows = run_select(
            f"SELECT {parent_pk}, {label_col} FROM {parent_table} ORDER BY {label_col} ASC;"
        )
        options[field] = [(str(r[0]), str(r[1])) for r in rows]
    return options


def insert_record(table, form):
    cfg = ensure_table_allowed(table)
    fields = cfg["create_fields"]

    values = []
    for f in fields:
        v = (form.get(f) or "").strip()
        if v == "":
            raise ValueError(f"Camp obligatoriu lipsa: {f}")
        values.append(v)

    for f, v in zip(fields, values):
        if f.endswith("_id") and "fk_dropdowns" in cfg and f in cfg["fk_dropdowns"]:
            parent_table, parent_pk, _label = cfg["fk_dropdowns"][f]
            if not record_exists(parent_table, parent_pk, v):
                raise ValueError(f"Valoare invalida pentru {f} (nu exista in {parent_table}).")

    cols = ", ".join(fields)
    placeholders = ", ".join(["%s"] * len(fields))
    q = f"INSERT INTO {table} ({cols}) VALUES ({placeholders});"
    run_execute(q, tuple(values))


def update_record(table, rec_id, form):
    cfg = ensure_table_allowed(table)
    fields = cfg["update_fields"]
    if not fields:
        raise ValueError("Acest tabel nu are UPDATE in template.")

    pairs = []
    values = []
    for f in fields:
        v = (form.get(f) or "").strip()
        if v == "":
            raise ValueError(f"Camp obligatoriu lipsa: {f}")
        pairs.append(f"{f}=%s")
        values.append(v)

    for f, v in zip(fields, values):
        if f.endswith("_id") and "fk_dropdowns" in cfg and f in cfg["fk_dropdowns"]:
            parent_table, parent_pk, _label = cfg["fk_dropdowns"][f]
            if not record_exists(parent_table, parent_pk, v):
                raise ValueError(f"Valoare invalida pentru {f} (nu exista in {parent_table}).")

    values.append(rec_id)
    q = f"UPDATE {table} SET {', '.join(pairs)} WHERE {cfg['pk']}=%s;"
    run_execute(q, tuple(values))


def delete_record_safe(table, rec_id):
    cfg = ensure_table_allowed(table)

    for ch in cfg.get("children", []):
        run_execute(f"DELETE FROM {ch['table']} WHERE {ch['fk']}=%s;", (rec_id,))

    run_execute(f"DELETE FROM {table} WHERE {cfg['pk']}=%s;", (rec_id,))


@app.before_request
def guard_if_db_missing():
    allowed_endpoints = {"setup_required", "seed_demo", "static"}
    if request.path.startswith("/static/"):
        return
    if not database_is_ready() and request.endpoint not in allowed_endpoints:
        return redirect(url_for("setup_required"))


@app.route("/")
def index():
    counts = {}
    ready = database_is_ready()
    for t in CRUD_CONFIG.keys():
        try:
            counts[t] = run_select(f"SELECT COUNT(*) FROM {t};")[0][0] if ready else 0
        except Exception:
            counts[t] = 0
    return render_template("index.html", site_cfg=CRUD_CONFIG, counts=counts, ready=ready)


@app.route("/setup")
def setup_required():
    return render_template("setup_required.html", site_cfg=CRUD_CONFIG)


@app.route("/seed-admin")
@app.route("/seed-demo")
def seed_demo():
    if not database_is_ready():
        flash("Baza de date nu este initializata inca.", "error")
        return redirect(url_for("setup_required"))

    if run_select("SELECT id FROM brands LIMIT 1;"):
        flash("Exista deja date demonstrative in tabelul brands.", "info")
        return redirect(url_for("crud_list", table="brands"))

    run_execute(
        "INSERT INTO brands (brand_name, country) VALUES (%s, %s);",
        ("DemoBrand", "Romania"),
    )
    flash("Brand demo creat.", "success")
    return redirect(url_for("crud_list", table="brands"))


@app.route("/crud/<table>")
def crud_list(table):
    cfg = ensure_table_allowed(table)
    cols, rows = fetch_list(table)
    return render_template(
        "crud_list.html",
        site_cfg=CRUD_CONFIG,
        table=table,
        table_cfg=cfg,
        cols=cols,
        rows=rows,
    )


@app.route("/crud/<table>/create", methods=["GET", "POST"])
def crud_create(table):
    cfg = ensure_table_allowed(table)
    fk_options = build_fk_options(cfg)

    if request.method == "POST":
        try:
            insert_record(table, request.form)
            flash("Creat cu succes.", "success")
            return redirect(url_for("crud_list", table=table))
        except Exception as e:
            flash(str(e), "error")

    return render_template(
        "crud_form.html",
        site_cfg=CRUD_CONFIG,
        table=table,
        table_cfg=cfg,
        mode="create",
        fields=cfg["create_fields"],
        values={},
        fk_options=fk_options,
        choices=cfg.get("choices", {}),
    )


@app.route("/crud/<table>/edit/<int:rec_id>", methods=["GET", "POST"])
def crud_edit(table, rec_id):
    cfg = ensure_table_allowed(table)
    cols, row = fetch_by_id(table, rec_id)
    if not row:
        abort(404)

    values = dict(zip(cols, row))
    fk_options = build_fk_options(cfg)

    if request.method == "POST":
        try:
            update_record(table, rec_id, request.form)
            flash("Update reusit.", "success")
            return redirect(url_for("crud_list", table=table))
        except Exception as e:
            flash(str(e), "error")

    return render_template(
        "crud_form.html",
        site_cfg=CRUD_CONFIG,
        table=table,
        table_cfg=cfg,
        mode="edit",
        fields=cfg["update_fields"],
        values=values,
        fk_options=fk_options,
        choices=cfg.get("choices", {}),
        rec_id=rec_id,
    )


@app.route("/crud/<table>/delete/<int:rec_id>", methods=["POST"])
def crud_delete(table, rec_id):
    ensure_table_allowed(table)
    try:
        delete_record_safe(table, rec_id)
        flash("Sters cu succes!", "success")
    except Exception as e:
        flash(str(e), "error")
    return redirect(url_for("crud_list", table=table))


@app.route("/search", methods=["GET", "POST"])
def search():
    result = None
    if request.method == "POST":
        table = (request.form.get("table") or "").strip()
        field = (request.form.get("field") or "").strip()
        value = (request.form.get("value") or "").strip()
        try:
            cfg = ensure_table_allowed(table)
            allowed_fields = set(cfg["list_fields"]) | set(cfg["create_fields"]) | set(cfg["update_fields"]) | {cfg["pk"]}
            if field not in allowed_fields:
                raise ValueError(f"Camp invalid pentru tabelul {table}: {field}")
            exists = record_exists(table, field, value)
            result = {"ok": True, "exists": exists, "table": table, "field": field, "value": value}
        except Exception as e:
            result = {"ok": False, "error": str(e)}

    return render_template("search.html", site_cfg=CRUD_CONFIG, result=result)


if __name__ == "__main__":
    app.run(debug=True)
