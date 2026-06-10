"""
数据获取模块 - 使用 curl_cffi 调用东方财富 API
绕过 AKShare 的 requests 依赖，直接使用浏览器指纹请求
"""

import json
import time
from typing import Dict, List, Optional
from curl_cffi import requests as curl_requests
import config


class EastMoneyFetcher:
    """东方财富数据获取器"""

    BASE_URL = "https://push2.eastmoney.com/api/qt/clist/get"
    IMPERSONATE = "chrome120"
    TIMEOUT = 15

    def __init__(self):
        self.session = curl_requests.Session()

    def _request(self, params: dict) -> dict:
        """发送请求并返回 JSON"""
        try:
            resp = self.session.get(
                self.BASE_URL,
                params=params,
                timeout=self.TIMEOUT,
                impersonate=self.IMPERSONATE,
            )
            resp.raise_for_status()
            return resp.json()
        except Exception as e:
            print(f"[Fetcher] Request failed: {e}")
            return {}

    def fetch_all_a_stocks(self, limit: int = 6000) -> List[Dict]:
        """获取全部A股实时行情"""
        params = {
            "pn": "1",
            "pz": str(limit),
            "po": "1",
            "np": "1",
            "fltt": "2",
            "invt": "2",
            "fid": "f20",  # 按总市值排序
            "fs": "m:0+t:6,m:0+t:13,m:0+t:80,m:1+t:2,m:1+t:23",
            "fields": config.EM_FIELDS,
        }
        data = self._request(params)
        return data.get("data", {}).get("diff", []) or []

    def fetch_specific_stocks(self, codes: List[str]) -> List[Dict]:
        """获取指定股票代码的实时行情"""
        if not codes:
            return []

        # 构建secid: 0=深市, 1=沪市, 116=北交所
        secids = []
        for code in codes:
            if code.startswith("6") or code.startswith("5"):
                secids.append(f"1.{code}")
            elif code.startswith("0") or code.startswith("3") or code.startswith("2"):
                secids.append(f"0.{code}")
            elif code.startswith("4") or code.startswith("8"):
                secids.append(f"0.{code}")
            else:
                secids.append(f"0.{code}")

        # 批量接口
        url = "https://push2.eastmoney.com/api/qt/ulist.np/get"
        params = {
            "fltt": "2",
            "invt": "2",
            "fields": config.EM_FIELDS,
            "secids": ",".join(secids),
        }
        try:
            resp = self.session.get(
                url, params=params, timeout=self.TIMEOUT, impersonate=self.IMPERSONATE
            )
            resp.raise_for_status()
            data = resp.json()
            return data.get("data", {}).get("diff", []) or []
        except Exception as e:
            print(f"[Fetcher] Batch fetch failed: {e}")
            return []

    def fetch_stock_history(
        self, code: str, period: str = "daily", limit: int = 120
    ) -> List[Dict]:
        """获取个股历史K线"""
        # 判断市场
        if code.startswith("6") or code.startswith("5"):
            secid = f"1.{code}"
        else:
            secid = f"0.{code}"

        url = "https://push2his.eastmoney.com/api/qt/stock/kline/get"
        params = {
            "secid": secid,
            "fields1": "f1,f2,f3,f4,f5,f6",
            "fields2": "f51,f52,f53,f54,f55,f56,f57,f58,f59,f60,f61",
            "klt": {"daily": "101", "weekly": "102", "monthly": "103"}.get(
                period, "101"
            ),
            "fqt": "0",
            "end": "20500101",
            "lmt": str(limit),
        }
        try:
            resp = self.session.get(
                url, params=params, timeout=self.TIMEOUT, impersonate=self.IMPERSONATE
            )
            resp.raise_for_status()
            data = resp.json()
            klines = data.get("data", {}).get("klines", [])
            result = []
            for line in klines:
                parts = line.split(",")
                if len(parts) >= 6:
                    result.append(
                        {
                            "date": parts[0],
                            "open": float(parts[1]),
                            "close": float(parts[2]),
                            "high": float(parts[3]),
                            "low": float(parts[4]),
                            "volume": float(parts[5]),
                            "amount": float(parts[6]) if len(parts) > 6 else 0,
                        }
                    )
            return result
        except Exception as e:
            print(f"[Fetcher] History fetch failed for {code}: {e}")
            return []

    def parse_stock_data(self, raw: dict) -> Optional[Dict]:
        """解析单条东财原始数据为结构化字典"""
        try:
            code = raw.get("f12", "")
            if not code:
                return None
            return {
                "code": code,
                "name": raw.get("f14", ""),
                "price": self._safe_float(raw.get("f2")),
                "change_pct": self._safe_float(raw.get("f3")),
                "change_amt": self._safe_float(raw.get("f4")),
                "volume": self._safe_float(raw.get("f5")),
                "turnover": self._safe_float(raw.get("f6")),
                "amplitude": self._safe_float(raw.get("f7")),
                "turnover_rate": self._safe_float(raw.get("f8")),
                "pe": self._safe_float(raw.get("f9")),
                "volume_ratio": self._safe_float(raw.get("f10")),
                "high": self._safe_float(raw.get("f15")),
                "low": self._safe_float(raw.get("f16")),
                "open": self._safe_float(raw.get("f17")),
                "pre_close": self._safe_float(raw.get("f18")),
                "market_cap": self._safe_float(raw.get("f20")),
                "circulating_cap": self._safe_float(raw.get("f21")),
            }
        except Exception:
            return None

    @staticmethod
    def _safe_float(val):
        """安全转换为float，处理'-'等无效值"""
        if val is None or val == "-" or val == "":
            return 0.0
        try:
            return float(val)
        except (ValueError, TypeError):
            return 0.0


# 全局单例
_fetcher: Optional[EastMoneyFetcher] = None


def get_fetcher() -> EastMoneyFetcher:
    global _fetcher
    if _fetcher is None:
        _fetcher = EastMoneyFetcher()
    return _fetcher


def fetch_constituents_data() -> List[Dict]:
    """获取观猹概念股成分股的实时数据"""
    fetcher = get_fetcher()
    codes = [c[0] for c in config.CONSTITUENTS]
    raw_data = fetcher.fetch_specific_stocks(codes)
    parsed = []
    for raw in raw_data:
        item = fetcher.parse_stock_data(raw)
        if item:
            # 补充板块信息
            for code, name, sector in config.CONSTITUENTS:
                if code == item["code"]:
                    item["sector"] = sector
                    break
            parsed.append(item)
    return parsed


def fetch_stock_history(code: str, period: str = "daily", limit: int = 120) -> List[Dict]:
    """获取个股历史K线数据"""
    return get_fetcher().fetch_stock_history(code, period, limit)
