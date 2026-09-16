# Human Validation Report

**Status: complete.** Two independent raters completed blinded evaluation of the metadata
k-candidates (k=2,3,4,5, model identity withheld) and the full-text final topics (k=8). All
numbers below are computed directly from the raw rater files in
`human_validation/Human_Result/` (verified programmatically; see
`src/human_validation_analysis.py` and its outputs `human_validation/metadata_human_*.csv`,
`human_validation/fulltext_human_*.csv`). Raw rater files are preserved unmodified in
`human_validation/Human_Result/`.

## Metadata k-selection: human evidence

| Blinded model | k | Combined mean coherence | Combined mean interpretability | Combined mean distinctiveness | Combined overall | Rater 1 preference | Rater 2 preference |
|---|---:|---:|---:|---:|---:|---|---|
| C | 2 | 3.50 | 3.75 | 3.50 | 3.58 | No | No |
| B | 3 | 4.33 | 4.17 | 4.00 | 4.17 | No | **Yes** |
| D | 4 | 4.00 | 3.88 | 3.75 | 3.88 | No | No |
| A | 5 | 4.20 | 3.90 | 3.80 | 3.97 | **Yes** | No |

Source: `human_validation/metadata_human_model_scores.csv`.

**Human evaluation supported the semantic interpretability of the candidate topic structures
but did not uniquely determine the preferred number of topics. Accordingly, human evaluation
was treated as complementary interpretive evidence rather than as the decisive criterion for
selecting k.** Rater 1 (`human_validation/metadata_human_overall_preferences.csv`) preferred
Model A (k=5): "provides the clearest and most interpretable overall representation... isolates
distinct areas... without leaving themes merged or creating redundant topics." Rater 2 preferred
Model B (k=3): "each internally coherent and clearly distinguishable... without the merging seen
in Model C's two-topic solution or the apparent over-splitting/redundancy seen in Model D... and
Model A." Model D (k=4, the quantitatively selected solution) was rated as interpretable by both
raters (combined overall 3.88/5) but was the first-choice preference of neither rater. **This
report does not claim human validation confirmed k=4** — see
`reports/METADATA_FINAL_K_VALIDATION.md` for how this evidence is combined with the
quantitative diagnostics.

Model-level questions (`human_validation/metadata_human_model_level_questions.csv`): both raters
flagged Model C (k=2) as merging distinct themes; Rater 1 rated Model D (k=4) as splitting one
theme unnecessarily (hallucinations/vulnerabilities); Rater 2 rated Model A (k=5) similarly,
noting its Topic 4 "overlaps heavily with Topics 1 and 3 and reads as a residual category."

### Intrusion tests (metadata only)

Rater 1 completed 2 of 14 intrusion items; Rater 2 completed all 14. Scored against the private
answer key (`human_validation/metadata_intrusion_test_answers.json.csv`, not available to the
raters at rating time): **Rater 1: 2/2 word-intrusion correct, 2/2 document-intrusion correct.
Rater 2: 14/14 word-intrusion correct, 14/14 document-intrusion correct.** This is a strong,
though partial (Rater 1 incomplete), positive validity signal — both raters could reliably
identify the deliberately inserted unrelated term/study, indicating the blinded topics carried
genuine, detectable semantic identity rather than being indistinguishable noise. Source:
`human_validation/metadata_human_intrusion_scored.csv`.

## Full-text (k=8) topics: human evidence

| Topic | Combined mean coherence | Combined mean interpretability | Combined mean distinctiveness | Combined overall |
|---|---:|---:|---:|---:|
| 0 | 4.50 | 4.50 | 4.00 | 4.33 |
| 1 | 4.00 | 4.00 | 4.50 | 4.17 |
| 2 | 3.50 | 3.50 | 4.00 | 3.67 |
| 3 | 4.50 | 4.00 | 4.50 | 4.33 |
| 4 | 3.50 | 3.50 | 2.50 | 3.17 |
| 5 | 5.00 | 5.00 | 4.50 | 4.83 |
| 6 | 4.00 | 4.00 | 3.50 | 3.83 |
| 7 | 3.50 | 3.50 | 3.50 | 3.50 |

**Combined across all 8 topics and 2 raters: coherence ≈ 4.06/5, interpretability ≈ 4.00/5,
distinctiveness ≈ 3.88/5.** Source: `human_validation/fulltext_human_ratings_per_topic.csv`,
`human_validation/fulltext_human_validation_summary.json`.

**Human evaluation provided generally positive evidence for topic coherence and
interpretability but weaker evidence for complete topic distinctiveness. Several fine-grained
topics were perceived as conceptually adjacent, indicating that the eight-topic solution should
be interpreted as a probabilistic thematic decomposition rather than eight mutually exclusive
conceptual categories.** Topic 5 (programming education) was the clearest topic to both raters
(combined overall 4.83/5). Topic 4 (LLM coding proficiency/programming tasks) was the weakest
(3.17/5; Rater 1: "General Coding Proficiency"; Rater 2 flagged it as broad/heterogeneous,
overlapping education/quality topics). Both raters' model-level notes
(`human_validation/Human_Result/Full_Text/model_level_questions_rater{1,2}*.csv`) independently
identified overlap between the security/quality topics (2 and 6) and, to a lesser extent, the
practitioner/developer-experience topics (0, 4, 7) — consistent with the quantitative cross-k
persistence finding that these were the only two "moderately" (rather than "highly") persistent
topics (`reports/FULLTEXT_FINAL_K_VALIDATION.md`).

This is neither a failed validation nor proof of eight perfectly discrete conceptual
categories: it is **partial human support for coherent broad themes, with limited
distinctiveness among several fine-grained topics**.

## Topic labels

Both raters independently proposed labels for every topic before any AI-drafted label was
shown to them (blinded packets in `human_validation/metadata_candidate_blinded/` and
`human_validation/fulltext_final_blinded/`). Raw labels for every candidate model are in
`human_validation/metadata_human_ratings_per_topic.csv` and
`human_validation/fulltext_human_ratings_raw.csv`. Per-topic labels for the two **final**
models (metadata k=4, full text k=8) are consolidated in
`human_validation/FINAL_TOPIC_LABELS.csv`. **No formal reconciliation session between the two
raters has occurred**; the `Final_Reconciled_Label` column is therefore marked "Pending
researcher reconciliation" throughout, not populated with an invented consensus.

## What this does and does not establish

- It establishes that both candidate/final topic solutions are broadly human-interpretable
  (mean ratings mostly 3.5–5.0/5 across both analyses) and that raters can reliably distinguish
  genuine topic content from inserted noise (intrusion tests).
- It does **not** establish a single human-preferred k for the metadata representation — the
  two raters disagreed (k=5 vs. k=3), and k=4 was neither rater's first choice.
- It does **not** establish that all 8 full-text topics are mutually exclusive, sharply bounded
  categories — several (2, 4, 6, 7) show weaker distinctiveness and documented conceptual
  overlap in both raters' free-text notes.
