# Metadata LDA Report (Analysis A)

Title + abstract + author keywords (where available) for the 66 primary
studies. Preprocessed, modelled, and evaluated fully independently of the
full-text analysis, per the frozen plan.

## 1. Frozen configuration (Stages 1-2)

| Parameter | Value |
|---|---|
| Domain-term handling | HF-B (generic filler list removed) |
| Phrase representation | Unigram |
| Dictionary | no_below=6, no_above=0.4 |
| Vocabulary size | 208 |
| alpha | 1.0 |
| eta | auto |
| passes / iterations | 20 / 200 |

Selected from a stable region of 33 eligible dictionary configurations (zero
empty documents at every one); bigrams and HF-A were both tested and
rejected because neither cleared the frozen >0.02 coherence / <0.03
stability-loss retention threshold (`results/metadata/stage1_decision.md`).
Priors: auto/auto was not within tolerance of the best-C_v prior, so the
single best prior (alpha=1.0, eta=auto) was used directly, not the
parsimony default (`results/metadata/stage2_decision.md`). Convergence
reached at the smallest tested budget (passes=20, iterations=200; JS=0.968,
dominant-topic agreement=0.978 vs. the next larger grid cell).

## 2. Definitive k-sweep (k=2..20, 20 seeds each, 380 fits)

Full curve in `results/metadata/k_sweep_summary.csv`. Coherence rises and
stability falls roughly monotonically with k; thin/zero-dominance topics are
essentially absent through k=10 and become severe beyond k≈12 (up to 4
zero-dominance and 10 very-thin topics at k=20) — see
`results/metadata/stage4_candidates.md` for the full per-k flag table.

**15 of the 19 tested k values were Pareto-optimal**
({2,3,4,5,6,7,8,9,10,12,13,14,16,17,18}) — the Pareto criterion alone did
not isolate a small candidate set; it excluded only 4 dominated k values
(11, 15, 19, 20). The pre-specified finalist-reduction rule then ranked the
15 Pareto-optimal k values by cross-seed stability and cut at 4, yielding
**k=2, 3, 4, 5**. Because cross-seed stability generally decreases as topic
count increases (visible in `results/metadata/k_sweep_summary.csv`), this
stability-first reduction rule tends to favour lower-dimensional, more
parsimonious solutions. This is not treated as a methodological flaw — the
rule was fixed before the definitive sweep was run — but it is stated
explicitly here rather than presenting k=2-5 as though the Pareto frontier
itself had isolated exactly those values.

## 3. Final selected model: k=4

**Reason for selection:** k=4 was the unanimous choice of both independent
human raters after blinded comparison against k=2, k=3, and k=5 (see
`reports/HUMAN_VALIDATION_REPORT.md`), consistent with its strong standing
in the quantitative multi-criterion evidence (lowest redundancy among the
Pareto-reduced finalists after k itself is accounted for, zero thin/zero
topics, best-balanced topic sizes of the four). This was not a
highest-coherence selection (k=5 has higher raw C_v among the finalists) nor
a most-balanced-wins selection — it reflects the totality of evidence per
plan §18/§34.

- Structural-medoid seed: **1212** (of 20 fitted seeds at k=4)
- Mean C_v: **0.3584** (SD 0.0485)
- Mean C_NPMI: **-0.1638** (SD 0.0146)
- Cross-seed stability: **0.5815** (SD 0.0513)
- Topic diversity (top-25): **0.8490**
- Redundancy (top-20 Jaccard, mean pairwise): **0.0394**; cosine: **0.2771**
- Dominant-study counts: **[22, 16, 15, 13]** (Topics 0-3); min=13, max=22, ratio=1.69
- Zero-dominance topics: **0**; topics with <5 dominant studies: **0**
- Probability-based prevalence: **[0.292, 0.242, 0.242, 0.225]**
- Normalized entropy: **0.9857**; Gini: **0.106**; CV of dominant counts: **0.235**
- Largest/smallest topic proportion: **33.3% / 19.7%**
- Mean assignment confidence (max topic probability): **0.719**; proportion
  <0.40: 1.5%, 0.40-0.60: 22.7%, >0.60: 75.8%

## 4. Robustness (finalist k=4, medoid seed 1212)

- **80% subsampling, 100 reps** (medoid seed fixed, sampling seeds 1-100):
  aligned JS mean=0.812 (SD 0.032), ARI mean=0.806 (SD 0.091), NMI
  mean=0.813; thin-topic emergence in 2/100 resamples.
- **Training-effort sensitivity** (passes=20/iter=200 vs. passes=100/iter=2000,
  same seed/dictionary): JS=0.884, dominant-topic ARI=0.929, NMI=0.918 —
  strong agreement, the model is not training-budget-limited.
- **Dictionary-neighbour sensitivity** (no_below=5/no_above=0.4 and
  no_below=6/no_above=0.5): JS 0.552 and 0.517; dominant-topic ARI 0.236 and
  0.152. Topic-word structure is moderately but not highly robust to small
  dictionary changes; document-level assignment is more sensitive still —
  reported honestly, not described as "robust" (plan §21).

Full detail: `results/metadata/subsampling_k4.csv`,
`training_effort_sensitivity.csv`, `dictionary_sensitivity.csv`.

## 5. Final topics

Reconciled labels per `reports/HUMAN_VALIDATION_REPORT.md`; full FREX/top-term/
highest-loading-study detail in `results/metadata/interpretation_packet_k4.md`.

**Topic 0 — API/Code Hallucination: Benchmarks and Mitigation** (dominant
for 22 studies, 29.2% prevalence). Top terms: hallucination, api, propose,
benchmark, development, prompt, class, requirement. Representative:
"Towards Mitigating API Hallucination in Code Generated by LLMs..." (S70,
p=0.936), "De-Hallucinator..." (S26, p=0.925), "CloudAPIBench..." (S51,
p=0.892).

**Topic 1 — AI-Generated Feedback in Programming Education** (dominant for
16 studies, 24.2% prevalence). Top terms: student, feedback, performance,
quality, education, learning, course. Representative: "Bridging the
Theory-Practice Gap..." (S16, p=0.883), "Automating Human Tutor-Style
Programming Feedback..." (S13, p=0.879).

**Topic 2 — Developer Trust and Experience with AI Coding Assistants**
(dominant for 15 studies, 24.2% prevalence). Top terms: tool, copilot,
assistant, participant, developer, experience, trust, community.
Representative: "AI chatbots in programming education..." (S06, p=0.943),
"'It would work for me too'..." (S62, p=0.935).

**Topic 3 — Empirical Code Correctness, Testing, and Non-Determinism**
(dominant for 13 studies, 22.5% prevalence). Top terms: problem, test,
solution, issue, correct, dataset, empirical, non[-determinism].
Representative: "No Need to Lift a Finger Anymore?..." (S50, p=0.942),
"Fight Fire with Fire..." (S43, p=0.905). Both human raters independently
flagged this as the least specific of the four topics — a shared limitation
of generic evaluation vocabulary, not an artifact of the k=4 choice
specifically (the same pattern recurs in every candidate model's analogous
topic).

## 6. Complementary, not confirmatory

This analysis provides a data-driven representation of recurring lexical
structure in the metadata corpus. It is not used to validate RQ1-RQ4, and
RQ1-RQ4 categories were never consulted in preprocessing, modelling, or
k-selection.
