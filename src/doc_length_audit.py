"""
Stage 0 -- Document-length audit (PRE_EXECUTION_ANALYSIS_PLAN.md SS4).

Computed on the substantive (post section-stripping) full-text token counts
from extraction/fulltext_extraction_report.csv. No LDA fitting here.
"""

from __future__ import annotations

import csv
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np

ROOT = Path(__file__).resolve().parents[1]
REPORT_CSV = ROOT / "extraction" / "fulltext_extraction_report.csv"
FIG_DIR = ROOT / "figures" / "fulltext"
OUT_MD = ROOT / "extraction" / "document_length_audit.md"


def main() -> None:
    with open(REPORT_CSV, newline="", encoding="utf-8") as f:
        rows = list(csv.DictReader(f))
    tokens = np.array([int(r["substantive_token_count"]) for r in rows])
    ids = [r["Study_ID"] for r in rows]
    assert len(tokens) == 66

    stats = {
        "n": len(tokens),
        "min": int(tokens.min()),
        "max": int(tokens.max()),
        "mean": float(tokens.mean()),
        "median": float(np.median(tokens)),
        "sd": float(tokens.std(ddof=1)),
        "q1": float(np.percentile(tokens, 25)),
        "q3": float(np.percentile(tokens, 75)),
    }
    stats["iqr"] = stats["q3"] - stats["q1"]
    stats["max_min_ratio"] = stats["max"] / stats["min"]
    iqr_upper_fence = stats["q3"] + 1.5 * stats["iqr"]
    # Stage-5 mandatory length cap (frozen per plan SS13): IQR upper bound,
    # rounded to the nearest 500 tokens.
    length_cap = int(round(iqr_upper_fence / 500) * 500)

    FIG_DIR.mkdir(parents=True, exist_ok=True)
    plt.style.use("grayscale")

    fig, ax = plt.subplots(figsize=(6, 4))
    ax.hist(tokens, bins=15, color="0.4", edgecolor="black")
    ax.set_xlabel("Substantive token count")
    ax.set_ylabel("Number of studies")
    ax.set_title("Full-text document length distribution (n=66)")
    fig.tight_layout()
    fig.savefig(FIG_DIR / "doc_length_histogram.png", dpi=200)
    plt.close(fig)

    fig, ax = plt.subplots(figsize=(4, 5))
    ax.boxplot(tokens, vert=True, patch_artist=True,
               boxprops=dict(facecolor="0.8"), medianprops=dict(color="black"))
    ax.set_ylabel("Substantive token count")
    ax.set_title("Full-text document length (n=66)")
    ax.set_xticklabels(["All studies"])
    fig.tight_layout()
    fig.savefig(FIG_DIR / "doc_length_boxplot.png", dpi=200)
    plt.close(fig)

    # combined figure (both panels together, as listed in plan SS32 item 17)
    fig, axes = plt.subplots(1, 2, figsize=(9, 4))
    axes[0].hist(tokens, bins=15, color="0.4", edgecolor="black")
    axes[0].set_xlabel("Substantive token count")
    axes[0].set_ylabel("Number of studies")
    axes[0].set_title("Histogram")
    axes[1].boxplot(tokens, vert=True, patch_artist=True,
                     boxprops=dict(facecolor="0.8"), medianprops=dict(color="black"))
    axes[1].set_ylabel("Substantive token count")
    axes[1].set_title("Boxplot")
    axes[1].set_xticklabels(["All studies"])
    fig.suptitle("Full-text document length distribution (n=66)")
    fig.tight_layout()
    fig.savefig(FIG_DIR / "doc_length_distribution.png", dpi=200)
    plt.close(fig)

    outliers = [(ids[i], int(tokens[i])) for i in range(len(tokens)) if tokens[i] > iqr_upper_fence]

    with open(OUT_MD, "w", encoding="utf-8") as f:
        f.write("# Document-Length Audit (full text, substantive tokens)\n\n")
        f.write(f"- n = {stats['n']}\n")
        f.write(f"- min = {stats['min']}\n")
        f.write(f"- max = {stats['max']}\n")
        f.write(f"- mean = {stats['mean']:.1f}\n")
        f.write(f"- median = {stats['median']:.1f}\n")
        f.write(f"- SD = {stats['sd']:.1f}\n")
        f.write(f"- Q1 = {stats['q1']:.1f}\n")
        f.write(f"- Q3 = {stats['q3']:.1f}\n")
        f.write(f"- IQR = {stats['iqr']:.1f}\n")
        f.write(f"- max/min ratio = {stats['max_min_ratio']:.2f}\n\n")
        f.write(f"- IQR upper fence (Q3 + 1.5*IQR) = {iqr_upper_fence:.1f}\n")
        f.write(f"- **Frozen Stage-5 length cap (rounded to nearest 500)**: **{length_cap}** tokens "
                "(per PRE_EXECUTION_ANALYSIS_PLAN.md SS13 -- fixed here, before any topic modelling, "
                "not chosen after seeing results)\n\n")
        f.write(f"- Documents above the IQR upper fence: **{len(outliers)}**\n\n")
        if outliers:
            f.write("| Study_ID | substantive_tokens |\n|---|---|\n")
            for sid, tok in sorted(outliers, key=lambda x: -x[1]):
                f.write(f"| {sid} | {tok} |\n")
            f.write("\n")
        f.write("Figures: `figures/fulltext/doc_length_histogram.png`, "
                "`doc_length_boxplot.png`, `doc_length_distribution.png` (combined).\n\n")
        f.write("This ~"
                f"{stats['max_min_ratio']:.0f}x max/min spread motivates the mandatory "
                "full-text length-sensitivity analysis (Stage 5, plan SS13): long articles can "
                "contribute disproportionately more word counts to classical LDA.\n")

    print(f"n={stats['n']} min={stats['min']} max={stats['max']} mean={stats['mean']:.1f} "
          f"median={stats['median']:.1f} SD={stats['sd']:.1f} IQR={stats['iqr']:.1f} "
          f"max/min={stats['max_min_ratio']:.2f}")
    print(f"Frozen length cap: {length_cap} tokens")
    print(f"Wrote {OUT_MD}")
    print(f"Wrote figures to {FIG_DIR}")


if __name__ == "__main__":
    main()
