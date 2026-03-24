# PhoneVault

## Description
PhoneVault is a database project that manages information about phones, brands, customers, stores, and sales. It also includes SQL queries executed from Python.

## Database Structure
Main tables:
- brands
- phones
- customers
- stores
- sales

Relationships:
- one brand → many phones
- one phone → many sales
- one customer → many sales
- one store → many sales

## Technologies
- Python
- SQL
- JSON

## Project Structure
PhoneVault/
├── app/
│   └── db.py
├── scripts/
│   ├── select_all.py
│   ├── filter_data.py
│   ├── group_by_stats.py
│   └── outputs/
└── README.md

## Features
- JOIN queries
- Aggregations (SUM, COUNT, AVG)
- GROUP BY and ORDER BY
- Parameterized queries
- Export to JSON

## How to Run
```
python scripts/select_all.py
python scripts/filter_data.py
python scripts/group_by_stats.py
```

## Output
JSON files are saved in:
scripts/outputs/

## Author
Made with ❤️ by Darian
