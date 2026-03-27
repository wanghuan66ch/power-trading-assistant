"""
数据模型 - 电力交易相关数据表
"""
from datetime import datetime
from sqlalchemy import String, Integer, Float, DateTime, Text, Boolean, Index
from sqlalchemy.orm import Mapped, mapped_column

from core.database import Base


class ProvincePrice(Base):
    """各省电力成交价格"""
    __tablename__ = "province_prices"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    province: Mapped[str] = mapped_column(String(32), index=True)  # 省份
    price_type: Mapped[str] = mapped_column(String(32))  # 尖/峰/平/谷
    price: Mapped[float] = mapped_column(Float)  # 元/兆瓦时
    capacity_mw: Mapped[float] = mapped_column(Float)  # 成交容量 MW
    recorded_at: Mapped[datetime] = mapped_column(DateTime, index=True)  # 记录时间
    source: Mapped[str] = mapped_column(String(255))  # 数据来源
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)


class TradeRecord(Base):
    """交易记录"""
    __tablename__ = "trade_records"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    trade_no: Mapped[str] = mapped_column(String(64), unique=True)  # 交易编号
    trade_type: Mapped[str] = mapped_column(String(16))  # 购电/售电
    counterparty: Mapped[str] = mapped_column(String(255))  # 交易对方
    province: Mapped[str] = mapped_column(String(32))
    capacity_mw: Mapped[float] = mapped_column(Float)  # 电量 MW
    price: Mapped[float] = mapped_column(Float)  # 价格 元/兆瓦时
    start_date: Mapped[datetime] = mapped_column(DateTime)
    end_date: Mapped[datetime] = mapped_column(DateTime)
    status: Mapped[str] = mapped_column(String(16), default="active")  # active/completed/cancelled
    notes: Mapped[str] = mapped_column(Text, default="")
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    __table_args__ = (
        Index("idx_trade_dates", "start_date", "end_date"),
        Index("idx_trade_province", "province"),
    )


class ForecastRecord(Base):
    """功率预测记录"""
    __tablename__ = "forecast_records"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    plant_id: Mapped[str] = mapped_column(String(64), index=True)  # 电站ID
    plant_type: Mapped[str] = mapped_column(String(16))  # 光伏/风电
    province: Mapped[str] = mapped_column(String(32))
    forecast_time: Mapped[datetime] = mapped_column(DateTime, index=True)  # 预测时间点
    predicted_power_mw: Mapped[float] = mapped_column(Float)  # 预测功率 MW
    actual_power_mw: Mapped[float] = mapped_column(Float, nullable=True)  # 实际功率（后续填入）
    weather_condition: Mapped[str] = mapped_column(String(64))  # 天气状况
    irradiance: Mapped[float] = mapped_column(Float, nullable=True)  # 辐照度
    wind_speed: Mapped[float] = mapped_column(Float, nullable=True)  # 风速
    confidence: Mapped[float] = mapped_column(Float, nullable=True)  # 预测置信度
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)


class PriceAlert(Base):
    """价格预警"""
    __tablename__ = "price_alerts"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    province: Mapped[str] = mapped_column(String(32))
    alert_type: Mapped[str] = mapped_column(String(32))  # high_price/low_price/big_swing
    threshold_price: Mapped[float] = mapped_column(Float)  # 触发阈值
    current_price: Mapped[float] = mapped_column(Float)  # 当前价格
    message: Mapped[str] = mapped_column(Text)
    is_sent: Mapped[bool] = mapped_column(Boolean, default=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
