# Stage 1 Decision -- metadata

Per the frozen rules in PRE_EXECUTION_ANALYSIS_PLAN.md SS9.

## Per-variant best dictionary config (frozen selection rule)

| HF | bigrams | no_below | no_above | vocab | empty_docs | mean_cv | mean_stability | note |
|---|---|---|---|---|---|---|---|---|
| A | False | 6 | 0.4 | 216 | 0 | 0.3201 | 0.5202 | selected from 34 eligible configs at neighbour tolerance step=1 |
| A | True | 6 | 0.5 | 222 | 0 | 0.3365 | 0.5086 | selected from 37 eligible configs at neighbour tolerance step=1 |
| B | False | 6 | 0.4 | 208 | 0 | 0.3445 | 0.5064 | selected from 33 eligible configs at neighbour tolerance step=1 |
| B | True | 6 | 0.4 | 206 | 0 | 0.3463 | 0.5227 | selected from 33 eligible configs at neighbour tolerance step=1 |

## Step 1: unigram vs. bigram

- Bigram mean C_v advantage (averaged over HF-A/HF-B): 0.0091 (threshold: >0.02)
- Bigram stability loss: -0.0023 (threshold: <0.03)
- **Decision: unigram (default)**

## Step 2: HF-A vs. HF-B (at the chosen bigram setting)

- HF-B mean C_v advantage over HF-A: 0.0244 (threshold: >0.02)
- HF-B stability loss: 0.0138 (threshold: <0.03)
- **Decision: HF-B (remove HF-B filler list)**

## FINAL Stage 1 configuration

- HF variant: **HF-B**
- Bigrams: **False**
- no_below: **6**
- no_above: **0.4**
- Vocabulary size: **208**
- Empty documents: **0**
- Pilot mean C_v: **0.3445** (SD 0.0213)
- Pilot mean C_NPMI: **-0.1932** (SD 0.0217)
- Pilot mean stability: **0.5064** (SD 0.0598)
- Pilot mean diversity: **0.5710**
- Selection note: selected from 33 eligible configs at neighbour tolerance step=1
