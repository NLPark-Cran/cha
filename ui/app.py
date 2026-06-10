"""
Flet 应用主框架 - 导航、主题、路由、登录
"""

import json
import flet as ft
import config
from auth.oauth import watcha_oauth
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
            padding=ft.Padding(20, 20, 20, 20),
        )

    def _get_session_data(self) -> dict:
        """从内存会话存储获取当前用户数据"""
        # 通过 sys.modules 访问 main.py 中的全局变量
        import sys
        main_mod = sys.modules.get("__main__")
        if main_mod and hasattr(main_mod, "get_session_data"):
            return main_mod.get_session_data(self.page.session.id)
        return {}

    def _is_logged_in(self) -> bool:
        """检查是否已登录"""
        return bool(self._get_session_data().get("access_token"))

    def _get_userinfo(self) -> dict:
        """获取用户信息"""
        return self._get_session_data().get("userinfo", {})

    def _on_login_click(self, e: ft.ControlEvent):
        """点击登录按钮"""
        pkce = watcha_oauth.generate_pkce()

        # 构建授权 URL (code_verifier 编码在 state 中)
        auth_url = watcha_oauth.build_auth_url(pkce, scope="read")

        # 使用 JavaScript 跳转 (替换当前页面)
        self.page.launch_url(auth_url, web_window_name="_self")

    def _on_logout_click(self, e: ft.ControlEvent):
        """登出"""
        import sys
        main_mod = sys.modules.get("__main__")
        if main_mod and hasattr(main_mod, "clear_session"):
            main_mod.clear_session(self.page.session.id)
        self.page.open(ft.SnackBar(content=ft.Text("已退出登录")))
        self.page.update()

    def _build_user_widget(self) -> ft.Control:
        """构建用户登录状态控件"""
        if self._is_logged_in():
            userinfo = self._get_userinfo()
            nickname = userinfo.get("nickname", "观猹用户")
            avatar_url = userinfo.get("avatar_url", "")

            return ft.PopupMenuButton(
                content=ft.Row(
                    [
                        ft.CircleAvatar(
                            foreground_image_src=avatar_url if avatar_url else None,
                            content=ft.Text(nickname[:1]) if not avatar_url else None,
                            radius=16,
                            bgcolor=config.BRAND_COLOR,
                        ),
                        ft.Text(nickname, size=13, color=ft.Colors.GREY_700),
                        ft.Icon(ft.Icons.ARROW_DROP_DOWN, size=16, color=ft.Colors.GREY_500),
                    ],
                    spacing=6,
                ),
                items=[
                    ft.PopupMenuItem(
                        text="退出登录",
                        icon=ft.Icons.LOGOUT,
                        on_click=self._on_logout_click,
                    ),
                ],
            )
        else:
            return ft.ElevatedButton(
                "观猹登录",
                icon=ft.Icons.LOGIN,
                on_click=self._on_login_click,
                style=ft.ButtonStyle(
                    bgcolor=config.BRAND_COLOR,
                    color=ft.Colors.WHITE,
                    padding=ft.Padding(16, 8, 16, 8),
                ),
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
                    padding=ft.Padding(0, 0, 12, 0),
                ),
                ft.Container(
                    content=self._build_user_widget(),
                    padding=ft.Padding(0, 0, 16, 0),
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
