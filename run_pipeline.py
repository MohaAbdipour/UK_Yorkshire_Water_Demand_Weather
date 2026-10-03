from pathlib import Path
import pandas as pd
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

from src.demand import read_and_aggregate_demand
from src.weather import read_weather
from src.features import build_features, FEATURES
from src.model import seasonal_naive, ridge, hgb


ROOT = Path(__file__).resolve().parent
DEMAND = ROOT / "data/raw/demand/yorkshire_daily_customer_meter.csv"
WEATHER = ROOT / "data/raw/weather/haduk_yorkshire_daily.csv"
PROCESSED = ROOT / "data/processed"
OUTPUTS = ROOT / "outputs"

TEST_DAYS = 90


def main():
    PROCESSED.mkdir(parents=True, exist_ok=True)
    OUTPUTS.mkdir(parents=True, exist_ok=True)

    demand = read_and_aggregate_demand(DEMAND)
    weather = read_weather(WEATHER)

    joined = demand.merge(weather, on="date", how="inner")
    joined = build_features(joined)
    joined.to_csv(PROCESSED / "model_table.csv", index=False)

    data = joined.dropna(subset=[
        "demand_m3_per_meter",
        "demand_lag7",
        "demand_lag14",
        "demand_roll7",
    ]).reset_index(drop=True)

    if len(data) < TEST_DAYS + 180:
        raise ValueError(
            f"Only {len(data)} usable joined days. "
            "Check demand/weather date coverage."
        )

    train = data.iloc[:-TEST_DAYS].copy()
    test = data.iloc[-TEST_DAYS:].copy()

    results = [
        seasonal_naive(test),
        ridge(train, test, FEATURES),
        hgb(train, test, FEATURES),
    ]

    metrics = pd.DataFrame(
        [{"model": r.name, **r.metrics} for r in results]
    ).sort_values("MAE")
    metrics.to_csv(OUTPUTS / "metrics.csv", index=False)

    preds = test[[
        "date", "demand_m3_per_meter", "n_observations",
        "tasmax", "tasmin", "rainfall"
    ]].copy()
    for r in results:
        preds[r.name] = r.prediction
    preds.to_csv(OUTPUTS / "predictions.csv", index=False)

    plt.figure(figsize=(11, 5.5))
    plt.plot(preds["date"], preds["demand_m3_per_meter"],
             label="Observed", linewidth=2)
    for r in results:
        plt.plot(preds["date"], preds[r.name], label=r.name, alpha=0.85)
    plt.ylabel("Mean consumption (m³ per observed meter/day)")
    plt.xlabel("Date")
    plt.title("Held-out Yorkshire customer-demand forecast")
    plt.legend()
    plt.tight_layout()
    plt.savefig(OUTPUTS / "forecast_test.png", dpi=180)
    plt.close()

    joined_plot = data.copy()
    joined_plot["tmean"] = (joined_plot["tasmax"] + joined_plot["tasmin"]) / 2
    plt.figure(figsize=(7, 5))
    plt.scatter(
        joined_plot["tmean"],
        joined_plot["demand_m3_per_meter"],
        alpha=0.35
    )
    plt.xlabel("Mean temperature (°C)")
    plt.ylabel("Mean consumption (m³ per observed meter/day)")
    plt.title("Daily demand–temperature relationship")
    plt.tight_layout()
    plt.savefig(OUTPUTS / "demand_weather_relationship.png", dpi=180)
    plt.close()

    best_ml = min(
        [r for r in results if r.name != "seasonal_naive_7d"],
        key=lambda r: r.metrics["MAE"],
    )
    tmean = (preds["tasmax"] + preds["tasmin"]) / 2
    residual = preds["demand_m3_per_meter"].to_numpy() - best_ml.prediction

    plt.figure(figsize=(7, 5))
    plt.scatter(tmean, residual, alpha=0.75)
    plt.axhline(0, linewidth=1)
    plt.xlabel("Mean temperature (°C)")
    plt.ylabel("Observed - predicted demand")
    plt.title(f"Residuals vs temperature: {best_ml.name}")
    plt.tight_layout()
    plt.savefig(OUTPUTS / "residuals_vs_temperature.png", dpi=180)
    plt.close()

    ridge_result = next(r for r in results if r.name == "ridge")
    coef = ridge_result.model.named_steps["model"].coef_
    pd.DataFrame({
        "feature": FEATURES,
        "standardised_coefficient": coef,
    }).assign(
        abs_coef=lambda x: x["standardised_coefficient"].abs()
    ).sort_values(
        "abs_coef", ascending=False
    ).drop(columns="abs_coef").to_csv(
        OUTPUTS / "ridge_coefficients.csv", index=False
    )

    print("\nHeld-out performance")
    print(metrics.to_string(index=False))
    print("\nDate coverage:")
    print(data["date"].min().date(), "to", data["date"].max().date())
    print("\nOutputs:", OUTPUTS)


if __name__ == "__main__":
    main()
