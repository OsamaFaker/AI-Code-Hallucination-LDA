# Corpus Audit

The systematic mapping review contains 71 included studies: 66 primary and
five secondary studies. The LDA analysis uses the 66 primary studies only;
secondary studies are excluded because they synthesize evidence from primary
research and are not treated as independent analytical units. See
`corpus/corpus_manifest.csv` for the full 71-study manifest with the
`included_in_lda` flag, and `corpus/primary_studies_manifest.csv` for the
66-study LDA analytical corpus with extraction-status detail.

## Counts

- Total included studies (71_Final_SMR + Master Data): 71
- Primary studies (Master Data): 66
- Secondary studies (Master Data): 5
- PDFs in `66_Primery_Study/`: 66
- PDFs in `71_Final_SMR/`: 71
- Matched primary PDFs to Master Data rows: 66
- Unmatched PDFs: 0

**N = 66 confirmed.**

## Duplicate checks

- Duplicate Study_IDs: 0
- Duplicate DOIs (non-null): 0
- Duplicate normalized titles: 0
- Duplicate PDF SHA-256 hashes: 0

## Secondary studies excluded from LDA (documented, not modeled)

| Study ID   | Title                                                                                                        |   Year | DOI                           |
|:-----------|:-------------------------------------------------------------------------------------------------------------|-------:|:------------------------------|
| S04        | A Review on Code Generation with LLMs: Application and Evaluation                                            |   2023 | 10.1109/MedAI59581.2023.00044 |
| S37        | Exploring Human-Centered Approaches in Generative AI and Introductory Programming Research: A Scoping Review |   2024 | 10.1145/3689535.3689553       |
| S67        | Hallucination by Code Generation LLMs: Taxonomy, Benchmarks, Mitigation, and Challenges                      |   2025 | nan                           |
| S68        | Novice Developers’ Perspectives on Adopting LLMs for Software Development: A Systematic Literature Review    |   2024 | 10.48550/arXiv.2503.07556     |
| S69        | SoK: Exploring Hallucinations and Security Risks in AI-Assisted Software Development                         |   2025 | 10.48550/arXiv.2502.18468     |

## Matching method

PDF filenames in `66_Primery_Study/` were matched to `Master Data` rows in
`EMSE_MASTER_REFERENCE_v6_4_FINAL.xlsx` by normalized-title matching (lowercased,
punctuation-stripped, leading numeric/S-prefix removed), with containment and token-Jaccard
(>= 0.6) fallbacks for titles altered by filesystem-safe renaming. All matches were 1:1;
no PDF required manual disambiguation beyond the automated fallback.

## Notes

- Abstract/keyword availability per study is populated in `data/metadata_representation.csv`
  by the extraction step (Section 4/5), not in this manifest.
- The five secondary studies are documented here for completeness but are never extracted,
  preprocessed, or modeled.
