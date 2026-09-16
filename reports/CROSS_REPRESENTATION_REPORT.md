# Cross-Representation Comparison — Analysis A (Metadata) vs. Analysis B (Full Text)

Computed only after both representations independently froze their final models (protocol
Section 25). Both analyses cover the same 66 primary studies.

**Interpretive note (repair task Parts 10–11):** the observations below describe *statistical
correspondence*, not causal mechanism. Differences between the two representations' topic
structures may reflect their different text content, but they may equally reflect the
different selected k (4 vs. 8), stochastic variation across model fits, or — for the full-text
model specifically — the document-length sensitivity documented in
`reports/ROBUSTNESS_REPORT.md` (a length-balanced sensitivity check agreed with the full
full-text model on only 33% of dominant-topic assignments). This analysis cannot statistically
decompose how much of the observed divergence is attributable to each of these factors, and
does not attempt to. Language below is deliberately hedged (“may reflect”, “is consistent
with”, “partial correspondence”) rather than causal (“full text reveals…”, “these themes
require full text…”).

## Topic counts

k_A (metadata) = 4 [FINAL — see `reports/METADATA_FINAL_K_VALIDATION.md`], k_B (full text) = 8
[FINAL — see `reports/FULLTEXT_FINAL_K_VALIDATION.md`, which also shows this structure is
persistent across the k=8–15 near-equivalent region]. Both are corroborated by completed
blinded human validation (`reports/HUMAN_VALIDATION_REPORT.md`; for metadata, corroboration is
partial — the two raters preferred different k values from each other and from k=4). These
were **not** forced to match — the
protocol explicitly permits and anticipates k_A ≠ k_B, and treats disagreement as a legitimate
reflection of differing thematic granularity (protocol Section 26), not a modeling failure —
though, per the note above, part of this difference could also stem from the two
representations independently selecting different k under the same selection procedure, not
solely from a difference in the underlying content.

## Topic alignment

Rectangular Hungarian matching on topic-word distributions projected onto a shared vocabulary
(since k_A ≠ k_B): every metadata topic matched to a full-text topic (0 unmatched on the
metadata side); 4 of the 8 full-text topics had no metadata counterpart (unmatched). Full
alignment detail, including per-pair JS similarity/cosine/top-20 Jaccard:
`results/cross_representation/topic_alignment.json`.

Matched pairs (rectangular Hungarian; JS similarity/cosine/top-20 Jaccard from
`results/cross_representation/topic_alignment.json`):

| Metadata topic | Full-text topic | JS similarity | Cosine | Top-20 Jaccard |
|---|---|---:|---:|---:|
| T0 (hallucination benchmarking / correctness verification) | T6 (code vulnerability, determinism & fix quality) | 0.182 | 0.545 | 0.053 |
| T1 (requirements-driven / safety-critical generation) | T2 (security-focused benchmark evaluation) | 0.175 | 0.353 | 0.081 |
| T2 (AI in programming education) | T5 (programming education, instruction & feedback) | 0.233 | 0.669 | 0.143 |
| T3 (API/dependency hallucination and mitigation) | T3 (API/dependency hallucination detection & mitigation) | 0.207 | 0.567 | 0.143 |

The strongest correspondence, on both JS similarity and cosine, is education↔education
(metadata T2 / full-text T5) and API-hallucination↔API-hallucination (metadata T3 / full-text
T3) — themes salient enough to be visible even from titles/abstracts/keywords. These "best"
matches are still only moderately similar in absolute terms (JS similarity 0.18–0.23, top-20
Jaccard ≤0.14), indicating **partial, not full, correspondence** between the two
representations' topics — consistent with the modest ARI/NMI below, not necessarily with a
substantive difference in the underlying themes each representation "sees."

Four full-text topics have **no metadata counterpart** under this k_A<k_B rectangular
matching: T0 (developer trust & community perception), T1 (package hallucination & malicious
dependency risk), T4 (programming exercises/training tasks), and T7 (bug patterns &
developer-reported issues). This pattern **is consistent with** these themes depending on
methodology-, results-, or discussion-level detail not present in titles/abstracts/keywords;
it is also consistent with these being among the topics introduced when full-text's k
(8) exceeds metadata's k (4) for reasons unrelated to content (a larger k mechanically permits
more distinct topics). The present analysis does not distinguish between these explanations.

## Dominant-topic assignment agreement

Adjusted Rand Index = 0.191, Normalized Mutual Information = 0.298 (both computed on the
dominant-topic label for all 66 shared studies; full contingency matrix at
`results/cross_representation/dominant_topic_contingency_matrix.csv`, figure at
`figures/comparison/14_dominant_topic_contingency.png`). This is a **modest** level of
agreement. Per protocol Section 26, such disagreement may partly reflect differing thematic
granularity between representations, but — per the interpretive note above — it may also
partly reflect the differing k, model stochasticity, and (for the full-text side) document-length
sensitivity. We do not interpret modest agreement as evidence that either representation's
model is unreliable, nor as evidence that one representation is more "correct" than the other.

## Interpretation

All four metadata topics have *some* full-text counterpart, with the clearest partial
correspondence for the **API/dependency hallucination mitigation** and **programming
education** themes — plausible candidates for "declared research focus" content visible even
in titles/abstracts (protocol Section 26), though this reading is not statistically confirmed
here. Full text additionally surfaces four themes with no metadata counterpart: **developer
trust/community perception**, **package hallucination/malicious dependency risk**,
**programming exercises and training tasks**, and **bug patterns/developer-reported issues**.
These *may* reflect content only available at the methodology/results/discussion level; they
*may* also partly reflect the larger k selected for full text and that representation's
documented sensitivity to document length. This pattern is consistent with, but should not be
described as confirming, the manual RQ1–RQ4 synthesis; any such comparison is exploratory and
reported separately in the final report's limitations section, never as validation.

## Recommended manuscript role of each representation (repair task Part 13)

Given the asymmetric robustness evidence already documented — metadata documents are far more
length-homogeneous by construction, the metadata model shows higher cross-seed stability
(0.66 vs. 0.54) and higher topic diversity (0.84 vs. 0.77), and the full-text model alone
shows material sensitivity to document length (`reports/ROBUSTNESS_REPORT.md`) — we recommend
presenting the **metadata LDA as the primary RQ5 analysis** and the **full-text LDA as a
secondary representation-sensitivity analysis**, used to assess whether a richer text
representation changes the recovered thematic structure, rather than presenting both as
equally definitive primary results. This recommendation is based on the quantitative
robustness asymmetry already established, not on which representation "found more themes" —
finding more themes at a larger k is an expected consequence of k, not evidence of superior
validity. Completed human validation did not surface a reason to reconsider this role
assignment (`reports/METADATA_FINAL_K_VALIDATION.md`, `reports/FULLTEXT_FINAL_K_VALIDATION.md`,
`reports/HUMAN_VALIDATION_REPORT.md`).
