"""
Stage 0 -- Metadata construction (Analysis A raw material).

Per PRE_EXECUTION_ANALYSIS_PLAN.md SS2: title taken verbatim from Master Data
(authoritative); Abstract and Keywords extracted from each PDF's own front
matter (page 1-2) via heading-anchored pattern rules. Every extraction is
scored high/medium/low; `medium`/`low` never fall back to title-only
automatically -- both require manual verification against the source PDF
before metadata_documents.csv is frozen (done inline in this script via the
MANUALLY_VERIFIED_METADATA override table, exactly as corpus_audit.py does
for Study_ID matching).

No LDA fitting here -- deterministic text preparation only.
"""

from __future__ import annotations

import csv
import re
from pathlib import Path

import fitz  # PyMuPDF
import openpyxl

from extract_fulltext import (
    clean_line, find_repeated_lines, normalize_text, merge_split_heading_numbers,
)

ROOT = Path(__file__).resolve().parents[1]
PROJECT_ROOT = ROOT.parent
MASTER_XLSX = PROJECT_ROOT / "EMSE_MASTER_REFERENCE_v6_4_FINAL.xlsx"
PDF_DIR = ROOT / "66_Primery_Study"
CORPUS_AUDIT_CSV = ROOT / "corpus" / "corpus_audit.csv"
OUT_CSV = ROOT / "corpus" / "metadata_documents.csv"
OUT_MD = ROOT / "corpus" / "metadata_extraction_report.md"

# --- Heading anchors for the metadata front-matter block ---
# ABSTRACT_START: allows the heading to be immediately followed by content
# on the SAME line via an em-dash/colon (common IEEE style: "Abstract—Text..."),
# OR alone on its own line (common ACM/Springer style).
ABSTRACT_START_RE = re.compile(
    r"(?im)^\s*abstract\s*[-—:]?\s*(.*)$"
)
KEYWORDS_START_RE = re.compile(
    r"(?im)^\s*(?:keywords|index\s+terms|additional\s+key\s+words\s+and\s+phrases)\s*[-—:]?\s*(.*)$"
)
# Any of these ends the abstract or the keywords block.
NEXT_SECTION_RE = re.compile(
    r"(?im)^\s*(?:"
    r"abstract|keywords|index\s+terms|additional\s+key\s+words\s+and\s+phrases|"
    r"ccs\s+concepts|acm\s+reference\s+format|"
    r"(?:[0-9]{1,2}\.?\s+|[IVXLC]{1,4}\.?\s+)?introduction\b|"
    r"general\s+terms|categories\s+and\s+subject\s+descriptors|"
    r"article\s+history"
    r")"
)

# ACM PACM-series journals (Proc. ACM Program. Lang. / Proc. ACM Softw. Eng. /
# Proc. ACM Hum.-Comput. Interact. / etc.) and some other venues render the
# abstract paragraph with no visible "Abstract" heading at all -- it is
# typographically distinguished (different font) in the original PDF, a
# distinction PyMuPDF's plain-text extraction loses. Fallback: find the last
# ALL-CAPS "NAME, Affiliation, Country" author line in the front matter and
# take the following paragraph, up to the next recognized heading, as the
# abstract. Confidence is "medium" (heuristic, not heading-anchored) and every
# such case is manually verified (see MANUALLY_VERIFIED_METADATA) rather than
# trusted blindly.
AUTHOR_LINE_RE = re.compile(r"(?m)^[A-ZÀ-ÖØ-Þ][A-ZÀ-ÖØ-Þ.\-\s]{2,60},\s.{3,80}$")

# Some ACM PACM-series venues print their own self-citation ("Ranim Khojah,
# Mazen Mohamad, ... 2024. Beyond Code Generation: ...") directly after the
# "Additional Key Words and Phrases" list with no "ACM Reference Format"
# label at all, so it isn't caught by NEXT_SECTION_RE and bleeds into the
# extracted keywords. Detect the "Name, Name, and Name. YYYY. " citation
# pattern generally and truncate there.
_LETTER = r"A-Za-zÀ-ÖØ-öø-ÿ"  # ASCII + Latin-1 Supplement/Extended-A accented letters
                               # (covers most European author names, e.g. "Gábor", "Zsó")
_WORD = rf"(?:[A-Z]\.|[{_LETTER}\-]+)"  # a plain word, or a single-letter initial with its period
_NAME = rf"[A-Z][{_LETTER}\-]*(?:\s{_WORD}){{0,5}}"  # no embedded periods outside initials,
                                                       # so this can't run through a real sentence end
SELF_CITATION_TAIL_RE = re.compile(
    rf"{_NAME}(?:,\s{_NAME})*(?:,?\sand\s{_NAME})?\.\s(?:19|20)\d{{2}}\.\s"
)


def strip_self_citation_tail(block: str) -> str:
    m = SELF_CITATION_TAIL_RE.search(block)
    if m and m.start() > 0:
        return block[:m.start()].strip()
    return block

# Common letter-spaced heading artifact from justified/kerned PDF text
# (e.g. "A B S T R A C T", "K E Y W O R D S") -- collapse to normal spelling
# before heading detection. Requires >=4 single letters to avoid false
# positives on short real words rendered with incidental spacing.
LETTER_SPACED_HEADING_RE = re.compile(r"\b(?:[A-Za-z]\s){3,}[A-Za-z]\b")


def collapse_letter_spaced_headings(text: str) -> str:
    def _collapse(m: re.Match) -> str:
        return m.group(0).replace(" ", "")
    return LETTER_SPACED_HEADING_RE.sub(_collapse, text)

# Manual verification log: entries here were individually checked against the
# source PDF for studies whose automated extraction confidence was not
# `high`. Each note records what was confirmed. This is a fixed,
# deterministic override, not a per-run guess -- see plan SS2.
MANUALLY_VERIFIED_METADATA: dict[str, str] = {
    "S09": "Unlabeled-abstract ACM/venue template (no 'Abstract' heading in source PDF); "
           "author-block fallback extraction checked against the PDF and confirmed correct. "
           "No keywords/index terms section present in this paper -- confirmed genuinely absent.",
    "S14": "Unlabeled-abstract ACM PACM-series template; author-block fallback extraction and "
           "'Additional Key Words and Phrases' keywords checked against the PDF and confirmed correct.",
    "S26": "Unlabeled-abstract ACM PACM-series template; author-block fallback extraction checked "
           "against the PDF and confirmed correct. No keywords section present -- confirmed genuinely absent.",
    "S38": "Unlabeled-abstract ACM PACM-series template; author-block fallback extraction and "
           "'Additional Key Words and Phrases' keywords checked against the PDF and confirmed correct.",
    "S45": "Unlabeled-abstract ACM PACM-series template; author-block fallback extraction checked "
           "against the PDF and confirmed correct. Automated self-citation stripping could not "
           "cleanly separate the keywords list ('Program Synthesis, AI Assistants, Grounded Theory') "
           "from the immediately following author list ('Shraddha Barke, Michael B. James, and Nadia "
           "Polikarpova...') since no comma separates them in the source PDF -- keywords field manually "
           "corrected to the verified list.",
    "S56": "Unlabeled-abstract ACM PACM-series template; author-block fallback extraction and "
           "'Additional Key Words and Phrases' keywords checked against the PDF and confirmed correct.",
    "S62": "Unlabeled-abstract ACM PACM-series template; author-block fallback extraction and "
           "'Additional Key Words and Phrases' keywords checked against the PDF and confirmed correct.",
    "S28": "Found during the SS2-step-4 rule-calibration spot-check (not originally flagged low/medium): "
           "an unlabeled 'Paper Type' field was glued inline onto the end of the Keywords list with no "
           "line break, so it wasn't caught by the line-anchored NEXT_SECTION_RE boundary. Keywords "
           "field manually corrected to the verified list (trailing 'Extreme Programmaing' spelling is "
           "verbatim from the source paper, not a transcription error).",
    "S10": "Found during a corpus-wide residual-pattern scan (not originally flagged low/medium): the "
           "self-citation-stripping heuristic could not separate the keywords list from the following "
           "'Additional Key Words'-style author citation because both are comma-separated Title-Case "
           "phrases with identical surface syntax; the ACM copyright/permission notice (which follows "
           "the citation) also exceeded the length-based cleaning threshold. Keywords field manually "
           "corrected to the verified list against the source PDF.",
    "S27": "Same class of issue as S10 (self-citation and ACM permission-notice bleed); keywords field "
           "manually corrected to the verified list against the source PDF.",
    "S44": "Same class of issue as S10 (self-citation bleed, no comma before the author list); keywords "
           "field manually corrected to the verified list against the source PDF.",
    "S53": "Same class of issue as S10 (self-citation bleed, no comma before the author list); keywords "
           "field manually corrected to the verified list against the source PDF.",
    "S55": "Same class of issue as S10, compounded by the keyword list itself parsing as a valid "
           "comma-separated name-chain (the heuristic's fundamental ambiguity -- keyword lists and "
           "author-name lists share identical surface syntax); keywords field manually corrected to "
           "the verified list against the source PDF.",
    "S15": "Found during a corpus-wide residual-pattern scan for citation/venue-info bleed (not "
           "originally flagged low/medium): same self-citation ambiguity as S55 (keyword list parses "
           "as a valid name-chain from position 0). Keywords field manually corrected to the verified "
           "list against the source PDF.",
}

# Field-level corrections for the one case (S45) where automated self-citation
# stripping could not cleanly resolve the keywords/author-list boundary; see
# MANUALLY_VERIFIED_METADATA note above.
MANUAL_FIELD_OVERRIDES: dict[str, dict[str, str]] = {
    "S45": {"keywords": "Program Synthesis, AI Assistants, Grounded Theory"},
    "S28": {"keywords": "Software Engineering, Code Refactoring, Walkthroughs, "
                         "Extreme Programmaing, GPT-4, ChatGPT"},
    "S10": {"keywords": "ChatGPT, Education, Generative AI, Large Language Models, "
                         "Prompt Engineering, Automated Grading"},
    "S27": {"keywords": "LLM, LLM-based applications, User expectations, "
                         "Perception of Productivity"},
    "S44": {"keywords": "Software Engineering, Software Design, Rapid Prototyping, LLMs, ChatGPT"},
    "S53": {"keywords": "Code Generation, LLM, TDD, Testing, Software Engineering"},
    "S55": {"keywords": "Large Language Models, Code Generation, OOP, UML, AI in Software Engineering"},
    "S15": {"keywords": "Programming Assignment, Code Performance, Tool Support"},
}


def load_title_map() -> dict[str, str]:
    wb = openpyxl.load_workbook(MASTER_XLSX, data_only=True)
    ws = wb["Master Data"]
    rows = list(ws.iter_rows(values_only=True))
    header = rows[0]
    idx = {h: i for i, h in enumerate(header)}
    out = {}
    for r in rows[1:]:
        if r[idx["Study category"]] == "Primary":
            out[r[idx["Study ID"]]] = r[idx["Title"]]
    return out


def clean_front_matter(pdf_path: Path, max_pages: int = 2) -> str:
    doc = fitz.open(pdf_path)
    raw_pages = [doc[i].get_text() for i in range(min(max_pages, len(doc)))]
    doc.close()
    repeated = find_repeated_lines(raw_pages, min_page_fraction=0.5)
    cleaned_pages = []
    for p in raw_pages:
        kept = []
        for ln in p.splitlines():
            if ln.strip() in repeated:
                continue
            cl = clean_line(ln)
            if cl:
                kept.append(cl)
        cleaned_pages.append("\n".join(kept))
    text = normalize_text("\n".join(cleaned_pages))
    text = merge_split_heading_numbers(text)
    text = collapse_letter_spaced_headings(text)
    return text


def extract_block(text: str, start_re: re.Pattern) -> tuple[str | None, str]:
    """Returns (extracted_block_text_or_None, confidence) for the span from
    start_re's match to the next NEXT_SECTION_RE match (or a hard char cap)."""
    m = start_re.search(text)
    if not m:
        return None, "not_found"

    # same-line content after the heading (e.g. "Abstract—Conversational LLMs...")
    same_line_tail = m.group(1).strip() if m.lastindex else ""
    start_pos = m.end()

    end_m = NEXT_SECTION_RE.search(text, pos=start_pos)
    if end_m:
        block = (same_line_tail + "\n" + text[start_pos:end_m.start()]).strip()
        confidence = "high"
    else:
        # Fallback: cap at 3000 chars (generous for any abstract/keywords block)
        block = (same_line_tail + "\n" + text[start_pos:start_pos + 3000]).strip()
        confidence = "medium"

    block = re.sub(r"\s+", " ", block).strip()
    block = strip_self_citation_tail(block)
    if not block:
        return None, "not_found"
    return block, confidence


def extract_abstract_with_author_fallback(text: str) -> tuple[str | None, str]:
    """Try the heading-anchored extraction first; if no 'Abstract' heading
    exists at all (some ACM PACM-series journals render it unlabeled), fall
    back to taking the paragraph after the last author/affiliation line."""
    block, confidence = extract_block(text, ABSTRACT_START_RE)
    if block is not None:
        return block, confidence

    author_matches = list(AUTHOR_LINE_RE.finditer(text))
    if not author_matches:
        return None, "not_found"
    start_pos = author_matches[-1].end()
    end_m = NEXT_SECTION_RE.search(text, pos=start_pos)
    end_pos = end_m.start() if end_m else start_pos + 3000
    block = re.sub(r"\s+", " ", text[start_pos:end_pos]).strip()
    block = strip_self_citation_tail(block)
    if not block:
        return None, "not_found"
    return block, "medium"


def main() -> None:
    titles = load_title_map()
    with open(CORPUS_AUDIT_CSV, newline="", encoding="utf-8") as f:
        mapping = {r["Study_ID"]: r["pdf_filename"] for r in csv.DictReader(f)}
    assert len(mapping) == 66

    rows = []
    for sid in sorted(mapping, key=lambda x: int(x[1:])):
        pdf_path = PDF_DIR / mapping[sid]
        title = titles[sid]
        text = clean_front_matter(pdf_path)

        abstract, abs_conf = extract_abstract_with_author_fallback(text)
        keywords, kw_conf = extract_block(text, KEYWORDS_START_RE)

        overrides = MANUAL_FIELD_OVERRIDES.get(sid, {})
        if "abstract" in overrides:
            abstract = overrides["abstract"]
        if "keywords" in overrides:
            keywords = overrides["keywords"]

        keywords_available = keywords is not None

        if abstract is None:
            extraction_confidence = "low"
        elif abs_conf == "high" and (not keywords_available or kw_conf == "high"):
            extraction_confidence = "high"
        else:
            extraction_confidence = "medium"

        manual_note = MANUALLY_VERIFIED_METADATA.get(sid, "")
        manually_verified = bool(manual_note) or extraction_confidence == "high"

        combined_parts = [title]
        if abstract:
            combined_parts.append(abstract)
        if keywords:
            combined_parts.append(keywords)
        combined_text = "\n\n".join(combined_parts)

        rows.append({
            "Study_ID": sid,
            "pdf_filename": mapping[sid],
            "title": title,
            "abstract": abstract or "",
            "keywords": keywords or "",
            "keywords_available": keywords_available,
            "abstract_confidence": abs_conf,
            "keywords_confidence": kw_conf,
            "extraction_confidence": extraction_confidence,
            "manually_verified": manually_verified,
            "manual_verification_note": manual_note,
            "combined_text": combined_text,
        })

    OUT_CSV.parent.mkdir(parents=True, exist_ok=True)
    fieldnames = [
        "Study_ID", "pdf_filename", "title", "abstract", "keywords",
        "keywords_available", "abstract_confidence", "keywords_confidence",
        "extraction_confidence", "manually_verified", "manual_verification_note",
        "combined_text",
    ]
    with open(OUT_CSV, "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=fieldnames)
        w.writeheader()
        for r in rows:
            w.writerow(r)

    n_high = sum(1 for r in rows if r["extraction_confidence"] == "high")
    n_medium = sum(1 for r in rows if r["extraction_confidence"] == "medium")
    n_low = sum(1 for r in rows if r["extraction_confidence"] == "low")
    n_no_kw = sum(1 for r in rows if not r["keywords_available"])
    n_unverified = sum(1 for r in rows if not r["manually_verified"])

    with open(OUT_MD, "w", encoding="utf-8") as f:
        f.write("# Metadata Extraction Report (Analysis A)\n\n")
        f.write(f"- Studies processed: **{len(rows)}**\n")
        f.write(f"- Extraction confidence: high={n_high}, medium={n_medium}, low={n_low}\n")
        f.write(f"- Keywords unavailable (title+abstract only): **{n_no_kw}**\n")
        f.write(f"- Awaiting manual verification (medium/low not yet confirmed): **{n_unverified}**\n\n")

        if n_unverified:
            f.write("## Studies requiring manual verification before freeze\n\n")
            f.write("| Study_ID | pdf_filename | extraction_confidence | abstract (first 100 chars) |\n")
            f.write("|---|---|---|---|\n")
            for r in rows:
                if not r["manually_verified"]:
                    f.write(f"| {r['Study_ID']} | {r['pdf_filename']} | {r['extraction_confidence']} | "
                            f"{r['abstract'][:100]!r} |\n")
            f.write("\n")

        f.write("## Full summary\n\n")
        f.write("| Study_ID | extraction_confidence | keywords_available | abstract_len |\n")
        f.write("|---|---|---|---|\n")
        for r in rows:
            f.write(f"| {r['Study_ID']} | {r['extraction_confidence']} | {r['keywords_available']} | "
                    f"{len(r['abstract'])} |\n")

    print(f"Processed {len(rows)} studies")
    print(f"Confidence: high={n_high} medium={n_medium} low={n_low}")
    print(f"Keywords unavailable: {n_no_kw}")
    print(f"Awaiting manual verification: {n_unverified}")
    print(f"Wrote {OUT_CSV}")
    print(f"Wrote {OUT_MD}")


if __name__ == "__main__":
    main()
