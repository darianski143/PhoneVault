from app.db import run_select

result = run_select("SELECT DATABASE() AS db_name, 'Conexiunea a avut loc cu succes!' AS status;")
print(result)