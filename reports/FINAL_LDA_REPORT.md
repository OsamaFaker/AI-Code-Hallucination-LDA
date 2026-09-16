# Final LDA Report — Dual-Representation Re-Analysis of 66 Primary Studies (RQ5)

**Manuscript:** "The Anatomy of a Phantom: A Socio-Technical Synthesis of AI Code Hallucinations."

This report consolidates the complete, prospectively-protocolled, data-driven LDA re-analysis.
Full detail is in `reports/METADATA_LDA_REPORT.md`, `FULLTEXT_LDA_REPORT.md`,
`CROSS_REPRESENTATION_REPORT.md`, `ROBUSTNESS_REPORT.md`, and every cited `results/`/`data/`/
`preprocessing/` file. Every number below is traceable to a generated file (no manually typed
result); see `results/validation_report.txt` for automated consistency checks and
`reports/FINAL_MANUSCRIPT_TRANSFER_TABLE.md` for the manuscript-ready numbers table.

## What was done

- **Corpus:** exactly 66 primary studies (5 secondary studies documented and excluded
  throughout — `corpus/corpus_audit.md`).
- **Two independent representations**, each with its own frozen preprocessing
  (`protocol/LDA_66_dual_representation_protocol.md`, hashed at
  `protocol/protocol_sha256.txt`), its own systematic dictionary-threshold grid (36 cells ×
  pilot k × 5 seeds), its own training-budget/prior pilot, its own domain-term and phrase
  sensitivity screens, and its own definitive sweep (k=2–20 × 20 seeds = 380 models each, 760
  total for the definitive stage alone; every model saved under `models/`).
- **Model selection** used a joint Pareto-front + documented-equivalence + parsimony rule
  (never coherence alone, never the max-coherence seed) — see
  `results/{rep}/k_selection_decision.json` and the amendment log
  (`protocol/protocol_amendments.md`) for two transparent mid-run corrections: first, after the
  rule initially selected a degenerate k=2 solution for the metadata representation; second,
  after the numeric k≥4 floor introduced by that first correction was itself judged to need
  independent justification and was replaced by a descriptive, candidate-by-candidate
  admissibility comparison (`reports/METADATA_FINAL_K_VALIDATION.md`) plus a cross-k
  topic-persistence analysis for full text (`reports/FULLTEXT_FINAL_K_VALIDATION.md`) and
  completed blinded human validation (see below). **k=4 (metadata) and k=8 (full text) are
  FINAL.**
- **Cross-seed stability**, **structural-medoid seed selection**, **80%×100 subsampling**,
  **training-effort**, **dictionary**, **phrase**, and **domain-term sensitivity** were all
  run for both representations; full-text additionally received a **document-length
  diagnostic and length-balanced sensitivity model** (Section 24).
- **Human validation** is complete: two independent raters, blinded to model identity, k, and
  any AI-drafted label, rated every candidate/final topic
  (`reports/HUMAN_VALIDATION_REPORT.md`). For metadata, the two raters preferred different k
  values from each other and from k=4 — **human validation did not confirm k=4**; k=4 was
  retained primarily on quantitative-parsimony grounds. For full text, human ratings
  corroborate the quantitative cross-k persistence result (combined coherence ≈4.06/5,
  interpretability ≈4.00/5, distinctiveness ≈3.88/5). Final topic labels were subsequently
  **researcher-reconciled** from both raters' independently proposed labels
  (`reports/TOPIC_LABEL_RECONCILIATION.md`, `human_validation/FINAL_TOPIC_LABELS.csv`) — not
  claimed as verbatim rater consensus. Raw rater files are preserved unaltered in
  `human_validation/Human_Result/`.

## Headline results

| | Analysis A (Metadata) | Analysis B (Full text) |
|---|---:|---:|
| Selected k | **4** | **8** |
| Vocabulary size | 397 | 2,626 |
| Representative (medoid) seed | 14 | 2 |
| Mean C_v / C_NPMI at selected k | 0.40 / −0.10 | 0.40 / −0.04 |
| Mean cross-seed stability (JS) | 0.66 | 0.54 |
| Mean topic diversity | 0.84 | 0.77 |
| 80%-subsampling mean topic similarity (JS) / ARI | 0.59 / 0.13 | 0.52 / 0.22 |

k_A ≠ k_B is a legitimate, expected result (protocol Section 20/26), not forced to agree.
Coherence values are reported descriptively and never characterized as "high," "strong," or
"excellent" — no external coherence benchmark for this domain/corpus size is invoked.

**Final reconciled topic labels** (`reports/TOPIC_LABEL_RECONCILIATION.md`):

| Metadata (k=4) | Full text (k=8) |
|---|---|
| T0: AI Code Verification, Vulnerability, and Developer Trust | T0: Developer Trust and Experience with AI Coding Assistants |
| T1: Requirements-Driven Prompting and Code Generation | T1: Package Hallucination and Supply-Chain Security Risks |
| T2: AI in Programming Education and Adoption | T2: Security and Safety-Critical Code Generation Benchmarks |
| T3: API/Dependency Hallucination Mitigation | T3: Hallucination Detection and Mitigation Methods |
| | T4: LLM Coding Proficiency and Programming Tasks |
| | T5: Programming Education, Learning, Feedback, and Assessment |
| | T6: Code Quality, Vulnerability, Complexity, and Non-Determinism |
| | T7: Bug Taxonomies and Practitioner-Reported Code Issues |

## Cross-representation relationship

All four metadata topics show partial correspondence with a full-text topic, most clearly for
**API/Dependency Hallucination Mitigation** (metadata T3 ↔ full-text T3) and **AI in
Programming Education and Adoption** (metadata T2 ↔ full-text T5, "Programming Education,
Learning, Feedback, and Assessment") — themes plausibly visible even from titles/abstracts.
Full text additionally surfaces four topics with no metadata counterpart — **Developer Trust
and Experience with AI Coding Assistants** (T0), **Package Hallucination and Supply-Chain
Security Risks** (T1), **LLM Coding Proficiency and Programming Tasks** (T4), and **Bug
Taxonomies and Practitioner-Reported Code Issues** (T7) — which *may* reflect content only
available at the methodology/results/discussion
level, but this **cannot be statistically distinguished** from the effect of full text's larger
selected k or its documented sensitivity to document length (see below); we do not claim a
causal explanation. Overall document-assignment agreement across representations is modest
(ARI=0.19, NMI=0.30), and even the closest-matching topic pairs show only moderate similarity
(JS similarity 0.18–0.23). Given this and the robustness asymmetry below, **we treat the
metadata analysis as the primary RQ5 result and the full-text analysis as a secondary
representation-sensitivity check**, not two equally-weighted alternatives. Full detail:
`reports/CROSS_REPRESENTATION_REPORT.md`.

## Key limitation: full-text length sensitivity

The most consequential robustness finding is that the full-text model shows a non-trivial
sensitivity to document length (length-balanced sensitivity model: only 33% dominant-topic
agreement with the full model; length weakly correlates with topic-assignment confidence,
r=0.25, p=0.043). Some of the metadata/full-text divergence documented above may partly
reflect this length sensitivity rather than a pure granularity effect. This is reported as an
open limitation, not resolved by re-weighting or re-selecting k. See
`reports/ROBUSTNESS_REPORT.md`.

## Relationship to the manual RQ1–RQ4 synthesis

RQ1–RQ4 categories were not used at any stage before both models were frozen (protocol
Section 30/20). The LDA analysis provides a **complementary exploratory representation** of
thematic structure; it does not, and is not claimed to, validate the manual mapping. Any
qualitative resemblance between LDA topics and RQ1–RQ4 categories (e.g., the API-hallucination
topic's overlap with RQ2/RQ3 causal and mitigation categories) should be read as a
cross-check of *coverage*, not as independent statistical confirmation.

## What remains before manuscript inclusion

Blinded human validation (metadata k-candidates and full-text final topics), label
reconciliation, and repository freezing are now **complete** — see
`reports/HUMAN_VALIDATION_REPORT.md`, `reports/TOPIC_LABEL_RECONCILIATION.md`,
`FINAL_ANALYSIS_FREEZE.md`. What remains is out of scope for this repository-freeze task:

1. **RQ5/methodology manuscript prose rewrite** — to be done as a separate subsequent task,
   drawing only from `reports/FROZEN_MANUSCRIPT_VALUES.md`,
   `human_validation/FINAL_TOPIC_LABELS.csv`, `reports/HUMAN_VALIDATION_REPORT.md`,
   `reports/FIGURE_INDEX.md`, and the frozen figures.
2. Optional: NMF/BERTopic exploratory cross-check (protocol Section 27) was not run in this
   pass; it is explicitly optional and would only be used to assess recurrence of broad themes
   under different modeling assumptions, never to select the reported LDA result.
3. Reviewer-response matrix with full point-by-point mapping:
   `reports/REVIEWER_LDA_RESPONSE_MATRIX.md`.
4. Final decision table: `reports/FINAL_K_DECISION_TABLE.md`.

## Traceability

Every quantitative claim in this report cites a specific file under `results/`, `data/`,
`preprocessing/`, or `human_validation/`. `results/validation_report.txt` records automated
checks (study counts, model counts, seed counts, medoid-seed consistency, etc.), all passing
at generation time.
