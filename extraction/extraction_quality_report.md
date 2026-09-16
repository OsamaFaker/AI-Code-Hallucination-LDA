# Extraction Quality Report

Parser: PyMuPDF (fitz) PyMuPDF 1.28.2: Python bindings for the MuPDF 1.28.2 library.
Python 3.11 running on win32 (64-bit).
. OCR was not required for any of the 66 primary
studies (all yielded machine-readable text via direct extraction).

## Analysis A (metadata) diagnostics

- Studies with missing abstract (heuristic extraction failed): 0 / 66
- Studies with missing author keywords: 24 / 66
- Missing keywords fall back to Title + Abstract only, per protocol Section 5.

## Analysis B (full text) diagnostics

- Studies where automatic section segmentation found zero recognized headings
  (fallback: full cleaned page body retained instead of section-restricted body): 0 / 66
- Cleaned body word count: mean=7351,
  median=6842,
  min=1674, max=26848

## Per-study flags

Study_ID            flags
     S71 missing_keywords
     S66 missing_keywords
     S09 missing_keywords
     S11 missing_keywords
     S14 missing_keywords
     S18 missing_keywords
     S21 missing_keywords
     S22 missing_keywords
     S23 missing_keywords
     S24 missing_keywords
     S26 missing_keywords
     S31 missing_keywords
     S35 missing_keywords
     S38 missing_keywords
     S41 missing_keywords
     S45 missing_keywords
     S62 missing_keywords
     S47 missing_keywords
     S48 missing_keywords
     S50 missing_keywords
     S51 missing_keywords
     S52 missing_keywords
     S56 missing_keywords
     S58 missing_keywords

## Method notes

- Running headers/footers removed by detecting lines repeated in the first/last 3 lines of
  >=40% of a document's pages.
- Boilerplate (copyright/ACM-ISBN/DOI lines/permission notices/bare page numbers) removed by
  regex pattern match.
- Section segmentation uses heading-line detection (short lines matching a canonical heading
  vocabulary: Introduction, Background/Related Work, Methodology, Results, Discussion,
  Conclusion; References/Acknowledgements/Appendix mapped to DROP). This is heuristic and
  imperfect across heterogeneous camera-ready layouts (ACM/IEEE/Springer/MDPI/arXiv); studies
  where no heading was recognized fall back to the full cleaned page body (front matter,
  author metadata already substantially stripped by the header/footer and boilerplate passes,
  but not by section segmentation) so no study is silently dropped from Analysis B.
- No missing text is invented. Where abstract/keywords cannot be reliably located, the field
  is left empty and recorded as such (never imputed).
