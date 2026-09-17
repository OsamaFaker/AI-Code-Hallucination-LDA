# GitHub Deployment Verification

## Repository

https://github.com/OsamaFaker/AI-Code-Hallucination-LDA

## Branch

`main`

## Final commit

`e6b0e8ccb7c46843c71fba0ad0527270f3738dd3` — "Fix figure-checksum registry path format;
verify GitHub deployment"

(Preceding commit `6a45b76a39b7b37bc0271bcaeaa88f889a8f17c4` — "Apply final human-validated
topic labels and freeze LDA analysis (v2)" — carried the analytically meaningful freeze
content; this final commit is a verification-tooling fix only, changing no analytical value.)

## Final tags

- `lda-final-freeze` → commit `b5302783f27ea6e447f8c0d52bb544cdfbb9dd9b` (v1 freeze, unmoved)
- `lda-final-freeze-v2` → commit `5988e6c72d5d6ca31eac995f8b5e43d40765a2e6` (v2 freeze with
  final topic labels, unmoved)

Both tags pushed and confirmed present on the remote (`git ls-remote origin`), pointing to
their original commits — neither was silently relocated.

## Local tracked files

385 (`git ls-files | wc -l`)

## Remote verified files

385 / 385 — every tracked file, not a sample. Method: direct HTTPS download from
`raw.githubusercontent.com` compared by SHA-256 against the committed git blob content (not
the CRLF-normalized working tree; `core.autocrlf=true` on this Windows checkout). Full table:
`reports/REMOTE_FILE_VERIFICATION.md`.

## Missing files

**0.**

## Hash mismatches

**0** (a transient mismatch on one file immediately after push was traced to GitHub's raw-CDN
cache propagation delay, resolved on re-check ~10 seconds later and independently confirmed via
`git diff origin/main` showing zero difference throughout; documented in
`reports/REMOTE_FILE_VERIFICATION.md`).

## Figure verification

**PASS** — 114/114 (57 figures × PNG+PDF) verified against both the live GitHub remote and the
`figures/FIGURE_SHA256.csv` registry. A path-format bug in that registry (Windows backslashes
instead of forward slashes; hash values were always correct) was found and fixed during this
verification — see `protocol/protocol_amendments.md` and
`reports/REMOTE_FIGURE_VERIFICATION.md`.

## Frozen-value verification

**PASS** — `results/FROZEN_FINAL_VALUES.json` downloaded directly from the GitHub remote and
compared against the expected table:

| Metric | Metadata (expected / remote) | Full text (expected / remote) |
|---|---|---|
| N | 66 / 66 | 66 / 66 |
| Final k | 4 / 4 | 8 / 8 |
| Vocabulary size | 397 / 397 | 2,626 / 2,626 |
| Seeds per k | 20 / 20 | 20 / 20 |
| Definitive models | 380 / 380 | 380 / 380 |
| Medoid seed | 14 / 14 | 2 / 2 |
| Mean C_v | 0.4035 / 0.4035 | 0.3958 / 0.3958 |
| Mean C_NPMI | -0.1042 / -0.1042 | -0.0432 / -0.0432 |
| Cross-seed JS stability | 0.6610 / 0.6610 | 0.5432 / 0.5432 |
| Topic diversity | 0.8425 / 0.8425 | 0.7669 / 0.7669 |
| 80% subsampling similarity | 0.5858 / 0.5858 | 0.5151 / 0.5151 |
| 80% subsampling ARI | 0.1287 / 0.1287 | 0.2192 / 0.2192 |

Zero discrepancies.

## Human-validation file verification

**PASS.** Final reconciled labels (all 12: 4 metadata + 8 full text) confirmed present,
word-for-word, in the remote copy of `human_validation/FINAL_TOPIC_LABELS.csv`. Remote copy
contains zero occurrences of `AI-DRAFT` or `Pending researcher reconciliation` in that file.
Raw rater files (`human_validation/Human_Result/`) confirmed present and, via the same
git-blob-vs-remote hash check, byte-identical to the local originals (which were themselves
confirmed unmodified by this and the prior task via `git diff --stat`).

## Critical files individually verified

`README.md`, `results/FROZEN_FINAL_VALUES.json`, `results/validation_report.txt`,
`human_validation/FINAL_TOPIC_LABELS.csv`, `reports/HUMAN_VALIDATION_REPORT.md`,
`reports/FINAL_LDA_REPORT.md`, `reports/FROZEN_MANUSCRIPT_VALUES.md`,
`reports/FIGURE_INDEX.md`, `FINAL_ANALYSIS_FREEZE.md` — each downloaded directly from the
remote and content-checked (final labels present, frozen values present, no stale markers) in
addition to the full-tree hash verification above.

## Repository accessibility

Confirmed via anonymous `git ls-remote` and direct HTTPS downloads (no authentication
required — public repository): repository accessible, default branch `main` contains the
final commit, all directories present (`protocol/`, `corpus/`, `extraction/`, `preprocessing/`,
`src/`, `results/`, `human_validation/`, `figures/`, `notebooks/`, `reports/`), `models/`
correctly absent (git-ignored, never pushed), no full-text article PDFs present in the tree.

## Overall deployment status

**PASS.**

```text
Missing tracked files: 0
Hash mismatches: 0
Broken figure references: 0
Frozen-value mismatches: 0
Repository validation: PASS
```
