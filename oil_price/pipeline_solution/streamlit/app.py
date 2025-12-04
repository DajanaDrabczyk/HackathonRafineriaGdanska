import streamlit as st
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

DB_PATH = os.getenv("DB_PATH")


embedder = SentenceTransformer("all-MiniLM-L6-v2")


rag_chunks = [
    "Tabela oil_prices: date(TEXT YYYY-MM-DD), price(REAL), percentChange(REAL), change(REAL).",
    "Q1 = styczeń, luty, marzec.",
    "Q2 = kwiecień, maj, czerwiec.",
    "Q3 = lipiec, sierpień, wrzesień.",
    "Q4 = październik, listopad, grudzień.",
    "Filtr roczny: date LIKE 'YYYY-%'.",
    "Filtr miesięczny: date LIKE 'YYYY-MM-%'.",
    "Średnie miesięczne: GROUP BY substr(date,1,7).",
    "Średnie kwartalne: użyj BETWEEN 'YYYY-MM-DD' AND 'YYYY-MM-DD'.",
    "Zawsze zwracaj date i price przy trendach.",
]


def build_faiss_index(chunks):
    vectors = embedder.encode(chunks)
    index = faiss.IndexFlatL2(vectors.shape[1])
    index.add(np.array(vectors).astype("float32"))
    return index, vectors

faiss_index, rag_vectors = build_faiss_index(rag_chunks)

def retrieve_context(query, k=3):
    qvec = embedder.encode([query]).astype("float32")
    _, idx = faiss_index.search(qvec, k)
    return "\n".join(rag_chunks[i] for i in idx[0])


def generate_sql(question: str, context: str):
    prompt = f"""
Jesteś modelem NL→SQL dla SQLite.

ZASADY:
- Używaj TYLKO tabeli oil_prices (date, price).
- Nie używaj YEAR(), MONTH(), STRFTIME() — SQLite tego nie ma.
- Filtr po roku: date LIKE 'YYYY-%'
- Filtr po miesiącu: date LIKE 'YYYY-MM-%'
- Średnie miesięczne MUSZĄ zwrócić dwie kolumny:
  substr(date,1,7) AS month, AVG(price) AS price
- Trendy czasowe MUSZĄ zwrócić: date, price
- ZAWSZE dodawaj ORDER BY date lub ORDER BY month.
- Nigdy nie używaj ``` ani formatowania markdown.
- Zwróć tylko czysty SQL.

# Kontekst RAG:
{context}

# Pytanie:
{question}

SQL:
""".strip()

    result = subprocess.run(
        ["ollama", "run", "llama3:latest"],
        input=prompt,
        capture_output=True,
        text=True
    )

    out = result.stdout.strip()
    out = re.sub(r"```.*?```", "", out, flags=re.DOTALL)
    out = out.replace("```", "").replace("sql", "")
    if "SQL:" in out:
        out = out.split("SQL:")[-1].strip()

    return out.strip()


def sql_firewall(sql):
    s = sql.lower().strip()

    if not s.startswith("select"):
        raise ValueError("Dozwolone są tylko SELECT-y.")

    BAD = ["drop", "delete", "insert", "update", "alter", "truncate", "create"]
    if any(b in s for b in BAD):
        raise ValueError("Niedozwolone słowo kluczowe SQL!")

    if ";" in s[:-1]:
        raise ValueError("Wykryto wiele komend — zabronione!")

    return sql


def run_sql(sql):
    conn = sqlite3.connect(DB_PATH)
    df = pd.read_sql_query(sql, conn)
    conn.close()
    return df


def plot(df, title):
    if "date" in df.columns:
        try:
            df["date"] = pd.to_datetime(df["date"])
        except:
            pass
        fig = px.line(df, x="date", y=df.columns[-1], title=title)
        return fig

    if df.shape[1] == 2:
        fig = px.bar(df, x=df.columns[0], y=df.columns[1], title=title)
        return fig

    return None


st.set_page_config(page_title="Oil Price AI", layout="wide")
st.title("Oil Price Demo AI — RAG + Ollama")
st.caption("Hackathon Edition — Drabs")

question = st.text_input("Zadaj pytanie:")

if st.button("Uruchom zapytanie"):

    if not question:
        st.warning("Najpierw wpisz pytanie.")
        st.stop()

    ctx = retrieve_context(question)
    st.subheader("Kontekst RAG")
    st.code(ctx)

    sql = generate_sql(question, ctx)
    st.subheader("SQL wygenerowany:")
    st.code(sql)

    try:
        safe_sql = sql_firewall(sql)
    except Exception as e:
        st.error(f"Błąd SQL: {e}")
        st.stop()

    df = run_sql(safe_sql)
    st.subheader("Wynik:")
    st.dataframe(df)

    if not df.empty:
        fig = plot(df, question)
        if fig:
            st.subheader("Wizualizacja")
            st.plotly_chart(fig)
