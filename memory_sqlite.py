import sqlite3, os, json, threading
from datetime import datetime

_DB_LOCK = threading.RLock()
_BASE_DIR = os.path.dirname(os.path.abspath(__file__))
_DATA_DIR = os.path.join(_BASE_DIR, 'data')
DB_PATH = os.path.join(_DATA_DIR, 'jai_memory.db')

def _connect():
    conn = sqlite3.connect(DB_PATH, check_same_thread=False)
    conn.row_factory = sqlite3.Row
    return conn

def init_db(db_path=None):
    global DB_PATH
    with _DB_LOCK:
        if db_path:
            DB_PATH = db_path
        os.makedirs(os.path.dirname(DB_PATH), exist_ok=True)
        conn = _connect()
        try:
            cur = conn.cursor()
            cur.execute('PRAGMA journal_mode=WAL;')
            cur.execute('''
                CREATE TABLE IF NOT EXISTS users (
                    user_id TEXT PRIMARY KEY,
                    language TEXT,
                    theme TEXT,
                    created_at TEXT NOT NULL,
                    updated_at TEXT NOT NULL
                )
            ''')
            cur.execute('''
                CREATE TABLE IF NOT EXISTS preferences (
                    user_id TEXT PRIMARY KEY,
                    data TEXT NOT NULL,
                    updated_at TEXT NOT NULL,
                    FOREIGN KEY(user_id) REFERENCES users(user_id) ON DELETE CASCADE
                )
            ''')
            cur.execute('''
                CREATE TABLE IF NOT EXISTS sessions (
                    session_id TEXT PRIMARY KEY,
                    user_id TEXT NOT NULL,
                    started_at TEXT NOT NULL,
                    FOREIGN KEY(user_id) REFERENCES users(user_id) ON DELETE CASCADE
                )
            ''')
            cur.execute('''
                CREATE TABLE IF NOT EXISTS messages (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    session_id TEXT,
                    user_id TEXT NOT NULL,
                    role TEXT NOT NULL CHECK(role IN ('user','assistant','system')),
                    content TEXT NOT NULL,
                    timestamp TEXT NOT NULL,
                    FOREIGN KEY(user_id) REFERENCES users(user_id)
                )
            ''')
            conn.commit()
        finally:
            conn.close()

def _ensure_user(user_id):
    now = datetime.utcnow().isoformat() + 'Z'
    with _DB_LOCK:
        conn = _connect()
        try:
            conn.execute('''
                INSERT OR IGNORE INTO users(user_id, language, theme, created_at, updated_at)
                VALUES (?, NULL, NULL, ?, ?)
            ''', (user_id, now, now))
            conn.commit()
        finally:
            conn.close()

def _ensure_session(session_id, user_id):
    now = datetime.utcnow().isoformat() + 'Z'
    with _DB_LOCK:
        conn = _connect()
        try:
            conn.execute('''
                INSERT OR IGNORE INTO sessions(session_id, user_id, started_at)
                VALUES (?, ?, ?)
            ''', (session_id, user_id, now))
            conn.commit()
        finally:
            conn.close()

def store_message(user_id, role, content, session_id=None, timestamp=None):
    if not user_id or not role:
        return
    ts = timestamp or (datetime.utcnow().isoformat() + 'Z')
    sid = session_id or 'default'
    _ensure_user(user_id)
    _ensure_session(sid, user_id)
    with _DB_LOCK:
        conn = _connect()
        try:
            conn.execute('''
                INSERT INTO messages(session_id, user_id, role, content, timestamp)
                VALUES (?, ?, ?, ?, ?)
            ''', (sid, user_id, role, content or '', ts))
            conn.commit()
        finally:
            conn.close()

def get_recent_messages(user_id, session_id=None, limit=20):
    with _DB_LOCK:
        conn = _connect()
        try:
            if session_id:
                rows = conn.execute('''
                    SELECT role, content, timestamp FROM messages
                    WHERE user_id=? AND session_id=?
                    ORDER BY id DESC LIMIT ?
                ''', (user_id, session_id, int(limit))).fetchall()
            else:
                rows = conn.execute('''
                    SELECT role, content, timestamp FROM messages
                    WHERE user_id=?
                    ORDER BY id DESC LIMIT ?
                ''', (user_id, int(limit))).fetchall()
            return [dict(r) for r in rows][::-1]
        finally:
            conn.close()

def upsert_user_profile(user_id, language=None, theme=None):
    _ensure_user(user_id)
    now = datetime.utcnow().isoformat() + 'Z'
    with _DB_LOCK:
        conn = _connect()
        try:
            conn.execute(
                'UPDATE users SET language=COALESCE(?,language), theme=COALESCE(?,theme), updated_at=? WHERE user_id=?',
                (language, theme, now, user_id)
            )
            conn.commit()
        finally:
            conn.close()

def update_user_preferences(user_id, preferences: dict):
    _ensure_user(user_id)
    now = datetime.utcnow().isoformat() + 'Z'
    data = json.dumps(preferences or {})
    with _DB_LOCK:
        conn = _connect()
        try:
            conn.execute('''
                INSERT INTO preferences(user_id, data, updated_at)
                VALUES (?, ?, ?)
                ON CONFLICT(user_id) DO UPDATE SET data=excluded.data, updated_at=excluded.updated_at
            ''', (user_id, data, now))
            conn.commit()
        finally:
            conn.close()

def get_user_profile(user_id):
    with _DB_LOCK:
        conn = _connect()
        try:
            u = conn.execute('SELECT * FROM users WHERE user_id=?', (user_id,)).fetchone()
            p = conn.execute('SELECT data FROM preferences WHERE user_id=?', (user_id,)).fetchone()
            return {
                'user_id': user_id,
                'language': (u['language'] if u else None),
                'theme': (u['theme'] if u else None),
                'preferences': (json.loads(p['data']) if p and p['data'] else {}),
            }
        finally:
            conn.close()
