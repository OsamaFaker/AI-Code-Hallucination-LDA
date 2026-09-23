# Stage 4 Candidate Selection -- fulltext

## Mega-/thin-/zero-topic flags, all k (inspection triggers, not rejections)

| k | flags |
|---|---|
| 2 | large topic proportion: 54.5% |
| 3 | large topic proportion: 42.4% |
| 4 | (none) |
| 5 | (none) |
| 6 | (none) |
| 7 | (none) |
| 8 | (none) |
| 9 | THIN (<5 studies) topics: 2 |
| 10 | THIN (<5 studies) topics: 1 |
| 11 | THIN (<5 studies) topics: 2 |
| 12 | VERY THIN (<3 studies) topics: 1; THIN (<5 studies) topics: 3 |
| 13 | VERY THIN (<3 studies) topics: 2; THIN (<5 studies) topics: 5 |
| 14 | VERY THIN (<3 studies) topics: 2; THIN (<5 studies) topics: 6 |
| 15 | VERY THIN (<3 studies) topics: 2; THIN (<5 studies) topics: 7 |
| 16 | VERY THIN (<3 studies) topics: 2; THIN (<5 studies) topics: 9 |
| 17 | VERY THIN (<3 studies) topics: 2; THIN (<5 studies) topics: 9 |
| 18 | VERY THIN (<3 studies) topics: 5; THIN (<5 studies) topics: 13 |
| 19 | VERY THIN (<3 studies) topics: 5; THIN (<5 studies) topics: 14 |
| 20 | VERY THIN (<3 studies) topics: 6; THIN (<5 studies) topics: 16 |

## Pareto-optimal set: 19 k value(s)

k = [2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15, 16, 17, 18, 19, 20]

## Finalists after frozen reduction rule (max 4, ranked by stability): 4 k value(s)

| k | mean_cv | mean_cnpmi | mean_stability | mean_diversity | redundancy_jaccard | zero_dom | thin<5 | entropy | assign_conf |
|---|---|---|---|---|---|---|---|---|---|
| 2 | 0.2542 | -0.2743 | 0.7176 | 0.9730 | 0.0000 | 0 | 0 | 0.9940 | 0.8862 |
| 3 | 0.2792 | -0.2427 | 0.6356 | 0.9407 | 0.0446 | 0 | 0 | 0.9720 | 0.8611 |
| 4 | 0.2957 | -0.2512 | 0.5913 | 0.9070 | 0.0261 | 0 | 0 | 0.9496 | 0.8448 |
| 5 | 0.3108 | -0.2514 | 0.5524 | 0.8800 | 0.0292 | 0 | 0 | 0.9488 | 0.8406 |

## Cross-k persistence among finalists (rectangular Hungarian alignment)

| k1 | k2 | matched topics | mean JS similarity | mean top-20 Jaccard | unmatched in k2 |
|---|---|---|---|---|---|
| 2 | 3 | 2 | 0.7654 | 0.6388 | 1 |
| 3 | 4 | 3 | 0.7742 | 0.6349 | 1 |
| 4 | 5 | 4 | 0.6066 | 0.2341 | 1 |

High JS similarity / Jaccard between consecutive finalists suggests the larger k mostly subdivides or duplicates themes already present at the smaller k; low values suggest genuinely new themes emerge. Interpreted qualitatively in the final report, not used as an automatic elimination rule.
