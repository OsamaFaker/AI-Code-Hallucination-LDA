# Metadata Final k Validation

**Status: FINAL — k=4.** This report removes the previous ad hoc `k≥4` floor from the
automatic selection rule (see `protocol/protocol_amendments.md` for the full history of that
rule and its removal) and replaces it with (1) an objective, descriptive admissibility
assessment of every candidate k∈{2,3,4,5} using the **structural medoid** model at each k
(never a coherence-selected seed), and (2) completed blinded human rating
(`reports/HUMAN_VALIDATION_REPORT.md`). Nothing here re-imposes an arbitrary minimum k; the
reasoning below is candidate-by-candidate, and the human evidence is reported exactly as
collected, including its disagreement with the quantitative pick.

Quantitative source: `results/metadata/k2_k5_candidate_comparison.csv` (medoid-model-specific
metrics, not seed-averaged).

## Candidate-by-candidate evidence

| k | Medoid seed | Dominant-study counts per topic | Zero-dominance | <3-study topics | Stability (mean JS) | Diversity | C_v |
|---|---|---|---|---|---:|---:|---:|
| 2 | 16 | [18, 48] | 0 | 0 | 0.782 | 0.975 | 0.365 |
| 3 | 0 | [17, 47, 2] | 0 | 1 | 0.710 | 0.883 | 0.473 |
| 4 | 14 | [21, 1, 21, 23] | 0 | 1 | 0.661 | 0.838 | 0.422 |
| 5 | 6 | [13, 2, 18, 13, 20] | 0 | 1 | 0.622 | 0.820 | 0.422 |

### k=2: not sufficient

One topic absorbs 48/66 (73%) of studies; the other only 18/66 (27%). Stability and diversity
are the highest of any candidate, but this is a mechanical artifact of having only two
topics — with just two topics there is little room for either pairwise overlap (hence
"diversity" ≈0.98) or seed disagreement about which of two broad clusters a document falls
into (hence high stability). A topic that captures nearly three-quarters of the corpus is not
functioning as a distinguishing theme; it behaves as an undifferentiated "everything else"
bucket. **k=2 is judged insufficient to resolve meaningful thematic structure**, independent
of its favorable raw metric values.

### k=3: not sufficient

The dominant-topic split [17, 47, 2] shows the *same* mega-topic problem as k=2 (71% of the
corpus in one topic) while *additionally* introducing a thin topic (2 dominant studies). k=3
does not resolve k=2's core problem and adds a new one. **k=3 is judged insufficient.**

### k=4: currently best-supported by quantitative evidence

The dominant-topic split [21, 1, 21, 23] has no mega-topic — the three largest topics are
close in size (21, 21, 23; each ≈32–35% of the corpus), a materially more even and
informative split than k=2 or k=3. The one thin topic (1 dominant study; the
"requirements-driven/safety-critical code generation" topic, T1, prevalence 0.062) is a real
concern and is **not dismissed**: both human raters rated it interpretable (Rater 1: "Prompting
for Domain-Specific Requirements", coherence 4/5; Rater 2: "Code Generation Methods &
Requirements-Driven Prompting", coherence 4/5) — human evidence does not support treating it as
a modeling artifact to be dropped, though it remains the lowest-prevalence topic in the model.

### k=5: does not improve on k=4

The dominant-topic split [13, 2, 18, 13, 20] again contains a thin topic (2 dominant studies)
— k=5 does not resolve the thin-topic issue present at k=4, and both cross-seed stability
(0.622 vs. 0.661) and topic diversity (0.820 vs. 0.838) are lower than at k=4. Splitting into
a 5th topic does not appear to reveal additional stable structure by these metrics alone.
**k=5 is not currently preferred over k=4**, though this is re-checked against human ratings
below.

## Quantitative conclusion

Based on dominant-topic balance, cross-seed stability, and diversity alone, **k=4 is the
best-supported candidate among {2,3,4,5}** — not because of an imposed floor, but because k=2
and k=3 both exhibit a severe mega-topic under-differentiation failure mode that is judged
more serious than k=4/k=5's single thin topic, and k=5 does not improve on k=4 by any measured
criterion.

## Human evidence

Two independent raters completed blinded evaluation of all four candidates
(`reports/HUMAN_VALIDATION_REPORT.md` for full detail; raw files in
`human_validation/Human_Result/`). **The human evaluation did not uniquely select the same
topic count.** Rater 1 preferred Model A (k=5, combined overall rating 3.97/5). Rater 2
preferred Model B (k=3, combined overall rating 4.17/5, the highest of any candidate). Model D
(k=4) was rated interpretable by both raters (combined overall 3.88/5) but was the first
preference of neither. Intrusion tests (word/document) were answered correctly in 16/16
completed attempts across both raters, indicating raters could reliably distinguish genuine
topic content from inserted noise.

> Human evaluation supported the semantic interpretability of the candidate topic structures
> but did not uniquely determine the preferred number of topics. Accordingly, human evaluation
> was treated as complementary interpretive evidence rather than as the decisive criterion for
> selecting k.

## Final decision: k=4

Combining the quantitative and human evidence per protocol repair task Part 3 (quantitative
adequacy + stability + non-redundancy + human interpretability + parsimony — no new arbitrary
weighted score): k=2 and k=3 are excluded by the quantitative mega-topic evidence regardless of
Rater 2's preference for k=3 (Rater 2's own model-level notes independently flag Model C, k=2,
as merging distinguishable sub-themes, and Model B, k=3, was not evaluated by either rater
against the mega-topic diagnostic, which is a structural property invisible from topic content
alone). k=5 does not improve on k=4 by any quantitative measure, and Rater 2 independently
identified over-splitting/redundancy in Model A (k=5, "Topic 4 overlaps heavily with Topics 1
and 3 and reads as a residual category"). **k=4 is retained as the most defensible
quantitative–parsimony compromise, corroborated (not confirmed) by human evidence that finds
it interpretable, though it was neither human rater's individually preferred solution.**

> Human evaluation found all candidate solutions broadly interpretable but did not produce a
> single preferred topic count: one evaluator favored a five-topic solution and the other a
> three-topic solution. The four-topic solution nevertheless received generally positive
> topic-level ratings and remained the quantitatively preferred compromise because lower-k
> solutions were dominated by a single broad topic, whereas the five-topic solution added
> granularity without a clear improvement in the quantitative diagnostics. Accordingly, human
> evaluation was used as complementary evidence of semantic interpretability rather than as a
> decisive criterion for selecting k.

**Do not describe this as "human validation confirmed k=4."** It did not.
