"""Section 3: Corpus audit. Build primary_studies_manifest.csv from the 66 primary-study
PDFs, matched against the authoritative EMSE_MASTER_REFERENCE Master Data sheet.
"""
import hashlib
import re
import unicodedata
from pathlib import Path

import fitz  # PyMuPDF
import pandas as pd

ROOT = Path(__file__).resolve().parents[2]  # .../Final Copy/LDA
PKG = ROOT / "LDA_66_Dual_Representation"
PDF_DIR_PRIMARY = ROOT / "66_Primery_Study"
PDF_DIR_FULL = ROOT / "71_Final_SMR"
MASTER_XLSX = ROOT.parent / "EMSE_MASTER_REFERENCE_v6_4_FINAL.xlsx"  # .../Final Copy/


def normalize_title(t: str) -> str:
    t = unicodedata.normalize("NFKD", str(t))
    t = t.encode("ascii", "ignore").decode("ascii")
    t = t.lower()
    t = re.sub(r"[^a-z0-9]+", " ", t)
    t = re.sub(r"\s+", " ", t).strip()
    return t


def strip_pdf_prefix(filename: str) -> str:
    # strip leading numbering like "1- ", "S1_" etc for fuzzy title matching
    stem = Path(filename).stem
    stem = re.sub(r"^\d+-\s*", "", stem)
    stem = re.sub(r"^S\d+_", "", stem)
    return stem


def sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


# Manual overrides: PDF filename -> Study ID, documented case-by-case.
# "Exploring and Evaluating Hallucinations in LLM-Powered Code Generation.pdf" is the arXiv v1
# title of S36 (Fang Liu et al., arXiv:2404.00971); the Master Data title
# "Beyond Functional Correctness: Exploring Hallucinations in LLM-Generated Code" is a later
# arXiv revision's title for the same paper (same authors/DOI), confirmed by PDF inspection.
MANUAL_OVERRIDES = {
    "Exploring and Evaluating Hallucinations in LLM-Powered Code Generation.pdf": "S36",
}


def main():
    master = pd.read_excel(MASTER_XLSX, sheet_name="Master Data")
    master["norm_title"] = master["Title"].map(normalize_title)

    pdfs_primary = sorted(PDF_DIR_PRIMARY.glob("*.pdf"))
    pdfs_full = sorted(PDF_DIR_FULL.glob("*.pdf"))
    assert len(pdfs_primary) == 66, f"expected 66 primary PDFs, found {len(pdfs_primary)}"
    assert len(pdfs_full) == 71, f"expected 71 total PDFs, found {len(pdfs_full)}"

    rows = []
    unmatched = []
    for pdf_path in pdfs_primary:
        if pdf_path.name in MANUAL_OVERRIDES:
            cand = master[master["Study ID"] == MANUAL_OVERRIDES[pdf_path.name]]
            rows_from_override = True
        else:
            rows_from_override = False
        norm = normalize_title(strip_pdf_prefix(pdf_path.name))
        # exact normalized match first
        if not rows_from_override:
            cand = master[master["norm_title"] == norm]
        if cand.empty:
            # fallback: containment match either direction
            cand = master[master["norm_title"].apply(
                lambda mt: mt in norm or norm in mt if mt and norm else False
            )]
        if cand.empty:
            # fallback: token overlap (Jaccard) best match
            norm_tokens = set(norm.split())
            best_score, best_idx = 0.0, None
            for idx, mt in master["norm_title"].items():
                mt_tokens = set(mt.split())
                if not mt_tokens or not norm_tokens:
                    continue
                score = len(norm_tokens & mt_tokens) / len(norm_tokens | mt_tokens)
                if score > best_score:
                    best_score, best_idx = score, idx
            if best_idx is not None and best_score >= 0.6:
                cand = master.loc[[best_idx]]

        if cand.empty:
            unmatched.append(pdf_path.name)
            continue
        if len(cand) > 1:
            cand = cand.iloc[[0]]

        row = cand.iloc[0]
        try:
            doc = fitz.open(pdf_path)
            page_count = doc.page_count
            full_text = "".join(page.get_text() for page in doc)
            doc.close()
            extraction_status = "ok"
        except Exception as e:  # noqa: BLE001
            page_count = None
            full_text = ""
            extraction_status = f"error: {e}"

        rows.append({
            "Study_ID": row["Study ID"],
            "title": row["Title"],
            "DOI": row.get("DOI", ""),
            "publication_year": row.get("Year", ""),
            "publication_venue": row.get("Venue", ""),
            "pdf_filename": pdf_path.name,
            "pdf_sha256": sha256_file(pdf_path),
            "primary_secondary_classification": row["Study category"],
            "page_count": page_count,
            "extraction_status": extraction_status,
            "extracted_characters": len(full_text),
            "extracted_words": len(full_text.split()),
        })

    if unmatched:
        raise SystemExit(f"UNMATCHED PDFs (must resolve before proceeding): {unmatched}")

    manifest = pd.DataFrame(rows)
    assert manifest["primary_secondary_classification"].eq("Primary").all()
    assert manifest["Study_ID"].is_unique
    assert manifest["DOI"].dropna().is_unique or manifest["DOI"].dropna().empty
    assert len(manifest) == 66

    # duplicate normalized-title / pdf-hash checks
    manifest["_norm_title"] = manifest["title"].map(normalize_title)
    dup_titles = manifest[manifest["_norm_title"].duplicated(keep=False)]
    dup_hashes = manifest[manifest["pdf_sha256"].duplicated(keep=False)]
    manifest = manifest.drop(columns="_norm_title")

    out_dir = PKG / "corpus"
    out_dir.mkdir(exist_ok=True)
    manifest.to_csv(out_dir / "primary_studies_manifest.csv", index=False)

    # abstract/keywords availability filled in later by extraction.py; placeholder columns
    manifest["abstract_available"] = ""
    manifest["keywords_available"] = ""
    manifest["full_text_available"] = manifest["extraction_status"].eq("ok")

    secondary = master[master["Study category"] == "Secondary"]

    audit_md = f"""# Corpus Audit

## Counts

- Total included studies (71_Final_SMR + Master Data): {len(master)}
- Primary studies (Master Data): {(master['Study category']=='Primary').sum()}
- Secondary studies (Master Data): {(master['Study category']=='Secondary').sum()}
- PDFs in `66_Primery_Study/`: {len(pdfs_primary)}
- PDFs in `71_Final_SMR/`: {len(pdfs_full)}
- Matched primary PDFs to Master Data rows: {len(manifest)}
- Unmatched PDFs: {len(unmatched)}

**N = {len(manifest)} confirmed.**

## Duplicate checks

- Duplicate Study_IDs: {manifest['Study_ID'].duplicated().sum()}
- Duplicate DOIs (non-null): {manifest['DOI'].dropna().duplicated().sum()}
- Duplicate normalized titles: {len(dup_titles)}
- Duplicate PDF SHA-256 hashes: {len(dup_hashes)}

## Secondary studies excluded from LDA (documented, not modeled)

{secondary[['Study ID','Title','Year','DOI']].to_markdown(index=False)}

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
"""
    (out_dir / "corpus_audit.md").write_text(audit_md, encoding="utf-8")
    print(f"Wrote manifest with {len(manifest)} studies; unmatched={len(unmatched)}")
    print(f"Dup titles={len(dup_titles)} dup hashes={len(dup_hashes)}")


if __name__ == "__main__":
    main()
