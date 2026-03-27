"""
功率预测服务 - 基于气象数据的 AI 预测
已升级：集成 LightGBM 训练模型进行真实推理
"""
import logging
from datetime import datetime
from typing import Optional

import httpx
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from core.config import settings
from models.trade import ForecastRecord

logger = logging.getLogger(__name__)

# ─── 懒加载预测器（避免启动时文件未就绪）──────────────────────────────────

_predictor = None


def _get_predictor():
    """获取预测器单例，懒加载避免循环导入"""
    global _predictor
    if _predictor is None:
        try:
            from ml.models.predictor import PowerPredictor
            _predictor = PowerPredictor()
            info = _predictor.get_model_info()
            logger.info(f"🧠 预测器初始化完成: PV={'已加载' if info['pv']['loaded'] else '未加载'}, Wind={'已加载' if info['wind']['loaded'] else '未加载'}")
        except Exception as e:
            logger.warning(f"⚠️ 无法加载 ML 模型，将使用物理模型: {e}")
            _predictor = None
    return _predictor


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
        plant_type: str = "光伏",
        capacity_mw: float = 100.0,
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

        irradiance = weather.get("irradiance", 0.0)
        wind_speed = weather.get("wind_speed", 0.0)
        temperature = weather.get("temperature", 25.0)

        # Step 2: 调用预测模型
        predictor = _get_predictor()
        if predictor:
            result = predictor.predict(
                plant_type=plant_type,
                irradiance=irradiance,
                wind_speed=wind_speed,
                temperature=temperature,
                latitude=latitude,
                capacity_mw=capacity_mw,
            )
            predicted_power = result["predicted_power_mw"]
            confidence = result["confidence"]
            model_type = result.get("model_type", "LightGBM")
        else:
            # 回退物理模型
            predicted_power, confidence, model_type = self._physics_predict(
                plant_type, irradiance, wind_speed, temperature, capacity_mw
            )

        # Step 3: 保存预测记录
        forecast = ForecastRecord(
            plant_id=plant_id,
            plant_type=plant_type,
            province=self._lat_lon_to_province(latitude, longitude),
            forecast_time=forecast_date,
            predicted_power_mw=predicted_power,
            weather_condition=weather.get("weather_condition", "未知"),
            irradiance=irradiance if plant_type == "光伏" else None,
            wind_speed=wind_speed if plant_type == "风电" else None,
            confidence=confidence,
        )
        self.db.add(forecast)
        await self.db.commit()

        return {
            "plant_id": plant_id,
            "plant_type": plant_type,
            "forecast_time": forecast_date.isoformat(),
            "predicted_power_mw": round(predicted_power, 3),
            "capacity_mw": capacity_mw,
            "capacity_factor": round(predicted_power / capacity_mw, 4) if capacity_mw else 0,
            "confidence": round(confidence, 3),
            "model_type": model_type,
            "weather": weather,
        }

    def _physics_predict(
        self,
        plant_type: str,
        irradiance: float,
        wind_speed: float,
        temperature: float,
        capacity_mw: float,
    ) -> tuple[float, float, str]:
        """物理模型回退（当 ML 模型不可用时）"""
        if plant_type == "光伏":
            norm_irr = min(irradiance / 800, 1.0)
            panel_temp = temperature + (irradiance / 800) * 25
            temp_factor = 1.0 - 0.004 * max(panel_temp - 25, 0)
            predicted = capacity_mw * norm_irr * max(temp_factor, 0)
        elif plant_type == "风电":
            if wind_speed < 3 or wind_speed > 25:
                predicted = 0.0
            else:
                rated = 12.0
                if wind_speed >= rated:
                    predicted = capacity_mw
                else:
                    predicted = capacity_mw * (wind_speed ** 3) / (rated ** 3)
        else:
            predicted = capacity_mw * 0.3
        return max(predicted, 0), 0.80, "Physics"

    async def _fetch_weather(
        self,
        lat: float,
        lon: float,
        target_date: datetime,
    ) -> Optional[dict]:
        """从 Open-Meteo 获取气象预报（免费无需API Key）"""
        try:
            if not self.http_client:
                self.http_client = httpx.AsyncClient(timeout=30.0)

            params = {
                "latitude": lat,
                "longitude": lon,
                "hourly": "temperature_2m,direct_radiation,wind_speed_10m,weather_code",
                "forecast_days": 7,
                "timezone": "Asia/Shanghai",
            }
            response = await self.http_client.get(
                "https://api.open-meteo.com/v1/forecast",
                params=params,
            )
            response.raise_for_status()
            data = response.json()

            hourly = data.get("hourly", {})
            times = hourly.get("time", [])
            target_str = target_date.strftime("%Y-%m-%dT%H:00")

            if target_str not in times:
                # 找最接近的小时
                best_idx = min(range(len(times)), key=lambda i: abs(times[i].replace("T", " ").replace(":00", "") - target_str.replace("T", " ").replace(":00", "")))
                idx = best_idx
            else:
                idx = times.index(target_str)

            weather_code = hourly.get("weather_code", [0])[idx]
            weather = {
                "temperature": hourly["temperature_2m"][idx],
                "irradiance": hourly["direct_radiation"][idx],
                "wind_speed": hourly["wind_speed_10m"][idx],
                "weather_condition": self._weather_code_to_text(weather_code),
                "weather_code": weather_code,
            }
            return weather

        except Exception as e:
            logger.error(f"获取气象数据失败: {e}")
            return None

    def _weather_code_to_text(self, code: int) -> str:
        """WMO 天气代码转文字"""
        mapping = {
            0: "晴", 1: "晴间多云", 2: "多云", 3: "阴",
            45: "雾", 48: "雾凇",
            51: "小毛毛雨", 53: "中毛毛雨", 55: "大毛毛雨",
            61: "小雨", 63: "中雨", 65: "大雨",
            71: "小雪", 73: "中雪", 75: "大雪",
            80: "阵雨", 81: "中阵雨", 82: "大阵雨",
            85: "阵雪", 86: "大雪阵雪",
            95: "雷暴", 96: "雷暴+冰雹", 99: "强雷暴+冰雹",
        }
        return mapping.get(code, f"代码{code}")

    def _lat_lon_to_province(self, lat: float, lon: float) -> str:
        """根据经纬度估算省份（简化）"""
        if 20 <= lat <= 30 and 108 <= lon <= 122:
            if lon < 115:
                return "广东" if lat < 26 else "广西"
            return "广东"
        elif 30 <= lat <= 38 and 114 <= lon <= 123:
            if lon < 120:
                return "江苏" if lat < 35 else "安徽"
            return "山东" if lat < 37 else "江苏"
        elif 38 <= lat <= 45 and 115 <= lon <= 126:
            return "山东" if lat < 38 else "河北"
        return "未知"
