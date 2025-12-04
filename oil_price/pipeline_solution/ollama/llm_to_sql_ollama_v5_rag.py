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


embedder = SentenceTransformer("all-MiniLM-L6-v2")


rag_chunks = [
    """
Tabela: oil_prices
Kolumny:
  - date (TEXT, format YYYY-MM-DD)
  - price (REAL)
  - percentChange (REAL)
  - change (REAL)
""",

    "Q1 = styczeń, luty, marzec.",
    "Q2 = kwiecień, maj, czerwiec.",
    "Q3 = lipiec, sierpień, wrzesień.",
    "Q4 = październik, listopad, grudzień.",

    "Filtr po roku: WHERE date LIKE 'YYYY-%'.",
    "Filtr po miesiącu: WHERE date LIKE 'YYYY-MM-%'.",
    "Filtr po kwartale używa BETWEEN, np. 2010-Q1 to 2010-01-01 — 2010-03-31.",

    "Średnia cena w roku: SELECT AVG(price) FROM oil_prices WHERE date LIKE '2010-%';",
    "Ceny miesięczne: SELECT date, price FROM oil_prices WHERE date LIKE '2010-03-%';",
    "Ceny z kwartału: SELECT date, price FROM oil_prices WHERE date BETWEEN '2010-04-01' AND '2010-06-30';",
]


def build_faiss_index(chunks):
    vectors = embedder.encode(chunks)
    index = faiss.IndexFlatL2(vectors.shape[1])
    index.add(np.array(vectors).astype("float32"))
    return index, vectors

faiss_index, rag_vectors = build_faiss_index(rag_chunks)


def retrieve_context(query, k=3):
    qvec = embedder.encode([query]).astype("float32")
    distances, indices = faiss_index.search(qvec, k)
    return "\n\n".join(rag_chunks[i] for i in indices[0])


def generate_sql(question: str, context: str):

    prompt = f"""
Jesteś ekspertem NL→SQL dla SQLite.

UŻYWAJ TYLKO:
- SELECT
- WHERE
- BETWEEN
- LIKE 'YYYY-%'

ZAKAZ:
- YEAR(), MONTH(), DAY(), STRFTIME(), funkcji z MySQL/Postgres
- DROP, DELETE, UPDATE, INSERT, ALTER, CREATE, TRUNCATE
- markdown, ```sql, ```.

Upewnij się, że tabela to ZAWSZE oil_prices.

Jeśli użytkownik pyta o trend, ceny, przebieg, miesiące lub kwartały:
→ ZAWSZE zwróć DWIE kolumny: date, price.

Jeśli użytkownik pyta o średnią:
→ Zwróć jedną kolumnę: AVG(price).

# KONTEKST RAG:
{context}

# PYTANIE:
{question}

# SQL (bez żadnego markdown):
"""

    result = subprocess.run(
        ["ollama", "run", "qwen2.5:1.5b-instruct", prompt],
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

    context = retrieve_context(question)
    sql = generate_sql(question, context)

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
