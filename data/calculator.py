"""
指数计算引擎 - 观猹概念股指计算
采用等权法，每只成分股对指数影响相同
"""

from typing import Dict, List
from datetime import datetime
import config


class IndexCalculator:
    """观猹概念股指计算器"""

    def __init__(self):
        # 基期数据: code -> price
        self.base_prices: Dict[str, float] = {}
        self.initialized = False

    def init_base_prices(self, stocks_data: List[Dict]):
        """初始化基期价格 (首次运行时)"""
        for stock in stocks_data:
            code = stock.get("code")
            pre_close = stock.get("pre_close", 0)
            price = stock.get("price", 0)
            # 使用昨收价作为基准，若无效则使用当前价
            base = pre_close if pre_close > 0 else price
            if base > 0:
                self.base_prices[code] = base
        if self.base_prices:
            self.initialized = True

    def calculate_index(self, stocks_data: List[Dict]) -> Dict:
        """
        计算观猹概念股指
        等权法: 每只成分股的收益率等权平均，再乘以基点
        """
        if not stocks_data:
            return self._empty_result()

        # 如果未初始化基期价格，用当前pre_close初始化
        if not self.initialized:
            self.init_base_prices(stocks_data)

        returns = []
        valid_stocks = []
        up_count = 0
        down_count = 0
        flat_count = 0
        total_volume = 0
        total_turnover = 0
        total_market_cap = 0

        sector_returns = {k: [] for k in config.SECTOR_MAP.keys()}

        for stock in stocks_data:
            code = stock.get("code")
            price = stock.get("price", 0)
            pre_close = stock.get("pre_close", 0)
            sector = stock.get("sector", "其他")

            if price <= 0:
                continue

            # 计算收益率
            if code in self.base_prices and self.base_prices[code] > 0:
                base = self.base_prices[code]
            elif pre_close > 0:
                base = pre_close
            else:
                continue

            ret = (price - base) / base * 100  # 百分比
            returns.append(ret)
            valid_stocks.append(stock)

            # 涨跌统计
            change_pct = stock.get("change_pct", 0)
            if change_pct > 0.01:
                up_count += 1
            elif change_pct < -0.01:
                down_count += 1
            else:
                flat_count += 1

            total_volume += stock.get("volume", 0)
            total_turnover += stock.get("turnover", 0)
            total_market_cap += stock.get("market_cap", 0)

            # 板块收益
            if sector in sector_returns:
                sector_returns[sector].append(change_pct)

        if not returns:
            return self._empty_result()

        # 等权平均收益率
        avg_return = sum(returns) / len(returns)
        # 指数点位 = 基点 * (1 + 平均收益率/100)
        index_value = config.INDEX_BASE_VALUE * (1 + avg_return / 100)

        # 指数涨跌幅（相对昨收）
        # 用等权平均的今日涨跌幅
        today_changes = [s.get("change_pct", 0) for s in valid_stocks]
        index_change_pct = sum(today_changes) / len(today_changes) if today_changes else 0

        # 板块统计
        sector_stats = {}
        for sector, rets in sector_returns.items():
            if rets:
                sector_stats[sector] = {
                    "avg_change": round(sum(rets) / len(rets), 2),
                    "count": len(rets),
                    "color": config.SECTOR_MAP[sector]["color"],
                }

        # 排序找出领涨/领跌
        sorted_by_change = sorted(valid_stocks, key=lambda x: x.get("change_pct", 0), reverse=True)

        return {
            "value": round(index_value, 2),
            "change_pct": round(index_change_pct, 2),
            "change_amt": round(index_value * index_change_pct / 100, 2),
            "up_count": up_count,
            "down_count": down_count,
            "flat_count": flat_count,
            "total_volume": total_volume,
            "total_turnover": total_turnover,
            "total_market_cap": total_market_cap,
            "constituent_count": len(valid_stocks),
            "sector_stats": sector_stats,
            "top_gainers": sorted_by_change[:5],
            "top_losers": sorted_by_change[-5:][::-1],
            "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "stocks": valid_stocks,
        }

    def _empty_result(self) -> Dict:
        return {
            "value": config.INDEX_BASE_VALUE,
            "change_pct": 0.0,
            "change_amt": 0.0,
            "up_count": 0,
            "down_count": 0,
            "flat_count": 0,
            "total_volume": 0,
            "total_turnover": 0,
            "total_market_cap": 0,
            "constituent_count": 0,
            "sector_stats": {},
            "top_gainers": [],
            "top_losers": [],
            "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "stocks": [],
        }


# 全局单例
calculator = IndexCalculator()
