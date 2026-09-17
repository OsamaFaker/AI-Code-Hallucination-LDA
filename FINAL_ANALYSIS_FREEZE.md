# Final Analysis Freeze (v2 — final topic labels applied)

**Freeze date:** 2026-09-18
**Supersedes:** the v1 freeze (commit `b5302783f27ea6e447f8c0d52bb544cdfbb9dd9b`, tag
`lda-final-freeze`), which had all quantitative results frozen but topic labels marked
"Pending researcher reconciliation." This v2 freeze applies the final researcher-reconciled
topic labels and re-verifies every quantitative value unchanged (see below).
**Git commit hash (this freeze's content):** `6a45b76a39b7b37bc0271bcaeaa88f889a8f17c4`
**Release tag:** `lda-final-freeze-v2` (the v1 tag `lda-final-freeze` is left in place,
unmoved, per policy — a new tag is created rather than silently relocating an existing one).

## What changed since v1

Only descriptive topic labels and their dependent narrative text (reports, README). **No
quantitative result changed.** Confirmed by re-running `src/freeze_values.py` in this task:
`results/FROZEN_FINAL_VALUES.json`'s SHA-256 is byte-identical to v1
(`eb0313e40615c8281a1e21b86f9bc6400c854994c8009ea32399528839e4804`), as is
`corpus/primary_studies_manifest.csv`, `protocol/LDA_66_dual_representation_protocol.md`, and
`figures/FIGURE_SHA256.csv` (no figure needed regeneration — none of the 57 figures render
descriptive topic-name text; all use T0/T1/... indices or blinded Model A/B/C/D letters).

Applied in this freeze:
- `human_validation/FINAL_TOPIC_LABELS.csv`: `Final_Reconciled_Label` populated for all 12
  topics (4 metadata + 8 full text), replacing "Pending researcher reconciliation"; new
  `Reconciliation_Status` / `Reconciliation_Note` columns added. Original
  `Rater_1_Label`/`Rater_2_Label` columns unchanged.
- `reports/TOPIC_LABEL_RECONCILIATION.md`: new — documents the reconciliation process.
- `reports/HUMAN_VALIDATION_REPORT.md`: label-reconciliation section added.
- `reports/METADATA_LDA_REPORT.md`, `reports/FULLTEXT_LDA_REPORT.md`,
  `reports/FINAL_LDA_REPORT.md`, `reports/FROZEN_MANUSCRIPT_VALUES.md`,
  `reports/CROSS_REPRESENTATION_REPORT.md`, `reports/FINAL_K_DECISION_TABLE.md`,
  `reports/REVIEWER_LDA_RESPONSE_MATRIX.md`, `reports/FINAL_MANUSCRIPT_TRANSFER_TABLE.md`,
  `README.md`: final reconciled labels inserted; "provisional"/"pending" status language
  corrected to "FINAL"; `AI-DRAFT` markers removed from final-facing tables (retained,
  untouched, in the original archived packet JSONs under `human_validation/{metadata,fulltext}/`
  for provenance).
- `results/RESULT_PROVENANCE.csv`: 4 new rows for final labels and the reconciliation report.
- `src/validate_repository.py`: new checks for label completeness, absence of stale
  "Pending"/"AI-DRAFT" markers in final outputs, raw-rater-file presence, and
  models/-git-ignored + regeneration-command documentation.
- README: explicit `models/` git-ignore rationale and regeneration command added.

Raw human-rating files (`human_validation/Human_Result/`) are **unmodified** — confirmed via
`git diff --stat` against the v1 commit returning no output.

An authoritative reconciliation workbook,
`human_validation/Human_Result/Final_Result_Summary/FINAL_TOPIC_LABELS_RECONCILED.xlsx`
(present in the working tree but not yet committed at the start of this task), was found to
contain the same 12 reconciled labels applied here, word-for-word, plus a per-topic
reconciliation-rationale note; `human_validation/FINAL_TOPIC_LABELS.csv`'s
`Reconciliation_Note` column was updated to use those specific notes in place of generic
boilerplate.

## Checksums

| Artifact | SHA-256 | Changed since v1? |
|---|---|---|
| `corpus/primary_studies_manifest.csv` | `8b7ba7201937ae92e783d32fdee6449f174fa519aabf5bcd3797a6d561b74ce` | No |
| `protocol/LDA_66_dual_representation_protocol.md` | `b7d2e1b5c3eb9e97a04bfd4e5c933f00c2b51a43befdbf0c1fb6fe464301e19c` | No |
| `results/FROZEN_FINAL_VALUES.json` | `eb0313e40615c8281a1e21b86f9bc6400c854994c8009ea32399528839e4804` | No |
| `results/FROZEN_FINAL_VALUES.csv` | `1827d6fd94cdc5bb373d4aa2cb929a82d51bc7555cba1031cf2c85683e3b685` | No |
| `figures/FIGURE_SHA256.csv` | `abab0c35fdbf5c537735e56a47b8218373d008d97c6e2ce0cd1f017b42fdb8d` | No |
| `human_validation/FINAL_TOPIC_LABELS.csv` | `f34751cea639412724b529309dcc127f191c1f71d9462042a0222725181d75` | **Yes (labels + per-topic reconciliation notes applied)** |
| `reports/HUMAN_VALIDATION_REPORT.md` | `463a9d6d988098ac654fda469c7e043587f6c92d5ea5f5ae79a1b649bc88b39` | **Yes (reconciliation section added)** |
| `reports/TOPIC_LABEL_RECONCILIATION.md` | `6b3abc69f78012673469aa36303f271af4b8554254d58689f87a3948c80dcb9` | **Yes (new file; references the authoritative source workbook)** |
| `reports/FROZEN_MANUSCRIPT_VALUES.md` | `809904d5d0b850156865db7e942dfd035af9af22a633dbd4e822528b81296d4` | **Yes (label sections added)** |

## Environment

Unchanged from v1: Python 3.11.15; gensim 4.4.0; spaCy 3.8.16 (en_core_web_sm 3.8.0); pandas
3.0.5; numpy 2.4.6; scipy 1.17.1; scikit-learn 1.9.1; matplotlib 3.11.2. See
`reports/ENVIRONMENT_SNAPSHOT.md`, `requirements.txt`, `environment.yml`.

## `models/` — intentionally excluded, regenerable

`models/` (~203MB) remains git-ignored, not committed, and not stored via Git LFS. It is fully
regenerable from the frozen corpus, preprocessing configuration, seeds, final k, code, and
pinned environment. Regeneration command: see README.md "`models/` is intentionally
git-ignored" section (`src/definitive_k_sweep.py`, both representations).

## Validation status

`results/validation_report.txt`: **ALL CHECKS PASS**, including this freeze's new checks —
final topic labels populated (12/12), no "Pending researcher reconciliation" remaining, no
`AI-DRAFT` marker in final reconciled labels, reconciliation status correctly attributed
("Researcher reconciled after independent human rating", never "Rater consensus"), raw rater
files present, `models/` confirmed git-ignored with a documented regeneration command — plus
every check carried over from v1 (corpus N=66, both representations 66 documents, k=4/k=8,
medoid seeds 14/2, 20 seeds × 380 models per representation, dominant-topic counts sum to 66,
topic prevalence sums to ~1, 57/57 figures present with checksums, manuscript transfer table
and result provenance populated).

## What is and is not frozen

**Frozen (this freeze):** everything from v1, plus final researcher-reconciled topic labels for
all 12 final topics and every report/README section that names them.

**Not yet done (out of scope for this task):** the manuscript's RQ5 prose and methodology
section have not been rewritten. The next task should draw only from
`reports/FROZEN_MANUSCRIPT_VALUES.md`, `human_validation/FINAL_TOPIC_LABELS.csv`,
`reports/HUMAN_VALIDATION_REPORT.md`, `reports/FIGURE_INDEX.md`, and the frozen figures.

## Deployment addendum (2026-09-17): GitHub publication + figure-registry path fix

Published to `https://github.com/OsamaFaker/AI-Code-Hallucination-LDA` (branch `main`, tags
`lda-final-freeze` and `lda-final-freeze-v2` both pushed pointing to their original commits,
unmoved). During remote verification, `figures/FIGURE_SHA256.csv` was found to use
Windows-backslash paths instead of git/GitHub forward-slash paths (hash **values** were always
correct; only the path **keys** were malformed) — fixed via `src/build_figure_checksums.py`
and logged in `protocol/protocol_amendments.md`. This is a verification-tooling fix, not a
re-freeze of analytical content, so no new version number or tag was created for it; it is
included in the commit(s) following `6a45b76a39b7b37bc0271bcaeaa88f889a8f17c4` on `main`.
Updated checksum: `figures/FIGURE_SHA256.csv` =
`93801b23d6e8a112a9e6728061b9a72e1e14355a44d0c858d1422dd72031dd1`. Every tracked file (380) and
every figure (114 PNG+PDF files) was independently re-downloaded from GitHub's raw content and
SHA-256-verified against the committed git blob, with zero missing files and zero mismatches —
see `reports/REMOTE_FILE_VERIFICATION.md`, `reports/REMOTE_FIGURE_VERIFICATION.md`,
`reports/GITHUB_DEPLOYMENT_VERIFICATION.md`.

## Statement of record

> This freeze contains the final analytical outputs, human-validation evidence, reconciled
> topic labels, and publication figures used as the source of truth for the manuscript LDA
> methodology and RQ5 results. Do not alter final values or labels after this point without
> creating an explicit new freeze (a new dated entry/version in this file, a new commit and
> tag, and, if the change is substantive, a logged amendment in
> `protocol/protocol_amendments.md`).
