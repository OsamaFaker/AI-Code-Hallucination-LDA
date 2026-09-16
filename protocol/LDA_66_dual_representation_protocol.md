# Protocol: Dual-Representation LDA Re-Analysis of 66 Primary Studies

**Review title:** "The Anatomy of a Phantom: A Socio-Technical Synthesis of AI Code Hallucinations."

**Status:** FROZEN prospectively, before any model is fit or any topic is inspected.
Any post-hoc change is logged in `protocol_amendments.md` with date, original rule,
revised rule, and justification. Amendments driven by substantive results (rather than
implementation bugs) are not permitted.

**Source instruction document:** `../../LDA_66_Dual_Representation_Claude_Prompt.md` (frozen
requirements list). This protocol operationalizes every numbered section of that document.

---

## 1. Corpus definition

- The systematic-review corpus contains **71 included studies**: **66 primary** + **5 secondary**.
- Source of truth for study identity, classification, title, authors, year, venue, and DOI:
  `EMSE_MASTER_REFERENCE_v6_4_FINAL.xlsx`, sheet `Master Data` (71 rows, `Study category`
  column = `Primary`/`Secondary`, 66/5 split confirmed).
- PDF sources:
  - `66_Primery_Study/` — 66 files, all primary studies (used for LDA).
  - `71_Final_SMR/` — 71 files, full included set (used only to document/audit exclusion of
    the 5 secondary studies; never modeled).
- **Only the 66 primary studies enter LDA** at any stage: extraction, preprocessing,
  dictionary construction, parameter optimization, model fitting, topic-number selection,
  topic interpretation, robustness analysis, topic prevalence, cross-representation comparison.
- PDF-to-Study-ID matching is performed by normalized-title matching against `Master Data`,
  manually verified. Any unmatched PDF is flagged and resolved before N=66 is confirmed.

## 2. Analysis A — Metadata representation

`combined_text = Title + Abstract + Author Keywords` (keywords appended only when extracted
from the PDF; otherwise `Title + Abstract`). No LLM-generated or externally inferred keywords.
Title and abstract text are each used exactly once (no duplication). Keyword availability is
recorded per study in `data/metadata_representation.csv`.

## 3. Analysis B — Full-text representation

Cleaned substantive body text of the same 66 PDFs: Introduction, Background/Related Work,
Methodology, Results, Discussion, Conclusion (where identifiable). Removed: reference list,
running headers/footers, page numbers, publisher/copyright boilerplate, DOI boilerplate,
affiliation blocks, author metadata blocks, repeated title/abstract blocks, navigation text,
emails, non-substantive URLs, OCR garbage. Content is not removed merely because it shapes
topic formation. Exact removed-element counts per study are logged in
`data/fulltext_representation_manifest.csv`.

## 4. Extraction method

PyMuPDF (`fitz`) primary parser (layout-preserving text extraction, per-page). OCR is not
invoked unless normal extraction yields a suspiciously short document (see thresholds in
`extraction/extraction_quality_report.md`); OCR fallback is `pytesseract` if triggered.
Section identification is heuristic (regex over common heading forms: Introduction, Related
Work/Background, Method(ology), Results, Discussion, Conclusion, References, Acknowledgements,
Appendix) — imperfect by nature of heterogeneous camera-ready PDF layouts, and diagnostics are
saved so failures are visible rather than silently absorbed.

## 5. Text-cleaning rules

Unicode NFKC normalization; de-hyphenation across PDF line breaks; ligature repair; removal of
control characters; collapsing of repeated whitespace; email/URL stripping (full text only,
URLs retained in metadata abstracts if substantively part of the sentence); reference-list
truncation from the detected "References"/"Bibliography" heading onward.

## 6. Preprocessing candidate values (Stage 1 grid)

- `no_above` (high-document-frequency cutoff) ∈ {0.50, 0.60, 0.70, 0.75, 0.80, 0.85, 0.90, 0.95, 1.00}
- `no_below` (rare-word cutoff, absolute doc count) ∈ {2, 3, 4, 5}
- Domain-term treatment: HF-A (retain all), HF-B (remove ubiquitous low-discriminative terms),
  HF-C (retain + interpret via FREX/exclusivity)
- Phrase treatment: unigrams-only vs. unigrams+bigrams (gensim `Phrases`, `min_count` ∈ {2,3,5},
  NPMI scorer, multiple thresholds); trigrams as an optional sensitivity check only
- POS filter: retained set {NOUN, PROPN, VERB, ADJ} as default; alternatives tested only if
  the default is not clearly defensible

Because Stage 1 is explicitly a *pilot* used only "to eliminate clearly poor preprocessing
choices" (source doc §15), the dictionary-threshold grid (36 no_above×no_below combinations)
is evaluated at a representative, resource-bounded subset of the full design: **k ∈ {5, 10, 15}**
(low/mid/high of the source document's suggested pilot set {3,5,7,10,15}) and **5 random
seeds** (0–4). This is a documented, prospective scope decision, not a post-hoc reduction: the
full 20-seed, k=2–20 design is reserved for the definitive sweep (§9 below) on the frozen
preprocessing configuration only. Domain-term treatment (HF-A/B/C) and phrase treatment are
each evaluated as a separate controlled comparison on the winning dictionary configuration,
not as a full cross product with the dictionary grid, to avoid combinatorial explosion while
remaining systematic within each factor.

## 7. Dictionary-filtering candidate values

See §6. Final `no_below`/`no_above` are selected per representation independently (Analysis A
and B may differ because of differing document-length distributions), from a *stable region*
of parameter space (not the single maximum-C_v cell), preferring the most parsimonious/
conventional configuration among near-equivalent neighbors.

## 8. Phrase-detection settings

See §6. Selection criteria: stability, interpretability, vocabulary coverage, redundancy.
Phrases are discovered by the detector, never manually forced.

## 9. High-frequency-word experiments

Per §6/§11 of the source document: full per-token frequency/document-frequency profiling for
both representations (`preprocessing/{metadata,fulltext}_high_frequency_terms.csv`), followed
by the systematic `no_above`/`no_below` grid described above, followed by the HF-A/B/C domain-
term sensitivity comparison (source doc §12).

## 10. LDA hyperparameter search

Stage 2 (training/convergence pilot, source doc §15): `passes` ∈ {10,20,30,40}, `iterations`
∈ {200,400,800}, `alpha` ∈ {auto, symmetric, asymmetric}, `eta` ∈ {auto, symmetric}, evaluated
at the frozen Stage-1 preprocessing configuration, k ∈ {5,10,15}, 5 seeds, to identify the
smallest training budget at which per-topic-word distributions have converged (successive
budget increases produce ≤ a small, documented change in mean topic-word JS distance). The
frozen budget is used for the entire definitive sweep and all robustness analyses.

## 11. k-range

k = 2..20 per representation, independently for Analysis A and Analysis B; extended to 21–25
only if k=20 remains plausible (topics adequately populated, no degenerate collapse) — never
extended merely to chase a higher coherence value.

## 12. Seeds

20 seeds (0–19), identical seed set reused across every k, for both representations:
19 k-values × 20 seeds = 380 models per representation, 760 models total for the definitive
sweep (before Stage 1/2 pilot models and robustness-analysis models, which are additional and
separately counted).

## 13. Evaluation metrics

Per model: `C_v`, `C_NPMI`, `C_UMass` (optional/supporting); topic diversity (unique-word
proportion across fixed top-20 lists); topic redundancy (pairwise top-20 Jaccard, full-
distribution cosine, Jensen-Shannon similarity); topic prevalence (mean probability, dominant-
study count/%, min/median/max document-topic probability); thin-topic counts (0/1/<3/<5
dominant studies); document-assignment confidence (top-1 vs top-2 margin, and proportion of
studies with dominant probability <0.40, 0.40–0.60, >0.60); topic exclusivity; a documented
FREX-style score (harmonic mean of within-topic frequency rank and exclusivity rank, following
the standard STM-style FREX formulation, weight 0.7 on exclusivity by default — documented,
not tuned post hoc).

## 14. Cross-seed stability method

For each k, all 20 seeded models are pairwise-aligned using the Hungarian algorithm on
full topic-word probability-vector distances (primary alignment cost = Jensen-Shannon
divergence). Reported: mean/SD/median/min/max of aligned JS similarity (primary), cosine
similarity (secondary), top-20 Jaccard (supporting).

## 15. Final-model selection criteria

Multi-criterion, Pareto-front-based joint evaluation of mean C_v, mean C_NPMI, seed stability,
topic diversity, redundancy, thin-topic incidence, zero-dominance-topic count, topic
prevalence balance, interpretability (post-hoc, human/LLM-assisted), and parsimony (preferring
smaller k among near-equivalent Pareto-optimal points). No coherence-only selection; no
post-hoc numerical weighting scheme. k_A and k_B are allowed, and expected, to differ.

## 16. Representative-seed selection

Structural medoid: for the selected k, the seed whose mean aligned structural similarity
(JS-based) to all other seeded models at that k is maximal. Not the maximum-coherence seed.

## 17. Robustness analyses

- Training-effort sensitivity (substantially increased passes/iterations vs. frozen budget)
- 80% document subsampling without replacement, 100 repetitions per representation, same
  sampled Study_IDs used for every metric within a repetition (topic similarity, ARI, NMI)
- Prior sensitivity (alpha/eta alternatives)
- Dictionary sensitivity (neighboring no_below/no_above)
- Phrase sensitivity (unigram-only vs. unigram+bigram)
- Frequent-domain-term sensitivity (HF-A/B/C, re-examined at the final model)
- Full-text-only: document-length diagnostics + a length-balanced (per-section token-capped)
  sensitivity model

## 18. Human interpretation procedure

The AI system (Claude) is not a substitute for independent human raters and is not presented
as one. For every final topic in Analysis A and B, an interpretation packet is generated
(top-20 probability terms, top-20 FREX terms, 10 highest-loading study titles/abstracts,
prevalence) together with a blank, structured rating sheet
(`human_validation/{metadata,fulltext}/topic_XX_rating_sheet.csv`) covering: proposed label,
description, coherence (1–5), interpretability (1–5), distinctiveness (1–5), incoherent-topic
flag, word-intrusion result, document-intrusion result. At least two independent human
evaluators complete these sheets outside of this pipeline; reconciliation and disagreement
reporting occur only after both sheets are returned. Any AI-drafted label appearing in the
packet is explicitly marked `[AI-DRAFT — NOT A VALIDATED HUMAN LABEL]` and excluded from the
manuscript-ready outputs until replaced or ratified by human raters.

## 19. Cross-representation comparison

Only after each representation has independently frozen its final model. Shared-vocabulary
topic alignment (standard Hungarian if k_A=k_B, rectangular Hungarian + unmatched-topic
reporting otherwise); cosine/JS/top-20 Jaccard similarity; ARI/NMI/Variation of Information
on dominant-topic assignment across the shared 66 studies; contingency matrix; qualitative
match classification (strong/partial/representation-specific) based on combined quantitative
similarity and reconciled human labels.

## 20. Independence from manual RQ1–RQ4 classification

RQ1–RQ4 categories (from `Master Data` / `Category Mapping`) are never used during
preprocessing, fitting, k-selection, or labeling before a model is frozen. Only after freezing
may an exploratory, clearly-labeled comparison be reported. LDA is never described as
"validating" the manual synthesis.

---

## Amendment log

See `protocol_amendments.md` (created only if/when an amendment occurs).
