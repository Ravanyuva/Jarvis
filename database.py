import sqlite3
import datetime
import os

class JarvisDB:
    def __init__(self, db_path="jarvis.db"):
        self.db_path = db_path
        self.conn = None
        self._connect()
        self._init_tables()

    def _connect(self):
        try:
            self.conn = sqlite3.connect(self.db_path, check_same_thread=False)
            self.conn.row_factory = sqlite3.Row
            print("[DB] Connected to SQLite memory.")
        except Exception as e:
            print(f"[DB ERROR] Connection failed: {e}")

    def _init_tables(self):
        if not self.conn:
            return
        
        cursor = self.conn.cursor()
        
        # History
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS history (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                timestamp TEXT,
                user_text TEXT,
                intent TEXT,
                response TEXT
            )
        ''')
        
        # Notes
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS notes (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                timestamp TEXT,
                note TEXT
            )
        ''')
        
        # Users
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS users (
                username TEXT PRIMARY KEY,
                password TEXT,
                email TEXT,
                subscription TEXT,
                created_at TEXT
            )
        ''')
        
        # Preferences (Key-Value Store for Learning)
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS preferences (
                key TEXT PRIMARY KEY,
                value TEXT,
                updated_at TEXT
            )
        ''')

        # Skills / Routines (New)
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS skills (
                name TEXT PRIMARY KEY,
                steps TEXT,

                created_at TEXT
            )
        ''')
        
        self.conn.commit()

    # --- Skills Management ---
    def add_skill(self, name, steps):
        if not self.conn: return False
        try:
            import json
            steps_json = json.dumps(steps)
            with self.conn:
                self.conn.execute('INSERT OR REPLACE INTO skills (name, steps, created_at) VALUES (?, ?, ?)',
                                  (name.lower(), steps_json, datetime.datetime.now().isoformat()))
            return True
        except Exception as e:
            print(f"[DB ERROR] Add Skill: {e}")
            return False

    def get_skill(self, name):
        if not self.conn: return None
        try:
            import json
            cursor = self.conn.cursor()
            cursor.execute('SELECT steps FROM skills WHERE name = ?', (name.lower(),))
            row = cursor.fetchone()
            if row:
                return json.loads(row['steps'])
            return None
        except Exception:
            return None


    def log_interaction(self, user_text, intent_type, jarvis_response):
        if not self.conn: return
        try:
            with self.conn:
                self.conn.execute('''
                    INSERT INTO history (timestamp, user_text, intent, response)
                    VALUES (?, ?, ?, ?)
                ''', (datetime.datetime.now().isoformat(), user_text, intent_type, jarvis_response))
        except Exception as e:
            print(f"[DB ERROR] Log interaction: {e}")

    def get_recent_history(self, limit=5):
        if not self.conn: return []
        try:
            cursor = self.conn.cursor()
            cursor.execute('SELECT * FROM history ORDER BY id DESC LIMIT ?', (limit,))
            return [dict(row) for row in cursor.fetchall()]
        except Exception:
            return []

    def save_note(self, text):
        if not self.conn: return False
        try:
            with self.conn:
                self.conn.execute('INSERT INTO notes (timestamp, note) VALUES (?, ?)', 
                                  (datetime.datetime.now().isoformat(), text))
            return True
        except Exception as e:
            print(f"[DB ERROR] Save note: {e}")
            return False

    def get_notes(self, limit=5):
        if not self.conn: return []
        try:
            cursor = self.conn.cursor()
            cursor.execute('SELECT note FROM notes ORDER BY id DESC LIMIT ?', (limit,))
            return [row['note'] for row in cursor.fetchall()]
        except Exception:
            return []

    # --- Preference / Learning ---
    def set_preference(self, key, value):
        if not self.conn: return False
        try:
            with self.conn:
                self.conn.execute('''
                    INSERT INTO preferences (key, value, updated_at) 
                    VALUES (?, ?, ?)
                    ON CONFLICT(key) DO UPDATE SET value=excluded.value, updated_at=excluded.updated_at
                ''', (key, value, datetime.datetime.now().isoformat()))
            return True
        except Exception as e:
            print(f"[DB ERROR] Set preference: {e}")
            return False

    def get_preference(self, key):
        if not self.conn: return None
        try:
            cursor = self.conn.cursor()
            cursor.execute('SELECT value FROM preferences WHERE key = ?', (key,))
            row = cursor.fetchone()
            return row['value'] if row else None
        except Exception:
            return None

    # --- User Management (Legacy Support) ---
    def create_user(self, username, password_hash, email=None):
        if not self.conn: return False
        try:
            with self.conn:
                self.conn.execute('INSERT INTO users (username, password, email, subscription, created_at) VALUES (?, ?, ?, ?, ?)',
                                  (username, password_hash, email, "FREE", datetime.datetime.now().isoformat()))
            return True
        except sqlite3.IntegrityError:
            return False # Already exists
        except Exception as e:
            print(f"[DB ERROR] Create user: {e}")
            return False

# Global instance
db = JarvisDB()
