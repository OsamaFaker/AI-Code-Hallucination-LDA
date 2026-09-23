# Full-Text Extraction Report

- Studies processed: **66**
- OCR/manual-inspection triggers: **1** (Tesseract is not installed on this machine; any trigger requires manual review before Stage 1)
- Low-confidence section detection: **1**
- Substantive token count — min 1531, max 26348, mean 6806

## OCR / manual-inspection triggers

| Study_ID | pdf_filename | triggers | chars_per_page | alpha_ratio | bad_char_ratio |
|---|---|---|---|---|---|
| S32 | Evaluating_Large_Language_Models_in_Class-Level_Code_Generation.pdf | excess_replacement_or_control_chars | 7395.0 | 0.8652 | 0.01108 |

## Known residual extraction artifacts (manually inspected)

Confirmed non-systemic, sub-paragraph leakage that survived the general cleaning rules; see `qa_scan_fulltext.py` for the corpus-wide scan that found these.

- **S17**: ~2 lines of page-1 footnote text (funding acknowledgement, 'Communicated by:' line, author contribution note) extracted immediately after the 'Introduction' heading due to PDF footnote ordering; and a one-sentence 'Conflict of interest' statement glued inline (no line break) near the References boundary.
- **S64**: One-sentence 'Conflict of interest' statement glued inline (no line break, title-case so not caught by the ALL-CAPS inline-heading fallback) shortly before the References boundary.

## Low-confidence section detection (manual spot-check candidates)

| Study_ID | pdf_filename | start_heading | end_heading | substantive_tokens |
|---|---|---|---|---|
| S34 | Experiences and Challenges in AI-Driven Modular Software.pdf | introduction | references_inline_caps | 8934 |

## Full extraction summary

| Study_ID | pages | section_detection | substantive_tokens | ocr_trigger |
|---|---|---|---|---|
| S01 | 6 | high | 3617 | False |
| S02 | 9 | high | 3675 | False |
| S03 | 12 | high | 7798 | False |
| S05 | 7 | high | 4378 | False |
| S06 | 10 | high | 4928 | False |
| S07 | 10 | high | 2591 | False |
| S08 | 41 | high | 1531 | False |
| S09 | 27 | high | 11848 | False |
| S10 | 9 | high | 7004 | False |
| S11 | 7 | high | 2563 | False |
| S12 | 5 | high | 3865 | False |
| S13 | 12 | high | 8359 | False |
| S14 | 22 | high | 9867 | False |
| S15 | 11 | high | 7217 | False |
| S16 | 9 | high | 5910 | False |
| S17 | 48 | high | 19945 | False |
| S18 | 5 | high | 2901 | False |
| S19 | 8 | high | 5798 | False |
| S20 | 34 | high | 8963 | False |
| S21 | 10 | high | 4187 | False |
| S22 | 9 | high | 4054 | False |
| S23 | 9 | high | 4979 | False |
| S24 | 10 | high | 4788 | False |
| S25 | 18 | high | 5696 | False |
| S26 | 23 | high | 8970 | False |
| S27 | 11 | high | 8097 | False |
| S28 | 10 | high | 4246 | False |
| S29 | 11 | high | 7574 | False |
| S30 | 18 | high | 6420 | False |
| S31 | 22 | high | 4889 | False |
| S32 | 13 | high | 9820 | True |
| S33 | 7 | high | 4665 | False |
| S34 | 18 | low | 8934 | False |
| S35 | 12 | high | 2366 | False |
| S36 | 18 | high | 7560 | False |
| S38 | 10 | high | 4283 | False |
| S39 | 6 | high | 3623 | False |
| S40 | 5 | high | 3492 | False |
| S41 | 6 | high | 2593 | False |
| S42 | 16 | high | 12599 | False |
| S43 | 18 | high | 14191 | False |
| S44 | 6 | high | 3186 | False |
| S45 | 27 | high | 12931 | False |
| S46 | 19 | high | 2504 | False |
| S47 | 13 | high | 7671 | False |
| S48 | 15 | high | 11390 | False |
| S49 | 7 | high | 3513 | False |
| S50 | 37 | high | 26348 | False |
| S51 | 18 | high | 5210 | False |
| S52 | 19 | high | 13680 | False |
| S53 | 12 | high | 8391 | False |
| S54 | 9 | high | 3856 | False |
| S55 | 4 | high | 2652 | False |
| S56 | 22 | high | 9547 | False |
| S57 | 11 | high | 8661 | False |
| S58 | 22 | high | 9967 | False |
| S59 | 12 | high | 7582 | False |
| S60 | 22 | high | 8370 | False |
| S61 | 10 | high | 7601 | False |
| S62 | 39 | high | 4330 | False |
| S63 | 5 | high | 2819 | False |
| S64 | 31 | high | 9857 | False |
| S65 | 7 | high | 4218 | False |
| S66 | 23 | high | 5164 | False |
| S70 | 12 | high | 7273 | False |
| S71 | 7 | high | 1676 | False |
