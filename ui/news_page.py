"""
新闻与情绪报告页面
"""

import sys
import flet as ft
from data.news_fetcher import fetch_concept_news, calculate_market_sentiment
from data.cache import cache
import config


class NewsPage:
    """新闻与情绪页面"""

    def __init__(self, page: ft.Page):
        self.page = page

    def _is_logged_in(self) -> bool:
        main_mod = sys.modules.get("__main__")
        if main_mod and hasattr(main_mod, "get_session_data"):
            session = main_mod.get_session_data(self.page.session.id)
            return bool(session.get("access_token"))
        return False

    def _get_sentiment_icon(self, label: str) -> str:
        return {"positive": "🟢", "negative": "🔴", "neutral": "⚪"}.get(label, "⚪")

    def _get_sentiment_color(self, label: str):
        return {"positive": "#27AE60", "negative": "#E74C3C", "neutral": ft.Colors.GREY_500}.get(label, ft.Colors.GREY_500)

    def _build_sentiment_card(self, sentiment: dict) -> ft.Control:
        """情绪指数卡片"""
        score = sentiment.get("score", 0)
        label = sentiment.get("label", "neutral")
        color = self._get_sentiment_color(label)
        emoji = {"positive": "😊", "negative": "😟", "neutral": "😐"}.get(label, "😐")
        label_text = {"positive": "乐观", "negative": "悲观", "neutral": "中性"}.get(label, "中性")

        return ft.Card(
            content=ft.Container(
                content=ft.Column(
                    [
                        ft.Text("市场情绪指数", size=14, color=ft.Colors.GREY_600),
                        ft.Row(
                            [
                                ft.Text(emoji, size=40),
                                ft.Column(
                                    [
                                        ft.Text(f"{score:+.2f}", size=32, weight=ft.FontWeight.BOLD, color=color),
                                        ft.Text(label_text, size=14, color=color, weight=ft.FontWeight.BOLD),
                                    ],
                                    spacing=0,
                                ),
                            ],
                            spacing=16,
                        ),
                        ft.Divider(height=8),
                        ft.Row(
                            [
                                ft.Text(f"🟢 正向 {sentiment.get('positive', 0)}", size=11, color="#27AE60"),
                                ft.Text(f"⚪ 中性 {sentiment.get('neutral', 0)}", size=11, color=ft.Colors.GREY_500),
                                ft.Text(f"🔴 负向 {sentiment.get('negative', 0)}", size=11, color="#E74C3C"),
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

    def _build_news_list(self, news: list) -> ft.Control:
        """新闻列表"""
        if not news:
            return ft.Container(
                content=ft.Text("暂无新闻数据", color=ft.Colors.GREY_400),
                alignment=ft.Alignment(0, 0),
                padding=ft.Padding(40, 40, 40, 40),
            )

        rows = []
        for item in news[:30]:
            sent = item.get("sentiment", {})
            label = sent.get("label", "neutral")
            color = self._get_sentiment_color(label)
            icon = self._get_sentiment_icon(label)

            rows.append(
                ft.Container(
                    content=ft.Column(
                        [
                            ft.Row(
                                [
                                    ft.Text(icon, size=12),
                                    ft.Text(item.get("stock_name", ""), size=11, color=ft.Colors.GREY_500, width=60),
                                    ft.Text(item["title"], size=13, color=ft.Colors.GREY_800, expand=True),
                                ],
                                spacing=6,
                            ),
                            ft.Row(
                                [
                                    ft.Text(item.get("publish_time", ""), size=10, color=ft.Colors.GREY_400),
                                    ft.Text(item.get("source", ""), size=10, color=ft.Colors.GREY_400),
                                    ft.Text(
                                        sent.get("label", "neutral"),
                                        size=10,
                                        color=color,
                                        weight=ft.FontWeight.BOLD,
                                    ),
                                ],
                                spacing=12,
                            ),
                        ],
                        spacing=4,
                    ),
                    padding=ft.Padding(12, 10, 12, 10),
                    border=ft.Border(bottom=ft.BorderSide(1, ft.Colors.GREY_100)),
                )
            )

        return ft.Column(rows, spacing=0)

    def build(self) -> ft.Control:
        """构建新闻与情绪页面"""
        if not self._is_logged_in():
            return ft.Container(
                content=ft.Column(
                    [
                        ft.Icon(ft.Icons.LOCK_OUTLINE, size=48, color=ft.Colors.GREY_300),
                        ft.Text("新闻与情绪报告", size=16, weight=ft.FontWeight.BOLD, color=ft.Colors.GREY_500),
                        ft.Text("登录后查看概念股相关新闻与市场情绪分析", size=12, color=ft.Colors.GREY_400),
                    ],
                    alignment=ft.MainAxisAlignment.CENTER,
                    horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                ),
                alignment=ft.Alignment(0, 0),
                expand=True,
            )

        # 获取新闻数据
        stocks = cache.get_stocks()
        if not stocks:
            stocks = [(c[0], c[1], c[2]) for c in config.CONSTITUENTS]
        else:
            stocks = [(s["code"], s["name"], s.get("sector", "")) for s in stocks]

        news = fetch_concept_news(stocks, limit_per_stock=3)
        sentiment = calculate_market_sentiment(news)

        return ft.Column(
            [
                ft.Text("新闻与情绪", size=18, weight=ft.FontWeight.BOLD, color=ft.Colors.GREY_800),
                ft.Text("概念股相关新闻与市场情绪分析", size=12, color=ft.Colors.GREY_500),
                ft.Divider(height=12, color=ft.Colors.TRANSPARENT),

                # 情绪指数
                self._build_sentiment_card(sentiment),
                ft.Divider(height=16, color=ft.Colors.TRANSPARENT),

                # 新闻列表
                ft.Card(
                    content=ft.Container(
                        content=ft.Column(
                            [
                                ft.Row(
                                    [
                                        ft.Text("相关新闻", size=14, weight=ft.FontWeight.BOLD, color=ft.Colors.GREY_700),
                                        ft.Text(f"共 {len(news)} 条", size=11, color=ft.Colors.GREY_400),
                                    ],
                                    alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
                                ),
                                ft.Divider(height=8),
                                self._build_news_list(news),
                            ],
                            spacing=4,
                        ),
                        padding=ft.Padding(16, 16, 16, 16),
                    ),
                    elevation=1,
                    bgcolor=ft.Colors.WHITE,
                ),
            ],
            scroll=ft.ScrollMode.AUTO,
            expand=True,
        )
