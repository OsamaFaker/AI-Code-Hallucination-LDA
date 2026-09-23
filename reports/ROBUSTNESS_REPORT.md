# Robustness Report

Consolidated robustness evidence for the final selected models (metadata
k=4, full-text k=4), per plan §13/§21-24. Full per-finalist detail (including
the rejected k=2/3/5 candidates) is in `results/{metadata,fulltext}/`.

## 1. Document subsampling (80%, no replacement, 100 repetitions)

Each repetition's `LdaModel` uses the finalist's own structural-medoid seed
(metadata: 1212, full-text: 505) — fixed across all 100 repetitions, so the
experiment isolates sensitivity to document removal from
random-initialization variance. Sampling seeds 1-100 (fixed
`numpy.random.default_rng` draws) determined which 80% of studies were
included each repetition; recorded in `subsampling_seeds_k4.csv` for both
representations.

| Metric | Metadata (k=4) | Full-text (k=4) |
|---|---|---|
| Aligned JS similarity (mean, SD) | 0.812 (0.032) | 0.810 (0.038) |
| ARI, dominant-topic assignment (mean, SD) | 0.806 (0.091) | 0.799 (0.099) |
| NMI (mean) | 0.813 | 0.799 |
| Thin-topic (<5 studies) emergence | 2/100 | 0/100 |

Topic-word stability (JS ≈0.81 for both) is reported separately from
document-assignment stability (ARI ≈0.80 for both) per plan §21 — the two
are close here, but this is not assumed and was verified, not asserted, for
every finalist. Neither representation's final model is described as
"robust" without this quantitative backing: ARI~0.80 indicates *substantial
but incomplete* document-assignment agreement under 20% document removal,
not near-perfect agreement.

## 2. Training-effort sensitivity (frozen budget vs. passes=100/iterations=2000)

| Metric | Metadata (k=4) | Full-text (k=4) |
|---|---|---|
| JS similarity | 0.884 | 0.905 |
| Dominant-topic ARI | 0.929 | 0.856 |
| Dominant-topic NMI | 0.918 | 0.865 |

Both final models show strong agreement under a substantially increased
training budget (100 passes and 2,000 iterations, versus the frozen 20
passes and 200 iterations — five times as many passes and ten times as many
iterations) — neither model is training-budget-limited at the frozen
Stage-2 configuration.

## 3. Dictionary-threshold sensitivity (immediate grid neighbours)

| Representation | no_below/no_above | vocab | JS | Dominant-topic ARI | NMI |
|---|---|---|---|---|---|
| Metadata | 5/0.4 | 273 | 0.552 | 0.236 | 0.351 |
| Metadata | 6/0.5 | 211 | 0.517 | 0.152 | 0.214 |
| Full-text | 5/0.4 | 1780 | 0.569 | 0.284 | 0.293 |
| Full-text | 6/0.5 | 1667 | 0.516 | 0.230 | 0.274 |

Topic-word distributions are moderately (not highly) robust to a single-step
dictionary threshold change in both representations (JS 0.52-0.57).
Document-level dominant-topic assignment is considerably more sensitive
(ARI 0.15-0.28) — **this is reported explicitly as a real limitation, not
described as robust** (plan §21's rule applies here as much as to
subsampling). Both final models share this weakness to a similar degree;
it does not differentiate among the finalists and was not used as a
selection criterion.

## 4. Full-text document-length sensitivity (mandatory)

- Length→confidence correlation at k=4: **Pearson r=0.358 (p=0.0031)**,
  significant. Present (with varying significance) across k=3,4,5; not
  significant at k=2.
- Length-balanced refit (2/66 documents capped at 15,500 tokens via
  deterministic section-proportional systematic sampling) vs. original,
  at k=4: JS=0.938, ARI=0.945, NMI=0.936.

**Interpretation, held to both halves honestly:** full-text topic
*assignment confidence* is measurably associated with document length, but
the *topic structure itself* is robust to the length-balancing correction.
Both facts are reported; neither is suppressed because it complicates the
narrative (plan §24).

## 5. Cross-seed stability in context

Stability at the selected k=4 (metadata 0.582, full-text 0.591) is
below the smaller finalists (k=2 stability >0.71 in both representations)
but was not treated as disqualifying — the Pareto reduction and the
robustness/training-effort/redundancy evidence above jointly support k=4
over the higher-stability, higher-redundancy, or (for full text) less
training-effort-robust alternatives. See
`reports/HUMAN_VALIDATION_REPORT.md` for the full multi-criterion
reconciliation.

## 6. Summary judgment

Neither final model is presented as unconditionally robust. Concrete,
quantified limitations carried into the manuscript: (a) document-level
assignment is meaningfully sensitive to both 20% document removal and
single-step dictionary threshold changes in both representations; (b)
full-text assignment confidence correlates with document length. Concrete,
quantified strengths: (a) both models are insensitive to a substantially
increased training budget (five times the passes, ten times the
iterations); (b) topic-word structure survives length-balancing
correction in full text; (c) neither final model exhibits zero-dominance or
thin topics at the full-corpus fit.
