# 股猹猹 | 观猹概念股指实时追踪 — 开发指南

## 项目概述

- **名称**: 股猹猹 (CHA - Cha Hubs Analytics)
- **域名**: https://cha.hub.tt2.li
- **GitHub**: https://github.com/NLPark-Cran/cha
- **目标**: 基于 watcha.cn 生态的 AI 产业链概念股指实时追踪网页

## 技术栈

| 层级 | 技术 | 版本 |
|------|------|------|
| UI 框架 | Flet | 0.85.3 |
| 图表 | matplotlib (base64→Image) | 3.10.9 |
| 后端逻辑 | Python | 3.13 |
| 数据获取 | curl_cffi + 东方财富 API | — |
| 数据持久化 | SQLite | — |
| 部署 | systemd + nginx + Let's Encrypt | — |

## ⚠️ Flet 0.85 API 关键差异（与旧版对比）

本项目使用 Flet **0.85.3**（2026年6月发布），与早期版本有大量破坏性 API 变更：

### 布局
- `ft.padding.all(N)` → `ft.Padding(N, N, N, N)`
- `ft.padding.symmetric(horizontal=H, vertical=V)` → `ft.Padding(H, V, H, V)`
- `ft.padding.only(right=R)` → `ft.Padding(0, 0, R, 0)`
- `ft.alignment.center` → `ft.Alignment(0, 0)`
- `ft.border_radius.only(top_left=8, top_right=8)` → `ft.BorderRadius(8, 8, 0, 0)`
- `ft.border.all(1, color)` → `ft.Border(top=BorderSide(1,color), right=..., bottom=..., left=...)`
- `ft.border.only(bottom=...)` → `ft.Border(top=..., right=..., bottom=..., left=...)`

### 控件参数
- `TextButton(text=...)` → `TextButton(content=ft.Text(...))`
- `ElevatedButton(text=...)` → `ElevatedButton(content=ft.Text(...))`
- `PopupMenuItem(text=...)` → `PopupMenuItem(content=ft.Text(...))`
- `Chip(label_style=...)` → `Chip(label_text_style=...)`
- `ButtonStyle(foreground_color=...)` → `ButtonStyle(color=...)`
- `Card(color=...)` → `Card(bgcolor=...)`
- `Container(border_radius=4)` → `Container(border_radius=ft.BorderRadius(4,4,4,4))`

### 图标
- 使用 `ft.Icons.XXX`（大写），不是 `ft.icons.xxx`
- `PIE_CHART_OUTLINED` 不存在 → 用 `PIE_CHART_OUTLINE_OUTLINED`

### 浏览器交互
- `page.client_storage` → **不存在**，改用内存存储或 URL state
- `page.query_params` → `page.query.to_dict`（注意：`query.get()` 会抛 KeyError，用 `.to_dict.get()`）
- `page.launch_url(url, web_window_name="_self")` → `page.launch_url(url, web_popup_window_name="_self")`

### 图表
- `ft.PlotlyChart` → **不存在**，改用 matplotlib 生成 base64 → `ft.Image(src="data:image/png;base64,...")`
- `ft.Chart` / `ft.BarChart` / `ft.LineChart` → **不存在**

### 响应式布局
- 使用 `ft.ResponsiveRow` + `ft.Column(col={"xs": 12, "sm": 6, "md": 4})` 替代固定宽度的 Row

## 项目结构

```
cha/
├── main.py              # 入口 + OAuth 回调处理 + 内存会话存储
├── config.py            # 股票池、品牌色、指数配置
├── requirements.txt
├── auth/
│   └── oauth.py         # 观猹 OAuth2.0 客户端 (PKCE + state 传递)
├── data/
│   ├── fetcher.py       # curl_cffi + 东方财富 API
│   ├── calculator.py    # 等权法指数计算
│   ├── cache.py         # 线程安全内存缓存
│   └── storage.py       # SQLite 历史数据
├── ui/
│   ├── app.py           # 主框架 (AppBar + NavBar)
│   ├── dashboard.py     # 仪表盘 (ResponsiveRow)
│   ├── constituents.py  # 成分股列表
│   ├── chart_page.py    # 走势图 (matplotlib base64)
│   ├── sector_analysis.py # 板块分析
│   └── about.py         # 关于页
├── utils/
│   └── helpers.py       # 格式化/颜色工具
├── assets/
│   └── favicon.png      # 品牌 favicon
├── cran/skill/
│   └── watcha-oauth/    # 观猹 OAuth Skill
├── nginx/cha.conf       # nginx 站点配置
└── systemd/cha.service  # systemd 服务配置
```

## 部署

```bash
# 服务控制
sudo systemctl {start|stop|restart|status} cha

# 查看日志
sudo journalctl -u cha -f

# 手动测试
source venv/bin/activate
python main.py --port 8501 --host 127.0.0.1
```

nginx 反向代理到 `127.0.0.1:8501`，SSL 由 certbot 管理。

## 数据源

- **主要**: 东方财富 API（通过 curl_cffi 调用）
- **频率**: 30 秒轮询
- **延迟**: 约 3 秒
- **成分股**: 22 只 A 股，覆盖 AI 算力/应用/芯片/云计算/营销/机器人

## 登录

- 仅支持 watcha.cn OAuth2.0
- PKCE + Authorization Code 流程
- `code_verifier` 编码在 OAuth state 参数中传递（无需浏览器存储）
- 开发环境凭据：`client_id=1p9Mcr+CNLPAMFC0`
