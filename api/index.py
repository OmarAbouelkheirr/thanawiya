from fastapi import FastAPI, Query
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
import sqlite3
import os
import urllib.request
import struct

app = FastAPI(title="High School Exam Results API")

# Enable CORS for local testing
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

DB_GITHUB_URL = "https://media.githubusercontent.com/media/OmarAbouelkheirr/thanawiya/main/results.db"

def is_lfs_pointer(path):
    try:
        with open(path, "r", encoding="utf-8") as f:
            return f.read(100).startswith("version https://git-lfs.github.com/")
    except Exception:
        return False

def ensure_db():
    current_dir = os.path.dirname(os.path.abspath(__file__))
    paths_to_try = [
        os.path.join(current_dir, "..", "results.db"),
        os.path.join(current_dir, "results.db"),
        os.path.join("/tmp", "results.db"),
    ]

    for p in paths_to_try:
        if os.path.exists(p) and os.path.getsize(p) > 1024 and not is_lfs_pointer(p):
            return p

    # Download to /tmp
    tmp_path = "/tmp/results.db"
    try:
        print(f"Downloading database from {DB_GITHUB_URL} to {tmp_path}...")
        urllib.request.urlretrieve(DB_GITHUB_URL, tmp_path)
        if os.path.exists(tmp_path) and os.path.getsize(tmp_path) > 1024:
            print(f"Database downloaded successfully ({os.path.getsize(tmp_path)} bytes)")
            return tmp_path
    except Exception as e:
        print(f"Failed to download database: {e}")

    # Try local even if LFS pointer (unlikely to work)
    for p in paths_to_try:
        if os.path.exists(p) and os.path.getsize(p) > 0:
            return p
    return paths_to_try[0]

db_path = ensure_db()

VISITOR_DB = os.path.join(os.path.dirname(db_path) if os.path.isdir(os.path.dirname(db_path)) else "/tmp", "visitors.db")

def init_visitor_db():
    try:
        conn = sqlite3.connect(VISITOR_DB)
        conn.execute("CREATE TABLE IF NOT EXISTS visitors (id INTEGER PRIMARY KEY, count INTEGER DEFAULT 0)")
        conn.execute("INSERT OR IGNORE INTO visitors (id, count) VALUES (1, 0)")
        conn.commit()
        conn.close()
    except Exception as e:
        print(f"Visitor DB init warning: {e}")

def get_visitor_count():
    try:
        conn = sqlite3.connect(VISITOR_DB)
        cursor = conn.cursor()
        cursor.execute("SELECT count FROM visitors WHERE id = 1")
        row = cursor.fetchone()
        conn.close()
        return row[0] if row else 0
    except Exception:
        return 0

def increment_visitor_count():
    try:
        conn = sqlite3.connect(VISITOR_DB)
        conn.execute("UPDATE visitors SET count = count + 1 WHERE id = 1")
        conn.commit()
        conn.close()
    except Exception as e:
        print(f"Visitor increment warning: {e}")

init_visitor_db()

STATUS_MAP = {
    1: {"text": "ناجح دور أول", "passed": True},
    2: {"text": "راسب دور أول", "passed": False},
    3: {"text": "دور ثان", "passed": False},
    4: {"text": "ناجح دور ثان", "passed": True},
    5: {"text": "راسب دور ثان", "passed": False},
    6: {"text": "راسب", "passed": False},
    7: {"text": "غياب", "passed": False},
    8: {"text": "ناجح", "passed": True}
}

@app.get("/api/search")
def search(q: str = Query(..., min_length=1)):
    q_stripped = q.strip()
    if not q_stripped:
        return {"results": []}

    conn = sqlite3.connect(db_path)
    # Configure rows to be dictionaries
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()

    results = []
    
    # Check if input is a seating number (all digits)
    if q_stripped.isdigit():
        seating_no = int(q_stripped)
        cursor.execute(
            "SELECT seating_no, name, degree, status FROM students WHERE seating_no = ? LIMIT 1",
            (seating_no,)
        )
        rows = cursor.fetchall()
    else:
        words = q_stripped.split()
        if len(words) > 1:
            conditions = " AND ".join(["name LIKE ?" for _ in words])
            params = ["%" + w + "%" for w in words]
            cursor.execute(
                f"SELECT seating_no, name, degree, status FROM students WHERE {conditions} LIMIT 50",
                params
            )
        else:
            cursor.execute(
                "SELECT seating_no, name, degree, status FROM students WHERE name LIKE ? LIMIT 50",
                ("%" + q_stripped + "%",)
            )
        rows = cursor.fetchall()

    conn.close()

    for row in rows:
        status_info = STATUS_MAP.get(row["status"], {"text": "غير معروف", "passed": False})
        percentage = round((row["degree"] / 320) * 100, 2)
        results.append({
            "seating_no": row["seating_no"],
            "name": row["name"],
            "degree": row["degree"],
            "percentage": percentage,
            "status_text": status_info["text"],
            "passed": status_info["passed"]
        })

    return {"results": results}

@app.get("/")
def home():
    html_path = os.path.join(os.path.dirname(__file__), "..", "index.html")
    return FileResponse(html_path)

@app.get("/api/visitors")
def visitors():
    increment_visitor_count()
    count = get_visitor_count()
    return {"count": count}

@app.get("/api/health")
def health():
    db_exists = os.path.exists(db_path)
    return {
        "status": "healthy",
        "database_found": db_exists,
        "database_size_mb": round(os.path.getsize(db_path) / (1024 * 1024), 2) if db_exists else 0
    }
