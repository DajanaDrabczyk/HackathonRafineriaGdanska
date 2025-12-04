import sqlite3
import torch
from transformers import AutoTokenizer, AutoModelForCausalLM
from dotenv import load_dotenv
import os

load_dotenv()

DB_PATH = os.getenv("DB_PATH")

MODEL_NAME = "TinyLlama/TinyLlama-1.1B-Chat-v1.0"

print("[Ładowanie TinyLlama…]")

tokenizer = AutoTokenizer.from_pretrained(MODEL_NAME)
model = AutoModelForCausalLM.from_pretrained(
    MODEL_NAME,
    torch_dtype=torch.float32,
    device_map="cpu"
)

EOS = tokenizer.eos_token_id


def generate_sql(question):
    prompt = f"""
You convert text questions to SQL.
Database: SQLite.
Table: oil_prices(date TEXT, price REAL, percentChange REAL, change REAL)

Return ONLY SQL query.

Question: {question}
SQL:
"""

    inputs = tokenizer(prompt, return_tensors="pt").to("cpu")

    with torch.no_grad():
        outputs = model.generate(
            **inputs,
            max_new_tokens=120,
            do_sample=False,
            eos_token_id=EOS,
            pad_token_id=EOS,
            max_time=5.0      
        )

    text = tokenizer.decode(outputs[0], skip_special_tokens=True)

    if "SQL:" in text:
        sql = text.split("SQL:")[-1]
    else:
        sql = text

    sql = sql.replace("```", "").strip()
    sql = sql.split("\n")[0].strip()   

    return sql


def run_sql(sql):
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()
    cur.execute(sql)
    rows = cur.fetchall()
    conn.close()
    return rows


if __name__ == "__main__":
    question = input("Pytanie użytkownika: ")

    sql = generate_sql(question)
    print("\n[SQL]:", sql)

    try:
        result = run_sql(sql)
        print("\n[Wynik SQL]:")
        for r in result:
            print(r)
    except Exception as e:
        print("\nBŁĄD SQL:", e)
