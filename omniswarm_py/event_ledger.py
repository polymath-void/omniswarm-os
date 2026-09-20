import sqlite3
import json
import time

class EventLedger:
    def __init__(self, db_path: str):
        self.db_path = db_path
        self._init_table()

    def _get_connection(self):
        return sqlite3.connect(self.db_path)

    def _init_table(self):
        conn = self._get_connection()
        cursor = conn.cursor()
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS os_events (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                timestamp REAL,
                event_type TEXT,
                payload TEXT
            )
        """)
        conn.commit()
        conn.close()

    def log_event(self, event_type: str, payload: dict):
        conn = self._get_connection()
        cursor = conn.cursor()
        cursor.execute(
            "INSERT INTO os_events (timestamp, event_type, payload) VALUES (?, ?, ?)",
            (time.time(), event_type, json.dumps(payload))
        )
        conn.commit()
        conn.close()

    def query_events_since(self, since_timestamp: float) -> list:
        conn = self._get_connection()
        cursor = conn.cursor()
        cursor.execute(
            "SELECT timestamp, event_type, payload FROM os_events WHERE timestamp > ? ORDER BY timestamp ASC",
            (since_timestamp,)
        )
        rows = cursor.fetchall()
        conn.close()
        
        events = []
        for ts, event_type, payload_str in rows:
            events.append({
                "timestamp": ts,
                "event_type": event_type,
                "payload": json.loads(payload_str)
            })
        return events
