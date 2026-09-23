"""
Verify frozen outputs -- a lightweight, fast check that the committed result
files, reports, and figures are internally consistent with each other and
with the values recorded in reports/FROZEN_MANUSCRIPT_VALUES.md.

This is NOT a reproduction of the LDA pipeline: it does not refit any model,
re-run preprocessing, or re-run the k-sweep. It only re-reads and
recomputes simple aggregates (means, SDs, row/column counts, hash digests)
directly from the already-frozen CSV/JSON/Markdown files already committed
to this repository. See README.md "Reproduce the analysis from frozen
inputs" for the full pipeline this repository can also regenerate.

Every check prints PASS/FAIL and the script exits non-zero if any check
fails. Nothing here is silently skipped.
"""

from __future__ import annotations

import csv
import hashlib
import json
import re
import sys
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
FAILURES: list[str] = []


def check(label: str, condition: bool, detail: str = "") -> None:
    status = "PASS" if condition else "FAIL"
    print(f"[{status}] {label}" + (f" -- {detail}" if detail and not condition else ""))
    if not condition:
        FAILURES.append(label)


# ---------------------------------------------------------------------------
# 0. Frozen file checksums (FREEZE_SHA256.txt)
# ---------------------------------------------------------------------------

def verify_checksums() -> None:
    registry = ROOT / "FREEZE_SHA256.txt"
    if not registry.exists():
        check("FREEZE_SHA256.txt exists", False, "not found")
        return
    for line in registry.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line:
            continue
        expected_hash, rel_path = line.split(maxsplit=1)
        path = ROOT / rel_path
        actual_hash = hashlib.sha256(path.read_bytes()).hexdigest() if path.exists() else None
        check(f"checksum matches: {rel_path}", actual_hash == expected_hash, f"expected {expected_hash}, got {actual_hash}")


# ---------------------------------------------------------------------------
# 1. Corpus counts
# ---------------------------------------------------------------------------

def verify_corpus() -> None:
    with open(ROOT / "corpus" / "corpus_manifest.csv", newline="", encoding="utf-8") as f:
        rows = list(csv.DictReader(f))
    check("corpus_manifest.csv has 71 rows", len(rows) == 71, f"got {len(rows)}")
    n_primary = sum(1 for r in rows if r["study_category"] == "Primary")
    n_secondary = sum(1 for r in rows if r["study_category"] == "Secondary")
    n_yes = sum(1 for r in rows if r["included_in_lda"] == "Yes")
    n_no = sum(1 for r in rows if r["included_in_lda"] == "No")
    check("66 Primary studies", n_primary == 66, f"got {n_primary}")
    check("5 Secondary studies", n_secondary == 5, f"got {n_secondary}")
    check("66 included_in_lda=Yes", n_yes == 66, f"got {n_yes}")
    check("5 included_in_lda=No", n_no == 5, f"got {n_no}")

    with open(ROOT / "corpus" / "primary_studies_manifest.csv", newline="", encoding="utf-8") as f:
        primary_ids = set(r["Study_ID"] for r in csv.DictReader(f))
    yes_ids = set(r["study_id"] for r in rows if r["included_in_lda"] == "Yes")
    check(
        "corpus_manifest.csv Yes-studies match the 66-study LDA corpus exactly",
        primary_ids == yes_ids,
        f"symmetric difference: {primary_ids.symmetric_difference(yes_ids)}",
    )


# ---------------------------------------------------------------------------
# 2. Model-selection result files: k=4 aggregates, medoid seeds, counts
# ---------------------------------------------------------------------------

EXPECTED = {
    "metadata": {
        "seed": 1212,
        "mean_cv": 0.3584,
        "mean_cnpmi": -0.1638,
        "mean_stability": 0.5815,
        "diversity": 0.8490,
        "dominant_counts": [22, 16, 15, 13],
        "prevalence_pct": [29.2, 24.2, 24.2, 22.5],
    },
    "fulltext": {
        "seed": 505,
        "mean_cv": 0.2957,
        "mean_cnpmi": -0.2512,
        "mean_stability": 0.5913,
        "diversity": 0.9070,
        "dominant_counts": [17, 8, 16, 25],
        "prevalence_pct": [26.6, 13.5, 22.7, 37.2],
    },
}


def verify_representation(rep: str) -> None:
    df = pd.read_csv(ROOT / "results" / rep / "k_sweep_summary.csv")
    check(f"{rep}: k_sweep_summary.csv covers k=2..20 (19 rows)", len(df) == 19, f"got {len(df)}")
    row = df[df["k"] == 4].iloc[0]
    exp = EXPECTED[rep]

    check(f"{rep}: structural-medoid seed at k=4 == {exp['seed']}", int(row["medoid_seed"]) == exp["seed"])
    check(f"{rep}: mean C_v at k=4 == {exp['mean_cv']}", round(float(row["mean_cv"]), 4) == exp["mean_cv"])
    check(f"{rep}: mean C_NPMI at k=4 == {exp['mean_cnpmi']}", round(float(row["mean_cnpmi"]), 4) == exp["mean_cnpmi"])
    check(f"{rep}: mean stability at k=4 == {exp['mean_stability']}", round(float(row["mean_stability"]), 4) == exp["mean_stability"])
    check(f"{rep}: topic diversity at k=4 == {exp['diversity']}", round(float(row["mean_diversity"]), 4) == exp["diversity"])

    dominant = json.loads(row["dominant_counts_json"])
    check(f"{rep}: dominant-study counts == {exp['dominant_counts']}", dominant == exp["dominant_counts"], f"got {dominant}")

    prevalence = json.loads(row["prevalence_json"])
    prevalence_pct = [round(p * 100, 1) for p in prevalence]
    check(f"{rep}: prevalence (%) == {exp['prevalence_pct']}", prevalence_pct == exp["prevalence_pct"], f"got {prevalence_pct}")

    check(f"{rep}: zero-dominance topics at k=4 == 0", int(row["zero_dominance_topics"]) == 0)
    check(f"{rep}: thin (<5-study) topics at k=4 == 0", int(row["topics_lt5"]) == 0)

    by_seed = pd.read_csv(ROOT / "results" / rep / "k_sweep_by_seed.csv")
    check(
        f"{rep}: definitive sweep has 380 fits (19 k x 20 seeds)",
        len(by_seed) == 380,
        f"got {len(by_seed)}",
    )
    check(f"{rep}: definitive sweep has exactly 20 distinct seeds", by_seed["seed"].nunique() == 20)
    check(f"{rep}: definitive sweep covers k=2..20", sorted(by_seed["k"].unique().tolist()) == list(range(2, 21)))


# ---------------------------------------------------------------------------
# 3. Robustness aggregates, recomputed directly from the per-repetition CSVs
# ---------------------------------------------------------------------------

def verify_robustness(rep: str, expected_js: float, expected_ari: float) -> None:
    df = pd.read_csv(ROOT / "results" / rep / "subsampling_k4.csv")
    js_mean = round(df["js_similarity"].mean(), 3)
    ari_mean = round(df["ari"].mean(), 3)
    check(f"{rep}: recomputed subsampling JS mean == {expected_js}", js_mean == expected_js, f"got {js_mean}")
    check(f"{rep}: recomputed subsampling ARI mean == {expected_ari}", ari_mean == expected_ari, f"got {ari_mean}")


# ---------------------------------------------------------------------------
# 4. Cross-representation comparison
# ---------------------------------------------------------------------------

def verify_cross_representation() -> None:
    perm = pd.read_csv(ROOT / "results" / "cross_representation" / "permutation_test.csv").iloc[0]
    check("cross-representation ARI == 0.2384", round(float(perm["observed_ari"]), 4) == 0.2384)
    check("cross-representation NMI == 0.2738", round(float(perm["observed_nmi"]), 4) == 0.2738)
    check("permutation test used 10,000 repetitions", int(perm["n_permutations"]) == 10000)

    ctab = pd.read_csv(ROOT / "results" / "cross_representation" / "contingency_matrix.csv", index_col=0)
    mat = ctab.to_numpy(dtype=int)
    check(
        "contingency matrix matches the frozen 4x4 table",
        mat.tolist() == [[1, 1, 3, 17], [9, 2, 2, 3], [7, 1, 7, 0], [0, 4, 4, 5]],
    )


# ---------------------------------------------------------------------------
# 5. Topic labels: exactly the 8 frozen labels, nowhere contradicted
# ---------------------------------------------------------------------------

FINAL_LABELS = [
    "API/Code Hallucination: Benchmarks and Mitigation",
    "AI-Generated Feedback in Programming Education",
    "Developer Trust and Experience with AI Coding Assistants",
    "Empirical Code Correctness, Testing, and Non-Determinism",
    "Programming Education: Instruction, Grading, and Trust",
    "Code Repair, Verification, and Determinism Benchmarking",
    "Practitioner Perspectives on Package Hallucination and Security Risk",
    "Iterative and Retrieval-Based Hallucination Mitigation",
]


def verify_topic_labels() -> None:
    metadata_report = (ROOT / "reports" / "METADATA_LDA_REPORT.md").read_text(encoding="utf-8")
    fulltext_report = (ROOT / "reports" / "FULLTEXT_LDA_REPORT.md").read_text(encoding="utf-8")
    combined = re.sub(r"\s+", " ", metadata_report + " " + fulltext_report)
    for label in FINAL_LABELS:
        label_normalized = re.sub(r"\s+", " ", label)
        check(f"topic label present: {label[:40]}...", label_normalized in combined)


# ---------------------------------------------------------------------------
# 6. Scan reader-facing files for known-conflicting stale values
# ---------------------------------------------------------------------------

STALE_PATTERNS = [
    r"seed\s*14\b",
    r"seed\s*2\b(?!\d)",
    r"full[- ]text.{0,20}k\s*=\s*8\b",
    r"k\s*=\s*8\s*[-–]\s*15\b",
    r"passes\s*=\s*30\b",
    r"iterations\s*=\s*800\b",
    r"no_below\s*=\s*5,?\s*no_above\s*=\s*0\.50\b",
    r"no_below\s*=\s*4,?\s*no_above\s*=\s*0\.75\b",
    r"ARI\s*=\s*0\.19\b",
    r"NMI\s*=\s*0\.30\b",
]
# Heuristic scan: matches are a starting point for manual review, not a
# guarantee of either correctness (false negatives possible) or an actual
# conflict (false positives possible, e.g. "k=8" appearing while describing
# a diagnostic property of the k-sweep curve rather than a selected model).

SCAN_DIRS = ["README.md", "reports", "figures/LDA_FIGURE_INDEX.md", "corpus/corpus_audit.md"]
SCAN_EXCLUDE_DIRS = {"provenance"}


def scan_for_stale_values() -> None:
    hits: list[str] = []
    for name in SCAN_DIRS:
        p = ROOT / name
        paths = [p] if p.is_file() else (p.rglob("*.md") if p.is_dir() else [])
        for path in paths:
            if any(part in SCAN_EXCLUDE_DIRS for part in path.relative_to(ROOT).parts):
                continue
            text = path.read_text(encoding="utf-8")
            for pattern in STALE_PATTERNS:
                if re.search(pattern, text, flags=re.IGNORECASE):
                    hits.append(f"{path.relative_to(ROOT)}: pattern /{pattern}/")
    check(
        "no stale/conflicting configuration values in reader-facing files",
        len(hits) == 0,
        "; ".join(hits),
    )


# ---------------------------------------------------------------------------

def main() -> int:
    verify_checksums()
    verify_corpus()
    verify_representation("metadata")
    verify_representation("fulltext")
    verify_robustness("metadata", 0.812, 0.806)
    verify_robustness("fulltext", 0.810, 0.799)
    verify_cross_representation()
    verify_topic_labels()
    scan_for_stale_values()

    print()
    if FAILURES:
        print(f"{len(FAILURES)} check(s) FAILED:")
        for f in FAILURES:
            print(f"  - {f}")
        return 1
    print("All verification checks PASSED.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
