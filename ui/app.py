"""
Flet 应用主框架 - 导航、主题、路由、登录
"""

import sys
import flet as ft
import config
from auth.oauth import watcha_oauth
from ui.dashboard import DashboardPage
from ui.constituents import ConstituentsPage
from ui.chart_page import ChartPage
from ui.sector_analysis import SectorAnalysisPage
from ui.about import AboutPage
from ui.profile import ProfilePage
from ui.portfolio import PortfolioPage
from ui.news_page import NewsPage
from ui.signals_page import SignalsPage


class ChaApp:
    """股猹猹应用主框架"""

    def __init__(self, page: ft.Page):
        self.page = page
        self.current_page_index = 0
        self.pages = [
            DashboardPage(page),      # 0
            ConstituentsPage(page),   # 1
            ChartPage(page),          # 2
            SectorAnalysisPage(page), # 3
            NewsPage(page),           # 4
            SignalsPage(page),        # 5
            PortfolioPage(page),      # 6
            ProfilePage(page),        # 7
            AboutPage(page),          # 8
        ]
        self.content_area = ft.Container(
            content=self.pages[0].build(),
            expand=True,
            padding=ft.Padding(16, 16, 16, 16),
        )

    def _get_main_module(self):
        """获取 main 模块"""
        return sys.modules.get("__main__")

    def _get_session_data(self) -> dict:
        """从内存会话存储获取当前用户数据"""
        main_mod = self._get_main_module()
        if main_mod and hasattr(main_mod, "get_session_data"):
            return main_mod.get_session_data(self.page.session.id)
        return {}

    def _is_logged_in(self) -> bool:
        """检查是否已登录"""
        return bool(self._get_session_data().get("access_token"))

    def _get_userinfo(self) -> dict:
        """获取用户信息"""
        return self._get_session_data().get("userinfo", {})

    def _get_user_id(self) -> int:
        """获取数据库用户 ID"""
        return self._get_session_data().get("user_id", 0)

    def _on_login_click(self, e: ft.ControlEvent):
        """点击登录按钮"""
        pkce = watcha_oauth.generate_pkce()
        auth_url = watcha_oauth.build_auth_url(pkce, scope="read")
        self.page.run_task(self._async_launch_url, auth_url)

    async def _async_launch_url(self, url: str):
        await self.page.launch_url(url, web_popup_window_name="_self")

    def _on_logout_click(self, e: ft.ControlEvent):
        """登出"""
        main_mod = self._get_main_module()
        if main_mod and hasattr(main_mod, "clear_session"):
            main_mod.clear_session(self.page.session.id)
        # 清除持久化登录
        if main_mod and hasattr(main_mod, "clear_persistent_login"):
            self.page.run_task(main_mod.clear_persistent_login)
        # 刷新 UI 回到未登录状态
        self._refresh_after_auth_change()
        self.page.show_dialog(ft.SnackBar(content=ft.Text("已退出登录")))

    def _refresh_after_auth_change(self):
        """认证状态变化后刷新 UI"""
        # 重建导航栏
        self.nav_bar.destinations = self._build_nav_destinations()
        # 如果当前页面在未登录状态下不可见，跳转到仪表盘
        visible_indices = self._get_visible_page_indices()
        if self.current_page_index not in visible_indices and visible_indices:
            self.current_page_index = visible_indices[0]
            self.content_area.content = self.pages[self.current_page_index].build()
        self.nav_bar.selected_index = self.current_page_index
        self.nav_bar.update()
        self.content_area.update()
        # 重建 AppBar 用户控件
        self.app_bar.actions = [
            ft.Container(
                content=self._build_user_widget(),
                padding=ft.Padding(0, 0, 12, 0),
            ),
        ]
        self.app_bar.update()

    def _get_visible_page_indices(self) -> list:
        """获取当前认证状态下可见的页面索引"""
        if self._is_logged_in():
            # 登录后：仪表盘(0)、成分股(1)、走势图(2)、板块(3)、新闻(4)、信号(5)、自选(6)、我的(7)、关于(8)
            return [0, 1, 2, 3, 4, 5, 6, 7, 8]
        # 未登录：仅仪表盘(0)和关于(8)
        return [0, 8]

    def _build_nav_destinations(self) -> list:
        """根据登录状态构建导航目的地"""
        all_dests = [
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
                icon=ft.Icons.PIE_CHART_OUTLINE_OUTLINED,
                selected_icon=ft.Icons.PIE_CHART,
                label="板块",
            ),
            ft.NavigationBarDestination(
                icon=ft.Icons.NEWSPAPER_OUTLINED,
                selected_icon=ft.Icons.NEWSPAPER,
                label="新闻",
            ),
            ft.NavigationBarDestination(
                icon=ft.Icons.NOTIFICATIONS_OUTLINED,
                selected_icon=ft.Icons.NOTIFICATIONS,
                label="信号",
            ),
            ft.NavigationBarDestination(
                icon=ft.Icons.STACKED_LINE_CHART_OUTLINED,
                selected_icon=ft.Icons.STACKED_LINE_CHART,
                label="自选",
            ),
            ft.NavigationBarDestination(
                icon=ft.Icons.PERSON_OUTLINE,
                selected_icon=ft.Icons.PERSON,
                label="我的",
            ),
            ft.NavigationBarDestination(
                icon=ft.Icons.INFO_OUTLINED,
                selected_icon=ft.Icons.INFO,
                label="关于",
            ),
        ]
        visible = self._get_visible_page_indices()
        return [all_dests[i] for i in visible]

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
                            radius=14,
                            bgcolor=config.BRAND_COLOR,
                        ),
                        ft.Text(nickname, size=12, color=ft.Colors.GREY_700),
                    ],
                    spacing=4,
                ),
                items=[
                    ft.PopupMenuItem(
                        content=ft.Text("我的成分股"),
                        icon=ft.Icons.STACKED_LINE_CHART,
                        on_click=lambda e: self._switch_to_page(6),
                    ),
                    ft.PopupMenuItem(
                        content=ft.Text("个人中心"),
                        icon=ft.Icons.PERSON,
                        on_click=lambda e: self._switch_to_page(7),
                    ),
                    ft.PopupMenuItem(
                        content=ft.Text("退出登录"),
                        icon=ft.Icons.LOGOUT,
                        on_click=self._on_logout_click,
                    ),
                ],
            )
        else:
            return ft.Button(
                content=ft.Text("登录", size=12),
                icon=ft.Icons.LOGIN,
                on_click=self._on_login_click,
                style=ft.ButtonStyle(
                    bgcolor=config.BRAND_COLOR,
                    color=ft.Colors.WHITE,
                    padding=ft.Padding(10, 6, 10, 6),
                    icon_size=16,
                ),
            )

    def _switch_to_page(self, index: int):
        """切换到指定页面"""
        self.current_page_index = index
        self.content_area.content = self.pages[index].build()
        self.nav_bar.selected_index = index
        self.nav_bar.update()
        self.content_area.update()

    def on_nav_change(self, e: ft.ControlEvent):
        """导航切换"""
        visible = self._get_visible_page_indices()
        selected = e.control.selected_index
        # 将 NavigationBar 的 selected_index 映射回实际的页面索引
        if selected < len(visible):
            self.current_page_index = visible[selected]
            self.content_area.content = self.pages[self.current_page_index].build()
            self.content_area.update()

    def build(self) -> ft.Control:
        """构建应用布局"""
        self.app_bar = ft.AppBar(
            title=ft.Row(
                [
                    ft.Icon(ft.Icons.TRENDING_UP, color=config.BRAND_COLOR, size=22),
                    ft.Text(config.APP_NAME, size=18, weight=ft.FontWeight.BOLD, color=config.BRAND_COLOR),
                ],
                spacing=6,
            ),
            bgcolor=ft.Colors.WHITE,
            elevation=1,
            center_title=False,
            actions=[
                ft.Container(
                    content=self._build_user_widget(),
                    padding=ft.Padding(0, 0, 12, 0),
                ),
            ],
        )

        self.nav_bar = ft.NavigationBar(
            selected_index=0,
            on_change=self.on_nav_change,
            destinations=self._build_nav_destinations(),
            bgcolor=ft.Colors.WHITE,
            elevation=2,
            label_behavior=ft.NavigationBarLabelBehavior.ONLY_SHOW_SELECTED,
        )

        return ft.Column(
            [
                self.app_bar,
                ft.Container(
                    content=self.content_area,
                    expand=True,
                    bgcolor=ft.Colors.GREY_50,
                ),
                self.nav_bar,
            ],
            expand=True,
            spacing=0,
        )
