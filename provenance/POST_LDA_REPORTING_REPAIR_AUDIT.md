# Post-LDA Reporting Repair Audit

Scope: a reporting/comparison repair only. **No LDA model was refitted with
different settings, no k was changed, no seed was changed, no preprocessing
or dictionary was changed, no prior was changed, no final topic label was
changed, and no human rating was altered.** Both final models (metadata
k=4/seed=1212; full-text k=4/seed=505) were deterministically reconstructed
from their exact frozen configuration solely to obtain their already-fixed
topic-word/document-topic distributions for the corrected cross-
representation computation — verified to reproduce the frozen dominant-study
counts `[22,16,15,13]` and `[17,8,16,25]` exactly before any new number was
used.

| # | Issue | Original treatment | Correction made | Files changed | Numerical results changed? | Reason |
|---|---|---|---|---|---|---|
| 1 | Union-vocabulary topic-word comparison | Compared topic-word vectors zero-padded onto the *union* of both vocabularies; near-zero JS/cosine attributed to "probability dilution" | Recomputed on the vocabulary *intersection* (19 shared terms); reports per-topic coverage before renormalization; renormalizes before computing JS/cosine/top-10/top-20 Jaccard; "dilution" framing withdrawn in favour of an explicit low-coverage caution | `CROSS_REPRESENTATION_REPORT.md`, `FROZEN_MANUSCRIPT_VALUES.md`, new: `src/stage7_cross_representation_v2.py`, `results/cross_representation/intersection_analysis.csv` | **Yes** — new values (JS 0.45-0.56, cosine 0.46-0.82, top-10 Jaccard 0.25-0.67) supplement, and are now primary over, the old union-based values (JS 0.01-0.03), which are preserved as superseded, not deleted | Union-based zero-padding onto a vocabulary ~7-8x larger than metadata's own is a different (and less informative) measurement than intersection-based comparison; the old explanation described the method's own artifact as if it were evidence about the topics |
| 2 | "Clearly non-random" ARI/NMI claim | Asserted from ARI>0/NMI>0 alone | Ran a 10,000-repetition permutation test (fixed seed=42, full-text labels permuted against fixed metadata labels); chance-exceeding claim now made only with this backing (p<0.0001 for both) | `CROSS_REPRESENTATION_REPORT.md`, `FINAL_LDA_REPORT.md`, `MANUSCRIPT_TEXT.md`, `FROZEN_MANUSCRIPT_VALUES.md`, new: `results/cross_representation/permutation_test.csv` | **Yes (addition)** — ARI/NMI values themselves unchanged (reverified identical); new permutation p-values added | Positive ARI/NMI alone doesn't establish the agreement exceeds chance; the claim needed either downgrading to "modest" or a real test, and the test was performed |
| 3 | "Pre-registered" terminology | Used in `MANUSCRIPT_TEXT.md`, `FINAL_LDA_REPORT.md` to describe the internal protocol | Replaced with "pre-specified" / "fixed before model fitting" in all manuscript-facing text | `MANUSCRIPT_TEXT.md`, `FINAL_LDA_REPORT.md` | No | Protocol was frozen internally before results were seen, but was never externally registered; "pre-registered" implies the latter |
| 4 | Human-blinding description | Stated raters had "no access to k" without qualifying that topic count was inherently visible | Rewritten: raters blinded to model identity, seed, configuration, quantitative metrics, and the numerical k label — but the number of displayed topics was necessarily observable, since complete models were shown | `HUMAN_VALIDATION_REPORT.md`, `FINAL_LDA_REPORT.md`, `MANUSCRIPT_TEXT.md` | No | Precision: the previous wording was misleading, not false, but did not distinguish "the k label was hidden" from "topic count was unobservable" |
| 5 | Rater independence/externality wording | "Two raters... independently scored" without flagging that one rater is a project author | Added explicit statement that Rater 2 is a project author; "independent" now explicitly scoped to mean independence *between* raters (blinded, no shared knowledge before submission), not externality; confirmed no file called them "external evaluators" | `HUMAN_VALIDATION_REPORT.md`, `MANUSCRIPT_TEXT.md`, `FINAL_LDA_REPORT.md` | No | Avoids implying an external-validation study design that wasn't the actual design |
| 6 | Dictionary-sensitivity framing | Already reported as a limitation (verified, not previously overstated as robustness) | Left substantively as-is; training-effort wording nearby corrected (#7) | `ROBUSTNESS_REPORT.md` (wording adjacent to dictionary section only) | No | On review, dictionary-sensitivity language already met the bar; no change needed there specifically |
| 7 | "5-25x" training-effort description | Derived a single fold-increase by multiplying passes×iterations (20×200=4,000 vs. 100×2,000=200,000 -> ~50x, or informally described as "5-25x" depending on which factor) | Replaced with the precise, non-multiplied description: "100 passes and 2,000 iterations vs. 20 passes and 200 iterations — five times as many passes and ten times as many iterations" | `ROBUSTNESS_REPORT.md`, `FINAL_LDA_REPORT.md`, `MANUSCRIPT_TEXT.md` | No | The original phrasing invited a misleading single multiplier; passes and iterations were multiplied separately as instructed |
| 8 | Pareto/finalist-reduction framing | Implied k={2,3,4,5} came from Pareto analysis narrowing the candidates | Explicitly reports that 15/19 (metadata) and 19/19 (full text) k values were Pareto-optimal — Pareto alone did not isolate a small set — and that the *separate*, pre-specified stability-ranked cutoff produced the four finalists, with the disclosed implication that this mechanically favours smaller k | `METADATA_LDA_REPORT.md`, `FULLTEXT_LDA_REPORT.md`, `FINAL_LDA_REPORT.md`, `MANUSCRIPT_TEXT.md` | No | Accuracy: conflating "Pareto-optimal" with "the four finalists" overstated what the Pareto step alone accomplished |
| 9 | Causal/absolute cross-representation language | "Genuine split," "full text reveals," "what full methodological text reveals" | Replaced with "distributed correspondence" / "partial one-to-many correspondence" and "consistent with representation-dependent thematic granularity"; removed implication that either representation captures more complete or more correct structure | `CROSS_REPRESENTATION_REPORT.md`, `FINAL_LDA_REPORT.md`, `MANUSCRIPT_TEXT.md` | No | The data support a descriptive pattern, not a demonstrated causal mechanism |
| 10 | "k=4 was clearly superior" (full text) | Framing leaned toward k=4 as the stronger choice without qualification | Reframed throughout as "k=4 was retained as the more conservative multi-criterion solution, not because it was demonstrated clearly superior to k=5"; k=5's specific advantages (raw C_v, subsampling ARI/NMI, Rater 2's preference, unique competitive-programming topic) restated alongside | `HUMAN_VALIDATION_REPORT.md`, `FULLTEXT_LDA_REPORT.md`, `FINAL_LDA_REPORT.md`, `MANUSCRIPT_TEXT.md` | No | The original text already avoided an explicit "superior" claim but the framing needed to be made unambiguous per instruction |
| 11 | Over-claiming validation language | Scan found no instances of "human validation proved," "confirms the true topic structure," or similar in the report set | No changes required | — | No | Existing text already used "supports," "evidence of interpretability," "complementary" — verified compliant on search |
| 12 | Extraction artifacts ("a.", "def", "p4") | Already documented as a limitation, not retroactively cleaned | Left as documented; explicitly re-stated that no retroactive cleaning/refit was performed and no claim is made about their material effect absent a test | `MANUSCRIPT_TEXT.md` (limitations, restated) | No | Matches instruction: document, don't fix now, don't overclaim effect |

## Verification performed

One transcription error was caught and corrected during this verification
pass: `CROSS_REPRESENTATION_REPORT.md`'s permutation-test table initially
reported estimated-looking placeholder values for the permutation mean/SD
(ARI: -0.0026 (0.019); NMI: 0.0847 (0.023)) instead of reading them from
`results/cross_representation/permutation_test.csv`. Corrected to the
actual computed values: ARI permutation mean -0.0002 (SD 0.0214), NMI
permutation mean 0.0563 (SD 0.0262). The observed ARI/NMI values and both
p-values (<0.0001) were already correct and unaffected. This is flagged
explicitly rather than silently fixed, per the audit-trail requirement.

No other numeric discrepancies were found:

- Reconstructed both frozen final models from their exact saved
  configuration and confirmed dominant-study counts match the frozen
  record exactly: metadata `[22,16,15,13]`, full text `[17,8,16,25]`.
- Recomputed document-level ARI/NMI directly from the reconstructed
  models: 0.2384/0.2738 — matches the previously reported value exactly.
- Cross-checked C_v, C_NPMI, stability, and dominant-study counts for both
  representations against `FROZEN_MANUSCRIPT_VALUES.md` in every report
  file that cites them (`METADATA_LDA_REPORT.md`, `FULLTEXT_LDA_REPORT.md`,
  `ROBUSTNESS_REPORT.md`) — all consistent, no transcription errors found.
- Project-wide search for `pre-registered`, `preregistered`, `clearly
  non-random`, `probability dilution`, `reveals themes`, `true thematic
  structure`, `human validation confirmed`, `external raters`, `no access
  to k`, `5-25x` in `reports/` — remaining occurrences are either
  intentional (explaining what was withdrawn/corrected) or in
  `reports/PRE_EXECUTION_ANALYSIS_PLAN.md`, the original internal protocol
  document, which was intentionally left unedited (see below).

## Scope decision: `PRE_EXECUTION_ANALYSIS_PLAN.md` not edited

This file uses "pre-registered" twice, in its own internal sense (grids and
checks fixed before results were seen). It is the frozen planning artifact
the user approved at the start of the project, not manuscript-facing
reporting text, and it is not listed among the files this repair task
named for editing (items 15-20 of the repair instructions name
`CROSS_REPRESENTATION_REPORT.md`, `ROBUSTNESS_REPORT.md`,
`HUMAN_VALIDATION_REPORT.md`, `FINAL_LDA_REPORT.md`, `MANUSCRIPT_TEXT.md`,
and `FROZEN_MANUSCRIPT_VALUES.md` specifically). Left unmodified; flagged
here for visibility rather than silently skipped.

## Files changed

`reports/CROSS_REPRESENTATION_REPORT.md` (full rewrite),
`reports/FROZEN_MANUSCRIPT_VALUES.md` (cross-representation section
extended),
`reports/ROBUSTNESS_REPORT.md` (training-effort wording),
`reports/HUMAN_VALIDATION_REPORT.md` (blinding/independence wording,
full-text decision framing),
`reports/METADATA_LDA_REPORT.md` (Pareto framing),
`reports/FULLTEXT_LDA_REPORT.md` (Pareto framing, decision framing),
`reports/FINAL_LDA_REPORT.md` (full rewrite),
`reports/MANUSCRIPT_TEXT.md` (full rewrite).

New files: `src/stage7_cross_representation_v2.py`,
`results/cross_representation/intersection_analysis.csv`,
`results/cross_representation/permutation_test.csv`,
`results/cross_representation/contingency_matrix.csv`,
`results/cross_representation/comparison_SUPERSEDED_union_vocab.md` (audit
copy of the original output, explicitly marked superseded, not deleted).

Not changed: `reports/PRE_EXECUTION_ANALYSIS_PLAN.md` (see scope decision
above); any file under `results/{metadata,fulltext}/` (k-sweep, subsampling,
training-effort, dictionary-sensitivity, length-sensitivity outputs — all
verified against the frozen record, none required correction);
`human_validation/Rater1.md`, `human_validation/Rater2.md` (ratings
untouched).
