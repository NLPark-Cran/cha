"""
板块分析页面 - 六大板块热力图与对比
"""

import flet as ft
from data.cache import cache
import config


class SectorAnalysisPage:
    """板块分析页面"""

    def __init__(self, page: ft.Page):
        self.page = page

    def _build_sector_cards(self) -> list:
        """板块卡片"""
        data = cache.get_index_data()
        sector_stats = data.get("sector_stats", {})
        stocks = cache.get_stocks()

        cards = []
        for sector_name, info in config.SECTOR_MAP.items():
            stat = sector_stats.get(sector_name, {"avg_change": 0, "count": 0})
            change = stat["avg_change"]
            color = info["color"]
            weight = info["weight"]

            # 计算该板块内个股的涨跌分布
            sector_stocks = [s for s in stocks if s.get("sector") == sector_name]
            up = sum(1 for s in sector_stocks if s.get("change_pct", 0) > 0)
            down = sum(1 for s in sector_stocks if s.get("change_pct", 0) < 0)

            change_color = "#E74C3C" if change > 0 else "#27AE60" if change < 0 else "#95A5A6"
            icon = "▲" if change > 0 else "▼" if change < 0 else "-"

            card = ft.Card(
                content=ft.Container(
                    content=ft.Column(
                        [
                            ft.Row(
                                [
                                    ft.Container(
                                        width=12,
                                        height=12,
                                        bgcolor=color,
                                        border_radius=6,
                                    ),
                                    ft.Text(sector_name, size=16, weight=ft.FontWeight.BOLD),
                                ],
                                spacing=8,
                            ),
                            ft.Divider(height=8),
                            ft.Row(
                                [
                                    ft.Text(
                                        f"{icon} {change:+.2f}%",
                                        size=24,
                                        weight=ft.FontWeight.BOLD,
                                        color=change_color,
                                    ),
                                ],
                                alignment=ft.MainAxisAlignment.CENTER,
                            ),
                            ft.Divider(height=4, color=ft.Colors.TRANSPARENT),
                            ft.Row(
                                [
                                    _stat_item("权重", f"{weight*100:.0f}%"),
                                    _stat_item("成分股", str(stat.get("count", 0))),
                                    _stat_item("上涨", str(up), "#E74C3C"),
                                    _stat_item("下跌", str(down), "#27AE60"),
                                ],
                                alignment=ft.MainAxisAlignment.SPACE_EVENLY,
                            ),
                        ],
                        spacing=4,
                    ),
                    padding=ft.Padding(16, 16, 16, 16),
                    width=260,
                ),
                elevation=2,
                bgcolor=ft.Colors.WHITE,
            )
            cards.append(card)

        return cards

    def _build_sector_table(self) -> ft.Control:
        """板块详细对比表"""
        data = cache.get_index_data()
        sector_stats = data.get("sector_stats", {})
        stocks = cache.get_stocks()

        rows = []
        for sector_name, info in config.SECTOR_MAP.items():
            stat = sector_stats.get(sector_name, {"avg_change": 0, "count": 0})
            sector_stocks = [s for s in stocks if s.get("sector") == sector_name]

            if sector_stocks:
                avg_price = sum(s.get("price", 0) for s in sector_stocks) / len(sector_stocks)
                total_cap = sum(s.get("market_cap", 0) for s in sector_stocks)
                max_change = max(s.get("change_pct", 0) for s in sector_stocks)
                min_change = min(s.get("change_pct", 0) for s in sector_stocks)
            else:
                avg_price = total_cap = max_change = min_change = 0

            change = stat["avg_change"]
            color = "#E74C3C" if change > 0 else "#27AE60" if change < 0 else "#95A5A6"

            rows.append(
                ft.DataRow(
                    cells=[
                        ft.DataCell(
                            ft.Row([
                                ft.Container(width=10, height=10, bgcolor=info["color"], border_radius=5),
                                ft.Text(sector_name),
                            ], spacing=8)
                        ),
                        ft.DataCell(ft.Text(str(stat.get("count", 0)))),
                        ft.DataCell(ft.Text(f"{avg_price:.2f}")),
                        ft.DataCell(ft.Text(f"{change:+.2f}%", color=color)),
                        ft.DataCell(ft.Text(f"{max_change:+.2f}%", color="#E74C3C")),
                        ft.DataCell(ft.Text(f"{min_change:+.2f}%", color="#27AE60")),
                        ft.DataCell(ft.Text(f"{total_cap/1e8:.1f}亿")),
                    ]
                )
            )

        return ft.Card(
            content=ft.Container(
                content=ft.DataTable(
                    columns=[
                        ft.DataColumn(ft.Text("板块", weight=ft.FontWeight.BOLD)),
                        ft.DataColumn(ft.Text("数量", weight=ft.FontWeight.BOLD)),
                        ft.DataColumn(ft.Text("均价", weight=ft.FontWeight.BOLD)),
                        ft.DataColumn(ft.Text("平均涨跌", weight=ft.FontWeight.BOLD)),
                        ft.DataColumn(ft.Text("最大涨幅", weight=ft.FontWeight.BOLD)),
                        ft.DataColumn(ft.Text("最大跌幅", weight=ft.FontWeight.BOLD)),
                        ft.DataColumn(ft.Text("总市值", weight=ft.FontWeight.BOLD)),
                    ],
                    rows=rows,
                    border=ft.border.all(1, ft.Colors.GREY_200),
                    border_radius=8,
                ),
                padding=ft.Padding(16, 16, 16, 16),
            ),
            elevation=2,
        )

    def build(self) -> ft.Control:
        """构建板块分析页面"""
        return ft.Column(
            [
                ft.Text("板块分析", size=18, weight=ft.FontWeight.BOLD, color=ft.Colors.GREY_800),
                ft.Text("观猹概念股六大板块表现对比", size=12, color=ft.Colors.GREY_500),
                ft.Divider(height=16, color=ft.Colors.TRANSPARENT),
                # 板块卡片
                ft.Row(
                    self._build_sector_cards(),
                    wrap=True,
                    spacing=16,
                    run_spacing=16,
                    alignment=ft.MainAxisAlignment.START,
                ),
                ft.Divider(height=24, color=ft.Colors.TRANSPARENT),
                # 板块对比表
                self._build_sector_table(),
            ],
            scroll=ft.ScrollMode.AUTO,
            expand=True,
        )


def _stat_item(label: str, value: str, color: str = ft.Colors.GREY_600) -> ft.Control:
    """统计小项"""
    return ft.Column(
        [
            ft.Text(value, size=14, weight=ft.FontWeight.BOLD, color=color),
            ft.Text(label, size=10, color=ft.Colors.GREY_400),
        ],
        horizontal_alignment=ft.CrossAxisAlignment.CENTER,
        spacing=2,
    )
