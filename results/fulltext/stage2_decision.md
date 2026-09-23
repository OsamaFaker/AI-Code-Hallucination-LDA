# Stage 2 Decision -- fulltext

## Priors

- Best-C_v prior: alpha=1.0, eta=auto (C_v=0.3259)
- Priors within tolerance of best (comparable set): 14
- auto/auto in comparable set: True
- **Selected: alpha=auto, eta=auto** (C_v=0.3214, stability=0.4674)

## Convergence / training budget

- Converged at passes=20, iterations=200 (JS vs next=0.9585 >= 0.95, dominant-topic agreement=0.9687 >= 0.95)
- **Selected: passes=20, iterations=200**

## FROZEN Stage 2 configuration

- alpha = **auto**
- eta = **auto**
- passes = **20**
- iterations = **200**

These four values are frozen and used, together with the Stage 1 dictionary/preprocessing config, for the Stage 3 definitive k-sweep. Not revisited except via a documented protocol amendment (plan SS35).
