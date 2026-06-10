"""
新闻获取与情感分析模块
"""

import akshare as ak
from typing import List, Dict
from datetime import datetime
import re


# 情感词典
POSITIVE_WORDS = {
    "涨停", "突破", "利好", "增长", "超预期", "上升", "大涨", "飙升", "强劲",
    "复苏", "扩张", "盈利", "净利润", "营收增长", "订单", "中标", "签约",
    "创新", "领先", "龙头", "优势", "攀升", "创新高", "放量", "资金流入",
    "增持", "回购", "分红", "高送转", "并购", "合作", "战略合作",
}

NEGATIVE_WORDS = {
    "跌停", "下跌", "利空", "亏损", "不及预期", "下降", "大跌", "暴跌", "疲软",
    "衰退", "收缩", "亏损", "净利润下滑", "营收下降", "订单取消", "违约",
    "落后", "劣势", "下滑", "创新低", "缩量", "资金流出", "减持", "抛售",
    "停产", "整顿", "调查", "处罚", "退市", "风险", "暴雷", "债务",
}


def analyze_sentiment(title: str, content: str = "") -> dict:
    """简单规则情感分析，返回 {'score': -1~1, 'label': 'positive'/'negative'/'neutral'}"""
    text = title + " " + content
    pos_count = sum(1 for w in POSITIVE_WORDS if w in text)
    neg_count = sum(1 for w in NEGATIVE_WORDS if w in text)

    if pos_count > neg_count:
        score = min(1.0, 0.3 + (pos_count - neg_count) * 0.2)
        label = "positive"
    elif neg_count > pos_count:
        score = max(-1.0, -0.3 - (neg_count - pos_count) * 0.2)
        label = "negative"
    else:
        score = 0.0
        label = "neutral"

    return {"score": score, "label": label, "pos": pos_count, "neg": neg_count}


def fetch_stock_news(symbol: str, limit: int = 10) -> List[Dict]:
    """获取单只股票的新闻"""
    try:
        df = ak.stock_news_em(symbol=symbol)
        if df.empty:
            return []
        results = []
        for _, row in df.head(limit).iterrows():
            sentiment = analyze_sentiment(row["新闻标题"], row.get("新闻内容", ""))
            results.append({
                "symbol": symbol,
                "title": row["新闻标题"],
                "content": row.get("新闻内容", "")[:200],
                "publish_time": row["发布时间"],
                "source": row.get("文章来源", "东方财富"),
                "url": row.get("新闻链接", ""),
                "sentiment": sentiment,
            })
        return results
    except Exception as e:
        print(f"[NewsFetcher] Failed to fetch news for {symbol}: {e}")
        return []


def fetch_concept_news(constituents: List[tuple], limit_per_stock: int = 5) -> List[Dict]:
    """获取概念股全部新闻，去重后按时间排序"""
    all_news = []
    seen_titles = set()
    for code, name, sector in constituents:
        news = fetch_stock_news(code, limit=limit_per_stock)
        for item in news:
            if item["title"] not in seen_titles:
                seen_titles.add(item["title"])
                item["stock_name"] = name
                item["sector"] = sector
                all_news.append(item)

    # 按发布时间排序（最新的在前）
    all_news.sort(key=lambda x: x.get("publish_time", ""), reverse=True)
    return all_news


def calculate_market_sentiment(news_list: List[Dict]) -> dict:
    """计算市场情绪指数"""
    if not news_list:
        return {"score": 0.0, "label": "neutral", "positive": 0, "negative": 0, "neutral": 0}

    positive = sum(1 for n in news_list if n["sentiment"]["label"] == "positive")
    negative = sum(1 for n in news_list if n["sentiment"]["label"] == "negative")
    neutral = len(news_list) - positive - negative

    total = len(news_list)
    score = (positive - negative) / total if total > 0 else 0.0

    if score > 0.2:
        label = "positive"
    elif score < -0.2:
        label = "negative"
    else:
        label = "neutral"

    return {
        "score": round(score, 2),
        "label": label,
        "positive": positive,
        "negative": negative,
        "neutral": neutral,
        "total": total,
    }
