from pathlib import Path
import numpy as np
import pandas as pd
import xarray as xr
from prepare_haduk_weather import extract_series


def test_extract_series_selects_yorkshire_label(tmp_path: Path):
    p = tmp_path / "tasmax.nc"
    ds = xr.Dataset(
        {"tasmax": (("time", "region"), [[10.0, 11.0], [12.0, 13.0]])},
        coords={
            "time": pd.date_range("2013-01-01", periods=2),
            "region": [0, 1],
            "region_name": ("region", np.array(["North West", "Yorkshire and The Humber"], dtype=object)),
        },
    )
    ds.to_netcdf(p)
    out = extract_series(p, "tasmax", "Yorkshire", None)
    assert list(out["tasmax"]) == [11.0, 13.0]
