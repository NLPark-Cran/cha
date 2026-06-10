"""
用户数据服务层 - 用户管理、登录记录、自定义成分股
"""

import sqlite3
from datetime import datetime
from typing import List, Dict, Optional
import config


class UserService:
    """用户数据服务"""

    def __init__(self, db_path: str = config.DB_PATH):
        self.db_path = db_path

    def _get_conn(self):
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        return conn

    # ─── 用户管理 ───

    def get_or_create_user(self, watcha_user_id: str, nickname: str = "", avatar_url: str = "") -> Dict:
        """获取或创建用户，返回用户字典"""
        with self._get_conn() as conn:
            # 尝试查找
            row = conn.execute(
                "SELECT * FROM users WHERE watcha_user_id = ?",
                (watcha_user_id,)
            ).fetchone()

            now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

            if row:
                user = dict(row)
                # 更新最后登录时间和昵称/头像
                conn.execute(
                    "UPDATE users SET last_login_at = ?, nickname = COALESCE(NULLIF(?, ''), nickname), avatar_url = COALESCE(NULLIF(?, ''), avatar_url) WHERE id = ?",
                    (now, nickname, avatar_url, user["id"])
                )
                conn.commit()
                user["last_login_at"] = now
                if nickname:
                    user["nickname"] = nickname
                if avatar_url:
                    user["avatar_url"] = avatar_url
                return user

            # 创建新用户
            cursor = conn.execute(
                "INSERT INTO users (watcha_user_id, nickname, avatar_url, created_at, last_login_at) VALUES (?, ?, ?, ?, ?)",
                (watcha_user_id, nickname, avatar_url, now, now)
            )
            conn.commit()
            return {
                "id": cursor.lastrowid,
                "watcha_user_id": watcha_user_id,
                "nickname": nickname,
                "avatar_url": avatar_url,
                "created_at": now,
                "last_login_at": now,
            }

    def get_user_by_watcha_id(self, watcha_user_id: str) -> Optional[Dict]:
        """通过观猹用户 ID 查找用户"""
        with self._get_conn() as conn:
            row = conn.execute(
                "SELECT * FROM users WHERE watcha_user_id = ?",
                (watcha_user_id,)
            ).fetchone()
            return dict(row) if row else None

    # ─── 登录记录 ───

    def record_login(self, user_id: int, ip: str = "", user_agent: str = ""):
        """记录一次登录"""
        with self._get_conn() as conn:
            conn.execute(
                "INSERT INTO login_logs (user_id, login_at, ip, user_agent) VALUES (?, ?, ?, ?)",
                (user_id, datetime.now().strftime("%Y-%m-%d %H:%M:%S"), ip, user_agent)
            )
            conn.commit()

    def get_login_history(self, user_id: int, limit: int = 20) -> List[Dict]:
        """获取用户登录历史"""
        with self._get_conn() as conn:
            rows = conn.execute(
                "SELECT * FROM login_logs WHERE user_id = ? ORDER BY login_at DESC LIMIT ?",
                (user_id, limit)
            ).fetchall()
            return [dict(row) for row in rows]

    def get_login_count(self, user_id: int) -> int:
        """获取用户总登录次数"""
        with self._get_conn() as conn:
            row = conn.execute(
                "SELECT COUNT(*) as cnt FROM login_logs WHERE user_id = ?",
                (user_id,)
            ).fetchone()
            return row["cnt"] if row else 0

    # ─── 自定义成分股 ───

    def get_user_portfolio(self, user_id: int) -> List[Dict]:
        """获取用户的自定义成分股列表"""
        with self._get_conn() as conn:
            rows = conn.execute(
                "SELECT * FROM user_portfolios WHERE user_id = ? ORDER BY added_at",
                (user_id,)
            ).fetchall()
            return [dict(row) for row in rows]

    def add_stock_to_portfolio(self, user_id: int, code: str, name: str, sector: str = "") -> bool:
        """添加股票到用户组合"""
        try:
            with self._get_conn() as conn:
                conn.execute(
                    "INSERT INTO user_portfolios (user_id, code, name, sector) VALUES (?, ?, ?, ?)",
                    (user_id, code, name, sector)
                )
                conn.commit()
                return True
        except sqlite3.IntegrityError:
            # 已存在
            return False

    def remove_stock_from_portfolio(self, user_id: int, code: str) -> bool:
        """从用户组合中移除股票"""
        with self._get_conn() as conn:
            cursor = conn.execute(
                "DELETE FROM user_portfolios WHERE user_id = ? AND code = ?",
                (user_id, code)
            )
            conn.commit()
            return cursor.rowcount > 0

    def reset_portfolio(self, user_id: int):
        """清空用户自定义组合"""
        with self._get_conn() as conn:
            conn.execute("DELETE FROM user_portfolios WHERE user_id = ?", (user_id,))
            conn.commit()

    def init_default_portfolio(self, user_id: int):
        """为用户初始化默认的 22 只成分股"""
        import config as cfg
        self.reset_portfolio(user_id)
        for code, name, sector in cfg.CONSTITUENTS:
            self.add_stock_to_portfolio(user_id, code, name, sector)

    def has_custom_portfolio(self, user_id: int) -> bool:
        """检查用户是否有自定义成分股"""
        with self._get_conn() as conn:
            row = conn.execute(
                "SELECT COUNT(*) as cnt FROM user_portfolios WHERE user_id = ?",
                (user_id,)
            ).fetchone()
            return row["cnt"] > 0


# 全局单例
user_service = UserService()
