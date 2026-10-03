"""Reproducible data audit and fixed-parameter expanding-window comparison."""
from pathlib import Path
import json
import numpy as np
import pandas as pd
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from src.features import build_features, FEATURES
from src.weather import read_weather
from src.model import ridge, hgb, score

ROOT = Path(__file__).resolve().parent
OUT = ROOT / 'outputs' / 'validation_review'


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    raw = pd.read_csv(ROOT / 'data/raw/demand/yorkshire_daily_customer_meter.csv')
    columns = [c for c in raw if '/' in c]
    values = raw[columns].apply(pd.to_numeric, errors='coerce')
    clean = values.where(values >= 0)
    dates = pd.to_datetime(columns, format='%d/%m/%Y')
    assert dates.is_unique and (dates.to_series().diff().dropna().dt.days == 1).all()
    daily = pd.DataFrame({'date': dates, 'mean': clean.mean(),
                          'median': clean.median(), 'count': clean.count(),
                          'maximum': clean.max(),
                          'largest_record_share': clean.max()/clean.sum()}).reset_index(drop=True)
    daily.to_csv(OUT / 'daily_quality.csv', index=False)
    extremes = clean.stack().nlargest(20).rename('consumption_m3').reset_index()
    extremes.columns = ['source_row_index', 'date', 'consumption_m3']
    extremes.to_csv(OUT / 'largest_readings.csv', index=False)
    top_row = clean.max(axis=1).idxmax()
    summary = {'meter_records': len(raw), 'days': len(dates),
               'missing_cells': int(values.isna().sum().sum()),
               'negative_cells': int((values < 0).sum().sum()),
               'minimum_daily_records': int(clean.count().min()),
               'maximum_daily_records': int(clean.count().max()),
               'largest_reading_m3': float(clean.max().max()),
               'largest_reading_source_row_index': int(top_row),
               'largest_record_share_on_peak_mean_day': float(daily.loc[daily['mean'].idxmax(), 'largest_record_share']),
               'complete_records': int(clean.notna().all(axis=1).sum())}
    (OUT / 'quality_summary.json').write_text(json.dumps(summary, indent=2))
    weather = read_weather(ROOT / 'data/raw/weather/haduk_yorkshire_daily.csv')
    # Removing this record is an explicitly retrospective diagnostic, not a validated cleaning rule.
    targets = {'original_mean': clean.mean(),
               'exclude_largest_record_sensitivity': clean.drop(index=top_row).mean()}
    metrics = []
    predictions = []
    for scenario, target in targets.items():
        frame = pd.DataFrame({'date': dates, 'demand_m3_per_meter': target.to_numpy()})
        frame = build_features(frame.merge(weather, on='date', validate='one_to_one'))
        assert len(frame) == len(dates)
        frame = frame.dropna(subset=['demand_lag1','demand_lag7','demand_lag14','demand_roll7'])
        # Six non-overlapping 90-day blocks, ending at the original final test boundary.
        for fold, start in enumerate(range(len(frame)-540, len(frame), 90), 1):
            train, test = frame.iloc[:start], frame.iloc[start:start+90]
            assert len(train) >= 365 and train.date.max() < test.date.min()
            history = FEATURES[8:]
            models = {'previous_day': test.demand_lag1.to_numpy(),
                      'weekly_baseline': test.demand_lag7.to_numpy(),
                      'ridge_without_weather': ridge(train,test,history).prediction,
                      'ridge_with_weather': ridge(train,test,FEATURES).prediction,
                      'gradient_boosting': hgb(train,test,FEATURES).prediction}
            for name, pred in models.items():
                metrics.append({'scenario': scenario, 'fold': fold, 'model': name,
                                'train_days': len(train), 'start': test.date.min(),
                                'end': test.date.max(), **score(test.demand_m3_per_meter,pred)})
                predictions.extend({'scenario':scenario,'fold':fold,'model':name,
                                    'date':d,'observed':y,'predicted':p}
                                   for d,y,p in zip(test.date,test.demand_m3_per_meter,pred))
    results = pd.DataFrame(metrics)
    results.to_csv(OUT / 'fold_metrics.csv', index=False)
    pd.DataFrame(predictions).to_csv(OUT / 'validation_predictions.csv', index=False)
    average = results.groupby(['scenario','model'])[['MAE','RMSE']].mean()
    average.to_csv(OUT / 'average_metrics.csv')
    fig, axes = plt.subplots(3,1,figsize=(11,9),sharex=True)
    axes[0].plot(daily.date,daily['mean'],label='Mean'); axes[0].plot(daily.date,daily['median'],label='Median')
    axes[0].set_ylabel('m³ / record / day'); axes[0].legend()
    axes[1].plot(daily.date,daily['count']); axes[1].set_ylabel('Reporting records')
    axes[2].plot(daily.date,100*daily.largest_record_share); axes[2].set_ylabel('Largest record (%)')
    axes[0].set_title('Demand quality: extremes and changing coverage')
    fig.tight_layout(); fig.savefig(OUT / 'data_quality.png',dpi=150); plt.close(fig)
    print(json.dumps(summary,indent=2))
    print(average.to_string())
    base=results[results.scenario=='original_mean'].pivot(index='fold',columns='model',values='MAE')
    print('Original mean fold MAE:\n',base.to_string())


if __name__ == '__main__':
    main()
