from __future__ import annotations

import argparse
from pathlib import Path
import numpy as np
import pandas as pd
import xarray as xr


def _candidate_region_labels(ds: xr.Dataset, region_dim: str = "region"):
    candidates = []
    for name, coord in ds.coords.items():
        if region_dim not in coord.dims:
            continue
        vals = np.asarray(coord.values)
        if vals.ndim != 1:
            continue
        if vals.dtype.kind in {"U", "S", "O"}:
            candidates.append((name, [str(v) for v in vals]))
    for name, var in ds.data_vars.items():
        if region_dim not in var.dims:
            continue
        vals = np.asarray(var.values)
        if vals.ndim == 1 and vals.dtype.kind in {"U", "S", "O"}:
            candidates.append((name, [str(v) for v in vals]))
    return candidates


def _select_region_index(ds: xr.Dataset, pattern: str, region_dim: str = "region") -> int:
    pattern_l = pattern.lower()
    for name, labels in _candidate_region_labels(ds, region_dim):
        matches = [i for i, label in enumerate(labels) if pattern_l in label.lower()]
        if len(matches) == 1:
            print(f"Matched region using {name}: {labels[matches[0]]}")
            return matches[0]
        if len(matches) > 1:
            raise ValueError(
                f"Pattern {pattern!r} matched multiple regions in {name}: "
                + ", ".join(labels[i] for i in matches)
            )
    raise ValueError(
        f"Could not find a labelled region matching {pattern!r}. "
        "Use --region-index after inspecting the dataset metadata."
    )


def extract_series(path: Path, variable: str, region_pattern: str, region_index: int | None):
    ds = xr.open_dataset(path)
    try:
        if variable not in ds:
            # fall back to the only plausible data variable
            vars_ = [v for v in ds.data_vars if "time" in ds[v].dims]
            if len(vars_) != 1:
                raise ValueError(f"Variable {variable!r} not found in {path}; data vars={list(ds.data_vars)}")
            variable = vars_[0]

        da = ds[variable]
        if "time" not in da.dims:
            raise ValueError(f"{variable} in {path} has no time dimension: {da.dims}")

        region_dim = next((d for d in da.dims if d.lower() == "region"), None)
        if region_dim is not None:
            idx = region_index if region_index is not None else _select_region_index(ds, region_pattern, region_dim)
            da = da.isel({region_dim: idx})

        # If extra singleton dimensions remain, squeeze them.
        da = da.squeeze(drop=True)
        if da.ndim != 1 or da.dims[0] != "time":
            raise ValueError(
                f"After region selection, expected a 1-D time series; got dims={da.dims}, shape={da.shape}"
            )

        df = da.to_dataframe(name=variable).reset_index()[["time", variable]]
        df = df.rename(columns={"time": "date"})
        df["date"] = pd.to_datetime(df["date"]).dt.normalize()
        return df
    finally:
        ds.close()


def main():
    p = argparse.ArgumentParser(description="Extract a Yorkshire HadUK-Grid regional daily weather CSV.")
    p.add_argument("--tasmax", type=Path, required=True)
    p.add_argument("--tasmin", type=Path, required=True)
    p.add_argument("--rainfall", type=Path, required=True)
    p.add_argument("--region-pattern", default="Yorkshire")
    p.add_argument("--region-index", type=int, default=None)
    p.add_argument(
        "--out",
        type=Path,
        default=Path("data/raw/weather/haduk_yorkshire_daily.csv"),
    )
    args = p.parse_args()

    frames = [
        extract_series(args.tasmax, "tasmax", args.region_pattern, args.region_index),
        extract_series(args.tasmin, "tasmin", args.region_pattern, args.region_index),
        extract_series(args.rainfall, "rainfall", args.region_pattern, args.region_index),
    ]

    out = frames[0]
    for f in frames[1:]:
        out = out.merge(f, on="date", how="inner")

    out = out.sort_values("date").drop_duplicates("date")
    args.out.parent.mkdir(parents=True, exist_ok=True)
    out.to_csv(args.out, index=False)
    print(f"Saved {len(out):,} daily rows to {args.out}")
    print(f"Coverage: {out.date.min().date()} to {out.date.max().date()}")


if __name__ == "__main__":
    main()
