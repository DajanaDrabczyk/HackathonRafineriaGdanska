import sqlite3

from dotenv import load_dotenv
import os

load_dotenv()

DB_PATH = "/Users/dajanadrabczyk/Documents/Hackathon/dataset_examples/weather.db"
print("DB_PATH =", DB_PATH)


conn = sqlite3.connect(DB_PATH)
cur = conn.cursor()

cur.execute("SELECT * FROM weather limit 5;")
#cur.execute("SELECT name FROM sqlite_master WHERE type='table';")
print("Tabele:", cur.fetchall())

conn.close()
