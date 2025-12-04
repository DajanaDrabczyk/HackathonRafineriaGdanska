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
Jesteś ekspertem w generowaniu zapytań SQL dla SQLite.
…
WAŻNE:
Gdy użytkownik pyta o ceny, trendy lub wykresy, ZAWSZE zwracaj dwie kolumny:
date oraz price.
Przykład:
SELECT date, price
FROM oil_prices
WHERE date BETWEEN '2010-01-01' AND '2010-12-31';
NIGDY nie zwracaj tylko kolumny price.
NIGDY nie zwracaj zapytań jedno-kolumnowych.
NIGDY nie używaj markdown ani backticków.
Pytanie użytkownika:
{q}
SQL:
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


def plot_results(df: pd.DataFrame, question="Wynik zapytania"):
    if "date" in df.columns:
        try:
            df["date"] = pd.to_datetime(df["date"]).dt.tz_localize(None)
        except:
            pass

    if "date" in df.columns and "price" in df.columns:
        fig = px.line(df, x="date", y="price", title=question)
        fig.show()
        return

    if df.shape[1] == 1:
        print("\n(Wynik jednowymiarowy — bez wykresu)")
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

    if not df.empty:
        plot_results(df, question)
