# Reproducibility Report

Consolidated reproducibility record for the frozen dual-representation LDA analysis. This
report answers: what would someone else need to reproduce this analysis exactly, and how do
we know the frozen outputs are internally consistent?

## Environment

Python 3.11.15; gensim 4.4.0; spaCy 3.8.16 (en_core_web_sm 3.8.0); pandas 3.0.5; numpy 2.4.6;
scipy 1.17.1; scikit-learn 1.9.1; matplotlib 3.11.2; pymupdf 1.28.2; nltk 3.10.3; pyLDAvis
3.4.1. Full pinned list: `requirements.txt`, `environment.yml`. Setup and full pipeline
commands (every one actually run to produce this repository's frozen outputs): `README.md`
"Reproduction" section. Full package inventory and rationale for the local `uv`-managed
virtual environment: `reports/ENVIRONMENT_SNAPSHOT.md`.

## Determinism

- All 760 definitive-sweep models (380 per representation, k=2-20 × 20 seeds) use fixed,
  documented `random_state` seeds (0-19).
- Dictionary construction, training budget, and priors are frozen before the definitive sweep
  (`results/{metadata,fulltext}/stage1_selected_config.json`,
  `stage2_frozen_training_config.json`) and applied identically across every seed/k.
- Structural-medoid selection is a deterministic function of the 20 saved models per k (no
  randomness beyond the model-fitting seeds themselves).
- `models/` is git-ignored (~203MB, regenerable) — see README "`models/` is intentionally
  git-ignored" for the exact regeneration command
  (`src/definitive_k_sweep.py`, both representations, reproduces every seeded model including
  the two frozen medoid models at `models/metadata/k04_seed14.model` and
  `models/fulltext/k08_seed02.model`).

## What is NOT bit-for-bit guaranteed

- gensim's `LdaModel` uses multi-threaded variational inference internally; while
  `random_state` fixes the seed, minor floating-point non-associativity across BLAS thread
  counts can in principle cause tiny numerical differences on a different core count than the
  20-core machine used here. This is not expected to change any reported value beyond the 4
  decimal places already used throughout, and cross-seed/robustness analyses were designed
  specifically to demonstrate the reported topic structure is not sensitive to this level of
  noise.
- PDF text extraction (`src/extraction.py`, PyMuPDF) is deterministic for a given PDF and
  PyMuPDF version; the pinned version (1.28.2) is recorded for exact reproduction.

## Internal-consistency verification performed

1. **Frozen-value programmatic verification** (`src/freeze_values.py`): every headline
   quantitative value (N, k, vocabulary, seeds, model counts, medoid seeds, C_v, C_NPMI,
   stability, diversity, subsampling similarity/ARI) is recomputed directly from
   `results/{rep}/*.csv`/`*.json` source files and compared against the expected table with a
   0.001 tolerance. Zero discrepancies have ever been found across three verification passes
   (initial freeze, and two subsequent re-verifications after the k-floor repair and the
   topic-label-reconciliation task) — see `results/FROZEN_FINAL_VALUES.json`
   (`freeze_status: "VERIFIED"`).
2. **Repository validator** (`src/validate_repository.py`): 36 automated PASS/FAIL checks
   covering corpus counts, model counts, seed counts, medoid-seed consistency, dominant-topic
   count sums, topic-prevalence sums, figure/figure-registry/checksum completeness, manuscript
   transfer table and provenance population, label-reconciliation completeness, and raw
   human-rating file presence. Current status: **ALL CHECKS PASS**
   (`results/validation_report.txt`).
3. **Human-validation data verification**: every combined statistic reported in
   `reports/HUMAN_VALIDATION_REPORT.md` (e.g. full-text combined coherence 4.0625, rater
   preferences, intrusion-test accuracy) was independently recomputed from the raw rater CSVs
   in `human_validation/Human_Result/` and cross-checked against an independently-produced
   summary workbook, with an exact match (`src/human_validation_analysis.py`).
4. **Topic-label verification**: the researcher-reconciled labels in
   `human_validation/FINAL_TOPIC_LABELS.csv` were verified word-for-word identical to an
   independently-discovered authoritative source workbook
   (`human_validation/Human_Result/Final_Result_Summary/FINAL_TOPIC_LABELS_RECONCILED.xlsx`).
5. **Figure/data consistency**: all 57 figures are generated directly from the same frozen
   `results/`/`human_validation/` files cited in the reports (never hand-edited); SHA-256
   checksums for every figure file are recorded in `figures/FIGURE_SHA256.csv` and re-verified
   unchanged across the label-reconciliation task (no figure renders descriptive topic-name
   text, only T0/T1/... indices or blinded Model A-D letters, so none needed regeneration when
   labels were finalized).

## Amendment and freeze history

Every substantive change to the analysis (not implementation-only bug fixes) is logged with
date, original rule, revised rule, and justification in `protocol/protocol_amendments.md`.
Freeze checkpoints and their checksums are recorded in `FINAL_ANALYSIS_FREEZE.md`.

## Known limitations affecting reproducibility

- Full-text article PDFs and their extracted text are not redistributed (copyright; see
  `LICENSE`, `.gitignore`) — a re-extraction from the same source PDFs (not included in this
  repository) is required to exactly reproduce `data/fulltext_texts/`, which is itself
  git-ignored.
- The five secondary studies' PDFs are similarly not included; they are documented in
  `corpus/corpus_audit.md` but never modeled.
