"""
各省电力交易中心爬虫
"""
from spiders.provinces.guangdong import GuangdongSpider
from spiders.provinces.shandong import ShandongSpider
from spiders.provinces.national import NationalSpider

__all__ = [
    "GuangdongSpider",
    "ShandongSpider",
    "NationalSpider",
]
