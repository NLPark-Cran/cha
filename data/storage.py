"""
SQLite 历史数据持久化
"""

import sqlite3
import json
from typing import List, Dict
from datetime import datetime
import os
import config


class Storage:
    """SQLite 数据持久化"""

    def __init__(self, db_path: str = config.DB_PATH):
        self.db_path = db_path
        os.makedirs(os.path.dirname(db_path), exist_ok=True)
        self._init_db()

    def _init_db(self):
        """初始化数据库表"""
        with sqlite3.connect(self.db_path) as conn:
            conn.execute("""
                CREATE TABLE IF NOT EXISTS index_history (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    date TEXT NOT NULL,
                    time TEXT NOT NULL,
                    value REAL NOT NULL,
                    change_pct REAL,
                    change_amt REAL,
                    up_count INTEGER,
                    down_count INTEGER,
                    flat_count INTEGER,
                    total_volume REAL,
                    total_turnover REAL,
                    UNIQUE(date, time)
                )
            """)
            conn.execute("""
                CREATE TABLE IF NOT EXISTS stock_history (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    date TEXT NOT NULL,
                    time TEXT NOT NULL,
                    code TEXT NOT NULL,
                    name TEXT,
                    price REAL,
                    change_pct REAL,
                    change_amt REAL,
                    volume REAL,
                    sector TEXT,
                    UNIQUE(date, time, code)
                )
            """)
            conn.execute("""
                CREATE INDEX IF NOT EXISTS idx_index_date ON index_history(date)
            """)
            conn.execute("""
                CREATE INDEX IF NOT EXISTS idx_stock_date ON stock_history(date, code)
            """)
            conn.commit()

    def save_index_snapshot(self, index_data: Dict):
        """保存指数快照"""
        now = datetime.now()
        date_str = now.strftime("%Y-%m-%d")
        time_str = now.strftime("%H:%M:%S")
        try:
            with sqlite3.connect(self.db_path) as conn:
                conn.execute("""
                    INSERT OR REPLACE INTO index_history
                    (date, time, value, change_pct, change_amt, up_count, down_count, flat_count, total_volume, total_turnover)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    date_str, time_str,
                    index_data.get("value", 0),
                    index_data.get("change_pct", 0),
                    index_data.get("change_amt", 0),
                    index_data.get("up_count", 0),
                    index_data.get("down_count", 0),
                    index_data.get("flat_count", 0),
                    index_data.get("total_volume", 0),
                    index_data.get("total_turnover", 0),
                ))
                conn.commit()
        except Exception as e:
            print(f"[Storage] Save index snapshot failed: {e}")

    def save_stocks_snapshot(self, stocks: List[Dict]):
        """保存成分股快照"""
        now = datetime.now()
        date_str = now.strftime("%Y-%m-%d")
        time_str = now.strftime("%H:%M:%S")
        try:
            with sqlite3.connect(self.db_path) as conn:
                for stock in stocks:
                    conn.execute("""
                        INSERT OR REPLACE INTO stock_history
                        (date, time, code, name, price, change_pct, change_amt, volume, sector)
                        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                    """, (
                        date_str, time_str,
                        stock.get("code", ""),
                        stock.get("name", ""),
                        stock.get("price", 0),
                        stock.get("change_pct", 0),
                        stock.get("change_amt", 0),
                        stock.get("volume", 0),
                        stock.get("sector", ""),
                    ))
                conn.commit()
        except Exception as e:
            print(f"[Storage] Save stocks snapshot failed: {e}")

    def get_index_history(self, date: str) -> List[Dict]:
        """获取某日的指数历史数据"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                conn.row_factory = sqlite3.Row
                rows = conn.execute(
                    "SELECT * FROM index_history WHERE date = ? ORDER BY time",
                    (date,)
                ).fetchall()
                return [dict(row) for row in rows]
        except Exception as e:
            print(f"[Storage] Query failed: {e}")
            return []

    def get_stock_history(self, code: str, date: str) -> List[Dict]:
        """获取某只股票的某日历史数据"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                conn.row_factory = sqlite3.Row
                rows = conn.execute(
                    "SELECT * FROM stock_history WHERE code = ? AND date = ? ORDER BY time",
                    (code, date)
                ).fetchall()
                return [dict(row) for row in rows]
        except Exception as e:
            print(f"[Storage] Query failed: {e}")
            return []


# 全局单例
storage = Storage()
