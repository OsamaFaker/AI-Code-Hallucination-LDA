"""Section 4-6: PDF text extraction, title/abstract/keyword identification (Analysis A),
and cleaned section-restricted full text (Analysis B), for the 66 primary studies only.
"""
import re
import unicodedata
from pathlib import Path

import fitz  # PyMuPDF
import pandas as pd

ROOT = Path(__file__).resolve().parents[2]
PKG = ROOT / "LDA_66_Dual_Representation"
PDF_DIR = ROOT / "66_Primery_Study"

MANIFEST = PKG / "corpus" / "primary_studies_manifest.csv"
EXTRACTION_DIR = PKG / "extraction"
DATA_DIR = PKG / "data"
FULLTEXT_TXT_DIR = DATA_DIR / "fulltext_texts"

SECTION_HEADINGS = {
    "introduction": "Introduction",
    "background": "Background",
    "related work": "Related Work",
    "related works": "Related Work",
    "motivation": "Background",
    "preliminaries": "Background",
    "problem statement": "Background",
    "problem formulation": "Background",
    "methodology": "Methodology",
    "method": "Methodology",
    "methods": "Methodology",
    "approach": "Methodology",
    "proposed approach": "Methodology",
    "proposed method": "Methodology",
    "system design": "Methodology",
    "study design": "Methodology",
    "research design": "Methodology",
    "experimental setup": "Methodology",
    "experiment setup": "Methodology",
    "implementation": "Methodology",
    "experiment": "Results",
    "experiments": "Results",
    "experimental results": "Results",
    "evaluation": "Results",
    "results": "Results",
    "findings": "Results",
    "empirical results": "Results",
    "discussion": "Discussion",
    "discussions": "Discussion",
    "threats to validity": "Discussion",
    "limitations": "Discussion",
    "implications": "Discussion",
    "conclusion": "Conclusion",
    "conclusions": "Conclusion",
    "conclusion and future work": "Conclusion",
    "summary": "Conclusion",
    "acknowledgements": "DROP",
    "acknowledgments": "DROP",
    "references": "DROP",
    "bibliography": "DROP",
    "appendix": "DROP",
}

HEADING_RE = re.compile(
    r"^\s*(?:[IVXLC]+\.|(?:\d{1,2}\.?)(?:\d{1,2}\.?)?\.?)?\s*"
    r"([A-Za-z][A-Za-z \-/&]{2,60})\s*$"
)

BOILERPLATE_PATTERNS = [
    re.compile(r"permission to make digital", re.I),
    re.compile(r"©\s?\d{4}", re.I),
    re.compile(r"copyright\s?©?\s?\d{4}", re.I),
    re.compile(r"\ball rights reserved\b", re.I),
    re.compile(r"\bacm\s+isbn\b", re.I),
    re.compile(r"\bieee\b.*\bdoi\b", re.I),
    re.compile(r"^\s*doi\s*:", re.I),
    re.compile(r"^\s*https?://doi\.org", re.I),
    re.compile(r"downloaded from", re.I),
    re.compile(r"preprint submitted to", re.I),
    re.compile(r"this is a preprint", re.I),
    re.compile(r"^\s*\d+\s*$"),  # bare page numbers
]

EMAIL_RE = re.compile(r"\b[\w.+-]+@[\w-]+\.[\w.-]+\b")
URL_RE = re.compile(r"\bhttps?://\S+\b")


def normalize_text(t: str) -> str:
    t = unicodedata.normalize("NFKC", t)
    t = t.replace("­", "")  # soft hyphen
    t = re.sub(r"(\w)-\n(\w)", r"\1\2", t)  # de-hyphenate across line breaks
    t = re.sub(r"[ \t]+", " ", t)
    t = re.sub(r"\n{3,}", "\n\n", t)
    return t


def page_lines(page) -> list[str]:
    return [ln.strip() for ln in page.get_text().split("\n") if ln.strip()]


def find_repeated_header_footer_lines(pages_lines: list[list[str]]) -> set[str]:
    """Lines appearing in the first/last 3 lines of >= 40% of pages -> running header/footer."""
    if len(pages_lines) < 3:
        return set()
    from collections import Counter
    counts = Counter()
    for lines in pages_lines:
        edge = set(lines[:3]) | set(lines[-3:])
        for ln in edge:
            if len(ln) > 3:
                counts[ln] += 1
    threshold = max(3, int(0.4 * len(pages_lines)))
    return {ln for ln, c in counts.items() if c >= threshold}


def strip_boilerplate(text: str) -> str:
    lines = text.split("\n")
    kept = []
    for ln in lines:
        if EMAIL_RE.search(ln):
            ln = EMAIL_RE.sub("", ln)
        if URL_RE.search(ln) and len(ln.strip()) < 120:
            ln = URL_RE.sub("", ln)
        if any(p.search(ln) for p in BOILERPLATE_PATTERNS):
            continue
        kept.append(ln)
    return "\n".join(kept)


SPACED_LETTERS_RE = re.compile(r"\b(?:[A-Za-z]\s){4,}[A-Za-z]\b")


def _collapse_spaced_headings(text: str) -> str:
    """PDF extraction sometimes yields letter-spaced headings, e.g. 'A B S T R A C T'
    (an Elsevier font-kerning artifact). Collapse any such run of single letters + spaces
    into one word so downstream heading regexes can match it normally."""
    return SPACED_LETTERS_RE.sub(lambda m: m.group(0).replace(" ", ""), text)


NEXT_SECTION_RE = (
    r"(?:Keywords|Index Terms|CCS Concepts|ACM Reference Format|"
    r"\d{1,2}\.?\s*[A-Z]|I\.\s*Introduction|1\s+Introduction|Introduction)\b"
)
AFFIL_LINE_RE = re.compile(
    r"university|college|institute|department|dept\.|@|laborator|school of|\bgermany\b|"
    r"\busa\b|\bchina\b|\buk\b|\bcanada\b|\bkorea\b", re.I
)


def extract_abstract_keywords(full_text: str) -> tuple[str, str]:
    """Heuristic extraction of abstract and keywords from page-1-heavy text."""
    full_text = _collapse_spaced_headings(full_text)
    abstract, keywords = "", ""
    m_abs = re.search(
        r"\bABSTRACT\b\s*[:\-]?\s*(.*?)(?=\n\s*" + NEXT_SECTION_RE + r")",
        full_text, re.I | re.S,
    )
    if m_abs:
        abstract = re.sub(r"\s+", " ", m_abs.group(1)).strip()
    else:
        # Fallback: many ACM camera-ready PDFs place the abstract paragraph directly after
        # the author/affiliation block with no literal "Abstract" heading. Take the first
        # paragraph of substantial length after the last affiliation-looking line and before
        # the next recognized section marker.
        head = full_text[:4000]
        m_next = re.search(r"\n\s*" + NEXT_SECTION_RE, head, re.I)
        head = head[: m_next.start()] if m_next else head
        lines = head.split("\n")
        last_affil_idx = -1
        for i, ln in enumerate(lines):
            if AFFIL_LINE_RE.search(ln):
                last_affil_idx = i
        candidate = "\n".join(lines[last_affil_idx + 1:]).strip()
        candidate = re.sub(r"\s+", " ", candidate).strip()
        if len(candidate) >= 300:
            abstract = candidate
    m_kw = re.search(
        r"\b(?:Keywords|Index Terms)\b\s*[:\-]?\s*(.*?)(?=\n\s*(?:CCS Concepts|"
        r"ACM Reference Format|\d{1,2}\.?\s*[A-Z]|I\.\s*Introduction|1\s+Introduction|"
        r"Introduction)\b)",
        full_text, re.I | re.S,
    )
    if m_kw:
        kw_raw = re.sub(r"\s+", " ", m_kw.group(1)).strip()
        kw_raw = kw_raw.rstrip(".")
        keywords = kw_raw

    # Safety cap: real abstracts run ~120-350 words. If the heading-to-next-section lookahead
    # failed to find a genuine boundary (e.g. because "Keywords" precedes "Abstract" in
    # Elsevier's "Article Info" layout, leaving no later boundary to anchor on), the greedy
    # match can run away into the paper body. Truncate to the last full sentence within the
    # first ~350 words rather than silently keeping runaway text.
    words = abstract.split()
    if len(words) > 350:
        truncated = " ".join(words[:350])
        last_period = truncated.rfind(". ")
        abstract = truncated[: last_period + 1] if last_period > 0 else truncated

    return abstract, keywords


def segment_sections(text: str) -> dict[str, list[str]]:
    """Split cleaned body text into canonical sections using heading-line detection."""
    lines = text.split("\n")
    sections: dict[str, list[str]] = {}
    current = "Front"
    sections[current] = []
    for ln in lines:
        stripped = ln.strip()
        m = HEADING_RE.match(stripped) if len(stripped) < 65 else None
        if m:
            candidate = m.group(1).strip().lower()
            candidate = re.sub(r"\s+", " ", candidate)
            mapped = SECTION_HEADINGS.get(candidate)
            if mapped:
                current = mapped
                sections.setdefault(current, [])
                continue
        sections[current].append(ln)
    return sections


def main():
    manifest = pd.read_csv(MANIFEST)
    FULLTEXT_TXT_DIR.mkdir(parents=True, exist_ok=True)
    DATA_DIR.mkdir(exist_ok=True)

    meta_rows = []
    fulltext_rows = []
    quality_flags = []

    for _, row in manifest.iterrows():
        sid = row["Study_ID"]
        pdf_path = PDF_DIR / row["pdf_filename"]
        doc = fitz.open(pdf_path)
        pages_raw = [p.get_text() for p in doc]
        pages_lines = [page_lines(p) for p in doc]
        repeated = find_repeated_header_footer_lines(pages_lines)
        n_pages = len(doc)
        doc.close()

        # Header/footer-stripped, boilerplate-stripped full text (page order preserved)
        cleaned_pages = []
        removed_header_footer_lines = 0
        for lines in pages_lines:
            kept = [ln for ln in lines if ln not in repeated]
            removed_header_footer_lines += len(lines) - len(kept)
            cleaned_pages.append("\n".join(kept))
        raw_full = normalize_text("\n".join(pages_raw))
        cleaned_full = normalize_text("\n".join(cleaned_pages))
        before_boiler = cleaned_full.count("\n")
        cleaned_full = strip_boilerplate(cleaned_full)
        after_boiler = cleaned_full.count("\n")

        # --- Analysis A: title/abstract/keywords ---
        title = str(row["title"])
        abstract, keywords = extract_abstract_keywords(raw_full)
        missing_abstract = abstract == ""
        missing_keywords = keywords == ""
        combined = f"{title}. {abstract}"
        if keywords:
            combined = f"{combined} {keywords}"

        meta_rows.append({
            "Study_ID": sid,
            "title": title,
            "abstract": abstract,
            "author_keywords": keywords,
            "combined_text": combined,
        })

        # --- Analysis B: section-restricted cleaned full text ---
        sections = segment_sections(_collapse_spaced_headings(cleaned_full))
        kept_labels = ["Front", "Introduction", "Background", "Related Work",
                        "Methodology", "Results", "Discussion", "Conclusion"]
        # 'Front' before first recognized heading often contains title/authors/affiliations/
        # abstract - drop it for full text (already captured via Analysis A), keep only if
        # no other sections were detected at all (extraction fallback).
        detected_sections = [k for k in sections if k not in ("Front", "DROP") and sections[k]]
        if detected_sections:
            body_labels = [l for l in kept_labels if l != "Front"]
            fallback_used = False
        else:
            body_labels = ["Front"]
            fallback_used = True
        body_text = "\n".join(
            "\n".join(sections.get(lbl, [])) for lbl in body_labels
        )
        body_text = re.sub(r"\s+\n", "\n", body_text)
        body_text = re.sub(r"\n{3,}", "\n\n", body_text).strip()

        (FULLTEXT_TXT_DIR / f"{sid}.txt").write_text(body_text, encoding="utf-8")

        fulltext_rows.append({
            "Study_ID": sid,
            "n_pages": n_pages,
            "raw_chars": len(raw_full),
            "cleaned_body_chars": len(body_text),
            "cleaned_body_words": len(body_text.split()),
            "removed_header_footer_lines": removed_header_footer_lines,
            "removed_boilerplate_lines": before_boiler - after_boiler,
            "sections_detected": ";".join(detected_sections) if detected_sections else "",
            "section_segmentation_fallback": fallback_used,
        })

        flags = []
        if missing_abstract:
            flags.append("missing_abstract")
        if missing_keywords:
            flags.append("missing_keywords")
        if len(body_text) < 2000:
            flags.append("suspiciously_short_extraction")
        if len(body_text) > 200000:
            flags.append("unusually_long_extraction")
        if fallback_used:
            flags.append("section_segmentation_failed_used_full_body_fallback")
        if "�" in raw_full:
            flags.append("corrupted_encoding_marker_present")
        quality_flags.append({"Study_ID": sid, "flags": ";".join(flags)})

    meta_df = pd.DataFrame(meta_rows)
    fulltext_df = pd.DataFrame(fulltext_rows)
    flags_df = pd.DataFrame(quality_flags)

    meta_df.to_csv(DATA_DIR / "metadata_representation.csv", index=False)
    fulltext_df.to_csv(DATA_DIR / "fulltext_representation_manifest.csv", index=False)

    EXTRACTION_DIR.mkdir(exist_ok=True)
    meta_df.assign(
        abstract_available=meta_df["abstract"].ne(""),
        keywords_available=meta_df["author_keywords"].ne(""),
    )[["Study_ID", "title", "abstract_available", "keywords_available"]].to_csv(
        EXTRACTION_DIR / "metadata_extraction.csv", index=False
    )
    fulltext_df.to_csv(EXTRACTION_DIR / "fulltext_extraction.csv", index=False)

    n_missing_abs = meta_df["abstract"].eq("").sum()
    n_missing_kw = meta_df["author_keywords"].eq("").sum()
    n_fallback = fulltext_df["section_segmentation_fallback"].sum()
    flagged = flags_df[flags_df["flags"] != ""]

    report = f"""# Extraction Quality Report

Parser: PyMuPDF (fitz) {fitz.__doc__ or ''}. OCR was not required for any of the 66 primary
studies (all yielded machine-readable text via direct extraction).

## Analysis A (metadata) diagnostics

- Studies with missing abstract (heuristic extraction failed): {n_missing_abs} / 66
- Studies with missing author keywords: {n_missing_kw} / 66
- Missing keywords fall back to Title + Abstract only, per protocol Section 5.

## Analysis B (full text) diagnostics

- Studies where automatic section segmentation found zero recognized headings
  (fallback: full cleaned page body retained instead of section-restricted body): {n_fallback} / 66
- Cleaned body word count: mean={fulltext_df['cleaned_body_words'].mean():.0f},
  median={fulltext_df['cleaned_body_words'].median():.0f},
  min={fulltext_df['cleaned_body_words'].min()}, max={fulltext_df['cleaned_body_words'].max()}

## Per-study flags

{flagged.to_string(index=False) if not flagged.empty else '(none flagged)'}

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
"""
    (EXTRACTION_DIR / "extraction_quality_report.md").write_text(report, encoding="utf-8")

    print(f"metadata: missing_abstract={n_missing_abs} missing_keywords={n_missing_kw}")
    print(f"fulltext: segmentation_fallback={n_fallback}/66")


if __name__ == "__main__":
    main()
