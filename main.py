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
from data.user_service import user_service
from auth.oauth import watcha_oauth

# 内存会话存储: session_id -> {token, userinfo, user_id}
_user_sessions: dict = {}

# 已处理的 OAuth code，避免重复处理
_processed_codes: set = set()


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


async def persist_login(page: ft.Page, access_token: str, refresh_token: str, expires_in: int, userinfo: dict):
    """将登录信息持久化到 SharedPreferences 和数据库"""
    prefs = ft.SharedPreferences()
    await prefs.set("access_token", access_token)
    await prefs.set("refresh_token", refresh_token or "")
    await prefs.set("userinfo", json.dumps(userinfo))

    # 同步到数据库
    watcha_id = userinfo.get("id") or userinfo.get("sub") or userinfo.get("nickname", "")
    db_user = user_service.get_or_create_user(
        watcha_user_id=watcha_id,
        nickname=userinfo.get("nickname", ""),
        avatar_url=userinfo.get("avatar_url", ""),
    )
    user_service.record_login(db_user["id"])

    # 设置内存会话
    set_session_data(page.session.id, {
        "access_token": access_token,
        "refresh_token": refresh_token,
        "expires_in": expires_in,
        "userinfo": userinfo,
        "user_id": db_user["id"],
    })
    print(f"[OAuth] Login persisted for user {db_user['id']} ({userinfo.get('nickname', '')})")


async def restore_session(page: ft.Page):
    """从 SharedPreferences 恢复登录会话"""
    try:
        prefs = ft.SharedPreferences()
        access_token = await prefs.get("access_token")
        if not access_token:
            return

        # 验证 token 有效性
        userinfo = watcha_oauth.get_userinfo(access_token)
        if not userinfo:
            # Token 已失效，清除
            await prefs.remove("access_token")
            await prefs.remove("refresh_token")
            await prefs.remove("userinfo")
            return

        # 恢复数据库用户记录
        watcha_id = userinfo.get("id") or userinfo.get("sub") or userinfo.get("nickname", "")
        db_user = user_service.get_or_create_user(
            watcha_user_id=watcha_id,
            nickname=userinfo.get("nickname", ""),
            avatar_url=userinfo.get("avatar_url", ""),
        )

        set_session_data(page.session.id, {
            "access_token": access_token,
            "refresh_token": await prefs.get("refresh_token") or "",
            "userinfo": userinfo,
            "user_id": db_user["id"],
        })
        print(f"[Session] Restored for user {db_user['id']} ({userinfo.get('nickname', '')})")
        page.update()
    except Exception as e:
        print(f"[Session] Restore failed: {e}")


async def clear_persistent_login():
    """清除持久化登录信息"""
    try:
        prefs = ft.SharedPreferences()
        await prefs.remove("access_token")
        await prefs.remove("refresh_token")
        await prefs.remove("userinfo")
    except Exception as e:
        print(f"[Session] Clear persistent login failed: {e}")


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

    # 避免重复处理同一个 code（包括已处理和已失败的）
    if code in _processed_codes:
        return
    _processed_codes.add(code)

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

    nickname = userinfo.get("nickname", "观猹用户")
    print(f"[OAuth] Login success: {nickname}")
    page.show_dialog(ft.SnackBar(content=ft.Text(f"欢迎回来，{nickname}!")))

    # 同步获取/创建数据库用户，得到 user_id
    watcha_id = userinfo.get("id") or userinfo.get("sub") or userinfo.get("nickname", "")
    db_user = user_service.get_or_create_user(
        watcha_user_id=watcha_id,
        nickname=userinfo.get("nickname", ""),
        avatar_url=userinfo.get("avatar_url", ""),
    )
    user_id = db_user["id"]
    user_service.record_login(user_id)

    # 同步设置内存会话，让 UI 立即更新
    set_session_data(page.session.id, {
        "access_token": access_token,
        "refresh_token": refresh_token,
        "expires_in": expires_in,
        "userinfo": userinfo,
        "user_id": user_id,
    })

    # 异步持久化到 localStorage 和数据库
    page.run_task(persist_login, page, access_token, refresh_token, expires_in, userinfo)


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

    # 尝试恢复之前的登录会话
    page.run_task(restore_session, page)

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
