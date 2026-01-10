import sqlite3
from datetime import datetime
import json

class JAIMemory:
    def __init__(self, db_path="jai_memory.db"):
        self.conn = sqlite3.connect(db_path, check_same_thread=False)  # Allow multi-threading
        self.cursor = self.conn.cursor()
        self._create_tables()

    def _create_tables(self):
        self.cursor.execute('''
            CREATE TABLE IF NOT EXISTS short_term (
                id INTEGER PRIMARY KEY,
                timestamp TEXT,
                content TEXT
            )
        ''')
        self.cursor.execute('''
            CREATE TABLE IF NOT EXISTS long_term (
                id INTEGER PRIMARY KEY,
                key TEXT UNIQUE,
                value TEXT,
                timestamp TEXT,
                importance REAL
            )
        ''')
        self.conn.commit()

    def add_short_term(self, content):
        timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        # If content is a dict, serialize to JSON
        if isinstance(content, dict):
            content = json.dumps(content)
        self.cursor.execute("INSERT INTO short_term (timestamp, content) VALUES (?, ?)", (timestamp, content))
        self.conn.commit()
        return self.cursor.lastrowid

    def get_short_term(self, limit=10):
        self.cursor.execute("SELECT * FROM short_term ORDER BY timestamp DESC LIMIT ?", (limit,))
        results = []
        for row in self.cursor.fetchall():
            try:
                # Try to deserialize content as JSON
                content = json.loads(row[2])
            except json.JSONDecodeError:
                content = row[2]  # Fallback to raw string
            results.append({"id": row[0], "timestamp": row[1], "content": content})
        return results

    def remember_long_term(self, key, value, importance=0.5):
        timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        try:
            self.cursor.execute("INSERT INTO long_term (key, value, timestamp, importance) VALUES (?, ?, ?, ?)",
                              (key, value, timestamp, importance))
            self.conn.commit()
            return self.cursor.lastrowid
        except sqlite3.IntegrityError:
            return False  # Key already exists

    def update_long_term(self, key, new_value):
        self.cursor.execute("UPDATE long_term SET value = ?, timestamp = ? WHERE key = ?",
                          (new_value, datetime.now().strftime('%Y-%m-%d %H:%M:%S'), key))
        self.conn.commit()
        return self.cursor.rowcount > 0

    def forget_long_term(self, key):
        self.cursor.execute("DELETE FROM long_term WHERE key = ?", (key,))
        self.conn.commit()
        return self.cursor.rowcount > 0

    def recall_long_term(self, key):
        self.cursor.execute("SELECT value FROM long_term WHERE key = ?", (key,))
        result = self.cursor.fetchone()
        return result[0] if result else None

    def get_long_term(self, min_importance=0.0):
        self.cursor.execute("SELECT key, value, timestamp, importance FROM long_term WHERE importance >= ? ORDER BY importance DESC",
                          (min_importance,))
        return [{"key": row[0], "value": row[1], "timestamp": row[2], "importance": row[3]} for row in self.cursor.fetchall()]

    def forget_short_term(self, short_term_id):
        self.cursor.execute("DELETE FROM short_term WHERE id = ?", (short_term_id,))
        self.conn.commit()
        return self.cursor.rowcount > 0

    def search_memories(self, keyword):
        # Search long-term memory for keyword matches in key or value
        self.cursor.execute(
            "SELECT key, value FROM long_term WHERE key LIKE ? OR value LIKE ?", 
            (f"%{keyword}%", f"%{keyword}%")
        )
        results = [{"key": row[0], "value": row[1]} for row in self.cursor.fetchall()]
        return results

    def __del__(self):
        self.conn.close()
