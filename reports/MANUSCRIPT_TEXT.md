# Manuscript-Ready Text

Draft text for direct adaptation into the manuscript. All values are copied
from `reports/FROZEN_MANUSCRIPT_VALUES.md`.

## A. Methodology

Topic modelling was conducted using Latent Dirichlet Allocation (LDA) on
the 66 primary studies, applied independently to two representations: (i)
title, abstract, and author-supplied keywords ("metadata"), and (ii)
cleaned substantive full text ("full text"). Each representation was
preprocessed, its dictionary and priors selected, and its topic number (k)
searched independently, using a staged analysis protocol whose parameter
grids, seed lists, model-selection criteria, and robustness procedures were
fixed before the definitive topic-number search (4 preprocessing variants ×
40 dictionary configurations at a fixed pilot k-set and 5 seeds; a prior and
training-budget pilot; then a definitive sweep across k=2-20 with 20
independent random seeds per k), fit with gensim's `LdaModel` (never a
multi-threaded variant, to preserve strict reproducibility under a fixed
seed). For each k, cross-seed stability was quantified via Hungarian-aligned
Jensen-Shannon similarity of topic-word distributions, and the structural
medoid (not the highest-coherence seed) was used as that k's representative
model. Candidate k values were narrowed via Pareto-dominance across
coherence (C_v, C_NPMI), stability, diversity, redundancy, topic-population
diagnostics, and parsimony (15/19 metadata k values and all 19 full-text k
values were Pareto-optimal — the Pareto step alone did not isolate a small
candidate set), then reduced to at most four finalists per representation by
a pre-specified rule that ranks Pareto-optimal k values by cross-seed
stability; because stability generally decreases with topic count, this
rule tends to favour lower-dimensional solutions, which is disclosed rather
than left implicit. Finalists underwent 100-repetition 80% document
subsampling, training-effort and dictionary-threshold sensitivity analysis,
and — for full text — a mandatory document-length sensitivity check. Final
model selection integrated this quantitative evidence with blinded scoring
completed independently by two raters (one a project author), who scored
anonymized, randomly-ordered candidate models without access to model
identity, seed, configuration, or any quantitative metric, and without the
numerical k label — though the number of topics displayed for a given
model was necessarily observable, since complete candidate models were
shown.

## B. RQ5 Results

Both representations converged, independently, on a four-topic solution
(k=4) — a post-hoc observation, not a designed or constrained match between
the two independently-run pipelines. Metadata topics were: API/code
hallucination benchmarks and mitigation (22/66 studies dominant, 29.2%
probability mass); AI-generated feedback in programming education (16
studies, 24.2%); developer trust and experience with AI coding assistants
(15 studies, 24.2%); and empirical code correctness, testing, and
non-determinism (13 studies, 22.5%; both raters independently noted this as
the least specific topic). Full-text topics were: programming education
instruction, grading, and trust (17 studies, 26.6%); code repair,
verification, and determinism benchmarking (8 studies, 13.5%); practitioner
perspectives on package hallucination and security risk (16 studies,
22.7%); and iterative and retrieval-based hallucination mitigation (25
studies, 37.2% — the highest-rated topic by both raters).

Document-level agreement between the two representations' final models was
modest (ARI=0.238, NMI=0.274). A permutation test (metadata assignments
fixed, full-text dominant-topic labels randomly permuted across the 66
studies, 10,000 repetitions, fixed seed) found both observed values
exceeded all 10,000 permuted values (empirical p<0.0001 for each),
supporting that this agreement exceeds chance. Word-level topic comparison
used the two representations' shared vocabulary (19 terms — 9.1% of
metadata's 208-term vocabulary, 1.3% of full-text's 1,503-term vocabulary);
because each topic's probability mass on this shared vocabulary was low
(2-10% coverage), word-level similarity estimates are interpreted with
corresponding caution. Two of the four metadata topics corresponded
strongly to a single full-text topic (77% and 56% study concentration in
the dominant-topic contingency matrix); the other two corresponded to a
distributed, partial one-to-many pattern across multiple full-text topics.
This pattern is consistent with representation-dependent thematic
granularity — differences may reflect document representation,
independently selected vocabularies of very different size, stochastic
model variation, and differences in how themes are lexically expressed in
short metadata versus substantive full text, rather than one
representation capturing a more complete or more correct thematic
structure.

## C. Robustness

Both final models showed strong agreement under a substantially increased
training budget (100 passes and 2,000 iterations, versus the frozen 20
passes and 200 iterations — five times as many passes and ten times as many
iterations; dominant-topic agreement ARI 0.86-0.93) and no zero-dominance or
thin (<5-study) topics at the full-corpus fit. Under 80% document
subsampling (100 repetitions), both models retained substantial
document-assignment agreement (ARI≈0.80) with the full-corpus model, though
this falls short of near-perfect agreement and is reported as such.
**Topic-word structure showed moderate sensitivity to neighbouring
dictionary thresholds (JS 0.52-0.57), while dominant document assignments
were substantially more sensitive (ARI 0.15-0.28)** — a genuine limitation,
kept prominent rather than described as robustness. Full text additionally
showed a statistically significant positive correlation between document
length and topic-assignment confidence (r=0.358, p=0.003); the recovered
topic structure and dominant assignments nonetheless remained largely
preserved under the predefined length-balancing intervention (JS=0.938,
ARI=0.945) — both findings are reported together, and neither is used to
claim document length has no effect or that the model is insensitive to it.

## D. Limitations

The full-text final k was selected under genuine, documented disagreement
between the two raters (one preferred k=4, the other k=5); the
reconciliation toward k=4 rests on quantitative robustness criteria rather
than rater consensus, and k=4 was retained as the more conservative
multi-criterion solution, not because it was demonstrated to be superior —
the alternative k=5 solution's principal strength, a highly specific
competitive-programming/algorithmic topic not resolved at k=4, is a real
cost of this choice. Document-level topic assignments in both
representations are only moderately robust to plausible small changes in
dictionary construction (ARI 0.15-0.28), indicating some instability in
which specific studies anchor which topic even where topics' word-level
content is comparatively more stable. Full-text topic-assignment confidence
is measurably associated with document length. The full-text vocabulary
retains a small number of residual extraction artifacts (isolated tokens
such as participant-ID labels and code-listing fragments, e.g. "a.", "def",
"p4") not fully removed by the cleaning pipeline; these were not
retroactively cleaned and the model was not refitted, since their material
effect on the results was not independently tested. Cross-representation
word-level comparison is limited by a small (19-term), low-coverage (2-10%)
shared vocabulary between two independently-built dictionaries of very
different size (208 vs. 1,503 terms); document-level comparison, backed by
a permutation test, is the stronger evidence of cross-representation
relationship, but still indicates only partial (not strong) agreement. The
finalist-reduction rule that produced each representation's four candidate
k values ranks by cross-seed stability, which generally decreases with
topic count — this mechanically favours lower-dimensional, more
parsimonious solutions among the finalists actually presented to raters,
a property of the pre-specified rule that is disclosed here rather than
left implicit.

## E. Reviewer-response paragraph

Topic number was selected via a full k=2-20 search rather than a single
assumed value, with 20 independently-seeded fits per k to characterize
cross-seed stability rather than relying on a single run. Model selection
used Pareto-style multi-criterion reasoning across coherence, stability,
diversity, redundancy, and topic-population diagnostics (never
"highest-coherence wins" or "most-balanced wins" in isolation); we report
explicitly that the Pareto step alone left 15/19 (metadata) and 19/19
(full text) k values undominated, and that the subsequent
stability-ranked finalist cut — fixed before the sweep — mechanically
favours smaller k, rather than presenting the resulting k=2-5 finalists as
though Pareto dominance alone had isolated them. Topic-population
diagnostics (zero-dominance and thin-topic counts) were tracked across the
full k range and used as inspection triggers, not automatic rejection
thresholds. Finalists underwent quantitative robustness testing —
100-repetition document subsampling, training-effort sensitivity,
dictionary-threshold sensitivity, and (for full text) document-length
sensitivity — with results reported even where they revealed limitations
(e.g., dictionary-threshold sensitivity in document assignment remains
substantial rather than resolved, and a significant length-confidence
correlation in full text). Human evaluation used two raters completing
blinded scoring independently (one a project author, not an external
evaluator) on anonymized candidate models with no access to quantitative
metrics, configuration, or model identity, though the number of topics in
a displayed model was necessarily observable; where the two raters
disagreed (full-text k), this is reported transparently rather than
resolved by vote, with the final decision's quantitative rationale made
explicit and the non-selected alternative's genuine strengths preserved
rather than discarded. Cross-representation agreement is described as
modest and, where a stronger statistical claim is made (that agreement
exceeds chance), that claim is backed by a 10,000-repetition permutation
test rather than asserted from a positive ARI value alone; word-level
cross-representation similarity is reported alongside its shared-vocabulary
coverage so readers can judge how much of each topic's content that
comparison actually reflects. Finally, the two representations (metadata
and full text) were modelled, evaluated, and human-validated in full
independence before any comparison between them was made, so that any
observed convergence or divergence reflects the data rather than a shared
or coupled modelling choice; where both representations converged (final
k=4 for both), this is reported as a post-hoc observation from two
independent pipelines rather than a designed outcome.
