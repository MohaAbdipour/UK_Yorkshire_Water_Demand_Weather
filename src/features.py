from __future__ import annotations
import numpy as np
import pandas as pd


FEATURES = [
    "tasmax", "tasmin", "tmean", "rainfall",
    "tmean_3d", "tmean_7d", "rain_3d", "rain_7d",
    "dow", "is_weekend", "doy_sin", "doy_cos",
    "demand_lag1", "demand_lag7", "demand_lag14", "demand_roll7",
]


def build_features(df: pd.DataFrame) -> pd.DataFrame:
    out = df.sort_values("date").copy()
    if out["date"].isna().any() or out["date"].duplicated().any():
        raise ValueError("Feature dates must be valid and unique.")
    if not out["date"].diff().dropna().eq(pd.Timedelta(days=1)).all():
        raise ValueError("Daily features require consecutive dates; resolve missing days first.")

    out["tmean"] = (out["tasmax"] + out["tasmin"]) / 2
    out["dow"] = out["date"].dt.dayofweek
    out["is_weekend"] = (out["dow"] >= 5).astype(int)

    doy = out["date"].dt.dayofyear
    out["doy_sin"] = np.sin(2 * np.pi * doy / 365.25)
    out["doy_cos"] = np.cos(2 * np.pi * doy / 365.25)

    out["tmean_3d"] = out["tmean"].rolling(3, min_periods=1).mean()
    out["tmean_7d"] = out["tmean"].rolling(7, min_periods=1).mean()
    out["rain_3d"] = out["rainfall"].rolling(3, min_periods=1).sum()
    out["rain_7d"] = out["rainfall"].rolling(7, min_periods=1).sum()

    target = out["demand_m3_per_meter"]
    out["demand_lag1"] = target.shift(1)
    out["demand_lag7"] = target.shift(7)
    out["demand_lag14"] = target.shift(14)

    # Critical leakage protection: shift first, then roll.
    out["demand_roll7"] = target.shift(1).rolling(7).mean()

    return out
