"""
股猹猹 | 观猹概念股指实时追踪系统 - 入口
"""

import asyncio
import json
import shutil
import sys
import urllib.parse

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
    sys.stderr.write(f"[OAuth] Login persisted for user {db_user['id']} ({userinfo.get('nickname', '')})\n")
    sys.stderr.flush()


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
        sys.stderr.write(f"[Session] Restored for user {db_user['id']} ({userinfo.get('nickname', '')})\n")
        sys.stderr.flush()
        page.update()
    except Exception as e:
        sys.stderr.write(f"[Session] Restore failed: {e}\n")
        sys.stderr.flush()


async def clear_persistent_login():
    """清除持久化登录信息"""
    try:
        prefs = ft.SharedPreferences()
        await prefs.remove("access_token")
        await prefs.remove("refresh_token")
        await prefs.remove("userinfo")
    except Exception as e:
        sys.stderr.write(f"[Session] Clear persistent login failed: {e}\n")
        sys.stderr.flush()


async def check_browser_oauth(page: ft.Page):
    """检查浏览器 localStorage 中是否有 OAuth 回调参数
    Flet 0.85 web 模式下 page.query.to_dict 无法获取 URL query，
    通过 index.html 中的 JavaScript 将参数存入 localStorage，
    这里通过 SharedPreferences 读取。
    """
    try:
        prefs = ft.SharedPreferences()
        code = await prefs.get("cha_oauth_code")
        state = await prefs.get("cha_oauth_state")

        if not code or not state:
            sys.stderr.write("[OAuth] No code/state in browser storage\n")
            sys.stderr.flush()
            return

        sys.stderr.write(f"[OAuth] Found code/state in browser storage, exchanging token...\n")
        sys.stderr.flush()

        # 清除 storage 中的参数，避免重复处理
        await prefs.remove("cha_oauth_code")
        await prefs.remove("cha_oauth_state")

        # 换取 token
        token_data = watcha_oauth.exchange_code(code, state)
        sys.stderr.write(f"[OAuth] Token response: {token_data}\n")
        sys.stderr.flush()

        if not token_data or "access_token" not in token_data:
            sys.stderr.write("[OAuth] Failed to exchange code\n")
            sys.stderr.flush()
            return

        access_token = token_data["access_token"]
        refresh_token = token_data.get("refresh_token")
        expires_in = token_data.get("expires_in", 1800)

        # 获取用户信息
        userinfo = watcha_oauth.get_userinfo(access_token)
        sys.stderr.write(f"[OAuth] Userinfo: {userinfo}\n")
        sys.stderr.flush()

        if not userinfo:
            sys.stderr.write("[OAuth] Get userinfo returned None\n")
            sys.stderr.flush()
            return

        nickname = userinfo.get("nickname", "观猹用户")
        sys.stderr.write(f"[OAuth] Login success: {nickname}\n")
        sys.stderr.flush()

        # 同步设置 session（让 UI 立即显示登录状态）
        watcha_id = userinfo.get("id") or userinfo.get("sub") or userinfo.get("nickname", "")
        db_user = user_service.get_or_create_user(
            watcha_user_id=watcha_id,
            nickname=userinfo.get("nickname", ""),
            avatar_url=userinfo.get("avatar_url", ""),
        )
        user_service.record_login(db_user["id"])

        set_session_data(page.session.id, {
            "access_token": access_token,
            "refresh_token": refresh_token,
            "expires_in": expires_in,
            "userinfo": userinfo,
            "user_id": db_user["id"],
        })

        # 持久化到 localStorage
        await persist_login(page, access_token, refresh_token, expires_in, userinfo)

        # 显示欢迎提示并刷新 UI
        page.show_dialog(ft.SnackBar(content=ft.Text(f"欢迎回来，{nickname}!")))
        page.update()

    except Exception as e:
        sys.stderr.write(f"[OAuth] check_browser_oauth error: {e}\n")
        sys.stderr.flush()


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

    # 检查浏览器 localStorage 中的 OAuth 回调参数
    page.run_task(check_browser_oauth, page)

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
