# Full-Text Final k Validation

**Status: FINAL — k=8.** Quantitative cross-k persistence analysis and independent blinded
human rating are both complete (protocol repair task Part 6); see the "Human validation" section
below.

## Problem addressed

The original k-selection identified {8, 9, 12, 13, 14, 15} as a near-equivalent candidate
region for the full-text representation (composite score within 0.05 of the region's best
point). k=8 was selected only by the parsimony tie-break within that region. This report does
**not** claim k=8 is uniquely optimal; instead it tests whether k=8's topic structure persists
as k increases through the rest of that region, which is the evidence actually needed to
justify treating k=8 as representative of the region rather than an arbitrary pick within it.

## Method

Using the already-fitted, already-saved structural-medoid model at each candidate k (no
refitting), each of k=8's 8 topics was matched via Hungarian alignment (on full topic-word
distributions, same frozen dictionary throughout) to its best-matching topic at each of
k=9, 12, 13, 14, 15. Source: `results/fulltext/cross_k_topic_persistence.csv`; per-topic
summary: `results/fulltext/cross_k_topic_persistence_summary.csv`; heatmap:
`figures/fulltext/F16_cross_k_persistence_heatmap.png`.

## Persistence classification (mean best-match JS similarity across k=9..15)

| k=8 topic | Provisional theme | Mean similarity | Classification |
|---|---|---:|---|
| T0 | Developer trust & community perception | 0.599 | highly persistent |
| T1 | Package hallucination / malicious dependency risk | 0.568 | highly persistent |
| T2 | Security-focused benchmark evaluation | 0.500 | moderately persistent |
| T3 | API/dependency hallucination detection & mitigation | 0.631 | highly persistent |
| T4 | Programming exercises & skill assessment | 0.435 | moderately persistent |
| T5 | Programming education & feedback | 0.638 | highly persistent |
| T6 | Code vulnerability, determinism & fix quality | 0.627 | highly persistent |
| T7 | Bug patterns & developer-reported issues | 0.580 | highly persistent |

**6 of 8 topics are highly persistent** (mean similarity ≥0.55) across the entire candidate
region; the remaining 2 (T2, T4) are moderately persistent (0.40–0.55) but never unstable
(none fall below 0.40). No k=8 topic disappears or is contradicted at higher k.

## What the additional topics at higher k represent

At each higher k, the topics that do *not* match any k=8 topic were inspected directly (term
lists, not AI labels) rather than assumed to be genuine new themes. Across k=9 through k=15,
these unmatched topics predominantly reuse vocabulary already present in k=8's T0
(developer/participant/copilot/suggestion), T2/T6 (security/vulnerability/attack), and T7
(bug/repair) topics — e.g. k=12's unmatched T3 ("participant, copilot, suggestion, class,
assistant, interaction, programmer") and k=14's unmatched T1 ("copilot, participant,
suggestion, programmer, technical, mode, comment") both look like finer subdivisions of k=8's
T0, not new content. A small number of unmatched topics at the highest k values (e.g. k=15's
T14: "participant, suggestion, assistant, diagram, uml, accuracy, class, impact, correctness")
have a more distinct vocabulary (UML/diagram-specific) but very low apparent prevalence and
thin dominant-study counts (`results/fulltext/fulltext_k_candidate_comparison.csv` shows k=15
has 3 topics with <3 dominant studies, vs. 0 at k=8) — consistent with fragmentation rather
than a robust additional theme.

**Interpretation**: the evidence supports describing k=9–15's additional topics as
predominantly *subdivisions* of k=8's structure rather than *stable new conceptual content*,
though this reading should be confirmed by human raters (see below) rather than asserted from
term-list inspection alone.

## Manuscript framing

Consistent with protocol repair task Part 7, this analysis supports:

> "k=8 was selected as the most parsimonious representation of a broader region of
> quantitatively comparable solutions (k=8–15); its topic structure was highly or moderately
> persistent across that entire region, with additional topics at higher k predominantly
> subdividing rather than replacing k=8's themes."

and explicitly avoids:

> ~~"k=8 was the optimal model."~~

## Human validation of the final topics — complete

Two independent raters completed blinded evaluation of all 8 k=8 topics (AI-drafted labels
withheld; full detail in `reports/HUMAN_VALIDATION_REPORT.md`). Combined across both raters:
mean coherence ≈4.06/5, mean interpretability ≈4.00/5, mean distinctiveness ≈3.88/5. This
**corroborates** the quantitative persistence finding rather than merely assuming it: Topic 5
(programming education, one of the 6 "highly persistent" topics) was the strongest topic to
both raters (4.83/5 overall). Topic 4 (programming exercises/training, one of the 2
"moderately persistent" topics flagged above) was the weakest (3.17/5) — both raters
independently described it as broad/heterogeneous, overlapping with education and quality
content. Topic 2 (the other "moderately persistent" topic, security-focused benchmark
evaluation) also scored lower on distinctiveness (4.0) than most topics, with both raters'
free-text notes flagging overlap with Topic 6 (vulnerability/complexity). **The quantitative
persistence classification and the independent human ratings agree on which topics are most
and least well-resolved at k=8.**

> Human evaluation provided generally positive evidence for topic coherence and
> interpretability but weaker evidence for complete topic distinctiveness. Several fine-grained
> topics were perceived as conceptually adjacent, indicating that the eight-topic solution
> should be interpreted as a probabilistic thematic decomposition rather than eight mutually
> exclusive conceptual categories.

Raw rater files: `human_validation/Human_Result/Full_Text/`; consolidated tables:
`human_validation/fulltext_human_ratings_per_topic.csv`,
`human_validation/fulltext_human_ratings_raw.csv`. Topic labels proposed independently by each
rater (not yet reconciled into a single consensus label) are in
`human_validation/FINAL_TOPIC_LABELS.csv`.
