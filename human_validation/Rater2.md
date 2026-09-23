# Independent Rater Scores — Blinded Topic Model Comparison

Rater: Osama. Scored independently before opening any ANSWER_KEY file. Scale 1 (poor) – 5 (excellent).

---

## PACKET 1: METADATA (title/abstract-based topics)

### Model A (k=4)

| Topic | Coh | Interp | Dist | Spec | Label |
|---|---|---|---|---|---|
| 1 | 4 | 4 | 4 | 4 | API/Code Hallucination Benchmarks & Mitigation |
| 2 | 3 | 3 | 3 | 2 | Empirical Code Correctness & Testing |
| 3 | 4 | 4 | 3 | 4 | Developer Trust & Experience with AI Coding Assistants |
| 4 | 4 | 4 | 4 | 4 | AI-Generated Feedback in Programming Education |

- **T1** — Benchmark/mitigation papers for API and package hallucination (CloudAPIBench, COLLU‑BENCH, De‑Hallucinator). Clean, well-formed.
- **T2** — Empirical correctness/testing/non-determinism studies. Over-broad; generic function-word terms ("problem," "solution," "issue") give it a catch-all feel. Mild overlap with T1.
- **T3** — Copilot/ChatGPT adoption, trust, community influence. Overlaps with T4 (some education-adjacent papers appear in both).
- **T4** — GPT-4/feedback/grading in programming courses. Well-formed; overlaps with T3.

**Model A overall:** Coherence 4 / Interpretability 4 / Distinctiveness 3. No over-merging. Mild over-splitting risk between T3/T4 (both education-adjacent) but the trust-vs-feedback distinction is real. **Best-balanced model in this packet.**

### Model B (k=3)

| Topic | Coh | Interp | Dist | Spec | Label |
|---|---|---|---|---|---|
| 1 | 4 | 4 | 4 | 4 | API/Code Hallucination Benchmarks & Mitigation |
| 2 | 3 | 3 | 3 | 2 | Programming Education & LLM Code Quality Evaluation |
| 3 | 4 | 4 | 4 | 4 | Developer Trust & Experience with AI Coding Assistants |

- **T1, T3** — essentially identical to Model A's T1 and T3.
- **T2** — collapses Model A's T2 (correctness/testing) and T4 (education/feedback) into one topic. Internally heterogeneous; two distinguishable themes forced together.

**Model B overall:** Coherence 3.5 / Interpretability 3.5 / Distinctiveness 4. **Over-merging flag: T2 = Model A's T2+T4 merged** — recommend splitting.

### Model C (k=2)

| Topic | Coh | Interp | Dist | Spec | Label |
|---|---|---|---|---|---|
| 1 | 2 | 3 | 2 | 1–2 | AI Coding Tools: Education, Trust & Human Use |
| 2 | 3 | 3 | 2 | 2 | Hallucination, Benchmarks & Code Testing |

Essentially a coarse binary split of the whole corpus (technical/hallucination vs. everything human-facing). Each topic is internally heterogeneous ("AI code stuff" territory).

**Model C overall:** Coherence 2.5 / Interpretability 3 / Distinctiveness 2. **Severe over-merging** — collapses distinctions Models A/B/D all recover. Least useful model in this packet.

### Model D (k=5)

| Topic | Coh | Interp | Dist | Spec | Label |
|---|---|---|---|---|---|
| 1 | 3 | 3 | 3 | 2 | LLM Code-Generation Capability & Correctness Evaluation |
| 2 | 4 | 4 | 3 | 4 | API Hallucination Mitigation Techniques |
| 3 | 4 | 4 | 3 | 3 | Hallucination Benchmarks & Taxonomies |
| 4 | 4 | 4 | 4 | 4 | Developer Trust & Experience with AI Coding Assistants |
| 5 | 3 | 3 | 3 | 3 | Programming Education: Feedback, Assessment & Empirical Evaluation |

- **T2 vs T3** — both hallucination-focused; share "hallucination"/"api" in top terms. T2 leans mitigation-technique, T3 leans benchmark/taxonomy — a real but narrow distinction. **Overlap flag: T2↔T3.**
- **T1 vs T5** — both touch evaluation/empirical/quality; T1 is code-capability-focused, T5 is course/feedback-focused. **Overlap flag: T1↔T5.**
- **T4** — clean, matches A/B's Copilot-trust topic.

**Model D overall:** Coherence 3.5 / Interpretability 3.5 / Distinctiveness 3. **Over-splitting flag:** splits Model A's single hallucination topic into T2+T3, and creates redundancy between T1/T5. Most granular but with two redundant pairs.

### Metadata packet — preferred model: **Model A**
Best balance of coherence/specificity without the redundancy Model D introduces (T2/T3 and T1/T5 splits) or the collapsing Model B/C exhibit. Model A's only weakness is T2's genericness, which is a specificity problem shared by every model's "correctness/testing" topic, not one A introduced.

---

## PACKET 2: FULL-TEXT (technical/methods-vocabulary topics)

General note: full-text topics carry much more technical jargon (HumanEval, MBPP, cyclomatic, determinism/temperature, package/dependency) than the generic discourse terms in the metadata packet, giving sharper specificity but occasional interpretability friction from jargon and apparent tokenization noise ("a.", "def", "p2/p4/p7" participant-ID leakage).

### Model A (k=2)

| Topic | Coh | Interp | Dist | Spec | Label |
|---|---|---|---|---|---|
| 1 | 4 | 3 | 5 | 5 | Hallucination Detection & Technical Benchmarking (Determinism, Package/API) |
| 2 | 2 | 3 | 5 | 2 | Human & Educational Dimensions of AI Coding Tools |

Trivial distinctiveness at k=2 (complementary halves of the corpus). T2 merges education, trust, community, and security-attack content into one broad bucket. **Severe over-merging on the T2 side.** Too coarse to be useful as-is.

### Model B (k=3)

| Topic | Coh | Interp | Dist | Spec | Label |
|---|---|---|---|---|---|
| 1 | 3 | 3 | 3 | 3 | Code Repair, Verification & Determinism (Benchmark Evaluation) |
| 2 | 3 | 4 | 4 | 3 | Programming Education: Instruction, Grading & Trust |
| 3 | 5 | 4 | 3 | 5 | Package/Dependency Hallucination: Taxonomy & Mitigation |

- **T1 vs T3** — share benchmark vocabulary (humaneval, javascript, buggy, mbpp) — **overlap flag**, though thematically distinct (repair/verification vs. package-hallucination taxonomy/mitigation).
- **T3** is the strongest single topic in the full-text packet: tight, specific, clearly nameable (taxonomy, mitigation, RAG, agent).
- **T2** bundles security/"attack" terms with pure grading/instruction content — minor heterogeneity, consistent with a recurring cross-model pattern in this corpus.

**Model B overall:** Coherence 3.7 / Interpretability 3.7 / Distinctiveness 3.3. Clean three-way split (technical-repair / education / package-hallucination); mild T1↔T3 vocabulary overlap.

### Model C (k=5)

| Topic | Coh | Interp | Dist | Spec | Label |
|---|---|---|---|---|---|
| 1 | 4 | 4 | 3 | 4 | Classroom & Instructor Perspectives on AI Coding Tools (Qualitative) |
| 2 | 4 | 3 | 3 | 4 | Hallucination Detection Signals: Determinism & Syntactic/Factual Conflict |
| 3 | 3 | 3 | 4 | 3 | Security Vulnerabilities & Assessment/Grading of AI-Generated Code |
| 4 | 4 | 4 | 3 | 4 | Package/Dependency Hallucination & Agentic Code Generation |
| 5 | 5 | 4 | 4 | 5 | Competitive-Programming Benchmark Evaluation (LeetCode Difficulty & Multi-Round Fixing) |

- **T2 vs T4** — both technical hallucination clusters sharing "humaneval"/"hallucinate" — **overlap flag**, candidate for merging.
- **T3** — bundles two threads (security/attack vs. grading/rubric) that don't obviously belong together — **possible split candidate**, or at minimum flagged as heterogeneous.
- **T1** — clean, qualitative classroom/instructor cluster; mild overlap with T3's teacher/grade terms.
- **T5** — the standout topic of the whole full-text packet: tight, highly specific (LeetCode, difficulty levels, C++, competition metrics).

**Model C overall:** Coherence 3.8 / Interpretability 3.6 / Distinctiveness 3.4. Finest-grained model; T5 is excellent, but T2/T4 redundancy and T3's internal heterogeneity are real costs of the extra granularity.

### Model D (k=4)

| Topic | Coh | Interp | Dist | Spec | Label |
|---|---|---|---|---|---|
| 1 | 3 | 3 | 3 | 3 | Practitioner Perspectives on Package Hallucination & Malicious Code Risk |
| 2 | 4 | 3–4 | 3 | 3 | Code Repair, Verification & Determinism Benchmarking |
| 3 | 3 | 4 | 4 | 3 | Programming Education: Instruction, Grading & Trust |
| 4 | 5 | 4 | 3 | 5 | Iterative & Retrieval-Based Hallucination Mitigation (Agentic Methods) |

- **T1** — mixes qualitative practitioner-survey vocabulary (dialogue, sentiment, satisfaction) with technical malicious/package-hallucination vocabulary — heterogeneous, **possible split candidate**.
- **T2** — coarsens what Model C splits into T2 (detection signals) + T5 (competitive-programming/LeetCode) — **under-splitting relative to Model C**.
- **T3** — matches the recurring education/grading/trust topic seen in every model.
- **T4** — the sharpest topic in Model D: retrieval/agent/self-consistency mitigation methods, very specific.

**Model D overall:** Coherence 3.75 / Interpretability 3.5 / Distinctiveness 3.25. Sits between B and C in granularity; T1's heterogeneity is its main weakness, and T2 loses the LeetCode-specific granularity C recovers.

### Full-text packet — preferred model: **Model C**, with **Model B** as a strong, more parsimonious runner-up
C gives the most interpretable fine-grained structure (T5 in particular is excellent, T1 is clean), at the cost of T2/T4 redundancy and a heterogeneous T3. B is more conservative and nearly as good — its package-hallucination topic (T3) is arguably the single tightest topic across either packet — but it forgoes the LeetCode-specific and security-vs-grading distinctions C surfaces. A is too coarse to recommend; D's T1 heterogeneity and its coarsening of C's technical split are its main drawbacks relative to C.

---

## Cross-packet observation
Metadata-packet topics lean on generic discourse/boilerplate terms (propose, demonstrate, exist, framework), which caps specificity even in otherwise coherent topics (e.g., every model's "correctness/testing" topic scores low on specificity). Full-text-packet topics carry far more technical/domain vocabulary (benchmark names, methodology terms), giving sharper specificity and some genuinely excellent topics (Model B/full T3, Model C/full T5) — but at the cost of occasional jargon-interpretability friction and apparent tokenization noise (isolated tokens like "a.", "def", "p2/p4/p7").
