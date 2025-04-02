import sqlite3
from datetime import datetime

DB_FILE = "health_data.db"

def init_db():
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS health_entry (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            timestamp TEXT,
            weight REAL,
            blood_sugar REAL,
            sleep_hours REAL,
            mood TEXT,
            notes TEXT
        )
    ''')
    conn.commit()
    conn.close()

def insert_entry(entry):
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    cursor.execute('''
        INSERT INTO health_entry (timestamp, weight, blood_sugar, sleep_hours, mood, notes)
        VALUES (?, ?, ?, ?, ?, ?)
    ''', (
        entry['timestamp'],
        entry['weight'],
        entry['blood_sugar'],
        entry['sleep_hours'],
        entry['mood'],
        entry['notes']
    ))
    conn.commit()
    conn.close()

def get_all_entries():
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM health_entry ORDER BY timestamp")
    rows = cursor.fetchall()
    conn.close()
    return rows