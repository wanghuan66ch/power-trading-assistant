"""
功率预测服务 - 基于气象数据的 AI 预测
"""
import logging
from datetime import datetime, timedelta
from typing import Optional

import httpx
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from core.config import settings
from models.trade import ForecastRecord

logger = logging.getLogger(__name__)


class PowerForecastService:
    """光伏/风电功率预测服务"""

    def __init__(self, db: AsyncSession):
        self.db = db
        self.http_client: Optional[httpx.AsyncClient] = None

    async def predict(
        self,
        plant_id: str,
        forecast_date: datetime,
        latitude: float = 30.0,
        longitude: float = 120.0,
    ) -> dict:
        """
        执行功率预测

        流程：
        1. 获取气象预报数据（辐照度/风速/温度）
        2. 调用 AI 模型预测出力
        3. 存入数据库
        """
        # Step 1: 获取气象数据
        weather = await self._fetch_weather(latitude, longitude, forecast_date)
        if not weather:
            return {"error": "获取气象数据失败"}

        # Step 2: 调用预测模型
        predicted_power = await self._run_ml_model(
            plant_type="光伏",  # 根据plant_id判断
            irradiance=weather.get("irradiance", 0),
            wind_speed=weather.get("wind_speed", 0),
            temperature=weather.get("temperature", 25),
            capacity_mw=100,  # 假设100MW装机
        )

        # Step 3: 保存预测记录
        forecast = ForecastRecord(
            plant_id=plant_id,
            plant_type="光伏",
            province="浙江",
            forecast_time=forecast_date,
            predicted_power_mw=predicted_power,
            weather_condition=weather.get("weather_condition", "未知"),
            irradiance=weather.get("irradiance"),
            wind_speed=weather.get("wind_speed"),
            confidence=0.85,  # 简化
        )
        self.db.add(forecast)
        await self.db.commit()

        return {
            "plant_id": plant_id,
            "forecast_time": forecast_date.isoformat(),
            "predicted_power_mw": round(predicted_power, 2),
            "confidence": 0.85,
            "weather": weather,
        }

    async def _fetch_weather(
        self,
        lat: float,
        lon: float,
        target_date: datetime,
    ) -> Optional[dict]:
        """从 Open-Meteo 获取气象预报"""
        try:
            if not self.http_client:
                self.http_client = httpx.AsyncClient(timeout=30.0)

            params = {
                "latitude": lat,
                "longitude": lon,
                "hourly": "temperature_2m,direct_radiation,wind_speed_10m",
                "forecast_days": 7,
                "timezone": "Asia/Shanghai",
            }
            response = await self.http_client.get(
                "https://api.open-meteo.com/v1/forecast",
                params=params,
            )
            response.raise_for_status()
            data = response.json()

            # 找到目标时间的数据
            hourly = data.get("hourly", {})
            times = hourly.get("time", [])
            target_str = target_date.strftime("%Y-%m-%dT%H:00")

            if target_str in times:
                idx = times.index(target_str)
                return {
                    "temperature": hourly["temperature_2m"][idx],
                    "irradiance": hourly["direct_radiation"][idx],
                    "wind_speed": hourly["wind_speed_10m"][idx],
                    "weather_condition": self._weather_code_to_text(
                        data.get("hourly", {}).get("weather_code", [0])[idx]
                    ),
                }

            return None

        except Exception as e:
            logger.error(f"获取气象数据失败: {e}")
            return None

    async def _run_ml_model(
        self,
        plant_type: str,
        irradiance: float,
        wind_speed: float,
        temperature: float,
        capacity_mw: float,
    ) -> float:
        """
        运行机器学习预测模型
        实际使用 XGBoost / LightGBM 加载预训练模型
        这里做简化演示
        """
        if plant_type == "光伏":
            # 简化的光伏出力模型：功率 = 容量 × 辐照率 × 温度系数
            irradiance_factor = min(irradiance / 800, 1.0)  # 800 W/m² 为标准辐照
            temp_factor = 1 - 0.004 * max(temperature - 25, 0)  # 温度每高1度降低0.4%
            predicted = capacity_mw * irradiance_factor * temp_factor
        elif plant_type == "风电":
            # 简化风电模型：功率 ∝ 风速^3
            if wind_speed < 3 or wind_speed > 25:
                predicted = 0
            else:
                rated = 12  # 额定风速 m/s
                if wind_speed >= rated:
                    predicted = capacity_mw
                else:
                    predicted = capacity_mw * (wind_speed ** 3) / (rated ** 3)
        else:
            predicted = capacity_mw * 0.3

        return max(predicted, 0)

    def _weather_code_to_text(self, code: int) -> str:
        """WMO 天气代码转文字"""
        mapping = {
            0: "晴",
            1: "晴间多云",
            2: "多云",
            3: "阴",
            45: "雾",
            51: "小毛毛雨",
            53: "中毛毛雨",
            55: "大毛毛雨",
            61: "小雨",
            63: "中雨",
            65: "大雨",
            71: "小雪",
            73: "中雪",
            75: "大雪",
            80: "阵雨",
            95: "雷暴",
        }
        return mapping.get(code, f"代码{code}")
