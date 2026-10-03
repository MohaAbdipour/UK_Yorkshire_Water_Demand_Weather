from __future__ import annotations

from pathlib import Path
import re
import pandas as pd


META_HINTS = ("property", "meter", "dma", "location")


def _looks_like_date(text: str) -> bool:
    try:
        parsed = pd.to_datetime(str(text), dayfirst=True, errors="coerce")
        return not pd.isna(parsed)
    except Exception:
        return False


def read_and_aggregate_demand(path: str | Path) -> pd.DataFrame:
    """
    Read the wide Yorkshire Water meter dataset and aggregate it by day.

    Primary target = mean consumption across available meter records.
    The count of contributing observations is retained for QA.
    """
    path = Path(path)
    if not path.exists():
        raise FileNotFoundError(
            f"{path} not found. Run `python download_demand.py` first."
        )

    df = pd.read_csv(path, low_memory=False)

    date_cols = [c for c in df.columns if _looks_like_date(c)]
    if not date_cols:
        raise ValueError(
            "No date-like columns were found. "
            f"First columns: {list(df.columns[:20])}"
        )

    meta_cols = [c for c in df.columns if c not in date_cols]

    long = df.melt(
        id_vars=meta_cols,
        value_vars=date_cols,
        var_name="date",
        value_name="consumption_m3",
    )

    long["date"] = pd.to_datetime(long["date"], dayfirst=True, errors="coerce")
    long["consumption_m3"] = pd.to_numeric(long["consumption_m3"], errors="coerce")

    # Basic physical QA. Negative customer consumption is not meaningful here.
    long.loc[long["consumption_m3"] < 0, "consumption_m3"] = pd.NA
    long = long.dropna(subset=["date", "consumption_m3"])

    agg = (
        long.groupby("date")["consumption_m3"]
        .agg(
            mean_consumption_m3="mean",
            median_consumption_m3="median",
            total_consumption_m3="sum",
            n_observations="count",
        )
        .reset_index()
        .sort_values("date")
    )

    # Keep the modelling target explicit.
    agg["demand_m3_per_meter"] = agg["mean_consumption_m3"]

    return agg


def read_dma_daily(path: str | Path) -> pd.DataFrame | None:
    """
    Optional DMA-level aggregation if a DMA column can be identified.
    Returns None when no DMA-like column exists.
    """
    path = Path(path)
    df = pd.read_csv(path, low_memory=False)
    date_cols = [c for c in df.columns if _looks_like_date(c)]
    meta_cols = [c for c in df.columns if c not in date_cols]

    dma_col = next((c for c in meta_cols if "dma" in str(c).lower()), None)
    if dma_col is None:
        return None

    long = df.melt(
        id_vars=meta_cols,
        value_vars=date_cols,
        var_name="date",
        value_name="consumption_m3",
    )
    long["date"] = pd.to_datetime(long["date"], dayfirst=True, errors="coerce")
    long["consumption_m3"] = pd.to_numeric(long["consumption_m3"], errors="coerce")
    long = long.dropna(subset=["date", dma_col, "consumption_m3"])

    return (
        long.groupby(["date", dma_col])["consumption_m3"]
        .agg(["mean", "median", "count"])
        .reset_index()
    )
