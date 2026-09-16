# Final Analysis Freeze

**Freeze date:** 2026-09-16
**Git commit hash (frozen content):** `ff7574215d15c86ab5aa9c642f86064864d74ef8`
**Release tag:** `lda-final-freeze`

## Checksums

| Artifact | SHA-256 |
|---|---|
| `corpus/primary_studies_manifest.csv` | `8b7ba7201937ae92e783d32fdee6449f174fa519aabf5bcd3797a6d561b74ce` |
| `protocol/LDA_66_dual_representation_protocol.md` | see `protocol/protocol_sha256.txt` |
| `results/FROZEN_FINAL_VALUES.json` | `eb0313e40615c8281a1e21b86f9bc6400c854994c8009ea32399528839e4804` |
| `results/FROZEN_FINAL_VALUES.csv` | `1827d6fd94cdc5bb373d4aa2cb929a82d51bc7555cba1031cf2c85683e3b685` |
| `figures/FIGURE_SHA256.csv` (registry of all 57×2 figure files) | `abab0c35fdbf5c537735e56a47b8218373d008d97c6e2ce0cd1f017b42fdb8d` |
| `reports/FROZEN_MANUSCRIPT_VALUES.md` | `b91e78a6e9e247fd9fd6e4f3630243c3a9aad6f19099e01393b76908aa1ad1c` |

Full list, including every figure's individual PNG/PDF hash: `figures/FIGURE_SHA256.csv`. This
file's own checksum is recorded in `ANALYSIS_FREEZE_SHA256.txt`.

## Environment

Python 3.11.15; gensim 4.4.0; spaCy 3.8.16 (en_core_web_sm 3.8.0); pandas 3.0.5; numpy 2.4.6;
scipy 1.17.1; scikit-learn 1.9.1; matplotlib 3.11.2. Full pinned list:
`requirements.txt`, `environment.yml`, `reports/ENVIRONMENT_SNAPSHOT.md`.

## Validation status

`results/validation_report.txt`: **ALL CHECKS PASS** (corpus N=66, both representations 66
documents, 0 secondary studies, k=4/k=8 final models, medoid seeds 14/2, 20 seeds × 380 models
per representation, human-validation files present, frozen values verified against source
files with zero discrepancies, dominant-topic counts sum to 66 for both models, topic
prevalence sums to ~1 for both models, 57/57 registered figures present with checksums,
manuscript transfer table and result provenance populated).

## What is and is not frozen

**Frozen:** corpus definition and manifest; both representations' preprocessing configuration;
both definitive k-sweeps (760 models) and their selected k/medoid seed; the k-selection
rationale for both representations (including the completed metadata k=2-5 candidate
comparison and full-text k=8-15 cross-k persistence analysis); all robustness results;
completed human-validation data and its consolidated summaries; the cross-representation
comparison; all 57 figures; the numerical values in `results/FROZEN_FINAL_VALUES.{json,csv}`
and `reports/FROZEN_MANUSCRIPT_VALUES.md`.

**Not yet done (out of scope for this freeze task):** the manuscript's RQ5 prose and
methodology section have not been rewritten — `reports/FROZEN_MANUSCRIPT_VALUES.md` is the
single source the subsequent rewrite must draw from. Final topic labels are not yet reconciled
between the two human raters (`human_validation/FINAL_TOPIC_LABELS.csv` marks all rows
"Pending researcher reconciliation").

## Statement of record

> These files constitute the analytical source of truth for the manuscript's LDA methodology
> and RQ5 results. Do not alter final values after this point without creating an explicit new
> freeze (a new dated entry in this file, a new commit, and, if the change is substantive, a
> logged amendment in `protocol/protocol_amendments.md`).
