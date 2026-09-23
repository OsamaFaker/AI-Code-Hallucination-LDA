# Document-Length Audit (full text, substantive tokens)

- n = 66
- min = 1531
- max = 26348
- mean = 6810.9
- median = 5747.0
- SD = 4296.0
- Q1 = 3858.2
- Q3 = 8609.0
- IQR = 4750.8
- max/min ratio = 17.21

- IQR upper fence (Q3 + 1.5*IQR) = 15735.1
- **Frozen Stage-5 length cap (rounded to nearest 500)**: **15500** tokens (per PRE_EXECUTION_ANALYSIS_PLAN.md SS13 -- fixed here, before any topic modelling, not chosen after seeing results)

- Documents above the IQR upper fence: **2**

| Study_ID | substantive_tokens |
|---|---|
| S50 | 26348 |
| S17 | 19945 |

Figures: `figures/fulltext/doc_length_histogram.png`, `doc_length_boxplot.png`, `doc_length_distribution.png` (combined).

This ~17x max/min spread motivates the mandatory full-text length-sensitivity analysis (Stage 5, plan SS13): long articles can contribute disproportionately more word counts to classical LDA.
