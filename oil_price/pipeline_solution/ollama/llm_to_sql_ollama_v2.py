import sqlite3
import subprocess
import json

from dotenv import load_dotenv
import os

load_dotenv()

DB_PATH = os.getenv("DB_PATH")

PROMPT = """
Jesteś ekspertem w generowaniu zapytań SQL dla SQLite.

WAŻNE:
Gdy użytkownik odnosi się do kwartału:
- Q1 lub "1. kwartał" lub "pierwszy kwartał" = styczeń, luty, marzec
- Q2 = kwiecień, maj, czerwiec
- Q3 = lipiec, sierpień, wrzesień
- Q4 = październik, listopad, grudzień

ZAWSZE generuj zakresy dat używając BETWEEN, np.:

SELECT AVG(price)
FROM oil_prices
WHERE date BETWEEN '2010-01-01' AND '2010-03-31';

Nigdy nie zwracaj częściowego SQL. Nigdy nie pomijaj FROM. Nigdy nie pomijaj WHERE.
Nigdy nie używaj markdown ani backticków.

Pytanie użytkownika:
{q}

SQL:
"""



def llm(question):
    prompt = PROMPT.format(q=question)

    result = subprocess.run(
        ["ollama", "run", "qwen2.5:1.5b-instruct", prompt],
        capture_output=True,
        text=True
    )

    out = result.stdout

    sql = (
        out.split("SQL:")[-1]
            .replace("```sql", "")
            .replace("```", "")
            .strip()
    )

    return sql



def run_sql(sql):
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()
    cur.execute(sql)
    rows = cur.fetchall()
    conn.close()
    return rows

if __name__ == "__main__":
    q = input("Pytanie użytkownika: ")

    sql = llm(q)
    print("\n[SQL]:", sql)

    try:
        result = run_sql(sql)
        print("\n[Wynik]:", result)
    except Exception as e:
        print("\nBŁĄD SQL:", e)
