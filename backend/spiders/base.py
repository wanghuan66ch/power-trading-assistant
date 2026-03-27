"""
爬虫基类
"""
import logging
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Optional
import httpx
from bs4 import BeautifulSoup

from core.config import settings

logger = logging.getLogger(__name__)


@dataclass
class CrawlResult:
    """爬取结果"""
    province: str
    price_type: str           # 尖峰/高峰/平段/低谷/综合均价
    price: float               # 元/兆瓦时
    capacity_mw: float         # 成交容量 MW
    recorded_at: str           # 记录时间 ISO字符串
    source: str                # 数据来源URL
    source_name: str           # 数据来源名称
    is_real_data: bool = True  # 是否是真实数据（vs估算/模拟）
    notes: str = ""            # 备注
    raw_data: dict = field(default_factory=dict)  # 原始数据


class BaseSpider(ABC):
    """各省电力交易中心爬虫基类"""

    name: str = "base_spider"
    province: str = ""

    def __init__(self):
        self.client: Optional[httpx.AsyncClient] = None
        self._headers = {
            "User-Agent": settings.spider_user_agent,
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
            "Accept-Language": "zh-CN,zh;q=0.9,en;q=0.8",
        }

    async def _get_client(self) -> httpx.AsyncClient:
        if self.client is None:
            self.client = httpx.AsyncClient(
                timeout=30.0,
                headers=self._headers,
                follow_redirects=True,
            )
        return self.client

    async def close(self):
        if self.client:
            await self.client.aclose()
            self.client = None

    async def fetch(self, url: str, method: str = "GET", **kwargs) -> Optional[str]:
        """发送HTTP请求并返回页面内容"""
        try:
            client = await self._get_client()
            if method.upper() == "POST":
                response = await client.post(url, **kwargs)
            else:
                response = await client.get(url, **kwargs)
            response.raise_for_status()
            return response.text
        except httpx.HTTPStatusError as e:
            logger.warning(f"[{self.name}] HTTP {e.response.status_code} for {url}")
        except httpx.TimeoutException:
            logger.warning(f"[{self.name}] Timeout for {url}")
        except Exception as e:
            logger.error(f"[{self.name}] Error fetching {url}: {e}")
        return None

    def parse_html(self, html: str) -> BeautifulSoup:
        """解析HTML"""
        return BeautifulSoup(html, "lxml")

    @abstractmethod
    async def crawl(self) -> list[CrawlResult]:
        """
        执行爬取，返回结果列表
        由子类实现
        """
        ...

    async def __aenter__(self):
        return self

    async def __aexit__(self, *args):
        await self.close()
