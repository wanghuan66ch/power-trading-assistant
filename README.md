# ⚡ Power Trading Assistant

电力交易辅助工具 - 价格监控、功率预测、交易管理、策略推荐

## 核心功能

- 📊 **价格监控** - 实时抓取各省电力交易中心成交数据，价格走势可视化
- 🔮 **功率预测** - 基于气象数据的 AI 光伏/风电出力预测
- 📝 **交易管理** - 交易台账、履约率计算、盈亏试算
- 💡 **策略推荐** - 购售电时机建议、合约期限结构优化
- ⚠️ **风险看板** - 合约缺口预警、偏差考核估算、政策新闻聚合

## 技术栈

| 层次 | 技术 |
|------|------|
| 后端 | Python 3.11+ / FastAPI |
| 数据库 | PostgreSQL + TimescaleDB |
| 前端 | React 18 + TypeScript + TailwindCSS |
| 爬虫 | httpx + Playwright |
| AI预测 | XGBoost + LightGBM |
| 部署 | Docker + Docker Compose |

## 快速启动

```bash
# 后端
cd backend
pip install -r requirements.txt
uvicorn main:app --reload --port 8000

# 前端
cd frontend
npm install
npm run dev
```

## 项目结构

```
power-trading-assistant/
├── backend/
│   ├── api/          # API 路由
│   ├── core/         # 核心配置
│   ├── models/       # 数据库模型
│   ├── schemas/      # Pydantic 模型
│   ├── services/     # 业务逻辑
│   └── spiders/      # 爬虫
├── frontend/
│   ├── src/
│   │   ├── components/  # React 组件
│   │   ├── pages/       # 页面
│   │   ├── hooks/       # 自定义 Hooks
│   │   └── utils/       # 工具函数
│   └── public/
├── tests/
├── docs/
└── README.md
```

## 许可协议

MIT License
