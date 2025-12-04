import os
import sqlite3
import requests
import plotly.express as px
import pandas as pd

from dotenv import load_dotenv
import os

load_dotenv()

GROQ_API_KEY = os.getenv("GROQ_API_KEY")
DB_PATH = os.getenv("DB_PATH")



def generate_sql(question: str, schema_description: str):
    url = "https://api.groq.com/openai/v1/chat/completions"
    headers = {
        "Authorization": f"Bearer {os.environ[GROQ_API_KEY]}",
        "Content-Type": "application/json"
    }

    prompt = f"""
Jesteś modelem NL→SQL. Generuj TYLKO poprawny SQL na SQLite.
Baza danych ma schemat:

{schema_description}

Użytkownik pyta:
{question}

Zwróć tylko SQL, bez komentarzy, bez ```sql.
"""

    body = {
        "model": "llama-3.1-8b-instant",
        "messages": [{"role": "user", "content": prompt}],
        "temperature": 0
    }

    resp = requests.post(url, headers=headers, json=body)
    resp_json = resp.json()

    if "error" in resp_json:
        raise RuntimeError(f"Groq API error: {resp_json['error']}")

    if "choices" not in resp_json:
        raise RuntimeError(f"Unexpected Groq response: {resp_json}")

    sql = resp_json["choices"][0]["message"]["content"]
    return sql.strip()


def sql_firewall(sql: str):
    sql_lower = sql.lower()

    forbidden = ["drop", "delete", "truncate", "alter", "update", "insert"]
    if any(f in sql_lower for f in forbidden):
        raise ValueError(f"ZABLOKOWANO niebezpieczne zapytanie: {sql}")

    if not sql_lower.startswith("select"):
        raise ValueError("Tylko SELECT jest dozwolony.")

    return sql


conn = sqlite3.connect(DB_PATH)

def run_sql(sql: str):
    df = pd.read_sql_query(sql, conn)
    return df


def plot_results(df: pd.DataFrame, title="Wynik zapytania"):
    if "date" in df.columns:
        try:
            df["date"] = pd.to_datetime(df["date"])
        except:
            pass

    fig = px.line(df, x=df.columns[0], y=df.columns[-1], title=title)
    fig.show()


if __name__ == "__main__":
    schema = """
Tabela: oil_prices
Kolumny:
- date TEXT
- price REAL
- percentChange REAL
- change REAL
"""

    question = input("Pytanie użytkownika: ")

    sql = generate_sql(question, schema)
    print("\n[SQL wygenerowany]:", sql)

    try:
        safe_sql = sql_firewall(sql)
    except Exception as e:
        print("\nFirewall:", e)
        exit()

    df = run_sql(safe_sql)
    print("\n[Wynik]:")
    print(df)

    if len(df.columns) >= 2:
        plot_results(df, title=question)
    else:
        print("\n(Brak kolumn do wykresu)")
