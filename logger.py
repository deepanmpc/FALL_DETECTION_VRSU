import csv
import sqlite3
import os
import time

CSV_FILE = 'fall_events.csv'
DB_FILE = 'fall_events.db'

def init_db():
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS fall_events (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            timestamp REAL,
            person_id INTEGER,
            event_type TEXT,
            angle_degrees REAL,
            confidence_score REAL,
            duration_seconds REAL,
            frame_number INTEGER
        )
    ''')
    conn.commit()
    conn.close()

    if not os.path.exists(CSV_FILE):
        with open(CSV_FILE, 'w', newline='') as f:
            writer = csv.writer(f)
            writer.writerow(['timestamp', 'person_id', 'event_type', 'angle_degrees', 'confidence_score', 'duration_seconds', 'frame_number'])

init_db()

def log_event(timestamp, person_id, event_type, angle_degrees, confidence_score, duration_seconds, frame_number):
    """Logs a state transition event to both CSV and SQLite database."""
    # CSV
    with open(CSV_FILE, 'a', newline='') as f:
        writer = csv.writer(f)
        writer.writerow([timestamp, person_id, event_type, angle_degrees, confidence_score, duration_seconds, frame_number])
        
    # SQLite
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    cursor.execute('''
        INSERT INTO fall_events (timestamp, person_id, event_type, angle_degrees, confidence_score, duration_seconds, frame_number)
        VALUES (?, ?, ?, ?, ?, ?, ?)
    ''', (timestamp, person_id, event_type, angle_degrees, confidence_score, duration_seconds, frame_number))
    conn.commit()
    conn.close()

def query_recent_falls(hours=24):
    """Returns fall events from the last specified hours."""
    cutoff_time = time.time() - (hours * 3600)
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    # Assuming 'timestamp' in the db is a unix epoch timestamp
    cursor.execute('''
        SELECT * FROM fall_events 
        WHERE timestamp >= ?
        ORDER BY timestamp DESC
    ''', (cutoff_time,))
    results = cursor.fetchall()
    conn.close()
    return results
