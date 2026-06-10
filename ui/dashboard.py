"""
仪表盘页面 - 核心数据展示
"""

import flet as ft
from data.cache import cache
from utils.helpers import format_number, format_volume, change_color, change_icon
import config


class DashboardPage:
    """仪表盘页面"""

    def __init__(self, page: ft.Page):
        self.page = page

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
                                    size=48,
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
                                    size=20,
                                    weight=ft.FontWeight.BOLD,
                                    color=color,
                                ),
                                ft.Text(
                                    f"{change_amt:+.2f}",
                                    size=16,
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
                padding=ft.Padding(24, 24, 24, 24),
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

        up_pct = up / total * 100
        down_pct = down / total * 100

        return ft.Card(
            content=ft.Container(
                content=ft.Column(
                    [
                        ft.Text("涨跌分布", size=14, color=ft.Colors.GREY_600),
                        ft.Row(
                            [
                                ft.Column(
                                    [
                                        ft.Text(str(up), size=28, weight=ft.FontWeight.BOLD, color="#E74C3C"),
                                        ft.Text("上涨", size=12, color=ft.Colors.GREY_500),
                                    ],
                                    horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                                ),
                                ft.Column(
                                    [
                                        ft.Text(str(down), size=28, weight=ft.FontWeight.BOLD, color="#27AE60"),
                                        ft.Text("下跌", size=12, color=ft.Colors.GREY_500),
                                    ],
                                    horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                                ),
                                ft.Column(
                                    [
                                        ft.Text(str(flat), size=28, weight=ft.FontWeight.BOLD, color=ft.Colors.GREY_500),
                                        ft.Text("平盘", size=12, color=ft.Colors.GREY_500),
                                    ],
                                    horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                                ),
                            ],
                            alignment=ft.MainAxisAlignment.SPACE_EVENLY,
                        ),
                        ft.Divider(height=8, color=ft.Colors.TRANSPARENT),
                        # 进度条
                        ft.Row(
                            [
                                ft.Container(
                                    bgcolor="#E74C3C",
                                    height=6,
                                    border_radius=ft.BorderRadius(3, 3, 3, 3),
                                    width=up_pct * 2.5,
                                ),
                                ft.Container(
                                    bgcolor="#27AE60",
                                    height=6,
                                    border_radius=ft.BorderRadius(3, 3, 3, 3),
                                    width=down_pct * 2.5,
                                ),
                            ],
                            spacing=2,
                        ),
                    ],
                    alignment=ft.MainAxisAlignment.CENTER,
                ),
                padding=ft.Padding(20, 20, 20, 20),
            ),
            elevation=2,
            bgcolor=ft.Colors.WHITE,
        )

    def _build_top_movers(self, title: str, stocks: list, gainers: bool = True) -> ft.Control:
        """涨跌幅排行列表"""
        rows = []
        for i, s in enumerate(stocks[:5], 1):
            color = change_color(s.get("change_pct", 0))
            rows.append(
                ft.Row(
                    [
                        ft.Text(str(i), size=12, color=ft.Colors.GREY_400, width=20),
                        ft.Text(s.get("name", ""), size=13, expand=True),
                        ft.Text(f"{s.get('price',0):.2f}", size=13, width=60, text_align=ft.TextAlign.RIGHT),
                        ft.Text(
                            f"{s.get('change_pct',0):+.2f}%",
                            size=13,
                            color=color,
                            width=70,
                            text_align=ft.TextAlign.RIGHT,
                        ),
                    ],
                    spacing=8,
                )
            )

        return ft.Card(
            content=ft.Container(
                content=ft.Column(
                    [
                        ft.Text(title, size=14, weight=ft.FontWeight.BOLD, color=ft.Colors.GREY_700),
                        ft.Divider(height=8),
                        *rows,
                    ],
                    spacing=10,
                ),
                padding=ft.Padding(16, 16, 16, 16),
            ),
            elevation=2,
            bgcolor=ft.Colors.WHITE,
        )

    def _build_intraday_chart(self) -> ft.Control:
        """日内走势图 (使用简单折线表示)"""
        history = cache.get_history()
        if len(history) < 2:
            return ft.Card(
                content=ft.Container(
                    content=ft.Text("数据收集中，走势图将在刷新后显示...", color=ft.Colors.GREY_400),
                    padding=ft.Padding(40, 40, 40, 40),
                    alignment=ft.Alignment(0, 0),
                ),
                elevation=2,
            )

        # 简单文本形式展示最新几个点位
        recent = history[-10:]
        dots = []
        for h in recent:
            color = change_color(h.get("change_pct", 0))
            dots.append(
                ft.Container(
                    content=ft.Text(f"{h['value']:.1f}", size=10, color=color),
                    bgcolor=ft.Colors.WHITE,
                    border_radius=ft.BorderRadius(4, 4, 4, 4),
                    padding=ft.Padding(6, 2, 6, 2),
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
                                ft.Text("日内走势", size=14, weight=ft.FontWeight.BOLD, color=ft.Colors.GREY_700),
                                ft.Text(f"共{len(history)}个数据点", size=11, color=ft.Colors.GREY_400),
                            ],
                            alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
                        ),
                        ft.Divider(height=8),
                        ft.Row(dots, wrap=True, spacing=4, run_spacing=4),
                    ],
                ),
                padding=ft.Padding(16, 16, 16, 16),
            ),
            elevation=2,
            bgcolor=ft.Colors.WHITE,
        )

    def build(self) -> ft.Control:
        """构建仪表盘页面"""
        data = cache.get_index_data()

        return ft.Column(
            [
                # 第一行: 指数卡片 + 涨跌分布
                ft.Row(
                    [
                        ft.Container(content=self._build_index_card(), expand=1),
                        ft.Container(content=self._build_market_breadth(), expand=1),
                    ],
                    wrap=True,
                    spacing=16,
                    run_spacing=16,
                    alignment=ft.MainAxisAlignment.START,
                ),
                ft.Divider(height=16, color=ft.Colors.TRANSPARENT),
                # 第二行: 领涨领跌 + 走势图
                ft.Row(
                    [
                        ft.Container(content=self._build_top_movers("🔥 领涨榜", data.get("top_gainers", []), True), expand=1),
                        ft.Container(content=self._build_top_movers("❄️ 领跌榜", data.get("top_losers", []), False), expand=1),
                        ft.Container(content=self._build_intraday_chart(), expand=2),
                    ],
                    wrap=True,
                    spacing=16,
                    run_spacing=16,
                    alignment=ft.MainAxisAlignment.START,
                ),
            ],
            scroll=ft.ScrollMode.AUTO,
            expand=True,
        )


def _mini_stat(label: str, value: str, color: str) -> ft.Control:
    """小统计项"""
    return ft.Column(
        [
            ft.Text(value, size=16, weight=ft.FontWeight.BOLD, color=color),
            ft.Text(label, size=11, color=ft.Colors.GREY_500),
        ],
        horizontal_alignment=ft.CrossAxisAlignment.CENTER,
        spacing=2,
    )
