"""
爬虫服务 - 电力交易中心数据抓取
已升级为真实数据爬虫系统
"""
import logging
from datetime import datetime
from typing import Optional

from sqlalchemy.ext.asyncio import AsyncSession

from models.trade import ProvincePrice
from spiders.runner import SpiderRunner
from spiders.provinces.guangdong import GuangdongSpider
from spiders.provinces.shandong import ShandongSpider
from spiders.provinces.national import NationalSpider

logger = logging.getLogger(__name__)


class ElectricityPriceSpider:
    """
    电力交易中心价格爬虫（主服务）
    协调各省级爬虫抓取真实数据
    """

    def __init__(self, db: AsyncSession):
        self.db = db
        self.runner = SpiderRunner(db)

    async def crawl_latest_prices(self) -> int:
        """
        抓取各省最新成交价格
        返回新增记录数
        """
        logger.info("🚀 开始抓取各省电力交易中心数据...")
        stats = await self.runner.run_all()
        total = stats.get("_total", 0)
        logger.info(f"✅ 抓取完成，总计 {total} 条新记录: {stats}")
        return total

    async def crawl_province(self, province: str) -> int:
        """抓取指定省份数据"""
        logger.info(f"🚀 开始抓取 {province} 电力交易数据...")
        count = await self.runner.run_province(province)
        logger.info(f"✅ {province} 抓取完成，{count} 条新记录")
        return count

    async def test_spiders(self) -> dict:
        """测试各爬虫连通性"""
        results = {}

        test_spiders = [
            ("广东", GuangdongSpider()),
            ("山东", ShandongSpider()),
            ("全国", NationalSpider()),
        ]

        for name, spider in test_spiders:
            try:
                async with spider:
                    data = await spider.crawl()
                    results[name] = {
                        "status": "ok",
                        "count": len(data),
                        "data": [
                            {
                                "province": r.province,
                                "price_type": r.price_type,
                                "price": r.price,
                                "capacity_mw": r.capacity_mw,
                                "recorded_at": r.recorded_at,
                                "source": r.source[:50] if r.source else "",
                                "is_real": r.is_real_data,
                            }
                            for r in data[:5]  # 只返回前5条
                        ],
                    }
            except Exception as e:
                results[name] = {"status": "error", "message": str(e)}

        return results
