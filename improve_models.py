"""Nested chronological selection using only prior-day observations.

The last 90 days of each outer training set select a small, fixed candidate
library. Outer scores never select a candidate. Log models target the same
original mean/median, with predictions transformed back before scoring.
"""
from pathlib import Path
import numpy as np
import pandas as pd
from sklearn.linear_model import Ridge
from sklearn.pipeline import make_pipeline
from sklearn.preprocessing import StandardScaler
from src.features import FEATURES, build_features
from src.model import score
from src.weather import read_weather
from final_analysis import windows

ROOT = Path(__file__).resolve().parent
HISTORY = FEATURES[8:]
PAST_WEATHER = [f'past_{f}' for f in FEATURES[:8]]


def available_features(frame):
    out = build_features(frame)
    for f in FEATURES[:8]:
        out[f'past_{f}'] = out[f].shift(1)
    return out


def predict(train, test, kind, weather=False, alpha=10):
    if kind == 'previous_day':
        return test.demand_lag1.to_numpy()
    if kind == 'weekly':
        return test.demand_lag7.to_numpy()
    features = HISTORY + (PAST_WEATHER if weather else [])
    y = train.demand_m3_per_meter.to_numpy()
    model = make_pipeline(StandardScaler(), Ridge(alpha=alpha))
    model.fit(train[features], np.log1p(y) if kind == 'log_ridge' else y)
    p = model.predict(test[features])
    return np.maximum(0, np.expm1(p) if kind == 'log_ridge' else p)


def select(train, candidates):
    fit, validation = train.iloc[:-90], train.iloc[-90:]
    if len(fit) < 180:
        raise ValueError('Insufficient inner training history.')
    results = []
    for candidate in candidates:
        pred = predict(fit, validation, **candidate)
        results.append(float(np.abs(validation.demand_m3_per_meter.to_numpy()-pred).mean()))
    winner = int(np.argmin(results))
    return candidates[winner], results[winner]


def main():
    out = ROOT/'outputs/improved'
    out.mkdir(parents=True, exist_ok=True)
    raw = pd.read_csv(ROOT/'data/raw/demand/yorkshire_daily_customer_meter.csv')
    columns = [c for c in raw if '/' in c]
    dates = pd.to_datetime(columns,format='%d/%m/%Y')
    values = raw[columns].apply(pd.to_numeric,errors='coerce')
    values = values.where(values>=0)
    weather = read_weather(ROOT/'data/raw/weather/haduk_yorkshire_daily.csv')
    candidates = [{'kind':'previous_day'},{'kind':'weekly'}]+[
        {'kind':kind,'weather':w,'alpha':a}
        for kind in ['ridge','log_ridge'] for w in [False,True] for a in [1,10,100]]
    metrics, selections, predictions = [], [], []
    for (dma,location),rows in raw.groupby(['DMA','meter location']).groups.items():
        v = values.loc[rows]
        first,last = np.flatnonzero(v.count().to_numpy()>0)[[0,-1]]
        for target in ['mean','median']:
            base = pd.DataFrame({'date':dates,'demand_m3_per_meter':getattr(v,target)().to_numpy()}).iloc[first:last+1]
            frame = available_features(base.merge(weather,on='date',how='left',validate='one_to_one')).iloc[14:]
            if not np.isfinite(frame[HISTORY+PAST_WEATHER+['demand_m3_per_meter']].to_numpy()).all():
                raise ValueError('Nonfinite model inputs.')
            for fold,(start,end) in enumerate(windows(len(frame)),1):
                train,test = frame.iloc[:start],frame.iloc[start:end]
                winner, inner_mae = select(train,candidates)
                selections.append({'DMA':dma,'location':location,'target':target,'fold':fold,
                    'inner_start':train.date.iloc[-90],'inner_end':train.date.iloc[-1],
                    'test_start':test.date.iloc[0],'test_end':test.date.iloc[-1],
                    'candidate':str(winner),'inner_MAE':inner_mae})
                models = {'selected':winner,'previous_day':{'kind':'previous_day'},
                    'weekly':{'kind':'weekly'},'fixed_history_ridge':{'kind':'ridge'},
                    'fixed_past_weather_ridge':{'kind':'ridge','weather':True},
                    'fixed_log_history_ridge':{'kind':'log_ridge'}}
                for name,candidate in models.items():
                    p = predict(train,test,**candidate)
                    metrics.append({'DMA':dma,'location':location,'target':target,'fold':fold,
                        'model':name,**score(test.demand_m3_per_meter,p)})
                    predictions.extend({'DMA':dma,'location':location,'target':target,'fold':fold,
                        'model':name,'date':d,'observed':y,'predicted':z}
                        for d,y,z in zip(test.date,test.demand_m3_per_meter,p))
    m = pd.DataFrame(metrics)
    m.to_csv(out/'fold_metrics.csv',index=False)
    pd.DataFrame(selections).to_csv(out/'selections.csv',index=False)
    pd.DataFrame(predictions).to_csv(out/'predictions.csv',index=False)
    summary=m.groupby(['DMA','location','target','model']).MAE.mean().unstack()
    summary['selected_vs_history_pct']=100*(summary.selected/summary.fixed_history_ridge-1)
    summary.to_csv(out/'summary.csv')
    print(summary.to_string())


if __name__=='__main__':
    main()
