from __future__ import annotations

import subprocess
import sys
import uuid
from pathlib import Path

ROOT = Path(__file__).resolve().parent
NETCDF = ROOT / "data" / "raw" / "weather" / "netcdf"

RAIN = NETCDF / "rainfall_hadukgrid_uk_region_day_18910101-20251231.nc"
TMAX = NETCDF / "tasmax_hadukgrid_uk_region_day_19310101-20251231.nc"
TMIN = NETCDF / "tasmin_hadukgrid_uk_region_day_19310101-20251231.nc"


def run(*args: str) -> None:
    print("+", " ".join(args))
    subprocess.run(args, cwd=ROOT, check=True)


def main() -> None:
    if not (ROOT / "data/raw/demand/yorkshire_daily_customer_meter.csv").exists():
        run(sys.executable, "download_demand.py")
    if not all(p.exists() for p in (RAIN, TMAX, TMIN)):
        run(sys.executable, "download_haduk.py")
    run(
        sys.executable,
        "prepare_haduk_weather.py",
        "--tasmax", str(TMAX),
        "--tasmin", str(TMIN),
        "--rainfall", str(RAIN),
        "--region-pattern", "Yorkshire",
    )
    run(sys.executable, "-m", "pytest", "-q", "--basetemp",
        str(ROOT / (".pytest-run-" + uuid.uuid4().hex)))
    run(sys.executable, "run_pipeline.py")
    run(sys.executable, "review_validation.py")
    run(sys.executable, "review_coverage.py")
    run(sys.executable, "final_analysis.py")
    run(sys.executable, "improve_models.py")
    run(sys.executable, "create_visual_report.py")


if __name__ == "__main__":
    main()
