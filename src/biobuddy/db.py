"""
Database module for SQLite operations.
"""
import sqlite3


_all_ = ['Database', 'get_db']


class Database:
    def __init__(self, db_path):
        self.db_path = db_path
        self._conn = sqlite3.connect(self.db_path)
        # Enable Foreign Key support (SQLite has it off by default)
        self._conn.execute("PRAGMA foreign_keys = ON;")
        self._conn.row_factory = sqlite3.Row

    def close(self):
        self._conn.close()

    @property
    def connection(self):
        return self._conn

    @property
    def cursor(self):
        return self._conn.cursor()

    def execute(self, query, params=None):
        cursor = self._conn.cursor()
        if params:
            cursor.execute(query, params)
        else:
            cursor.execute(query)
        self._conn.commit()
        return cursor

    def execute_script(self, script):
        cursor = self._conn.cursor()
        cursor.executescript(script)
        self._conn.commit()
        return cursor

    def select_one(self, query, params=None):
        cursor = self._conn.cursor()
        if params:
            cursor.execute(query, params)
        else:
            cursor.execute(query)
        return cursor.fetchone()


def get_db(db_path='biobuddy.db') -> Database:
    """Helper function to get a Database instance."""
    return Database(db_path)
