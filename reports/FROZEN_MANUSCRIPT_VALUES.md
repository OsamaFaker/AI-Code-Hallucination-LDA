# Frozen Manuscript Values

Single authoritative source for every number eventually reported in the
paper. Values here are copied from the underlying CSV/MD outputs (cited
inline); if a discrepancy is ever found between this file and a source CSV,
the CSV is authoritative and this file must be corrected to match, not the
reverse.

## Reproducibility

| | |
|---|---|
| Python | 3.11.15 |
| gensim | 4.4.0 |
| spaCy | 3.8.16 (en_core_web_sm 3.8.0) |
| PyMuPDF | 1.28.2 |
| scikit-learn | 1.9.1 |
| scipy | 1.17.1 |
| numpy | 2.4.6 |
| pandas | 3.0.5 |
| openpyxl | 3.1.5 |
| Operating environment | Windows 11, isolated `.venv` (not system Python) |
| Corpus | 66 primary studies; SHA-256 checksums in `corpus/corpus_audit.csv` |
| Master seed list | [42,101,202,303,404,505,606,707,808,909,1010,1111,1212,1313,1414,1515,1616,1717,1818,1919,2020,2121,2222,2323,2424,2525,2626,2727,2828,2929] |
| Pilot seeds (Stage 1-2) | first 5: [42,101,202,303,404] |
| Definitive seeds (Stage 3) | first 20 of master list |
| Subsampling sampling-seeds | integers 1-100 (fixed `numpy.random.default_rng`) |
| Pilot k-set | {5, 10, 15} |

## Metadata (Analysis A) — FINAL k=4

| Item | Value | Source |
|---|---|---|
| Selected k | 4 | `results/metadata/stage4_candidates.md`, `HUMAN_VALIDATION_REPORT.md` |
| Selection reason | Unanimous human-rater preference + strongest redundancy/robustness among finalists | `HUMAN_VALIDATION_REPORT.md` |
| Structural-medoid seed | 1212 | `results/metadata/k_sweep_summary.csv` |
| Dictionary | no_below=6, no_above=0.4, vocab=208 | `results/metadata/stage1_decision.md` |
| Domain-term handling / phrase rep. | HF-B / unigram | `results/metadata/stage1_decision.md` |
| alpha / eta | 1.0 / auto | `results/metadata/stage2_decision.md` |
| passes / iterations | 20 / 200 | `results/metadata/stage2_decision.md` |
| Mean C_v (SD) | 0.3584 (0.0485) | `results/metadata/k_sweep_summary.csv` |
| Mean C_NPMI (SD) | -0.1638 (0.0146) | ibid. |
| Cross-seed stability (SD) | 0.5815 (0.0513) | ibid. |
| Topic diversity (top-25) | 0.8490 | ibid. |
| Redundancy (Jaccard / cosine) | 0.0394 / 0.2771 | ibid. |
| Dominant-study counts | [22, 16, 15, 13] | ibid. |
| Min / max dominant count | 13 / 22 | ibid. |
| Probabilistic prevalence | [0.292, 0.242, 0.242, 0.225] | ibid. |
| Normalized entropy | 0.9857 | ibid. |
| CV / Gini (dominant counts) | 0.2347 / 0.1061 | ibid. |
| Mean assignment confidence | 0.7193 | ibid. |
| Subsampling JS / ARI / NMI | 0.812 / 0.806 / 0.813 | `results/metadata/subsampling_k4.csv` |
| Training-effort JS / ARI / NMI | 0.884 / 0.929 / 0.918 | `results/metadata/training_effort_sensitivity.csv` |
| Dictionary sensitivity (2 neighbours) | JS 0.552/0.517; ARI 0.236/0.152 | `results/metadata/dictionary_sensitivity.csv` |

## Full text (Analysis B) — FINAL k=4

| Item | Value | Source |
|---|---|---|
| Selected k | 4 | `results/fulltext/stage4_candidates.md`, `HUMAN_VALIDATION_REPORT.md` |
| Selection reason | Rater 1's top choice + strongest redundancy/training-effort robustness; Rater 2 preferred k=5 (documented disagreement) | `HUMAN_VALIDATION_REPORT.md` |
| Structural-medoid seed | 505 | `results/fulltext/k_sweep_summary.csv` |
| Dictionary | no_below=6, no_above=0.4, vocab=1503 | `results/fulltext/stage1_decision.md` |
| Domain-term handling / phrase rep. | HF-A / unigram (HF-A = HF-B at this threshold) | `results/fulltext/stage1_decision.md` |
| alpha / eta | auto / auto | `results/fulltext/stage2_decision.md` |
| passes / iterations | 20 / 200 | `results/fulltext/stage2_decision.md` |
| Mean C_v (SD) | 0.2957 (0.0271) | `results/fulltext/k_sweep_summary.csv` |
| Mean C_NPMI (SD) | -0.2512 (0.0166) | ibid. |
| Cross-seed stability (SD) | 0.5913 (0.0296) | ibid. |
| Topic diversity (top-25) | 0.9070 | ibid. |
| Redundancy (Jaccard / cosine) | 0.0261 / 0.2922 | ibid. |
| Dominant-study counts | [17, 8, 16, 25] | ibid. |
| Min / max dominant count | 8 / 25 | ibid. |
| Probabilistic prevalence | [0.266, 0.135, 0.227, 0.372] | ibid. |
| Normalized entropy | 0.9496 | ibid. |
| CV / Gini (dominant counts) | 0.4214 / 0.1970 | ibid. |
| Mean assignment confidence | 0.8448 | ibid. |
| Subsampling JS / ARI / NMI | 0.810 / 0.799 / 0.799 | `results/fulltext/subsampling_k4.csv` |
| Training-effort JS / ARI / NMI | 0.905 / 0.856 / 0.865 | `results/fulltext/training_effort_sensitivity.csv` |
| Dictionary sensitivity (2 neighbours) | JS 0.569/0.516; ARI 0.284/0.230 | `results/fulltext/dictionary_sensitivity.csv` |
| Length-confidence correlation (Pearson r, p) | 0.358, 0.0031 | `results/fulltext/length_sensitivity_correlation.csv` |
| Length-balanced vs. original (JS/ARI/NMI) | 0.938 / 0.945 / 0.936 | `results/fulltext/length_sensitivity_comparison.csv` |
| Documents length-balanced | 2 / 66 (cap = 15,500 tokens) | `extraction/document_length_audit.md` |

## Cross-representation comparison

| Item | Value | Source |
|---|---|---|
| Document-level ARI / NMI | 0.2384 / 0.2738 | `results/cross_representation/intersection_analysis.csv`, `reports/CROSS_REPRESENTATION_REPORT.md` |
| Strongest topic correspondence | meta0↔ft3 (hallucination-mitigation), 17/22 studies (77.3%) | `results/cross_representation/contingency_matrix.csv` |
| Second correspondence | meta1↔ft0 (education), 9/16 studies (56.3%) | ibid. |
| Topics with distributed correspondence | meta2 (developer trust): 46.7%/46.7%/6.7% split across ft0/ft2/ft1; meta3 (correctness/testing): 38.5%/30.8%/30.8% split across ft3/ft1/ft2 | ibid. |

### Cross-representation comparison — shared-vocabulary analysis

| Item | Value | Source |
|---|---|---|
| Metadata vocabulary size | 208 | `results/cross_representation/intersection_analysis.csv` |
| Full-text vocabulary size | 1,503 | ibid. |
| Shared vocabulary (intersection) size | **19** | ibid. |
| % of metadata vocabulary shared | 9.13% | ibid. |
| % of full-text vocabulary shared | 1.26% | ibid. |
| Per-topic shared-vocab coverage (raw, pre-renorm) | meta: 0.029-0.096; ft: 0.021-0.101 | ibid. |
| JS similarity (matched pairs) | 0.449-0.562 | ibid. |
| Cosine similarity (matched pairs) | 0.458-0.821 | ibid. |
| Top-10 Jaccard (matched pairs) | 0.250-0.667 | ibid. |
| Top-20 Jaccard (matched pairs) | 1.000 (near-vacuous at 19-term intersection — see report) | ibid. |
| Permutation test (10,000 reps, seed=42) | p(ARI) < 0.0001, p(NMI) < 0.0001 | `results/cross_representation/permutation_test.csv` |

## Final topic labels

See `reports/HUMAN_VALIDATION_REPORT.md` §"Reconciled final topic labels"
for the full reconciled label set (both representations, both raters'
proposed labels shown alongside the reconciled label). Not duplicated here
to avoid a second source of truth for label text — that section is
authoritative for labels; this file is authoritative for numbers.

## Human validation

| | Metadata | Full text |
|---|---|---|
| Raters | 2 (independent, blinded) | 2 (independent, blinded) |
| Preference agreement | Unanimous (k=4) | Disagreed (Rater 1: k=4; Rater 2: k=5, k=3 runner-up) |
| Final k after reconciliation | 4 | 4 (documented disagreement, not majority vote) |
