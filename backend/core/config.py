"""
核心配置文件
"""
from pathlib import Path
from pydantic_settings import BaseSettings
from pydantic import Field


class Settings(BaseSettings):
    """应用配置"""

    # 服务
    host: str = "0.0.0.0"
    port: int = 8000
    debug: bool = True

    # 数据库
    database_url: str = "sqlite+aiosqlite:////home/wanghuan/code/power-trading-assistant/power_trading.db"

    # JWT 密钥
    secret_key: str = Field(default="change-me-in-production-abc123xyz", env="SECRET_KEY")

    # 电力交易中心 API（公开数据）
    electricity交易中心_base: str = "https://www.95598.cn"  #  example

    # 气象 API（用于功率预测）
    weather_api_key: str = Field(default="", env="WEATHER_API_KEY")
    weather_api_base: str = "https://api.open-meteo.com/v1"

    # Redis（缓存）
    redis_url: str = "redis://localhost:6379/0"

    # 爬虫配置
    spider_user_agent: str = (
        "PowerTradingAssistant/0.1 (+mailto:admin@example.com)"
    )

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"


settings = Settings()
