"""Fixed-model, expanding-window comparisons by area and meter location."""
from pathlib import Path
import json
import hashlib
import numpy as np
import pandas as pd
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from src.features import build_features, FEATURES
from src.model import ridge, score
from src.weather import read_weather

ROOT = Path(__file__).resolve().parent
OUT = ROOT / 'outputs/final'


def windows(n, minimum_train=365, block=90):
    """Latest nonoverlapping blocks, each preceded by >=365 daily rows."""
    count = min(6, (n-minimum_train)//block)
    return [(s, s+block) for s in range(n-count*block, n, block)]


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    source = ROOT / 'data/raw/demand/yorkshire_daily_customer_meter.csv'
    raw = pd.read_csv(source)
    columns = [c for c in raw if '/' in c]
    dates = pd.to_datetime(columns, format='%d/%m/%Y')
    values = raw[columns].apply(pd.to_numeric, errors='coerce')
    values = values.where(values >= 0)
    weather = read_weather(ROOT / 'data/raw/weather/haduk_yorkshire_daily.csv')
    all_metrics, all_predictions, cover = [], [], []
    for (dma, location), rows in raw.groupby(['DMA','meter location']).groups.items():
        v = values.loc[rows]
        observed = v.count().to_numpy() > 0
        first, last = np.flatnonzero(observed)[[0,-1]]
        for target in ['mean','median']:
            y = getattr(v, target)().to_numpy()
            base = pd.DataFrame({'date':dates,'demand_m3_per_meter':y,
                                 'n_observations':v.count().to_numpy()}).iloc[first:last+1]
            frame = build_features(base.merge(weather,on='date',how='left',validate='one_to_one'))
            assert (frame.date.diff().dropna().dt.days == 1).all()
            frame = frame.iloc[14:].reset_index(drop=True)
            assert frame[FEATURES+['demand_m3_per_meter']].notna().all().all()
            for fold, (start,end) in enumerate(windows(len(frame)),1):
                train, test = frame.iloc[:start], frame.iloc[start:end]
                assert train.date.max() < test.date.min()
                # Training-derived coverage threshold; retain all days for primary scores.
                threshold = 0.9*train.n_observations.median()
                sufficient = test.n_observations >= threshold
                cover.append({'DMA':dma,'location':location,'target':target,'fold':fold,
                              'train_days':len(train),'start':test.date.min(),'end':test.date.max(),
                              'coverage_threshold':threshold,'low_coverage_days':int((~sufficient).sum())})
                models = {'previous_day':test.demand_lag1.to_numpy(),
                          'weekly_baseline':test.demand_lag7.to_numpy(),
                          'ridge_without_weather':ridge(train,test,FEATURES[8:]).prediction,
                          'ridge_with_weather':ridge(train,test,FEATURES).prediction}
                for name,pred in models.items():
                    for scope, mask in [('all_days',np.ones(len(test),dtype=bool)),
                                       ('coverage_sensitivity',sufficient.to_numpy())]:
                        if mask.sum() < 2:
                            continue
                        all_metrics.append({'DMA':dma,'location':location,'target':target,
                            'fold':fold,'model':name,'scope':scope,'n':int(mask.sum()),
                            **score(test.demand_m3_per_meter.to_numpy()[mask],pred[mask])})
                    all_predictions.extend({'DMA':dma,'location':location,'target':target,
                        'fold':fold,'model':name,'date':d,'observed':o,'predicted':p,
                        'coverage_ok':bool(ok)} for d,o,p,ok in zip(test.date,test.demand_m3_per_meter,pred,sufficient))
    metrics = pd.DataFrame(all_metrics)
    metrics.to_csv(OUT/'fold_metrics.csv',index=False)
    pd.DataFrame(all_predictions).to_csv(OUT/'predictions.csv',index=False)
    pd.DataFrame(cover).to_csv(OUT/'coverage.csv',index=False)
    avg = metrics[metrics.scope=='all_days'].groupby(['DMA','location','target','model']).MAE.mean().unstack()
    avg['weather_MAE_change_pct'] = 100*(avg.ridge_with_weather/avg.ridge_without_weather-1)
    avg.to_csv(OUT/'summary.csv')
    fig, axes=plt.subplots(2,1,figsize=(11,8))
    labels=[f'Area {a} / {b} / {c}' for a,b,c in avg.index]
    avg[['previous_day','weekly_baseline','ridge_without_weather','ridge_with_weather']].plot.bar(ax=axes[0])
    axes[0].set_yscale('log'); axes[0].set_ylabel('Mean block MAE (m³; log scale)')
    axes[0].set_xticklabels([]); axes[0].set_xlabel(''); axes[0].legend(fontsize=8,ncol=2)
    axes[1].bar(range(len(avg)),avg.weather_MAE_change_pct,color=['#b45309' if x>0 else '#168575' for x in avg.weather_MAE_change_pct])
    axes[1].axhline(0,color='black',linewidth=0.8)
    axes[1].set_xticks(range(len(avg)),labels,rotation=30,ha='right')
    axes[1].set_ylabel('Weather change in MAE (%)\nNegative = improvement')
    axes[0].set_title('Separate area and meter targets — retrospective validation')
    fig.tight_layout(); fig.savefig(OUT/'comparison.png',dpi=160); plt.close(fig)
    (OUT/'provenance.json').write_text(json.dumps({'demand_sha256':hashlib.sha256(source.read_bytes()).hexdigest(),
        'weather_sha256':hashlib.sha256((ROOT/'data/raw/weather/haduk_yorkshire_daily.csv').read_bytes()).hexdigest(),
        'minimum_training_rows':365,'block_days':90,'max_blocks':6,'ridge_alpha':10,
        'coverage_threshold':'90% of training median record count; evaluation sensitivity only'},indent=2))
    print(avg.to_string())


if __name__ == '__main__':
    main()
