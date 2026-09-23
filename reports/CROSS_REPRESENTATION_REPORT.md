# Cross-Representation Comparison Report

Topic-word distributions are compared on the vocabulary **intersection** of
the two representations' independently-built dictionaries, with coverage
reported explicitly and interpreted with the caution that low coverage
warrants.

Neither final model (metadata k=4, seed 1212; full text k=4, seed 505) was
refitted for this comparison — both are deterministically reconstructed from
their frozen configuration (verified: reconstructed dominant-study counts
match the frozen record exactly, [22,16,15,13] and [17,8,16,25]) purely to
obtain their already-fixed topic-word and document-topic distributions for
comparison. This is a comparison step, not a model-selection stage.

## 1. Representation characteristics

| | Metadata | Full text |
|---|---|---|
| Source text | Title + abstract + keywords | Cleaned substantive full text |
| Vocabulary size | 208 | 1,503 |
| Dictionary threshold | no_below=6, no_above=0.4 | no_below=6, no_above=0.4 |
| Domain-term handling | HF-B | HF-A (= HF-B at this threshold) |

## 2. Shared-vocabulary intersection

**V_shared = metadata_vocabulary ∩ fulltext_vocabulary = 19 terms.**

| | Value |
|---|---|
| Metadata vocabulary size | 208 |
| Full-text vocabulary size | 1,503 |
| Intersection size | 19 |
| % of metadata vocabulary in intersection | 9.13% |
| % of full-text vocabulary in intersection | 1.26% |

The intersection is small in absolute and relative terms for both
representations. This is expected: the two dictionaries were built from
structurally different text (a ~130-token curated title/abstract/keyword
string vs. ~3,000+ tokens of methodological prose) and selected
independently, with no shared-vocabulary constraint anywhere in the
protocol. Full list: `results/cross_representation/intersection_analysis.csv`.

## 3. Per-topic shared-vocabulary coverage and renormalized similarity

For each of the four Hungarian-matched topic pairs, each topic's raw
probability mass on V_shared was recorded **before** renormalization
(coverage), then each restricted vector was renormalized to sum to 1 over
V_shared before computing similarity. Topic alignment used these
renormalized shared-vocabulary vectors and was **not** constrained to agree
with the document-level contingency matrix in §5 — the two are independent
lines of evidence.

| Metadata topic | Full-text topic | Coverage (meta) | Coverage (ft) | JS similarity | Cosine similarity | Top-10 Jaccard | Top-20 Jaccard |
|---|---|---|---|---|---|---|---|
| 0 (hallucination/mitigation) | 3 (iterative/retrieval mitigation) | 0.029 | 0.021 | 0.523 | 0.619 | 0.667 | 1.000 |
| 1 (education/feedback) | 0 (education/grading/trust) | 0.080 | 0.101 | 0.449 | 0.458 | 0.429 | 1.000 |
| 2 (developer trust) | 2 (package hallucination/practitioner) | 0.096 | 0.060 | 0.518 | 0.821 | 0.250 | 1.000 |
| 3 (correctness/testing) | 1 (repair/verification/determinism) | 0.048 | 0.034 | 0.562 | 0.796 | 0.429 | 1.000 |

**Coverage is low throughout (2.1%-10.1% of each topic's probability mass
falls on the 19 shared terms).** Per the interpretation rule below, the
JS/cosine/Jaccard values above should be read with this in mind: they
describe similarity on a small slice of each topic's actual content, not
the whole of it.

**A note on top-20 Jaccard:** with only 19 shared terms in total, "top-20"
of a 19-term vocabulary captures essentially the entire shared vocabulary
for both topics almost irrespective of ranking, which is why it reads 1.000
for every pair — this statistic is close to vacuous at this intersection
size and should not be read as evidence of strong alignment. **Top-10
Jaccard (0.25-0.67) is the more informative figure here**, since it
requires genuine agreement on which half of the shared vocabulary each
topic actually emphasizes, and it does discriminate meaningfully between
pairs (highest for the hallucination/mitigation match, lowest for the
developer-trust match).

**Interpretation rule applied:** because shared-vocabulary coverage is low
for every topic pair, these topic-word similarity estimates are interpreted
cautiously. The two representations assign the large majority of each
topic's probability mass to representation-specific vocabulary — terms
that simply do not occur in the other representation's independently-built
dictionary at all. This is not treated as a mathematical artifact to be
explained away; it is reported as a genuine constraint on how much the
topic-word comparison alone can tell us, and the document-level analysis in
§5 is weighted accordingly as complementary, not redundant, evidence.

## 4. Document-level agreement (same 66 studies, dominant topic)

- **ARI = 0.2384, NMI = 0.2738** (computed from the reconstructed frozen
  models' dominant-topic assignments over the same 66 studies).
- Described as **modest cross-representation agreement** — not as "clearly
  non-random" on the strength of ARI being greater than zero alone.

### Permutation test

To support any statement stronger than "modest," a label-permutation test
was run: metadata dominant-topic assignments held fixed, full-text
dominant-topic labels randomly permuted across the 66 studies, 10,000
repetitions, fixed seed=42 (`results/cross_representation/permutation_test.csv`).

| | Observed | Permutation mean (SD) | Empirical p-value |
|---|---|---|---|
| ARI | 0.2384 | -0.0002 (0.0214) | **< 0.0001** |
| NMI | 0.2738 | 0.0563 (0.0262) | **< 0.0001** |

The observed ARI and NMI both exceed all 10,000 permuted values (empirical
p = 1/10,001 ≈ 0.0001 for each, the floor achievable at this permutation
count). **This supports a statement that agreement exceeds chance**,
backed by the permutation test rather than asserted from ARI>0 alone.

## 5. Contingency matrix and descriptive correspondence

| | ft0 (education) | ft1 (repair/verif.) | ft2 (package/practitioner) | ft3 (mitigation) |
|---|---|---|---|---|
| **meta0** (hallucination/mitigation) | 1 | 1 | 3 | **17** |
| **meta1** (education/feedback) | **9** | 2 | 2 | 3 |
| **meta2** (developer trust) | 7 | 1 | 7 | 0 |
| **meta3** (correctness/testing) | 0 | 4 | 4 | 5 |

Percentages recalculated directly from this matrix (row totals: meta0=22,
meta1=16, meta2=15, meta3=13):

- **meta0 → ft3**: 17/22 = **77.3%** of meta0's dominant-assigned studies
  are also dominant-assigned to ft3.
- **meta1 → ft0**: 9/16 = **56.3%**.
- **meta2**: distributed — 7/15 (46.7%) to ft0, 7/15 (46.7%) to ft2, 1/15
  (6.7%) to ft1. No single full-text topic captures a majority.
- **meta3**: distributed — 5/13 (38.5%) to ft3, 4/13 (30.8%) to ft1, 4/13
  (30.8%) to ft2.

**Descriptive language used throughout this section, per the correction:**
meta0/ft3 and meta1/ft0 show strong correspondence. meta2 and meta3 show
**distributed correspondence** (also describable as **partial
one-to-many correspondence**) across multiple full-text topics rather than
concentration in one. This pattern is **consistent with
representation-dependent thematic granularity** — it is not stated as a
proven "genuine split," since that would require evidence beyond this
comparison to establish causally.

## 6. Limitations

- The word-level comparison is constrained by a very small (19-term) and
  low-coverage (2-10%) shared vocabulary; it should be read as a narrow,
  supplementary signal, not the primary evidence of cross-representation
  relationship.
- The document-level comparison (§4-5) is the stronger evidence here,
  backed by a permutation test, but ARI=0.24/NMI=0.27 still indicate only
  partial, not strong, agreement — most of the association is concentrated
  in two of the four topic pairs.
- Topic alignment (§3, Hungarian on renormalized shared vocabulary) and
  document alignment (§5, from each model's own full document-topic
  distributions) are independent computations and were not forced to
  agree; that they picked out the same four pairs is itself a modestly
  reassuring cross-check, not a guaranteed outcome.

## 7. Cautious interpretation (summary)

Differences and correspondences between the two representations may reflect
document representation, independently selected vocabularies of very
different size, stochastic variation in independent LDA fits, and
differences in how themes are lexically expressed in short metadata versus
substantive full text. The observed pattern — two topics with strong,
concentrated correspondence and two with distributed, partial
correspondence — is consistent with representation-dependent thematic
granularity. This report does not claim that full text "reveals" themes
metadata misses, that full text captures a "true" underlying structure, or
that metadata topics are causally explained by full-text ones; it reports
what was measured, with the coverage and permutation-test caveats above
attached to each claim.
