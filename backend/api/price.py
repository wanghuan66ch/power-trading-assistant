"""
价格监控 API
"""
import logging
from datetime import datetime, timedelta
from typing import Optional

from fastapi import APIRouter, Depends, Query
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from core.database import get_db
from models.trade import ProvincePrice, PriceAlert
from schemas.trade import ProvincePriceResponse, PriceTrend, PriceAlertResponse

logger = logging.getLogger(__name__)
router = APIRouter()


@router.get("/provinces", response_model=list[ProvincePriceResponse])
async def get_all_prices(
    province: Optional[str] = Query(None),
    price_type: Optional[str] = Query(None),
    limit: int = Query(100, le=1000),
    db: AsyncSession = Depends(get_db),
):
    """获取各省电力成交价格（最新）"""
    query = select(ProvincePrice).order_by(ProvincePrice.recorded_at.desc())
    if province:
        query = query.where(ProvincePrice.province == province)
    if price_type:
        query = query.where(ProvincePrice.price_type == price_type)
    query = query.limit(limit)

    result = await db.execute(query)
    return result.scalars().all()


@router.get("/trend", response_model=list[PriceTrend])
async def get_price_trend(
    province: Optional[str] = Query(None),
    db: AsyncSession = Depends(get_db),
):
    """获取各省价格趋势（最近7天统计）"""
    now = datetime.utcnow()
    week_ago = now - timedelta(days=7)

    query = (
        select(
            ProvincePrice.province,
            ProvincePrice.price_type,
            func.max(ProvincePrice.price).label("max_price_7d"),
            func.min(ProvincePrice.price).label("min_price_7d"),
            func.avg(ProvincePrice.price).label("avg_price_7d"),
            (func.max(ProvincePrice.price) - func.min(ProvincePrice.price)).label("change_pct"),
        )
        .where(ProvincePrice.recorded_at >= week_ago)
        .group_by(ProvincePrice.province, ProvincePrice.price_type)
    )

    if province:
        query = query.where(ProvincePrice.province == province)

    result = await db.execute(query)
    rows = result.all()

    trends = []
    for row in rows:
        current_q = select(ProvincePrice.price).where(
            ProvincePrice.province == row.province,
            ProvincePrice.price_type == row.price_type,
        ).order_by(ProvincePrice.recorded_at.desc()).limit(1)
        current_result = await db.execute(current_q)
        current_price = current_result.scalar() or 0

        trends.append(PriceTrend(
            province=row.province,
            price_type=row.price_type,
            current_price=current_price,
            avg_price_7d=round(row.avg_price_7d, 2),
            max_price_7d=row.max_price_7d,
            min_price_7d=row.min_price_7d,
            change_pct=round(row.change_pct or 0, 2),
        ))

    return trends


@router.post("/refresh")
async def refresh_prices(db: AsyncSession = Depends(get_db)):
    """触发价格数据刷新（从各省交易中心抓取）"""
    from services.spider import ElectricityPriceSpider

    spider = ElectricityPriceSpider(db)
    count = await spider.crawl_latest_prices()
    return {"message": f"抓取完成，新增 {count} 条记录"}


@router.post("/refresh/{province}")
async def refresh_province(province: str, db: AsyncSession = Depends(get_db)):
    """抓取指定省份数据"""
    from services.spider import ElectricityPriceSpider

    spider = ElectricityPriceSpider(db)
    count = await spider.crawl_province(province)
    return {"message": f"{province} 抓取完成，新增 {count} 条记录"}


@router.get("/test-spiders")
async def test_spiders(db: AsyncSession = Depends(get_db)):
    """测试各省爬虫连通性，返回各爬虫状态和样例数据"""
    from services.spider import ElectricityPriceSpider

    spider = ElectricityPriceSpider(db)
    results = await spider.test_spiders()
    return {"spiders": results}


@router.get("/alerts", response_model=list[PriceAlertResponse])
async def get_price_alerts(db: AsyncSession = Depends(get_db)):
    """获取价格预警"""
    query = select(PriceAlert).order_by(PriceAlert.created_at.desc()).limit(50)
    result = await db.execute(query)
    return result.scalars().all()
