"""
预测推理模块 - 加载训练好的模型进行实时功率预测
"""
import os
import json
import numpy as np
from datetime import datetime
from typing import Optional, Literal
import logging

import lightgbm as lgb

logger = logging.getLogger(__name__)

# ─── 路径 ────────────────────────────────────────────────────────────────────

ML_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
MODEL_DIR = os.path.join(ML_DIR, "models", "saved")


# ─── 特征构建 ────────────────────────────────────────────────────────────────

def build_pv_features(
    irradiance: float,      # W/m²
    temperature: float,     # °C
    hour: float,            # 0-24
    day_of_year: int,       # 1-366
    latitude: float = 30.0,
    capacity_mw: float = 100.0,
) -> np.ndarray:
    """构建光伏特征向量（与训练时完全一致）"""

    # 归一化辐照
    norm_irradiance = np.clip(irradiance / 1000.0, 0, 1.5)

    # 板温
    panel_temp = temperature + (irradiance / 800) * 25
    temp_factor = np.clip(1.0 - 0.004 * max(panel_temp - 25, 0), 0, 1)

    # 太阳高度角（简化）
    declination = 23.45 * np.sin(np.radians(360 / 365 * (day_of_year - 81)))
    lat_rad = np.radians(latitude)
    hour_angle = 15 * (hour - 12)
    cos_zenith = (
        np.sin(lat_rad) * np.sin(np.radians(declination)) +
        np.cos(lat_rad) * np.cos(np.radians(declination)) * np.cos(np.radians(hour_angle))
    )
    solar_elevation_cos = np.clip(cos_zenith, 0, 1)

    # 时间特征
    doy_sin = np.sin(2 * np.pi * day_of_year / 365)
    doy_cos = np.cos(2 * np.pi * day_of_year / 365)
    hour_sin = np.sin(2 * np.pi * hour / 24)
    hour_cos = np.cos(2 * np.pi * hour / 24)

    # 交叉特征
    norm_x_seasonal = norm_irradiance * doy_cos
    norm_x_temp = norm_irradiance * temp_factor

    features = np.array([[
        irradiance, temperature, hour, day_of_year,
        0.0,  # cloud_cover (简化)
        capacity_mw,
        # 派生特征
        norm_irradiance, temp_factor, solar_elevation_cos,
        hour_sin, hour_cos, doy_sin, doy_cos,
        norm_x_seasonal, norm_x_temp,
    ]], dtype=np.float32)

    return features


def build_wind_features(
    wind_speed: float,       # m/s
    temperature: float,     # °C
    hour: float,            # 0-24
    day_of_year: int,       # 1-366
    capacity_mw: float = 100.0,
) -> np.ndarray:
    """构建风电特征向量"""

    log_wind = np.log(wind_speed + 1)
    wind_cubed = wind_speed ** 3
    wind_squared = wind_speed ** 2
    seasonal_factor = np.sin(2 * np.pi * (day_of_year - 80) / 365)
    hour_sin = np.sin(2 * np.pi * hour / 24)
    hour_cos = np.cos(2 * np.pi * hour / 24)

    features = np.array([[
        wind_speed, temperature, hour, day_of_year, capacity_mw,
        # 派生特征
        log_wind, wind_cubed, wind_squared,
        hour_sin, hour_cos, seasonal_factor,
    ]], dtype=np.float32)

    return features


# ─── 预测器类 ────────────────────────────────────────────────────────────────

class PowerPredictor:
    """
    功率预测器
    支持光伏/风电，自动加载训练好的 LightGBM 模型
    """

    PV_FEATURE_NAMES = [
        "irradiance", "temperature", "hour", "day_of_year",
        "cloud_cover", "capacity_mw",
        "norm_irradiance", "temp_factor", "solar_elevation_cos",
        "hour_sin", "hour_cos", "doy_sin", "doy_cos",
        "norm_x_seasonal", "norm_x_temp",
    ]

    WIND_FEATURE_NAMES = [
        "wind_speed", "temperature", "hour", "day_of_year", "capacity_mw",
        "log_wind", "wind_cubed", "wind_squared",
        "hour_sin", "hour_cos", "seasonal_factor",
    ]

    def __init__(self, model_dir: str = MODEL_DIR):
        self.model_dir = model_dir
        self.pv_model: Optional[lgb.Booster] = None
        self.wind_model: Optional[lgb.Booster] = None
        self.pv_report: Optional[dict] = None
        self.wind_report: Optional[dict] = None
        self._load_models()

    def _load_models(self):
        """加载模型文件"""
        pv_path = os.path.join(self.model_dir, "pv_model_lgb.json")
        wind_path = os.path.join(self.model_dir, "wind_model_lgb.json")

        if os.path.exists(pv_path):
            self.pv_model = lgb.Booster(model_file=pv_path)
            logger.info(f"✅ 光伏模型已加载: {pv_path}")
        else:
            logger.warning(f"⚠️ 光伏模型不存在: {pv_path}，将使用简化的物理模型")

        if os.path.exists(wind_path):
            self.wind_model = lgb.Booster(model_file=wind_path)
            logger.info(f"✅ 风电模型已加载: {wind_path}")
        else:
            logger.warning(f"⚠️ 风电模型不存在: {wind_path}，将使用简化的物理模型")

        # 加载报告
        for model_type, path in [("pv", pv_path), ("wind", wind_path)]:
            report_path = path.replace(".json", "_report.json")
            if os.path.exists(report_path):
                with open(report_path, "r") as f:
                    if model_type == "pv":
                        self.pv_report = json.load(f)
                    else:
                        self.wind_report = json.load(f)

    def predict(
        self,
        plant_type: Literal["光伏", "风电"],
        irradiance: float = 0.0,
        wind_speed: float = 0.0,
        temperature: float = 25.0,
        hour: float = None,
        day_of_year: int = None,
        latitude: float = 30.0,
        capacity_mw: float = 100.0,
    ) -> dict:
        """
        执行功率预测

        Parameters
        ----------
        plant_type : 光伏 / 风电
        irradiance : W/m²，直接辐照（光伏用）
        wind_speed : m/s（风电用）
        temperature : °C
        hour : 小时（0-24），默认当前小时
        day_of_year : 一年中第几天，默认今天
        latitude : 纬度（光伏用）
        capacity_mw : 装机容量 MW

        Returns
        -------
        dict with predicted_power_mw, confidence, model_type, features
        """
        if hour is None:
            hour = datetime.now().hour + datetime.now().minute / 60.0
        if day_of_year is None:
            day_of_year = datetime.now().timetuple().tm_yday

        if plant_type in ("光伏", "solar", "pv", "PV"):
            return self._predict_pv(irradiance, temperature, hour, day_of_year, latitude, capacity_mw)
        else:
            return self._predict_wind(wind_speed, temperature, hour, day_of_year, capacity_mw)

    def _predict_pv(
        self,
        irradiance: float,
        temperature: float,
        hour: float,
        day_of_year: int,
        latitude: float,
        capacity_mw: float,
    ) -> dict:
        """光伏预测"""
        features = build_pv_features(irradiance, temperature, hour, day_of_year, latitude, capacity_mw)

        if self.pv_model is not None:
            # 使用 LightGBM 模型
            raw_pred = self.pv_model.predict(features)[0]
            model_type = "LightGBM"
        else:
            # 回退到物理模型
            norm_irr = np.clip(irradiance / 1000, 0, 1.5)
            panel_temp = temperature + (irradiance / 800) * 25
            temp_factor = max(1.0 - 0.004 * max(panel_temp - 25, 0), 0)
            raw_pred = capacity_mw * norm_irr * temp_factor
            model_type = "Physics"

        # 夜间强制为0
        declination = 23.45 * np.sin(np.radians(360 / 365 * (day_of_year - 81)))
        lat_rad = np.radians(latitude)
        hour_angle = 15 * (hour - 12)
        cos_zenith = (
            np.sin(lat_rad) * np.sin(np.radians(declination)) +
            np.cos(lat_rad) * np.cos(np.radians(declination)) * np.cos(np.radians(hour_angle))
        )
        if cos_zenith <= 0.05:
            raw_pred = 0.0

        predicted_power = max(raw_pred, 0)

        # 置信度（基于物理模型一致性）
        if self.pv_report:
            mape = self.pv_report.get("test_mape", 15)
            confidence = max(1 - mape / 100, 0.5)
        else:
            confidence = 0.80

        return {
            "predicted_power_mw": round(float(predicted_power), 3),
            "capacity_mw": capacity_mw,
            "capacity_factor": round(predicted_power / capacity_mw, 4),
            "confidence": round(confidence, 3),
            "model_type": model_type,
            "irradiance": irradiance,
            "temperature": temperature,
            "hour": round(hour, 2),
            "day_of_year": day_of_year,
        }

    def _predict_wind(
        self,
        wind_speed: float,
        temperature: float,
        hour: float,
        day_of_year: int,
        capacity_mw: float,
    ) -> dict:
        """风电预测"""
        features = build_wind_features(wind_speed, temperature, hour, day_of_year, capacity_mw)

        if self.wind_model is not None:
            raw_pred = self.wind_model.predict(features)[0]
            model_type = "LightGBM"
        else:
            # 回退到物理功率曲线
            cut_in = 3.0
            rated = 12.0
            if wind_speed < cut_in or wind_speed > 25:
                raw_pred = 0.0
            elif wind_speed >= rated:
                raw_pred = capacity_mw
            else:
                ratio = (wind_speed ** 3 - cut_in ** 3) / (rated ** 3 - cut_in ** 3)
                raw_pred = capacity_mw * np.clip(ratio, 0, 1)
            model_type = "PowerCurve"

        predicted_power = max(raw_pred, 0)

        if self.wind_report:
            mape = self.wind_report.get("test_mape", 15)
            confidence = max(1 - mape / 100, 0.5)
        else:
            confidence = 0.80

        return {
            "predicted_power_mw": round(float(predicted_power), 3),
            "capacity_mw": capacity_mw,
            "capacity_factor": round(predicted_power / capacity_mw, 4),
            "confidence": round(confidence, 3),
            "model_type": model_type,
            "wind_speed": wind_speed,
            "temperature": temperature,
            "hour": round(hour, 2),
            "day_of_year": day_of_year,
        }

    def get_model_info(self) -> dict:
        """获取模型信息"""
        return {
            "pv": {
                "loaded": self.pv_model is not None,
                "model_type": "LightGBM",
                "report": self.pv_report,
            },
            "wind": {
                "loaded": self.wind_model is not None,
                "model_type": "LightGBM",
                "report": self.wind_report,
            },
        }


# ─── 全局单例 ────────────────────────────────────────────────────────────────

_predictor: Optional[PowerPredictor] = None


def get_predictor() -> PowerPredictor:
    """获取预测器单例"""
    global _predictor
    if _predictor is None:
        _predictor = PowerPredictor()
    return _predictor


def predict_power(
    plant_type: str,
    irradiance: float = 0.0,
    wind_speed: float = 0.0,
    temperature: float = 25.0,
    latitude: float = 30.0,
    capacity_mw: float = 100.0,
) -> dict:
    """快捷预测接口"""
    predictor = get_predictor()
    return predictor.predict(
        plant_type=plant_type,
        irradiance=irradiance,
        wind_speed=wind_speed,
        temperature=temperature,
        latitude=latitude,
        capacity_mw=capacity_mw,
    )
