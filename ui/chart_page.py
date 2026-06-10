"""
走势图页面 - 使用 matplotlib 生成图表
"""

import base64
import io
import flet as ft
from data.cache import cache
from data.fetcher import fetch_stock_history
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import config


def _fig_to_base64(fig) -> str:
    """将 matplotlib Figure 转为 base64 data URI"""
    buf = io.BytesIO()
    fig.savefig(buf, format='png', dpi=100, bbox_inches='tight',
                facecolor='white', edgecolor='none')
    buf.seek(0)
    img_b64 = base64.b64encode(buf.read()).decode()
    plt.close(fig)
    return f"data:image/png;base64,{img_b64}"


class ChartPage:
    """走势图页面"""

    def __init__(self, page: ft.Page):
        self.page = page
        self.selected_stock = None
        self.period = "daily"

    def _build_index_chart(self) -> ft.Control:
        """指数走势图"""
        history = cache.get_history()
        if len(history) < 2:
            return ft.Container(
                content=ft.Text("数据收集中，请稍候...", color=ft.Colors.GREY_400),
                alignment=ft.Alignment(0, 0),
                padding=ft.Padding(40, 40, 40, 40),
            )

        times = [h["time"][-5:] for h in history]  # 只取 HH:MM
        values = [h["value"] for h in history]

        fig, ax = plt.subplots(figsize=(8, 3.5))
        ax.plot(times, values, color=config.BRAND_COLOR, linewidth=2, marker='o', markersize=3)
        ax.fill_between(times, values, alpha=0.15, color=config.BRAND_COLOR)
        ax.set_title("观猹概念股指 - 日内走势", fontsize=12, color='#333')
        ax.set_xlabel("时间", fontsize=9)
        ax.set_ylabel("指数点位", fontsize=9)
        ax.grid(True, alpha=0.3)
        ax.tick_params(labelsize=8)
        plt.xticks(rotation=45)
        plt.tight_layout()

        img_src = _fig_to_base64(fig)
        return ft.Image(src=img_src, fit=ft.ImageFit.CONTAIN, expand=True)

    def _build_stock_kline(self) -> ft.Control:
        """个股K线图"""
        stocks = cache.get_stocks()
        if not stocks:
            return ft.Container(
                content=ft.Text("暂无数据", color=ft.Colors.GREY_400),
                alignment=ft.Alignment(0, 0),
                padding=ft.Padding(40, 40, 40, 40),
            )

        stock = self.selected_stock or stocks[0]
        code = stock.get("code", "")
        name = stock.get("name", "")

        history = fetch_stock_history(code, period=self.period, limit=60)
        if not history:
            return ft.Container(
                content=ft.Text(f"无法获取 {name} 的历史数据", color=ft.Colors.GREY_400),
                alignment=ft.Alignment(0, 0),
                padding=ft.Padding(40, 40, 40, 40),
            )

        dates = [h["date"][5:] for h in history]  # 只取 MM-DD
        closes = [h["close"] for h in history]
        volumes = [h["volume"] for h in history]

        fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(8, 5), gridspec_kw={'height_ratios': [3, 1]})

        # 价格线
        ax1.plot(dates, closes, color=config.BRAND_COLOR, linewidth=1.5)
        ax1.set_title(f"{name} ({code}) - {self._period_label()}", fontsize=12, color='#333')
        ax1.set_ylabel("价格", fontsize=9)
        ax1.grid(True, alpha=0.3)
        ax1.tick_params(labelsize=8)

        # 成交量
        ax2.bar(dates, volumes, color=config.BRAND_COLOR, alpha=0.6, width=0.6)
        ax2.set_ylabel("成交量", fontsize=9)
        ax2.grid(True, alpha=0.3)
        ax2.tick_params(labelsize=8)

        plt.setp(ax1.xaxis.get_majorticklabels(), rotation=45)
        plt.setp(ax2.xaxis.get_majorticklabels(), rotation=45)
        plt.tight_layout()

        img_src = _fig_to_base64(fig)
        return ft.Image(src=img_src, fit=ft.ImageFit.CONTAIN, expand=True)

    def _period_label(self) -> str:
        return {"daily": "日线", "weekly": "周线", "monthly": "月线"}.get(self.period, "日线")

    def _on_stock_select(self, e: ft.ControlEvent):
        """选择股票"""
        code = e.control.data
        stocks = cache.get_stocks()
        for s in stocks:
            if s.get("code") == code:
                self.selected_stock = s
                break
        self.page.update()

    def _on_period_change(self, e: ft.ControlEvent):
        """切换周期"""
        self.period = e.control.data
        self.page.update()

    def build(self) -> ft.Control:
        """构建走势图页面"""
        stocks = cache.get_stocks()
        stock_chips = []
        for s in stocks[:10]:
            is_selected = self.selected_stock and self.selected_stock.get("code") == s.get("code")
            stock_chips.append(
                ft.Chip(
                    label=ft.Text(s.get("name", "")),
                    data=s.get("code"),
                    on_click=self._on_stock_select,
                    bgcolor=config.BRAND_COLOR if is_selected else ft.Colors.GREY_200,
                    label_text_style=ft.TextStyle(
                        color=ft.Colors.WHITE if is_selected else ft.Colors.GREY_700,
                        size=12,
                    ),
                )
            )

        period_buttons = []
        for p, label in [("daily", "日线"), ("weekly", "周线"), ("monthly", "月线")]:
            is_active = self.period == p
            period_buttons.append(
                ft.ElevatedButton(
                    content=ft.Text(label),
                    data=p,
                    on_click=self._on_period_change,
                    style=ft.ButtonStyle(
                        bgcolor=config.BRAND_COLOR if is_active else ft.Colors.GREY_200,
                        color=ft.Colors.WHITE if is_active else ft.Colors.GREY_700,
                        padding=ft.Padding(16, 8, 16, 8),
                    ),
                )
            )

        return ft.Column(
            [
                ft.Text("走势图", size=18, weight=ft.FontWeight.BOLD, color=ft.Colors.GREY_800),
                ft.Divider(height=8, color=ft.Colors.TRANSPARENT),
                # 指数日内走势
                self._build_index_chart(),
                ft.Divider(height=16, color=ft.Colors.TRANSPARENT),
                # 个股选择
                ft.Row(
                    [
                        ft.Text("个股K线:", size=13, weight=ft.FontWeight.BOLD, color=ft.Colors.GREY_600),
                        ft.Row(stock_chips, wrap=True, spacing=8),
                    ],
                    wrap=True,
                    spacing=12,
                ),
                ft.Row(period_buttons, spacing=8),
                ft.Divider(height=8, color=ft.Colors.TRANSPARENT),
                # 个股K线
                self._build_stock_kline(),
            ],
            scroll=ft.ScrollMode.AUTO,
            expand=True,
        )
