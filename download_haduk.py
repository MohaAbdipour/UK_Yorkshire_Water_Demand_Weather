from __future__ import annotations

import argparse
import os
from pathlib import Path
import requests

BASE = "https://dap.ceda.ac.uk/badc/ukmo-hadobs/data/insitu/MOHC/HadOBS/HadUK-Grid/v1.3.2.ceda/region"

FILES = {
    "rainfall": "rainfall/day/v20260512/rainfall_hadukgrid_uk_region_day_18910101-20251231.nc",
    "tasmax": "tasmax/day/v20260512/tasmax_hadukgrid_uk_region_day_19310101-20251231.nc",
    "tasmin": "tasmin/day/v20260512/tasmin_hadukgrid_uk_region_day_19310101-20251231.nc",
}


def download(url: str, out: Path, token: str) -> None:
    out.parent.mkdir(parents=True, exist_ok=True)
    headers = {"Authorization": f"Bearer {token}"}
    with requests.get(url, headers=headers, stream=True, timeout=120) as r:
        r.raise_for_status()
        ctype = r.headers.get("content-type", "")
        if "text/html" in ctype.lower():
            raise RuntimeError(
                "CEDA returned HTML rather than NetCDF. Check that CEDA_TOKEN is valid "
                "and that your account can access HadUK-Grid."
            )
        with out.open("wb") as f:
            for chunk in r.iter_content(chunk_size=1024 * 1024):
                if chunk:
                    f.write(chunk)
    print(f"Saved {out.name}: {out.stat().st_size / 1_000_000:.2f} MB")


def main() -> None:
    p = argparse.ArgumentParser(
        description="Download HadUK-Grid v1.3.2 administrative-region daily NetCDF files from CEDA."
    )
    p.add_argument(
        "--out-dir", type=Path, default=Path("data/raw/weather/netcdf"),
        help="Output folder for the three source NetCDF files.",
    )
    args = p.parse_args()

    token = os.environ.get("CEDA_TOKEN")
    if not token:
        raise SystemExit(
            "CEDA_TOKEN is not set. Create a CEDA access token and set it as an environment variable.\n"
            "See: https://help.ceda.ac.uk/article/5100-archive-access-tokens"
        )

    for var, rel in FILES.items():
        url = f"{BASE}/{rel}"
        out = args.out_dir / Path(rel).name
        download(url, out, token)


if __name__ == "__main__":
    main()
