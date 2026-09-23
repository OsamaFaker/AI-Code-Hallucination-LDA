# Stage 1 Decision -- fulltext

Per the frozen rules in PRE_EXECUTION_ANALYSIS_PLAN.md SS9.

## Per-variant best dictionary config (frozen selection rule)

| HF | bigrams | no_below | no_above | vocab | empty_docs | mean_cv | mean_stability | note |
|---|---|---|---|---|---|---|---|---|
| A | False | 6 | 0.4 | 1503 | 0 | 0.3214 | 0.4674 | selected from 25 eligible configs at neighbour tolerance step=1 |
| A | True | 6 | 0.4 | 1853 | 0 | 0.3254 | 0.4971 | selected from 38 eligible configs at neighbour tolerance step=1 |
| B | False | 6 | 0.4 | 1503 | 0 | 0.3214 | 0.4674 | selected from 34 eligible configs at neighbour tolerance step=1 |
| B | True | 6 | 0.4 | 1807 | 0 | 0.3265 | 0.4928 | selected from 38 eligible configs at neighbour tolerance step=1 |

## Step 1: unigram vs. bigram

- Bigram mean C_v advantage (averaged over HF-A/HF-B): 0.0045 (threshold: >0.02)
- Bigram stability loss: -0.0275 (threshold: <0.03)
- **Decision: unigram (default)**

## Step 2: HF-A vs. HF-B (at the chosen bigram setting)

- HF-B mean C_v advantage over HF-A: -0.0000 (threshold: >0.02)
- HF-B stability loss: 0.0000 (threshold: <0.03)
- **Decision: HF-A (retain domain terms)**

## FINAL Stage 1 configuration

- HF variant: **HF-A**
- Bigrams: **False**
- no_below: **6**
- no_above: **0.4**
- Vocabulary size: **1503**
- Empty documents: **0**
- Pilot mean C_v: **0.3214** (SD 0.0249)
- Pilot mean C_NPMI: **-0.2382** (SD 0.0162)
- Pilot mean stability: **0.4674** (SD 0.0543)
- Pilot mean diversity: **0.7947**
- Selection note: selected from 25 eligible configs at neighbour tolerance step=1
