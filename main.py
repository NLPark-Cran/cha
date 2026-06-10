"""
股猹猹 | 观猹概念股指实时追踪系统 - 入口
"""

import asyncio
import json
import flet as ft
import sys

sys.path.insert(0, '.')

from ui.app import ChaApp
from data.fetcher import fetch_constituents_data
from data.calculator import calculator
from data.cache import cache
from data.storage import storage
from auth.oauth import watcha_oauth
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
                page.update()
        except Exception as e:
            print(f"[Background] Refresh error: {e}")
        await asyncio.sleep(config.REFRESH_INTERVAL)


def handle_oauth_callback(page: ft.Page):
    """处理 OAuth 回调 (从 query_params 中提取 code)"""
    query = page.query_params
    code = query.get("code")
    state = query.get("state")
    error = query.get("error")

    if error:
        print(f"[OAuth] Error from Watcha: {error} - {query.get('error_description', '')}")
        page.open(ft.SnackBar(content=ft.Text(f"登录失败: {error}")))
        return

    if not code:
        return

    # 从 client_storage 中取出之前保存的 PKCE 参数和 state
    stored_state = page.client_storage.get("watcha_oauth_state")
    stored_verifier = page.client_storage.get("watcha_code_verifier")

    if not stored_verifier:
        print("[OAuth] No code_verifier found in storage")
        page.open(ft.SnackBar(content=ft.Text("登录状态丢失，请重试")))
        return

    if stored_state and stored_state != state:
        print(f"[OAuth] State mismatch: {stored_state} != {state}")
        page.open(ft.SnackBar(content=ft.Text("登录验证失败，请重试")))
        return

    # 换取 token
    token_data = watcha_oauth.exchange_code(code, stored_verifier)
    if not token_data or "access_token" not in token_data:
        print(f"[OAuth] Failed to exchange code: {token_data}")
        page.open(ft.SnackBar(content=ft.Text("换取 Token 失败，请重试")))
        return

    access_token = token_data["access_token"]
    refresh_token = token_data.get("refresh_token")
    expires_in = token_data.get("expires_in", 1800)

    # 获取用户信息
    userinfo = watcha_oauth.get_userinfo(access_token)
    if not userinfo:
        page.open(ft.SnackBar(content=ft.Text("获取用户信息失败")))
        return

    # 存储登录状态
    page.client_storage.set("watcha_access_token", access_token)
    page.client_storage.set("watcha_refresh_token", refresh_token or "")
    page.client_storage.set("watcha_userinfo", json.dumps(userinfo))

    # 清理临时参数
    page.client_storage.remove("watcha_oauth_state")
    page.client_storage.remove("watcha_code_verifier")

    print(f"[OAuth] Login success: {userinfo.get('nickname')}")
    page.open(ft.SnackBar(content=ft.Text(f"欢迎回来，{userinfo.get('nickname', '观猹用户')}!")))

    # 清除 URL 中的 code 参数 (刷新页面)
    page.launch_url("/", web_window_name="_self")


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

    # 检查 OAuth 回调
    handle_oauth_callback(page)

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
