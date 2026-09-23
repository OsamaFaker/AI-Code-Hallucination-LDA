# Human Validation Report

Two raters (Rater 1; Rater 2 = Osama, an author/researcher on this project)
completed the blinded evaluations independently — each scored the blinded
comparison packets (`human_validation/{metadata,fulltext}/blinded_comparison_packet.md`)
before either opened the corresponding `ANSWER_KEY_do_not_share_with_raters.md`,
and neither saw the other's scores before submitting. Because one rater is
a project author, "independent" here describes independence *between*
raters (blinded scoring, no shared knowledge before submission), not
externality to the project — this report does not describe them as
external evaluators.

Raters were blinded to model identity, random seed, dictionary parameters,
priors, training parameters, all quantitative model-selection metrics,
topic prevalence, dominant-study counts, and any previous researcher
labels. The numerical **k label itself** was withheld — but the **number of
topics displayed** for a given candidate model was necessarily observable,
since every topic in a model was shown in full; this is an unavoidable
consequence of presenting complete candidate models for evaluation, not a
blinding failure. Each topic's top-20 probability terms, top-20 FREX terms,
and 10 highest-loading study titles/abstracts were shown.

Full per-topic scores are preserved verbatim in `human_validation/Rater1.md`
and `human_validation/Rater2.md`.

## Metadata packet — blinded label → real k

| Blinded label | Real k | medoid seed |
|---|---|---|
| Model A | 4 | 1212 |
| Model B | 3 | 1212 |
| Model C | 2 | 808 |
| Model D | 5 | 303 |

**Both raters independently preferred Model A (k=4).** Rater 1: "cleanest
separation of concerns without over-merging into catch-alls or over-splitting
into duplicate technical themes." Rater 2: "best-balanced model in this
packet... no over-merging, mild over-splitting risk between T3/T4 but the
trust-vs-feedback distinction is real." This is a clean, unanimous result —
no reconciliation judgment call was required for metadata.

Both raters independently flagged the same weak topic (metadata Topic 3 —
correctness/testing/non-determinism) as the least specific/most generic of
the four (Rater 1 specificity=3, Rater 2 specificity=2), attributing this to
its reliance on generic discourse terms ("problem," "solution," "issue")
rather than a defect specific to k=4 — the same genericness appears in every
candidate model's analogous topic, per both raters.

## Full-text packet — blinded label → real k

| Blinded label | Real k | medoid seed |
|---|---|---|
| Model A | 2 | 404 |
| Model B | 3 | 505 |
| Model C | 5 | 1919 |
| Model D | 4 | 505 |

**Raters disagreed.** Rater 1 preferred Model D (k=4): "well-balanced
4-topic solution. Clear semantic boundaries separate educational deployment,
empirical stability, developer workflows/security, and iterative
mitigation." Rater 2 preferred Model C (k=5), with Model B (k=3) as a
"strong, more parsimonious runner-up" — citing k=5's standout
competitive-programming/LeetCode topic (T5, scored 5/4/4/5) and its
finer-grained recovery of a security-vs-grading distinction that coarser
models blur. Rater 2 did not rank Model D (k=4) first or second, describing
it as sitting "between B and C in granularity," with topic 1's internal
heterogeneity (mixing practitioner-survey vocabulary with technical
malicious/package-hallucination vocabulary) as its main weakness.

This disagreement is reported transparently, not resolved by vote (per plan
§28, human judgment is complementary evidence, integrated with quantitative
quality, robustness, and parsimony — never a majority rule with n=2 raters
in any case).

### Reconciliation (full-text k)

| Criterion | k=3 | k=4 | k=5 |
|---|---|---|---|
| mean C_v | 0.279 | 0.296 | 0.311 |
| mean stability | 0.636 | 0.591 | 0.552 |
| mean diversity | 0.941 | 0.907 | 0.880 |
| redundancy (Jaccard, lower better) | 0.045 | **0.026** | 0.029 |
| zero/thin(<5) topics, full corpus | 0/0 | 0/0 | 0/0 |
| subsampling JS (100 reps) | 0.821 | 0.810 | 0.794 |
| subsampling ARI / NMI | 0.724 / 0.716 | 0.799 / 0.799 | **0.831 / 0.857** |
| thin-topic emergence under subsampling | 0/100 | 0/100 | 7/100 |
| training-effort JS | 0.844 | **0.905** | 0.900 |
| training-effort ARI / NMI | 0.652 / 0.620 | **0.856 / 0.865** | 0.784 / 0.799 |
| cross-k persistence from previous k (JS) | 0.774 (3←2... n/a) | 0.774 (4←3) | 0.607 (5←4) |
| rater #1 preference | — | 1st | — |
| rater #2 preference | 2nd (runner-up) | — | 1st |

k=5 wins on raw coherence and on subsampling document-assignment agreement,
and Rater 2's qualitative case for it (the LeetCode/competitive-programming
topic) is genuine. But k=4 is the strongest all-round performer on the
criteria that most directly probe overfitting and reliability: it has the
**lowest topic redundancy** of the three, is **dramatically more robust to
increased training effort** (ARI 0.86 vs. 0.65 at k=3 and 0.78 at k=5 — the
biggest gap in the whole comparison), and matches k=3's perfect 0/100
thin-topic safety under subsampling where k=5 shows fragility in 7% of
resamples. The k=4→5 cross-k persistence (JS=0.607) is also markedly lower
than the k=2→3 and k=3→4 transitions (JS≈0.77), indicating k=5 is not simply
"k=4 plus one clean additional split" but a more substantial restructuring —
which, combined with its lower stability and higher redundancy, argues for
caution before treating it as a strict improvement.

**Decision: k=4 for full-text, retained as the more conservative
multi-criterion solution — not as the clearly superior one.** k=5 remains
a credible alternative: it has higher raw C_v, stronger subsampling ARI/NMI
(0.831/0.857 vs. k=4's 0.799/0.799), was Rater 2's first choice, and
contains a highly specific competitive-programming topic with no analogue
at k=4. k=4 was preferred because it has lower redundancy, higher
cross-seed stability, higher diversity, stronger training-effort robustness,
zero thin-topic emergence across 100 subsamples (vs. 7/100 for k=5), was
Rater 1's first choice, and was not rejected as incoherent by Rater 2 (who
placed it as a reasonable middle ground, not a poor model). k=4 was
selected through this reasoned integration of criteria, not by coherence
maximum, not by human vote, and not because it was judged unambiguously
better — it was not. k=5's genuine strengths are preserved as a documented
limitation/alternative, not discarded.

**This was not majority-vote arbitration.** Metadata converged unanimously.
Full-text did not, and the k=4 decision rests on the quantitative robustness
profile plus Rater 1's endorsement and Rater 2's non-rejection, exactly as
plan §28 requires — never "highest coherence wins" (that would be k=5) and
never "most balanced wins" (arguably k=3 on some diagnostics).

## Reconciled final topic labels

Derived from both raters' proposed labels, high-probability terms, FREX
terms, and highest-loading studies (plan §29). Label reconciliation did not
alter the model, topic-word distributions, study assignments, or ratings.

### Metadata, k=4

| Topic | Reconciled label | Rater 1 label | Rater 2 label |
|---|---|---|---|
| 0 | API/Code Hallucination: Benchmarks and Mitigation | API Hallucination Mitigation | API/Code Hallucination Benchmarks & Mitigation |
| 1 | AI-Generated Feedback in Programming Education | AI in Programming Education | AI-Generated Feedback in Programming Education |
| 2 | Developer Trust and Experience with AI Coding Assistants | Developer Trust & Tool Adoption | Developer Trust & Experience with AI Coding Assistants |
| 3 | Empirical Code Correctness, Testing, and Non-Determinism | LLM Code Generation Quality & Benchmarking | Empirical Code Correctness & Testing |

### Full text, k=4

| Topic | Reconciled label | Rater 1 label | Rater 2 label |
|---|---|---|---|
| 0 | Programming Education: Instruction, Grading, and Trust | Higher Education Instruction & Grading | Programming Education: Instruction, Grading & Trust |
| 1 | Code Repair, Verification, and Determinism Benchmarking | Empirical Verification & Output Stability | Code Repair, Verification & Determinism (Benchmark Evaluation) |
| 2 | Practitioner Perspectives on Package Hallucination and Security Risk | Developer Practice & Package Security Risks | Practitioner Perspectives on Package Hallucination & Malicious Code Risk |
| 3 | Iterative and Retrieval-Based Hallucination Mitigation | Iterative Refinement & Hallucination Mitigation | Iterative & Retrieval-Based Hallucination Mitigation (Agentic Methods) |

Full-text Topic 2 was independently flagged by Rater 2 as internally
heterogeneous (qualitative practitioner-survey vocabulary mixed with
technical malicious/package-hallucination vocabulary) and by Rater 1 as
part of a well-separated 4-topic structure; both are preserved as
complementary evidence in `reports/FULLTEXT_LDA_REPORT.md`.

## Word/document intrusion validation

Not performed — optional per plan §27, deprioritized given the strength of
signal already available from two independent full-packet raters and the
quantitative robustness suite. Noted here as a documented scope decision,
not a silent omission.
