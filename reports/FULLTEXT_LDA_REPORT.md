# Analysis B — Full-Text LDA Report

**k=8 is provisional**, selected by parsimony from the near-equivalent region k∈{8,9,12,13,
14,15} and supported by a cross-k topic-persistence analysis, but pending blinded human
validation — see `reports/FULLTEXT_FINAL_K_VALIDATION.md` and
`reports/FINAL_K_DECISION_TABLE.md`. This report is also recommended to be read as a
**secondary, representation-sensitivity analysis**, not an equally-weighted alternative to
Analysis A — see `reports/CROSS_REPRESENTATION_REPORT.md`.

Corpus: same 66 primary studies as Analysis A. Representation: cleaned, section-restricted
full text (Introduction/Background/Related Work/Methodology/Results/Discussion/Conclusion;
references, headers/footers, boilerplate, and affiliation/author blocks removed — see
`extraction/extraction_quality_report.md`, `data/fulltext_representation_manifest.csv`).

## Preprocessing (frozen)

- Same spaCy pipeline as Analysis A (`preprocessing/fulltext/preprocessing_meta.json`), fit
  independently on the full-text corpus.
- One deterministic lemma correction applied (`datum`→`data`), shared with Analysis A.
- Dictionary: `no_below=4`, `no_above=0.75` (vocabulary size 2626), selected from the same
  36-cell systematic grid design as Analysis A but run independently on this corpus
  (`results/fulltext/stage1_dictionary_threshold_sweep.csv`,
  `results/fulltext/stage1_selected_config.json`). The higher `no_above` than Analysis A's
  0.50 reflects the longer, more heterogeneous full-text documents, per protocol's explicit
  allowance for independently selected thresholds by representation.
- Training budget: `passes=30`, `iterations=800`, `alpha=auto`, `eta=auto` (same frozen budget
  as Analysis A, arrived at independently via the fulltext convergence pilot,
  `results/fulltext/stage2_convergence_pilot.csv`).

## Sensitivity screens

- **Domain-term treatment** (k=10 pilot): mean C_v 0.384 (HF-A) → 0.444 (HF-B, 4 ubiquitous
  domain terms removed); document-assignment ARI=0.097, NMI=0.404 — again a real, non-trivial
  effect. HF-A (retain) was kept as the frozen configuration for consistency with Analysis A
  and because removal did not clearly improve stability/diversity/redundancy jointly. See
  `results/fulltext/domain_term_sensitivity.json`.
- **Phrase treatment** (k=10 pilot): mean C_v 0.384 (unigram) → 0.388 (unigram+bigram); 2,949
  bigram phrases discovered (data-driven); document-assignment ARI=0.136. The frozen model
  uses unigrams only — the coherence gain from bigrams was marginal and not accompanied by a
  clear stability/diversity improvement. See `results/fulltext/phrase_sensitivity.json`.

## Definitive k-sweep

k = 2–20, 20 seeds each (380 models), `results/fulltext/definitive_ksweep_runs.csv`;
cross-seed stability in `results/fulltext/seed_stability_by_k.csv`. Every k in 2–20 was
Pareto-optimal on the joint criterion set for this representation (i.e. the front did not
discriminate strongly by itself); the unweighted composite score identified k=14 as the
front's best point, with k ∈ {8, 9, 12, 13, 14, 15} substantively equivalent (within 0.05
composite score) and at/above the documented k≥4 floor. Parsimony then selects the smallest
of that equivalent set. Full record: `results/fulltext/k_selection_decision.json`.

**Selected k = 8.**

Representative model: **structural medoid, seed 2** (mean aligned similarity = 0.554;
`results/fulltext/representative_seed_k08.json`).

At the selected k: mean C_v = 0.396, mean C_NPMI = −0.043, mean cross-seed JS stability =
0.543, mean topic diversity = 0.767. Full-text topics are, as expected, less stable across
seeds than the shorter metadata representation (0.54 vs. 0.66) — reported as a genuine
representation difference, not adjusted away.

## Final topics (Analysis B, k=8, seed=2)

Full packets in `human_validation/fulltext/topic_XX_packet.json`; blank rating sheets in
`human_validation/fulltext/topic_rating_sheet_rater{1,2}.csv`. **Labels below are AI-drafted,
not human-validated** (protocol Section 22).

| Topic | Prevalence | Top probability terms | [AI-DRAFT] provisional label |
|---|---:|---|---|
| 0 | 0.115 | participant, copilot, developer, suggestion, experience, community, trust | Developer trust & community perception of AI coding tools |
| 1 | 0.075 | package, hallucination, rate, grader, javascript, repository, malicious | Package hallucination & malicious/insecure dependency risk |
| 2 | 0.063 | class, requirement, completion, api, signal, security, benchmark, attack | Security-focused benchmark evaluation of code completion |
| 3 | 0.224 | hallucination, api, requirement, return, benchmark, token, self, project | API/dependency hallucination detection & mitigation frameworks |
| 4 | 0.140 | chatgpt, exercise, topic, developer, project, pass, training, difficulty | Programming exercises, training tasks & skill assessment |
| 5 | 0.185 | student, chatgpt, course, feedback, assignment, explanation, group | Programming education, instruction & feedback |
| 6 | 0.123 | chatgpt, snippet, value, complexity, vulnerability, non, scenario, round | Code vulnerability, determinism & fix quality |
| 7 | 0.075 | bug, pattern, participant, assistant, suggestion, buggy, sample, label | Bug patterns & developer-reported assistant issues |

## Full-text-only diagnostics (Section 24)

- Token length: mean 3,717, median ≈ 3,470 (see `results/fulltext/length_diagnostics.json`),
  max/min ratio ≈ 11.7× — full-text documents vary substantially in length.
- Document length is weakly-to-moderately associated with topic-assignment confidence
  (Pearson r = 0.249, p = 0.043) — marginal but non-negligible; reported transparently as a
  limitation rather than dismissed.
- **Length-balanced sensitivity model** (per-document token cap ≈2,400 tokens, approximating
  section-balanced sampling): mean topic-word JS similarity to the full model = 0.446,
  dominant-topic agreement = 33.3%. This is a materially lower agreement than the
  training-effort/dictionary robustness checks, indicating that document length has a
  non-trivial influence on the fitted full-text topic structure. This is reported as a genuine
  limitation of Analysis B, not smoothed over — see `reports/ROBUSTNESS_REPORT.md` and the
  manuscript limitations paragraph.

## Robustness (final model)

- **Training-effort sensitivity**: JS similarity 0.902, dominant-topic agreement 93.9% — good
  convergence at the frozen budget. (`results/fulltext/training_effort_sensitivity.json`)
- **80% subsampling, 100 repetitions**: mean topic similarity (JS) = 0.515, mean ARI = 0.219
  (`results/fulltext/subsampling_80pct_summary.json`).
- **Dictionary sensitivity**: `results/fulltext/dictionary_sensitivity.csv`.

## Relationship to RQ1–RQ4

Same independence as Analysis A: RQ1–RQ4 categories played no role before freezing; any
comparison is exploratory (see `reports/CROSS_REPRESENTATION_REPORT.md`).
