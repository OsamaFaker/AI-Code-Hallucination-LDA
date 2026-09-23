# Final LDA Report

Top-level synthesis. Full detail in `METADATA_LDA_REPORT.md`,
`FULLTEXT_LDA_REPORT.md`, `ROBUSTNESS_REPORT.md`,
`HUMAN_VALIDATION_REPORT.md`, `CROSS_REPRESENTATION_REPORT.md`, and
`FROZEN_MANUSCRIPT_VALUES.md` (the authoritative numbers table).

## What was done

Two fully independent LDA analyses of the same 66 primary studies —
metadata (title+abstract+keywords) and full text — each with its own
preprocessing, dictionary selection, priors, training budget, and
definitive k=2-20 sweep (20 seeds each), following a staged analysis
protocol whose parameter grids, seed lists, model-selection criteria, and
robustness procedures were fixed before the definitive topic-number search
(`reports/PRE_EXECUTION_ANALYSIS_PLAN.md`). Every threshold used for model
selection (dictionary stable-region rule, bigram/domain-term retention
rule, convergence rule, prior-comparability rule, Pareto reduction rule)
was fixed before any k-sweep result was observed, and none were changed
afterward.

## Outcome

Both representations independently landed on final finalist sets of
k∈{2,3,4,5} — but this reduction came from a pre-specified
stability-ranked cutoff applied *after* Pareto filtering, not from Pareto
dominance alone: 15/19 metadata k values and all 19/19 full-text k values
were themselves Pareto-optimal (see `METADATA_LDA_REPORT.md` §2,
`FULLTEXT_LDA_REPORT.md` §2). Because cross-seed stability generally
decreases with topic count, the stability-ranked cutoff mechanically favours
smaller k among the finalists presented to raters — a property of the
pre-specified rule, disclosed here rather than left implicit. Both
representations were resolved to **k=4** — but by different evidentiary
paths, honestly reported:

- **Metadata**: two raters, scoring independently and blind to model
  identity/configuration/metrics, unanimously preferred k=4, consistent
  with its quantitative standing (lowest redundancy among the finalists,
  zero thin/zero-dominance topics, best topic-size balance).
- **Full text**: the two raters *disagreed* (Rater 1: k=4; Rater 2: k=5,
  with k=3 as a parsimonious runner-up). k=4 was **retained as the more
  conservative multi-criterion solution, not because it was demonstrated
  clearly superior to k=5** — k=5 remained a credible alternative, with
  higher raw coherence, stronger subsampling ARI/NMI, and a highly-specific
  competitive-programming topic absent at k=4. k=4 was preferred for its
  lowest redundancy among the disputed finalists, its markedly stronger
  training-effort robustness, and its perfect thin-topic safety under
  subsampling (k=5 showed fragility in 7/100 resamples), combined with
  Rater 1's endorsement and Rater 2's explicit non-rejection of k=4 as a
  reasonable model (positioned as a middle ground, not a poor one). Full
  reconciliation: `FULLTEXT_LDA_REPORT.md`, `HUMAN_VALIDATION_REPORT.md`.

That both representations land on the same k is a **post-hoc observation
from two independently-run pipelines**, not a designed outcome — nothing in
either pipeline constrained k to match the other (plan §1). It should be
read as one data point of convergence, not proof of a single "true" k.

## Cross-representation relationship

Document-level agreement between the two final models is **modest**
(ARI=0.238, NMI=0.274). A 10,000-repetition permutation test (fixed seed,
full-text labels permuted against fixed metadata labels) found both
observed values exceed all 10,000 permuted values (empirical p<0.0001 for
each) — this is the evidence for any claim that the agreement exceeds
chance; the claim is not made from the positive ARI value alone. Word-level
topic-word comparison, corrected to use the two representations' shared
vocabulary (19 terms; 9.1% of metadata's 208-term vocabulary, 1.3% of
full-text's 1,503-term vocabulary), shows each matched topic pair drawing
only 2-10% of its probability mass from that shared vocabulary — low
coverage that warrants cautious interpretation of the resulting
similarity figures (`CROSS_REPRESENTATION_REPORT.md` §3).

Two of the four metadata topics (hallucination/mitigation; education/
feedback) correspond strongly to a single full-text topic each (77% and
56% study concentration in the dominant-topic contingency matrix,
respectively); the other two (developer trust; correctness/testing) show a
**distributed, partial one-to-many correspondence** across multiple
full-text topics rather than concentration in one. This pattern is
**consistent with representation-dependent thematic granularity** —
differences may reflect document representation, independently selected
vocabularies of very different size, stochastic model variation, and
differences in how themes are lexically expressed in short metadata versus
substantive full text. This is not stated as a proven causal explanation,
and neither representation is described as more complete or more correct
than the other. Full detail: `CROSS_REPRESENTATION_REPORT.md`.

## Robustness posture (both final models)

Neither final model is presented as unconditionally robust. Both show
strong agreement under a substantially increased training budget (100
passes/2,000 iterations vs. the frozen 20 passes/200 iterations — five
times the passes, ten times the iterations) and no zero-dominance or thin
topics at the full-corpus fit. Both show only moderate topic-word
robustness (JS 0.52-0.57) and **substantially more sensitive**
document-assignment robustness (ARI 0.15-0.28) to single-step dictionary
threshold changes — kept as a visible limitation, not downplayed — and to
20% document removal (ARI≈0.80 under subsampling: substantial but
incomplete agreement, not near-perfect). Full text additionally shows a
statistically significant length→confidence correlation (r=0.358,
p=0.003), alongside topic structure that remains largely preserved under a
length-balancing correction (JS=0.938, ARI=0.945) — both findings are
reported together; neither is used to claim the model is insensitive to
document length. All of this is reported explicitly per
`ROBUSTNESS_REPORT.md` — none of it was grounds to discard k=4 in either
representation, since the same pattern was checked and found comparable
across the competing finalists.

## What this analysis does not claim

- It does not validate, and was not designed to validate, the manually
  derived RQ1-RQ4 categories (never consulted in preprocessing, modelling,
  or k-selection). It is offered as a complementary exploratory analysis
  and as evidence of interpretability, not proof of a "true" topic
  structure.
- It does not claim full text "reveals" themes metadata misses, or vice
  versa — differences are attributed to representation, vocabulary-size
  effects, stochastic variation, and thematic-granularity differences
  consistent with, but not proven to be caused by, the representation
  change (see `CROSS_REPRESENTATION_REPORT.md`).
- It does not claim k=4 is uniquely, provably optimal for either
  representation — the full-text choice in particular rests on a
  documented, reasoned reconciliation of real rater disagreement, not
  unanimous consensus, and k=5 remains a credible, documented alternative.
- Human evaluation is treated as evidence that supports the selected
  solution's interpretability, not as proof that it is the correct one.

## Manuscript-ready text

See `reports/MANUSCRIPT_TEXT.md` for the methodology paragraph, RQ5 results
paragraph, robustness paragraph, limitations paragraph, and reviewer-response
paragraph.
