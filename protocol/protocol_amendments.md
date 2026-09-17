# Protocol Amendments / Implementation Corrections

Per protocol Section "Status": substantive methodological changes require a logged amendment;
implementation-error corrections are explicitly permitted and are logged here for full
traceability, even though they do not change the frozen methodology itself.

## 2026-09-14 — Jensen-Shannon similarity numerical fix

- **Issue:** `src/lda_core.py`'s `js_similarity()` used `scipy.spatial.distance.jensenshannon`
  directly. On near-identical high-dimensional sparse topic-word distributions, floating-point
  underflow can make the pre-sqrt quantity a tiny negative number, causing scipy to return NaN
  (with a `RuntimeWarning: invalid value encountered in sqrt`). The original fallback treated
  NaN as similarity 0.0 (maximally dissimilar) - the opposite of the true near-identical
  (~1.0) relationship. This surfaced during the Stage 2 metadata convergence pilot (one
  warning observed), which specifically compares same-seed models across adjacent training
  budgets - exactly the case most likely to produce near-identical topic pairs.
- **Fix:** replaced with a manually epsilon-clipped, normalized JS-divergence computation that
  cannot produce a negative pre-sqrt value, applied in both `js_similarity()` and
  `pairwise_redundancy()`.
- **Scope of correction:** Stage 1 dictionary-threshold sweeps (`stage1_dictionary_sweep.py`,
  both representations) and the metadata Stage 2 pilot had already run with the buggy version
  before this fix was applied. Given the bug requires near-perfect distribution identity to
  trigger (not reproduced in 2000 synthetic-distribution trials) and Stage 1 compares
  *different* random seeds' topics (far less likely to be near-identical than the same-seed,
  adjacent-budget comparisons in Stage 2), its effect on the Stage 1 dictionary-configuration
  selection is judged negligible and those sweeps were not re-run. Stage 2 (both
  representations) and every subsequent stage (domain/phrase sensitivity, the definitive
  k-sweep, cross-seed stability, robustness analyses, cross-representation comparison) were
  run only after this fix, since those stages are more exposed to the failure mode and the
  compute cost of re-running Stage 2 is small.
- **Justification:** implementation error discovered during the run, corrected per the
  protocol's explicit allowance ("Any modification must be recorded... unless an
  implementation error is discovered"), not a change to the frozen methodology.

## 2026-09-14 — Model-selection parsimony rule refined (substantive amendment)

- **Original rule (protocol Section 20 / `model_selection.py` first implementation):**
  compute the Pareto front over {mean C_v, mean C_NPMI, cross-seed stability, topic
  diversity, topic redundancy, thin-topic incidence, zero-dominance-topic count}; among
  Pareto-optimal k values, select the smallest (global parsimony).
- **Observed problem:** applied to the Analysis A (metadata) definitive k-sweep results, this
  rule selected k=2. Inspection showed k=2 (and k=3) mechanically dominate several criteria
  not because they are substantively better topic structures, but because with only 2-3
  topics absorbing ~22-33 studies each on average, near-zero thin-topic/zero-dominance counts
  and low pairwise redundancy are close to guaranteed by arithmetic, not by genuine topical
  coherence. A 2-topic model cannot plausibly resolve the distinct causal/detection/mitigation/
  human-impact sub-themes the review is investigating, so treating k=2 as "equivalent" to
  larger, more Pareto-competitive k values (the front also included k=12,13,15,16,17,18,20)
  purely because it is Pareto-optimal was judged a flaw in the selection rule, not a genuine
  finding.
- **Revised rule:** parsimony (smallest-k tie-break) now applies only among Pareto-optimal k
  values that are *substantively equivalent* to the front's best point - defined as within
  0.05 of the best unweighted, min-max-normalized composite score across the same seven
  criteria (equal weights fixed a priori, not tuned after seeing results) - and only at or
  above a documented floor of k=4, below which thin-topic/zero-dominance metrics cannot
  meaningfully discriminate topic quality for this corpus size (66 studies). Full detail and
  the resulting equivalence set are recorded in `results/{rep}/k_selection_decision.json`.
- **Scope:** applied identically, prospectively (i.e., before inspecting the full-text
  k-selection outcome) to both Analysis A and Analysis B - it is a correction to the general
  decision procedure, not a per-representation adjustment chosen to reach a preferred result.
- **Justification:** the original rule technically matched the protocol text ("prefer a
  parsimonious ... configuration when several ... configurations produce equivalent
  structures") but the implementation did not operationalize "equivalent structures"
  correctly - it treated Pareto-optimality alone as equivalence, which is too permissive.
  This is logged as a substantive amendment (not merely an implementation bug) because it
  changes a decision rule after observing its output on real data; the change is a general
  correction to the selection procedure's logic, not a choice tuned to produce a particular k.

## 2026-09-17 — Figure-checksum registry path-format fix (implementation error)

- **Issue:** `figures/FIGURE_SHA256.csv` was generated on Windows using `str(Path)` directly,
  producing backslash-separated paths (e.g. `figures\metadata\M8_....png`) instead of the
  forward-slash paths used by git/GitHub (`figures/metadata/M8_....png`). All 114 SHA-256
  **values** were correct; only the path **keys** were wrong, which caused every figure to
  fail an automated remote-verification lookup during the GitHub-deployment task despite the
  actual file content being byte-identical between local and remote.
- **Fix:** `src/build_figure_checksums.py` (new, using `Path.as_posix()`) regenerates
  `figures/FIGURE_SHA256.csv` with portable forward-slash paths. Re-verified 114/114 figures
  PASS against both the corrected registry and the live GitHub remote
  (`reports/REMOTE_FIGURE_VERIFICATION.md`).
- **Justification:** implementation error discovered during GitHub-deployment verification,
  corrected per the protocol's explicit allowance for implementation-error fixes. No figure
  content, hash value, or analytical result changed.

## 2026-09-16 — Removal of the k≥4 floor; replaced with descriptive admissibility + blinded human validation

- **Original rule (2026-09-14 amendment above):** parsimony applies only among Pareto-optimal
  k within 0.05 composite score of the front's best point AND at or above a floor of k=4.
- **Concern raised:** the k≥4 floor, while motivated by a genuine observation (k=2's
  near-guaranteed dominance on redundancy/thin-topic metrics), was itself a numeric threshold
  chosen without independent justification, and risked being read as post-hoc reasoning to
  preserve a preferred k rather than a principled admissibility criterion.
- **Revised rule:** the floor is removed from the automatic selection logic entirely. In its
  place, every candidate k in the original near-equivalent region is evaluated descriptively
  on the **structural-medoid model's own** dominant-topic balance (mega-topic dominance vs.
  thin-topic incidence — a qualitative failure-mode distinction, not a numeric cutoff),
  stability, and diversity (`results/metadata/k2_k5_candidate_comparison.csv`,
  `reports/METADATA_FINAL_K_VALIDATION.md`), and blinded human validation (topic identity and
  k value withheld from raters) is required before the decision is treated as final. For the
  full-text representation, the analogous concern (k=8 selected by parsimony from a
  6-candidate near-equivalent region) is addressed by a direct cross-k topic-persistence
  analysis (`results/fulltext/cross_k_topic_persistence.csv`,
  `reports/FULLTEXT_FINAL_K_VALIDATION.md`) showing k=8's structure is highly-to-moderately
  persistent across the full candidate region, rather than by asserting k=8 is uniquely best.
- **Justification:** substantive amendment, logged per the protocol's amendment rules. The
  underlying concern that motivated the original floor (k=2/k=3's mega-topic
  under-differentiation) is retained and re-argued transparently in
  `reports/METADATA_FINAL_K_VALIDATION.md` without relying on an unjustified numeric floor.
