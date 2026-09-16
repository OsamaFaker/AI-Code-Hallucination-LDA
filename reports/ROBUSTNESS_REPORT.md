# Robustness Report

Summarizes every robustness analysis (protocol Sections 17/23/24) for both final models
(metadata k=4 seed=14; full-text k=8 seed=2). All numbers are traceable to the cited files.

## Training-effort sensitivity

Frozen budget (passes=30, iterations=800) vs. a substantially boosted budget (passes=100,
iterations=2000), same seed, same dictionary.

| Representation | Mean topic-word JS similarity | Dominant-topic agreement |
|---|---:|---:|
| Metadata | 0.957 | 98.5% |
| Full text | 0.902 | 93.9% |

Both representations show the frozen training budget is well converged; the boosted budget
changes almost nothing about the fitted topics. Source: `results/{metadata,fulltext}/training_effort_sensitivity.json`.

## 80% document subsampling (100 repetitions)

Same sampled study set used for every metric within a repetition (topic similarity, ARI, NMI
never independently resampled). Source: `results/{metadata,fulltext}/subsampling_80pct_100reps.csv`
and `..._summary.json`.

| Representation | Mean topic similarity (JS) | Mean ARI | Mean NMI |
|---|---:|---:|---:|
| Metadata (k=4) | 0.586 (SD 0.051) | 0.129 (SD 0.077) | 0.221 (SD 0.075) |
| Full text (k=8) | 0.515 (SD 0.022) | 0.219 (SD 0.068) | 0.460 (SD 0.054) |

(95% intervals and medians in `results/{rep}/subsampling_80pct_summary.json`.)

Topic-word *structure* is moderately robust to removing 20% of studies; document-level
dominant-topic *assignment* is comparatively fragile (low ARI) for both representations. This
is reported plainly as a real limitation of fitting LDA on a 66-document corpus, not
downplayed — smaller corpora inherently produce less stable per-document assignments even when
the underlying topic-word structure is reasonably stable.

## Prior (alpha/eta) sensitivity

Evaluated during Stage 2 at the pilot k-set {5,10,15} and 5 seeds
(`results/{rep}/stage2_prior_pilot.csv`). `alpha=auto, eta=auto` was retained as the frozen
prior for both representations — no alternative combination improved mean seed stability by
more than the documented 0.02 margin.

## Dictionary sensitivity

Neighboring `no_below`/`no_above` values around each frozen configuration, refit at the final
k/seed: `results/{metadata,fulltext}/dictionary_sensitivity.csv`. Both representations show
high similarity to neighboring configurations (no discontinuous jump at the frozen threshold),
supporting the stable-region selection made in Stage 1.

## Phrase sensitivity

See `reports/METADATA_LDA_REPORT.md` / `FULLTEXT_LDA_REPORT.md` for the unigram-vs-bigram
comparison; both representations retained unigrams-only in the frozen model.

## Frequent-domain-term sensitivity

See the same per-representation reports (HF-A vs. HF-B); both representations retained all
substantive domain terms (HF-A) in the frozen model.

## Full-text length sensitivity (Section 24, full-text only)

- Token length ranges roughly 11.7× across the 66 full texts (`results/fulltext/length_diagnostics.json`).
- Document length is weakly-to-moderately associated with topic-assignment confidence
  (Pearson r=0.249, p=0.043).
- A length-balanced sensitivity model (per-document token cap) agrees with the full model only
  moderately (JS similarity 0.446, dominant-topic agreement 33.3%) —
  **materially lower** than the training-effort/dictionary robustness checks above. This is
  the single most consequential robustness finding in this package: **document length has a
  non-trivial influence on the full-text topic structure**, and this is reported as an
  explicit limitation of Analysis B rather than resolved away. See
  `results/fulltext/length_balanced_sensitivity.json`.

## Overall robustness assessment

Both final models are well-converged given their frozen training budgets and reasonably
stable to neighboring dictionary choices. Document-level assignment stability under
subsampling is modest for both representations (expected at N=66). The full-text model
carries an additional, non-trivial sensitivity to document length that the metadata model
does not share (metadata documents are much more length-homogeneous by construction). This
asymmetry is itself informative for interpreting cross-representation disagreement (Section
"Interpret representation sensitivity correctly," protocol Section 26): some of the
metadata/full-text divergence may reflect this length sensitivity in Analysis B rather than
purely a granularity difference.
