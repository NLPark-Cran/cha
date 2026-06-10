"""
仪表盘页面 - 核心数据展示
"""

import sys
import flet as ft
from data.cache import cache
from utils.helpers import format_number, format_volume, change_color, change_icon
import config


class DashboardPage:
    """仪表盘页面"""

    def __init__(self, page: ft.Page):
        self.page = page

    def _is_logged_in(self) -> bool:
        """检查是否已登录"""
        main_mod = sys.modules.get("__main__")
        if main_mod and hasattr(main_mod, "get_session_data"):
            session = main_mod.get_session_data(self.page.session.id)
            return bool(session.get("access_token"))
        return False

    def _build_index_card(self) -> ft.Control:
        """指数大卡片"""
        data = cache.get_index_data()
        value = data.get("value", config.INDEX_BASE_VALUE)
        change_pct = data.get("change_pct", 0)
        change_amt = data.get("change_amt", 0)
        color = change_color(change_pct)
        icon = change_icon(change_pct)

        return ft.Card(
            content=ft.Container(
                content=ft.Column(
                    [
                        ft.Text("观猹概念股指", size=14, color=ft.Colors.GREY_600),
                        ft.Row(
                            [
                                ft.Text(
                                    f"{value:,.2f}",
                                    size=42,
                                    weight=ft.FontWeight.BOLD,
                                    color=color,
                                ),
                            ],
                            alignment=ft.MainAxisAlignment.CENTER,
                        ),
                        ft.Row(
                            [
                                ft.Text(
                                    f"{icon} {change_pct:+.2f}%",
                                    size=18,
                                    weight=ft.FontWeight.BOLD,
                                    color=color,
                                ),
                                ft.Text(
                                    f"{change_amt:+.2f}",
                                    size=14,
                                    color=color,
                                ),
                            ],
                            alignment=ft.MainAxisAlignment.CENTER,
                            spacing=12,
                        ),
                        ft.Divider(height=10, color=ft.Colors.TRANSPARENT),
                        ft.Row(
                            [
                                _mini_stat("涨跌家数", f"{data.get('up_count',0)}↑ {data.get('down_count',0)}↓", change_color(1)),
                                _mini_stat("总市值", format_number(data.get('total_market_cap',0), 0), ft.Colors.BLUE_GREY),
                                _mini_stat("成交额", format_volume(data.get('total_turnover',0)), ft.Colors.BLUE_GREY),
                            ],
                            alignment=ft.MainAxisAlignment.SPACE_EVENLY,
                        ),
                    ],
                    alignment=ft.MainAxisAlignment.CENTER,
                    horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                ),
                padding=ft.Padding(20, 20, 20, 20),
            ),
            elevation=2,
            bgcolor=ft.Colors.WHITE,
        )

    def _build_market_breadth(self) -> ft.Control:
        """市场涨跌家数卡片"""
        data = cache.get_index_data()
        up = data.get("up_count", 0)
        down = data.get("down_count", 0)
        flat = data.get("flat_count", 0)
        total = up + down + flat
        if total == 0:
            total = 1

        return ft.Card(
            content=ft.Container(
                content=ft.Column(
                    [
                        ft.Text("涨跌分布", size=14, color=ft.Colors.GREY_600),
                        ft.Row(
                            [
                                ft.Column(
                                    [
                                        ft.Text(str(up), size=24, weight=ft.FontWeight.BOLD, color="#E74C3C"),
                                        ft.Text("上涨", size=11, color=ft.Colors.GREY_500),
                                    ],
                                    horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                                ),
                                ft.Column(
                                    [
                                        ft.Text(str(down), size=24, weight=ft.FontWeight.BOLD, color="#27AE60"),
                                        ft.Text("下跌", size=11, color=ft.Colors.GREY_500),
                                    ],
                                    horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                                ),
                                ft.Column(
                                    [
                                        ft.Text(str(flat), size=24, weight=ft.FontWeight.BOLD, color=ft.Colors.GREY_500),
                                        ft.Text("平盘", size=11, color=ft.Colors.GREY_500),
                                    ],
                                    horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                                ),
                            ],
                            alignment=ft.MainAxisAlignment.SPACE_EVENLY,
                        ),
                    ],
                    alignment=ft.MainAxisAlignment.CENTER,
                ),
                padding=ft.Padding(16, 16, 16, 16),
            ),
            elevation=2,
            bgcolor=ft.Colors.WHITE,
        )

    def _build_top_movers(self, title: str, stocks: list) -> ft.Control:
        """涨跌幅排行列表"""
        rows = []
        for i, s in enumerate(stocks[:5], 1):
            color = change_color(s.get("change_pct", 0))
            rows.append(
                ft.Row(
                    [
                        ft.Text(str(i), size=11, color=ft.Colors.GREY_400, width=18),
                        ft.Text(s.get("name", ""), size=12, expand=True),
                        ft.Text(f"{s.get('change_pct',0):+.2f}%", size=12, color=color, width=65, text_align=ft.TextAlign.RIGHT),
                    ],
                    spacing=6,
                )
            )

        return ft.Card(
            content=ft.Container(
                content=ft.Column(
                    [
                        ft.Text(title, size=13, weight=ft.FontWeight.BOLD, color=ft.Colors.GREY_700),
                        ft.Divider(height=6),
                        *rows,
                    ],
                    spacing=8,
                ),
                padding=ft.Padding(12, 12, 12, 12),
            ),
            elevation=2,
            bgcolor=ft.Colors.WHITE,
        )

    def _build_intraday_chart(self) -> ft.Control:
        """日内走势简览"""
        history = cache.get_history()
        if len(history) < 2:
            return ft.Card(
                content=ft.Container(
                    content=ft.Text("数据收集中...", color=ft.Colors.GREY_400),
                    padding=ft.Padding(20, 20, 20, 20),
                    alignment=ft.Alignment(0, 0),
                ),
                elevation=2,
                bgcolor=ft.Colors.WHITE,
            )

        recent = history[-8:]
        dots = []
        for h in recent:
            color = change_color(h.get("change_pct", 0))
            dots.append(
                ft.Container(
                    content=ft.Column(
                        [
                            ft.Text(f"{h['value']:.1f}", size=10, color=color, weight=ft.FontWeight.BOLD),
                            ft.Text(h["time"][-5:], size=8, color=ft.Colors.GREY_400),
                        ],
                        horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                        spacing=0,
                    ),
                    bgcolor=ft.Colors.WHITE,
                    border_radius=ft.BorderRadius(4, 4, 4, 4),
                    padding=ft.Padding(4, 2, 4, 2),
                    border=ft.Border(
                        top=ft.BorderSide(1, ft.Colors.GREY_200),
                        right=ft.BorderSide(1, ft.Colors.GREY_200),
                        bottom=ft.BorderSide(1, ft.Colors.GREY_200),
                        left=ft.BorderSide(1, ft.Colors.GREY_200),
                    ),
                )
            )

        return ft.Card(
            content=ft.Container(
                content=ft.Column(
                    [
                        ft.Row(
                            [
                                ft.Text("日内走势", size=13, weight=ft.FontWeight.BOLD, color=ft.Colors.GREY_700),
                                ft.Text(f"{len(history)}点", size=10, color=ft.Colors.GREY_400),
                            ],
                            alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
                        ),
                        ft.Divider(height=6),
                        ft.Row(dots, wrap=True, spacing=4, run_spacing=4),
                    ],
                ),
                padding=ft.Padding(12, 12, 12, 12),
            ),
            elevation=2,
            bgcolor=ft.Colors.WHITE,
        )

    def _build_login_prompt(self, title: str) -> ft.Control:
        """未登录提示卡片"""
        return ft.Card(
            content=ft.Container(
                content=ft.Column(
                    [
                        ft.Icon(ft.Icons.LOCK_OUTLINE, size=32, color=ft.Colors.GREY_300),
                        ft.Text(title, size=13, color=ft.Colors.GREY_500),
                        ft.Text("登录后查看", size=11, color=ft.Colors.GREY_400),
                    ],
                    alignment=ft.MainAxisAlignment.CENTER,
                    horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                    spacing=4,
                ),
                padding=ft.Padding(20, 20, 20, 20),
                alignment=ft.Alignment(0, 0),
            ),
            elevation=1,
            bgcolor=ft.Colors.WHITE,
        )

    def build(self) -> ft.Control:
        """构建仪表盘页面"""
        data = cache.get_index_data()
        is_login = self._is_logged_in()

        return ft.Column(
            [
                # 第一行: 指数卡片 + 涨跌分布
                ft.ResponsiveRow(
                    [
                        ft.Column([self._build_index_card()], col={"xs": 12, "sm": 12, "md": 6, "lg": 6, "xl": 6}),
                        ft.Column([self._build_market_breadth() if is_login else self._build_login_prompt("涨跌分布")], col={"xs": 12, "sm": 12, "md": 6, "lg": 6, "xl": 6}),
                    ],
                    spacing=16,
                    run_spacing=16,
                ),
                ft.Divider(height=16, color=ft.Colors.TRANSPARENT),
                # 第二行: 领涨领跌 + 走势图
                ft.ResponsiveRow(
                    [
                        ft.Column([self._build_top_movers("🔥 领涨榜", data.get("top_gainers", [])) if is_login else self._build_login_prompt("领涨榜")], col={"xs": 12, "sm": 6, "md": 4, "lg": 4, "xl": 4}),
                        ft.Column([self._build_top_movers("❄️ 领跌榜", data.get("top_losers", [])) if is_login else self._build_login_prompt("领跌榜")], col={"xs": 12, "sm": 6, "md": 4, "lg": 4, "xl": 4}),
                        ft.Column([self._build_intraday_chart() if is_login else self._build_login_prompt("日内走势")], col={"xs": 12, "sm": 12, "md": 4, "lg": 4, "xl": 4}),
                    ],
                    spacing=16,
                    run_spacing=16,
                ),
            ],
            scroll=ft.ScrollMode.AUTO,
            expand=True,
        )


def _mini_stat(label: str, value: str, color: str) -> ft.Control:
    """小统计项"""
    return ft.Column(
        [
            ft.Text(value, size=14, weight=ft.FontWeight.BOLD, color=color),
            ft.Text(label, size=10, color=ft.Colors.GREY_500),
        ],
        horizontal_alignment=ft.CrossAxisAlignment.CENTER,
        spacing=2,
    )
