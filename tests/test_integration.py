import numpy as np
import pandas as pd
from src.features import build_features, FEATURES
from src.model import seasonal_naive, ridge, hgb


def test_models_run_end_to_end():
    rng = np.random.default_rng(42)
    n = 420
    date = pd.date_range("2013-01-01", periods=n, freq="D")
    tmean = 10 + 7*np.sin(2*np.pi*np.arange(n)/365.25)
    rainfall = rng.gamma(1.0, 1.5, n)
    demand = 0.32 + 0.006*np.maximum(tmean-15, 0) - 0.002*np.minimum(rainfall, 5) + rng.normal(0, 0.01, n)
    df = pd.DataFrame({
        "date": date,
        "demand_m3_per_meter": demand,
        "n_observations": 1800,
        "tasmax": tmean + 4,
        "tasmin": tmean - 4,
        "rainfall": rainfall,
    })
    x = build_features(df).dropna().reset_index(drop=True)
    train, test = x.iloc[:-60], x.iloc[-60:]
    results = [seasonal_naive(test), ridge(train, test, FEATURES), hgb(train, test, FEATURES)]
    for r in results:
        assert len(r.prediction) == len(test)
        assert np.isfinite(r.prediction).all()
        assert r.metrics["MAE"] >= 0
