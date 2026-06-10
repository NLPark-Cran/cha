"""
观猹 (watcha.cn) OAuth2.0 登录模块
支持 PKCE + Authorization Code 流程
通过 state 参数传递 code_verifier，无需 client_storage
"""

import base64
import hashlib
import json
import os
import secrets
import urllib.parse
from typing import Optional, Dict
from curl_cffi import requests as curl_requests

# 观猹 OAuth 配置
# 开发环境测试凭据 (来自 watcha-oauth skill)
WATCHA_CLIENT_ID = "1p9Mcr+CNLPAMFC0"
WATCHA_CLIENT_SECRET = "aqkUs+5ZGLSVG6A/L/I0ib9uownWxH+w"
WATCHA_AUTH_URL = "https://watcha.cn/oauth/authorize"
WATCHA_TOKEN_URL = "https://watcha.cn/oauth/api/token"
WATCHA_USERINFO_URL = "https://watcha.cn/oauth/api/userinfo"
WATCHA_INTROSPECT_URL = "https://watcha.cn/oauth/api/introspect"

# 回调地址 (需与注册 domain 匹配)
REDIRECT_URI = "https://cha.hub.tt2.li"


def _encode_state(verifier: str, nonce: str) -> str:
    """将 verifier 和 nonce 编码进 state 字符串"""
    payload = json.dumps({"v": verifier, "n": nonce})
    return base64.urlsafe_b64encode(payload.encode()).decode().rstrip("=")


def _decode_state(state: str) -> Optional[Dict[str, str]]:
    """从 state 字符串解析 verifier 和 nonce"""
    try:
        # 补齐 base64 padding
        padding = 4 - len(state) % 4
        if padding != 4:
            state += "=" * padding
        payload = base64.urlsafe_b64decode(state.encode()).decode()
        return json.loads(payload)
    except Exception:
        return None


class WatchaOAuth:
    """观猹 OAuth 客户端"""

    def __init__(self):
        self.session = curl_requests.Session()

    @staticmethod
    def generate_pkce() -> Dict[str, str]:
        """生成 PKCE 参数"""
        code_verifier = base64.urlsafe_b64encode(
            os.urandom(32)
        ).decode("ascii").rstrip("=")
        code_challenge = base64.urlsafe_b64encode(
            hashlib.sha256(code_verifier.encode()).digest()
        ).decode("ascii").rstrip("=")
        return {
            "code_verifier": code_verifier,
            "code_challenge": code_challenge,
            "code_challenge_method": "S256",
        }

    def build_auth_url(self, pkce: Dict[str, str], scope: str = "read") -> str:
        """构建观猹授权页面 URL (code_verifier 编码在 state 中)"""
        nonce = secrets.token_urlsafe(8)
        state = _encode_state(pkce["code_verifier"], nonce)
        params = {
            "response_type": "code",
            "client_id": WATCHA_CLIENT_ID,
            "redirect_uri": REDIRECT_URI,
            "scope": scope,
            "state": state,
            "code_challenge": pkce["code_challenge"],
            "code_challenge_method": pkce["code_challenge_method"],
        }
        # client_id 含特殊字符需 URL 编码
        query = urllib.parse.urlencode(params, quote_via=urllib.parse.quote)
        return f"{WATCHA_AUTH_URL}?{query}"

    def exchange_code(self, code: str, state: str) -> Optional[Dict]:
        """用授权码换取 Token (从 state 解析 code_verifier)"""
        decoded = _decode_state(state)
        if not decoded or "v" not in decoded:
            print("[OAuth] Failed to decode state")
            return None

        code_verifier = decoded["v"]
        data = {
            "grant_type": "authorization_code",
            "code": code,
            "redirect_uri": REDIRECT_URI,
            "client_id": WATCHA_CLIENT_ID,
            "client_secret": WATCHA_CLIENT_SECRET,
            "code_verifier": code_verifier,
        }
        try:
            resp = self.session.post(
                WATCHA_TOKEN_URL,
                data=data,
                timeout=15,
                impersonate="chrome120",
            )
            resp.raise_for_status()
            return resp.json()
        except Exception as e:
            print(f"[OAuth] Exchange code failed: {e}")
            return None

    def get_userinfo(self, access_token: str) -> Optional[Dict]:
        """获取用户信息"""
        try:
            resp = self.session.get(
                f"{WATCHA_USERINFO_URL}?access_token={access_token}",
                timeout=15,
                impersonate="chrome120",
            )
            resp.raise_for_status()
            result = resp.json()
            if result.get("statusCode") == 200:
                return result.get("data")
            return None
        except Exception as e:
            print(f"[OAuth] Get userinfo failed: {e}")
            return None

    def refresh_token(self, refresh_token: str) -> Optional[Dict]:
        """刷新 AccessToken"""
        data = {
            "grant_type": "refresh_token",
            "refresh_token": refresh_token,
        }
        try:
            resp = self.session.post(
                WATCHA_TOKEN_URL,
                data=data,
                timeout=15,
                impersonate="chrome120",
            )
            resp.raise_for_status()
            return resp.json()
        except Exception as e:
            print(f"[OAuth] Refresh token failed: {e}")
            return None

    def introspect(self, token: str, token_type_hint: str = "access_token") -> Optional[Dict]:
        """校验 Token 是否有效"""
        data = {
            "token": token,
            "token_type_hint": token_type_hint,
        }
        try:
            resp = self.session.post(
                WATCHA_INTROSPECT_URL,
                data=data,
                timeout=15,
                impersonate="chrome120",
            )
            resp.raise_for_status()
            result = resp.json()
            if result.get("statusCode") == 200:
                return result.get("data")
            return None
        except Exception as e:
            print(f"[OAuth] Introspect failed: {e}")
            return None


# 全局单例
watcha_oauth = WatchaOAuth()
