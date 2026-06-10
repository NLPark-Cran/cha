"""
走势图页面 - 使用 Plotly 展示指数和个股走势
"""

import flet as ft
from data.cache import cache
from data.fetcher import fetch_stock_history
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import config


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
                alignment=ft.alignment.center,
                padding=ft.padding.all(40),
            )

        times = [h["time"] for h in history]
        values = [h["value"] for h in history]
        changes = [h.get("change_pct", 0) for h in history]

        fig = go.Figure()
        fig.add_trace(go.Scatter(
            x=times,
            y=values,
            mode='lines+markers',
            name='观猹指数',
            line=dict(color=config.BRAND_COLOR, width=2),
            marker=dict(size=4),
            fill='tozeroy',
            fillcolor='rgba(58, 175, 120, 0.1)',
        ))

        fig.update_layout(
            title=dict(text="观猹概念股指 - 日内走势", font=dict(size=16, color="#333")),
            xaxis_title="时间",
            yaxis_title="指数点位",
            height=350,
            margin=dict(l=50, r=20, t=50, b=40),
            paper_bgcolor='white',
            plot_bgcolor='white',
            hovermode='x unified',
        )
        fig.update_xaxes(showgrid=True, gridwidth=1, gridcolor='#eee')
        fig.update_yaxes(showgrid=True, gridwidth=1, gridcolor='#eee')

        return ft.PlotlyChart(fig, expand=True)

    def _build_stock_kline(self) -> ft.Control:
        """个股K线图"""
        stocks = cache.get_stocks()
        if not stocks:
            return ft.Container(
                content=ft.Text("暂无数据", color=ft.Colors.GREY_400),
                alignment=ft.alignment.center,
                padding=ft.padding.all(40),
            )

        # 默认选第一只
        stock = self.selected_stock or stocks[0]
        code = stock.get("code", "")
        name = stock.get("name", "")

        history = fetch_stock_history(code, period=self.period, limit=60)
        if not history:
            return ft.Container(
                content=ft.Text(f"无法获取 {name} 的历史数据", color=ft.Colors.GREY_400),
                alignment=ft.alignment.center,
                padding=ft.padding.all(40),
            )

        dates = [h["date"] for h in history]
        opens = [h["open"] for h in history]
        highs = [h["high"] for h in history]
        lows = [h["low"] for h in history]
        closes = [h["close"] for h in history]
        volumes = [h["volume"] for h in history]

        fig = make_subplots(
            rows=2, cols=1,
            shared_xaxes=True,
            vertical_spacing=0.05,
            row_heights=[0.7, 0.3],
        )

        fig.add_trace(go.Candlestick(
            x=dates,
            open=opens,
            high=highs,
            low=lows,
            close=closes,
            name=name,
            increasing_line_color='#E74C3C',
            decreasing_line_color='#27AE60',
        ), row=1, col=1)

        fig.add_trace(go.Bar(
            x=dates,
            y=volumes,
            name='成交量',
            marker_color=config.BRAND_COLOR,
            opacity=0.6,
        ), row=2, col=1)

        fig.update_layout(
            title=dict(text=f"{name} ({code}) - {self._period_label()}", font=dict(size=16, color="#333")),
            height=450,
            margin=dict(l=50, r=20, t=50, b=40),
            paper_bgcolor='white',
            plot_bgcolor='white',
            showlegend=False,
            xaxis_rangeslider_visible=False,
        )
        fig.update_xaxes(showgrid=True, gridwidth=1, gridcolor='#eee')
        fig.update_yaxes(showgrid=True, gridwidth=1, gridcolor='#eee')
        fig.update_yaxes(title_text="价格", row=1, col=1)
        fig.update_yaxes(title_text="成交量", row=2, col=1)

        return ft.PlotlyChart(fig, expand=True)

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
                    label_style=ft.TextStyle(
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
                    text=label,
                    data=p,
                    on_click=self._on_period_change,
                    style=ft.ButtonStyle(
                        bgcolor=config.BRAND_COLOR if is_active else ft.Colors.GREY_200,
                        foreground_color=ft.Colors.WHITE if is_active else ft.Colors.GREY_700,
                        padding=ft.padding.symmetric(horizontal=16, vertical=8),
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
