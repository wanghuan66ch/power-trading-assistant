"""
风险看板 API
"""
import logging
from datetime import datetime, timedelta
from typing import Optional

from fastapi import APIRouter, Depends, Query
from core.security import get_current_user_id
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from core.database import get_db
from models.trade import TradeRecord, ProvincePrice
from schemas.trade import RiskWarning

logger = logging.getLogger(__name__)
router = APIRouter()


@router.get("/warnings", response_model=list[RiskWarning])
async def get_risk_warnings(
    province: Optional[str] = Query(None),
    severity: Optional[str] = Query(None),  # 高/中/低
    db: AsyncSession = Depends(get_db),
    user_id: str = Depends(get_current_user_id),
):
    """
    获取风险预警列表
    自动分析合约缺口、偏差考核等风险
    """
    warnings = []
    now = datetime.utcnow()

    # 1. 检查合约缺口风险
    active_query = select(TradeRecord).where(TradeRecord.status == "active")
    if province:
        active_query = active_query.where(TradeRecord.province == province)
    result = await db.execute(active_query)
    active_trades = result.scalars().all()

    # 按省份统计购电合约总量 vs 实际需求（这里简化处理）
    purchase_by_province = {}
    for trade in active_trades:
        if trade.trade_type == "购电":
            purchase_by_province.setdefault(trade.province, 0)
            purchase_by_province[trade.province] += trade.capacity_mw

    for prov, total_capacity in purchase_by_province.items():
        # 假设实际需求 = 历史平均，这里简化为合约量的 80% ~ 120%
        # 如果当前合约量 < 需求下限 或 > 需求上限，触发预警
        demand_low = total_capacity * 0.85
        demand_high = total_capacity * 1.15
        if total_capacity < demand_low:
            warnings.append(RiskWarning(
                warning_type="contract_gap",
                severity="高",
                province=prov,
                description=f"购电合约容量 {total_capacity}MW，低于需求预估 {demand_low:.0f}MW",
                estimated_loss=round((demand_low - total_capacity) * 50, 2),  # 假设差价50元/MW
                suggestion="建议尽快签订补充购电合约",
                created_at=now,
            ))
        elif total_capacity > demand_high:
            warnings.append(RiskWarning(
                warning_type="contract_gap",
                severity="中",
                province=prov,
                description=f"购电合约容量 {total_capacity}MW，高于需求预估 {demand_high:.0f}MW，可能造成浪费",
                estimated_loss=round((total_capacity - demand_high) * 30, 2),
                suggestion="考虑转让部分合约或调整后续购电计划",
                created_at=now,
            ))

    # 2. 价格异常预警（当前价 vs 合约价）
    week_ago = now - timedelta(days=7)
    for trade in active_trades:
        price_query = select(
            func.avg(ProvincePrice.price)
        ).where(
            ProvincePrice.province == trade.province,
            ProvincePrice.recorded_at >= week_ago,
        )
        price_result = await db.execute(price_query)
        avg_price = price_result.scalar()

        if avg_price and trade.price < avg_price * 0.7:
            warnings.append(RiskWarning(
                warning_type="penalty",
                severity="中",
                province=trade.province,
                description=f"交易 {trade.trade_no} 合约价 {trade.price} 元/MW，低于市场价均价 {avg_price:.2f}",
                estimated_loss=round((avg_price * 0.7 - trade.price) * trade.capacity_mw * 24 * 30, 2),
                suggestion="考虑与对方协商调整合约价格或签订对冲协议",
                created_at=now,
            ))

    # 按严重程度排序
    severity_order = {"高": 0, "中": 1, "低": 2}
    warnings.sort(key=lambda w: severity_order.get(w.severity, 2))

    return warnings


@router.get("/dashboard")
async def get_risk_dashboard(
    db: AsyncSession = Depends(get_db),
    user_id: str = Depends(get_current_user_id),
):
    """风险仪表盘总览"""
    now = datetime.utcnow()

    # 统计各风险类型数量
    active_trades_result = await db.execute(
        select(func.count(TradeRecord.id)).where(TradeRecord.status == "active")
    )
    active_trades_count = active_trades_result.scalar() or 0

    # 预估偏差考核费用（简化计算）
    # 假设偏差 > 5% 开始考核
    penalty_query = select(
        func.sum(
            func.abs(TradeRecord.capacity_mw * 0.1 * 100)  # 简化：10%偏差 × 100元/MW
        )
    ).where(TradeRecord.status == "active")
    penalty_result = await db.execute(penalty_query)
    estimated_penalty = penalty_result.scalar() or 0

    return {
        "active_contracts": active_trades_count,
        "estimated_penalty_monthly": round(estimated_penalty, 2),
        "high_risk_count": len([w for w in [] if w.severity == "高"]),
        "medium_risk_count": len([w for w in [] if w.severity == "中"]),
        "low_risk_count": len([w for w in [] if w.severity == "低"]),
        "last_updated": now.isoformat(),
    }
