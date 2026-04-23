import os
from sqlalchemy import create_engine, text
from dotenv import load_dotenv

load_dotenv()

url = os.getenv("DATABASE_URL")
print(f"Connecting to: {url[:20]}...")

try:
    engine = create_engine(url)
    with engine.connect() as conn:
        result = conn.execute(text("SELECT version();"))
        print(f"Success! DB Version: {result.fetchone()[0]}")
except Exception as e:
    print(f"Failed to connect: {e}")
