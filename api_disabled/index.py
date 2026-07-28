from fastapi import FastAPI, Query
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from supabase import create_client
import os

app = FastAPI(title="High School Exam Results API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

SUPABASE_URL = os.environ.get("SUPABASE_URL")
SUPABASE_KEY = os.environ.get("SUPABASE_KEY")

if not SUPABASE_URL or not SUPABASE_KEY:
    raise RuntimeError("SUPABASE_URL and SUPABASE_KEY must be set")

supabase = create_client(SUPABASE_URL, SUPABASE_KEY)

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

def format_results(rows):
    results = []
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
    return results

@app.get("/api/search")
def search(q: str = Query(..., min_length=1)):
    q_stripped = q.strip()
    if not q_stripped:
        return {"results": []}

    if q_stripped.isdigit():
        seating_no = int(q_stripped)
        response = supabase.table("students").select("*").eq("seating_no", seating_no).limit(1).execute()
    else:
        words = q_stripped.split()
        if len(words) > 1:
            query = supabase.table("students").select("*")
            for w in words:
                query = query.ilike("name", f"%{w}%")
            response = query.limit(50).execute()
        else:
            response = supabase.table("students").select("*").ilike("name", f"%{q_stripped}%").limit(50).execute()

    return {"results": format_results(response.data)}

@app.get("/")
def home():
    html_path = os.path.join(os.path.dirname(__file__), "..", "index.html")
    return FileResponse(html_path)

@app.get("/api/visitors")
def visitors():
    data = supabase.table("visitors").select("count").eq("id", 1).execute()
    current = data.data[0]["count"] if data.data else 0
    supabase.table("visitors").update({"count": current + 1}).eq("id", 1).execute()
    return {"count": current + 1}

@app.get("/api/health")
def health():
    return {"status": "healthy", "database": "supabase"}