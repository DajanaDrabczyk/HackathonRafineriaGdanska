import sqlite3
import subprocess
import json

from dotenv import load_dotenv
import os

load_dotenv()

DB_PATH = os.getenv("DB_PATH")

PROMPT = """
NEW PROMPT
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

# Napisz funkcję safe_sql, która sprawdza, czy zapytanie SQL jest bezpieczne.
def safe_sql(sql: str):
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

    # Napisz blok try-except, który używa safe_sql przed wykonaniem zapytania.
