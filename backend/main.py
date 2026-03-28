"""
⚡ Power Trading Assistant - Backend API
电力交易辅助工具后端服务
"""
import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from api import price, trade, forecast, strategy, risk, auth  # noqa: F401
import models  # noqa: F401 - 注册所有 Model
from core.config import settings
from core.database import engine, Base
from core.scheduler import setup_scheduler, list_jobs

# 日志配置
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """应用启动和关闭事件"""
    # 启动时创建数据库表
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    # 启动定时任务调度器
    setup_scheduler()
    logger.info("✅ 数据库初始化完成")
    logger.info(f"🚀 服务启动: http://{settings.host}:{settings.port}")
    yield
    # 关闭时清理
    from core.scheduler import scheduler
    scheduler.shutdown(wait=False)
    await engine.dispose()
    logger.info("👋 服务已关闭")


app = FastAPI(
    title="⚡ Power Trading Assistant",
    description="电力交易辅助工具 API",
    version="0.1.0",
    lifespan=lifespan,
)

# CORS 配置
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # 生产环境应限制
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 注册路由
app.include_router(price.router, prefix="/api/v1/price", tags=["价格监控"])
app.include_router(trade.router, prefix="/api/v1/trade", tags=["交易管理"])
app.include_router(forecast.router, prefix="/api/v1/forecast", tags=["功率预测"])
app.include_router(strategy.router, prefix="/api/v1/strategy", tags=["策略推荐"])
app.include_router(risk.router, prefix="/api/v1/risk", tags=["风险看板"])
app.include_router(auth.router)  # 认证（登录/注册）


@app.get("/")
async def root():
    return {"message": "⚡ Power Trading Assistant API", "version": "0.1.0"}


@app.get("/api/v1/health")
async def health():
    return {"status": "healthy"}


@app.get("/api/v1/scheduler/jobs")
async def scheduler_jobs():
    """查看定时任务状态（需认证）"""
    from core.security import get_current_user_id
    from fastapi import Depends
    user_id = Depends(get_current_user_id)
    return {"jobs": list_jobs()}


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "main:app",
        host=settings.host,
        port=settings.port,
        reload=settings.debug,
    )
