"""
交易管理 API
"""
import logging
import uuid
from datetime import datetime
from typing import Optional

from fastapi import APIRouter, Depends, Query, HTTPException
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from core.database import get_db
from models.trade import TradeRecord
from schemas.trade import (
    TradeRecordCreate, TradeRecordUpdate, TradeRecordResponse, TradeStatistics
)

logger = logging.getLogger(__name__)
router = APIRouter()


@router.get("/", response_model=list[TradeRecordResponse])
async def list_trades(
    province: Optional[str] = Query(None),
    status: Optional[str] = Query(None),
    trade_type: Optional[str] = Query(None),
    limit: int = Query(50, le=500),
    offset: int = Query(0),
    db: AsyncSession = Depends(get_db),
):
    """查询交易记录列表"""
    query = select(TradeRecord).order_by(TradeRecord.created_at.desc())
    if province:
        query = query.where(TradeRecord.province == province)
    if status:
        query = query.where(TradeRecord.status == status)
    if trade_type:
        query = query.where(TradeRecord.trade_type == trade_type)

    query = query.limit(limit).offset(offset)
    result = await db.execute(query)
    return result.scalars().all()


@router.post("/", response_model=TradeRecordResponse)
async def create_trade(
    trade: TradeRecordCreate,
    db: AsyncSession = Depends(get_db),
):
    """新增交易记录"""
    trade_no = f"T-{datetime.utcnow().strftime('%Y%m%d%H%M%S')}-{uuid.uuid4().hex[:6].upper()}"
    db_trade = TradeRecord(
        trade_no=trade_no,
        trade_type=trade.trade_type,
        counterparty=trade.counterparty,
        province=trade.province,
        capacity_mw=trade.capacity_mw,
        price=trade.price,
        start_date=trade.start_date,
        end_date=trade.end_date,
        notes=trade.notes,
    )
    db.add(db_trade)
    await db.commit()
    await db.refresh(db_trade)
    logger.info(f"新建交易记录: {trade_no}")
    return db_trade


@router.get("/{trade_id}", response_model=TradeRecordResponse)
async def get_trade(trade_id: int, db: AsyncSession = Depends(get_db)):
    """查询单条交易记录"""
    result = await db.execute(select(TradeRecord).where(TradeRecord.id == trade_id))
    trade = result.scalar_one_or_none()
    if not trade:
        raise HTTPException(status_code=404, detail="交易记录不存在")
    return trade


@router.patch("/{trade_id}", response_model=TradeRecordResponse)
async def update_trade(
    trade_id: int,
    update: TradeRecordUpdate,
    db: AsyncSession = Depends(get_db),
):
    """更新交易记录（如状态、备注）"""
    result = await db.execute(select(TradeRecord).where(TradeRecord.id == trade_id))
    trade = result.scalar_one_or_none()
    if not trade:
        raise HTTPException(status_code=404, detail="交易记录不存在")

    if update.status is not None:
        trade.status = update.status
    if update.notes is not None:
        trade.notes = update.notes
    trade.updated_at = datetime.utcnow()

    await db.commit()
    await db.refresh(trade)
    return trade


@router.delete("/{trade_id}")
async def delete_trade(trade_id: int, db: AsyncSession = Depends(get_db)):
    """删除交易记录"""
    result = await db.execute(select(TradeRecord).where(TradeRecord.id == trade_id))
    trade = result.scalar_one_or_none()
    if not trade:
        raise HTTPException(status_code=404, detail="交易记录不存在")

    await db.delete(trade)
    await db.commit()
    return {"message": "删除成功"}


@router.get("/stats/summary", response_model=TradeStatistics)
async def get_trade_statistics(db: AsyncSession = Depends(get_db)):
    """获取交易统计摘要"""
    result = await db.execute(
        select(
            func.count(TradeRecord.id).label("total_trades"),
            func.sum(TradeRecord.capacity_mw).label("total_capacity_mw"),
            func.avg(TradeRecord.price).label("avg_price"),
            func.sum(TradeRecord.capacity_mw * TradeRecord.price).label("total_amount"),
        )
    )
    row = result.one()

    active_result = await db.execute(
        select(func.count(TradeRecord.id)).where(TradeRecord.status == "active")
    )
    active_count = active_result.scalar()

    completed_result = await db.execute(
        select(func.count(TradeRecord.id)).where(TradeRecord.status == "completed")
    )
    completed_count = completed_result.scalar()

    return TradeStatistics(
        total_trades=row.total_trades or 0,
        total_capacity_mw=row.total_capacity_mw or 0,
        avg_price=round(row.avg_price or 0, 2),
        total_amount=row.total_amount or 0,
        active_trades=active_count or 0,
        completed_trades=completed_count or 0,
    )
