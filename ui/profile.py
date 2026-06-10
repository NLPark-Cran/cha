"""
个人中心页面 - 用户信息、登录记录、统计
"""

import sys
import flet as ft
from data.user_service import user_service
import config


class ProfilePage:
    """个人中心页面"""

    def __init__(self, page: ft.Page):
        self.page = page

    def _get_session_data(self) -> dict:
        """获取当前会话数据"""
        main_mod = sys.modules.get("__main__")
        if main_mod and hasattr(main_mod, "get_session_data"):
            return main_mod.get_session_data(self.page.session.id)
        return {}

    def _get_user_id(self) -> int:
        return self._get_session_data().get("user_id", 0)

    def _get_userinfo(self) -> dict:
        return self._get_session_data().get("userinfo", {})

    def _build_stat_card(self, label: str, value: str, icon: ft.IconData, color: str) -> ft.Control:
        """统计卡片"""
        return ft.Card(
            content=ft.Container(
                content=ft.Row(
                    [
                        ft.Icon(icon, size=28, color=color),
                        ft.Column(
                            [
                                ft.Text(value, size=20, weight=ft.FontWeight.BOLD, color=ft.Colors.GREY_800),
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

    def _build_login_history(self, user_id: int) -> ft.Control:
        """登录历史列表"""
        logs = user_service.get_login_history(user_id, limit=20)
        if not logs:
            return ft.Container(
                content=ft.Text("暂无登录记录", color=ft.Colors.GREY_400),
                alignment=ft.Alignment(0, 0),
                padding=ft.Padding(20, 20, 20, 20),
            )

        rows = []
        for log in logs:
            rows.append(
                ft.Row(
                    [
                        ft.Icon(ft.Icons.ACCESS_TIME, size=14, color=ft.Colors.GREY_400),
                        ft.Text(log["login_at"], size=12, color=ft.Colors.GREY_700, expand=True),
                        ft.Text(f"IP: {log['ip'] or '-'}" if log.get('ip') else "", size=11, color=ft.Colors.GREY_400),
                    ],
                    spacing=8,
                )
            )

        return ft.Column(rows, spacing=8)

    def build(self) -> ft.Control:
        """构建个人中心页面"""
        userinfo = self._get_userinfo()
        user_id = self._get_user_id()
        nickname = userinfo.get("nickname", "观猹用户")
        avatar_url = userinfo.get("avatar_url", "")

        # 获取统计数据
        login_count = user_service.get_login_count(user_id) if user_id else 0
        portfolio = user_service.get_user_portfolio(user_id) if user_id else []
        portfolio_count = len(portfolio)

        # 获取用户信息（包含 last_login_at）
        db_user = user_service.get_user_by_watcha_id(
            userinfo.get("id") or userinfo.get("sub") or userinfo.get("nickname", "")
        ) if user_id else None
        last_login = db_user.get("last_login_at", "-") if db_user else "-"

        return ft.Column(
            [
                ft.Text("个人中心", size=18, weight=ft.FontWeight.BOLD, color=ft.Colors.GREY_800),
                ft.Divider(height=12, color=ft.Colors.TRANSPARENT),

                # 用户资料卡片
                ft.Card(
                    content=ft.Container(
                        content=ft.Row(
                            [
                                ft.CircleAvatar(
                                    foreground_image_src=avatar_url if avatar_url else None,
                                    content=ft.Text(nickname[:1], size=24) if not avatar_url else None,
                                    radius=30,
                                    bgcolor=config.BRAND_COLOR,
                                ),
                                ft.Column(
                                    [
                                        ft.Text(nickname, size=18, weight=ft.FontWeight.BOLD, color=ft.Colors.GREY_800),
                                        ft.Text(f"观猹 ID: {userinfo.get('id', userinfo.get('sub', '-'))}", size=12, color=ft.Colors.GREY_500),
                                    ],
                                    spacing=4,
                                ),
                            ],
                            spacing=16,
                        ),
                        padding=ft.Padding(20, 20, 20, 20),
                    ),
                    elevation=2,
                    bgcolor=ft.Colors.WHITE,
                ),

                ft.Divider(height=16, color=ft.Colors.TRANSPARENT),

                # 统计卡片行
                ft.ResponsiveRow(
                    [
                        ft.Column([self._build_stat_card("最近上线", last_login[:16] if last_login != "-" else "-", ft.Icons.SCHEDULE, config.BRAND_COLOR)], col={"xs": 12, "sm": 4}),
                        ft.Column([self._build_stat_card("登录次数", str(login_count), ft.Icons.LOGIN, ft.Colors.BLUE_400)], col={"xs": 12, "sm": 4}),
                        ft.Column([self._build_stat_card("自选成分", f"{portfolio_count} 只", ft.Icons.STACKED_LINE_CHART, ft.Colors.ORANGE_400)], col={"xs": 12, "sm": 4}),
                    ],
                    spacing=12,
                    run_spacing=12,
                ),

                ft.Divider(height=16, color=ft.Colors.TRANSPARENT),

                # 登录记录
                ft.Card(
                    content=ft.Container(
                        content=ft.Column(
                            [
                                ft.Row(
                                    [
                                        ft.Text("登录记录", size=14, weight=ft.FontWeight.BOLD, color=ft.Colors.GREY_700),
                                        ft.Text(f"共 {login_count} 次", size=11, color=ft.Colors.GREY_400),
                                    ],
                                    alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
                                ),
                                ft.Divider(height=8),
                                self._build_login_history(user_id),
                            ],
                            spacing=4,
                        ),
                        padding=ft.Padding(16, 16, 16, 16),
                    ),
                    elevation=2,
                    bgcolor=ft.Colors.WHITE,
                ),
            ],
            scroll=ft.ScrollMode.AUTO,
            expand=True,
        )
