"""
Flet 应用主框架 - 导航、主题、路由
"""

import flet as ft
import config
from ui.dashboard import DashboardPage
from ui.constituents import ConstituentsPage
from ui.chart_page import ChartPage
from ui.sector_analysis import SectorAnalysisPage
from ui.about import AboutPage


class ChaApp:
    """股猹猹应用主框架"""

    def __init__(self, page: ft.Page):
        self.page = page
        self.current_page_index = 0
        self.pages = [
            DashboardPage(page),
            ConstituentsPage(page),
            ChartPage(page),
            SectorAnalysisPage(page),
            AboutPage(page),
        ]
        self.content_area = ft.Container(
            content=self.pages[0].build(),
            expand=True,
            padding=ft.padding.all(20),
        )

    def on_nav_change(self, e: ft.ControlEvent):
        """导航切换"""
        self.current_page_index = e.control.selected_index
        self.content_area.content = self.pages[self.current_page_index].build()
        self.content_area.update()

    def build(self) -> ft.Control:
        """构建应用布局"""
        # 顶部标题栏
        app_bar = ft.AppBar(
            title=ft.Row(
                [
                    ft.Icon(ft.Icons.TRENDING_UP, color=config.BRAND_COLOR, size=28),
                    ft.Text(
                        config.APP_NAME,
                        size=24,
                        weight=ft.FontWeight.BOLD,
                        color=config.BRAND_COLOR,
                    ),
                    ft.Text(
                        f"| {config.APP_SUBTITLE}",
                        size=14,
                        color=ft.Colors.GREY_600,
                    ),
                ],
                spacing=8,
            ),
            bgcolor=ft.Colors.WHITE,
            elevation=1,
            actions=[
                ft.Container(
                    content=ft.Row(
                        [
                            ft.Icon(ft.Icons.SCHEDULE, size=14, color=ft.Colors.GREY_500),
                            ft.Text(
                                "实时更新",
                                size=12,
                                color=ft.Colors.GREY_500,
                            ),
                        ],
                        spacing=4,
                    ),
                    padding=ft.padding.only(right=20),
                ),
            ],
        )

        # 底部导航栏
        nav_bar = ft.NavigationBar(
            selected_index=self.current_page_index,
            on_change=self.on_nav_change,
            destinations=[
                ft.NavigationBarDestination(
                    icon=ft.Icons.DASHBOARD_OUTLINED,
                    selected_icon=ft.Icons.DASHBOARD,
                    label="仪表盘",
                ),
                ft.NavigationBarDestination(
                    icon=ft.Icons.LIST_ALT_OUTLINED,
                    selected_icon=ft.Icons.LIST_ALT,
                    label="成分股",
                ),
                ft.NavigationBarDestination(
                    icon=ft.Icons.SHOW_CHART_OUTLINED,
                    selected_icon=ft.Icons.SHOW_CHART,
                    label="走势图",
                ),
                ft.NavigationBarDestination(
                    icon=ft.Icons.PIE_CHART_OUTLINED,
                    selected_icon=ft.Icons.PIE_CHART,
                    label="板块分析",
                ),
                ft.NavigationBarDestination(
                    icon=ft.Icons.INFO_OUTLINED,
                    selected_icon=ft.Icons.INFO,
                    label="关于",
                ),
            ],
            bgcolor=ft.Colors.WHITE,
            elevation=2,
        )

        return ft.Column(
            [
                app_bar,
                ft.Container(
                    content=self.content_area,
                    expand=True,
                    bgcolor=ft.Colors.GREY_50,
                ),
                nav_bar,
            ],
            expand=True,
            spacing=0,
        )
