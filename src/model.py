from __future__ import annotations

from dataclasses import dataclass
import numpy as np
import pandas as pd
from sklearn.ensemble import HistGradientBoostingRegressor
from sklearn.impute import SimpleImputer
from sklearn.linear_model import Ridge
from sklearn.metrics import mean_absolute_error, mean_squared_error, r2_score
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import StandardScaler


@dataclass
class Result:
    name: str
    prediction: np.ndarray
    metrics: dict
    model: object | None = None


def score(y, pred):
    y = np.asarray(y, dtype=float)
    pred = np.asarray(pred, dtype=float)
    denom = np.maximum(np.abs(y), 1e-9)
    return {
        "MAE": mean_absolute_error(y, pred),
        "RMSE": mean_squared_error(y, pred) ** 0.5,
        "MAPE_pct": np.mean(np.abs((y - pred) / denom)) * 100,
        "R2": r2_score(y, pred),
    }


def seasonal_naive(test):
    pred = test["demand_lag7"].to_numpy()
    return Result(
        "seasonal_naive_7d",
        pred,
        score(test["demand_m3_per_meter"], pred),
    )


def ridge(train, test, features):
    model = Pipeline([
        ("imputer", SimpleImputer(strategy="median")),
        ("scaler", StandardScaler()),
        ("model", Ridge(alpha=10.0)),
    ])
    model.fit(train[features], train["demand_m3_per_meter"])
    pred = model.predict(test[features])
    return Result("ridge", pred, score(test["demand_m3_per_meter"], pred), model)


def hgb(train, test, features):
    model = Pipeline([
        ("imputer", SimpleImputer(strategy="median")),
        ("model", HistGradientBoostingRegressor(
            learning_rate=0.05,
            max_iter=350,
            max_leaf_nodes=15,
            l2_regularization=1.0,
            random_state=42,
        )),
    ])
    model.fit(train[features], train["demand_m3_per_meter"])
    pred = model.predict(test[features])
    return Result(
        "hist_gradient_boosting",
        pred,
        score(test["demand_m3_per_meter"], pred),
        model,
    )
