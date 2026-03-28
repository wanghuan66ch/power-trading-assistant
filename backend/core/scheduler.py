"""
定时任务调度器
- 每 30 分钟自动爬取各省电力价格
- 每小时重新计算风险预警
- 每天 9:00 发送日报（预留接口）
"""
import logging
from datetime import datetime, timezone

from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.interval import IntervalTrigger
from apscheduler.triggers.cron import CronTrigger

from core.database import AsyncSessionLocal
from services.spider import ElectricityPriceSpider

logger = logging.getLogger(__name__)

scheduler = AsyncIOScheduler(timezone="Asia/Shanghai")


async def _crawl_prices_job():
    """定时爬取各省电力价格"""
    logger.info("⏰ [定时任务] 开始爬取电力价格...")
    async with AsyncSessionLocal() as db:
        spider = ElectricityPriceSpider(db)
        try:
            count = await spider.crawl_latest_prices()
            logger.info(f"✅ [定时任务] 价格爬取完成，新增 {count} 条记录")
        except Exception as e:
            logger.error(f"❌ [定时任务] 价格爬取失败: {e}")


async def _refresh_risk_job():
    """定时刷新风险预警（触发计算）"""
    logger.info("⏰ [定时任务] 开始重新计算风险预警...")
    # 风险预警目前是实时计算的，此处预留后续扩展（缓存/通知）
    from api.risk import get_risk_warnings, get_risk_dashboard
    async with AsyncSessionLocal() as db:
        try:
            warnings = await get_risk_warnings(db=db)
            dashboard = await get_risk_dashboard(db=db)
            logger.info(f"✅ [定时任务] 风险预警刷新完成：高风险 {dashboard.get('high_risk_count',0)} 条，"
                         f"中风险 {dashboard.get('medium_risk_count',0)} 条")
        except Exception as e:
            logger.error(f"❌ [定时任务] 风险计算失败: {e}")


def setup_scheduler():
    """注册并启动定时任务"""
    # 每 30 分钟爬取一次价格
    scheduler.add_job(
        _crawl_prices_job,
        trigger=IntervalTrigger(minutes=30),
        id="crawl_prices",
        name="爬取各省电力价格",
        replace_existing=True,
        max_instances=1,
    )

    # 每小时重新计算风险
    scheduler.add_job(
        _refresh_risk_job,
        trigger=IntervalTrigger(hours=1),
        id="refresh_risk",
        name="刷新风险预警",
        replace_existing=True,
        max_instances=1,
    )

    # 每天 9:00 爬取一次日报数据
    scheduler.add_job(
        _crawl_prices_job,
        trigger=CronTrigger(hour=9, minute=0, timezone="Asia/Shanghai"),
        id="daily_price_report",
        name="每日价格日报爬取",
        replace_existing=True,
    )

    scheduler.start()
    logger.info("✅ 定时任务调度器已启动")
    logger.info("   - 爬取价格: 每 30 分钟")
    logger.info("   - 刷新风险: 每 1 小时")
    logger.info("   - 日报爬取: 每天 09:00")


def list_jobs():
    """返回当前所有任务状态"""
    return [
        {
            "id": job.id,
            "name": job.name,
            "next_run": job.next_run_time.isoformat() if job.next_run_time else None,
            "trigger": str(job.trigger),
        }
        for job in scheduler.get_jobs()
    ]
