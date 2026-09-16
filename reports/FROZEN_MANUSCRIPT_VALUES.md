# Frozen Manuscript Values

**This is the single authoritative source for the subsequent RQ5/methodology rewrite. Do not
pull numbers from any other document once this file exists.** Every value cites its repository
source path. This is a values freeze only — RQ5 prose has not been rewritten in this task.

## Corpus

- Final N = **66** primary studies. 5 secondary studies documented and excluded from every LDA
  stage. Source: `corpus/primary_studies_manifest.csv`, `corpus/corpus_audit.md`.

## Metadata analysis (primary RQ5 representation)

| Value | Result | Source |
|---|---|---|
| Representation | Title + Abstract + Author Keywords (Title+Abstract only for 24/66 studies) | `data/metadata_representation.csv` |
| Dictionary | no_below=5, no_above=0.50, vocab=397 | `results/metadata/stage1_selected_config.json` |
| Training budget | passes=30, iterations=800, alpha=eta=auto | `results/metadata/stage2_frozen_training_config.json` |
| Final k | **4** | `results/metadata/k_selection_decision.json` |
| Structural-medoid seed | **14** (mean similarity 0.690) | `results/metadata/representative_seed_k04.json` |
| Mean C_v at k=4 | 0.4035 | `results/metadata/definitive_ksweep_runs.csv` |
| Mean C_NPMI | -0.1042 | `results/metadata/definitive_ksweep_runs.csv` |
| Mean cross-seed JS stability | 0.6610 | `results/metadata/seed_stability_by_k.csv` |
| Mean topic diversity | 0.8425 | `results/metadata/definitive_ksweep_runs.csv` |
| 80% subsampling topic similarity (JS) | 0.5858 | `results/metadata/subsampling_80pct_100reps.csv` |
| 80% subsampling ARI | 0.1287 | `results/metadata/subsampling_80pct_100reps.csv` |
| Training-effort sensitivity | JS=0.9573, dominant agreement=98.5% | `results/metadata/training_effort_sensitivity.json` |

## Metadata k-selection rationale (factual summary)

k=2 and k=3 both show a "mega-topic" (71-73% of the corpus in one topic) and are judged
insufficient. k=4 has the most balanced dominant-topic split of any candidate (21/1/21/23) and
no mega-topic. k=5 does not improve on k=4 by any quantitative measure and re-introduces a
thin topic. k=4 is the most defensible quantitative-parsimony compromise. Full detail:
`reports/METADATA_FINAL_K_VALIDATION.md`.

## Metadata human-validation result (factual summary)

Two independent raters, blinded to model identity and k, rated candidates k=2,3,4,5.
**They did not agree on a preferred k** (Rater 1 → k=5; Rater 2 → k=3). Combined mean overall
ratings: k=2: 3.58/5, k=3: 4.17/5 (highest), k=4: 3.88/5, k=5: 3.97/5. k=4 was rated
interpretable by both raters but was neither rater's first choice. Intrusion tests: 16/16
correct across both raters (2/2 for Rater 1, who completed only 2 of 14 items; 14/14 for
Rater 2). **Human validation did not confirm k=4** — it is used as complementary
interpretability evidence, not a decisive criterion. Full detail:
`reports/HUMAN_VALIDATION_REPORT.md`, `reports/METADATA_FINAL_K_VALIDATION.md`.

## Final metadata topic labels

Not yet reconciled between raters — see `human_validation/FINAL_TOPIC_LABELS.csv`
(`Final_Reconciled_Label` = "Pending researcher reconciliation" for all 4 topics). Raters'
independent labels are recorded in the same file for reference.

## Full-text analysis (secondary representation-sensitivity analysis)

| Value | Result | Source |
|---|---|---|
| Representation | Cleaned, section-restricted full text (Intro-Conclusion) | `data/fulltext_representation_manifest.csv` |
| Dictionary | no_below=4, no_above=0.75, vocab=2626 | `results/fulltext/stage1_selected_config.json` |
| Training budget | passes=30, iterations=800, alpha=eta=auto | `results/fulltext/stage2_frozen_training_config.json` |
| Final k | **8** | `results/fulltext/k_selection_decision.json` |
| Structural-medoid seed | **2** (mean similarity 0.554) | `results/fulltext/representative_seed_k08.json` |
| Mean C_v at k=8 | 0.3958 | `results/fulltext/definitive_ksweep_runs.csv` |
| Mean C_NPMI | -0.0432 | `results/fulltext/definitive_ksweep_runs.csv` |
| Mean cross-seed JS stability | 0.5432 | `results/fulltext/seed_stability_by_k.csv` |
| Mean topic diversity | 0.7669 | `results/fulltext/definitive_ksweep_runs.csv` |
| 80% subsampling topic similarity (JS) | 0.5151 | `results/fulltext/subsampling_80pct_100reps.csv` |
| 80% subsampling ARI | 0.2192 | `results/fulltext/subsampling_80pct_100reps.csv` |
| Training-effort sensitivity | JS=0.9023, dominant agreement=93.9% | `results/fulltext/training_effort_sensitivity.json` |

## Full-text cross-k persistence (factual summary)

Near-equivalent candidate region: k∈{8,9,12,13,14,15}. Cross-k Hungarian alignment of k=8's
topics against each higher k: **6/8 topics highly persistent** (mean JS similarity ≥0.55
across k=9-15), **2/8 moderately persistent** (T2 security-benchmark, T4
exercises/training; 0.40-0.55), none unstable. Higher-k topics predominantly subdivide rather
than replace k=8's structure. **k=8 is described as "the most parsimonious representation of a
broader region of quantitatively comparable and thematically persistent solutions," never as
"optimal" or "best."** Full detail: `reports/FULLTEXT_FINAL_K_VALIDATION.md`,
`results/fulltext/cross_k_topic_persistence.csv`.

## Full-text human validation (factual summary)

Two independent raters, blinded to AI-drafted labels, rated all 8 final topics. Combined:
**mean coherence ≈4.06/5, mean interpretability ≈4.00/5, mean distinctiveness ≈3.88/5.**
Strongest topic: T5 (programming education, 4.83/5). Weakest: T4 (programming
exercises/training, 3.17/5). The two topics with only moderate quantitative persistence (T2,
T4) also show the weakest human-rated distinctiveness — quantitative and human evidence agree
on which topics are least well-resolved. **This should be reported as generally positive
coherence/interpretability evidence with weaker distinctiveness evidence for several
fine-grained topics — not as failed validation, and not as proof of 8 mutually exclusive
categories.** Full detail: `reports/HUMAN_VALIDATION_REPORT.md`.

## Full-text length sensitivity (factual summary)

Document length varies ~11.7x across the 66 full texts. Weak-to-moderate association between
length and topic-assignment confidence: **r=0.249, p=0.043**. A length-balanced sensitivity
model (per-document token cap) agrees with the full model on only **33.3% of dominant-topic
assignments** (JS similarity 0.446 to the full model) — materially lower than the
training-effort/dictionary robustness checks. **This is a genuine limitation of the full-text
analysis and is not hidden or softened.** Source: `results/fulltext/length_diagnostics.json`,
`results/fulltext/length_balanced_sensitivity.json`.

## Cross-representation comparison

k_A=4, k_B=8 (not forced to agree). **ARI=0.191, NMI=0.298** on dominant-topic assignment
across all 66 shared studies — described as **modest/partial correspondence**, never as strong
convergence. All 4 metadata topics have some full-text counterpart (strongest: education↔
education JS=0.233; API-hallucination↔API-hallucination JS=0.207); 4 full-text topics have no
metadata counterpart. Differences **may reflect** representation content, differing k,
document-length sensitivity (full text only), or stochastic variation — this analysis does not
and cannot statistically decompose which factor dominates. Full text is treated as a
**secondary representation-sensitivity analysis**, not an equally-weighted alternative to the
metadata analysis, based on the robustness asymmetry above (not on topic count). Source:
`results/cross_representation/topic_alignment.json`,
`results/cross_representation/dominant_topic_contingency_matrix.csv`.

## Limitations (factual, for the manuscript limitations paragraph)

1. Document-level topic assignment is comparatively fragile under 80% subsampling for both
   representations (ARI 0.13 metadata / 0.22 full text), even though topic-word structure is
   more stable (JS 0.59 / 0.52).
2. Full-text topic structure shows material sensitivity to document length (see above) — not
   present in the metadata model (documents are far more length-homogeneous by construction).
3. Coherence values (C_v≈0.40 both representations) are descriptive only; no external benchmark
   is invoked, and coherence/stability/any visualization is never treated as independent
   validation.
4. Metadata k=4 is a quantitative-parsimony compromise not confirmed by either individual human
   rater (who disagreed with each other); full-text k=8 is the parsimonious representative of a
   broader persistent region, not a uniquely optimal solution.
5. Final topic labels are not yet reconciled between the two human raters
   (`human_validation/FINAL_TOPIC_LABELS.csv`).
6. This LDA analysis is statistically independent of the manual RQ1-RQ4 classification; it was
   not informed by RQ1-RQ4 at any stage before both models were frozen, and does not validate
   that classification.
