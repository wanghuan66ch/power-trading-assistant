"""
功率预测 API
"""
import logging
from datetime import datetime, timedelta
from typing import Optional

from fastapi import APIRouter, Depends, Query
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from core.database import get_db
from models.trade import ForecastRecord
from schemas.trade import ForecastCreate, ForecastResponse, ForecastAccuracy

logger = logging.getLogger(__name__)
router = APIRouter()


@router.get("/", response_model=list[ForecastResponse])
async def list_forecasts(
    plant_id: Optional[str] = Query(None),
    province: Optional[str] = Query(None),
    plant_type: Optional[str] = Query(None),  # 光伏/风电
    limit: int = Query(100, le=500),
    db: AsyncSession = Depends(get_db),
):
    """查询功率预测记录"""
    query = select(ForecastRecord).order_by(ForecastRecord.forecast_time.desc())
    if plant_id:
        query = query.where(ForecastRecord.plant_id == plant_id)
    if province:
        query = query.where(ForecastRecord.province == province)
    if plant_type:
        query = query.where(ForecastRecord.plant_type == plant_type)
    query = query.limit(limit)

    result = await db.execute(query)
    return result.scalars().all()


@router.post("/", response_model=ForecastResponse)
async def create_forecast(
    forecast: ForecastCreate,
    db: AsyncSession = Depends(get_db),
):
    """新建功率预测（通常由定时任务调用）"""
    db_forecast = ForecastRecord(
        plant_id=forecast.plant_id,
        plant_type=forecast.plant_type,
        province=forecast.province,
        forecast_time=forecast.forecast_time,
        predicted_power_mw=forecast.predicted_power_mw,
        weather_condition=forecast.weather_condition,
        irradiance=forecast.irradiance,
        wind_speed=forecast.wind_speed,
        confidence=forecast.confidence,
    )
    db.add(db_forecast)
    await db.commit()
    await db.refresh(db_forecast)
    return db_forecast


@router.post("/predict")
async def trigger_prediction(
    plant_id: str,
    forecast_date: Optional[datetime] = None,
    db: AsyncSession = Depends(get_db),
):
    """触发一次功率预测（调用 AI 模型）"""
    from services.forecast import PowerForecastService

    if forecast_date is None:
        forecast_date = datetime.utcnow()

    service = PowerForecastService(db)
    result = await service.predict(plant_id, forecast_date)
    return result


@router.get("/accuracy/{plant_id}", response_model=ForecastAccuracy)
async def get_forecast_accuracy(
    plant_id: str,
    db: AsyncSession = Depends(get_db),
):
    """获取某电站的预测准确率"""
    # 统计最近7天有实际值的预测
    week_ago = datetime.utcnow() - timedelta(days=7)
    query = select(ForecastRecord).where(
        ForecastRecord.plant_id == plant_id,
        ForecastRecord.forecast_time >= week_ago,
        ForecastRecord.actual_power_mw.isnot(None),
    ).order_by(ForecastRecord.forecast_time.desc())

    result = await db.execute(query)
    records = result.scalars().all()

    if not records:
        return ForecastAccuracy(
            plant_id=plant_id,
            plant_type="",
            accuracy_1h=0.0,
            accuracy_24h=0.0,
            mae=0.0,
            mape=0.0,
        )

    # 计算准确率
    total = len(records)
    abs_errors = [abs(r.predicted_power_mw - r.actual_power_mw) for r in records]
    pct_errors = [
        abs(r.predicted_power_mw - r.actual_power_mw) / max(r.actual_power_mw, 0.01) * 100
        for r in records
    ]

    return ForecastAccuracy(
        plant_id=plant_id,
        plant_type=records[0].plant_type,
        accuracy_1h=round(100 - min(sum(pct_errors[:1]) / max(sum(pct_errors), 0.01), 100), 2),
        accuracy_24h=round(100 - min(sum(pct_errors) / total / max(sum(pct_errors), 0.01) * 100, 100), 2),
        mae=round(sum(abs_errors) / total, 2),
        mape=round(sum(pct_errors) / total, 2),
    )
