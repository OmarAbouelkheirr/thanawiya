-- Create students table
CREATE TABLE students (
    seating_no INTEGER PRIMARY KEY,
    name TEXT NOT NULL,
    degree REAL NOT NULL,
    status INTEGER NOT NULL
);

-- Create index on name for fast search
CREATE INDEX idx_students_name ON students USING btree (name);

-- Create visitors table for counting
CREATE TABLE visitors (
    id INTEGER PRIMARY KEY DEFAULT 1,
    count INTEGER DEFAULT 0
);

-- Insert initial visitor row
INSERT INTO visitors (id, count) VALUES (1, 0);