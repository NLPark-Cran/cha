"""
内存缓存管理 - 全局共享数据
"""

from typing import Dict, List, Optional
from datetime import datetime
import threading


class DataCache:
    """线程安全的内存数据缓存"""

    def __init__(self):
        self._lock = threading.RLock()
        self._stocks: List[Dict] = []
        self._index_data: Dict = {}
        self._last_update: Optional[str] = None
        self._history: List[Dict] = []  # 日内历史点位
        self._max_history = 480  # 最多保存480个数据点 (约4小时，每30秒一个)

    def update(self, stocks: List[Dict], index_data: Dict):
        with self._lock:
            self._stocks = stocks
            self._index_data = index_data
            self._last_update = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

            # 记录历史点位
            if index_data.get("value"):
                self._history.append({
                    "time": self._last_update,
                    "value": index_data["value"],
                    "change_pct": index_data.get("change_pct", 0),
                })
                # 限制历史数据长度
                if len(self._history) > self._max_history:
                    self._history = self._history[-self._max_history:]

    def get_stocks(self) -> List[Dict]:
        with self._lock:
            return list(self._stocks)

    def get_index_data(self) -> Dict:
        with self._lock:
            return dict(self._index_data)

    def get_last_update(self) -> Optional[str]:
        with self._lock:
            return self._last_update

    def get_history(self) -> List[Dict]:
        with self._lock:
            return list(self._history)

    def get_stock_by_code(self, code: str) -> Optional[Dict]:
        with self._lock:
            for s in self._stocks:
                if s.get("code") == code:
                    return dict(s)
            return None


# 全局缓存实例
cache = DataCache()
