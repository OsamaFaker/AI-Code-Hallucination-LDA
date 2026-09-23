import csv
import re
from pathlib import Path
from collections import Counter

ROOT = Path(__file__).resolve().parents[1]
FT_DIR = ROOT / "extraction" / "fulltext"
REPORT = ROOT / "extraction" / "fulltext_extraction_report.csv"

SUSPECT_PATTERNS = {
    "orcid": re.compile(r"\bORCID\b", re.IGNORECASE),
    "downloaded_from": re.compile(r"\bdownloaded\s+(on|from)\b", re.IGNORECASE),
    "copyright_symbol": re.compile(r"©"),
    "email": re.compile(r"\S+@\S+\.\w+"),
    "doi_url": re.compile(r"https?://doi\.org|doi:\s*10\.\d{4,}", re.IGNORECASE),
    "isbn": re.compile(r"\bISBN\b", re.IGNORECASE),
    "acm_ref_format": re.compile(r"ACM Reference Format", re.IGNORECASE),
    "restrictions_apply": re.compile(r"restrictions apply", re.IGNORECASE),
    "conflict_of_interest_leak": re.compile(r"conflicts?\s+of\s+interest", re.IGNORECASE),
    "funding_leak": re.compile(r"\bthis work was supported\b", re.IGNORECASE),
    "abstract_leak": re.compile(r"^\s*ABSTRACT\s*$", re.IGNORECASE | re.MULTILINE),
    "keywords_leak": re.compile(r"^\s*(KEYWORDS|INDEX TERMS)\s*$", re.IGNORECASE | re.MULTILINE),
}

with open(REPORT, newline="", encoding="utf-8") as f:
    rows = {r["Study_ID"]: r for r in csv.DictReader(f)}

print(f"{'Study_ID':8} {'start':14} {'end':26} {'conf':6} {'tokens':7}  suspects")
counter = Counter()
for sid in sorted(rows, key=lambda x: int(x[1:])):
    r = rows[sid]
    text = (FT_DIR / f"{sid}.txt").read_text(encoding="utf-8")
    hits = [name for name, pat in SUSPECT_PATTERNS.items() if pat.search(text)]
    for h in hits:
        counter[h] += 1
    flag = " <<<" if hits else ""
    print(f"{sid:8} {r['section_start_heading']:14} {r['section_end_heading']:26} "
          f"{r['section_detection']:6} {r['substantive_token_count']:7}  {','.join(hits)}{flag}")

print("\n--- Suspect pattern totals ---")
for name, count in counter.most_common():
    print(f"{name}: {count}")

print("\n--- start_heading distribution ---")
print(Counter(r["section_start_heading"] for r in rows.values()))
print("\n--- end_heading distribution ---")
print(Counter(r["section_end_heading"] for r in rows.values()))
