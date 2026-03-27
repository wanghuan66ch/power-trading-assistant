"""
爬虫运行器
统一执行各省爬虫并保存结果到数据库
"""
import logging
from datetime import datetime
from typing import Optional

from sqlalchemy.ext.asyncio import AsyncSession

from spiders.base import BaseSpider, CrawlResult
from spiders.provinces.guangdong import GuangdongSpider
from spiders.provinces.shandong import ShandongSpider
from spiders.provinces.national import NationalSpider
from models.trade import ProvincePrice

logger = logging.getLogger(__name__)


class SpiderRunner:
    """爬虫运行器"""

    def __init__(self, db: AsyncSession):
        self.db = db
        self.spiders: list[BaseSpider] = [
            GuangdongSpider(),
            ShandongSpider(),
            NationalSpider(),
        ]

    async def run_all(self) -> dict[str, int]:
        """运行所有爬虫，返回各省抓取数量"""
        stats = {}
        total = 0

        for spider in self.spiders:
            try:
                async with spider:
                    results = await spider.crawl()
                    count = await self._save_results(results)
                    stats[spider.name] = count
                    total += count
                    logger.info(f"✅ {spider.name}: 保存 {count} 条记录")
            except Exception as e:
                logger.error(f"❌ {spider.name} 执行失败: {e}")
                stats[spider.name] = 0

        stats["_total"] = total
        return stats

    async def run_province(self, province: str) -> int:
        """运行指定省份的爬虫"""
        spider_map = {
            "广东": GuangdongSpider,
            "山东": ShandongSpider,
            "全国": NationalSpider,
        }

        spider_cls = spider_map.get(province)
        if not spider_cls:
            logger.warning(f"未找到省份对应爬虫: {province}")
            return 0

        spider = spider_cls()
        try:
            async with spider:
                results = await spider.crawl()
                count = await self._save_results(results)
                logger.info(f"✅ {province}: 保存 {count} 条记录")
                return count
        except Exception as e:
            logger.error(f"❌ {province} 爬虫失败: {e}")
            return 0

    async def _save_results(self, results: list[CrawlResult]) -> int:
        """保存爬取结果到数据库"""
        count = 0
        for r in results:
            try:
                recorded_at = parse_iso_date(r.recorded_at)
                record = ProvincePrice(
                    province=r.province,
                    price_type=r.price_type,
                    price=r.price,
                    capacity_mw=r.capacity_mw,
                    recorded_at=recorded_at or datetime.utcnow(),
                    source=r.source,
                )
                self.db.add(record)
                count += 1
            except Exception as e:
                logger.warning(f"保存记录失败: {e}")
                continue

        if count > 0:
            await self.db.commit()
        return count


def parse_iso_date(date_str: str) -> Optional[datetime]:
    """解析ISO格式日期字符串"""
    if not date_str:
        return None
    try:
        # 尝试多种格式
        for fmt in [
            "%Y-%m-%dT%H:%M:%S",
            "%Y-%m-%dT%H:%M:%S.%f",
            "%Y-%m-%d %H:%M:%S",
            "%Y-%m-%d",
        ]:
            try:
                return datetime.strptime(date_str[:19], fmt.replace("%Y-%m-%dT%H:%M:%S", "%Y-%m-%dT%H:%M:%S"))
            except ValueError:
                try:
                    return datetime.strptime(date_str[:19], "%Y-%m-%dT%H:%M:%S")
                except ValueError:
                    pass
        # 手动解析
        if "T" in date_str:
            date_part, time_part = date_str.split("T")
            parts = date_part.split("-")
            if len(parts) == 3 and len(time_part) >= 6:
                h, m, s = int(time_part[0:2]), int(time_part[3:5]), int(time_part[6:8])
                return datetime(int(parts[0]), int(parts[1]), int(parts[2]), h, m, s)
    except Exception:
        pass
    return None
