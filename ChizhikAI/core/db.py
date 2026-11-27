import json
import os
import sqlite3


class Database:
    """Small SQLite chat store retained for compatibility with existing user data."""

    def __init__(self):
        db_path = os.path.join(os.path.expanduser("~"), ".chizhik_ai", "chats.db")
        os.makedirs(os.path.dirname(db_path), exist_ok=True)
        self.conn = sqlite3.connect(db_path, check_same_thread=False)
        self.conn.execute("PRAGMA foreign_keys = ON")
        self._create_tables()

    def _create_tables(self):
        self.conn.execute(
            "CREATE TABLE IF NOT EXISTS chats ("
            "id INTEGER PRIMARY KEY AUTOINCREMENT, title TEXT NOT NULL, "
            "created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP)"
        )
        self.conn.execute(
            "CREATE TABLE IF NOT EXISTS messages ("
            "id INTEGER PRIMARY KEY AUTOINCREMENT, chat_id INTEGER NOT NULL, "
            "role TEXT NOT NULL, content TEXT NOT NULL, media_path TEXT, "
            "timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP, "
            "FOREIGN KEY(chat_id) REFERENCES chats(id) ON DELETE CASCADE)"
        )
        self.conn.commit()

    def create_chat(self, title="Новый чат"):
        cursor = self.conn.execute("INSERT INTO chats (title) VALUES (?)", (title,))
        self.conn.commit()
        return cursor.lastrowid

    def get_chats(self):
        return self.conn.execute("SELECT id, title FROM chats ORDER BY created_at DESC, id DESC").fetchall()

    def add_message(self, chat_id, role, content, media_path=None):
        self.conn.execute(
            "INSERT INTO messages (chat_id, role, content, media_path) VALUES (?, ?, ?, ?)",
            (chat_id, role, content, media_path),
        )
        self.conn.commit()

    def get_messages(self, chat_id):
        return self.conn.execute(
            "SELECT role, content, media_path FROM messages WHERE chat_id=? ORDER BY timestamp, id",
            (chat_id,),
        ).fetchall()

    def delete_chat(self, chat_id):
        self.conn.execute("DELETE FROM messages WHERE chat_id=?", (chat_id,))
        self.conn.execute("DELETE FROM chats WHERE id=?", (chat_id,))
        self.conn.commit()

    def close(self):
        self.conn.close()
