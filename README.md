# Dual-Representation LDA Analysis — AI Code Hallucinations

## 1. Repository purpose

Reproducibility package for the LDA topic-modeling component (RQ5) of the
manuscript **"The Anatomy of a Phantom: A Socio-Technical Synthesis of AI
Code Hallucinations."** It documents the corpus, preprocessing, model
fitting, topic-number selection, human semantic evaluation, robustness
analysis, and cross-representation comparison, together with the code and
frozen data needed to verify every reported number and to reproduce the
analysis from scratch.

LDA here is a corpus-level characterization of recurring lexical structure.
It is a complementary line of evidence, not independent validation of the
manually derived RQ1–RQ4 classifications: those classifications are never
consulted in preprocessing, model fitting, parameter selection, or k
selection.

See `provenance/README.md` for methodological/audit material retained for
traceability but not used as a source for any value in this README.

## 2. Study corpus

The systematic mapping review includes **71 studies**: **66 primary** and
**5 secondary**. The LDA analysis uses the **66 primary studies only** — the
5 secondary studies are documented but excluded, because they synthesize
evidence from primary research and are not independent analytical units.

- `corpus/corpus_manifest.csv` — all 71 included studies (study_id,
  study_category, title, year, doi, included_in_lda).
- `corpus/primary_studies_manifest.csv` — the 66-study LDA analytical
  corpus, with PDF checksums and extraction status.
- `corpus/corpus_audit.md` — corpus construction and integrity checks
  (duplicate/PDF-match checks, matching method).

## 3. Analytical design

Two representations of the same 66 studies are built and modeled
**independently** — separate preprocessing, separate dictionary search,
separate priors, separate topic-number search, separate robustness
analysis, and separate human evaluation. They are compared only after both
are finalized (§15).

## 4. Metadata representation (primary RQ5 representation)

Title, abstract, and author-supplied keywords for each of the 66 studies.
Where keywords are genuinely unavailable, they are left unavailable — never
generated or inferred. Source: `corpus/metadata_documents.csv`,
`corpus/metadata_extraction_report.md`.

## 5. Full-text sensitivity representation

Cleaned substantive text extracted from the study PDFs (PyMuPDF):
Introduction, Background/Related Work, Methodology, Results, Discussion,
and Conclusion, where identifiable. Excluded: references, running
headers/footers, page numbers, publisher boilerplate, author/affiliation
blocks, duplicated front matter. Unicode NFKC normalization, dehyphenation
across line breaks, ligature repair, control-character removal, and
whitespace normalization are applied consistently across all 66 documents.
Source: `src/extract_fulltext.py`, `extraction/fulltext_extraction_report.md`.

Raw extracted full text is derived from copyrighted third-party
publications and is **not redistributed** in this repository (see
`LICENSE`, `.gitignore`); it is produced locally, at `extraction/fulltext/`,
only when the pipeline is reproduced (§18).

This representation is a **representation-sensitivity analysis**, not a
second primary result.

## 6. Preprocessing

Implemented in `src/preprocessing.py`, applied identically (deterministically,
corpus-wide) to both representations:

- Tokenization, lemmatization, POS tagging, and lowercasing via spaCy
  `en_core_web_sm` (3.8.0).
- Retain tokens tagged `NOUN`, `PROPN`, `VERB`, `ADJ`.
- Remove standard spaCy English stopwords, punctuation, purely numeric
  tokens, single-character tokens, and tokens with no alphabetic character.
- No corpus-specific stopwords are introduced interactively or on the basis
  of observed topic results.

Two predefined high-frequency-term conditions are evaluated per
representation:

- **HF-A**: normal generic cleaning only.
- **HF-B**: HF-A plus removal of a fixed, corpus-agnostic academic-writing
  filler list, frozen before the corpus's frequency table was inspected:
  `paper, study, studies, research, result, results, finding, findings,
  approach, method, methods, methodology, work, author, authors,
  researcher, researchers, section, figure, table, example, examples,
  case, et, al`.

Unigram and unigram+bigram tokenizations are both evaluated during
parameter selection. Documents are represented as integer bag-of-words
counts — TF-IDF and embedding vectors are not used as LDA input.

**Final configurations:** Metadata = HF-B + unigram. Full text = HF-A +
unigram (HF-A and HF-B converge to identical results at the selected
dictionary threshold).

## 7. Dictionary selection

For each representation, `no_below ∈ {2,3,4,5,6}` × `no_above ∈
{0.40,0.50,0.60,0.70,0.75,0.80,0.90,1.00}` (40 candidate dictionaries) is
evaluated for each preprocessing variant. Selection is a
**multi-configuration stability assessment**, not a maximum-coherence pick:
a configuration is eligible only if it has zero empty documents and is not
an isolated coherence spike relative to its immediate grid neighbours. See
`results/{metadata,fulltext}/stage1_decision.md`.

**Final dictionaries:**

| Representation | no_below | no_above | Vocabulary size |
|---|---|---|---|
| Metadata | 6 | 0.40 | 208 |
| Full text | 6 | 0.40 | 1,503 |

## 8. Seed strategy

Frozen master seed list (`src/stage3_sweep.py`):

```
[42, 101, 202, 303, 404, 505, 606, 707, 808, 909,
 1010, 1111, 1212, 1313, 1414, 1515, 1616, 1717, 1818, 1919,
 2020, 2121, 2222, 2323, 2424, 2525, 2626, 2727, 2828, 2929]
```

- **Pilot stages**: the first 5 seeds `[42, 101, 202, 303, 404]`.
- **Definitive topic-number search**: the first 20 seeds.

## 9. Model fitting

Definitive search: `k = 2, 3, …, 20` (19 values) × 20 seeds =
**380 independently seeded models per representation**
(`results/{metadata,fulltext}/k_sweep_by_seed.csv`, 380 rows each).
`gensim.models.LdaModel` (single-threaded) throughout, for strict
reproducibility under a fixed seed.

Standard models use **20 passes / 200 iterations**.

| Representation | alpha | eta |
|---|---|---|
| Metadata | 1.0 | auto |
| Full text | auto | auto |

## 10. Topic-number selection

Final k is **not** selected by maximum C_v alone. Every candidate k is
evaluated on a joint diagnostic set: C_v, C_NPMI, cross-seed stability,
topic diversity, inter-topic redundancy, topic prevalence, dominant-study
distribution, zero/thin-topic occurrence, and parsimony
(`results/{metadata,fulltext}/k_sweep_summary.csv`, `stage4_candidates.md`).

For each k, the 20 seeded models' full topic-word probability distributions
are pairwise Hungarian-aligned and compared by Jensen-Shannon similarity.
The **structural medoid** — the seed with the greatest mean aligned
similarity to the other 19 seeds, never the highest-coherence seed — is
used as that k's representative model.

Each k is Pareto-screened across the diagnostic set. When more than four k
values remain Pareto-optimal, the pre-specified rule ranks them by
cross-seed stability (descending) and keeps the top four, ties broken by
smaller k (parsimony tie-break). For both representations this yields:

**k ∈ {2, 3, 4, 5}**, evaluated in further detail.

## 11. Human semantic evaluation

Two raters (one a project author) independently score anonymized,
randomly-ordered candidate models, blinded to model identity, random seed,
parameter configuration, all quantitative model-selection metrics, topic
prevalence, dominant-study counts, and the numerical k label. (The number
of topics visible in a complete candidate model is necessarily observable.)
Raters assessed coherence, interpretability, distinctiveness, and
specificity, and independently proposed descriptive topic labels.

Human assessment is **complementary evidence**, integrated with the
quantitative criteria in §10 — not proof of a uniquely correct topic
structure, and never resolved by majority vote (n=2 raters).

Full scoring, blinding protocol, and reconciliation:
`reports/HUMAN_VALIDATION_REPORT.md`; raw per-rater scores in
`human_validation/Rater1.md` and `human_validation/Rater2.md`.

## 12. Final metadata model

| | |
|---|---|
| k | 4 |
| Structural-medoid seed | **1212** |
| Dictionary | no_below=6, no_above=0.40, vocabulary=208 |
| Priors | alpha=1.0, eta=auto |
| Training | passes=20, iterations=200 |
| Mean C_v (SD) | 0.3584 (0.0485) |
| Mean C_NPMI (SD) | -0.1638 (0.0146) |
| Mean cross-seed stability (SD) | 0.5815 (0.0513) |
| Topic diversity (top-25) | 0.8490 |
| Zero-dominance / thin topics | 0 / 0 |

Both human raters independently preferred the metadata k=4 solution
(unanimous).

| ID | Topic | Dominant studies | Prevalence |
|---|---|---:|---:|
| T0 | API/Code Hallucination: Benchmarks and Mitigation | 22 | 29.2% |
| T1 | AI-Generated Feedback in Programming Education | 16 | 24.2% |
| T2 | Developer Trust and Experience with AI Coding Assistants | 15 | 24.2% |
| T3 | Empirical Code Correctness, Testing, and Non-Determinism | 13 | 22.5% |

Prevalence is the mean document-topic probability across all 66 studies —
a distinct measure from the dominant-study counts (studies for which a
topic has the single highest probability). Topic membership is
probabilistic throughout. Full detail: `reports/METADATA_LDA_REPORT.md`.

## 13. Final full-text model

| | |
|---|---|
| k | 4 |
| Structural-medoid seed | **505** |
| Dictionary | no_below=6, no_above=0.40, vocabulary=1,503 |
| Priors | alpha=auto, eta=auto |
| Training | passes=20, iterations=200 |
| Mean C_v (SD) | 0.2957 (0.0271) |
| Mean C_NPMI (SD) | -0.2512 (0.0166) |
| Mean cross-seed stability (SD) | 0.5913 (0.0296) |
| Topic diversity (top-25) | 0.9070 |
| Zero-dominance / thin topics | 0 / 0 |

Human assessment was **not unanimous**: one rater preferred k=4; the other
preferred k=5, and identified k=3 as a parsimonious alternative. k=4 is
retained as the **conservative multi-criterion solution** — lowest
redundancy among the disputed finalists, markedly stronger training-effort
robustness, and perfect thin-topic safety under subsampling — **not
presented as uniquely superior**. k=5 remains a credible alternative.

| ID | Topic | Dominant studies | Prevalence |
|---|---|---:|---:|
| FT0 | Programming Education: Instruction, Grading, and Trust | 17 | 26.6% |
| FT1 | Code Repair, Verification, and Determinism Benchmarking | 8 | 13.5% |
| FT2 | Practitioner Perspectives on Package Hallucination and Security Risk | 16 | 22.7% |
| FT3 | Iterative and Retrieval-Based Hallucination Mitigation | 25 | 37.2% |

Full detail: `reports/FULLTEXT_LDA_REPORT.md`.

## 14. Robustness analyses

All checks run on each representation's finalist model (fixed
structural-medoid seed and configuration). Full detail:
`reports/ROBUSTNESS_REPORT.md`.

**80% document subsampling** (no replacement, 100 repetitions):

| | Metadata | Full text |
|---|---:|---:|
| Aligned topic-word JS similarity, mean (SD) | 0.812 (0.032) | 0.810 (0.038) |
| Dominant-assignment ARI, mean (SD) | 0.806 (0.091) | 0.799 (0.099) |

Interpreted as **substantial but incomplete** stability.

**Increased training effort** (passes=100, iterations=2000):

| | Metadata | Full text |
|---|---:|---:|
| Dominant-assignment ARI | 0.929 | 0.856 |

**Dictionary-neighbour sensitivity**: dominant document assignments are
**more sensitive** than topic-word structure. Observed ARI ≈ 0.15–0.28,
topic-word JS similarity ≈ 0.52–0.57. Treated as an important sensitivity,
not downplayed.

**Full-text length sensitivity**: Pearson r=0.358 (p=0.0031) between raw
document length and dominant-topic assignment confidence. Length-balanced
sensitivity model: JS=0.938, ARI=0.945, NMI=0.936.

## 15. Cross-representation analysis

Computed only after both representations' models were independently
finalized. Full detail: `reports/CROSS_REPRESENTATION_REPORT.md`.

- Document-level agreement: **ARI = 0.2384, NMI = 0.2738**.
- 10,000-repetition permutation test: none of the 10,000 permuted
  assignments equalled or exceeded the observed agreement (empirical
  p ≈ 0.0001).
- Metadata T0 → Full-text FT3: 17/22 studies = 77.3%. Metadata T1 →
  Full-text FT0: 9/16 studies = 56.3%. Metadata T2 and T3 show more
  **distributed correspondence** across multiple full-text topics.
- Vocabulary overlap: 208 (metadata) vs. 1,503 (full text) terms, 19 shared
  (9.1% of metadata vocabulary, 1.3% of full-text vocabulary), accounting
  for only ~2–10% of matched-topic probability mass.

**Interpretation:** the two representations show partial correspondence but
representation-dependent thematic granularity. Neither representation is
treated as uniquely revealing the true topic structure.

## 16. Repository structure

```
corpus/              71-study manifest, 66-study LDA corpus, extraction reports
extraction/           full-text extraction diagnostics (raw text is not redistributed)
preprocessing/        lemmatization audit reports
src/                  all analysis code (see §17-18 for execution order)
results/              every run-level metric and frozen numerical output
human_validation/     blinded rating materials and both raters' completed scores
figures/               figures (PNG+PDF) and the figure index
reports/               narrative reports; reports/FROZEN_MANUSCRIPT_VALUES.md is
                       the single canonical values table every other report agrees with
provenance/            methodological/audit records retained for traceability only
                       (not a source for reproduction or manuscript values)
models/                every fitted LdaModel; git-ignored, regenerable (see §18)
```

## 17. Verify frozen outputs

A lightweight check that the committed result files, reports, and figures
are internally consistent with each other and with
`reports/FROZEN_MANUSCRIPT_VALUES.md`. It recomputes simple aggregates
(means, SDs, row/column counts) directly from the already-frozen CSV/JSON
files already in this repository, checks the eight final topic labels are
present, and scans reader-facing files for known-conflicting configuration
values.

**This is not a reproduction of the LDA pipeline** — it does not refit any
model or re-run preprocessing, and completes in seconds.

```bash
python src/verify_frozen_outputs.py
```

## 18. Reproduce the analysis from frozen inputs

Full pipeline, in order. Every command loops over both representations by
default unless a representation is given as an argument.

```bash
# Environment (§19)
python -m venv .venv && .venv/Scripts/activate   # or .venv/bin/activate
pip install -r requirements.txt

# Stage 0 — corpus and text extraction (deterministic; no LDA fitting)
python src/corpus_audit.py
python src/extract_metadata.py
python src/extract_fulltext.py
python src/doc_length_audit.py
python src/run_lemma_audits.py

# Stage 1 — preprocessing x dictionary grid search, then frozen-rule selection
python src/stage1_sweep.py
python src/stage1_select.py

# Stage 2 — priors and convergence search, then frozen-rule selection
python src/stage2_sweep.py
python src/stage2_select.py

# Stage 3 — definitive k=2..20 sweep, 20 seeds each (380 fits/representation)
# COMPUTATIONALLY EXPENSIVE: this is the long-running step.
python src/stage3_sweep.py

# Stage 4 — diagnostics, Pareto screening, finalist reduction (k in {2,3,4,5})
python src/stage4_select.py

# Stage 5 — robustness (subsampling, training-effort, dictionary-neighbour;
#           length-sensitivity is full-text only). Also long-running.
python src/stage5_robustness.py
python src/stage5_length_sensitivity.py

# Stage 6 — interpretation packets and blinded human-evaluation packets
python src/stage6_packets.py

# [Human evaluation happens here — see human_validation/, §11. Both raters'
#  scores are already recorded in human_validation/Rater1.md and Rater2.md.]

# Stage 7 — cross-representation comparison (vocabulary-intersection method)
python src/stage7_cross_representation_v2.py

# Figures
python src/make_manuscript_figures.py
```

Stage 3 (the definitive k-sweep) and Stage 5 (robustness) are the
computationally expensive steps; every other stage completes quickly.
Reproducing the full pipeline requires the source PDFs of the 66 primary
studies, obtained independently via the DOIs in `corpus/corpus_manifest.csv`
(not redistributed here — see `LICENSE`).

A documentation-only run of §17 is **not** equivalent to this reproduction:
it verifies the already-committed outputs are consistent, but does not
refit any model.

## 19. Environment

| | |
|---|---|
| Python | 3.11.15 (see `.python-version`) |
| gensim | 4.4.0 |
| spaCy | 3.8.16 (`en_core_web_sm` 3.8.0) |
| PyMuPDF | 1.28.2 |
| scikit-learn 1.9.1 · scipy 1.17.1 · numpy 2.4.6 · pandas 3.0.5 · openpyxl 3.1.5 · matplotlib 3.11.2 |

`requirements.txt` pins Python packages only (pip does not pin the Python
interpreter itself). `.python-version` and `environment.yml` record the
Python version. Installing from `requirements.txt` (or `environment.yml`)
installs the exact pinned `en_core_web_sm==3.8.0` wheel directly — this
repository never uses a bare `spacy download en_core_web_sm` command, which
would silently fetch an arbitrary later model version.

```bash
# venv + pip
python -m venv .venv
.venv/Scripts/activate      # Windows; .venv/bin/activate on macOS/Linux
pip install -r requirements.txt

# or conda/mamba
conda env create -f environment.yml
```

## 20. Limitations

- LDA does not validate, and is not designed to validate, the manually
  derived RQ1–RQ4 categories.
- No single coherence metric alone proves model quality; k=4 was selected
  through the joint diagnostic set in §10–11.
- k=4 is not presented as the objectively true topic number for either
  representation — for full text in particular, k=5 remains a credible,
  documented alternative.
- Metadata and full text are not claimed to recover the same latent
  structure; correspondence is modest and partly distributed (§15).
- The permutation test's statistical significance supports that
  cross-representation agreement exceeds chance — it does not by itself
  imply strong agreement; ARI=0.238/NMI=0.274 are modest.
- Document-level topic assignments in both representations are only
  moderately robust to small, plausible dictionary-threshold changes (§14).

## 21. Citation

See `CITATION.cff`.
