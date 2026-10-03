from pathlib import Path
import pandas as pd
from src.demand import read_and_aggregate_demand


def test_wide_demand_is_aggregated_by_day(tmp_path: Path):
    p = tmp_path / "demand.csv"
    pd.DataFrame({
        "PROPERTY": [1, 2],
        "METER LOCATION": ["Internal", "External"],
        "DMA": ["A", "A"],
        "24/03/2012": [0.2, 0.4],
        "25/03/2012": [0.3, None],
    }).to_csv(p, index=False)

    out = read_and_aggregate_demand(p)
    assert list(out["n_observations"]) == [2, 1]
    assert abs(out.loc[0, "demand_m3_per_meter"] - 0.3) < 1e-12
    assert abs(out.loc[1, "demand_m3_per_meter"] - 0.3) < 1e-12
