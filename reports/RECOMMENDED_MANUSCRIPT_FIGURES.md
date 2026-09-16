# Recommended Main-Manuscript Figures

Of 57 total figures (`reports/FIGURE_INDEX.md`), four are recommended for the main manuscript.
Everything else is recommended for supplementary material or repository-only reference — full
figure coverage exists for readers who want it, without crowding the main text.

## Main Figure A: Metadata model-selection evidence

**Files:** `figures/metadata/M8_candidate_comparison_dominant_counts.png` (mega-topic
visibility across k=2-5) + `figures/human_validation/HM3_preferred_topic_count.png` (human
raters disagree, and k=4 was neither rater's pick).

**Why:** this is the single figure pair that makes the k-selection story defensible at a
glance — it shows *both* why k=2/k=3 were rejected (visually obvious mega-topic dominance) and
*honestly* shows that k=4 was a quantitative-parsimony compromise, not a human-confirmed
choice. Together they pre-empt the most likely reviewer question ("why not just report the
human-preferred k?").

## Main Figure B: Final metadata topic prevalence and representative terms

**Files:** `figures/metadata/M_topic_prevalence.png` + `figures/metadata/M_top_terms.png`
(or a manuscript-formatted combination of the two).

**Why:** this is the primary RQ5 result — the four final metadata topics, their size (n and
%), and their defining terms (probability + FREX). It is the figure a reader needs to
understand what Analysis A actually found.

## Main Figure C: Full-text cross-k persistence

**Files:** `figures/fulltext/F16_cross_k_persistence_heatmap.png` +
`figures/fulltext/F17_cross_k_persistence_summary.png`.

**Why:** supports the claim that k=8 is "the most parsimonious representative of a broader
region of quantitatively comparable and thematically persistent solutions" rather than a
uniquely optimal k — this is load-bearing for the full text section's credibility and directly
answers the near-equivalent-region concern.

## Main Figure D: Metadata/full-text representation comparison

**Files:** `figures/comparison/C5_representation_metrics_comparison.png` (robustness
asymmetry justifying the primary/secondary role split) + `figures/fulltext/F20_length_vs_confidence.png`
(the length-sensitivity limitation that motivates that split).

**Why:** this is the figure that carries the paper's most important interpretive move —
justifying why metadata is primary and full text is a secondary sensitivity check — using
the actual robustness numbers rather than assertion.

## Everything else: supplementary or repository-only

- **Supplementary material** (recommended): M9-M19 detail figures, F1-F15/F18-F23 detail
  figures, HM1/HM2, HF1-HF5, C1-C4/C6, R1-R8. These support specific methodological claims
  (coherence sweeps, robustness checks, per-topic human ratings) that a careful reviewer or
  replicator would want but that would overwhelm the main text.
- **Repository-only**: none excluded outright — all 57 figures are retained in the repository
  for full traceability; this list is about manuscript placement, not exclusion from the
  reproducibility package.
