import os
import psycopg2
from dotenv import load_dotenv

load_dotenv()

conn_string = os.getenv("DATABASE_URL")
print(f"Connecting to Postgres directly...")

try:
    conn = psycopg2.connect(conn_string)
    cur = conn.cursor()
    cur.execute("SELECT 1;")
    print("Success! Result:", cur.fetchone())
    cur.close()
    conn.close()
except Exception as e:
    print(f"Failed: {e}")
