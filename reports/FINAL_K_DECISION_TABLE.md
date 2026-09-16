# Final k Decision Table

**Status: FINAL.** Quantitative columns and human-evidence columns are both complete
(`reports/HUMAN_VALIDATION_REPORT.md`) and traceable to generated files.

| Decision | Metadata | Full Text |
|---|---|---|
| Final k | **4 (FINAL)** | **8 (FINAL)** |
| Evidence supporting k | k=2,3 rejected for mega-topic under-differentiation (71–73% of corpus in one topic); k=4 has the most even dominant-topic split of all candidates (21/1/21/23); k=5 does not improve stability, diversity, or thin-topic count over k=4. See `reports/METADATA_FINAL_K_VALIDATION.md`. | k=8 selected by parsimony from the near-equivalent region {8,9,12,13,14,15}; cross-k persistence analysis shows k=8's topics are 75% highly persistent / 25% moderately persistent (none unstable) across that entire region, with higher-k topics predominantly subdividing rather than replacing k=8's structure. See `reports/FULLTEXT_FINAL_K_VALIDATION.md`. |
| Structural-medoid seed | 14 (mean similarity 0.690) | 2 (mean similarity 0.554) |
| Human coherence (combined mean) | 3.88/5 for the k=4 solution (range 3.58–4.17 across candidates k=2,3,4,5) — **not the raters' individually preferred k** | 4.06/5 (combined across all 8 topics) |
| Human interpretability (combined mean) | 3.88/5 for k=4 | 4.00/5 |
| Human distinctiveness (combined mean) | 3.75/5 for k=4 | 3.88/5 |
| Human k preference | **Raters disagreed**: Rater 1→k=5, Rater 2→k=3; neither chose k=4 | N/A (single final model rated, not a k-candidate comparison) |
| Cross-seed stability (mean JS) | 0.661 | 0.543 |
| Subsampling topic stability (mean JS, 100×80%) | 0.586 | 0.515 |
| Subsampling dominant-assignment ARI | 0.129 | 0.219 |
| Major limitation | One thin topic (T1, "Requirements-Driven Prompting and Code Generation", 1 dominant study) — human raters rated it interpretable (4/5 coherence both raters), so it is not treated as a modeling artifact. | Non-trivial document-length sensitivity (length-balanced sensitivity model: only 33% dominant-topic agreement with the full model); 2 of 8 topics (T2 "Security and Safety-Critical Code Generation Benchmarks", T4 "LLM Coding Proficiency and Programming Tasks") only moderately persistent across the candidate k region and lowest human-rated distinctiveness. |
| Final reconciled topic labels | `reports/TOPIC_LABEL_RECONCILIATION.md` (4 topics) | `reports/TOPIC_LABEL_RECONCILIATION.md` (8 topics) |
| Role in manuscript | **Primary** | **Sensitivity** (representation-sensitivity check on the primary metadata result) |

## Basis for the Primary / Sensitivity role assignment

Based on: metadata documents are structurally more length-homogeneous (titles+abstracts vary
far less in length than full papers); the metadata model has higher cross-seed stability
(0.661 vs. 0.543) and higher topic diversity (0.838 vs. 0.767); and only the full-text model
shows material sensitivity to document length. It is **not** based on topic count (full text
finding more topics is an expected consequence of its larger k, not evidence of superior
validity) and **not** based on which representation "agrees more" with the manual RQ1–RQ4
synthesis (which was not consulted). Completed human validation did not surface a reason to
reconsider this assignment: the metadata model's flagged thin topic (T1) was rated interpretable
by both raters, and the full-text model's two weakest-distinctiveness topics (T2, T4) are
exactly the two topics the independent cross-k persistence analysis had already flagged as only
moderately (not highly) persistent — the quantitative and human evidence converge rather than
conflict.
