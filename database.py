import sqlite3
import pandas as pd

class DatabaseManager:
    def __init__(self, db_name='trading_journal.db'):
        self.db_name = db_name
        self.init_db()

    def get_connection(self):
        return sqlite3.connect(self.db_name)

    def init_db(self):
        """Tạo bảng nếu chưa có"""
        query = """
        CREATE TABLE IF NOT EXISTS trades (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            date TEXT, asset TEXT, side TEXT, 
            entry REAL, exit REAL, quantity REAL, 
            pl REAL, notes TEXT
        )
        """
        with self.get_connection() as conn:
            conn.execute(query)

    def add_trade(self, date, asset, side, entry, exit_p, qty, pl, notes):
        query = "INSERT INTO trades (date, asset, side, entry, exit, quantity, pl, notes) VALUES (?,?,?,?,?,?,?,?)"
        with self.get_connection() as conn:
            conn.execute(query, (date, asset, side, entry, exit_p, qty, pl, notes))

    def get_all_trades(self):
        return pd.read_sql_query("SELECT * FROM trades ORDER BY date DESC", self.get_connection())

    def get_stats(self):
        query = "SELECT SUM(pl) as total_pl, COUNT(*) as count FROM trades"
        with self.get_connection() as conn:
            return pd.read_sql_query(query, conn)
