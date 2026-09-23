# Final Analysis Freeze

This repository's LDA analysis is frozen at the values recorded in
`reports/FROZEN_MANUSCRIPT_VALUES.md`, the single canonical values table
every narrative report agrees with. Final models: metadata k=4 (structural-medoid
seed 1212), full text k=4 (structural-medoid seed 505).

## Checksums

SHA-256 of the frozen numerical source files (also in `FREEZE_SHA256.txt`):

```
c275bd4c2840194319ed2d46719642cd0e07f37633219ede70250684a67908e5  reports/FROZEN_MANUSCRIPT_VALUES.md
0f5e173674d4b42b831483ddfed642700dadc7d4978de8d8b7a0d418fff0c079  corpus/corpus_manifest.csv
8b7ba7201937ae92e783d32fdee6449f174fa519aabf5bcd3797a6d561b74ced  corpus/primary_studies_manifest.csv
067870d7b8a96262005692109d4df65778f25a265fb7e381ae3553f594240a29  results/metadata/k_sweep_summary.csv
de51d830d03edb6583fe202019c16929ddca30b1da3e54b7a2f785067939ea3e  results/metadata/k_sweep_by_seed.csv
871ce50540ad6abe1baad4668a825bef313924b30bcef15cf5dc4f692a2ebf43  results/fulltext/k_sweep_summary.csv
a41ecd26773416d132989cb67849fc2da7d160c08b14ada536c70b9cc121a82c  results/fulltext/k_sweep_by_seed.csv
fd8c870b9aff3625242b2a45431b6f1c471a2211aceced4d90b6c036ecce8fe5  results/cross_representation/contingency_matrix.csv
c993d2e6b5608ffa1e1135ae3dd7775b44ed75df52d60d5115202acd28928721  results/cross_representation/permutation_test.csv
5f493b0d18c21ff89524fd2db00c04eb147c1d4489229ea518ba87400e5baaa3  results/cross_representation/intersection_analysis.csv
```

Recompute and compare with:

```bash
sha256sum -c FREEZE_SHA256.txt
```

## Statement of record

Values and topic labels in `reports/FROZEN_MANUSCRIPT_VALUES.md` are frozen.
Any future change to a reported value or label requires a new dated entry
here and a corresponding checksum update. See `src/verify_frozen_outputs.py`
for an automated check of internal consistency between the files above and
the narrative reports.
