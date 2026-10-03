from pathlib import Path
import requests

URL = (
    "https://datamillnorth.org/download/2y1yy/"
    "fb01ce66-423a-4111-9065-d989bdf0b3ce/"
    "Daily%20m3%201315.csv"
)

OUT = (
    Path(__file__).resolve().parent
    / "data" / "raw" / "demand"
    / "yorkshire_daily_customer_meter.csv"
)


def main():
    OUT.parent.mkdir(parents=True, exist_ok=True)
    print("Downloading Yorkshire Water daily customer meter data...")
    r = requests.get(URL, timeout=120)
    r.raise_for_status()
    OUT.write_bytes(r.content)
    print(f"Saved {len(r.content) / 1_000_000:.1f} MB to {OUT}")


if __name__ == "__main__":
    main()
