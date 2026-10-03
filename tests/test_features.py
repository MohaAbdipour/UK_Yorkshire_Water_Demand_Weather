import pandas as pd
import pytest
from src.features import build_features


def test_rolling_demand_uses_previous_days_only():
    df = pd.DataFrame({
        "date": pd.date_range("2014-01-01", periods=10, freq="D"),
        "demand_m3_per_meter": range(10, 20),
        "n_observations": [100] * 10,
        "tasmax": [10.0] * 10,
        "tasmin": [5.0] * 10,
        "rainfall": [0.0] * 10,
    })
    out = build_features(df)
    assert out.loc[7, "demand_roll7"] == sum(range(10, 17)) / 7


def test_missing_calendar_day_is_not_treated_as_previous_day():
    with pytest.raises(ValueError, match='consecutive'):
        build_features(pd.DataFrame({'date':pd.to_datetime(['2014-01-01','2014-01-03'])}))


def test_prior_weather_ignores_same_day_and_future_changes():
    from improve_models import available_features, HISTORY, PAST_WEATHER
    frame = pd.DataFrame({'date':pd.date_range('2014-01-01',periods=30),
        'demand_m3_per_meter':range(30),'tasmax':10.,'tasmin':5.,'rainfall':1.})
    original = available_features(frame)
    frame.loc[20:,['demand_m3_per_meter','tasmax','tasmin','rainfall']] = 1000.
    changed = available_features(frame)
    pd.testing.assert_series_equal(original.loc[20,HISTORY+PAST_WEATHER],changed.loc[20,HISTORY+PAST_WEATHER])
