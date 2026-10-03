"""Audit changing study composition without altering source observations."""
from pathlib import Path
import pandas as pd

ROOT = Path(__file__).resolve().parent
OUT = ROOT / 'outputs/validation_review'


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    raw = pd.read_csv(ROOT / 'data/raw/demand/yorkshire_daily_customer_meter.csv')
    columns = [c for c in raw if '/' in c]
    values = raw[columns].apply(pd.to_numeric, errors='coerce')
    values = values.where(values >= 0)
    dates = pd.to_datetime(columns, format='%d/%m/%Y')
    groups, summary = [], []
    for (dma, location), rows in raw.groupby(['DMA', 'meter location']).groups.items():
        v = values.loc[rows]
        count = v.count()
        available = count > 0
        groups.append(pd.DataFrame({'date': dates, 'DMA': dma, 'meter_location': location,
                                    'count': count.to_numpy(), 'mean': v.mean().to_numpy(),
                                    'median': v.median().to_numpy(), 'max': v.max().to_numpy()}))
        summary.append({'DMA': dma, 'meter_location': location, 'records': len(rows),
                        'first_date': dates[available][0], 'last_date': dates[available][-1],
                        'reporting_days': int(available.sum())})
    pd.concat(groups).to_csv(OUT / 'coverage_by_group.csv', index=False)
    pd.DataFrame(summary).to_csv(OUT / 'group_summary.csv', index=False)
    extremes = values.max(axis=1).nlargest(10)
    records = raw.loc[extremes.index, ['property','DMA','meter location']].copy()
    records['source_row_index'] = records.index
    records['maximum_m3'] = extremes
    records['median_m3'] = values.loc[extremes.index].median(axis=1)
    records['peak_date'] = values.loc[extremes.index].idxmax(axis=1)
    records.to_csv(OUT / 'extreme_record_metadata.csv', index=False)
    print(pd.DataFrame(summary).to_string(index=False))
    print('Distinct properties:',raw.property.nunique())
    print('Properties with multiple records:',int((raw.groupby('property').size()>1).sum()))


if __name__ == '__main__':
    main()
