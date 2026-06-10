"""
成分股页面 - 完整成分股列表
"""

import flet as ft
from data.cache import cache
from utils.helpers import change_color
import config


class ConstituentsPage:
    """成分股页面"""

    def __init__(self, page: ft.Page):
        self.page = page
        self.sort_field = "change_pct"
        self.sort_desc = True
        self.search_text = ""

    def _build_header(self) -> ft.Control:
        """表头"""
        headers = [
            ("代码", 70, "code"),
            ("名称", 100, "name"),
            ("板块", 80, "sector"),
            ("最新价", 80, "price"),
            ("涨跌额", 80, "change_amt"),
            ("涨跌幅", 80, "change_pct"),
            ("成交量", 100, "volume"),
            ("换手率", 70, "turnover_rate"),
            ("市盈率", 70, "pe"),
        ]

        header_cells = []
        for label, width, field in headers:
            is_sorted = self.sort_field == field
            arrow = " ▼" if is_sorted and self.sort_desc else " ▲" if is_sorted else ""
            header_cells.append(
                ft.Container(
                    content=ft.TextButton(
                        content=ft.Text(label + arrow, size=12, weight=ft.FontWeight.BOLD),
                        style=ft.ButtonStyle(
                            padding=ft.Padding(4, 0, 4, 0),
                            text_style=ft.TextStyle(size=12, weight=ft.FontWeight.BOLD),
                        ),
                        on_click=lambda e, f=field: self._on_sort(f),
                    ),
                    width=width,
                    alignment=ft.Alignment(0, 0),
                )
            )

        return ft.Container(
            content=ft.Row(header_cells, spacing=0),
            bgcolor=ft.Colors.GREY_100,
            padding=ft.Padding(12, 8, 12, 8),
            border_radius=ft.BorderRadius(8, 8, 0, 0),
        )

    def _on_sort(self, field: str):
        """排序切换"""
        if self.sort_field == field:
            self.sort_desc = not self.sort_desc
        else:
            self.sort_field = field
            self.sort_desc = True
        self.page.update()

    def _on_search(self, e: ft.ControlEvent):
        """搜索"""
        self.search_text = e.control.value.lower()
        self.page.update()

    def _build_stock_rows(self) -> list:
        """构建股票行"""
        stocks = cache.get_stocks()

        # 过滤
        if self.search_text:
            stocks = [s for s in stocks if self.search_text in s.get("name", "").lower() or self.search_text in s.get("code", "")]

        # 排序
        reverse = self.sort_desc
        try:
            stocks = sorted(stocks, key=lambda x: x.get(self.sort_field, 0) or 0, reverse=reverse)
        except Exception:
            pass

        rows = []
        for stock in stocks:
            color = change_color(stock.get("change_pct", 0))
            sector = stock.get("sector", "")
            sector_color = config.SECTOR_MAP.get(sector, {}).get("color", ft.Colors.GREY)

            row = ft.Container(
                content=ft.Row(
                    [
                        ft.Text(stock.get("code", ""), size=12, width=70, text_align=ft.TextAlign.CENTER),
                        ft.Text(stock.get("name", ""), size=13, width=100, weight=ft.FontWeight.W_500),
                        ft.Container(
                            content=ft.Text(sector, size=10, color=ft.Colors.WHITE),
                            bgcolor=sector_color,
                            border_radius=ft.BorderRadius(4, 4, 4, 4),
                            padding=ft.Padding(6, 2, 6, 2),
                            width=80,
                            alignment=ft.Alignment(0, 0),
                        ),
                        ft.Text(f"{stock.get('price',0):.2f}", size=13, width=80, text_align=ft.TextAlign.RIGHT),
                        ft.Text(
                            f"{stock.get('change_amt',0):+.2f}",
                            size=13, width=80, text_align=ft.TextAlign.RIGHT, color=color,
                        ),
                        ft.Text(
                            f"{stock.get('change_pct',0):+.2f}%",
                            size=13, width=80, text_align=ft.TextAlign.RIGHT, color=color,
                        ),
                        ft.Text(f"{stock.get('volume',0):,.0f}", size=12, width=100, text_align=ft.TextAlign.RIGHT, color=ft.Colors.GREY_600),
                        ft.Text(f"{stock.get('turnover_rate',0):.2f}%", size=12, width=70, text_align=ft.TextAlign.RIGHT, color=ft.Colors.GREY_600),
                        ft.Text(f"{stock.get('pe',0):.1f}" if stock.get('pe',0) > 0 else "-", size=12, width=70, text_align=ft.TextAlign.RIGHT, color=ft.Colors.GREY_600),
                    ],
                    spacing=0,
                ),
                padding=ft.Padding(12, 10, 12, 10),
                border=ft.Border(
                    top=ft.BorderSide(0, ft.Colors.TRANSPARENT),
                    right=ft.BorderSide(0, ft.Colors.TRANSPARENT),
                    bottom=ft.BorderSide(1, ft.Colors.GREY_100),
                    left=ft.BorderSide(0, ft.Colors.TRANSPARENT),
                ),
                bgcolor=ft.Colors.WHITE,
            )
            rows.append(row)

        return rows

    def build(self) -> ft.Control:
        """构建成分股页面"""
        return ft.Column(
            [
                # 搜索栏
                ft.Row(
                    [
                        ft.Text("观猹概念股成分股", size=18, weight=ft.FontWeight.BOLD, color=ft.Colors.GREY_800),
                        ft.Container(expand=True),
                        ft.TextField(
                            hint_text="搜索代码或名称...",
                            prefix_icon=ft.Icons.SEARCH,
                            width=250,
                            height=40,
                            text_size=13,
                            on_change=self._on_search,
                            border_radius=20,
                        ),
                    ],
                    alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
                ),
                ft.Divider(height=12, color=ft.Colors.TRANSPARENT),
                # 表头
                self._build_header(),
                # 表格内容
                ft.Column(
                    self._build_stock_rows(),
                    scroll=ft.ScrollMode.AUTO,
                    expand=True,
                    spacing=0,
                ),
            ],
            expand=True,
        )
