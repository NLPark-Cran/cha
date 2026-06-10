"""
关于页面 - 观猹介绍、指数说明、免责声明
"""

import flet as ft
import config


class AboutPage:
    """关于页面"""

    def __init__(self, page: ft.Page):
        self.page = page

    def _section(self, title: str, content: str) -> ft.Control:
        """构建章节"""
        return ft.Column(
            [
                ft.Text(title, size=16, weight=ft.FontWeight.BOLD, color=config.BRAND_COLOR),
                ft.Divider(height=4, color=ft.Colors.TRANSPARENT),
                ft.Text(content, size=13, color=ft.Colors.GREY_700, selectable=True),
            ],
            spacing=4,
        )

    def build(self) -> ft.Control:
        """构建关于页面"""
        # 成分股列表文本
        stock_list_text = "\n".join(
            [f"• {code} {name} ({sector})" for code, name, sector in config.CONSTITUENTS]
        )

        return ft.Column(
            [
                ft.Text("关于股猹猹", size=20, weight=ft.FontWeight.BOLD, color=ft.Colors.GREY_800),
                ft.Divider(height=16),

                self._section(
                    "🟢 什么是观猹？",
                    "观猹（watcha.cn）是一个专注于 AI 产品与前沿科技的内容社区平台，"
                    "由 02 年出生的连续创业者仲泰创立。平台以\"真实体验、客观打分\"为核心竞争力，"
                    "致力于成为\"AI 时代的应用商店 + 开发者服务平台\"。\n\n"
                    "观猹的口号是\"玩 AI，上观猹！\"，它帮助用户发现真实好用的 AI 产品，"
                    "也帮助 AI 开发者找到第一批种子用户。"
                ),
                ft.Divider(height=16),

                self._section(
                    "📊 什么是观猹概念股指？",
                    "\"股猹猹\"是基于 watcha.cn 生态构建的 AI 产业链概念股指，"
                    "从 A 股中精选 22 只与 AI 算力、AI 应用、AI 芯片、云计算、"
                    "内容营销及机器人产业强相关的上市公司组成成分股。\n\n"
                    f"• 指数基期: {config.INDEX_BASE_DATE}\n"
                    f"• 指数基点: {config.INDEX_BASE_VALUE} 点\n"
                    "• 计算方法: 等权法 (每只成分股权重相同)\n"
                    "• 调仓频率: 季度调仓\n"
                    "• 数据来源: 东方财富 (通过 AKShare/curl_cffi 获取)"
                ),
                ft.Divider(height=16),

                self._section(
                    "📋 成分股列表 (22只)",
                    stock_list_text
                ),
                ft.Divider(height=16),

                self._section(
                    "⚠️ 免责声明",
                    "本网站提供的所有数据仅供学习和研究参考，不构成任何投资建议。\n\n"
                    "股市有风险，投资需谨慎。指数计算基于公开数据，可能存在延迟或误差。\n"
                    "观猹概念股指为社区自定义指数，不代表任何官方立场。\n\n"
                    "数据更新频率约 30 秒，基于东方财富公开接口获取，"
                    "实际行情请以交易所为准。"
                ),
                ft.Divider(height=16),

                ft.Row(
                    [
                        ft.Icon(ft.Icons.CODE, size=14, color=ft.Colors.GREY_400),
                        ft.Text(
                            "Built with Flet 0.85.3 + Python 3.13 | cha.hub.tt2.li",
                            size=11,
                            color=ft.Colors.GREY_400,
                        ),
                    ],
                    spacing=6,
                ),
                ft.Container(height=20),
            ],
            scroll=ft.ScrollMode.AUTO,
            expand=True,
        )
