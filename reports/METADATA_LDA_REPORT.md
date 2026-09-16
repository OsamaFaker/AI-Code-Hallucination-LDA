# Analysis A — Metadata LDA Report (Title + Abstract + Author Keywords)

**k=4 is FINAL.** It is the best-supported candidate by quantitative evidence among k∈{2,3,4,5}
(see `reports/METADATA_FINAL_K_VALIDATION.md`). Blinded human validation is complete
(`reports/HUMAN_VALIDATION_REPORT.md`) but **did not itself select k=4** — the two raters
preferred different candidates (k=5 and k=3 respectively); k=4 was retained primarily on
quantitative-parsimony grounds, with human evaluation as complementary interpretive evidence.
Topic labels below are researcher-reconciled from both raters' independent labels
(`reports/TOPIC_LABEL_RECONCILIATION.md`).

Corpus: 66 primary studies (5 secondary studies excluded throughout; see
`corpus/corpus_audit.md`). Representation: title + abstract, with author keywords appended
where extracted (42/66 studies; 24/66 use title+abstract only — see
`extraction/extraction_quality_report.md`).

## Preprocessing (frozen)

- Tokenization/lemmatization: spaCy `en_core_web_sm`, POS filter {NOUN, PROPN, VERB, ADJ},
  standard spaCy English stopwords (see `preprocessing/metadata/preprocessing_meta.json`).
- One deterministic lemma correction applied corpus-wide (`datum`→`data`); see
  `preprocessing/lemma_corrections.csv`.
- Dictionary: `no_below=5`, `no_above=0.50` (vocabulary size 397), selected from a systematic
  36-cell grid (`results/metadata/stage1_dictionary_threshold_sweep.csv`) via a documented
  stable-region + parsimony rule (`results/metadata/stage1_selected_config.json`) — **not**
  the maximum-coherence cell.
- Training budget: `passes=30`, `iterations=800`, `alpha=auto`, `eta=auto`, frozen via a
  convergence pilot (`results/metadata/stage2_convergence_pilot.csv`,
  `stage2_prior_pilot.csv`).
- Representation is Bag-of-Words counts (the appropriate input for classical probabilistic
  LDA); TF-IDF was not used as the primary representation.

## Sensitivity screens

- **Domain-term treatment** (HF-A retain vs. HF-B remove ubiquitous domain terms, at a
  representative k=10 pilot): mean C_v 0.387 → 0.374; document-assignment ARI=0.096,
  NMI=0.408 — removing the most ubiquitous domain terms (3 terms) measurably changes document
  groupings, so the decision to retain all substantive domain terms (HF-A) in the frozen model
  is a real methodological choice, not inconsequential. See
  `results/metadata/domain_term_sensitivity.json`.
- **Phrase treatment** (unigram vs. unigram+bigram, k=10 pilot): mean C_v 0.387 → 0.350; 386
  bigram phrases discovered (data-driven, not manually forced); document-assignment ARI=0.064
  (bigrams substantially reshuffle groupings). The frozen model uses unigrams only, since
  bigrams did not improve coherence, stability, or interpretability enough to justify the
  added vocabulary complexity for this short-text representation. See
  `results/metadata/phrase_sensitivity.json`.

## Definitive k-sweep

k = 2–20, 20 seeds each (380 models total), `results/metadata/definitive_ksweep_runs.csv`.
Cross-seed stability (Hungarian-aligned JS similarity) per k in
`results/metadata/seed_stability_by_k.csv`. Model selection used a Pareto front over C_v,
C_NPMI, stability, diversity, redundancy, thin-topic incidence, and zero-dominance count
(never coherence alone), with parsimony applied only among Pareto-optimal k values
substantively equivalent (within 0.05 composite score) to the front's best point, at or above
a documented floor of k=4 (see `protocol/protocol_amendments.md` for why this floor was
added). Full decision record: `results/metadata/k_selection_decision.json`.

**Selected k = 4** (k=5 was equivalent; both are far below the coherence-maximizing region of
the sweep, which is not used as a selection criterion on its own).

Representative model: **structural medoid, seed 14** (mean aligned similarity to the other 19
seeded k=4 models = 0.690 — not the highest-coherence seed;
`results/metadata/representative_seed_k04.json`).

At the selected k: mean C_v = 0.40 (interpreted only relative to this corpus/sweep, not as an
externally "high" or "good" value — no external coherence benchmark is claimed), mean C_NPMI
= −0.10, mean cross-seed JS stability = 0.66, mean topic diversity = 0.84.

## Final topics (Analysis A, k=4, seed=14)

Full packets (top-20 probability terms, top-20 FREX terms, 10 top-loading studies/abstracts,
prevalence) are in `human_validation/metadata/topic_XX_packet.json` (note: those packets'
`ai_draft_label` field is the original pre-rating draft, retained there for provenance only —
superseded by the reconciled labels below; see `reports/TOPIC_LABEL_RECONCILIATION.md`).
**Labels below are researcher-reconciled after two independent raters completed blinded
evaluation** (`reports/HUMAN_VALIDATION_REPORT.md`); reconciliation did not select k=4 (the
raters did not agree on a preferred k — see that report) and did not alter any quantitative
result.

| Topic | Prevalence | Top probability terms | Final reconciled label |
|---|---:|---|---|
| 0 | 0.254 | chatgpt, problem, hallucination, developer, type, copilot, dataset, tool | AI Code Verification, Vulnerability, and Developer Trust |
| 1 | 0.062 | requirement, prompt, function, input, domain, critical, development, specific | Requirements-Driven Prompting and Code Generation |
| 2 | 0.322 | chatgpt, student, tool, education, work, provide, assignment, feedback | AI in Programming Education and Adoption |
| 3 | 0.362 | hallucination, development, api, user, models, propose, complex, challenge | API/Dependency Hallucination Mitigation |

## Robustness (final model)

- **Training-effort sensitivity** (30/800 → 100/2000 passes/iterations): mean topic-word JS
  similarity 0.957, dominant-topic agreement 98.5% — the frozen budget is well converged.
  (`results/metadata/training_effort_sensitivity.json`)
- **80% subsampling, 100 repetitions**: mean topic similarity (JS) = 0.586, mean ARI = 0.129,
  mean NMI reported alongside in `results/metadata/subsampling_80pct_summary.json`. Topic
  *structure* (word distributions) is moderately stable under subsampling; document-level
  *assignment* (ARI) is comparatively fragile — expected at N=66 with only 4 topics, and
  reported transparently rather than described as "robust."
- **Dictionary sensitivity** (neighboring no_below/no_above): see
  `results/metadata/dictionary_sensitivity.csv`.

## Relationship to RQ1–RQ4

RQ1–RQ4 manual categories were not used in preprocessing, fitting, k-selection, or labeling.
Any comparison with the manual synthesis is exploratory and reported only in
`reports/CROSS_REPRESENTATION_REPORT.md` / `FINAL_LDA_REPORT.md`, after freezing. LDA is a
complementary exploratory representation, not a validation of the manual mapping.
