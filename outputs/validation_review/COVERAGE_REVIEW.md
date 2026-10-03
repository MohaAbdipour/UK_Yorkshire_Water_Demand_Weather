# Source and coverage investigation

## Verified source description

The [publisher catalogue](https://datamillnorth.org/dataset/daily-customer-meter-data-local-area-study-2y1yy), checked 3 October 2026, describes daily consumption in cubic metres and distinguishes internal from external meters. It does not explain the extreme readings on the catalogue page. A separate README is listed but was not retrieved in this review. Therefore no unit conversion or correction to the exceptional records is justified yet.

## Area participation explains major coverage changes

| Area | Meter location | Total source records | First reporting day | Last reporting day |
|---|---|---:|---|---|
| 1 | External | 702 | 2013-09-04 | 2015-02-11 |
| 1 | Internal | 271 | 2013-09-04 | 2015-02-16 |
| 2 | External | 1,383 | 2012-03-24 | 2015-04-21 |
| 2 | Internal | 240 | 2012-03-24 | 2015-04-22 |

These are first and last days with any valid readings, not guarantees of complete coverage throughout. Area 1's arrival and departure change the pooled target's composition. On the last study day only 114 internal records from Area 2 remain. That boundary day is not comparable with normal mixed-meter days.

There are 2,160 distinct anonymised properties but 2,596 meter records; 435 properties have multiple records. Pooling these records weights properties unequally and may represent overlapping consumption. The present target is explicitly a mean per observed meter record, not household demand or physical DMA supply.

## Extreme readings are concentrated in identifiable source records

| Anonymised property | Area | Location | Maximum daily m³ | Median daily m³ | Peak date |
|---|---|---|---:|---:|---|
| 163 | 1 | External | 11,910 | 0.778 | 2013-09-29 |
| 1303 | 2 | External | 1,378 | 0.545 | 2014-12-24 |
| 113 | 1 | External | 1,169 | 0.646 | 2015-01-01 |
| 419 | 1 | External | 724 | 0.353 | 2013-09-30 |

The largest source record is not the only exceptional series. Area 2 also has major extremes, so switching areas alone will not solve quality issues. These discrepancies warrant investigation but do not establish whether they are errors, different units, leakage, or unusual use.

## Recommended modelling design

Separate area and meter-location targets; start with Area 2 external meters because they provide the longest external-meter history. Assess reporting coverage and flag incomplete boundary days explicitly. Compare robust targets such as the daily median alongside the original mean, clearly acknowledging that these answer different questions. Establish any exclusion or capping rule from training data and source evidence before evaluation; do not select a rule because it improves the final test score. Keep previous-day and weekly baselines and repeat the weather comparison.

No raw observations were changed. `review_coverage.py` reproduces the group summaries and extreme-record tables in this folder. Source-unit explanations remain unresolved pending more detailed documentation or publisher clarification; no publisher was contacted.
