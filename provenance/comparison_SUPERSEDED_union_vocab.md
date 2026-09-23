# Cross-Representation Comparison -- metadata (k=4) vs full-text (k=4)

Rectangular Hungarian alignment on topic-word distributions projected onto the shared (union) vocabulary of both representations' frozen dictionaries.

## Topic alignment

| metadata topic | fulltext topic | JS similarity | cosine similarity | top-20 Jaccard |
|---|---|---|---|---|
| 0 | 3 | 0.0094 | 0.0103 | 0.0000 |
| 1 | 0 | 0.0320 | 0.0897 | 0.0526 |
| 2 | 2 | 0.0295 | 0.1201 | 0.0256 |
| 3 | 1 | 0.0165 | 0.0335 | 0.0256 |

Matched topics: 4/4. Unmatched: 0 (metadata), 0 (fulltext).

## Document-level agreement (dominant topic, same 66 studies)

- ARI = 0.2384
- NMI = 0.2738

## Dominant-topic contingency matrix (rows=metadata, cols=fulltext)

| | ft0 | ft1 | ft2 | ft3 |
|---|---|---|---|---|
| meta0 | 1 | 1 | 3 | 17 |
| meta1 | 9 | 2 | 2 | 3 |
| meta2 | 7 | 1 | 7 | 0 |
| meta3 | 0 | 4 | 4 | 5 |

Disagreement is not interpreted as model failure -- differences may reflect representation, stochastic variation, or genuinely different thematic granularity between what a title/abstract/keywords signal and what full-text methodological detail signals.
