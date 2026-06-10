"""
成分股管理页面 - 自定义个人指数成分股
"""

import sys
import flet as ft
from data.user_service import user_service
from data.fetcher import fetch_stocks_by_codes
from data.calculator import calculator
from utils.helpers import change_color, change_icon
import config


class PortfolioPage:
    """成分股管理页面"""

    def __init__(self, page: ft.Page):
        self.page = page
        self.search_results = []
        self.search_field = None
        self.portfolio_list = None
        self.preview_card = None

    def _get_session_data(self) -> dict:
        main_mod = sys.modules.get("__main__")
        if main_mod and hasattr(main_mod, "get_session_data"):
            return main_mod.get_session_data(self.page.session.id)
        return {}

    def _get_user_id(self) -> int:
        return self._get_session_data().get("user_id", 0)

    def _get_portfolio(self) -> list:
        """获取用户当前成分股列表，格式 [(code, name, sector), ...]"""
        user_id = self._get_user_id()
        if not user_id:
            return config.CONSTITUENTS
        portfolio = user_service.get_user_portfolio(user_id)
        if not portfolio:
            # 首次使用，初始化默认成分股
            user_service.init_default_portfolio(user_id)
            portfolio = user_service.get_user_portfolio(user_id)
        return [(p["code"], p["name"], p.get("sector", "")) for p in portfolio]

    def _remove_stock(self, code: str):
        """移除成分股"""
        user_id = self._get_user_id()
        if user_id:
            user_service.remove_stock_from_portfolio(user_id, code)
        self._refresh_ui()

    def _reset_default(self, e: ft.ControlEvent):
        """恢复默认成分股"""
        user_id = self._get_user_id()
        if user_id:
            user_service.init_default_portfolio(user_id)
        self._refresh_ui()

    def _on_search(self, e: ft.ControlEvent):
        """搜索股票"""
        query = e.control.value.strip().upper()
        if len(query) < 2:
            self.search_results = []
            self._refresh_search_results()
            return

        # 从默认成分股和全市场搜索（简化：只搜索默认成分股 + 常见AI股）
        all_candidates = list(config.CONSTITUENTS)
        # 扩展一些常见AI概念股
        extra = [
            ("002230", "科大讯飞", "AI应用"),
            ("300418", "昆仑万维", "AI应用"),
            ("300496", "中科创达", "AI应用"),
            ("688256", "寒武纪", "AI算力"),
            ("688041", "海光信息", "AI算力"),
            ("000977", "浪潮信息", "AI算力"),
            ("603019", "中科曙光", "AI算力"),
            ("601138", "工业富联", "AI算力"),
            ("300474", "景嘉微", "AI芯片"),
            ("688047", "龙芯中科", "AI芯片"),
            ("688521", "芯原股份", "AI芯片"),
            ("688158", "优刻得", "云计算"),
            ("600845", "宝信软件", "云计算"),
            ("300383", "光环新网", "云计算"),
            ("300413", "芒果超媒", "内容营销"),
            ("300058", "蓝色光标", "内容营销"),
            ("300364", "中文在线", "内容营销"),
            ("300251", "光线传媒", "内容营销"),
            ("002747", "埃斯顿", "机器人"),
            ("300124", "汇川技术", "机器人"),
            ("300002", "神州泰岳", "AI应用"),
            ("300308", "中际旭创", "AI算力"),
            ("002463", "沪电股份", "AI算力"),
            ("300502", "新易盛", "AI算力"),
            ("002371", "北方华创", "AI芯片"),
        ]
        all_candidates.extend(extra)

        self.search_results = [
            c for c in all_candidates
            if query in c[0] or query in c[1]
        ]
        self._refresh_search_results()

    def _add_stock(self, code: str, name: str, sector: str):
        """添加股票到组合"""
        user_id = self._get_user_id()
        if user_id:
            user_service.add_stock_to_portfolio(user_id, code, name, sector)
        self.search_field.value = ""
        self.search_results = []
        self._refresh_ui()

    def _refresh_ui(self):
        """刷新整个页面"""
        if self.portfolio_list:
            self.portfolio_list.controls = self._build_portfolio_chips()
            self.portfolio_list.update()
        if self.preview_card:
            self.preview_card.content = self._build_preview_content()
            self.preview_card.update()

    def _refresh_search_results(self):
        """刷新搜索结果"""
        if hasattr(self, 'search_result_container') and self.search_result_container:
            self.search_result_container.controls = self._build_search_result_rows()
            self.search_result_container.update()

    def _build_portfolio_chips(self) -> list:
        """构建当前成分股 Chip 列表"""
        portfolio = self._get_portfolio()
        chips = []
        for code, name, sector in portfolio:
            sector_color = config.SECTOR_MAP.get(sector, {}).get("color", ft.Colors.GREY)
            chips.append(
                ft.Chip(
                    label=ft.Text(f"{name} ({code})"),
                    leading=ft.Container(
                        width=8, height=8, bgcolor=sector_color, border_radius=ft.BorderRadius(4, 4, 4, 4)
                    ),
                    on_click=lambda e, c=code: self._remove_stock(c),
                    delete_icon=ft.Icon(ft.Icons.CLOSE, size=14),
                    on_delete=lambda e, c=code: self._remove_stock(c),
                    bgcolor=ft.Colors.WHITE,
                    label_text_style=ft.TextStyle(size=12),
                )
            )
        return chips

    def _build_search_result_rows(self) -> list:
        """构建搜索结果行"""
        rows = []
        current_codes = [c[0] for c in self._get_portfolio()]
        for code, name, sector in self.search_results[:10]:
            is_added = code in current_codes
            sector_color = config.SECTOR_MAP.get(sector, {}).get("color", ft.Colors.GREY)
            rows.append(
                ft.Container(
                    content=ft.Row(
                        [
                            ft.Row(
                                [
                                    ft.Container(width=8, height=8, bgcolor=sector_color, border_radius=ft.BorderRadius(4, 4, 4, 4)),
                                    ft.Text(f"{name} ({code})", size=13),
                                    ft.Text(sector, size=10, color=ft.Colors.GREY_500),
                                ],
                                spacing=6,
                            ),
                            ft.Button(
                                content=ft.Text("已添加" if is_added else "添加"),
                                disabled=is_added,
                                on_click=lambda e, c=code, n=name, s=sector: self._add_stock(c, n, s),
                                style=ft.ButtonStyle(
                                    padding=ft.Padding(8, 4, 8, 4),
                                    bgcolor=config.BRAND_COLOR if not is_added else ft.Colors.GREY_300,
                                    color=ft.Colors.WHITE,
                                ),
                            ),
                        ],
                        alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
                    ),
                    padding=ft.Padding(8, 6, 8, 6),
                    border=ft.Border(bottom=ft.BorderSide(1, ft.Colors.GREY_100)),
                )
            )
        return rows

    def _build_preview_content(self) -> ft.Control:
        """构建个人版指数预览"""
        portfolio = self._get_portfolio()
        if not portfolio:
            return ft.Container(
                content=ft.Text("暂无成分股", color=ft.Colors.GREY_400),
                alignment=ft.Alignment(0, 0),
                padding=ft.Padding(20, 20, 20, 20),
            )

        # 实时获取数据
        stocks = fetch_stocks_by_codes(portfolio)
        if not stocks:
            return ft.Container(
                content=ft.Text("数据获取中...", color=ft.Colors.GREY_400),
                alignment=ft.Alignment(0, 0),
                padding=ft.Padding(20, 20, 20, 20),
            )

        index_data = calculator.calculate_index(stocks)
        value = index_data.get("value", config.INDEX_BASE_VALUE)
        change_pct = index_data.get("change_pct", 0)
        color = change_color(change_pct)
        icon = change_icon(change_pct)

        return ft.Column(
            [
                ft.Text("我的观猹概念股指", size=14, color=ft.Colors.GREY_600),
                ft.Row(
                    [
                        ft.Text(f"{value:,.2f}", size=36, weight=ft.FontWeight.BOLD, color=color),
                    ],
                    alignment=ft.MainAxisAlignment.CENTER,
                ),
                ft.Row(
                    [
                        ft.Text(f"{icon} {change_pct:+.2f}%", size=16, weight=ft.FontWeight.BOLD, color=color),
                    ],
                    alignment=ft.MainAxisAlignment.CENTER,
                ),
                ft.Divider(height=8, color=ft.Colors.TRANSPARENT),
                ft.Text(f"基于 {len(stocks)} 只成分股计算", size=11, color=ft.Colors.GREY_400, text_align=ft.TextAlign.CENTER),
            ],
            alignment=ft.MainAxisAlignment.CENTER,
            horizontal_alignment=ft.CrossAxisAlignment.CENTER,
            spacing=4,
        )

    def build(self) -> ft.Control:
        """构建成分股管理页面"""
        self.search_field = ft.TextField(
            hint_text="搜索代码或名称添加成分股...",
            prefix_icon=ft.Icons.SEARCH,
            on_change=self._on_search,
            border_radius=20,
            height=40,
        )
        self.search_result_container = ft.Column(spacing=0)
        self.portfolio_list = ft.Row(self._build_portfolio_chips(), wrap=True, spacing=8)
        self.preview_card = ft.Card(
            content=self._build_preview_content(),
            elevation=2,
            bgcolor=ft.Colors.WHITE,
        )

        return ft.Column(
            [
                ft.Text("我的成分股", size=18, weight=ft.FontWeight.BOLD, color=ft.Colors.GREY_800),
                ft.Text("自定义你的观猹概念股指成分股", size=12, color=ft.Colors.GREY_500),
                ft.Divider(height=12, color=ft.Colors.TRANSPARENT),

                # 搜索区
                ft.Row(
                    [
                        ft.Container(content=self.search_field, expand=True),
                        ft.Button(
                            content=ft.Text("恢复默认"),
                            on_click=self._reset_default,
                            style=ft.ButtonStyle(
                                padding=ft.Padding(12, 6, 12, 6),
                                color=ft.Colors.GREY_600,
                            ),
                        ),
                    ],
                    spacing=8,
                ),
                self.search_result_container,
                ft.Divider(height=12, color=ft.Colors.TRANSPARENT),

                # 当前成分股
                ft.Card(
                    content=ft.Container(
                        content=ft.Column(
                            [
                                ft.Row(
                                    [
                                        ft.Text("当前成分股", size=14, weight=ft.FontWeight.BOLD, color=ft.Colors.GREY_700),
                                        ft.Text("点击 Chip 上的 ✕ 删除", size=10, color=ft.Colors.GREY_400),
                                    ],
                                    alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
                                ),
                                ft.Divider(height=8),
                                self.portfolio_list,
                            ],
                            spacing=4,
                        ),
                        padding=ft.Padding(16, 16, 16, 16),
                    ),
                    elevation=1,
                    bgcolor=ft.Colors.WHITE,
                ),

                ft.Divider(height=16, color=ft.Colors.TRANSPARENT),

                # 个人版指数预览
                self.preview_card,
            ],
            scroll=ft.ScrollMode.AUTO,
            expand=True,
        )
