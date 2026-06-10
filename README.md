# 股猹猹 | 观猹概念股指实时追踪

> 🟢 [https://cha.hub.tt2.li](https://cha.hub.tt2.li)

基于 [watcha.cn](https://watcha.cn) 生态构建的 AI 产业链概念股指实时追踪系统。

## 什么是观猹？

[观猹 (watcha.cn)](https://watcha.cn) 是一个专注于 AI 产品与前沿科技的内容社区平台，由 02 年出生的连续创业者仲泰创立。平台以"真实体验、客观打分"为核心竞争力，致力于成为"AI 时代的应用商店 + 开发者服务平台"。

## 什么是观猹概念股指？

"股猹猹"是从 A 股中精选 22 只与 AI 产业链强相关的上市公司组成的自定义指数，覆盖六大板块：

| 板块 | 权重 | 代表标的 |
|------|------|----------|
| AI 算力基础设施 | 25% | 寒武纪、海光信息、浪潮信息、中科曙光、工业富联 |
| AI 大模型与应用 | 30% | 科大讯飞、金山办公、三六零、昆仑万维、万兴科技、中科创达 |
| AI 芯片/半导体 | 15% | 景嘉微、龙芯中科、芯原股份 |
| 云计算/数据服务 | 15% | 优刻得、宝信软件、光环新网 |
| 内容平台/数字营销 | 10% | 芒果超媒、蓝色光标、中文在线、光线传媒 |
| 人形机器人/具身智能 | 5% | 埃斯顿、汇川技术 |

- **指数基期**: 2024-01-02
- **指数基点**: 1000 点
- **计算方法**: 等权法
- **调仓频率**: 季度调仓

## 技术栈

| 层级 | 技术 |
|------|------|
| 前端 UI | [Flet 0.85.3](https://flet.dev) (Flutter 渲染) |
| 图表 | Plotly 6.8.0 |
| 后端逻辑 | Python 3.13 + asyncio |
| 数据获取 | curl_cffi + 东方财富 API |
| 数据持久化 | SQLite |
| 部署 | systemd + nginx + Let's Encrypt |

## 本地运行

```bash
git clone git@github.com:NLPark-Cran/cha.git
cd cha
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
python main.py --port 8501 --host 127.0.0.1
```

访问 http://127.0.0.1:8501

## 数据说明

- 数据来源：东方财富公开 API（通过 curl_cffi 获取）
- 更新频率：30 秒
- 延迟：约 3 秒
- 免责声明：本网站数据仅供学习研究，不构成投资建议

## License

MIT
