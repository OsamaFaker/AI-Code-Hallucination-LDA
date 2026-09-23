# Stage 2 Decision -- metadata

## Priors

- Best-C_v prior: alpha=1.0, eta=auto (C_v=0.3767)
- Priors within tolerance of best (comparable set): 4
- auto/auto in comparable set: False
- **Selected: alpha=1.0, eta=auto** (C_v=0.3767, stability=0.4883)

## Convergence / training budget

- Converged at passes=20, iterations=200 (JS vs next=0.9683 >= 0.95, dominant-topic agreement=0.9778 >= 0.95)
- **Selected: passes=20, iterations=200**

## FROZEN Stage 2 configuration

- alpha = **1.0**
- eta = **auto**
- passes = **20**
- iterations = **200**

These four values are frozen and used, together with the Stage 1 dictionary/preprocessing config, for the Stage 3 definitive k-sweep. Not revisited except via a documented protocol amendment (plan SS35).
