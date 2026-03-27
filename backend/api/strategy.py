"""
策略推荐 API
"""
import logging
from datetime import datetime, timedelta
from typing import Optional

from fastapi import APIRouter, Depends, Query
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from core.database import get_db
from schemas.trade import StrategyRecommendation
from models.trade import ProvincePrice

logger = logging.getLogger(__name__)
router = APIRouter()


@router.get("/recommend", response_model=list[StrategyRecommendation])
async def get_strategy_recommendations(
    province: Optional[str] = Query(None),
    db: AsyncSession = Depends(get_db),
):
    """
    获取策略推荐
    基于各省价格与历史均值对比，给出购电/售电/观望建议
    """
    recommendations = []
    now = datetime.utcnow()
    week_ago = now - timedelta(days=7)

    # 获取各省最新价格和历史均价
    price_query = select(
        ProvincePrice.province,
        ProvincePrice.price_type,
        func.max(ProvincePrice.price).label("current_price"),
        func.avg(ProvincePrice.price).label("avg_price"),
    ).where(
        ProvincePrice.recorded_at >= week_ago
    ).group_by(
        ProvincePrice.province, ProvincePrice.price_type
    )

    result = await db.execute(price_query)
    rows = result.all()

    for row in rows:
        if not row.current_price or not row.avg_price:
            continue

        price_ratio = row.current_price / row.avg_price if row.avg_price else 1

        if price_ratio > 1.15:
            # 当前价高于均价15%+ → 推荐售电
            recommendations.append(StrategyRecommendation(
                strategy_type="售电推荐",
                urgency="高" if price_ratio > 1.3 else "中",
                target_province=row.province,
                suggested_price_range_min=round(row.current_price * 0.95, 2),
                suggested_price_range_max=round(row.current_price * 1.05, 2),
                reasoning=f"当前价格 {row.current_price} 元/兆瓦时，高于7日均价 {row.avg_price:.2f}，溢价 {price_ratio*100-100:.1f}%",
                valid_until=now + timedelta(hours=24),
            ))
        elif price_ratio < 0.85:
            # 当前价低于均价15%+ → 推荐购电
            recommendations.append(StrategyRecommendation(
                strategy_type="购电推荐",
                urgency="高" if price_ratio < 0.7 else "中",
                target_province=row.province,
                suggested_price_range_min=round(row.current_price * 0.95, 2),
                suggested_price_range_max=round(row.current_price * 1.05, 2),
                reasoning=f"当前价格 {row.current_price} 元/兆瓦时，低于7日均价 {row.avg_price:.2f}，折扣 {100-price_ratio*100:.1f}%",
                valid_until=now + timedelta(hours=24),
            ))

    return recommendations


@router.get("/contract-structure")
async def get_contract_structure_advice(
    province: str = Query(...),
    db: AsyncSession = Depends(get_db),
):
    """
    合约期限结构建议
    给出年度/季度/月度合约的推荐比例
    """
    # 基于当前价格波动率给出建议
    from models.trade import ProvincePrice

    week_ago = datetime.utcnow() - timedelta(days=7)
    result = await db.execute(
        select(
            func.stddev(ProvincePrice.price).label("stddev"),
            func.avg(ProvincePrice.price).label("avg_price"),
        ).where(
            ProvincePrice.province == province,
            ProvincePrice.recorded_at >= week_ago,
        )
    )
    row = result.one()

    if not row or not row.stddev:
        return {"advice": "数据不足，无法给出建议", "structure": []}

    cv = row.stddev / max(row.avg_price, 0.01)  # 变异系数

    if cv > 0.2:
        # 高波动 → 建议多签月度，少签年度
        structure = [
            {"type": "年度", "ratio": 0.3, "reason": "锁定长期低价"},
            {"type": "季度", "ratio": 0.3, "reason": "平衡成本与灵活性"},
            {"type": "月度", "ratio": 0.4, "reason": "当前价格波动大，灵活性优先"},
        ]
    elif cv < 0.1:
        # 低波动 → 建议多签年度
        structure = [
            {"type": "年度", "ratio": 0.6, "reason": "价格稳定，锁定长期合约最划算"},
            {"type": "季度", "ratio": 0.3, "reason": "保留一定灵活性"},
            {"type": "月度", "ratio": 0.1, "reason": "少量月度应对突发"},
        ]
    else:
        structure = [
            {"type": "年度", "ratio": 0.4, "reason": "基础保障"},
            {"type": "季度", "ratio": 0.4, "reason": "灵活调整"},
            {"type": "月度", "ratio": 0.2, "reason": "应对波动"},
        ]

    return {
        "province": province,
        "price_volatility": round(cv * 100, 2),
        "advice": "合理分散合约期限，降低价格波动风险",
        "structure": structure,
    }
