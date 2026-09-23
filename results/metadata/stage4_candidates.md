# Stage 4 Candidate Selection -- metadata

## Mega-/thin-/zero-topic flags, all k (inspection triggers, not rejections)

| k | flags |
|---|---|
| 2 | large topic proportion: 50.0% |
| 3 | (none) |
| 4 | (none) |
| 5 | THIN (<5 studies) topics: 1 |
| 6 | (none) |
| 7 | (none) |
| 8 | VERY THIN (<3 studies) topics: 1; THIN (<5 studies) topics: 1 |
| 9 | THIN (<5 studies) topics: 2 |
| 10 | VERY THIN (<3 studies) topics: 1; THIN (<5 studies) topics: 3 |
| 11 | VERY THIN (<3 studies) topics: 4; THIN (<5 studies) topics: 7 |
| 12 | ZERO-DOMINANCE topics: 1; VERY THIN (<3 studies) topics: 3; THIN (<5 studies) topics: 7 |
| 13 | ZERO-DOMINANCE topics: 2; VERY THIN (<3 studies) topics: 5; THIN (<5 studies) topics: 5 |
| 14 | ZERO-DOMINANCE topics: 1; VERY THIN (<3 studies) topics: 4; THIN (<5 studies) topics: 7 |
| 15 | ZERO-DOMINANCE topics: 3; VERY THIN (<3 studies) topics: 6; THIN (<5 studies) topics: 8 |
| 16 | ZERO-DOMINANCE topics: 2; VERY THIN (<3 studies) topics: 5; THIN (<5 studies) topics: 9 |
| 17 | ZERO-DOMINANCE topics: 2; VERY THIN (<3 studies) topics: 4; THIN (<5 studies) topics: 11 |
| 18 | ZERO-DOMINANCE topics: 2; VERY THIN (<3 studies) topics: 5; THIN (<5 studies) topics: 13 |
| 19 | ZERO-DOMINANCE topics: 4; VERY THIN (<3 studies) topics: 9; THIN (<5 studies) topics: 12 |
| 20 | ZERO-DOMINANCE topics: 4; VERY THIN (<3 studies) topics: 10; THIN (<5 studies) topics: 14 |

## Pareto-optimal set: 15 k value(s)

k = [2, 3, 4, 5, 6, 7, 8, 9, 10, 12, 13, 14, 16, 17, 18]

## Finalists after frozen reduction rule (max 4, ranked by stability): 4 k value(s)

| k | mean_cv | mean_cnpmi | mean_stability | mean_diversity | redundancy_jaccard | zero_dom | thin<5 | entropy | assign_conf |
|---|---|---|---|---|---|---|---|---|---|
| 2 | 0.3237 | -0.1487 | 0.7305 | 0.9410 | 0.0526 | 0 | 0 | 1.0000 | 0.8431 |
| 3 | 0.3473 | -0.1491 | 0.6477 | 0.8913 | 0.0441 | 0 | 0 | 0.9975 | 0.7523 |
| 4 | 0.3584 | -0.1638 | 0.5815 | 0.8490 | 0.0394 | 0 | 0 | 0.9857 | 0.7193 |
| 5 | 0.3695 | -0.1727 | 0.5489 | 0.8000 | 0.0487 | 0 | 1 | 0.9286 | 0.6661 |

## Cross-k persistence among finalists (rectangular Hungarian alignment)

| k1 | k2 | matched topics | mean JS similarity | mean top-20 Jaccard | unmatched in k2 |
|---|---|---|---|---|---|
| 2 | 3 | 2 | 0.7507 | 0.5741 | 1 |
| 3 | 4 | 3 | 0.8464 | 0.6069 | 1 |
| 4 | 5 | 4 | 0.6462 | 0.4268 | 1 |

High JS similarity / Jaccard between consecutive finalists suggests the larger k mostly subdivides or duplicates themes already present at the smaller k; low values suggest genuinely new themes emerge. Interpreted qualitatively in the final report, not used as an automatic elimination rule.
