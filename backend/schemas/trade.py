"""
Pydantic schemas - API 请求/响应模型
"""
from datetime import datetime
from typing import Optional
from pydantic import BaseModel, Field


# ─── 价格相关 ───────────────────────────────────────────────

class ProvincePriceBase(BaseModel):
    province: str
    price_type: str
    price: float
    capacity_mw: float
    recorded_at: datetime
    source: str


class ProvincePriceCreate(ProvincePriceBase):
    pass


class ProvincePriceResponse(ProvincePriceBase):
    id: int
    created_at: datetime

    class Config:
        from_attributes = True


class PriceTrend(BaseModel):
    """价格趋势"""
    province: str
    price_type: str
    current_price: float
    avg_price_7d: float
    max_price_7d: float
    min_price_7d: float
    change_pct: float  # 涨跌幅 %


# ─── 交易相关 ───────────────────────────────────────────────

class TradeRecordBase(BaseModel):
    trade_type: str = Field(..., description="购电/售电")
    counterparty: str
    province: str
    capacity_mw: float
    price: float
    start_date: datetime
    end_date: datetime
    notes: str = ""


class TradeRecordCreate(TradeRecordBase):
    pass


class TradeRecordUpdate(BaseModel):
    status: Optional[str] = None
    notes: Optional[str] = None


class TradeRecordResponse(TradeRecordBase):
    id: int
    trade_no: str
    status: str
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class TradeStatistics(BaseModel):
    """交易统计"""
    total_trades: int
    total_capacity_mw: float
    avg_price: float
    total_amount: float  # 总金额
    active_trades: int
    completed_trades: int


# ─── 预测相关 ───────────────────────────────────────────────

class ForecastBase(BaseModel):
    plant_id: str
    plant_type: str
    province: str
    forecast_time: datetime
    predicted_power_mw: float
    weather_condition: str
    irradiance: Optional[float] = None
    wind_speed: Optional[float] = None
    confidence: Optional[float] = None


class ForecastCreate(ForecastBase):
    pass


class ForecastResponse(ForecastBase):
    id: int
    actual_power_mw: Optional[float] = None
    created_at: datetime

    class Config:
        from_attributes = True


class ForecastAccuracy(BaseModel):
    """预测准确率"""
    plant_id: str
    plant_type: str
    accuracy_1h: float  # 1小时准确率
    accuracy_24h: float  # 24小时准确率
    mae: float  # 平均绝对误差
    mape: float  # 平均绝对百分比误差


# ─── 策略相关 ───────────────────────────────────────────────

class StrategyRecommendation(BaseModel):
    """策略推荐"""
    strategy_type: str  # 购电推荐/售电推荐/观望
    urgency: str  # 高/中/低
    target_province: str
    suggested_price_range_min: float
    suggested_price_range_max: float
    reasoning: str
    valid_until: datetime


# ─── 风险相关 ───────────────────────────────────────────────

class RiskWarning(BaseModel):
    """风险预警"""
    warning_type: str  # contract_gap/penalty/policy
    severity: str  # 高/中/低
    province: str
    description: str
    estimated_loss: Optional[float] = None  # 预估损失
    suggestion: str
    created_at: datetime
