# PRE-EXECUTION ANALYSIS PLAN — LDA Topic Modelling of 66 Primary Studies

Status: **DRAFT — awaiting explicit approval before Stage 1 execution begins.**
Per Master Prompt §41: no LDA fitting occurs until this plan is approved. Corpus
audit and full-text extraction (Stage 0) are prerequisite bookkeeping, not
modelling, and may proceed once the environment is ready; all dictionary,
prior, convergence, k-sweep, and robustness fitting is gated on approval of
this document.

This plan resolves four decisions made explicitly by the user prior to
drafting (recorded here for the record, not to be revisited after results are
observed):

1. **Environment**: isolated `.venv` (Python 3.11.15) created under `LDA/`,
   with gensim, spaCy (`en_core_web_sm`), PyMuPDF, scikit-learn, etc. installed
   into it. System Python (3.14) is not used for modelling.
2. **Metadata (abstract/keywords) source**: no abstract or keyword text exists
   in any spreadsheet in the project (`EMSE_MASTER_REFERENCE_v6_4_FINAL.xlsx`
   "Master Data" has Title/Authors/Year/coded categories only, no
   abstract/keywords columns). Abstract and Keywords must be extracted from
   each PDF's own front matter using deterministic pattern rules. A 10–15
   study calibration sample spanning different publisher templates (ACM,
   IEEE, Springer, arXiv, MDPI, etc.) is manually spot-checked to freeze the
   extraction *rules*; separately, and in addition, every individual study
   whose extraction is not `high`-confidence is manually verified against its
   own PDF before `metadata_documents.csv` is frozen — a `medium`/`low`
   confidence extraction never silently falls back to title-only. Title-only
   is used only when manual inspection confirms a paper genuinely has no
   abstract; keywords are omitted (never inferred) only when manual
   inspection confirms they are genuinely absent.
3. **Human evaluation (§26–28)**: Claude cannot serve as an independent human
   rater without defeating the purpose of blinded validation. The pipeline
   runs through quantitative candidate filtering (§18) and produces blinded
   rating packets (§25–27), then **pauses**. Execution resumes only after the
   user (plus a second independent rater) completes scoring.
4. **Computational scale**: a full Cartesian product across every dictionary
   × prior × convergence × preprocessing × k × seed combination is
   computationally prohibitive and is explicitly rejected. A **staged,
   pre-registered sequential design** is used instead (detailed below). All
   grids, pilot k-values, and seed lists are frozen in this document before
   any fitting occurs, per §35 (no result-driven retuning).

---

## 1. Confirmed 66-study corpus

Verified independently from two sources before this plan was written:

- `LDA/66_Primery_Study/` contains exactly **66 PDF files**.
- `EMSE_MASTER_REFERENCE_v6_4_FINAL.xlsx` → "Master Data" sheet contains
  **72 rows** (1 header + 71 studies), of which **66 rows have
  `Study category = Primary`** and **5 rows have `Study category = Secondary`**
  (S04, S37, S67, S68, S69 — confirmed absent from the PDF folder).

Formal deliverable (Stage 0, before any modelling): `corpus/corpus_audit.csv`
and `corpus/corpus_audit.md`, which will additionally establish:

- a Study_ID ↔ PDF filename mapping (matched via title similarity, since
  filenames are not currently ID-coded), recorded with match confidence;
- unique Study_ID check, duplicate-document check (hash-based);
- per-study title/abstract/keyword/full-text availability flags;
- document length in tokens (raw, pre-preprocessing);
- SHA-256 checksum of every source PDF.

The pipeline **does not proceed past Stage 0** unless the confirmed modelling
corpus is exactly 66 studies.

## 2. Metadata construction (Analysis A)

`combined_text = TITLE + ABSTRACT + KEYWORDS` (keywords appended only when
found; never generated). Extraction procedure:

1. Title taken verbatim from `Master Data.Title` (authoritative, already
   human-curated) rather than re-extracted from the PDF.
2. Abstract/Keywords extracted from PDF page 1–2 text (PyMuPDF) using
   heading-anchored regex: text between an `Abstract` heading and the next
   structural heading (`Keywords`/`Index Terms`/`CCS Concepts`/
   `ACM Reference Format`/`1. Introduction`/`I. Introduction`) is the abstract;
   text between a `Keywords`/`Index Terms` heading and the next structural
   heading is the keyword string.
3. Every extraction is scored `high` (both boundaries matched cleanly),
   `medium` (one boundary heuristic/ambiguous), or `low` (no reliable
   boundary found). `medium` and `low` never fall back to title-only
   automatically — both trigger mandatory manual verification against the
   source PDF. Title-only is used for a study only after manual inspection
   confirms the article genuinely has no abstract; keywords are omitted only
   after manual inspection confirms they are genuinely absent.
4. Rule-calibration spot-check: 10–15 studies, chosen to span the distinct
   venues/publisher templates present in the corpus (including at least one
   `high`-confidence case per template), reviewed against the source PDF
   before the general extraction rules are frozen. Any systematic error found
   here triggers a rule fix applied corpus-wide (documented), not a
   per-document patch. This is separate from, and in addition to, the
   mandatory per-document manual verification of every `medium`/`low` case in
   step 3 — every non-`high` extraction in the final 66-study corpus is
   manually checked before `metadata_documents.csv` is frozen, not merely the
   calibration sample.

Deliverable: `corpus/metadata_documents.csv` with columns `Study_ID, title,
abstract, keywords, keywords_available, extraction_confidence,
manually_verified, combined_text`.

## 3. Full-text extraction (Analysis B)

- Parser: PyMuPDF (`fitz`), page-by-page.
- OCR fallback (`pytesseract` + `pdf2image`) triggered when **any** of the
  following fixed, pre-registered checks fail, computed on the raw extracted
  text before section stripping: (a) total extracted text below 500
  characters or 100 whitespace-tokens; (b) mean characters-per-page below 200
  (implausibly sparse extraction for a scholarly PDF); (c) alphabetic-character
  ratio below 0.60 (alphabetic characters ÷ non-whitespace characters); (d)
  more than 1% of characters are Unicode replacement characters (U+FFFD) or
  control characters outside standard whitespace. Any trigger routes the
  study to OCR re-extraction and/or manual inspection — it never causes
  silent exclusion from the corpus. Every fallback and every raw quality
  metric is logged per study.
- Section retention/removal exactly per Master Prompt §5 (keep Introduction…
  Conclusion; strip references, bios, affiliations, headers/footers, page
  numbers, ToC, emails, URLs, OCR garbage). Section boundaries detected via a
  case-insensitive heading regex; where no reliable heading structure is
  found, the whole retained-text body (post reference-stripping) is kept and
  the study is flagged `section_detection = low_confidence` rather than
  guessed at.
- Normalization: Unicode NFKC, dehyphenation across line breaks, ligature
  repair, control-character removal, whitespace normalization.

Deliverable: `extraction/fulltext_extraction_report.csv` /
`.md` with per-study extraction method, OCR-fallback flag, section-detection
confidence, raw character/token count, and final substantive token count.

## 4. Document-length audit (§6)

Computed immediately after extraction, before any fitting: min/max/mean/
median/SD/IQR/max-min ratio of raw token counts, histogram + boxplot
(`figures/fulltext/doc_length_distribution.png`). This motivates the mandatory
length-sensitivity analysis in Stage 5b.

## 5. Preprocessing specification (frozen)

Shared conceptual pipeline, independently fit vocabularies per representation:

- spaCy `en_core_web_sm`: tokenize, lemmatize, lower-case.
- Retain POS: `NOUN, PROPN, VERB, ADJ`.
- Remove: standard spaCy English stopwords, punctuation, purely numeric
  tokens, single-character tokens, and tokens containing no alphabetic
  character at all (e.g. bare numbers, symbol strings). **Retained**: tokens
  containing digits or the characters `+ # _ . -` alongside at least one
  alphabetic character (e.g. `C++`, `C#`, `GPT-4`, `Python3`, `req2test`,
  versioned model names, package/API identifiers) — these are not discarded
  merely for containing a digit or symbol. This rule is applied corpus-wide
  and is not topic-specific.
- A corpus-level lemmatization-error audit is produced
  (`preprocessing/lemma_audit.md`); any manual correction must be
  deterministic, corpus-wide, documented, and not topic-specific.
- RQ1–RQ4 categories are never consulted during preprocessing.

### 5a. Domain-term sensitivity (§8) — frozen HF-B list

Two conditions, both evaluated in Stage 1 (never selected post hoc):

- **HF-A**: retain all substantive domain terms (no additional removal beyond
  §5's generic stopword/punctuation/numeric rules).
- **HF-B**: additionally remove a **predefined, corpus-agnostic** list of
  generic academic-writing filler terms that survive POS filtering. Chosen
  from general scholarly-writing genre knowledge, *not* from this corpus's
  frequency table, and explicitly excludes domain terms named in §8
  (code, LLM, model, programming, developer, hallucination):

  ```
  paper, study, studies, research, result, results, finding, findings,
  approach, method, methods, methodology, work, author, authors,
  researcher, researchers, section, figure, table, example, examples,
  case, et, al
  ```

### 5b. Phrase sensitivity (§9) — frozen bigram parameters

- **A. Unigram** representation.
- **B. Unigram+bigram**: gensim `Phrases` with `min_count=5`, `threshold=10.0`,
  default (original) scoring, applied once (bigrams only, no trigrams),
  fit independently per representation. Parameters fixed a priori; not tuned
  to preferred output.

This gives **4 preprocessing variants per representation**: {HF-A, HF-B} ×
{unigram, unigram+bigram}.

## 6. Bag-of-Words input (§10)

Integer BoW counts via `gensim.corpora.Dictionary` feed classical
`gensim.models.LdaModel`. `LdaModel` (single-threaded) is used for every fit
in every stage, including the definitive k-sweep — `LdaMulticore` is not used
anywhere, because its parallel online updates are not guaranteed deterministic
under a fixed seed. Where wall-clock time needs reducing, independent fits
(different seeds, different k, different pilot cells) are parallelized at the
process/job level, each running a single-threaded `LdaModel`; no fit is
internally multi-threaded. TF-IDF is not used as LDA input. No
neural/embedding topic model is used as the principal analysis.

## 7. Fixed master seed list

One deterministic seed list is used everywhere; pilots use a fixed prefix of
it so pilot and definitive results are drawn from the same sequence rather
than a separately-drawn sample:

```
[42, 101, 202, 303, 404, 505, 606, 707, 808, 909,
 1010, 1111, 1212, 1313, 1414, 1515, 1616, 1717, 1818, 1919,
 2020, 2121, 2222, 2323, 2424, 2525, 2626, 2727, 2828, 2929]
```

- Stage 1 & Stage 2 pilots: first **5** seeds `[42, 101, 202, 303, 404]`.
- Stage 3 definitive k-sweep: first **20** seeds. Extended to all 30 only if
  Stage-1 timing shows this is cheap enough (decided before Stage 3 begins,
  documented either way — not a post-hoc reaction to Stage-3 results).

## 8. Pilot k-set (frozen)

`{5, 10, 15}` — three values spanning the low/mid/high thirds of the eventual
k=2–20 range, deliberately avoiding the boundary values 2 and 20 so pilot
signal isn't distorted by edge effects. Used for all Stage 1 and Stage 2
pilots. Not derived from, or influenced by, any prior LDA result.

## 9. STAGE 1 — Preprocessing × dictionary selection (per representation)

Grid, fully crossed, at pilot k-set × 5 pilot seeds, using a **fixed pilot
training budget** (`passes=20, iterations=400, alpha='auto', eta='auto'`,
explicitly not the final frozen priors — that is decided in Stage 2):

- Preprocessing variants: 4 (HF-A/HF-B × unigram/bigram).
- Dictionary grid: `no_below ∈ {2,3,4,5,6}` × `no_above ∈ {0.40, 0.50, 0.60,
  0.70, 0.75, 0.80, 0.90, 1.00}` = 40 configurations.
- Total fits per representation: 4 × 40 × 3 × 5 = **2,400** (4,800 across both
  representations).

For every (preprocessing × dictionary) cell record: vocabulary size, % of
vocabulary removed, empty-document count, average document vocabulary, mean/SD
C_v, mean/SD C_NPMI, preliminary top-N topic diversity, and preliminary seed
stability computed as: for each pilot k, Hungarian-align the topic-word
distributions of every pair among the 5 pilot seeds' fitted models (full
distributions, exactly as Stage 3/§19), compute pairwise JS similarity on the
aligned topics, average over all pairs and then over the 3 pilot k values.

**Frozen dictionary-selection rule (§11)**: the highest-coherence cell is
never auto-selected. A configuration is *eligible* only if (a) it produces
zero empty documents, and (b) it is not an isolated maximum — i.e. its four
immediate grid neighbours (±1 step in `no_below`, ±1 step in `no_above`) have
mean C_v within 0.03 (absolute) and preliminary stability within 0.05
(absolute) of the candidate. Among eligible configurations forming a
contiguous stable region, the most parsimonious member (highest `no_below`,
lowest `no_above` — i.e. the smallest resulting vocabulary among the
eligible set) is selected. If no configuration satisfies (a) and (b)
simultaneously, the tolerance-defined neighbourhood check is relaxed by a
single fixed step (documented as a protocol note, not a retune) before
re-applying the same rule.

Bigrams are retained only if they show a meaningful multi-criterion advantage
over unigrams (§9) — defined as: bigram mean C_v exceeds unigram mean C_v by
>0.02 absolute AND preliminary stability is not lower by more than 0.03
absolute, both evaluated at the otherwise-matched selected dictionary
configuration. Otherwise unigram is the default. HF-A vs HF-B is decided by
the identical rule (coherence advantage >0.02 without a stability loss
>0.03) — not on whichever produces more attractive topics.

Deliverables: `results/metadata/dictionary_sweep.csv`,
`results/fulltext/dictionary_sweep.csv` (all 4 preprocessing variants
included, selected variant flagged).

**Checkpoint**: actual Stage-1 wall-clock time is reported before Stage 2
begins, since it calibrates whether the definitive-sweep seed count stays at
20 or extends to 30.

## 10. STAGE 2 — Priors and convergence (per representation, frozen config from Stage 1)

At pilot k-set × 5 pilot seeds:

- **Prior grid** (§12): `alpha ∈ {auto, symmetric, 0.05, 0.10, 0.25, 0.50,
  1.00}` × `eta ∈ {auto, symmetric}` = 14 combinations. Seed stability here
  uses the same Hungarian-aligned JS procedure as Stage 1 (§9) and Stage 3
  (§19) — topic labels permute across runs, so no stability metric anywhere
  in this plan is computed without first aligning topics via the Hungarian
  algorithm on full topic-word distributions. Evaluated on coherence, seed
  stability, diversity, redundancy, dominant-topic distribution, prevalence
  distribution. Priors are **not** chosen because they produce more evenly
  sized topics; among priors that are quantitatively comparable (mean C_v
  within 0.02 absolute of the best, stability within 0.03 absolute of the
  best), `auto`/`auto` is preferred as the most parsimonious choice.
- **Convergence/training-budget grid** (§13): `passes ∈ {10, 20, 30, 50}` ×
  `iterations ∈ {200, 400, 800, 1200}` = 16 combinations, ordered by total
  training effort (`passes × iterations`). Each combination is compared to the
  **next larger** combination in that ordering using Hungarian-aligned JS
  similarity of topic-word distributions and dominant-topic agreement (same
  seed, same dictionary). **Frozen convergence rule**: the selected budget is
  the smallest combination for which mean aligned JS similarity ≥ 0.95 AND
  dominant-topic agreement ≥ 0.95 relative to the next larger combination in
  the grid. If no combination satisfies this before reaching the largest grid
  cell (`passes=50, iterations=1200`), that largest cell is used and the
  non-convergence is reported explicitly rather than extrapolated.
- Total fits per representation: (14 + 16) × 3 × 5 = **450** (900 across both
  representations).

Alpha, eta, passes, and iterations are frozen after this stage and are not
revisited except via a documented protocol amendment (§35).

## 11. STAGE 3 — Definitive k-sweep (per representation, fully frozen config)

- `k = 2..20` (19 values, no skipping).
- 20 seeds per k (first 20 of the master list; see §7 checkpoint for possible
  extension to 30).
- Total: 19 × 20 = **380 fits per representation** (760 total).
- Full metric suite per §15 computed for every individual fit, then
  aggregated by k (never selected from a single seed, never selected from the
  mean coherence curve alone).

## 12. STAGE 4 — Diagnostics and multi-criterion candidate selection

Per k: topic-distribution diagnostics (§16 — CV, normalized entropy, Gini,
largest/smallest-topic proportion, max/min ratio), mega-/thin-/zero-topic
flags (§17, inspection triggers not automatic rejection), structural-medoid
selection per k (§19 — Hungarian-aligned JS similarity, medoid not
highest-coherence seed). Pareto-style multi-criterion selection (§18) over
C_v, C_NPMI, stability, diversity, redundancy, zero/thin-topic counts,
dominant-topic concentration, normalized entropy, assignment confidence, and
parsimony identifies the Pareto-optimal set of k values (k values not
dominated on every criterion by another k). **Frozen reduction rule**: if the
Pareto-optimal set contains more than 4 k values, rank them first by
cross-seed stability (descending) and retain the top-ranked values until at
most 4 remain; if a tie in stability persists at the cutoff, break it by
parsimony (smaller k preferred). This yields **2–4 finalist k values per
representation**. Cross-k topic persistence (§20) is examined across the
competitive region.

## 13. STAGE 5 — Robustness (finalists only)

For each of the 2–4 finalists per representation:

- **Subsampling** (§21): 80% of studies, no replacement, **100 repetitions**,
  same sampled study-ID set reused across all comparison metrics within a
  repetition. **Seed discipline (frozen)**: every refit for a given finalist
  uses that finalist's own structural-medoid seed (§19) as the fixed
  `LdaModel` `random_state` for all 100 repetitions — only the sampled
  document subset varies, so the experiment isolates sensitivity to document
  removal rather than conflating it with random-initialization variance. The
  100 *sampling* seeds (which control which 80% of study IDs are drawn each
  repetition, via a fixed `numpy.random.default_rng`) are the integers 1
  through 100 inclusive, identical across all finalists and both
  representations, recorded in
  `results/{metadata,fulltext}/subsampling_seeds.csv`. Metrics: aligned JS
  similarity, ARI, NMI, prevalence/size/entropy variability, thin-topic
  emergence frequency. Topic-word stability reported separately from
  document-assignment stability; low ARI is never called "robust."
- **Training-effort sensitivity** (§22): frozen budget vs. `passes=100,
  iterations=2000`, same seed/dictionary, aligned JS + dominant-topic
  agreement.
- **Dictionary sensitivity** (§23): refit at immediately neighbouring
  thresholds from the Stage-1 grid.
- **(Full text only) Length sensitivity** (§24, mandatory): correlation
  between document length and dominant-topic confidence/topic probability;
  a length-balanced sensitivity representation using a **predefined token cap
  per document, fixed before this run** (cap = the corpus's Stage-0 IQR upper
  bound, i.e. Q3 + 1.5×IQR of raw token counts, rounded to the nearest 500 —
  computed from the length audit in §4, not chosen after seeing topic
  results). **Cap application (frozen, deterministic, section-proportional)**:
  for documents exceeding the cap, tokens are drawn proportionally from each
  retained section (Introduction, Background/Related Work, Methodology,
  Results, Discussion, Conclusion) in proportion to that section's share of
  the document's substantive token count, using fixed-stride systematic
  sampling within each section (never truncation to the first N tokens, which
  would systematically over-represent Introduction/Related Work). For
  documents where §3's section detection was `low_confidence`, tokens are
  instead sampled evenly across the entire retained document body using the
  same fixed-stride systematic method (stride = floor(document_token_count /
  cap)). Documents under the cap are unchanged. Compared to the original
  full-text model via JS similarity, dominant-topic agreement, ARI, NMI,
  prevalence change. Reported even if it shows the model is sensitive to
  length.

## 14. STAGE 6 — Semantic interpretation packets and blinded human evaluation

- **Internal** interpretation packets (§25) for every finalist topic: top-20
  probability terms, top-20 FREX/exclusive terms, 10 highest-loading studies
  (title, abstract, probability), probability-based prevalence, neutral
  `Topic 0/1/…` labels only. These are the analyst-facing packets and are not
  shown to raters.
- **Rater-facing** blinded comparison packets (§26), derived from the
  internal packets with prevalence and all quantitative information removed:
  per topic, only top-20 probability terms, top-20 FREX terms, and the 10
  highest-loading study titles/abstracts are shown — no probability values,
  no prevalence, no topic-size information. What is withheld: the numeric
  `k` label, seed, dictionary/prior/training configuration, all quantitative
  metrics (§15), and model identity. What is *not* claimed to be hidden: the
  number of topics presented for a given candidate model is inherently
  visible to the rater simply by counting the packet's sections, since k
  cannot be concealed while still presenting all of a model's topics — this
  plan states explicitly that only the *label* `k` and the metrics behind it
  are withheld, not the observable topic count. Models are randomized to
  `Model A/B/C`, extended to `Model A/B/C/D` if four finalists survive
  Stage 4's reduction rule; topics randomized in order within each model.

**Execution pauses here.** Per the human-rater decision above, scoring
(coherence/interpretability/distinctiveness/specificity, 1–5, plus proposed
labels and over-broad/over-narrow/overlap flags) is completed independently
by two human raters outside this session. Word/document intrusion tasks
(§27) are prepared as optional supplementary evidence with a private answer
key. Nothing past this point (final model selection confirmation, label
reconciliation, cross-representation comparison, manuscript text) executes
until rating data is supplied back.

## 15. Cross-representation comparison (after both representations frozen and rated)

Rectangular Hungarian alignment over shared vocabulary (§30): JS similarity,
cosine similarity, top-20 Jaccard, matched/unmatched topics, ARI, NMI,
dominant-topic contingency matrix. Disagreement is not interpreted as model
failure; RQ1–RQ4 is consulted only as an exploratory post-freeze comparison
(§31), never to validate the LDA.

---

## Deliverables checklist (created progressively, not upfront)

`corpus/corpus_audit.{csv,md}`, `corpus/metadata_documents.csv`,
`extraction/fulltext_extraction_report.{csv,md}`, `preprocessing/lemma_audit.md`,
`results/{metadata,fulltext}/dictionary_sweep.csv`, per-stage figures per §32,
`reports/METADATA_LDA_REPORT.md`, `reports/FULLTEXT_LDA_REPORT.md`,
`reports/ROBUSTNESS_REPORT.md`, `reports/HUMAN_VALIDATION_REPORT.md`,
`reports/CROSS_REPRESENTATION_REPORT.md`, `reports/FINAL_LDA_REPORT.md`,
`reports/FROZEN_MANUSCRIPT_VALUES.md`. Reproducibility metadata (§36: package
versions, seeds, corpus/model hashes) captured in `config/` and referenced from
every report.

## Explicit acknowledgement of Master Prompt §40

This plan is designed to be capable of producing any scientifically supported
outcome, including: different k for metadata vs. full text, unequal topic
sizes, moderate rather than high coherence, rater disagreement, unstable
assignments, length-sensitivity in full text, and asymmetric robustness
between representations. Nothing in this plan will be altered after seeing
results except through a documented, rationale-bearing protocol amendment
(§35), which will itself be logged in `reports/FROZEN_MANUSCRIPT_VALUES.md`.

---

**Next step**: on approval of this document, Stage 0 (corpus audit + metadata
extraction + full-text extraction + document-length audit) executes first,
since Stages 1–3 cannot begin without its outputs. Stage 1 fitting does not
begin until Stage 0's deliverables (§1–4 above) are generated and the corpus
count is reconfirmed at exactly 66.
