"""
股猹猹 | 观猹概念股指实时追踪系统 - 入口
"""

import asyncio
import flet as ft
import sys

sys.path.insert(0, '.')

from ui.app import ChaApp
from data.fetcher import fetch_constituents_data
from data.calculator import calculator
from data.cache import cache
from data.storage import storage
import config


async def background_refresh(page: ft.Page):
    """后台定时刷新数据"""
    while True:
        try:
            stocks = fetch_constituents_data()
            if stocks:
                index_data = calculator.calculate_index(stocks)
                cache.update(stocks, index_data)
                storage.save_index_snapshot(index_data)
                storage.save_stocks_snapshot(stocks)
                # 触发所有页面更新
                page.update()
        except Exception as e:
            print(f"[Background] Refresh error: {e}")
        await asyncio.sleep(config.REFRESH_INTERVAL)


def main(page: ft.Page):
    """Flet 应用入口"""
    page.title = f"{config.APP_NAME} | {config.APP_SUBTITLE}"
    page.theme_mode = ft.ThemeMode.LIGHT
    page.padding = 0
    page.spacing = 0

    # 设置主题色
    page.theme = ft.Theme(
        color_scheme_seed=config.BRAND_COLOR,
        use_material3=True,
    )

    # 启动后台数据刷新
    page.run_task(background_refresh, page)

    # 初始化应用
    app = ChaApp(page)
    page.add(app.build())


if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument("--port", type=int, default=8501)
    parser.add_argument("--host", type=str, default="127.0.0.1")
    args = parser.parse_args()

    ft.run(
        main=main,
        host=args.host,
        port=args.port,
        view=ft.AppView.WEB_BROWSER if args.host == "127.0.0.1" else ft.AppView.FLET_APP,
    )
