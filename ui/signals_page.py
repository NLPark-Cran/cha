"""
信号分析页面 - 技术指标与买卖信号
"""

import sys
import flet as ft
from data.fetcher import fetch_stock_history
from data.signals import generate_signals
from data.cache import cache
from utils.helpers import change_color
import config


class SignalsPage:
    """信号分析页面"""

    def __init__(self, page: ft.Page):
        self.page = page

    def _is_logged_in(self) -> bool:
        main_mod = sys.modules.get("__main__")
        if main_mod and hasattr(main_mod, "get_session_data"):
            session = main_mod.get_session_data(self.page.session.id)
            return bool(session.get("access_token"))
        return False

    def _build_signal_badge(self, signal: str) -> ft.Control:
        colors = {
            "buy": ("#27AE60", "买入"),
            "sell": ("#E74C3C", "卖出"),
            "hold": ("#95A5A6", "观望"),
        }
        color, text = colors.get(signal, ("#95A5A6", "观望"))
        return ft.Container(
            content=ft.Text(text, size=12, weight=ft.FontWeight.BOLD, color=ft.Colors.WHITE),
            bgcolor=color,
            border_radius=ft.BorderRadius(4, 4, 4, 4),
            padding=ft.Padding(8, 4, 8, 4),
        )

    def _build_stock_signal_card(self, code: str, name: str, sector: str) -> ft.Control:
        """单只股票信号卡片"""
        history = fetch_stock_history(code, period="daily", limit=60)
        if not history or len(history) < 30:
            return ft.Container(
                content=ft.Text(f"{name} ({code}): 数据不足", size=12, color=ft.Colors.GREY_400),
                padding=ft.Padding(8, 8, 8, 8),
            )

        result = generate_signals(history)
        signal = result.get("signal", "hold")
        indicators = result.get("indicators", {})
        reason = result.get("reason", "")
        sector_color = config.SECTOR_MAP.get(sector, {}).get("color", ft.Colors.GREY)

        return ft.Card(
            content=ft.Container(
                content=ft.Column(
                    [
                        ft.Row(
                            [
                                ft.Row(
                                    [
                                        ft.Container(width=8, height=8, bgcolor=sector_color, border_radius=ft.BorderRadius(4, 4, 4, 4)),
                                        ft.Text(name, size=13, weight=ft.FontWeight.BOLD, color=ft.Colors.GREY_800),
                                        ft.Text(code, size=11, color=ft.Colors.GREY_400),
                                    ],
                                    spacing=6,
                                ),
                                self._build_signal_badge(signal),
                            ],
                            alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
                        ),
                        ft.Divider(height=6),
                        ft.Row(
                            [
                                _indicator_badge("RSI", f"{indicators.get('rsi', '-'):.1f}", self._rsi_color(indicators.get('rsi', 50))),
                                _indicator_badge("MACD", f"{indicators.get('macd', 0):.2f}", ft.Colors.BLUE_400),
                                _indicator_badge("MA5", f"{indicators.get('ma5', 0):.2f}", ft.Colors.PURPLE_400),
                                _indicator_badge("MA20", f"{indicators.get('ma20', 0):.2f}", ft.Colors.ORANGE_400),
                            ],
                            spacing=8,
                            wrap=True,
                        ),
                        ft.Text(reason, size=11, color=ft.Colors.GREY_600),
                    ],
                    spacing=6,
                ),
                padding=ft.Padding(12, 12, 12, 12),
            ),
            elevation=1,
            bgcolor=ft.Colors.WHITE,
        )

    def _rsi_color(self, rsi: float) -> str:
        if rsi < 30:
            return "#27AE60"
        elif rsi > 70:
            return "#E74C3C"
        return ft.Colors.GREY_600

    def build(self) -> ft.Control:
        """构建信号分析页面"""
        if not self._is_logged_in():
            return ft.Container(
                content=ft.Column(
                    [
                        ft.Icon(ft.Icons.LOCK_OUTLINE, size=48, color=ft.Colors.GREY_300),
                        ft.Text("信号分析", size=16, weight=ft.FontWeight.BOLD, color=ft.Colors.GREY_500),
                        ft.Text("登录后查看技术指标与买卖信号", size=12, color=ft.Colors.GREY_400),
                    ],
                    alignment=ft.MainAxisAlignment.CENTER,
                    horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                ),
                alignment=ft.Alignment(0, 0),
                expand=True,
            )

        # 获取成分股列表
        stocks = cache.get_stocks()
        if not stocks:
            stocks = [{"code": c[0], "name": c[1], "sector": c[2]} for c in config.CONSTITUENTS]

        # 统计信号
        buy_count = sell_count = hold_count = 0
        signal_cards = []
        for stock in stocks:
            code = stock.get("code", "")
            name = stock.get("name", "")
            sector = stock.get("sector", "")
            card = self._build_stock_signal_card(code, name, sector)
            signal_cards.append(card)

            # 快速统计（不重复获取数据）
            history = fetch_stock_history(code, period="daily", limit=60)
            if history and len(history) >= 30:
                result = generate_signals(history)
                sig = result.get("signal", "hold")
                if sig == "buy":
                    buy_count += 1
                elif sig == "sell":
                    sell_count += 1
                else:
                    hold_count += 1
            else:
                hold_count += 1

        return ft.Column(
            [
                ft.Text("信号分析", size=18, weight=ft.FontWeight.BOLD, color=ft.Colors.GREY_800),
                ft.Text("基于 RSI / MACD / 均线的技术分析信号", size=12, color=ft.Colors.GREY_500),
                ft.Divider(height=12, color=ft.Colors.TRANSPARENT),

                # 信号统计
                ft.ResponsiveRow(
                    [
                        ft.Column([_summary_card("买入信号", str(buy_count), "#27AE60", ft.Icons.TRENDING_UP)], col={"xs": 12, "sm": 4}),
                        ft.Column([_summary_card("卖出信号", str(sell_count), "#E74C3C", ft.Icons.TRENDING_DOWN)], col={"xs": 12, "sm": 4}),
                        ft.Column([_summary_card("观望", str(hold_count), "#95A5A6", ft.Icons.REMOVE)], col={"xs": 12, "sm": 4}),
                    ],
                    spacing=12,
                    run_spacing=12,
                ),

                ft.Divider(height=16, color=ft.Colors.TRANSPARENT),

                # 个股信号卡片
                ft.Text("个股信号详情", size=14, weight=ft.FontWeight.BOLD, color=ft.Colors.GREY_700),
                ft.Divider(height=8),
                ft.Column(signal_cards, spacing=8),
            ],
            scroll=ft.ScrollMode.AUTO,
            expand=True,
        )


def _indicator_badge(label: str, value: str, color: str) -> ft.Control:
    """指标标签"""
    return ft.Container(
        content=ft.Row(
            [
                ft.Text(label, size=10, color=ft.Colors.GREY_500),
                ft.Text(value, size=11, weight=ft.FontWeight.BOLD, color=color),
            ],
            spacing=4,
        ),
        border=ft.Border.all(1, ft.Colors.GREY_200),
        border_radius=ft.BorderRadius(4, 4, 4, 4),
        padding=ft.Padding(6, 3, 6, 3),
    )


def _summary_card(label: str, value: str, color: str, icon: ft.IconData) -> ft.Control:
    """汇总卡片"""
    return ft.Card(
        content=ft.Container(
            content=ft.Row(
                [
                    ft.Icon(icon, size=28, color=color),
                    ft.Column(
                        [
                            ft.Text(value, size=24, weight=ft.FontWeight.BOLD, color=color),
                            ft.Text(label, size=11, color=ft.Colors.GREY_500),
                        ],
                        spacing=2,
                    ),
                ],
                spacing=12,
            ),
            padding=ft.Padding(16, 16, 16, 16),
        ),
        elevation=1,
        bgcolor=ft.Colors.WHITE,
    )
