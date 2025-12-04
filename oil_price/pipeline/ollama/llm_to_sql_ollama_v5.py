import os
import sqlite3
import subprocess
import pandas as pd
import plotly.express as px
import faiss
import numpy as np
from sentence_transformers import SentenceTransformer
from dotenv import load_dotenv

load_dotenv()

DB_PATH = os.getenv("DB_PATH")


def generate_sql(q: str):

    prompt = f"""
NEW PROMPT
"""

    result = subprocess.run(
        ["ollama", "run", "sqlcoder:latest", prompt],
        capture_output=True,
        text=True
    )

    sql = result.stdout.strip()

    sql = sql.replace("```sql", "").replace("```", "")

    if "SQL:" in sql:
        sql = sql.split("SQL:")[-1].strip()

    return sql


def sql_firewall(sql: str):
    sql_lower = sql.lower()

    dangerous = ["drop", "delete", "update", "insert", "alter", "create", "truncate"]
    if any(d in sql_lower for d in dangerous):
        raise ValueError("ZABLOKOWANO niebezpieczne zapytanie!")

    if not sql_lower.startswith("select"):
        raise ValueError("Dozwolone tylko SELECT.")

    return sql

def run_sql(sql: str):
    conn = sqlite3.connect(DB_PATH)
    df = pd.read_sql_query(sql, conn)
    conn.close()
    return df

# Napisz funkcję plor_result do wyświetlania wykresów tylko wtedy, gdy wynik ma kolumny 'date' i 'price'.
def plot_results(df: pd.DataFrame, question="Wynik zapytania"):
        return


if __name__ == "__main__":
    question = input("Pytanie użytkownika: ")

    sql = generate_sql(question)

    print("\n[SQL wygenerowany przez OLLAMĘ]:", sql)

    try:
        safe = sql_firewall(sql)
    except Exception as e:
        print("\nBŁĄD FIREWALL:", e)
        exit()

    df = run_sql(safe)
    print("\n[Wynik SQL]:")
    print(df)

    # Dodaj wywołanie plot_results
