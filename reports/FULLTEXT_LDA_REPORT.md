# Full-Text LDA Report (Analysis B)

Cleaned substantive text (Introduction through Conclusion, references/bios/
affiliations/publisher boilerplate stripped) for the same 66 primary
studies. Preprocessed, modelled, and evaluated fully independently of the
metadata analysis.

## 1. Frozen configuration (Stages 1-2)

| Parameter | Value |
|---|---|
| Domain-term handling | HF-A (retain domain terms) |
| Phrase representation | Unigram |
| Dictionary | no_below=6, no_above=0.4 |
| Vocabulary size | 1503 |
| alpha | auto |
| eta | auto |
| passes / iterations | 20 / 200 |

HF-A and HF-B produced *identical* results at this dictionary threshold
(mean_cv=0.3214, vocab=1503 for both) — the no_above=0.4 filter already
excludes the HF-B filler terms as ubiquitous across the 66-document corpus,
so the two conditions converge without the explicit filler list making a
difference (`results/fulltext/stage1_decision.md`). Priors: all 14 tested
prior combinations were within tolerance of the best-C_v prior (a
notably flat coherence landscape), so auto/auto was used as the most
parsimonious choice. Convergence reached at passes=20, iterations=200
(JS=0.959, dominant-topic agreement=0.969).

## 2. Definitive k-sweep (k=2..20, 20 seeds each, 380 fits)

Full curve in `results/fulltext/k_sweep_summary.csv`. **All 19 tested k
values were Pareto-optimal** (no single k dominates another on every
criterion simultaneously) — the Pareto criterion did not narrow the
candidate set at all here. The pre-specified finalist-reduction rule then
ranked all 19 by cross-seed stability and cut at 4, yielding **k=2, 3, 4,
5**. As with metadata, because cross-seed stability generally decreases
with topic count, this stability-first rule mechanically favours
lower-dimensional solutions; this is stated explicitly rather than implying
the Pareto frontier itself isolated these four values (the rule, fixed
before the sweep, is not treated as a flaw, but its effect is disclosed).
Thin/zero-dominance topics are absent through
k=8 and increase steadily beyond that (up to 6 zero-dominance and 16
very-thin topics at k=20) — full flag table in
`results/fulltext/stage4_candidates.md`.

## 3. Final selected model: k=4

**Reason for selection:** unlike the metadata packet, the two human raters
disagreed on full-text (Rater 1 preferred k=4; Rater 2 preferred k=5, with
k=3 as a parsimonious runner-up). k=4 was **retained as the more
conservative multi-criterion solution, not because it was clearly
superior to k=5** — k=5 remained, and remains, a credible alternative with
higher raw coherence and stronger subsampling ARI/NMI. k=4 was selected via
multi-criterion reconciliation, not a vote: it has the lowest topic
redundancy of the three disputed finalists, is markedly more robust to
increased training effort (dominant-topic ARI 0.86 vs. 0.65 at k=3 and 0.78
at k=5 — the largest gap of any comparison in this analysis), matches k=3's
perfect subsampling thin-topic safety (k=5 shows fragility in 7/100
resamples), and is not rejected by either rater. Full reconciliation table
and reasoning in `reports/HUMAN_VALIDATION_REPORT.md`. k=5's genuine
strengths (higher raw coherence, a highly-specific competitive-programming
topic praised by
Rater 2) are preserved as a documented alternative, not discarded.

- Structural-medoid seed: **505** (of 20 fitted seeds at k=4)
- Mean C_v: **0.2957** (SD 0.0271)
- Mean C_NPMI: **-0.2512** (SD 0.0166)
- Cross-seed stability: **0.5913** (SD 0.0296)
- Topic diversity (top-25): **0.9070**
- Redundancy (top-20 Jaccard, mean pairwise): **0.0261**; cosine: **0.2922**
- Dominant-study counts: **[17, 8, 16, 25]** (Topics 0-3); min=8, max=25, ratio=3.13
- Zero-dominance topics: **0**; topics with <5 dominant studies: **0**
- Probability-based prevalence: **[0.266, 0.135, 0.227, 0.372]**
- Normalized entropy: **0.9496**; Gini: **0.197**; CV of dominant counts: **0.421**
- Largest/smallest topic proportion: **37.9% / 12.1%**
- Mean assignment confidence: **0.845**; proportion <0.40: 0%, 0.40-0.60: 13.6%,
  >0.60: 86.4%

Topic 1 (8 dominant studies, the smallest) is comfortably above the plan's
thin-topic threshold (<5) but is the least populated of the four —
consistent with Rater 2's observation that this topic (code repair/
verification/determinism benchmarking) is where a k=5 solution would peel
off a distinct, highly-specific competitive-programming sub-theme.

## 4. Robustness (finalist k=4, medoid seed 505)

- **80% subsampling, 100 reps**: aligned JS mean=0.810 (SD 0.038), ARI
  mean=0.799 (SD 0.099), NMI mean=0.799; thin-topic emergence in **0/100**
  resamples.
- **Training-effort sensitivity** (passes=20/iter=200 vs. passes=100/iter=2000):
  JS=0.905, dominant-topic ARI=0.856, NMI=0.865 — the strongest
  training-effort agreement of any finalist in either representation.
- **Dictionary-neighbour sensitivity** (no_below=5/no_above=0.4 and
  no_below=6/no_above=0.5): JS 0.569 and 0.516; dominant-topic ARI 0.284 and
  0.230. As with metadata, topic-word structure is moderately robust while
  document-level assignment is more sensitive to dictionary threshold
  choice — reported explicitly, not glossed over.

## 5. Document-length sensitivity (mandatory, full text only)

Correlation between raw document length and dominant-topic assignment
confidence, at k=4: **Pearson r=0.358 (p=0.0031)** — a statistically
significant positive association: longer documents tend to receive higher
topic-assignment confidence. This pattern held (with varying strength) at
every finalist k except k=2 (r=0.161, p=0.196, not significant).

Length-balanced sensitivity (2/66 documents exceeded the frozen 15,500-token
cap and were resampled via deterministic section-proportional systematic
sampling, not truncation): topic structure at k=4 remained close to the
original — JS=0.938, dominant-topic ARI=0.945, NMI=0.936, mean absolute
prevalence change small. **Full text is measurably length-sensitive in
assignment confidence, but the topic structure itself is robust to the
length-balancing intervention** — both facts are reported, per plan §24,
rather than suppressing the first because the second looks better.
Full detail: `results/fulltext/length_sensitivity_correlation.csv`,
`length_sensitivity_comparison.csv`.

## 6. Final topics

Reconciled labels per `reports/HUMAN_VALIDATION_REPORT.md`; full FREX/top-term/
highest-loading-study detail in `results/fulltext/interpretation_packet_k4.md`.

**Topic 0 — Programming Education: Instruction, Grading, and Trust**
(dominant for 17 studies, 26.6% prevalence). Top terms: participant,
course, assignment, education, grade, trust, instructor. Representative:
"From Ban It Till We Understand It..." (S42, p≈1.00), "Does ChatGPT Help
With Introductory Programming?" (S29, p≈1.00).

**Topic 1 — Code Repair, Verification, and Determinism Benchmarking**
(dominant for 8 studies, 13.5% prevalence — the smallest topic).
Top terms: round, exercise, vulnerable, similarity, determinism,
javascript, humaneval, temperature. Representative: "No Need to Lift a
Finger Anymore?" (S50, p≈1.00), "Fight Fire with Fire..." (S43, p≈1.00),
"An Empirical Study of the Non-determinism of ChatGPT..." (S09, p≈1.00).

**Topic 2 — Practitioner Perspectives on Package Hallucination and
Security Risk** (dominant for 16 studies, 22.7% prevalence). Top terms:
participant, package, conversation, malicious, dialogue, hallucinate,
practitioner. Representative: "Importing Phantoms: Measuring LLM Package
Hallucination Vulnerabilities" (S66, p≈1.00), "Hallucinating AI Hijacking
Attack..." (S46, p≈1.00). Rater 2 flagged this topic as internally
heterogeneous (qualitative practitioner-survey vocabulary mixed with
technical malicious-package vocabulary) — preserved as a known limitation.

**Topic 3 — Iterative and Retrieval-Based Hallucination Mitigation**
(dominant for 25 studies, 37.2% prevalence — the largest topic). Top
terms: iteration, dependency, conflict, humaneval, retrieval, codegen,
reasoning, agent. Representative: "Chain-of-Programming (CoP)..." (S20,
p≈1.00), "De-Hallucinator..." (S26, p≈1.00), "Towards Mitigating API
Hallucination..." (S70, p≈1.00). Rated highest by both raters (5/5, 5/5
coherence) — the strongest single topic in this representation.

## 7. Known extraction artifacts in the vocabulary

A small number of tokens in the top/FREX term lists (`a.`, `def`, `p4`)
are residual extraction noise — likely participant-ID labels (P1-P7) from
user-study papers and isolated code-listing fragments not fully stripped
by the full-text cleaning pipeline. Noted here for transparency (identified
independently by Rater 2 during blinded scoring); their presence does not
materially affect topic interpretability at the level these labels were
assigned, but is recorded as a limitation of the extraction pipeline rather
than corrected retroactively (per plan §35, no result-driven retuning after
protocol freeze).

## 8. Complementary, not confirmatory

This analysis provides a data-driven representation of recurring lexical
structure in the full-text corpus. It is not used to validate RQ1-RQ4.
