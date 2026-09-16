# Dual-Representation LDA Analysis — AI Code Hallucinations (66 Primary Studies)

Reproducible analysis package for the LDA topic-modeling component (RQ5) of the manuscript
**"The Anatomy of a Phantom: A Socio-Technical Synthesis of AI Code Hallucinations."**

This repository is frozen. See `FINAL_ANALYSIS_FREEZE.md` for the freeze record and
`reports/FROZEN_MANUSCRIPT_VALUES.md` for the single authoritative values table the manuscript
draws from. This README describes only the final analysis as frozen; earlier iterations are
not discussed here (see `protocol/protocol_amendments.md` for the audit trail of methodology
corrections made before freezing).

## Study context

Systematic mapping review of 71 included studies on AI code hallucinations; 66 are primary
empirical/technical studies and 5 are secondary (survey/review) studies. This LDA analysis
uses **only the 66 primary studies** — the 5 secondary studies are documented but never enter
preprocessing, model fitting, selection, robustness analysis, or human validation.

## Research purpose

To identify, independently of the manually-derived RQ1-RQ4 classification, a data-driven
topic structure across the 66 primary studies, under two independent text representations, and
to determine whether/how that structure is sensitive to the choice of representation.

## Metadata analysis (primary RQ5 representation)

Title + abstract + author keywords (title+abstract only where keywords were unavailable,
24/66 studies). **Final model: k=4, structural-medoid seed 14.** Chosen as primary because
metadata documents are far more length-homogeneous, and the metadata model shows higher
cross-seed stability (0.66 vs. 0.54) and diversity (0.84 vs. 0.77) than the full-text model.
See `reports/METADATA_LDA_REPORT.md`, `reports/METADATA_FINAL_K_VALIDATION.md`.

## Full-text analysis (secondary representation-sensitivity analysis)

Cleaned, section-restricted full text of the same 66 studies (Introduction-Conclusion;
references/boilerplate/headers removed). **Final model: k=8, structural-medoid seed 2**,
retained as the most parsimonious representative of a broader near-equivalent region
(k=8-15) whose topic structure was shown to be persistent, not as a uniquely optimal model.
Shows a documented, non-trivial sensitivity to document length (see Limitations). See
`reports/FULLTEXT_LDA_REPORT.md`, `reports/FULLTEXT_FINAL_K_VALIDATION.md`.

## Preprocessing

spaCy (`en_core_web_sm` 3.8.0) tokenization + lemmatization, POS filter {NOUN, PROPN, VERB,
ADJ}, standard English stopwords, one documented deterministic lemma correction
(`datum`→`data`). Dictionary thresholds selected independently per representation from a
systematic 36-cell grid (`no_below`∈{2,3,4,5}, `no_above`∈{0.50,...,1.00}). Integer bag-of-words
counts (not TF-IDF) are the primary LDA input. See `preprocessing/`, `reports/METADATA_LDA_REPORT.md`.

## Model fitting

gensim `LdaModel`, k=2-20 × 20 seeds per representation (380 models each, 760 total for the
definitive sweep), frozen training budget (passes=30, iterations=800, alpha=eta=auto) selected
via a separate convergence pilot. Every model is saved under `models/`.

## Model selection

Joint Pareto front over C_v, C_NPMI, cross-seed stability, diversity, redundancy, thin-topic
incidence, and zero-dominance count — never coherence alone, never the max-coherence seed.
Representative model = structural medoid (max mean aligned similarity across seeds). See
`src/model_selection.py`, `results/{metadata,fulltext}/k_selection_decision.json`,
`protocol/protocol_amendments.md` for the k-selection rule's amendment history.

## Human validation

Two independent raters, blinded to model identity, k, and any AI-drafted label, rated the
metadata k-candidates (k=2,3,4,5) and the full-text final topics (k=8) for coherence,
interpretability, and distinctiveness, and independently proposed labels. **Raters did not
converge on a preferred metadata k** (Rater 1→k=5, Rater 2→k=3); this is reported, not hidden.
See `reports/HUMAN_VALIDATION_REPORT.md`, `human_validation/`.

## Robustness

Training-effort sensitivity, dictionary-neighbor sensitivity, domain-term (HF-A/B) and
phrase-detection (unigram/bigram) sensitivity, and 100 repetitions of 80% document
subsampling, for both representations; full text additionally received a document-length
diagnostic and length-balanced sensitivity model. See `reports/ROBUSTNESS_REPORT.md`.

## Cross-representation analysis

Rectangular Hungarian topic alignment (k_A≠k_B), dominant-topic ARI/NMI, and topic-level
similarity — computed only after both models independently froze. Modest/partial
correspondence (ARI=0.19, NMI=0.30), described without causal claims. See
`reports/CROSS_REPRESENTATION_REPORT.md`.

## Repository structure

```
protocol/          frozen methodology + amendment log
corpus/             66-study manifest and audit
extraction/         PDF extraction diagnostics
preprocessing/       tokenization/lemmatization outputs, stopwords, HF-term profiles
src/                 all analysis code (see below for execution order)
results/             every run-level metric, frozen values, provenance, validation report
human_validation/    blinded rating materials + completed rater data + consolidated summaries
figures/             57 figures (PNG+PDF), registry, SHA-256 checksums
reports/             all narrative reports and the frozen manuscript-values file
models/              every fitted LdaModel (760+ for the definitive sweep alone)
data/                metadata/full-text representations (full-text is NOT redistributed - see LICENSE)
```

## Reproduction

Environment (Python 3.11; see `reports/ENVIRONMENT_SNAPSHOT.md` for exact pinned versions):

```bash
uv venv --python 3.11 .venv
uv pip install --python .venv -r requirements.txt
.venv/Scripts/python -m spacy download en_core_web_sm
```

Pipeline, in order (every command below was actually run to produce this repository's frozen
outputs):

```bash
# Corpus + extraction + preprocessing
.venv/Scripts/python src/corpus_audit.py
.venv/Scripts/python src/extraction.py
.venv/Scripts/python src/preprocess_corpus.py
.venv/Scripts/python src/lemma_quality_audit.py
.venv/Scripts/python src/hf_terms.py

# Stage 1: dictionary-threshold grid + selection (per representation)
.venv/Scripts/python src/stage1_dictionary_sweep.py metadata
.venv/Scripts/python src/stage1_dictionary_sweep.py fulltext
.venv/Scripts/python src/select_stage1_config.py metadata
.venv/Scripts/python src/select_stage1_config.py fulltext

# Stage 2: convergence/prior pilot (per representation)
.venv/Scripts/python src/stage2_convergence_pilot.py metadata 5 0.50
.venv/Scripts/python src/stage2_convergence_pilot.py fulltext 4 0.75

# Domain-term / phrase sensitivity (per representation)
.venv/Scripts/python src/domain_term_sensitivity.py metadata 5 0.50 30 800
.venv/Scripts/python src/domain_term_sensitivity.py fulltext 4 0.75 30 800
.venv/Scripts/python src/phrase_sensitivity.py metadata 5 0.50 30 800
.venv/Scripts/python src/phrase_sensitivity.py fulltext 4 0.75 30 800

# Definitive k=2-20 x 20-seed sweep (per representation; the expensive step)
.venv/Scripts/python src/definitive_k_sweep.py metadata 5 0.50 30 800 --alpha auto --eta auto --kmax 20
.venv/Scripts/python src/definitive_k_sweep.py fulltext 4 0.75 30 800 --alpha auto --eta auto --kmax 20

# Stability, selection, medoid seed (per representation)
.venv/Scripts/python src/cross_seed_stability.py metadata
.venv/Scripts/python src/cross_seed_stability.py fulltext
.venv/Scripts/python src/model_selection.py metadata
.venv/Scripts/python src/model_selection.py fulltext
.venv/Scripts/python src/representative_seed.py metadata 4
.venv/Scripts/python src/representative_seed.py fulltext 8

# k=2-5 metadata candidate comparison + k=8-15 full-text cross-k persistence
.venv/Scripts/python src/candidate_k_comparison.py metadata 2,3,4,5 5 0.50 k2_k5_candidate_comparison.csv
.venv/Scripts/python src/candidate_k_comparison.py fulltext 8,9,12,13,14,15 4 0.75 fulltext_k_candidate_comparison.csv
.venv/Scripts/python src/cross_k_persistence.py

# Human-validation materials (blinded packets + rating sheets)
.venv/Scripts/python src/human_validation_packets.py metadata 4 14 5 0.50
.venv/Scripts/python src/human_validation_packets.py fulltext 8 2 4 0.75
.venv/Scripts/python src/blinded_candidate_packets.py metadata 2,3,4,5 5 0.50
.venv/Scripts/python src/intrusion_tests.py metadata 5 0.50
# (raters complete the sheets outside this pipeline; results consolidated by:)
.venv/Scripts/python src/human_validation_analysis.py

# Robustness (per representation)
.venv/Scripts/python src/robustness.py subsample metadata 5 0.50 30 800 4 14 --model_path models/metadata/k04_seed14.model
.venv/Scripts/python src/robustness.py subsample fulltext 4 0.75 30 800 8 2 --model_path models/fulltext/k08_seed02.model
.venv/Scripts/python src/fulltext_length_diagnostics.py 4 0.75 8 30 800 2

# Cross-representation comparison
.venv/Scripts/python src/cross_representation.py 4 14 8 2 5 0.50 4 0.75

# Figures, freeze, provenance, validation
.venv/Scripts/python src/generate_all_figures.py
.venv/Scripts/python src/generate_all_figures_batch2.py
.venv/Scripts/python src/generate_all_figures_batch3.py
.venv/Scripts/python src/freeze_values.py
.venv/Scripts/python src/build_provenance.py
.venv/Scripts/python src/validate_repository.py
```

The definitive k-sweep steps are the most compute-intensive (~9 and ~21 minutes respectively
on a 20-core machine with `ProcessPoolExecutor(max_workers=12)`); everything else completes in
well under a minute each.

## Citation

See `CITATION.cff`.
