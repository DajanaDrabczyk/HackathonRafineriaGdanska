import os
import sqlite3
import json
import subprocess
from dotenv import load_dotenv

load_dotenv()

DB_PATH = os.getenv("DB_PATH")

conn = sqlite3.connect(DB_PATH)
cur = conn.cursor()

cur.execute("SELECT * FROM oil_prices LIMIT 5;")
rows = cur.fetchall()

conn.close()

data_preview = json.dumps(rows, indent=2)
print(data_preview)

prompt = prompt = f"""
Oto podgląd danych z tabeli oil_prices:

{data_preview}

Zadanie:
- Opisz, co widać w tym podglądzie danych.
- Uwzględnij tylko strukturę i zawartość (np. liczba kolumn, typy wartości, ogólny układ).
- Nie analizuj plików i nie zakładaj dostępu do baz — pracujesz wyłącznie na tekście przekazanym powyżej.
"""


result = subprocess.run(
    ["ollama", "run", "qwen2.5:1.5b-instruct", prompt],
    capture_output=True,
    text=True
)

print(result.stdout)
