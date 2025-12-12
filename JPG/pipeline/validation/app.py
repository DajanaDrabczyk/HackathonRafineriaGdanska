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
import difflib
import sys
faiss_index = None
rag_vectors = None
rag_chunks = []
# =====================================================================================
# Load .env
# =====================================================================================
load_dotenv()
CSV_PATH = os.getenv("CSV_PATH")
DB_PATH = os.getenv("DB_PATH")
TABLE_NAME = "AI_Impact_on_Jobs_2030"
if CSV_PATH is None or DB_PATH is None:
    st.error(":x: Brakuje CSV_PATH lub DB_PATH w pliku .env!")
    st.stop()
# =====================================================================================
# CSV → SQLite
# =====================================================================================
@st.cache_resource
def csv_to_sqlite(csv_path, sqlite_path, table_name=TABLE_NAME):
    df = pd.read_csv(csv_path)
    conn = sqlite3.connect(sqlite_path)
    df.to_sql(table_name, conn, if_exists="replace", index=False)
    conn.close()
    return df.columns.tolist()
table_columns = csv_to_sqlite(CSV_PATH, DB_PATH, TABLE_NAME)
# =====================================================================================
# RAG / FAISS
# =====================================================================================
embedder = SentenceTransformer("all-MiniLM-L6-v2")
rag_chunks = [
"Struktura tabeli AI_Impact_on_Jobs_2030:",
"- JobTitle",
"- Industry",
"- Country",
"- Year",
"- EmploymentChange",
"- AutomationRisk",
"- AvgSalary",
"- EducationLevel",
"- AI_Impact_Score",
"- ReskillingNeeded",
"- DemandGrowth",
"- Region",
"- ExperienceLevel",
"- RemotePossible"
]
def build_faiss_index(chunks):
    vectors = embedder.encode(chunks)
    vectors = np.array(vectors).astype("float32")
    dim = vectors.shape[1]
    index = faiss.IndexFlatL2(dim)
    index.add(vectors)
    return index, vectors
def retrieve_context(query, k=3):
    global faiss_index, rag_vectors, rag_chunks
    if faiss_index is None:
        return ""
    qvec = embedder.encode([query])
    qvec = np.array(qvec).astype("float32")
    if qvec.ndim == 1:
        qvec = qvec.reshape(1, -1)
    _, idx = faiss_index.search(qvec, k)
    return "\n".join(rag_chunks[i] for i in idx[0])
# =====================================================================================
# PROMPT
# =====================================================================================
def build_prompt(question, context, columns):
    cols_text = ", ".join(columns)
    return f"""
Jesteś ekspertem SQL. Tabela: **{TABLE_NAME}**
Kolumny: {cols_text}
Zasady:
- Zwracasz TYLKO czysty SELECT.
- Używasz WYŁĄCZNIE podanych kolumn.
- Używaj FROM {TABLE_NAME}.
Przykład: SELECT AVG(AvgSalary) FROM {TABLE_NAME};
Pytanie:
{question}
Kontekst:
{context}
"""
# =====================================================================================
# Ollama
# =====================================================================================
def call_ollama(prompt):
    result = subprocess.run(
        ["ollama", "run", "llama3.2:3b"],
        input=prompt,
        capture_output=True,
        text=True
    )
    out = result.stdout.strip()
    out = re.sub(r"```.*?```", "", out, flags=re.DOTALL)
    out = out.replace("```", "")
    return out.strip()
# =====================================================================================
# SQL firewall
# =====================================================================================
def sql_firewall(sql):
    s = sql.lower().strip()
    forbidden = ["drop ", "delete ", "insert ", "update ", "alter ", "truncate ", "create "]
    if any(f in s for f in forbidden):
        raise ValueError(":x: Niedozwolone zapytanie SQL.")
    if not s.startswith("select"):
        if s.startswith(("avg(", "sum(", "min(", "max(", "count(")):
            return sql
        raise ValueError("Tylko SELECT.")
    return sql
# =====================================================================================
# RUN SQL + autofix kolumn
# =====================================================================================
def run_sql_autofix(sql, db_path, table_cols):
    conn = sqlite3.connect(db_path)
    try:
        try:
            return pd.read_sql_query(sql, conn), sql
        except Exception as e:
            msg = str(e)
            m = re.search(r"no such column:? ?([A-Za-z0-9_]+)", msg)
            if not m:
                raise
            missing = m.group(1)
            candidates = difflib.get_close_matches(missing, table_cols, n=1, cutoff=0.5)
            if not candidates:
                raise RuntimeError(f"Nie znaleziono kolumny: {missing}")
            best = candidates[0]
            fixed_sql = re.sub(missing, best, sql, flags=re.IGNORECASE)
            return pd.read_sql_query(fixed_sql, conn), fixed_sql
    finally:
        conn.close()
# =====================================================================================
# Streamlit UI
# =====================================================================================
st.title(":mag: LLM → SQL → SQLite – Query App")
st.write("Wprowadź zapytanie w języku naturalnym — model wygeneruje SQL i pobierze dane z bazy.")
question = st.text_input("Twoje zapytanie:")
if st.button("Wyślij"):
    if question.strip() == "":
        st.warning("Wpisz zapytanie.")
        st.stop()
    ctx = retrieve_context(question)
    prompt = build_prompt(question, ctx, table_columns)
    sql = call_ollama(prompt)
    st.subheader(":large_blue_circle: Wygenerowany SQL")
    st.code(sql, language="sql")
    try:
        sql_checked = sql_firewall(sql)
        # dopisz FROM jeśli brakuje
        if "from" not in sql_checked.lower():
            sql_checked = sql_checked.rstrip(";")
            sql_checked += f" FROM {TABLE_NAME}"
        df, final_sql = run_sql_autofix(sql_checked, DB_PATH, table_columns)
        st.subheader(":large_green_circle: Użyty SQL (po ewentualnych poprawkach)")
        st.code(final_sql, language="sql")
        st.subheader(":bar_chart: Wynik zapytania")
        st.dataframe(df)
        # wykres jeśli są 2 kolumny
        if df.shape[1] == 2:
            fig = px.bar(df, x=df.columns[0], y=df.columns[1])
            st.plotly_chart(fig)
    except Exception as e:
        st.error(f"Błąd: {e}")