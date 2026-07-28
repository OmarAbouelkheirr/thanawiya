from fastapi import FastAPI, Query
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
import sqlite3
import os

app = FastAPI(title="High School Exam Results API")

# Enable CORS for local testing
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Resolve SQLite database path
current_dir = os.path.dirname(os.path.abspath(__file__))
db_path = os.path.join(current_dir, "..", "results.db")
if not os.path.exists(db_path):
    db_path = os.path.join(current_dir, "results.db")

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
        # Prefix search by name (utilizes idx_name)
        # Using LIKE 'query%'
        cursor.execute(
            "SELECT seating_no, name, degree, status FROM students WHERE name LIKE ? LIMIT 50",
            (q_stripped + "%",)
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

@app.get("/api/health")
def health():
    db_exists = os.path.exists(db_path)
    return {
        "status": "healthy",
        "database_found": db_exists,
        "database_size_mb": round(os.path.getsize(db_path) / (1024 * 1024), 2) if db_exists else 0
    }
