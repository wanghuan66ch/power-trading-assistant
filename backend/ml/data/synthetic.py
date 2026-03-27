"""
合成训练数据生成器
基于物理模型生成逼真的光伏/风电历史数据
用于模型训练演示（实际使用时替换为真实历史数据）
"""
import numpy as np
import pandas as pd
from datetime import datetime, timedelta
from typing import Literal
import os

RNG_SEED = 42
rng = np.random.default_rng(RNG_SEED)


# ─── 光伏数据生成 ────────────────────────────────────────────────────────────

def generate_pv_data(
    n_samples: int = 5000,
    latitude: float = 30.0,
    longitude: float = 120.0,
    capacity_mw: float = 100.0,
    start_date: str = "2024-01-01",
) -> pd.DataFrame:
    """
    生成光伏训练数据
    基于太阳辐照物理模型 + 随机天气扰动
    """
    start = pd.to_datetime(start_date)
    dates = [start + timedelta(hours=i * 6) for i in range(n_samples)]  # 每6小时一条

    records = []
    for dt in dates:
        doy = dt.timetuple().tm_yday
        hour = dt.hour + dt.minute / 60.0
        month = dt.month

        # 太阳天顶角
        declination = 23.45 * np.sin(np.radians(360 / 365 * (doy - 81)))
        lat_rad = np.radians(latitude)
        hour_angle = 15 * (hour - 12)
        cos_zenith = (
            np.sin(lat_rad) * np.sin(np.radians(declination)) +
            np.cos(lat_rad) * np.cos(np.radians(declination)) * np.cos(np.radians(hour_angle))
        )
        cos_zenith = np.clip(cos_zenith, -1, 1)
        zenith = np.degrees(np.arccos(cos_zenith))
        solar_elevation = max(90 - zenith, 0)

        if solar_elevation <= 0:
            # 夜间
            records.append({
                "datetime": dt, "latitude": latitude, "longitude": longitude,
                "capacity_mw": capacity_mw, "plant_type": "光伏",
                "hour": hour, "day_of_year": doy, "month": month,
                "irradiance": 0.0, "temperature": _ambient_temp(hour, doy),
                "wind_speed": rng.normal(3, 1), "cloud_cover": rng.uniform(0, 0.3),
                "actual_power_mw": 0.0, "theoretical_power_mw": 0.0,
            })
            continue

        # 理论最大辐照（晴天大气外）
        extra_radiation = 1361 * (1 + 0.033 * np.cos(np.radians(360 * doy / 365)))
        atmospheric_transmission = 0.7
        zenith_factor = np.sin(np.radians(solar_elevation))
        max_irradiance = extra_radiation * atmospheric_transmission * zenith_factor

        # 云量（季节+随机）
        cloud_base = 0.2 + 0.1 * np.cos(np.radians(360 * doy / 365))  # 夏季多云
        cloud_cover = np.clip(rng.beta(2, 5) + cloud_base * 0.5, 0, 1)

        # 实际辐照
        irradiance = max_irradiance * (1 - 0.65 * cloud_cover ** 0.5)
        irradiance = max(irradiance, 0)

        # 温度
        ambient_temp = _ambient_temp(hour, doy)
        # 板温：环境温度 + 辐照加热
        panel_temp = ambient_temp + (irradiance / 800) * 25
        temp_factor = 1.0 - 0.004 * max(panel_temp - 25, 0)

        # 实际功率
        norm_irr = np.clip(irradiance / 1000, 0, 1.5)
        # 加入随机误差（设备老化、遮挡、阴影等）
        noise = rng.normal(1.0, 0.08)  # 8%标准差
        actual_power = capacity_mw * norm_irr * temp_factor * noise
        actual_power = max(actual_power, 0)

        # 加入设备故障（5%概率降低30%出力）
        if rng.random() < 0.05:
            actual_power *= rng.uniform(0.5, 0.8)

        # 理论功率（无噪声）
        theoretical_power = capacity_mw * norm_irr * temp_factor

        records.append({
            "datetime": dt, "latitude": latitude, "longitude": longitude,
            "capacity_mw": capacity_mw, "plant_type": "光伏",
            "hour": hour, "day_of_year": doy, "month": month,
            "irradiance": float(irradiance), "temperature": float(ambient_temp),
            "wind_speed": float(max(rng.normal(3, 1.5), 0)),
            "cloud_cover": float(cloud_cover),
            "actual_power_mw": float(actual_power),
            "theoretical_power_mw": float(theoretical_power),
        })

    return pd.DataFrame(records)


def _ambient_temp(hour: float, doy: int) -> float:
    """根据时间估算环境温度（简化）"""
    # 温度日变化：最高14点，最低凌晨4点
    diurnal = -4 * np.cos(np.radians((hour - 14) * 15))
    # 温度季节变化：夏季高冬季低（北纬30度）
    seasonal = 10 * np.sin(np.radians(360 * (doy - 80) / 365))
    base_temp = 20  # 年均温
    return base_temp + diurnal + seasonal + rng.normal(0, 1.5)


# ─── 风电数据生成 ──────────────────────────────────────────────────────────

def generate_wind_data(
    n_samples: int = 5000,
    latitude: float = 38.0,
    longitude: float = 116.0,
    capacity_mw: float = 100.0,
    rated_speed: float = 12.0,
    cut_in_speed: float = 3.0,
    hub_height: float = 100.0,
    start_date: str = "2024-01-01",
) -> pd.DataFrame:
    """
    生成风电训练数据
    基于风速威布尔分布 + 轮毂高度修正 + 功率曲线
    """
    start = pd.to_datetime(start_date)
    dates = [start + timedelta(hours=i * 6) for i in range(n_samples)]

    # 威布尔分布参数（与地点相关）
    k_shape = rng.uniform(1.8, 2.2)  # 形状参数
    c_scale = rng.uniform(7, 9)       # 尺度参数 m/s

    # 基础风速（威布尔分布）
    base_wind_speeds = rng.weibull(k_shape, size=n_samples) * c_scale

    records = []
    for i, dt in enumerate(dates):
        doy = dt.timetuple().tm_yday
        hour = dt.hour + dt.minute / 60.0

        base_speed = base_wind_speeds[i]

        # 日变化：夜间风速高，白天低（大气边界层效应）
        diurnal_mod = 1.0 + 0.15 * np.sin(2 * np.pi * (hour - 22) / 24)
        # 季节变化：春秋季风大，冬夏季小
        seasonal_mod = 1.0 + 0.1 * np.cos(2 * np.pi * (doy - 30) / 365)
        # 随机天气扰动（大风/静风）
        weather_noise = rng.normal(1.0, 0.15)

        # 10m高度风速
        wind_speed_10m = max(base_speed * diurnal_mod * seasonal_mod * weather_noise, 0)

        # 推到轮毂高度（指数廓线）
        roughness = 0.1
        wind_speed_hub = wind_speed_10m * (hub_height / 10) ** roughness

        # 空气密度
        # 假设标准气压，温度影响密度
        temp = rng.uniform(-5, 35)
        air_density = 1.225 * 293.15 / (temp + 273.15)

        # 功率密度
        power_density = 0.5 * air_density * (wind_speed_hub ** 3)

        # 实际功率（根据功率曲线 + 误差）
        if wind_speed_hub < cut_in_speed or wind_speed_hub > 25:
            power_ratio = 0.0
        elif wind_speed_hub >= rated_speed:
            power_ratio = 1.0
        else:
            power_ratio = (wind_speed_hub ** 3 - cut_in_speed ** 3) / (rated_speed ** 3 - cut_in_speed ** 3)
            power_ratio = np.clip(power_ratio, 0, 1)

        # 湍流损失（高风速湍流大）
        turbulence_loss = 1.0 - 0.05 * min(wind_speed_hub / rated_speed, 1.5)
        # 随风速随机误差
        noise = rng.normal(1.0, 0.06)
        actual_power = capacity_mw * power_ratio * turbulence_loss * noise
        actual_power = max(actual_power, 0)

        # 理论功率
        theoretical_power = capacity_mw * power_ratio

        # 尾流损失（多风机场，这里简化为5%平均损失）
        wake_loss = rng.uniform(0.95, 1.0)

        records.append({
            "datetime": dt,
            "latitude": latitude, "longitude": longitude,
            "capacity_mw": capacity_mw, "plant_type": "风电",
            "hour": hour, "day_of_year": doy,
            "wind_speed": float(wind_speed_hub),
            "wind_speed_10m": float(wind_speed_10m),
            "temperature": float(temp),
            "air_density": float(air_density),
            "power_density": float(power_density),
            "actual_power_mw": float(actual_power * wake_loss),
            "theoretical_power_mw": float(theoretical_power),
        })

    return pd.DataFrame(records)


# ─── 数据保存 ───────────────────────────────────────────────────────────────

def generate_all_data(output_dir: str = None) -> dict[str, str]:
    """生成所有训练数据并保存"""
    if output_dir is None:
        output_dir = os.path.join(os.path.dirname(__file__), "raw")
    os.makedirs(output_dir, exist_ok=True)

    paths = {}

    print("🌞 生成光伏训练数据...")
    pv_df = generate_pv_data(n_samples=5000, latitude=30.0, longitude=120.0, capacity_mw=100.0)
    pv_path = os.path.join(output_dir, "pv_training.csv")
    pv_df.to_csv(pv_path, index=False)
    paths["pv"] = pv_path
    print(f"   光伏数据: {len(pv_df)} 条, 保存到 {pv_path}")

    # 分省份光伏数据
    for lat, lon, name in [(38, 116, "北方"), (23, 113, "南方")]:
        df = generate_pv_data(n_samples=3000, latitude=lat, longitude=lon, capacity_mw=50.0)
        p = os.path.join(output_dir, f"pv_{name}.csv")
        df.to_csv(p, index=False)
        print(f"   光伏数据({name}): {len(df)} 条, 保存到 {p}")

    print("🌀 生成风电训练数据...")
    wt_df = generate_wind_data(n_samples=5000, latitude=38.0, longitude=116.0, capacity_mw=100.0)
    wt_path = os.path.join(output_dir, "wind_training.csv")
    wt_df.to_csv(wt_path, index=False)
    paths["wind"] = wt_path
    print(f"   风电数据: {len(wt_df)} 条, 保存到 {wt_path}")

    for lat, lon, name in [(42, 118, "北方"), (26, 118, "南方")]:
        df = generate_wind_data(n_samples=3000, latitude=lat, longitude=lon, capacity_mw=50.0)
        p = os.path.join(output_dir, f"wind_{name}.csv")
        df.to_csv(p, index=False)
        print(f"   风电数据({name}): {len(df)} 条, 保存到 {p}")

    return paths


if __name__ == "__main__":
    paths = generate_all_data()
    print("✅ 数据生成完成:", paths)
