# Follow-up: prior-day weather and nested model selection

## Improvements to validity

`improve_models.py` tests models using calendar variables, previous observed demand and weather ending on the previous day. It avoids the same-day observed weather used in the earlier retrospective analysis. This assumes yesterday's observations are available when predictions are issued; actual metering/weather publication delays still need operational verification.

The shared feature builder now rejects duplicate, invalid or missing calendar dates. This prevents row offsets from silently becoming incorrect daily lags. A regression test changes same-day and future demand/weather and verifies that the prior-day predictor set does not change.

## A deliberately small candidate library

For each existing outer test block, the preceding training period's final 90 days select among 14 candidates: yesterday, weekly persistence, or Ridge with alpha 1/10/100, with or without previous-day weather, using either the original target or log1p target. Scaling is fitted only on the inner training rows. The winning candidate is then refitted on all outer training rows. Selection uses MAE in original units, and the outer test values are never used for candidate selection. Log predictions are transformed back with expm1; negative predictions are clipped to zero. This does not constitute an unbiased estimate of a conditional mean under log transformation.

A minimum 365-row outer training history leaves at least 275 inner fitting rows. One internal validation block can be unstable; this is intentionally a bounded experiment, not an extensive hyperparameter search. The fixed-history Ridge comparator is retained. Raw observations and target definitions are unchanged.

## Results

Average outer-block MAE, m³ per record per day:

| Target | Fixed history Ridge | Selected model procedure | Change |
|---|---:|---:|---:|
| Area 1 external mean | 0.206674 | 0.526911 | +154.95% |
| Area 1 external median | 0.006209 | 0.006355 | +2.34% |
| Area 1 internal mean | 0.009090 | 0.009745 | +7.20% |
| Area 1 internal median | 0.008236 | 0.008339 | +1.25% |
| Area 2 external mean | 0.060778 | 0.060466 | −0.51% |
| Area 2 external median | 0.007513 | 0.007466 | −0.64% |
| Area 2 internal mean | 0.064972 | 0.057489 | −11.52% |
| Area 2 internal median | 0.008251 | 0.008231 | −0.25% |

Area 1 has only one outer block per target. Area 2 has six. The 11.52% improvement for Area 2 internal mean is relative to Ridge; weekly persistence is still slightly better (0.056498). No overall improvement claim is justified. The log variant badly underperforms on Area 1 external mean despite winning its inner comparison. This demonstrates instability under the anomalous training distribution rather than supporting automatic deployment of the selected model.

Fixed prior-day weather Ridge produces MAE 0.060727 on Area 2 external mean, versus 0.060778 without weather: practically little difference. On its median target, prior-day weather slightly worsens MAE (0.007526 versus 0.007513). The earlier 3.36% gain used same-day observed weather and should not be quoted as an available-at-issue-time improvement.

## Decision

Retain simple history-only Ridge and persistence as reference methods, with previous results intact. Do not replace them globally with the model-selection procedure or remove anomalous source readings just to improve scores. The project now offers a more defensible information-timing comparison and transparent evidence that additional modelling complexity does not consistently help.

These same historical test periods have already been examined during project development. Nested selection prevents direct parameter fitting to the outer block, but does not make this an independent untouched confirmation dataset. No confidence intervals or significance claims are made. Source anomalies, reporting latency and population changes remain limitations.

## Reproduce

Run `.venv\Scripts\python.exe improve_models.py`, or use the complete `run_real_data.py` workflow. Results are in `outputs/improved/`: per-fold metrics, inner-selection decisions and dates, daily predictions and summary. These files preserve unsuccessful variants for auditability.
