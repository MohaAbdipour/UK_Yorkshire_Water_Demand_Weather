from __future__ import annotations

from pathlib import Path
import pandas as pd


ALIASES = {
    "date": ["date", "time", "day"],
    "tasmax": ["tasmax", "tmax", "max_temp", "maximum_temperature"],
    "tasmin": ["tasmin", "tmin", "min_temp", "minimum_temperature"],
    "rainfall": ["rainfall", "rain", "precipitation", "precip", "pr"],
}


def _pick(df, key):
    norm = {str(c).strip().lower(): c for c in df.columns}
    for candidate in ALIASES[key]:
        if candidate in norm:
            return norm[candidate]
    for nc, original in norm.items():
        if any(candidate in nc for candidate in ALIASES[key]):
            return original
    return None


def read_weather(path: str | Path) -> pd.DataFrame:
    path = Path(path)
    if not path.exists():
        raise FileNotFoundError(
            f"{path} not found. Create a daily HadUK CSV with "
            "date, tasmax, tasmin, rainfall."
        )

    df = pd.read_csv(path)
    cols = {k: _pick(df, k) for k in ALIASES}
    missing = [k for k, v in cols.items() if v is None]
    if missing:
        raise ValueError(
            f"Could not infer weather columns: {missing}. "
            f"Available columns: {list(df.columns)}"
        )

    date_text = df[cols["date"]].astype(str).str.strip()
    iso_dates = date_text.str.match(r"^\d{4}-\d{2}-\d{2}$")
    dates = pd.Series(pd.NaT, index=df.index, dtype="datetime64[ns]")
    dates.loc[iso_dates] = pd.to_datetime(
        date_text.loc[iso_dates], format="%Y-%m-%d", errors="raise"
    )
    dates.loc[~iso_dates] = pd.to_datetime(
        date_text.loc[~iso_dates], format="mixed", dayfirst=True, errors="raise"
    )

    out = pd.DataFrame({
        "date": dates,
        "tasmax": pd.to_numeric(df[cols["tasmax"]], errors="coerce"),
        "tasmin": pd.to_numeric(df[cols["tasmin"]], errors="coerce"),
        "rainfall": pd.to_numeric(df[cols["rainfall"]], errors="coerce"),
    })

    return (
        out.dropna(subset=["date"])
        .groupby("date", as_index=False)[["tasmax", "tasmin", "rainfall"]]
        .mean()
        .sort_values("date")
    )
