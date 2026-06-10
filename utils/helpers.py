"""
工具函数
"""


def format_number(n: float, decimals: int = 2) -> str:
    """格式化数字，大数转万/亿"""
    if n is None or n == 0:
        return "0"
    if abs(n) >= 1e8:
        return f"{n/1e8:.{decimals}f}亿"
    elif abs(n) >= 1e4:
        return f"{n/1e4:.{decimals}f}万"
    return f"{n:.{decimals}f}"


def format_volume(n: float) -> str:
    """格式化成交量"""
    if n is None or n == 0:
        return "0"
    if n >= 1e8:
        return f"{n/1e8:.2f}亿"
    elif n >= 1e4:
        return f"{n/1e4:.2f}万"
    return f"{n:.0f}"


def format_price(n: float) -> str:
    """格式化价格"""
    if n is None:
        return "-"
    return f"{n:.2f}"


def change_color(change_pct: float) -> str:
    """根据涨跌幅返回颜色 (A股: 红涨绿跌)"""
    if change_pct > 0:
        return "#E74C3C"  # 红
    elif change_pct < 0:
        return "#27AE60"  # 绿
    return "#95A5A6"  # 灰


def change_bg_color(change_pct: float) -> str:
    """根据涨跌幅返回背景色"""
    if change_pct > 0:
        return "#FDEAEA"
    elif change_pct < 0:
        return "#E8F5E9"
    return "#F5F5F5"


def change_icon(change_pct: float) -> str:
    """涨跌箭头"""
    if change_pct > 0:
        return "▲"
    elif change_pct < 0:
        return "▼"
    return "-"
