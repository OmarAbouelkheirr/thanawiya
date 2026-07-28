import sqlite3
import os
from supabase import create_client

SUPABASE_URL = os.environ.get("SUPABASE_URL")
SUPABASE_KEY = os.environ.get("SUPABASE_KEY")

if not SUPABASE_URL or not SUPABASE_KEY:
    print("Error: SUPABASE_URL and SUPABASE_KEY must be set")
    exit(1)

supabase = create_client(SUPABASE_URL, SUPABASE_KEY)

DB_PATH = os.path.join(os.path.dirname(__file__), "results.db")

conn = sqlite3.connect(DB_PATH)
conn.row_factory = sqlite3.Row
cursor = conn.cursor()

cursor.execute("SELECT seating_no, name, degree, status FROM students")
rows = cursor.fetchall()
conn.close()

print(f"Migrating {len(rows)} students to Supabase...")

BATCH_SIZE = 500
batch = []
for i, row in enumerate(rows, 1):
    batch.append({
        "seating_no": row["seating_no"],
        "name": row["name"],
        "degree": row["degree"],
        "status": row["status"]
    })
    if len(batch) == BATCH_SIZE:
        supabase.table("students").upsert(batch).execute()
        print(f"Migrated {i} / {len(rows)}")
        batch.clear()

if batch:
    supabase.table("students").upsert(batch).execute()

print(f"Migration complete. {len(rows)} students inserted.")

supabase.table("visitors").upsert({"id": 1, "count": 0}).execute()
print("Visitor counter initialized.")