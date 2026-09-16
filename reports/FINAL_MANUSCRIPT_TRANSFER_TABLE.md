# Final Manuscript Transfer Table

**Status: FINAL.** Both selected-k rows and all other rows are frozen and corroborated by completed blinded human validation (`reports/METADATA_FINAL_K_VALIDATION.md`, `reports/FULLTEXT_FINAL_K_VALIDATION.md`, `reports/HUMAN_VALIDATION_REPORT.md`, `reports/FINAL_K_DECISION_TABLE.md`). Final reconciled topic labels: `human_validation/FINAL_TOPIC_LABELS.csv`.

| Manuscript item | Metadata LDA | Full-text LDA | Source file |
|---|---:|---:|---|
| N | 66 | 66 | `corpus/primary_studies_manifest.csv` |
| Vocabulary size | 397 | 2626 | `results/{rep}/stage1_selected_config.json` |
| Selected k | 4 | 8 | `results/{rep}/k_selection_decision.json` |
| Number of seeds | 20 | 20 | `protocol (frozen)` |
| Number of models (definitive sweep) | 380 | 380 | `results/{rep}/definitive_ksweep_runs.csv` |
| Selected medoid seed | 14 | 2 | `results/{rep}/representative_seed_k*.json` |
| C_v (mean at selected k) | 0.4035 | 0.3958 | `results/{rep}/definitive_ksweep_runs.csv` |
| C_NPMI (mean at selected k) | -0.1042 | -0.0432 | `results/{rep}/definitive_ksweep_runs.csv` |
| Stability (mean JS similarity) | 0.661 | 0.5432 | `results/{rep}/seed_stability_by_k.csv` |
| Topic diversity (mean) | 0.8425 | 0.7669 | `results/{rep}/definitive_ksweep_runs.csv` |
| Subsampling similarity (mean JS, 100x80%) | 0.5858 | 0.5151 | `results/{rep}/subsampling_80pct_100reps.csv` |
| Subsampling ARI (mean, 100x80%) | 0.1287 | 0.2192 | `results/{rep}/subsampling_80pct_100reps.csv` |
