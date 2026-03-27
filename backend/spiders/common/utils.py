"""
通用工具函数
"""
import re
import logging
from datetime import datetime
from typing import Optional

logger = logging.getLogger(__name__)


def parse_price(price_str: str) -> Optional[float]:
    """
    从字符串中提取价格（单位：元/兆瓦时）
    支持格式：'380.3元/兆瓦时', '0.3803元/千瓦时', '380.3厘/千瓦时', '371.60'
    """
    if not price_str:
        return None
    text = str(price_str).strip()

    # 统一转换为元/兆瓦时
    # 厘/千瓦时 -> 元/兆瓦时（*10）
    li_match = re.search(r'([\d.]+)\s*(?:厘|分)/千瓦时', text)
    if li_match:
        return float(li_match.group(1)) * 10

    # 元/千瓦时 -> 元/兆瓦时（*1000）
    kwh_match = re.search(r'([\d.]+)\s*元/千瓦时', text)
    if kwh_match:
        return float(kwh_match.group(1)) * 1000

    # 元/兆瓦时
    mwh_match = re.search(r'([\d.]+)\s*元/兆瓦时', text)
    if mwh_match:
        return float(mwh_match.group(1))

    # 纯数字
    num_match = re.search(r'([\d.]+)', text)
    if num_match:
        val = float(num_match.group(1))
        # 判断是否是元/千瓦时的量级（<10），如果是则转换为元/兆瓦时
        if val < 10:
            return val * 1000
        return val

    return None


def parse_capacity(capacity_str: str) -> Optional[float]:
    """
    从字符串中提取容量（单位：MW）
    支持格式：'1000MW', '1000 万千瓦时', '1.5亿千瓦时'
    """
    if not capacity_str:
        return None
    text = str(capacity_str).strip().replace(",", "").replace("，", "")

    # 亿千瓦时 -> MW（*10000/1000 = *10）
    yi_match = re.search(r'([\d.]+)\s*亿千瓦时', text)
    if yi_match:
        return float(yi_match.group(1)) * 10 * 10000  # 亿kWh -> MWh

    # 万千瓦时 -> MW（直接等于）
    wan_match = re.search(r'([\d.]+)\s*万千瓦时', text)
    if wan_match:
        return float(wan_match.group(1)) * 10

    # MW
    mw_match = re.search(r'([\d.]+)\s*MW', text, re.IGNORECASE)
    if mw_match:
        return float(mw_match.group(1))

    # 万kWh
    wankwh_match = re.search(r'([\d.]+)\s*万kWh', text)
    if wankwh_match:
        return float(wankwh_match.group(1)) * 10

    # 亿kWh
    yikwh_match = re.search(r'([\d.]+)\s*亿kWh', text)
    if yikwh_match:
        return float(yikwh_match.group(1)) * 10 * 10000

    # 纯数字（亿千瓦时级别假设）
    num_match = re.search(r'([\d.]+)', text)
    if num_match:
        return float(num_match.group(1))

    return None


def parse_date(date_str: str) -> Optional[datetime]:
    """
    解析日期字符串
    支持格式：'2025-01-15', '2025年1月15日', '2025/01/15'
    """
    if not date_str:
        return None
    text = str(date_str).strip()

    # ISO格式
    iso_match = re.search(r'(\d{4})-(\d{1,2})-(\d{1,2})', text)
    if iso_match:
        return datetime(int(iso_match.group(1)), int(iso_match.group(2)), int(iso_match.group(3)))

    # 中文格式
    cn_match = re.search(r'(\d{4})年(\d{1,2})月(\d{1,2})日', text)
    if cn_match:
        return datetime(int(cn_match.group(1)), int(cn_match.group(2)), int(cn_match.group(3)))

    # 斜杠格式
    slash_match = re.search(r'(\d{4})/(\d{1,2})/(\d{1,2})', text)
    if slash_match:
        return datetime(int(slash_match.group(1)), int(slash_match.group(2)), int(slash_match.group(3)))

    return None


def extract_price_type(text: str) -> str:
    """从文本中识别电价类型"""
    text = str(text).strip()
    if any(k in text for k in ["尖峰", "尖", "peak"]):
        return "尖峰"
    elif any(k in text for k in ["高峰", "峰", "shoulder"]):
        return "高峰"
    elif any(k in text for k in ["平段", "平", "flat"]):
        return "平段"
    elif any(k in text for k in ["低谷", "谷", "trough", "valley", "low"]):
        return "低谷"
    elif any(k in text for k in ["实时", "现货", "spot"]):
        return "现货"
    elif any(k in text for k in ["日前", "day-ahead"]):
        return "日前"
    return "综合均价"


def safe_float(value, default: float = 0.0) -> float:
    """安全转换为浮点数"""
    try:
        return float(value)
    except (TypeError, ValueError):
        return default
