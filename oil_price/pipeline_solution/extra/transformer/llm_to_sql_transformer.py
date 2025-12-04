import os
import sqlite3
from transformers import AutoModelForCausalLM, AutoTokenizer
import torch

# --- LLM ---
model_id = "TinyLlama/TinyLlama-1.1B-Chat-v1.0"
tokenizer = AutoTokenizer.from_pretrained(model_id)
model = AutoModelForCausalLM.from_pretrained(model_id)

prompt = "SELECT avg(price) FROM oil_prices WHERE year=2008;"
inputs = tokenizer(prompt, return_tensors="pt")

with torch.no_grad():
    out = model.generate(**inputs, max_new_tokens=50)

sql_query = tokenizer.decode(out[0], skip_special_tokens=True)
print("[LLM wygenerował SQL]:", sql_query)


# --- DB ---
DB_PATH = os.getenv("DB_PATH")

if not DB_PATH:
    raise RuntimeError("Brakuje zmiennej środowiskowej DB_PATH.")

if not os.path.exists(DB_PATH):
    raise FileNotFoundError(f"Plik bazy nie istnieje: {DB_PATH}")

# Connect
conn = sqlite3.connect(DB_PATH)
cursor = conn.cursor()

try:
    cursor.execute(sql_query)
    result = cursor.fetchall()
    print("\n[Wynik SQL]:")
    print(result)

except sqlite3.Error as e:
    print("\n[SQL ERROR]:", e)

finally:
    conn.close()
