"""
股猹猹 | 观猹概念股指实时追踪系统 - 入口
"""

import asyncio
import json
import shutil
import sys

sys.path.insert(0, '.')

import flet as ft
from flet_web import get_package_web_dir

# Replace flet default favicon with our branded one
web_dir = get_package_web_dir()
shutil.copy("assets/favicon.png", f"{web_dir}/favicon.png")

import config
from ui.app import ChaApp
from data.fetcher import fetch_constituents_data
from data.calculator import calculator
from data.cache import cache
from data.storage import storage
from auth.oauth import watcha_oauth

# 内存会话存储: session_id -> {token, userinfo}
_user_sessions: dict = {}


def get_session_data(session_id: str) -> dict:
    """获取会话数据"""
    return _user_sessions.get(session_id, {})


def set_session_data(session_id: str, data: dict):
    """设置会话数据"""
    _user_sessions[session_id] = data


def clear_session(session_id: str):
    """清除会话数据"""
    _user_sessions.pop(session_id, None)


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
    """处理 OAuth 回调 (从 query 中提取 code 和 state)"""
    query_dict = page.query.to_dict
    code = query_dict.get("code")
    state = query_dict.get("state")
    error = query_dict.get("error")
    error_desc = query_dict.get("error_description", "")

    if error:
        print(f"[OAuth] Error from Watcha: {error} - {error_desc}")
        page.show_dialog(ft.SnackBar(content=ft.Text(f"登录失败: {error}")))
        return

    if not code or not state:
        return

    # 用 code + state 换取 token (state 中包含 code_verifier)
    token_data = watcha_oauth.exchange_code(code, state)
    if not token_data or "access_token" not in token_data:
        print(f"[OAuth] Failed to exchange code: {token_data}")
        page.show_dialog(ft.SnackBar(content=ft.Text("换取 Token 失败，请重试")))
        return

    access_token = token_data["access_token"]
    refresh_token = token_data.get("refresh_token")
    expires_in = token_data.get("expires_in", 1800)

    # 获取用户信息
    userinfo = watcha_oauth.get_userinfo(access_token)
    if not userinfo:
        page.show_dialog(ft.SnackBar(content=ft.Text("获取用户信息失败")))
        return

    # 存储到内存会话
    session_id = page.session.id
    set_session_data(session_id, {
        "access_token": access_token,
        "refresh_token": refresh_token,
        "expires_in": expires_in,
        "userinfo": userinfo,
    })

    nickname = userinfo.get("nickname", "观猹用户")
    print(f"[OAuth] Login success: {nickname}")
    page.show_dialog(ft.SnackBar(content=ft.Text(f"欢迎回来，{nickname}!")))

    # 清除 URL 中的 code 参数 (刷新页面到根路径)
    page.launch_url("/", web_popup_window_name="_self")


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
