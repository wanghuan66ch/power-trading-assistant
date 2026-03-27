"""
爬虫服务 - 电力交易中心数据抓取
"""
import logging
from datetime import datetime
from typing import Optional

import httpx
from sqlalchemy.ext.asyncio import AsyncSession

from core.config import settings
from models.trade import ProvincePrice

logger = logging.getLogger(__name__)


class ElectricityPriceSpider:
    """电力交易中心价格爬虫"""

    # 各省电力交易中心公开数据 URL（示例，实际需根据各中心调整）
    PROVINCE_CRAWLER_URLS = {
        "广东": "https://www.gdep.com.cn/eprice/web/lists.html",
        "江苏": "https://www.js.sgcc.com.cn/",
        "浙江": "https://www.zj.sgcc.com.cn/",
        "山东": "https://www.sd.sgcc.com.cn/",
        "北京": "https://www.bj.sgcc.com.cn/",
    }

    def __init__(self, db: AsyncSession):
        self.db = db
        self.client: Optional[httpx.AsyncClient] = None

    async def _get_client(self) -> httpx.AsyncClient:
        if self.client is None:
            self.client = httpx.AsyncClient(
                timeout=30.0,
                headers={"User-Agent": settings.spider_user_agent},
                follow_redirects=True,
            )
        return self.client

    async def close(self):
        if self.client:
            await self.client.aclose()

    async def crawl_latest_prices(self) -> int:
        """抓取各省最新成交价格"""
        total_count = 0

        for province, url in self.PROVINCE_CRAWLER_URLS.items():
            try:
                count = await self._crawl_province(province, url)
                total_count += count
            except Exception as e:
                logger.error(f"抓取 {province} 数据失败: {e}")

        return total_count

    async def _crawl_province(self, province: str, url: str) -> int:
        """抓取单个省份数据"""
        client = await self._get_client()

        try:
            response = await client.get(url)
            response.raise_for_status()
            html = response.text

            # 使用 BeautifulSoup 解析（这里需要根据实际页面结构调整）
            from bs4 import BeautifulSoup
            soup = BeautifulSoup(html, "lxml")

            # 示例：解析电价表格（实际需要根据目标网站结构调整）
            count = 0
            rows = soup.select("table.price-list tr")  # CSS选择器需要根据实际页面调整

            for row in rows:
                try:
                    cols = row.find_all("td")
                    if len(cols) < 4:
                        continue

                    # 根据实际页面结构调整解析逻辑
                    price_record = ProvincePrice(
                        province=province,
                        price_type=self._extract_price_type(cols),
                        price=float(self._extract_price(cols)),
                        capacity_mw=float(self._extract_capacity(cols)),
                        recorded_at=datetime.utcnow(),
                        source=url,
                    )
                    self.db.add(price_record)
                    count += 1
                except Exception as e:
                    logger.warning(f"解析行失败: {e}")
                    continue

            await self.db.commit()
            logger.info(f"✅ {province}: 新增 {count} 条记录")
            return count

        except httpx.HTTPStatusError as e:
            logger.error(f"HTTP 错误 {province}: {e.response.status_code}")
        except Exception as e:
            logger.error(f"抓取失败 {province}: {e}")

        return 0

    def _extract_price_type(self, cols) -> str:
        """从列中提取电价类型（尖/峰/平/谷）"""
        # 示例，需要根据实际页面结构调整
        text = cols[0].get_text(strip=True)
        return text if text else "尖峰谷平时段"

    def _extract_price(self, cols) -> str:
        """提取价格"""
        # 示例，需要根据实际页面结构调整
        return cols[1].get_text(strip=True).replace("元/兆瓦时", "").replace(",", "")

    def _extract_capacity(self, cols) -> str:
        """提取成交容量"""
        # 示例，需要根据实际页面结构调整
        return cols[2].get_text(strip=True).replace("MW", "").replace(",", "")
