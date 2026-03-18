import sqlite3
from datetime import datetime

class Database:
    def __init__(self):
        # Створюємо підключення до локальної бази SQLite
        self.conn = sqlite3.connect('trade_bot.db', check_same_thread=False)
        self.create_tables()

    def create_tables(self):
        cursor = self.conn.cursor()
        # Таблиця для історії угод
        cursor.execute('''CREATE TABLE IF NOT EXISTS trades 
                          (id INTEGER PRIMARY KEY AUTOINCREMENT, 
                           symbol TEXT, type TEXT, entry REAL, 
                           pnl REAL, status TEXT, date TEXT)''')
        self.conn.commit()

    def log_trade(self, symbol, trade_type, entry):
        """Записує відкриття угоди."""
        cursor = self.conn.cursor()
        date = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        cursor.execute("INSERT INTO trades (symbol, type, entry, status, date) VALUES (?, ?, ?, ?, ?)",
                       (symbol, trade_type, entry, 'OPEN', date))
        self.conn.commit()

    def get_daily_stats(self):
        """Отримує статистику за останні 24 години."""
        cursor = self.conn.cursor()
        # Тут можна додати складнішу логіку підрахунку профіту
        cursor.execute("SELECT COUNT(*) FROM trades WHERE status != 'OPEN'")
        count = cursor.fetchone()[0]
        return {"count": count}