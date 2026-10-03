# Data sources and acquisition

## 1. Yorkshire Water daily customer meter data

Dataset: **Daily customer meter data - local area study**  
Publisher: Yorkshire Water, distributed by Data Mill North  
Coverage described by the publisher: two anonymised Yorkshire DMAs, 2,160 anonymised properties, March 2012 to April 2015.  
Licence shown by Data Mill North: Creative Commons Attribution.

Verified direct CSV URL:

```text
https://datamillnorth.org/download/2y1yy/fb01ce66-423a-4111-9065-d989bdf0b3ce/Daily%20m3%201315.csv
```

Run:

```bash
python download_demand.py
```

Expected local file:

```text
data/raw/demand/yorkshire_daily_customer_meter.csv
```

## 2. Met Office HadUK-Grid daily weather

Current source used by the project: **HadUK-Grid Climate Observations by Administrative Regions over the UK, v1.3.2.ceda (1836–2025)**.

Required variables:

- `tasmax` — daily maximum air temperature (°C)
- `tasmin` — daily minimum air temperature (°C)
- `rainfall` — daily precipitation (mm)

CEDA catalogue DOI: `10.5285/386b3c1ee2054ef5ae0d73060963a9f1`

Exact archive release used: `v20260512`.

Files:

```text
rainfall_hadukgrid_uk_region_day_18910101-20251231.nc
tasmax_hadukgrid_uk_region_day_19310101-20251231.nc
tasmin_hadukgrid_uk_region_day_19310101-20251231.nc
```

CEDA requires a registered-user login for these data. For automated downloads, create an archive access token and expose it as `CEDA_TOKEN`; the repository never stores credentials.

Run:

```bash
python download_haduk.py
```

Then extract the Yorkshire regional series:

```bash
python prepare_haduk_weather.py \
  --tasmax data/raw/weather/netcdf/tasmax_hadukgrid_uk_region_day_19310101-20251231.nc \
  --tasmin data/raw/weather/netcdf/tasmin_hadukgrid_uk_region_day_19310101-20251231.nc \
  --rainfall data/raw/weather/netcdf/rainfall_hadukgrid_uk_region_day_18910101-20251231.nc \
  --region-pattern Yorkshire
```

The output is:

```text
data/raw/weather/haduk_yorkshire_daily.csv
```

with columns:

```text
date,tasmax,tasmin,rainfall
```

## Why regional weather rather than exact grid cells?

The Yorkshire Water DMAs are anonymised, so their precise locations are intentionally unavailable. A Yorkshire-and-Humber regional HadUK series is therefore used as an area-level weather exposure. This is transparent and reproducible, but it means the project should be presented as a portfolio forecasting exercise rather than a production DMA forecast.
