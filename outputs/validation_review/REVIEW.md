# Demand forecasting validation review

## Conclusion

The current evidence does not establish a consistent predictive benefit from weather. Data quality and changing meter coverage need resolution before presenting this as an operational forecasting model.

## Data audit

- 2,596 source meter records across 1,125 consecutive days; a record is not necessarily a unique property (internal and external meters can share a property).
- 660,783 missing readings and five negative readings. Existing aggregation excludes negative values.
- Daily reporting counts range from 114 to 2,541. Coverage changes sharply around September 2013 and February 2015, with particularly sparse boundary days.
- The highest reading is 11,910 m³ in source row index 197 on 29 September 2013. That record contributes 89.65% of total consumption on the day with the highest mean. The daily median does not show a corresponding spike.
- Only two records have nonmissing, nonnegative readings for the entire period; restricting to a fully complete panel would not be representative.
- These findings flag possible source anomalies, unit issues or atypical users. They do not prove an error and do not justify automatically deleting observations.

## Evaluation

Six expanding-training, nonoverlapping 90-day evaluation blocks cover 30 October 2013 through 22 April 2015. Parameters were fixed, with no tuning on these blocks. Each prediction uses the observed prior demand available that day; this is a sequence of daily predictions, not a 90-day forecast made at one origin. Same-day observed weather is retrospective information and would need forecast weather in deployment. Ridge without weather keeps the same calendar and demand-history predictors.

Average block MAE (m³ per observed meter record per day):

| Model | Original mean target | Exclude largest record: diagnostic only |
|---|---:|---:|
| Previous day | 0.056021 | 0.056035 |
| Weekly baseline | 0.059848 | 0.059865 |
| Ridge without weather | 0.056940 | 0.045878 |
| Ridge with weather | 0.062935 | 0.045699 |
| Gradient boosting with weather | 0.391128 | 0.063694 |

Weather increases Ridge's average MAE by about 10.5% on the original target. It improves Ridge in only one of six blocks. In the diagnostic exclusion scenario, weather improves average MAE by only about 0.4%, winning two of six blocks. No statistical significance is claimed.

Excluding source row 197 substantially reduces gradient boosting error, supporting sensitivity to the extreme training record as a major contributor. All evaluation blocks follow the September 2013 spike; this comparison mainly demonstrates sensitivity to contaminated or atypical training data. The exclusion was selected after viewing the full dataset and is not an independently validated cleaning rule. Raw files and main pipeline outputs remain unchanged by this review.

## Next work

Verify the extreme record's meaning and units against source documentation before adopting a cleaning rule. Investigate later high-contribution records and coverage shifts separately by DMA and meter location. Use coverage-aware sensitivity analyses and additional time periods before choosing a final model. Retain the previous-day baseline: it currently has the lowest average MAE on the original target.

## Reproduction and files

Run `.venv\Scripts\python.exe review_validation.py` from the project folder. The script asserts consecutive source dates, complete weather matching, at least a year of training, and training strictly preceding evaluation. It saves daily quality measures, largest readings, per-fold metrics, predictions, averages and `data_quality.png` here. RMSE in `average_metrics.csv` is the average of block RMSEs, not pooled RMSE.
