# Manuscript-Ready Text (RQ5: LDA Topic Structure)

**Status: superseded.** Human validation is complete and topic labels have been
researcher-reconciled (k_A=4, k_B=8 — both FINAL). This draft is kept only as a prose
reference; per the freeze task's own scoping, **the actual RQ5/methodology rewrite is a
separate subsequent task and must draw only from** `reports/FROZEN_MANUSCRIPT_VALUES.md`,
`human_validation/FINAL_TOPIC_LABELS.csv`, `reports/HUMAN_VALIDATION_REPORT.md`,
`reports/FIGURE_INDEX.md`, and the frozen figures — not from this file. The placeholder
bracketed notes below (`[Labels pending...]`) have been corrected to the final reconciled
labels for accuracy, but the surrounding prose has not been rewritten in this task.

## Methodological text

> To complement the manually derived RQ1–RQ4 classification, we conducted an independent,
> data-driven Latent Dirichlet Allocation (LDA) analysis of the 66 primary studies (the 5
> secondary studies were excluded from all LDA stages). We fit two independent models: Analysis
> A on a metadata representation (title + abstract + author keywords, or title + abstract where
> keywords were unavailable, 24/66 studies) and Analysis B on a cleaned, section-restricted
> full-text representation (Introduction through Conclusion; references, headers/footers,
> boilerplate, and author/affiliation metadata removed). Text was tokenized and lemmatized with
> spaCy (`en_core_web_sm` 3.8.0), retaining nouns, proper nouns, verbs, and adjectives after
> standard English stopword removal. We used integer bag-of-words counts as the input to
> classical probabilistic LDA (gensim), since LDA is a generative model over discrete token
> counts; TF-IDF was not used as the primary representation. Dictionary filtering thresholds
> (`no_below` ∈ {2,3,4,5}; `no_above` ∈ {0.50,…,1.00}) were selected independently for each
> representation from a systematic 36-cell grid via a documented stable-region-plus-parsimony
> rule (never the coherence-maximizing cell): `no_below=5, no_above=0.50` for Analysis A
> (vocabulary 397) and `no_below=4, no_above=0.75` for Analysis B (vocabulary 2,626). Training
> budget (passes=30, iterations=800) and priors (`alpha=eta=auto`) were frozen via a separate
> convergence pilot before the definitive sweep. For each representation we fit models across
> k=2–20 with 20 random seeds each (380 models per representation), computed C_v and C_NPMI
> coherence, cross-seed stability (Hungarian-aligned Jensen–Shannon similarity), topic
> diversity, and topic redundancy for every model, and selected k via a Pareto front over these
> criteria jointly (never coherence alone). For Analysis A, the four candidate k values in the
> Pareto-optimal, near-equivalent region (k=2,3,4,5) were compared descriptively on their
> structural-medoid model's dominant-topic balance, stability, and diversity: k=2 and k=3 were
> judged inadequate because a single topic absorbed 71–73% of the corpus in both cases (an
> under-differentiation failure mode), while k=4 achieved the most even topic-size distribution
> among all four candidates and k=5 did not improve on k=4 by any measured criterion; k=4 is
> therefore the best-supported value by quantitative evidence, corroborated (not confirmed -
> the two raters preferred different k values) by completed blinded human rating. For Analysis B, the six candidate k values in the near-equivalent region
> (k=8,9,12,13,14,15) were compared via cross-k topic-persistence analysis: the k=8 solution's
> topics were 75% highly persistent and 25% moderately persistent (none unstable) across the
> entire candidate region, with additional topics at higher k predominantly subdividing rather
> than replacing k=8's themes, supporting k=8 as a parsimonious representative of that region
> rather than a uniquely optimal solution. For each selected k, the representative model was
> the *structural medoid* seed (maximum mean aligned similarity to the other 19 seeded models),
> not the highest-coherence seed. Robustness was assessed via training-effort sensitivity,
> dictionary-neighbor sensitivity, domain-term and phrase-detection sensitivity, and 100
> repetitions of 80% document subsampling (identical sampled studies used for every metric
> within a repetition). Analysis B additionally received a document-length sensitivity check,
> which showed a non-trivial dependency of the full-text topic structure on document length
> (see Limitations). Given this asymmetric robustness evidence, we treat Analysis A (metadata)
> as the primary RQ5 analysis and Analysis B (full text) as a secondary
> representation-sensitivity analysis. All twelve final topics (four metadata, eight full text)
> were rated independently by at least two human evaluators, blinded to model identity and to
> any AI-drafted label, before topic labels were finalized (see Supplementary Material for the
> rating procedure and inter-rater agreement). The full protocol was frozen prospectively
> (SHA-256-hashed) before any model was fit; amendments (a refinement to the k-selection
> parsimony rule after an initial degenerate k=2 selection for Analysis A, and the subsequent
> removal of the numeric floor that first correction introduced, in favor of the descriptive
> admissibility and human-validation procedure above) are logged with justification in the
> accompanying reproducibility package.

## RQ5 results text

> Analysis A (metadata) yielded four topics (mean C_v=0.40, mean cross-seed stability=0.66):
> AI Code Verification, Vulnerability, and Developer Trust; Requirements-Driven Prompting and
> Code Generation; AI in Programming Education and Adoption; and API/Dependency Hallucination
> Mitigation. Analysis B (full text) yielded eight topics (mean C_v=0.40, mean cross-seed
> stability=0.54): Developer Trust and Experience with AI Coding Assistants; Package
> Hallucination and Supply-Chain Security Risks; Security and Safety-Critical Code Generation
> Benchmarks; Hallucination Detection and Mitigation Methods; LLM Coding Proficiency and
> Programming Tasks; Programming Education, Learning, Feedback, and Assessment; Code Quality,
> Vulnerability, Complexity, and Non-Determinism; and Bug Taxonomies and Practitioner-Reported
> Code Issues. (Labels are researcher-reconciled from two independent blinded raters' proposals;
> see `human_validation/FINAL_TOPIC_LABELS.csv` and `reports/TOPIC_LABEL_RECONCILIATION.md`.)
> Cross-representation comparison (after both models were independently frozen) showed modest
> agreement on dominant-topic assignment across the 66 studies (Adjusted Rand Index=0.19,
> Normalized Mutual Information=0.30). All four metadata topics showed partial correspondence
> with a full-text topic under rectangular Hungarian alignment, most clearly for the
> API/dependency-hallucination theme (JS similarity=0.21) and the education theme (JS
> similarity=0.23), though even these strongest matches were only moderately similar in
> absolute terms; four full-text topics (developer trust/community, package hallucination,
> training exercises, bug patterns) had no metadata counterpart. This pattern is consistent
> with these themes depending on methodology/results/discussion-level detail not captured in
> titles, abstracts, or keywords, but we cannot statistically rule out that it partly reflects
> the differing selected k (4 vs. 8) or the full-text model's documented sensitivity to
> document length (see Limitations) rather than representation content alone. We therefore
> characterize the divergence between representations as *representation-sensitive* rather
> than attributing it to a specific mechanism, and treat the full-text analysis as a secondary,
> complementary check on the primary metadata-based topic structure rather than an equally
> weighted alternative result.

## Limitations paragraph

> The LDA analysis has several limitations. First, with only 66 primary studies, document-level
> topic assignment is comparatively fragile under resampling (mean Adjusted Rand Index under
> 80% subsampling: 0.13 for the metadata model, 0.22 for the full-text model), even though the
> underlying topic-word structure is more stable (mean Jensen–Shannon similarity 0.59 and 0.52
> respectively); results at the level of individual document-topic assignments should be read
> with this in mind. Second, the full-text model shows a non-trivial sensitivity to document
> length: a length-balanced sensitivity check (capping tokens per document) agreed with the full
> model on only 33% of dominant-topic assignments, and document length was weakly associated
> with topic-assignment confidence (r=0.25, p=0.043). We cannot statistically decompose how much
> of the cross-representation divergence we report reflects this length sensitivity, the
> differing selected k, ordinary model stochasticity, or genuine differences in representation
> content, and we do not claim to; for this reason we treat the metadata analysis as primary and
> the full-text analysis as a secondary, representation-sensitivity check rather than an
> equally weighted alternative result. Third, coherence values (C_v≈0.40 for both
> representations) are reported descriptively; we do not characterize them as high, strong, or
> excellent, since no external benchmark exists for LDA coherence on a corpus of this size and
> domain, and coherence, stability, t-SNE/UMAP embeddings, and pyLDAvis visualizations (where
> used) are not treated as independent validation of topic quality. Fourth, the selected number
> of topics for each representation (k=4 metadata, k=8 full text) is the best-supported value
> from quantitative evidence — a descriptive admissibility comparison across the near-equivalent
> candidate region for metadata, and a cross-k topic-persistence analysis for full text.
> Independent human raters, blinded to model identity, subsequently rated the candidate/final
> topic solutions; for full text this rating corroborates the quantitative selection, but for
> metadata the two raters preferred different k values from each other and from k=4, so k=4 is
> reported as a quantitative-parsimony compromise supported by, not confirmed by, human
> evaluation — this disagreement is reported rather than resolved by re-weighting. Fifth, topic
> labels reported here were originally AI-drafted only to accelerate human-rater orientation and
> were not shown to raters before their independent ratings and proposed labels were recorded;
> the manuscript's final topic labels are researcher-reconciled from the two independent
> raters' own proposed labels (cross-checked against top-probability/FREX terms and
> highest-loading studies), not the original AI drafts, and are not claimed to be verbatim
> rater consensus (see `reports/TOPIC_LABEL_RECONCILIATION.md`). Finally, this LDA analysis is statistically independent
> of, and complementary to, the manually derived RQ1–RQ4 classification: it was not informed by
> RQ1–RQ4 categories at any stage prior to freezing the final models, and any qualitative
> correspondence we note between LDA topics and RQ1–RQ4 categories should be read as an informal
> cross-check of thematic coverage, not as independent statistical validation of the manual
> synthesis.
