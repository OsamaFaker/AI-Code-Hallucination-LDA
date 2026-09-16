# Topic Label Reconciliation

> Two evaluators independently assessed and labeled the LDA topics. Their original ratings and
> proposed labels were retained unchanged. Following completion of the independent assessment,
> the researchers reconciled the final descriptive labels by examining the semantic overlap
> between the two proposals together with the highest-probability terms, FREX terms, and
> highest-loading studies. This reconciliation affected only the descriptive topic names and
> did not alter the fitted models or quantitative results.

## Process

1. Two evaluators independently rated and labeled every candidate/final topic, blinded to
   model identity, k, and any AI-drafted label (`human_validation/metadata_candidate_blinded/`,
   `human_validation/fulltext_final_blinded/`).
2. Original ratings and labels were preserved exactly as submitted — see
   `human_validation/Human_Result/` (raw rater files, untouched) and
   `human_validation/{metadata,fulltext}_human_ratings_*.csv` (consolidated, also untouched by
   this reconciliation step).
3. Researchers subsequently examined, for each of the 4 final metadata topics and 8 final
   full-text topics: the two raters' independently proposed labels, the top-20 probability
   terms, the top-20 FREX/exclusive terms, and the highest-loading studies
   (`human_validation/{metadata,fulltext}/topic_*_packet.json`,
   `results/{metadata,fulltext}/definitive_ksweep_runs.csv`).
4. Final descriptive labels were reconciled from the shared semantic core of the two raters'
   proposals — not invented independently of them, and not a re-run of the rating process.
5. **Reconciliation did not alter**: ratings, model selection, topic-word distributions,
   document-topic assignments, or any quantitative result. See `results/FROZEN_FINAL_VALUES.json`
   (re-verified unchanged as part of this task, zero discrepancies).

## Reconciled labels and their basis

### Metadata (k=4)

| Topic | Rater 1 | Rater 2 | Reconciled label |
|---|---|---|---|
| 0 | Security Vulnerabilities & Copilot Usage | AI Code Verification, Vulnerability & Trust (ChatGPT/Copilot) | **AI Code Verification, Vulnerability, and Developer Trust** |
| 1 | Prompting for Domain-Specific Requirements | Code Generation Methods & Requirements-Driven Prompting | **Requirements-Driven Prompting and Code Generation** |
| 2 | AI in Computer Science Education | Education & Practitioner Adoption of ChatGPT | **AI in Programming Education and Adoption** |
| 3 | Mitigating API Hallucinations | API/Dependency-Level Hallucination Mitigation | **API/Dependency Hallucination Mitigation** |

Note (preserved from the original human-validation record, not altered by this reconciliation):
the two raters did not converge on a preferred **k** overall for the metadata representation
(Rater 1 preferred the 5-topic solution, Rater 2 the 3-topic solution). These reconciled
labels are for the **k=4 solution specifically**, which was retained on quantitative-parsimony
grounds (see `reports/METADATA_FINAL_K_VALIDATION.md`), not because either rater selected k=4.
Reconciling topic 0-3's *labels* is a separate step from confirming *k*, and this
reconciliation does not imply the latter.

### Full text (k=8)

| Topic | Rater 1 | Rater 2 | Reconciled label |
|---|---|---|---|
| 0 | Developer Experience & Trust | Developer Community Trust & Experience with AI Coding Assistants | **Developer Trust and Experience with AI Coding Assistants** |
| 1 | Package Hallucinations & Security | Package Hallucination & Supply-Chain/Malicious Code Risks | **Package Hallucination and Supply-Chain Security Risks** |
| 2 | Secure Class-Level Generation | Code Security, Safety-Critical & Class-Level Completion Benchmarks | **Security and Safety-Critical Code Generation Benchmarks** |
| 3 | Hallucination Mitigation | Hallucination Detection & Mitigation Methods (Benchmarks, Self-Consistency, RAG) | **Hallucination Detection and Mitigation Methods** |
| 4 | General Coding Proficiency | LLM Proficiency on Coding Exercises & Competitive-Programming Benchmarks | **LLM Coding Proficiency and Programming Tasks** |
| 5 | Computing Education & Learning | Programming Education: Student Learning, Feedback & Assessment | **Programming Education, Learning, Feedback, and Assessment** |
| 6 | Code Complexity & Determinism | Code Quality Metrics: Vulnerability (CWE), Complexity & Non-Determinism | **Code Quality, Vulnerability, Complexity, and Non-Determinism** |
| 7 | Bug Taxonomies & Interactive Fixing | Bug Taxonomy & Practitioner Survey of Code Defects/Patterns | **Bug Taxonomies and Practitioner-Reported Code Issues** |

Topics 2 and 4 are the two topics with only "moderately persistent" (rather than "highly
persistent") status in the cross-k analysis and the lowest human-rated distinctiveness scores
(`reports/FULLTEXT_FINAL_K_VALIDATION.md`, `reports/HUMAN_VALIDATION_REPORT.md`); their
reconciled labels retain the broader/compound phrasing both raters independently used, rather
than forcing an artificially narrow, falsely precise name.

## Record

Full reconciled table with rater-label provenance and per-topic reconciliation rationale:
`human_validation/FINAL_TOPIC_LABELS.csv`. Authoritative source workbook (verified
word-for-word identical to the labels applied here):
`human_validation/Human_Result/Final_Result_Summary/FINAL_TOPIC_LABELS_RECONCILED.xlsx`. Raw,
unaltered rater files: `human_validation/Human_Result/`.
