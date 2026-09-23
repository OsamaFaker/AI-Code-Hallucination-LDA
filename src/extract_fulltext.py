"""
Stage 0 — Full-text extraction (Analysis B raw material).

Per PRE_EXECUTION_ANALYSIS_PLAN.md SS3: PyMuPDF page-by-page extraction,
repeated header/footer removal, section-boundary detection (retain
Introduction..Conclusion; strip references/bios/affiliations/publisher
boilerplate/emails/URLs/OCR garbage), Unicode NFKC normalization,
dehyphenation, control-character removal, whitespace normalization.

OCR fallback triggers (logged, not auto-remediated -- Tesseract is not
installed on this machine; any trigger is routed to manual inspection):
  (a) total extracted text < 500 chars or < 100 whitespace-tokens
  (b) mean chars/page < 200
  (c) alphabetic-character ratio < 0.60
  (d) > 1% of characters are U+FFFD or non-whitespace control characters

No LDA fitting here -- deterministic text preparation only.
"""

from __future__ import annotations

import csv
import re
import unicodedata
from pathlib import Path

import fitz  # PyMuPDF

# Known, manually-inspected residual extraction artifacts that survived the
# general-purpose cleaning rules (see qa_scan_fulltext.py). Each is a single
# glued-inline heading/sentence (a few dozen words) inside a multi-thousand-
# word document -- confirmed non-systemic and left in place rather than
# writing an increasingly narrow regex for a single occurrence, per the
# corpus-wide/non-topic-specific rule in PRE_EXECUTION_ANALYSIS_PLAN.md SS5.
KNOWN_RESIDUAL_ARTIFACTS = {
    "S17": "~2 lines of page-1 footnote text (funding acknowledgement, "
           "'Communicated by:' line, author contribution note) extracted "
           "immediately after the 'Introduction' heading due to PDF footnote "
           "ordering; and a one-sentence 'Conflict of interest' statement "
           "glued inline (no line break) near the References boundary.",
    "S64": "One-sentence 'Conflict of interest' statement glued inline (no "
           "line break, title-case so not caught by the ALL-CAPS inline-"
           "heading fallback) shortly before the References boundary.",
}

ROOT = Path(__file__).resolve().parents[1]
PDF_DIR = ROOT / "66_Primery_Study"
CORPUS_AUDIT_CSV = ROOT / "corpus" / "corpus_audit.csv"
FULLTEXT_DIR = ROOT / "extraction" / "fulltext"
OUT_CSV = ROOT / "extraction" / "fulltext_extraction_report.csv"
OUT_MD = ROOT / "extraction" / "fulltext_extraction_report.md"

CONTROL_CHAR_RE = re.compile(r"[\x00-\x08\x0b\x0c\x0e-\x1f\x7f]")
REPLACEMENT_CHAR = "�"

# --- Section heading anchors (start of a stripped line, optionally numbered) ---
NUM_PREFIX = r"^\s*(?:(?:[0-9]{1,2}(?:\.[0-9]+)*\.?|[IVXLC]{1,5}\.?)\s+)?"

START_HEADINGS = {
    "introduction": r"introduction",
    "background": r"background",
    "related_work": r"related\s+work[s]?",
    "methodology": r"method(?:ology|s)?",
}
END_HEADINGS = {
    "acknowledg": r"acknowledge?ments?",
    "references": r"references?",
    "bibliography": r"bibliography",
    "appendix": r"appendix",
    # Publisher-metadata subsections that commonly appear between Conclusion
    # and References (esp. Taylor & Francis / Springer / Elsevier journals) --
    # not substantive content, so also valid end-of-body boundaries.
    "disclosure": r"disclosure(?:\s+statement)?",
    "funding": r"funding(?:\s+(?:statement|information))?",
    "data_availability": r"data\s+availability(?:\s+statement)?",
    "orcid": r"orcid",
    "conflict_of_interest": r"conflicts?\s+of\s+interest",
    "author_contributions": r"author(?:s)?['’]?\s+contributions?",
    "supplementary_material": r"supplementary\s+material[s]?",
}
BODY_SECTION_HEADINGS = {
    "results": r"results?(?:\s+and\s+discussion)?",
    "discussion": r"discussion",
    "conclusion": r"conclusions?(?:\s+and\s+future\s+work)?",
}


def compile_heading_re(phrase: str) -> re.Pattern:
    # Allow a short trailing qualifier on the same line, e.g. "INTRODUCTION AND
    # BACKGROUND", "CONCLUSION AND FUTURE WORK" -- but keep it bounded so a
    # body sentence that happens to start a wrapped line with the phrase isn't
    # mistaken for a heading.
    return re.compile(
        NUM_PREFIX + r"(" + phrase + r")\b(?:\s*[:\-]?\s*(?:and|&)\s+[a-z ]{0,30})?\s*\.?\s*$",
        re.IGNORECASE | re.MULTILINE,
    )


START_RES = {k: compile_heading_re(v) for k, v in {**START_HEADINGS, **BODY_SECTION_HEADINGS}.items()}
END_RES = {k: compile_heading_re(v) for k, v in END_HEADINGS.items()}
ABSTRACT_RE = compile_heading_re("abstract")

# Fallback for headings that PDF extraction glues onto the end of the
# preceding paragraph with no line break at all (seen e.g. as "...future
# work. REFERENCES Amazon Web Services..."). A bare, case-SENSITIVE ALL-CAPS
# whole-word match is a low-false-positive signal here: running prose refers
# to "references"/"the appendix" in lowercase or title case; an all-caps
# occurrence of the bare word is reliably a rendered heading, not body text.
END_HEADINGS_CASE_SENSITIVE_RE = re.compile(
    r"\b(ACKNOWLEDGE?MENTS?|REFERENCES?|BIBLIOGRAPHY|APPENDIX)\b"
)


def find_repeated_lines(pages: list[str], min_page_fraction: float = 0.3) -> set[str]:
    """Lines (stripped) that recur on >= min_page_fraction of pages -- treated as
    running headers/footers and removed page-by-page."""
    from collections import Counter

    counts: Counter[str] = Counter()
    for p in pages:
        lines = {ln.strip() for ln in p.splitlines() if ln.strip()}
        counts.update(lines)
    threshold = max(2, int(len(pages) * min_page_fraction))
    return {ln for ln, c in counts.items() if c >= threshold and len(ln) < 120}


PAGE_NUMBER_RE = re.compile(r"^\s*(?:page\s*)?\d{1,4}\s*(?:of\s*\d{1,4})?\s*$", re.IGNORECASE)
EMAIL_RE = re.compile(r"\S+@\S+\.\S+")
URL_RE = re.compile(r"(?:https?://|www\.)\S+")
DOI_ISBN_RE = re.compile(r"\b(?:DOI|ISBN)\s*[:#]?\s*[\w./-]+", re.IGNORECASE)
COPYRIGHT_RE = re.compile(
    r"(?:©|copyright|permission to make digital|all rights reserved|"
    r"acm reference format|isbn\s+978|"
    r"authorized licensed use limited to|downloaded on .{0,40}from ieee xplore|"
    r"restrictions apply|"
    r"downloaded from .{0,80}wiley online library|"
    r"terms and conditions .{0,40}on wiley online library|"
    r"governed by the applicable creative commons|"
    # Remaining fragments of the standard ACM permission-to-copy notice, seen
    # split across separate PDF lines from the "permission to make digital..."
    # opening sentence caught above.
    r"classroom use is granted without fee|"
    r"abstracting with credit is permitted|"
    r"request permissions from|"
    r"copies bear this notice and the full citation|"
    r"to copy otherwise,?\s*or republish|"
    r"redistribute to lists,?\s*requires prior|"
    r"^acm\s+\$\d)", re.IGNORECASE
)
REPEATED_CHAR_GARBAGE_RE = re.compile(r"(.)\1{6,}")  # 7+ identical repeated chars = garbage


def clean_line(line: str) -> str | None:
    s = line.strip()
    if not s:
        return None
    if PAGE_NUMBER_RE.match(s):
        return None
    if EMAIL_RE.search(s) and len(s) < 200:
        s = EMAIL_RE.sub(" ", s)
    s = URL_RE.sub(" ", s)
    s = DOI_ISBN_RE.sub(" ", s)
    if COPYRIGHT_RE.search(s) and len(s) < 600:
        return None
    s = REPEATED_CHAR_GARBAGE_RE.sub(" ", s)
    s = s.strip()
    return s if s else None


def dehyphenate(text: str) -> str:
    # word-\nword -> wordword (line-break hyphenation)
    text = re.sub(r"(\w)-\s*\n\s*(\w)", r"\1\2", text)
    return text


def normalize_text(text: str) -> str:
    text = unicodedata.normalize("NFKC", text)
    text = CONTROL_CHAR_RE.sub(" ", text)
    text = text.replace(REPLACEMENT_CHAR, " ")
    text = dehyphenate(text)
    text = re.sub(r"[ \t]+", " ", text)
    text = re.sub(r"\n{3,}", "\n\n", text)
    return text.strip()


def quality_flags(raw_text: str, n_pages: int) -> dict:
    chars = len(raw_text)
    tokens = len(raw_text.split())
    alpha = sum(1 for c in raw_text if c.isalpha())
    non_ws = sum(1 for c in raw_text if not c.isspace())
    alpha_ratio = (alpha / non_ws) if non_ws else 0.0
    bad_chars = raw_text.count(REPLACEMENT_CHAR) + len(CONTROL_CHAR_RE.findall(raw_text))
    bad_ratio = (bad_chars / len(raw_text)) if raw_text else 1.0
    chars_per_page = chars / n_pages if n_pages else 0.0

    triggers = []
    if chars < 500 or tokens < 100:
        triggers.append("total_text_too_short")
    if chars_per_page < 200:
        triggers.append("chars_per_page_too_low")
    if alpha_ratio < 0.60:
        triggers.append("alpha_ratio_too_low")
    if bad_ratio > 0.01:
        triggers.append("excess_replacement_or_control_chars")

    return {
        "raw_chars": chars,
        "raw_tokens": tokens,
        "chars_per_page": round(chars_per_page, 1),
        "alpha_ratio": round(alpha_ratio, 4),
        "bad_char_ratio": round(bad_ratio, 5),
        "ocr_triggers": ";".join(triggers),
        "needs_ocr_or_manual_inspection": bool(triggers),
    }


STANDALONE_NUMERAL_LINE_RE = re.compile(
    r"(?m)^\s*([0-9]{1,2}(?:\.[0-9]+)*\.?|[IVXLC]{1,5}\.?)\s*\n"
    r"(?:\s*[|\-–—.:]\s*\n)?"  # optional single separator-only line (e.g. "|")
    r"(?=\s*\S)"
)


def merge_split_heading_numbers(text: str) -> str:
    """PyMuPDF frequently extracts a numbered heading's numeral and its text
    as separate lines (e.g. '1\\nINTRODUCTION', or '1\\n|\\nINTRODUCTION' in
    journals that typeset a pipe separator). Merge the numeral (and any lone
    separator line) into the following line so heading regexes can match."""
    return STANDALONE_NUMERAL_LINE_RE.sub(r"\1 ", text)


# "Surname, X. ... (YYYY)" citation pattern. The gap between the author-
# initial and the year is allowed to cross a single line-wrap (PDF text
# extraction frequently breaks a citation's author list mid-name), so
# [\s\S] is used instead of "." for that span.
CITATION_RE = re.compile(
    r"[A-Z][A-Za-z'\-]+,?\s+[A-Z]\.(?:\s?[A-Z]\.)?[\s\S]{0,80}?\((?:19|20)\d{2}[a-z]?\)"
)


def strip_trailing_references_heuristic(text: str, search_from: int = 0) -> int | None:
    """Fallback for documents with no detectable References/Bibliography
    heading: locate the character offset from which citation-pattern matches
    ('Surname, X. ... (YYYY)') occur at high density for the remainder of the
    document, and treat that as the reference-list start. Operates on
    character windows (not text lines) since PDF line-wrapping inside a
    single reference is common and breaks line-based detection. Deterministic,
    corpus-wide, used only when no explicit end-heading was found. Returns
    None if no confident boundary is found (text is then left untouched)."""
    tail = text[search_from:]
    n = len(tail)
    if n < 1000:
        return None
    matches = [m.start() for m in CITATION_RE.finditer(tail)]
    if not matches:
        return None

    window = 600
    step = 200
    min_body_fraction = 0.4  # never cut before 40% into the remaining text
    start_scan = int(n * min_body_fraction)

    # Density (matches per window) at each scan point, then find the earliest
    # point after which density stays consistently high through to the end.
    scan_points = list(range(start_scan, n - window, step))
    if not scan_points:
        return None
    densities = []
    mi = 0
    for pos in scan_points:
        while mi < len(matches) and matches[mi] < pos:
            mi += 1
        count = sum(1 for x in matches[mi:] if x < pos + window)
        densities.append(count)

    threshold = 2  # >=2 citation-pattern matches per 600-char window
    # Find earliest scan point after which density stays >= threshold for at
    # least 80% of all remaining scan points (tolerates a few sparse windows
    # inside a reference list without losing the boundary).
    for idx, pos in enumerate(scan_points):
        remaining = densities[idx:]
        if not remaining:
            continue
        high = sum(1 for d in remaining if d >= threshold)
        if densities[idx] >= threshold and high / len(remaining) >= 0.8:
            # tighten: walk back through consecutive matches while the gap
            # between them stays small (< 500 chars), to find the true start
            # of this citation run rather than the window's scan point.
            j = mi if mi < len(matches) else len(matches) - 1
            while j > 0 and (matches[j] - matches[j - 1]) < 500:
                j -= 1
            return search_from + matches[j]
    return None


def find_section_span(cleaned_text: str) -> dict:
    """Locate the [start_of_Introduction .. end_before_References] span.
    Caller must pass text already through merge_split_heading_numbers(), since
    returned offsets index into exactly the string passed in here."""
    start_match = START_RES["introduction"].search(cleaned_text)
    start_key = "introduction"
    if not start_match:
        for key in ("background", "related_work"):
            m = START_RES[key].search(cleaned_text)
            if m:
                start_match, start_key = m, key
                break

    search_from = start_match.end() if start_match else 0

    end_candidates = []
    for key, pat in END_RES.items():
        m = pat.search(cleaned_text, pos=search_from)
        if m:
            end_candidates.append((m.start(), key))
    end_candidates.sort()

    if start_match and end_candidates:
        return {
            "start_pos": start_match.start(),
            "end_pos": end_candidates[0][0],
            "start_heading": start_key,
            "end_heading": end_candidates[0][1],
            "confidence": "high",
        }
    if end_candidates:
        # No clear start anchor: assume body starts after abstract/keywords block,
        # i.e. right after Abstract heading if found, else from the very top.
        abs_match = ABSTRACT_RE.search(cleaned_text)
        start_pos = abs_match.end() if abs_match else 0
        return {
            "start_pos": start_pos,
            "end_pos": end_candidates[0][0],
            "start_heading": "abstract_fallback" if abs_match else "document_start",
            "end_heading": end_candidates[0][1],
            "confidence": "low",
        }
    if start_match:
        cs_match = END_HEADINGS_CASE_SENSITIVE_RE.search(cleaned_text, pos=search_from)
        if cs_match:
            return {
                "start_pos": start_match.start(),
                "end_pos": cs_match.start(),
                "start_heading": start_key,
                "end_heading": f"{cs_match.group(1).lower()}_inline_caps",
                "confidence": "low",
            }
        # No heading-based end boundary at all: fall back to the citation-
        # density heuristic to still strip an unheaded reference list rather
        # than silently including it in the substantive text.
        heuristic_pos = strip_trailing_references_heuristic(cleaned_text, search_from)
        return {
            "start_pos": start_match.start(),
            "end_pos": heuristic_pos if heuristic_pos is not None else len(cleaned_text),
            "start_heading": start_key,
            "end_heading": "citation_density_heuristic" if heuristic_pos is not None else "document_end",
            "confidence": "low",
        }
    cs_match = END_HEADINGS_CASE_SENSITIVE_RE.search(cleaned_text)
    if cs_match:
        return {
            "start_pos": 0,
            "end_pos": cs_match.start(),
            "start_heading": "document_start",
            "end_heading": f"{cs_match.group(1).lower()}_inline_caps",
            "confidence": "low",
        }
    heuristic_pos = strip_trailing_references_heuristic(cleaned_text, 0)
    return {
        "start_pos": 0,
        "end_pos": heuristic_pos if heuristic_pos is not None else len(cleaned_text),
        "start_heading": "document_start",
        "end_heading": "citation_density_heuristic" if heuristic_pos is not None else "document_end",
        "confidence": "low",
    }


def process_pdf(pdf_path: Path) -> tuple[dict, str]:
    doc = fitz.open(pdf_path)
    raw_pages = [page.get_text() for page in doc]
    doc.close()
    n_pages = len(raw_pages)
    raw_text = "\n".join(raw_pages)

    qflags = quality_flags(raw_text, n_pages)

    repeated = find_repeated_lines(raw_pages)
    cleaned_pages = []
    for p in raw_pages:
        kept_lines = []
        for ln in p.splitlines():
            if ln.strip() in repeated:
                continue
            cl = clean_line(ln)
            if cl:
                kept_lines.append(cl)
        cleaned_pages.append("\n".join(kept_lines))
    cleaned_text = normalize_text("\n".join(cleaned_pages))
    cleaned_text = merge_split_heading_numbers(cleaned_text)

    span = find_section_span(cleaned_text)
    substantive = cleaned_text[span["start_pos"]:span["end_pos"]].strip()

    record = {
        "n_pages": n_pages,
        **qflags,
        "section_start_heading": span["start_heading"],
        "section_end_heading": span["end_heading"],
        "section_detection": span["confidence"],
        "substantive_char_count": len(substantive),
        "substantive_token_count": len(substantive.split()),
        "repeated_header_footer_lines_removed": len(repeated),
    }
    return record, substantive


def main() -> None:
    FULLTEXT_DIR.mkdir(parents=True, exist_ok=True)
    OUT_CSV.parent.mkdir(parents=True, exist_ok=True)

    with open(CORPUS_AUDIT_CSV, newline="", encoding="utf-8") as f:
        mapping = list(csv.DictReader(f))
    assert len(mapping) == 66

    rows = []
    for m in sorted(mapping, key=lambda x: x["Study_ID"]):
        sid = m["Study_ID"]
        pdf_path = PDF_DIR / m["pdf_filename"]
        record, substantive = process_pdf(pdf_path)
        record["Study_ID"] = sid
        record["pdf_filename"] = m["pdf_filename"]
        rows.append(record)

        out_txt = FULLTEXT_DIR / f"{sid}.txt"
        out_txt.write_text(substantive, encoding="utf-8")

    fieldnames = [
        "Study_ID", "pdf_filename", "n_pages",
        "raw_chars", "raw_tokens", "chars_per_page", "alpha_ratio", "bad_char_ratio",
        "ocr_triggers", "needs_ocr_or_manual_inspection",
        "repeated_header_footer_lines_removed",
        "section_start_heading", "section_end_heading", "section_detection",
        "substantive_char_count", "substantive_token_count",
    ]
    with open(OUT_CSV, "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=fieldnames)
        w.writeheader()
        for r in rows:
            w.writerow(r)

    n_ocr = sum(1 for r in rows if r["needs_ocr_or_manual_inspection"])
    n_low_conf = sum(1 for r in rows if r["section_detection"] == "low")
    tok_counts = [r["substantive_token_count"] for r in rows]

    with open(OUT_MD, "w", encoding="utf-8") as f:
        f.write("# Full-Text Extraction Report\n\n")
        f.write(f"- Studies processed: **{len(rows)}**\n")
        f.write(f"- OCR/manual-inspection triggers: **{n_ocr}**"
                " (Tesseract is not installed on this machine; any trigger requires "
                "manual review before Stage 1)\n")
        f.write(f"- Low-confidence section detection: **{n_low_conf}**\n")
        f.write(f"- Substantive token count — min {min(tok_counts)}, max {max(tok_counts)}, "
                f"mean {sum(tok_counts)/len(tok_counts):.0f}\n\n")

        if n_ocr:
            f.write("## OCR / manual-inspection triggers\n\n")
            f.write("| Study_ID | pdf_filename | triggers | chars_per_page | alpha_ratio | bad_char_ratio |\n")
            f.write("|---|---|---|---|---|---|\n")
            for r in rows:
                if r["needs_ocr_or_manual_inspection"]:
                    f.write(f"| {r['Study_ID']} | {r['pdf_filename']} | {r['ocr_triggers']} | "
                            f"{r['chars_per_page']} | {r['alpha_ratio']} | {r['bad_char_ratio']} |\n")
            f.write("\n")

        if KNOWN_RESIDUAL_ARTIFACTS:
            f.write("## Known residual extraction artifacts (manually inspected)\n\n")
            f.write("Confirmed non-systemic, sub-paragraph leakage that survived the general "
                    "cleaning rules; see `qa_scan_fulltext.py` for the corpus-wide scan that "
                    "found these.\n\n")
            for sid, note in KNOWN_RESIDUAL_ARTIFACTS.items():
                f.write(f"- **{sid}**: {note}\n")
            f.write("\n")

        if n_low_conf:
            f.write("## Low-confidence section detection (manual spot-check candidates)\n\n")
            f.write("| Study_ID | pdf_filename | start_heading | end_heading | substantive_tokens |\n")
            f.write("|---|---|---|---|---|\n")
            for r in rows:
                if r["section_detection"] == "low":
                    f.write(f"| {r['Study_ID']} | {r['pdf_filename']} | {r['section_start_heading']} | "
                            f"{r['section_end_heading']} | {r['substantive_token_count']} |\n")
            f.write("\n")

        f.write("## Full extraction summary\n\n")
        f.write("| Study_ID | pages | section_detection | substantive_tokens | ocr_trigger |\n")
        f.write("|---|---|---|---|---|\n")
        for r in rows:
            f.write(f"| {r['Study_ID']} | {r['n_pages']} | {r['section_detection']} | "
                    f"{r['substantive_token_count']} | {r['needs_ocr_or_manual_inspection']} |\n")

    print(f"Processed {len(rows)} studies")
    print(f"OCR/manual-inspection triggers: {n_ocr}")
    print(f"Low-confidence section detection: {n_low_conf}")
    print(f"Substantive tokens — min {min(tok_counts)}, max {max(tok_counts)}, "
          f"mean {sum(tok_counts)/len(tok_counts):.0f}")
    print(f"Wrote {OUT_CSV}")
    print(f"Wrote {OUT_MD}")
    print(f"Per-study substantive text written to {FULLTEXT_DIR}")


if __name__ == "__main__":
    main()
