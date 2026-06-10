"""
技术指标与信号分析模块
"""

from typing import List, Dict
import numpy as np


def calculate_ma(prices: List[float], period: int) -> List[float]:
    """计算移动平均线"""
    if len(prices) < period:
        return [np.nan] * len(prices)
    arr = np.array(prices)
    ma = np.convolve(arr, np.ones(period) / period, mode='valid')
    # 前面补 nan 使长度一致
    return [np.nan] * (period - 1) + ma.tolist()


def calculate_rsi(prices: List[float], period: int = 14) -> List[float]:
    """计算 RSI 相对强弱指标"""
    if len(prices) < period + 1:
        return [50.0] * len(prices)

    deltas = np.diff(prices)
    gains = np.where(deltas > 0, deltas, 0)
    losses = np.where(deltas < 0, -deltas, 0)

    avg_gains = np.convolve(gains, np.ones(period) / period, mode='valid')
    avg_losses = np.convolve(losses, np.ones(period) / period, mode='valid')

    rs = avg_gains / (avg_losses + 1e-10)
    rsi = 100 - (100 / (1 + rs))

    return [50.0] * (period) + rsi.tolist()


def calculate_macd(prices: List[float], fast: int = 12, slow: int = 26, signal: int = 9) -> Dict:
    """计算 MACD 指标"""
    if len(prices) < slow + signal:
        return {"macd": [0.0] * len(prices), "signal": [0.0] * len(prices), "histogram": [0.0] * len(prices)}

    arr = np.array(prices)
    ema_fast = _calculate_ema(arr, fast)
    ema_slow = _calculate_ema(arr, slow)
    macd_line = ema_fast - ema_slow
    signal_line = _calculate_ema(macd_line, signal)
    histogram = macd_line - signal_line

    return {
        "macd": macd_line.tolist(),
        "signal": signal_line.tolist(),
        "histogram": histogram.tolist(),
    }


def _calculate_ema(data: np.ndarray, period: int) -> np.ndarray:
    """计算指数移动平均"""
    alpha = 2 / (period + 1)
    ema = np.zeros_like(data)
    ema[0] = data[0]
    for i in range(1, len(data)):
        ema[i] = alpha * data[i] + (1 - alpha) * ema[i - 1]
    return ema


def generate_signals(history: List[Dict]) -> Dict:
    """基于历史数据生成交易信号
    history: [{"date": str, "close": float, "volume": float}, ...]
    返回最新信号和指标值
    """
    if len(history) < 30:
        return {"signal": "hold", "reason": "数据不足", "indicators": {}}

    closes = [h["close"] for h in history]
    volumes = [h["volume"] for h in history]

    # 计算指标
    rsi_values = calculate_rsi(closes)
    macd_data = calculate_macd(closes)
    ma5 = calculate_ma(closes, 5)
    ma10 = calculate_ma(closes, 10)
    ma20 = calculate_ma(closes, 20)

    latest_rsi = rsi_values[-1]
    latest_macd = macd_data["macd"][-1]
    latest_signal = macd_data["signal"][-1]
    prev_macd = macd_data["macd"][-2]
    prev_signal = macd_data["signal"][-2]
    latest_ma5 = ma5[-1]
    latest_ma10 = ma10[-1]
    latest_ma20 = ma20[-1]

    signals = []

    # RSI 超卖/超买
    if latest_rsi < 30:
        signals.append("RSI超卖(<30)")
    elif latest_rsi > 70:
        signals.append("RSI超买(>70)")

    # MACD 金叉/死叉
    if prev_macd < prev_signal and latest_macd >= latest_signal:
        signals.append("MACD金叉")
    elif prev_macd > prev_signal and latest_macd <= latest_signal:
        signals.append("MACD死叉")

    # 均线排列
    if latest_ma5 > latest_ma10 > latest_ma20:
        signals.append("均线多头排列")
    elif latest_ma5 < latest_ma10 < latest_ma20:
        signals.append("均线空头排列")

    # 综合判断
    buy_signals = sum(1 for s in signals if "超卖" in s or "金叉" in s or "多头" in s)
    sell_signals = sum(1 for s in signals if "超买" in s or "死叉" in s or "空头" in s)

    if buy_signals > sell_signals:
        signal = "buy"
        reason = f"买入信号({buy_signals}个): " + "、".join(signals)
    elif sell_signals > buy_signals:
        signal = "sell"
        reason = f"卖出信号({sell_signals}个): " + "、".join(signals)
    else:
        signal = "hold"
        reason = "观望: " + "、".join(signals) if signals else "暂无明确信号"

    return {
        "signal": signal,
        "reason": reason,
        "signals": signals,
        "indicators": {
            "rsi": round(latest_rsi, 2),
            "macd": round(latest_macd, 4),
            "macd_signal": round(latest_signal, 4),
            "ma5": round(latest_ma5, 2),
            "ma10": round(latest_ma10, 2),
            "ma20": round(latest_ma20, 2),
        }
    }
