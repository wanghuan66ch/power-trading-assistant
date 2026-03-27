"""
模型训练 - 光伏/风电功率预测
使用 LightGBM 梯度提升回归模型
"""
import os
import sys
import json
import joblib
import warnings
import numpy as np
import pandas as pd
from datetime import datetime

import lightgbm as lgb
from sklearn.model_selection import TimeSeriesSplit, cross_val_score
from sklearn.metrics import mean_absolute_error, r2_score

warnings.filterwarnings("ignore")

# ─── 路径配置 ────────────────────────────────────────────────────────────────

ML_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
MODEL_DIR = os.path.join(ML_DIR, "models", "saved")
DATA_DIR = os.path.join(ML_DIR, "data", "raw")
os.makedirs(MODEL_DIR, exist_ok=True)


# ─── 特征列表 ────────────────────────────────────────────────────────────────

PV_FEATURES = [
    "irradiance", "temperature", "hour", "day_of_year",
    "cloud_cover", "capacity_mw",
]

PV_DERIVED = [
    "norm_irradiance", "temp_factor", "solar_elevation_cos",
    "hour_sin", "hour_cos", "doy_sin", "doy_cos",
    "norm_x_seasonal", "norm_x_temp",
]

WIND_FEATURES = [
    "wind_speed", "temperature", "hour", "day_of_year", "capacity_mw",
]

WIND_DERIVED = [
    "log_wind", "wind_cubed", "wind_squared",
    "hour_sin", "hour_cos", "seasonal_factor",
]


def add_derived_features(df: pd.DataFrame, plant_type: str) -> pd.DataFrame:
    """为数据集添加派生特征"""
    df = df.copy()

    # 共同时间特征
    df["hour_sin"] = np.sin(2 * np.pi * df["hour"] / 24)
    df["hour_cos"] = np.cos(2 * np.pi * df["hour"] / 24)
    df["doy_sin"] = np.sin(2 * np.pi * df["day_of_year"] / 365)
    df["doy_cos"] = np.cos(2 * np.pi * df["day_of_year"] / 365)

    if plant_type == "光伏":
        # 光伏专用
        df["norm_irradiance"] = np.clip(df["irradiance"] / 1000, 0, 1.5)

        # 板温
        panel_temp = df["temperature"] + (df["irradiance"] / 800) * 25
        df["temp_factor"] = np.clip(1.0 - 0.004 * np.maximum(panel_temp - 25, 0), 0, 1)

        # 太阳高度角（简化）
        declination = 23.45 * np.sin(np.radians(360 / 365 * (df["day_of_year"] - 81)))
        lat_rad = np.radians(30)
        hour_angle = 15 * (df["hour"] - 12)
        cos_zenith = (
            np.sin(lat_rad) * np.sin(np.radians(declination)) +
            np.cos(lat_rad) * np.cos(np.radians(declination)) * np.cos(np.radians(hour_angle))
        )
        df["solar_elevation_cos"] = np.clip(cos_zenith, 0, 1)

        # 季节因子
        df["norm_x_seasonal"] = df["norm_irradiance"] * df["doy_cos"]
        df["norm_x_temp"] = df["norm_irradiance"] * df["temp_factor"]

        # 夜间剔除（辐照=0且夜间）
        df.loc[df["solar_elevation_cos"] < 0.05, "irradiance"] = 0

    elif plant_type == "风电":
        df["log_wind"] = np.log(df["wind_speed"] + 1)
        df["wind_cubed"] = df["wind_speed"] ** 3
        df["wind_squared"] = df["wind_speed"] ** 2
        df["seasonal_factor"] = np.sin(2 * np.pi * (df["day_of_year"] - 80) / 365)

    return df


def load_data(plant_type: str, region: str = None) -> pd.DataFrame:
    """加载训练数据"""
    if plant_type == "光伏":
        fname = f"pv_{region}.csv" if region else "pv_training.csv"
    else:
        fname = f"wind_{region}.csv" if region else "wind_training.csv"

    path = os.path.join(DATA_DIR, fname)
    if not os.path.exists(path):
        raise FileNotFoundError(f"数据文件不存在: {path}")

    df = pd.read_csv(path, parse_dates=["datetime"])
    print(f"  加载数据: {len(df)} 条, 时间范围: {df['datetime'].min()} ~ {df['datetime'].max()}")
    return df


def train_pv_model(data_path: str = None, save_path: str = None) -> dict:
    """训练光伏预测模型"""
    print("\n🌞 训练光伏预测模型...")
    print("=" * 60)

    if data_path is None:
        data_path = os.path.join(DATA_DIR, "pv_training.csv")
    if save_path is None:
        save_path = os.path.join(MODEL_DIR, "pv_model_lgb.json")

    # 加载数据
    df = pd.read_csv(data_path, parse_dates=["datetime"])
    df = add_derived_features(df, "光伏")
    df = df[df["irradiance"] > 0].copy()  # 只用白天数据训练

    # 特征和标签
    feature_cols = PV_FEATURES + PV_DERIVED
    X = df[feature_cols].values.astype(np.float32)
    y = df["actual_power_mw"].values.astype(np.float32)

    print(f"  训练样本: {len(X)}, 特征数: {len(feature_cols)}")
    print(f"  特征: {feature_cols}")

    # 时序划分（后20%为测试集）
    split_idx = int(len(X) * 0.8)
    X_train, X_test = X[:split_idx], X[split_idx:]
    y_train, y_test = y[:split_idx], y[split_idx:]

    # LightGBM 参数
    params = {
        "objective": "regression",
        "metric": ["mae", "mape"],
        "boosting_type": "gbdt",
        "num_leaves": 63,
        "learning_rate": 0.05,
        "feature_fraction": 0.85,
        "bagging_fraction": 0.85,
        "bagging_freq": 5,
        "min_child_samples": 20,
        "n_estimators": 1000,
        "verbose": -1,
        "random_state": 42,
    }

    # 训练
    model = lgb.LGBMRegressor(**params)
    model.fit(
        X_train, y_train,
        eval_set=[(X_test, y_test)],
        callbacks=[lgb.early_stopping(50, verbose=False)],
    )

    # 测试评估
    y_pred = model.predict(X_test)
    mae = mean_absolute_error(y_test, y_pred)
    mape = (np.abs(y_test[y_test > 0.1] - y_pred[y_test > 0.1]) / y_test[y_test > 0.1]).mean() * 100
    r2 = r2_score(y_test, y_pred)

    print(f"\n  📊 光伏模型测试集评估:")
    print(f"     MAE:  {mae:.2f} MW  ({mae/df['capacity_mw'].iloc[0]*100:.1f}% 装机)")
    print(f"     MAPE: {mape:.2f}%")
    print(f"     R²:   {r2:.4f}")

    # 特征重要性
    importance = pd.DataFrame({
        "feature": feature_cols,
        "importance": model.feature_importances_,
    }).sort_values("importance", ascending=False)
    print(f"\n  🔑 特征重要性 TOP5:")
    for _, row in importance.head(5).iterrows():
        print(f"     {row['feature']}: {row['importance']}")

    # 交叉验证
    tscv = TimeSeriesSplit(n_splits=5)
    cv_scores = cross_val_score(model, X, y, cv=tscv, scoring="neg_mean_absolute_error")
    print(f"\n  🔄 5折时序交叉验证 MAE: {-cv_scores.mean():.2f} ± {cv_scores.std():.2f} MW")

    # 保存模型
    model.booster_.save_model(save_path)
    print(f"\n  ✅ 模型已保存: {save_path}")

    # 评估报告
    report = {
        "plant_type": "光伏",
        "model_type": "LightGBM",
        "n_samples": len(X),
        "n_features": len(feature_cols),
        "features": feature_cols,
        "test_mae": round(mae, 4),
        "test_mape": round(mape, 4),
        "test_r2": round(r2, 4),
        "cv_mae_mean": round(-cv_scores.mean(), 4),
        "cv_mae_std": round(cv_scores.std(), 4),
        "n_trees": model.n_estimators_,
        "saved_at": datetime.now().isoformat(),
    }

    report_path = save_path.replace(".json", "_report.json")
    with open(report_path, "w", encoding="utf-8") as f:
        json.dump(report, f, ensure_ascii=False, indent=2)
    print(f"  📋 评估报告: {report_path}")

    return report


def train_wind_model(data_path: str = None, save_path: str = None) -> dict:
    """训练风电预测模型"""
    print("\n🌀 训练风电预测模型...")
    print("=" * 60)

    if data_path is None:
        data_path = os.path.join(DATA_DIR, "wind_training.csv")
    if save_path is None:
        save_path = os.path.join(MODEL_DIR, "wind_model_lgb.json")

    df = pd.read_csv(data_path, parse_dates=["datetime"])
    df = add_derived_features(df, "风电")

    feature_cols = WIND_FEATURES + WIND_DERIVED
    X = df[feature_cols].values.astype(np.float32)
    y = df["actual_power_mw"].values.astype(np.float32)

    print(f"  训练样本: {len(X)}, 特征数: {len(feature_cols)}")
    print(f"  特征: {feature_cols}")

    split_idx = int(len(X) * 0.8)
    X_train, X_test = X[:split_idx], X[split_idx:]
    y_train, y_test = y[:split_idx], y[split_idx:]

    params = {
        "objective": "regression",
        "metric": ["mae", "mape"],
        "boosting_type": "gbdt",
        "num_leaves": 63,
        "learning_rate": 0.05,
        "feature_fraction": 0.85,
        "bagging_fraction": 0.85,
        "bagging_freq": 5,
        "min_child_samples": 20,
        "n_estimators": 1000,
        "verbose": -1,
        "random_state": 42,
    }

    model = lgb.LGBMRegressor(**params)
    model.fit(
        X_train, y_train,
        eval_set=[(X_test, y_test)],
        callbacks=[lgb.early_stopping(50, verbose=False)],
    )

    y_pred = model.predict(X_test)
    mae = mean_absolute_error(y_test, y_pred)
    mape = (np.abs(y_test[y_test > 0.1] - y_pred[y_test > 0.1]) / y_test[y_test > 0.1]).mean() * 100
    r2 = r2_score(y_test, y_pred)

    print(f"\n  📊 风电模型测试集评估:")
    print(f"     MAE:  {mae:.2f} MW  ({mae/df['capacity_mw'].iloc[0]*100:.1f}% 装机)")
    print(f"     MAPE: {mape:.2f}%")
    print(f"     R²:   {r2:.4f}")

    importance = pd.DataFrame({
        "feature": feature_cols,
        "importance": model.feature_importances_,
    }).sort_values("importance", ascending=False)
    print(f"\n  🔑 特征重要性 TOP5:")
    for _, row in importance.head(5).iterrows():
        print(f"     {row['feature']}: {row['importance']}")

    tscv = TimeSeriesSplit(n_splits=5)
    cv_scores = cross_val_score(model, X, y, cv=tscv, scoring="neg_mean_absolute_error")
    print(f"\n  🔄 5折时序交叉验证 MAE: {-cv_scores.mean():.2f} ± {cv_scores.std():.2f} MW")

    model.booster_.save_model(save_path)
    print(f"\n  ✅ 模型已保存: {save_path}")

    report = {
        "plant_type": "风电",
        "model_type": "LightGBM",
        "n_samples": len(X),
        "n_features": len(feature_cols),
        "features": feature_cols,
        "test_mae": round(mae, 4),
        "test_mape": round(mape, 4),
        "test_r2": round(r2, 4),
        "cv_mae_mean": round(-cv_scores.mean(), 4),
        "cv_mae_std": round(cv_scores.std(), 4),
        "n_trees": model.n_estimators_,
        "saved_at": datetime.now().isoformat(),
    }

    report_path = save_path.replace(".json", "_report.json")
    with open(report_path, "w", encoding="utf-8") as f:
        json.dump(report, f, ensure_ascii=False, indent=2)
    print(f"  📋 评估报告: {report_path}")

    return report


def train_all() -> dict:
    """一键训练所有模型"""
    print("=" * 60)
    print("⚡ 电力功率预测模型训练")
    print(f"   时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 60)

    reports = {}

    # 生成数据
    from ml.data.synthetic import generate_all_data
    generate_all_data(DATA_DIR)

    # 训练
    reports["pv"] = train_pv_model()
    reports["wind"] = train_wind_model()

    # 保存总报告
    summary = {
        "trained_at": datetime.now().isoformat(),
        "reports": reports,
    }
    summary_path = os.path.join(MODEL_DIR, "training_summary.json")
    with open(summary_path, "w", encoding="utf-8") as f:
        json.dump(summary, f, ensure_ascii=False, indent=2)
    print(f"\n\n✅ 所有模型训练完成！总报告: {summary_path}")

    return reports


if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1] == "--all":
        train_all()
    elif len(sys.argv) > 1 and sys.argv[1] == "pv":
        train_pv_model()
    elif len(sys.argv) > 1 and sys.argv[1] == "wind":
        train_wind_model()
    else:
        print("用法: python -m ml.models.trainer [--all|pv|wind]")
        print("  --all : 生成数据 + 训练所有模型")
        print("  pv    : 仅训练光伏模型")
        print("  wind  : 仅训练风电模型")
