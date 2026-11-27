import sqlite3
import os

class Database:
    def __init__(self):
        db_path = os.path.join(os.path.expanduser("~"), ".chizhik_ai", "chats.db")
        os.makedirs(os.path.dirname(db_path), exist_ok=True)
        self.conn = sqlite3.connect(db_path, check_same_thread=False)
        self.cursor = self.conn.cursor()
        self._create_tables()

    def _create_tables(self):
        self.cursor.execute("CREATE TABLE IF NOT EXISTS chats (id INTEGER PRIMARY KEY AUTOINCREMENT, title TEXT NOT NULL, created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP)")
        self.cursor.execute("CREATE TABLE IF NOT EXISTS messages (id INTEGER PRIMARY KEY AUTOINCREMENT, chat_id INTEGER, role TEXT, content TEXT, media_path TEXT, timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP, FOREIGN KEY(chat_id) REFERENCES chats(id))")
        self.conn.commit()

    def create_chat(self, title="Новый чат"):
        self.cursor.execute("INSERT INTO chats (title) VALUES (?)", (title,))
        self.conn.commit()
        return self.cursor.lastrowid

    def get_chats(self):
        self.cursor.execute("SELECT id, title FROM chats ORDER BY created_at DESC")
        return self.cursor.fetchall()

    def add_message(self, chat_id, role, content, media_path=None):
        self.cursor.execute("INSERT INTO messages (chat_id, role, content, media_path) VALUES (?, ?, ?, ?)", (chat_id, role, content, media_path))
        self.conn.commit()

    def get_messages(self, chat_id):
        self.cursor.execute("SELECT role, content, media_path FROM messages WHERE chat_id=? ORDER BY timestamp ASC", (chat_id,))
        return self.cursor.fetchall()

    def delete_chat(self, chat_id):
        self.cursor.execute("DELETE FROM messages WHERE chat_id=?", (chat_id,))
        self.cursor.execute("DELETE FROM chats WHERE id=?", (chat_id,))
        self.conn.commit()