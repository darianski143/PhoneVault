import os
import sys
from pathlib import Path

from cryptography.fernet import Fernet

PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from flask import Flask, render_template, request, redirect, url_for, flash, abort, render_template_string
from app.db import run_select, run_execute

FERNET_KEY = os.getenv("PHONEVAULT_FERNET_KEY")
fernet = Fernet(FERNET_KEY.encode()) if FERNET_KEY else None

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
        "create_fields": ["first_name", "last_name", "username", "email", "phone_number", "password_hash"],
        "update_fields": ["first_name", "last_name", "username", "email", "phone_number", "password_hash"],
        "list_fields": ["id", "first_name", "last_name", "username", "email", "phone_number", "password_hash", "created_at"],
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


def encrypt_phone_value(value):
    if not value:
        return value
    if str(value).startswith("gAAAAA"):
        return value
    if not fernet:
        return value
    return fernet.encrypt(str(value).encode()).decode()


def decrypt_phone_value(value):
    if not value:
        return value
    if not str(value).startswith("gAAAAA"):
        return value
    if not fernet:
        return value
    try:
        return fernet.decrypt(str(value).encode()).decode()
    except Exception:
        return value


def fetch_list(table):
    cfg = ensure_table_allowed(table)
    pk = cfg["pk"]
    cols = cfg["list_fields"]
    if cols[0] != pk:
        cols = [pk] + [c for c in cols if c != pk]
    q = f"SELECT {', '.join(cols)} FROM {table} ORDER BY {cfg.get('default_sort', pk + ' DESC')};"
    rows = run_select(q)

    if table == "customers" and "phone_number" in cols:
        phone_idx = cols.index("phone_number")
        rows = [
            tuple(
                decrypt_phone_value(cell) if idx == phone_idx else cell
                for idx, cell in enumerate(row)
            )
            for row in rows
        ]

    return cols, rows


def fetch_by_id(table, rec_id):
    cfg = ensure_table_allowed(table)
    pk = cfg["pk"]
    cols = list(dict.fromkeys([pk] + cfg["list_fields"] + cfg["create_fields"] + cfg["update_fields"]))
    q = f"SELECT {', '.join(cols)} FROM {table} WHERE {pk}=%s LIMIT 1;"
    rows = run_select(q, (rec_id,))
    row = rows[0] if rows else None

    if row and table == "customers" and "phone_number" in cols:
        phone_idx = cols.index("phone_number")
        row = tuple(
            decrypt_phone_value(cell) if idx == phone_idx else cell
            for idx, cell in enumerate(row)
        )

    return cols, row


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

        if table == "customers" and f == "phone_number":
            v = encrypt_phone_value(v)

        values.append(v)

    if table == "customers" and "password_hash" in fields:
        pwd_idx = fields.index("password_hash")
        pwd_val = values[pwd_idx]
        if not str(pwd_val).startswith("$2b$"):
            try:
                import bcrypt
                values[pwd_idx] = bcrypt.hashpw(str(pwd_val).encode(), bcrypt.gensalt()).decode()
            except Exception:
                pass

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

        if table == "customers" and f == "phone_number":
            v = encrypt_phone_value(v)

        pairs.append(f"{f}=%s")
        values.append(v)

    if table == "customers" and "password_hash" in fields:
        pwd_idx = fields.index("password_hash")
        pwd_val = values[pwd_idx]
        if not str(pwd_val).startswith("$2b$"):
            try:
                import bcrypt
                values[pwd_idx] = bcrypt.hashpw(str(pwd_val).encode(), bcrypt.gensalt()).decode()
            except Exception:
                pass

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


def allowed_fields_for_table(table):
    cfg = ensure_table_allowed(table)
    allowed_fields = set(cfg["list_fields"]) | set(cfg["create_fields"]) | set(cfg["update_fields"]) | {cfg["pk"]}
    for field in cfg.get("fk_dropdowns", {}).keys():
        allowed_fields.add(field)
    return sorted(allowed_fields)


@app.route("/api/sqli/query", methods=["POST"])
def api_sqli_query():
    table = (request.form.get("table") or "").strip()
    field = (request.form.get("field") or "").strip()
    value = (request.form.get("value") or "").strip()
    mode = (request.form.get("mode") or "safe").strip().lower()

    ensure_table_allowed(table)
    allowed_fields = allowed_fields_for_table(table)
    if field not in allowed_fields:
        return {"ok": False, "mode": mode, "error": f"Camp invalid. Campuri permise: {', '.join(allowed_fields)}"}, 400

    limit = 25

    try:
        if mode == "unsafe":
            sql = f"SELECT * FROM {table} WHERE {field} = '{value}' LIMIT {limit};"
            rows = run_select(sql)
        else:
            mode = "safe"
            sql = f"SELECT * FROM {table} WHERE {field} = %s LIMIT {limit};"
            rows = run_select(sql, (value,))

        columns = [row[0] for row in run_select(f"SHOW COLUMNS FROM {table};")]
        return {
            "ok": True,
            "mode": mode,
            "sql": sql,
            "columns": columns,
            "rows": [list(row) for row in rows],
            "count": len(rows),
        }
    except Exception as e:
        sql_value = locals().get("sql", "-")
        return {"ok": False, "mode": mode, "sql": sql_value, "error": str(e)}, 500


@app.route("/sqli-lab")
def sqli_lab():
    tables = [
        {
            "name": table,
            "title": cfg.get("title", table),
            "fields": allowed_fields_for_table(table),
        }
        for table, cfg in CRUD_CONFIG.items()
    ]

    return render_template_string(
        """
        <!doctype html>
        <html lang="ro">
        <head>
            <meta charset="utf-8">
            <meta name="viewport" content="width=device-width, initial-scale=1">
            <title>PhoneVault - SQL Injection Lab</title>
            <style>
                body { margin: 0; font-family: Arial, sans-serif; background: #07111f; color: #e8eefc; }
                header { padding: 18px 26px; background: #101b31; border-bottom: 1px solid #22314f; }
                main { max-width: 1100px; margin: 28px auto; padding: 0 18px; }
                a { color: #a7c7ff; }
                .card { background: #121d33; border: 1px solid #263955; border-radius: 14px; padding: 18px; margin-bottom: 18px; box-shadow: 0 10px 24px rgba(0,0,0,.22); }
                label { display: block; font-size: 13px; color: #aebbe0; margin-bottom: 6px; }
                select, input { width: 100%; box-sizing: border-box; padding: 10px; border-radius: 10px; border: 1px solid #33486d; background: #0b1426; color: #e8eefc; }
                .grid { display: grid; grid-template-columns: repeat(4, 1fr); gap: 12px; }
                button { margin-top: 14px; padding: 10px 16px; border: 0; border-radius: 10px; background: #6ea8fe; color: #07111f; font-weight: bold; cursor: pointer; }
                button.secondary { background: #263955; color: #e8eefc; margin-left: 8px; }
                pre { white-space: pre-wrap; word-break: break-word; background: #081020; border-radius: 10px; padding: 12px; border: 1px solid #263955; }
                table { width: 100%; border-collapse: collapse; margin-top: 12px; font-size: 13px; }
                th, td { border-bottom: 1px solid #263955; padding: 8px; text-align: left; }
                th { color: #aebbe0; }
                .hint { color: #aebbe0; font-size: 14px; }
                .error { color: #ffb4b4; }
                @media (max-width: 800px) { .grid { grid-template-columns: 1fr; } }
            </style>
        </head>
        <body>
            <header>
                <strong>PhoneVault</strong> &nbsp; | &nbsp;
                <a href="{{ url_for('index') }}">Dashboard</a>
            </header>
            <main>
                <h1>SQL Injection Lab</h1>
                <p class="hint">Modul demonstrativ controlat: compară UNSAFE, unde valoarea este concatenată în SQL, cu SAFE, unde valoarea este transmisă parametrizat. Sunt permise doar interogări SELECT, iar tabelele și câmpurile sunt validate prin whitelist.</p>

                <section class="card">
                    <div class="grid">
                        <div>
                            <label for="tableSelect">Tabel</label>
                            <select id="tableSelect"></select>
                        </div>
                        <div>
                            <label for="fieldSelect">Câmp</label>
                            <select id="fieldSelect"></select>
                        </div>
                        <div>
                            <label for="valueInput">Valoare</label>
                            <input id="valueInput" value="DemoBrand" placeholder="Ex.: DemoBrand sau ' OR '1'='1">
                        </div>
                        <div>
                            <label for="modeSelect">Mod</label>
                            <select id="modeSelect">
                                <option value="safe">SAFE (parameterized)</option>
                                <option value="unsafe">UNSAFE (string concat)</option>
                            </select>
                        </div>
                    </div>
                    <button type="button" onclick="runQuery()">Rulează query</button>
                    <button type="button" class="secondary" onclick="clearResult()">Clear</button>
                </section>

                <section class="card">
                    <h2>Generated SQL</h2>
                    <pre id="sqlBox">-</pre>
                    <h2>Status</h2>
                    <pre id="statusBox">-</pre>
                </section>

                <section class="card">
                    <h2>Result</h2>
                    <div id="resultBox" class="hint">Nu există rezultat încă.</div>
                </section>
            </main>

            <script>
                const tables = {{ tables|tojson }};
                const tableSelect = document.getElementById('tableSelect');
                const fieldSelect = document.getElementById('fieldSelect');

                function escapeHtml(value) {
                    return String(value ?? '').replace(/[&<>'"]/g, function(char) {
                        return {'&': '&amp;', '<': '&lt;', '>': '&gt;', "'": '&#39;', '"': '&quot;'}[char];
                    });
                }

                function fillTables() {
                    tableSelect.innerHTML = '';
                    tables.forEach(function(t) {
                        const option = document.createElement('option');
                        option.value = t.name;
                        option.textContent = t.title + ' (' + t.name + ')';
                        tableSelect.appendChild(option);
                    });
                    fillFields();
                }

                function fillFields() {
                    const selected = tables.find(function(t) { return t.name === tableSelect.value; });
                    fieldSelect.innerHTML = '';
                    selected.fields.forEach(function(f) {
                        const option = document.createElement('option');
                        option.value = f;
                        option.textContent = f;
                        fieldSelect.appendChild(option);
                    });
                }

                function clearResult() {
                    document.getElementById('sqlBox').textContent = '-';
                    document.getElementById('statusBox').textContent = '-';
                    document.getElementById('resultBox').innerHTML = 'Nu există rezultat încă.';
                }

                async function runQuery() {
                    const form = new FormData();
                    form.append('table', tableSelect.value);
                    form.append('field', fieldSelect.value);
                    form.append('value', document.getElementById('valueInput').value);
                    form.append('mode', document.getElementById('modeSelect').value);

                    const response = await fetch('{{ url_for('api_sqli_query') }}', { method: 'POST', body: form });
                    const data = await response.json();

                    document.getElementById('sqlBox').textContent = data.sql || '-';
                    if (!data.ok) {
                        document.getElementById('statusBox').innerHTML = '<span class="error">Error - mode=' + escapeHtml(data.mode || '-') + ' - ' + escapeHtml(data.error) + '</span>';
                        document.getElementById('resultBox').innerHTML = '<span class="error">Query-ul a produs eroare.</span>';
                        return;
                    }

                    document.getElementById('statusBox').textContent = 'OK - mode=' + data.mode + ' - rows=' + data.count;
                    if (!data.rows.length) {
                        document.getElementById('resultBox').innerHTML = '<span class="hint">0 rânduri returnate.</span>';
                        return;
                    }

                    let html = '<table><thead><tr>';
                    data.columns.forEach(function(c) { html += '<th>' + escapeHtml(c) + '</th>'; });
                    html += '</tr></thead><tbody>';
                    data.rows.forEach(function(row) {
                        html += '<tr>';
                        row.forEach(function(cell) { html += '<td>' + escapeHtml(cell) + '</td>'; });
                        html += '</tr>';
                    });
                    html += '</tbody></table>';
                    document.getElementById('resultBox').innerHTML = html;
                }

                tableSelect.addEventListener('change', fillFields);
                fillTables();
            </script>
        </body>
        </html>
        """,
        tables=tables,
    )


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
