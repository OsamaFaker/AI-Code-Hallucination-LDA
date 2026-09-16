"""Section 28: publication-quality figures, per representation + cross-representation."""
import json
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
RESULTS_DIR = ROOT / "results"
FIG_DIR = ROOT / "figures"

plt.rcParams.update({"figure.dpi": 150, "font.size": 10, "axes.spines.top": False,
                      "axes.spines.right": False})


def _save(fig, path):
    path.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(path, bbox_inches="tight")
    plt.close(fig)


def model_selection_figures(label: str):
    runs = pd.read_csv(RESULTS_DIR / label / "definitive_ksweep_runs.csv")
    stab = pd.read_csv(RESULTS_DIR / label / "seed_stability_by_k.csv")
    out = FIG_DIR / label

    fig, ax = plt.subplots(figsize=(6, 4))
    for k, grp in runs.groupby("k"):
        ax.scatter([k] * len(grp), grp["c_v"], alpha=0.4, color="#4C72B0", s=14)
    means = runs.groupby("k")["c_v"].mean()
    ax.plot(means.index, means.values, color="#C44E52", marker="o", label="mean across seeds")
    ax.set_xlabel("k"); ax.set_ylabel("C_v"); ax.set_title(f"{label}: C_v vs k (seed variation)")
    ax.legend()
    _save(fig, out / "01_cv_vs_k.png")

    fig, ax = plt.subplots(figsize=(6, 4))
    for k, grp in runs.groupby("k"):
        ax.scatter([k] * len(grp), grp["c_npmi"], alpha=0.4, color="#4C72B0", s=14)
    means = runs.groupby("k")["c_npmi"].mean()
    ax.plot(means.index, means.values, color="#C44E52", marker="o")
    ax.set_xlabel("k"); ax.set_ylabel("C_NPMI"); ax.set_title(f"{label}: C_NPMI vs k")
    _save(fig, out / "02_cnpmi_vs_k.png")

    fig, ax = plt.subplots(figsize=(6, 4))
    ax.plot(stab["k"], stab["js_similarity_mean"], marker="o", color="#55A868")
    ax.fill_between(stab["k"], stab["js_similarity_min"], stab["js_similarity_max"], alpha=0.2, color="#55A868")
    ax.set_xlabel("k"); ax.set_ylabel("Cross-seed JS similarity"); ax.set_title(f"{label}: stability vs k")
    _save(fig, out / "03_stability_vs_k.png")

    fig, ax = plt.subplots(figsize=(6, 4))
    div = runs.groupby("k")["topic_diversity"].mean()
    ax.plot(div.index, div.values, marker="o", color="#8172B2")
    ax.set_xlabel("k"); ax.set_ylabel("Topic diversity (top-20 unique ratio)")
    ax.set_title(f"{label}: topic diversity vs k")
    _save(fig, out / "04_diversity_vs_k.png")

    fig, ax = plt.subplots(figsize=(6, 4))
    red = runs.groupby("k")["mean_top20_jaccard"].mean()
    ax.plot(red.index, red.values, marker="o", color="#CCB974")
    ax.set_xlabel("k"); ax.set_ylabel("Mean pairwise top-20 Jaccard")
    ax.set_title(f"{label}: topic redundancy vs k")
    _save(fig, out / "05_redundancy_vs_k.png")

    fig, ax = plt.subplots(figsize=(6, 4))
    zero = runs.groupby("k")["n_topics_0_studies"].mean()
    thin = runs.groupby("k")["n_topics_lt3_studies"].mean()
    ax.plot(zero.index, zero.values, marker="o", label="0-study topics", color="#C44E52")
    ax.plot(thin.index, thin.values, marker="s", label="<3-study topics", color="#DD8452")
    ax.set_xlabel("k"); ax.set_ylabel("Mean count"); ax.legend()
    ax.set_title(f"{label}: thin/zero-dominance topics vs k")
    _save(fig, out / "06_thin_zero_topics_vs_k.png")

    fig, axes = plt.subplots(2, 3, figsize=(15, 8))
    panels = [
        (means.index, runs.groupby("k")["c_v"].mean(), "C_v"),
        (means.index, runs.groupby("k")["c_npmi"].mean(), "C_NPMI"),
        (stab["k"], stab["js_similarity_mean"], "Stability"),
        (div.index, div.values, "Diversity"),
        (red.index, red.values, "Redundancy (Jaccard)"),
        (zero.index, zero.values, "Zero-dominance topics"),
    ]
    for ax, (x, y, title) in zip(axes.flat, panels):
        ax.plot(x, y, marker="o")
        ax.set_title(title); ax.set_xlabel("k")
    fig.suptitle(f"{label}: combined model-selection overview")
    fig.tight_layout()
    _save(fig, out / "07_combined_model_selection.png")
    print(f"[{label}] model-selection figures written")


def final_model_figures(label: str, k: int, seed: int):
    out = FIG_DIR / label
    sim_path = RESULTS_DIR / label / f"seed_similarity_matrix_k{k:02d}.csv"
    if sim_path.exists():
        sim = pd.read_csv(sim_path, index_col=0)
        fig, ax = plt.subplots(figsize=(7, 6))
        im = ax.imshow(sim.values, cmap="viridis")
        ax.set_xticks(range(len(sim.columns))); ax.set_xticklabels(sim.columns, rotation=90, fontsize=6)
        ax.set_yticks(range(len(sim.index))); ax.set_yticklabels(sim.index, fontsize=6)
        fig.colorbar(im, label="Mean aligned JS similarity")
        ax.set_title(f"{label} k={k}: seed-similarity heatmap")
        _save(fig, out / "08_seed_similarity_heatmap.png")

    runs = pd.read_csv(RESULTS_DIR / label / "definitive_ksweep_runs.csv")
    row = runs[(runs.k == k) & (runs.seed == seed)]
    if not row.empty:
        r = row.iloc[0]
        fig, ax = plt.subplots(figsize=(6, 4))
        bars = [r["prop_conf_lt_0.40"], r["prop_conf_0.40_0.60"], r["prop_conf_gt_0.60"]]
        ax.bar(["<0.40", "0.40-0.60", ">0.60"], bars, color=["#C44E52", "#DD8452", "#55A868"])
        ax.set_ylabel("Proportion of studies"); ax.set_title(f"{label} k={k} seed={seed}: dominant-topic confidence")
        _save(fig, out / "11_dominant_topic_confidence.png")
    print(f"[{label}] final-model figures written")


def comparison_figures():
    out = FIG_DIR / "comparison"
    ct_path = RESULTS_DIR / "cross_representation" / "dominant_topic_contingency_matrix.csv"
    if ct_path.exists():
        ct = pd.read_csv(ct_path, index_col=0)
        fig, ax = plt.subplots(figsize=(7, 6))
        im = ax.imshow(ct.values, cmap="magma")
        ax.set_xticks(range(len(ct.columns))); ax.set_xticklabels(ct.columns)
        ax.set_yticks(range(len(ct.index))); ax.set_yticklabels(ct.index)
        ax.set_xlabel("Full-text topic"); ax.set_ylabel("Metadata topic")
        for i in range(ct.shape[0]):
            for j in range(ct.shape[1]):
                ax.text(j, i, int(ct.values[i, j]), ha="center", va="center", color="white", fontsize=7)
        fig.colorbar(im, label="# studies")
        ax.set_title("Dominant-topic contingency: metadata vs full-text")
        _save(fig, out / "14_dominant_topic_contingency.png")

    align_path = RESULTS_DIR / "cross_representation" / "topic_alignment.json"
    if align_path.exists():
        with open(align_path, encoding="utf-8") as f:
            align = json.load(f)
        matched = align["matched_topics"]
        fig, ax = plt.subplots(figsize=(7, 5))
        labels = [f"A{m['metadata_topic']}-B{m['fulltext_topic']}" for m in matched]
        sims = [m["js_similarity"] for m in matched]
        ax.bar(labels, sims, color="#4C72B0")
        ax.set_xticklabels(labels, rotation=90, fontsize=7)
        ax.set_ylabel("JS similarity"); ax.set_title("Metadata vs full-text matched-topic similarity")
        _save(fig, out / "13_metadata_vs_fulltext_similarity.png")
    print("comparison figures written")


if __name__ == "__main__":
    import sys
    mode = sys.argv[1]
    if mode == "model_selection":
        model_selection_figures(sys.argv[2])
    elif mode == "final_model":
        final_model_figures(sys.argv[2], int(sys.argv[3]), int(sys.argv[4]))
    elif mode == "comparison":
        comparison_figures()
