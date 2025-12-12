#!/usr/bin/env python3
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

# =====================================================
# Load .env
# =====================================================
load_dotenv()
CSV_PATH = os.getenv("CSV_PATH")
DB_PATH = os.getenv("DB_PATH")
TABLE_NAME = "AI_Impact_on_Jobs_2030"

if CSV_PATH is None or DB_PATH is None:
    raise ValueError(":x: Brakuje CSV_PATH lub DB_PATH w pliku .env!")

# =====================================================
# CSV -> SQLite (z zawsze poprawną nazwą tabeli)
# =====================================================
def csv_to_sqlite(csv_path, sqlite_path, table_name=TABLE_NAME):
    df = pd.read_csv(csv_path)
    conn = sqlite3.connect(sqlite_path)
    df.to_sql(table_name, conn, if_exists="replace", index=False)
    conn.close()
    print(f":heavy_check_mark: Utworzono SQLite DB: {sqlite_path}, tabela: {table_name}")

print(":information_source: Nadpisuję bazę danych z CSV...")
csv_to_sqlite(CSV_PATH, DB_PATH, TABLE_NAME)

# =====================================================
# Helper: pobierz kolumny tabeli
# =====================================================
def get_table_columns(db_path, table_name=TABLE_NAME):
    conn = sqlite3.connect(db_path)
    try:
        cur = conn.cursor()
        cur.execute(f"PRAGMA table_info('{table_name}')")
        rows = cur.fetchall()
        cols = [r[1] for r in rows]  # 2nd column is name
        return cols
    finally:
        conn.close()

# =====================================================
# RAG / FAISS (prosty)
# =====================================================
embedder = SentenceTransformer("all-MiniLM-L6-v2")
rag_chunks = [
    
"Struktura tabeli AI_Impact_on_Jobs_2030 (każda kolumna jest tekstowa/liczbowa zgodnie z CSV):",
"- JobTitle – nazwa zawodu",
"- Industry – branża",
"- Country – kraj",
"- Year – rok prognozy",
"- EmploymentChange – prognozowana zmiana zatrudnienia do 2030 (%)",
"- AutomationRisk – ryzyko automatyzacji (%)",
"- AvgSalary – średnie wynagrodzenie (w USD)",
"- EducationLevel – wymagane wykształcenie",
"- AI_Impact_Score – ogólny wpływ AI (0–100)",
"- ReskillingNeeded – czy wymagane przekwalifikowanie (Yes/No)",
"- DemandGrowth – wzrost popytu (%)",
"- Region – region geograficzny",
"- ExperienceLevel – poziom doświadczenia (Entry/Mid/Senior)",
"- RemotePossible – możliwość pracy zdalnej (Yes/No)"
]

def build_faiss(chunks):
    if len(chunks) == 0:
        print(":warning: Brak chunków RAG — pomijam FAISS.")
        return None, None
    vecs = embedder.encode(chunks)
    index = faiss.IndexFlatL2(vecs.shape[1])
    index.add(np.array(vecs).astype("float32"))
    return index, vecs

faiss_index, vecs = build_faiss(rag_chunks)

def retrieve_context(query, k=3):
    if faiss_index is None:
        return ""
    qvec = embedder.encode([query]).astype("float32")
    _, idx = faiss_index.search(qvec, k)
    return "\n".join(rag_chunks[i] for i in idx[0])

# =====================================================
# LLM prompt (z listą kolumn)
# =====================================================
def build_prompt(question, context, columns):
    cols_text = ", ".join(columns)
    return f"""
Jesteś ekspertem SQL i analitykiem danych. Masz do dyspozycji tabelę **{TABLE_NAME}** z kolumnami:
{cols_text}

Zasady absolutne:
1) ZAWSZE używaj tylko tych nazw kolumn, które tu wypisałem (dokładna wielkość liter nie musi być zachowana, ale nazwy muszą odpowiadać).
2) ZAWSZE zwracaj tylko jedną rzecz:
   - jeśli pytanie dotyczy danych → zwróć TYLKO czysty SELECT (bez komentarzy, bez markdown, bez preambuł).
   - jeśli pytanie nie wymaga SQL → zwróć krótką odpowiedź tekstową.
3) Nie twórz nowych kolumn.
4) Nie używaj DDL ani DML (tylko SELECT).
5) Jeśli pytanie jest niejednoznaczne → wybierz typową interpretację i generuj SELECT.

Przykład: "podaj średnie zarobki" → SELECT AVG(AvgSalary) FROM AI_Impact_on_Jobs_2030;

Kontekst:
{context}

Pytanie użytkownika:
{question}

Zwróć WYŁĄCZNIE zapytanie SQL (SELECT). Nie dodawaj nic poza zapytaniem.
""".strip()

# =====================================================
# Ollama
# =====================================================
def call_ollama(prompt):
    try:
        result = subprocess.run(
            ["ollama", "run", "llama3.2:3b"],
            input=prompt,
            capture_output=True,
            text=True,
            check=False
        )
    except FileNotFoundError:
        print(":x: Nie znaleziono programu 'ollama' w PATH. Upewnij się, że jest zainstalowany.")
        return ""
    if result.returncode != 0:
        print(":x: Błąd Ollama:", result.stderr)
        return ""
    out = result.stdout.strip()
    out = re.sub(r"```.*?```", "", out, flags=re.DOTALL)
    out = out.replace("```", "")
    out = out.replace("sql", "")
    return out.strip()

# =====================================================
# SQL firewall
# =====================================================
def sql_firewall(sql: str):
    if not sql or sql.strip() == "":
        raise ValueError(":x: Model nie wygenerował SQL!")
    s = sql.lower().strip()
    forbidden = ["drop ", "delete ", "insert ", "update ", "alter ", "truncate ", "create "]
    if any(f in s for f in forbidden):
        raise ValueError(":x: ZABLOKOWANO niebezpieczne zapytanie!")
    if not s.startswith("select"):
        # jeśli model zwrócił np. "AVG(...)" bez FROM — spróbujemy dopasować
        if s.startswith("avg(") or s.startswith("count(") or s.startswith("sum(") or s.startswith("min(") or s.startswith("max("):
            # dozwolone — lecz upewnijmy się, że będzie miało FROM dalej (sprawdzane przy wykonaniu)
            return sql
        raise ValueError(":x: Dozwolone są tylko SELECT.")
    return sql

# =====================================================
# RUN SQL + auto-fix brakującej kolumny (fuzzy)
# =====================================================
def run_sql_with_autofix(sql, db_path, table_cols):
    conn = sqlite3.connect(db_path)
    try:
        try:
            df = pd.read_sql_query(sql, conn)
            return df, sql, None  # success
        except Exception as e:
            msg = str(e)
            # szukaj patternu 'no such column: <name>'
            m = re.search(r"no such column:? ?([A-Za-z0-9_]+)", msg, flags=re.IGNORECASE)
            if not m:
                raise
            missing = m.group(1)
            print(f":warning: Brak kolumny wykryty w SQL: '{missing}' — próbuję znaleźć najbliższe dopasowanie...")
            # fuzzy match
            candidates = difflib.get_close_matches(missing, table_cols, n=3, cutoff=0.5)
            if not candidates:
                raise RuntimeError(f":x: Nie udało się znaleźć dopasowania dla kolumny '{missing}'. Dostępne kolumny: {table_cols}")
            best = candidates[0]
            print(f":information_source: Zamieniam '{missing}' -> '{best}' i ponawiam zapytanie.")
            # replace (case-insensitive) occurrences of missing with best
            pattern = re.compile(re.escape(missing), flags=re.IGNORECASE)
            fixed_sql = pattern.sub(best, sql)
            try:
                df = pd.read_sql_query(fixed_sql, conn)
                return df, fixed_sql, f"Replaced column '{missing}' with '{best}'"
            except Exception as e2:
                print(":x: Naprawa nie pomogła:", e2)
                raise
    finally:
        conn.close()

# =====================================================
# Wykresy
# =====================================================
def plot(df, question):
    if df.empty:
        return
    if "date" in df.columns:
        df["date"] = pd.to_datetime(df["date"], errors="coerce")
        fig = px.line(df, x="date", y=df.columns[1], title=question)
        fig.show()
        return
    if df.shape[1] == 2:
        fig = px.bar(df, x=df.columns[0], y=df.columns[1], title=question)
        fig.show()

# =====================================================
# Main
# =====================================================
def main():
    cols = get_table_columns(DB_PATH, TABLE_NAME)
    if not cols:
        print(f":x: Nie znaleziono kolumn w tabeli {TABLE_NAME}. Sprawdź CSV i import.")
        sys.exit(1)
    print(f":heavy_check_mark: Dostępne kolumny: {cols}")

    q = input("Pytanie użytkownika: ")
    ctx = retrieve_context(q)
    prompt = build_prompt(q, ctx, cols)
    sql = call_ollama(prompt)

    print("\n==== SQL wygenerowany przez model ====")
    print(sql)

    try:
        sql = sql_firewall(sql)
    except Exception as e:
        print("\n:x: BŁĄD:", e)
        sys.exit(1)

    # Jeśli model nie podał FROM ... TABLE_NAME, dodaj FROM (proste dopasowanie)
    if re.search(r"from\s+[A-Za-z0-9_]+", sql, flags=re.IGNORECASE) is None:
        # spróbuj dodać FROM TABLE_NAME jeśli SELECT zawiera funkcję agregującą bez FROM
        if sql.strip().lower().startswith(("select ", "avg(", "count(", "sum(", "min(", "max(")):
            if "from" not in sql.lower():
                sql = sql.rstrip().rstrip(";")
                sql = f"{sql} FROM {TABLE_NAME}"
                print(f":information_source: Dodałem brakujący FROM: {sql}")

    try:
        df, used_sql, note = run_sql_with_autofix(sql, DB_PATH, cols)
    except Exception as e:
        print("\n:x: BŁĄD wykonania SQL:", e)
        sys.exit(1)

    print("\n==== WYKONANE SQL ====")
    print(used_sql)
    if note:
        print(":information_source:", note)

    print("\n==== WYNIK ====")
    print(df)

    plot(df, q)

if __name__ == "__main__":
    main()