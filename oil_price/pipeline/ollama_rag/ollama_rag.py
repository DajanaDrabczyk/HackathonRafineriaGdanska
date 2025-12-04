import os
import sqlite3
import subprocess
import pandas as pd
import plotly.express as px
import faiss
import numpy as np
from sentence_transformers import SentenceTransformer
from dotenv import load_dotenv
import re

load_dotenv()

# sciezka do bazy danych
DB_PATH = os.getenv("DB_PATH")


# embbeder do wektorow


# rag chunks do pobierania kontekstu


# funkcja budujaca indeks faiss


# funkcja pobierajaca kontekst


# funkcja build_prompt



def call_ollama(prompt):
    result = subprocess.run(
    ["ollama", "run", "sqlcoder:latest"],
    input=prompt,
    capture_output=True,
    text=True
)
    out = result.stdout.strip()

    out = re.sub(r"```.*?```", "", out, flags=re.DOTALL)
    out = out.replace("```", "")
    out = out.replace("sql", "")

    if "SQL:" in out:
        out = out.split("SQL:")[-1].strip()

    return out.strip()


def sql_firewall(sql: str):
    s = sql.lower()

    forbidden = ["drop", "delete", "insert", "update", "alter", "truncate", "create"]
    if any(f in s for f in forbidden):
        raise ValueError("ZABLOKOWANO niebezpieczne zapytanie!")

    if not s.startswith("select"):
        raise ValueError("Dozwolone są tylko SELECT.")

    return sql


def run_sql(sql):
    conn = sqlite3.connect(DB_PATH)
    df = pd.read_sql_query(sql, conn)
    conn.close()
    return df


def plot(df, question):
    if "date" in df.columns:
        df["date"] = pd.to_datetime(df["date"], errors="coerce")
        fig = px.line(df, x="date", y="price", title=question)
        fig.show()
        return

    if df.shape[1] == 2:
        fig = px.bar(df, x=df.columns[0], y=df.columns[1], title=question)
        fig.show()

# do walidacji
def generate_sql_with_rag(question: str):
    """
    Pełny pipeline:
    - pobiera kontekst z FAISS (RAG)
    - buduje prompt
    - wysyła do Ollamy
    - zwraca czysty SQL
    """
    ctx = retrieve_context(question)
    prompt = build_prompt(question, ctx)
    sql = call_ollama(prompt)
    return sql


if __name__ == "__main__":
    q = input("Pytanie użytkownika: ")

    ctx = retrieve_context(q)
    prompt = build_prompt(q, ctx)
    sql = call_ollama(prompt)

    print("\n[SQL wygenerowany przez model]:", sql)

    try:
        sql = sql_firewall(sql)
    except Exception as e:
        print("\nBŁĄD:", e)
        exit()

    df = run_sql(sql)
    print("\n[Wynik]:\n", df)

    if not df.empty:
        plot(df, q)