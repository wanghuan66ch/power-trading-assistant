"""
功率预测 API
"""
import logging
import asyncio
from datetime import datetime, timedelta
from typing import Optional

from fastapi import APIRouter, Depends, Query, BackgroundTasks
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
    plant_type: Optional[str] = Query(None),
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
    """新建功率预测"""
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
    plant_type: str = Query("光伏", description="光伏/风电"),
    latitude: float = Query(30.0, description="纬度"),
    longitude: float = Query(120.0, description="经度"),
    capacity_mw: float = Query(100.0, description="装机容量 MW"),
    forecast_date: Optional[datetime] = Query(None, description="预测时间，默认当前"),
    db: AsyncSession = Depends(get_db),
):
    """触发一次功率预测（调用 LightGBM AI 模型）"""
    from services.forecast import PowerForecastService

    if forecast_date is None:
        forecast_date = datetime.utcnow()

    service = PowerForecastService(db)
    result = await service.predict(
        plant_id=plant_id,
        forecast_date=forecast_date,
        latitude=latitude,
        longitude=longitude,
        plant_type=plant_type,
        capacity_mw=capacity_mw,
    )
    return result


@router.get("/model-info")
async def get_model_info():
    """查询已加载的预测模型信息"""
    from ml.models.predictor import get_predictor

    predictor = get_predictor()
    return predictor.get_model_info()


@router.post("/train")
async def trigger_training(background_tasks: BackgroundTasks):
    """触发模型训练（后台执行）"""
    async def _train():
        from ml.models.trainer import train_all
        try:
            await asyncio.get_event_loop().run_in_executor(None, train_all)
            logger.info("✅ 模型训练后台任务完成")
        except Exception as e:
            logger.error(f"❌ 模型训练失败: {e}")

    background_tasks.add_task(_train)
    return {"message": "模型训练已在后台启动，请稍后通过 /model-info 查看进度"}


@router.get("/accuracy/{plant_id}", response_model=ForecastAccuracy)
async def get_forecast_accuracy(
    plant_id: str,
    db: AsyncSession = Depends(get_db),
):
    """获取某电站的预测准确率"""
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
