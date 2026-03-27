"""
特征工程 - 光伏/风电功率预测
根据气象因素构建输入特征
"""
import numpy as np
import pandas as pd
from datetime import datetime
from typing import Optional


# ─── 光伏特征 ──────────────────────────────────────────────────────────────

def solar_zenith_angle(day_of_year: int, hour: float, latitude: float = 30.0) -> float:
    """
    计算太阳天顶角（度）
    基于简化天文公式
    """
    #declination = 23.45 * sin(360/365 * (day_of_year - 81))
    declination = 23.45 * np.sin(np.radians(360 / 365 * (day_of_year - 81)))
    lat_rad = np.radians(latitude)
    hour_angle = 15 * (hour - 12)  # 每小时15度

    cos_zenith = (
        np.sin(lat_rad) * np.sin(np.radians(declination)) +
        np.cos(lat_rad) * np.cos(np.radians(declination)) * np.cos(np.radians(hour_angle))
    )
    cos_zenith = np.clip(cos_zenith, -1, 1)
    zenith = np.degrees(np.arccos(cos_zenith))
    return zenith


def solar_irradiance_estimate(
    irradiance: float,          # 直接辐照 W/m²
    hour: float,               # 小时 (0-24)
    day_of_year: int,          # 一年中第几天
    cloud_cover: float = 0.0,  # 云量 0-1
    latitude: float = 30.0,
) -> dict:
    """
    估算光伏可利用辐照
    考虑太阳高度角、晴天指数、云量衰减
    """
    zenith = solar_zenith_angle(day_of_year, hour, latitude)
    # 太阳高度角 = 90 - 天顶角
    solar_elevation = max(90 - zenith, 0)

    if solar_elevation <= 0:
        return {
            "effective_irradiance": 0.0,
            "solar_elevation": 0.0,
            "clearness_index": 0.0,
        }

    # 晴天大气透射率（理想条件）
    tau = 0.7
    # 太阳高度角对辐照的修正
    height_factor = np.sin(np.radians(solar_elevation))
    # 云量衰减：云量每增加0.1，透射率降低约15%
    cloud_factor = 1.0 - 0.4 * cloud_cover
    # 晴天指数（实际/理想）
    kt = irradiance / (1000 * height_factor + 1e-6) if irradiance > 0 else 0
    kt = np.clip(kt, 0, 1.2)

    effective_irradiance = irradiance * cloud_factor * np.clip(height_factor, 0, 1)

    return {
        "effective_irradiance": float(effective_irradiance),
        "solar_elevation": float(solar_elevation),
        "clearness_index": float(kt),
        " zenith": float(zenith),
    }


def pv_features(
    irradiance: float,      # W/m² 直接辐射
    temperature: float,     # °C 环境温度
    hour: float,            # 小时 0-24
    day_of_year: int,       # 1-366
    latitude: float = 30.0,
    altitude: float = 0.0,   # 海拔 m
    capacity_mw: float = 100.0,  # 装机容量 MW
) -> dict:
    """
    构建光伏预测特征向量
    包含气象特征、时间特征、光伏物理特征
    """
    zenith = solar_zenith_angle(day_of_year, hour, latitude)
    solar_elevation = max(90 - zenith, 0)

    # 有效辐照
    eff = solar_irradiance_estimate(irradiance, hour, day_of_year, cloud_cover=0.0, latitude=latitude)

    # 归一化辐照（0-1，标准条件1000W/m²）
    norm_irr = np.clip(irradiance / 1000.0, 0, 1.5)

    # 温度对功率的影响（光伏板温度≠环境温度，经验公式）
    panel_temp = temperature + (irradiance / 800.0) * 20  # 强辐照下板温可高20-30°C
    temp_factor = 1.0 - 0.004 * max(panel_temp - 25, 0)  # 每高1°C降低0.4%

    # 季节因子（冬季低，夏季高，与纬度相关）
    seasonal_factor = np.sin(2 * np.pi * (day_of_year - 80) / 365)

    # 日内因子（日出日落，中午高峰）
    hour_factor = np.sin(np.pi * (hour - 6) / (14 if 6 <= hour <= 20 else 8))
    hour_factor = max(hour_factor, 0)

    return {
        "irradiance": irradiance,
        "irradiance_normalized": norm_irr,
        "effective_irradiance": eff["effective_irradiance"],
        "temperature": temperature,
        "panel_temperature": panel_temp,
        "temp_factor": max(temp_factor, 0),
        "solar_elevation": solar_elevation,
        "solar_elevation_cos": np.cos(np.radians(solar_elevation)),
        "seasonal_factor": seasonal_factor,
        "hour_factor": hour_factor,
        "day_of_year_sin": np.sin(2 * np.pi * day_of_year / 365),
        "day_of_year_cos": np.cos(2 * np.pi * day_of_year / 365),
        "hour_sin": np.sin(2 * np.pi * hour / 24),
        "hour_cos": np.cos(2 * np.pi * hour / 24),
        "norm_irr_x_seasonal": norm_irr * seasonal_factor,
        "norm_irr_x_temp": norm_irr * temp_factor,
        "capacity_mw": capacity_mw,
    }


# ─── 风电特征 ──────────────────────────────────────────────────────────────

def wind_power_density(wind_speed: float, air_density: float = 1.225) -> float:
    """风功率密度 W/m²（空气密度默认1.225 kg/m³）"""
    return 0.5 * air_density * (wind_speed ** 3)


def wind_capacity_factor(wind_speed: float, rated_speed: float = 12.0, cut_in: float = 3.0, cut_out: float = 25.0) -> float:
    """
    估算风电机组利用小时数比例
    基于典型风速分布的简化模型
    """
    if wind_speed < cut_in or wind_speed > cut_out:
        return 0.0
    if wind_speed >= rated_speed:
        return 1.0
    # 近似三次方关系
    return (wind_speed ** 3 - cut_in ** 3) / (rated_speed ** 3 - cut_in ** 3)


def wind_features(
    wind_speed: float,       # m/s 10m高度风速
    temperature: float,     # °C
    hour: float,             # 小时
    day_of_year: int,        # 1-366
    roughness: float = 0.1,   # 地表粗糙度
    capacity_mw: float = 100.0,
) -> dict:
    """
    构建风电预测特征向量
    """
    # 粗糙度影响的风速廓线修正（简化为指数廓线）
    # 假设测风高度10m，需要推到轮毂高度（通常80-120m）
    hub_height = 100.0
    wind_speed_hub = wind_speed * (hub_height / 10) ** roughness

    # 空气密度随温度变化（理想气体）
    # ρ = P/(RT)，近似认为气压不变，密度 ∝ 1/T(K)
    air_density = 1.225 * (273.15 / (temperature + 273.15))

    # 风功率密度
    power_density = wind_power_density(wind_speed_hub, air_density)

    # 容量因子
    cf = wind_capacity_factor(wind_speed_hub)

    # 湍流强度（风速标准差/平均风速），与天气相关
    turbulence = 0.1 + 0.05 * (1 if wind_speed > 15 else 0)  # 简化

    # 季节/日内因子（风速有日变化，夜间高白天低）
    diurnal_factor = 1.0 + 0.1 * np.sin(2 * np.pi * (hour - 4) / 24)

    return {
        "wind_speed": wind_speed,
        "wind_speed_hub": wind_speed_hub,
        "air_density": air_density,
        "power_density": power_density,
        "capacity_factor": cf,
        "turbulence": turbulence,
        "temperature": temperature,
        "diurnal_factor": diurnal_factor,
        "hour_sin": np.sin(2 * np.pi * hour / 24),
        "hour_cos": np.cos(2 * np.pi * hour / 24),
        "seasonal_factor": np.sin(2 * np.pi * (day_of_year - 80) / 365),
        "wind_cubed": wind_speed_hub ** 3,
        "wind_squared": wind_speed_hub ** 2,
        "log_wind": np.log(wind_speed_hub + 1),
        "capacity_mw": capacity_mw,
    }


# ─── 通用特征 ──────────────────────────────────────────────────────────────

def build_features(
    plant_type: str,         # '光伏' 或 '风电'
    irradiance: float,       # W/m²
    wind_speed: float,        # m/s
    temperature: float,       # °C
    hour: float,
    day_of_year: int,
    latitude: float = 30.0,
    capacity_mw: float = 100.0,
) -> dict:
    """统一特征构建接口"""
    if plant_type in ("光伏", "solar", "pv", "PV"):
        return pv_features(irradiance, temperature, hour, day_of_year, latitude, 0, capacity_mw)
    elif plant_type in ("风电", "wind", "WT"):
        return wind_features(wind_speed, temperature, hour, day_of_year, 0.1, capacity_mw)
    else:
        raise ValueError(f"Unknown plant type: {plant_type}")


def features_to_array(features: dict) -> np.ndarray:
    """将特征字典转换为numpy数组（用于模型输入）"""
    # 排除非数值字段
    exclude = {"capacity_mw"}
    arr = np.array([[v for k, v in features.items() if k not in exclude]], dtype=np.float32)
    return arr


FEATURE_NAMES_PV = [
    "irradiance_normalized", "effective_irradiance", "temp_factor",
    "solar_elevation_cos", "seasonal_factor", "hour_factor",
    "day_of_year_sin", "day_of_year_cos", "hour_sin", "hour_cos",
    "norm_irr_x_seasonal", "norm_irr_x_temp",
]

FEATURE_NAMES_WIND = [
    "capacity_factor", "wind_speed_hub", "power_density",
    "diurnal_factor", "hour_sin", "hour_cos",
    "seasonal_factor", "wind_cubed", "wind_squared", "log_wind",
]
