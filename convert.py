import sqlite3
import pandas as pd
import os

excel_file = "نتيجة ثانوية عامة نظام حديث.xlsx"
db_file = "results.db"

if os.path.exists(db_file):
    print(f"Removing existing {db_file}...")
    os.remove(db_file)

print("Reading Excel...")
df = pd.read_excel(excel_file)

# Keep only necessary columns
expected_cols = ['seating_no', 'arabic_name', 'total_degree', 'student_case_desc']
df = df[expected_cols].copy()

df['seating_no'] = pd.to_numeric(df['seating_no'], errors='coerce').fillna(0).astype(int)
df['total_degree'] = pd.to_numeric(df['total_degree'], errors='coerce').fillna(0.0).astype(float)
df['arabic_name'] = df['arabic_name'].astype(str).str.strip()

# Clean and map status
df['student_case_desc'] = df['student_case_desc'].astype(str).str.strip()

# Map status to tiny integers
status_map = {
    "ناجح دور أول": 1,
    "راسب دور أول": 2,
    "دور ثان": 3,
    "ناجح دور ثان": 4,
    "راسب دور ثان": 5,
    "راسب": 6,
    "غياب": 7,
    "غياب كلى دور أول": 7,
    "ناجح": 8
}
df['status_code'] = df['student_case_desc'].map(status_map).fillna(0).astype(int)

# Drop student_case_desc
df = df.drop(columns=['student_case_desc'])

conn = sqlite3.connect(db_file)
cursor = conn.cursor()

# SQLite optimizations
cursor.execute("PRAGMA page_size = 4096;")
cursor.execute("PRAGMA auto_vacuum = NONE;")

cursor.execute("""
CREATE TABLE students (
    seating_no INTEGER PRIMARY KEY,
    name TEXT,
    degree REAL,
    status INTEGER
);
""")

print("Inserting data...")
df_db = df.rename(columns={'seating_no': 'seating_no', 'arabic_name': 'name', 'total_degree': 'degree', 'status_code': 'status'})
df_db.to_sql('students', conn, if_exists='append', index=False)

print("Creating index on name...")
cursor.execute("CREATE INDEX idx_name ON students(name);")

print("Vacuuming...")
cursor.execute("VACUUM;")
conn.commit()
conn.close()

size = os.path.getsize(db_file)
print(f"Database results.db generated successfully. Size: {size / (1024*1024):.2f} MB")
