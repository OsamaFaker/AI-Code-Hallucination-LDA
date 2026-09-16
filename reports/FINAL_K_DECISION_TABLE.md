# Final k Decision Table

Quantitative columns are complete and traceable to generated files. Human-evidence columns
are **pending** completion of the blinded rating materials in `human_validation/` (protocol
repair task Parts 2–3, 6, 8–9) and are marked accordingly — not fabricated here.

| Decision | Metadata | Full Text |
|---|---|---|
| Final k | **4 (provisional)** | **8 (provisional)** |
| Evidence supporting k | k=2,3 rejected for mega-topic under-differentiation (71–73% of corpus in one topic); k=4 has the most even dominant-topic split of all candidates (21/1/21/23); k=5 does not improve stability, diversity, or thin-topic count over k=4. See `reports/METADATA_FINAL_K_VALIDATION.md`. | k=8 selected by parsimony from the near-equivalent region {8,9,12,13,14,15}; cross-k persistence analysis shows k=8's topics are 75% highly persistent / 25% moderately persistent (none unstable) across that entire region, with higher-k topics predominantly subdividing rather than replacing k=8's structure. See `reports/FULLTEXT_FINAL_K_VALIDATION.md`. |
| Structural-medoid seed | 14 (mean similarity 0.690) | 2 (mean similarity 0.554) |
| Human coherence | *pending* — `human_validation/metadata_candidate_blinded/` | *pending* — `human_validation/fulltext_final_blinded/` |
| Human interpretability | *pending* | *pending* |
| Human distinctiveness | *pending* | *pending* |
| Cross-seed stability (mean JS) | 0.661 | 0.543 |
| Subsampling topic stability (mean JS, 100×80%) | 0.586 | 0.515 |
| Subsampling dominant-assignment ARI | 0.129 | 0.219 |
| Major limitation | One thin topic (T1, 1 dominant study; "requirements-driven/safety-critical generation") flagged for human/intrusion-test review — may be a genuine minority theme or a modeling artifact. | Non-trivial document-length sensitivity (length-balanced sensitivity model: only 33% dominant-topic agreement with the full model); 2 of 8 topics (T2, T4) only moderately persistent across the candidate k region. |
| Role in manuscript | **Primary** | **Sensitivity** (representation-sensitivity check on the primary metadata result) |

## Basis for the Primary / Sensitivity role assignment

This is a quantitative, pre-human-validation recommendation (protocol repair task Part 13),
based on: metadata documents are structurally more length-homogeneous (titles+abstracts vary
far less in length than full papers); the metadata model has higher cross-seed stability
(0.661 vs. 0.543) and higher topic diversity (0.838 vs. 0.767); and only the full-text model
shows material sensitivity to document length. It is **not** based on topic count (full text
finding more topics is an expected consequence of its larger k, not evidence of superior
validity) and **not** based on which representation "agrees more" with the manual RQ1–RQ4
synthesis (which was not consulted). This role assignment should be revisited if human
validation surfaces reasons to reconsider it (e.g., if metadata's flagged thin topic is judged
incoherent by raters).
