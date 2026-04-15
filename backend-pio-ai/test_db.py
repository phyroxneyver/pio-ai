import os
from sqlalchemy import create_engine
url = "postgresql://neondb_owner:npg_P6r3fgWCkTIN@ep-snowy-wave-a4hmle25-pooler.us-east-1.aws.neon.tech/neondb?channel_binding=require&sslmode=require"
print(f"Connecting to {url}")
try:
    engine = create_engine(url)
    conn = engine.connect()
    print("Connected.")
    conn.close()
except Exception as e:
    print(f"Error: {e}")
