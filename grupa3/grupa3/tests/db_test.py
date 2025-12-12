import sqlite3

from dotenv import load_dotenv
import os

load_dotenv()

DB_PATH = os.getenv("DB_PATH")
print("DB_PATH =", DB_PATH)


conn = sqlite3.connect(DB_PATH)
cur = conn.cursor()

cur.execute("SELECT count(*) FROm imports;")
print("Tabele:", cur.fetchall())

conn.close()
