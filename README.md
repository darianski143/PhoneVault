# PhoneVault

## Description
PhoneVault is a database project that manages information about phones, brands, customers, stores, and sales. It features a completely containerized MariaDB setup via Docker, an extensive suite of Python scripts for business logic, and a full Flask-based Web UI.

## Database Structure
Main tables:
- **brands**
- **phones**
- **customers**
- **stores**
- **sales**
- **specifications**
- **customer_log**
- **sale_orders**
- **sale_order_items**

Relationships:
- one brand → many phones
- one phone → one specification
- one phone → many sales / sale_order_items
- one customer → many sales / sale_orders / logs
- one store → many sales / sale_orders
- one sale_order → many sale_order_items

## Technologies
- **Python** (Flask, python-dotenv, mariadb connector, cryptography)
- **SQL** (MariaDB)
- **Docker & Docker Compose**
- **HTML/CSS** (Flask templates)

## Project Structure
PhoneVault/
├── app/                  # Shared database connection logic (db.py)
├── docker-compose.yml    # Docker configuration for MariaDB service
├── flask_app/            # Main Web UI (web.py, static/, templates/)
├── scripts/              # Extensive Python logic (CRUD, benchmarks, security, import/export)
│   └── outputs/          # Execution outputs (JSON, CSV, PDF, PNG charts)
└── sql/                  # Structured SQL execution files (Schema, Procedures, Triggers)

## Features
- **Flask Web UI:** Interactive dashboard for managing your store, stock and sales parameters.
- **Docker Support:** Ready to launch database setup.
- **Advanced SQL Objects:** Database built with Triggers, Stored Procedures, and fine-tuned Indexes.
- **Reporting & Benchmarking:** Scripts designed to deliver PDFs, generate metrics charts (PNG), or format payloads as JSON/CSV.
- **Security Mechanisms:** Usage of Cryptography package for specific data points and proper config handling.

## How to Run
1. Start the MariaDB Docker container:
```bash
docker-compose up -d
```
2. Populate Data (if not persisted):
```bash
python scripts/rebuild_db.py
python scripts/insert_data.py
```
3. Run the Web App:
```bash
python flask_app/web.py
```

## Output
Generated execution metrics, reports, charts, and exports are saved natively under:
`scripts/outputs/`

## Author
Made with ❤️ by Darian
