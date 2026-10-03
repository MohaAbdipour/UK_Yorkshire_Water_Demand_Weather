import pandas as pd

from src.weather import read_weather


def test_weather_preserves_iso_dates_and_daily_coverage(tmp_path):
    dates = pd.date_range("2012-01-01", "2012-02-29")
    path = tmp_path / "weather.csv"
    pd.DataFrame({
        "date": dates.strftime("%Y-%m-%d"),
        "tasmax": range(len(dates)),
        "tasmin": 1.0,
        "rainfall": 0.0,
    }).to_csv(path, index=False)
    result = read_weather(path)
    assert result["date"].tolist() == dates.tolist()
    assert result["tasmax"].tolist() == list(range(len(dates)))
