"""Batch 3: regenerate the model-selection sweep figures (M1-M7/F1-F7), seed-similarity
heatmaps (M10/F8), dominant-confidence (M15/F13), and the two original cross-representation
figures (C1/C2), replacing the earlier ungitered/unregistered 01-14-numbered PNGs with
properly captioned, registry-tracked, PNG+PDF outputs under the M/F/C naming scheme.
"""
import json
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import pandas as pd

import sys
sys.path.insert(0, str(Path(__file__).resolve().parent))
from generate_all_figures import _save, THIS_SCRIPT

ROOT = Path(__file__).resolve().parents[1]
RESULTS_DIR = ROOT / "results"
FIG_DIR = ROOT / "figures"

plt.rcParams.update({"figure.dpi": 150, "savefig.dpi": 300, "font.size": 10,
                      "axes.spines.top": False, "axes.spines.right": False})


def model_selection_figures(label, prefix):
    runs = pd.read_csv(RESULTS_DIR / label / "definitive_ksweep_runs.csv")
    stab = pd.read_csv(RESULTS_DIR / label / "seed_stability_by_k.csv")
    n_k = runs["k"].nunique()

    fig, ax = plt.subplots(figsize=(6.5, 4.3))
    for k, grp in runs.groupby("k"):
        ax.scatter([k] * len(grp), grp["c_v"], alpha=0.4, color="#4C72B0", s=14)
    means = runs.groupby("k")["c_v"].mean()
    ax.plot(means.index, means.values, color="#C44E52", marker="o", label="mean across 20 seeds")
    ax.set_xlabel("k (number of topics)"); ax.set_ylabel("C_v coherence")
    ax.set_title(f"{prefix}1: {label} C_v vs k (N=66, k=2-20, 20 seeds/k)")
    ax.legend()
    _save(fig, FIG_DIR / label / f"{prefix}1_cv_vs_k",
          f"C_v coherence for every seeded model (points) and the per-k mean (line), {label}, "
          f"N=66, k=2-20, 20 seeds/k.", label, "results/{label}/definitive_ksweep_runs.csv".format(label=label), THIS_SCRIPT)

    fig, ax = plt.subplots(figsize=(6.5, 4.3))
    for k, grp in runs.groupby("k"):
        ax.scatter([k] * len(grp), grp["c_npmi"], alpha=0.4, color="#4C72B0", s=14)
    means = runs.groupby("k")["c_npmi"].mean()
    ax.plot(means.index, means.values, color="#C44E52", marker="o")
    ax.set_xlabel("k"); ax.set_ylabel("C_NPMI coherence")
    ax.set_title(f"{prefix}2: {label} C_NPMI vs k (N=66)")
    _save(fig, FIG_DIR / label / f"{prefix}2_cnpmi_vs_k",
          f"C_NPMI coherence per seeded model and per-k mean, {label}, N=66.", label,
          f"results/{label}/definitive_ksweep_runs.csv", THIS_SCRIPT)

    fig, ax = plt.subplots(figsize=(6.5, 4.3))
    ax.plot(stab["k"], stab["js_similarity_mean"], marker="o", color="#55A868")
    ax.fill_between(stab["k"], stab["js_similarity_min"], stab["js_similarity_max"], alpha=0.2, color="#55A868")
    ax.set_xlabel("k"); ax.set_ylabel("Cross-seed JS similarity")
    ax.set_title(f"{prefix}3: {label} cross-seed stability vs k (N=66, 20 seeds/k)")
    _save(fig, FIG_DIR / label / f"{prefix}3_stability_vs_k",
          f"Mean (line) and min-max range (band) of Hungarian-aligned cross-seed Jensen-"
          f"Shannon similarity per k, {label}, N=66.", label,
          f"results/{label}/seed_stability_by_k.csv", THIS_SCRIPT)

    fig, ax = plt.subplots(figsize=(6.5, 4.3))
    div = runs.groupby("k")["topic_diversity"].mean()
    ax.plot(div.index, div.values, marker="o", color="#8172B2")
    ax.set_xlabel("k"); ax.set_ylabel("Topic diversity (top-20 unique-word ratio)")
    ax.set_title(f"{prefix}4: {label} topic diversity vs k (N=66)")
    _save(fig, FIG_DIR / label / f"{prefix}4_diversity_vs_k",
          f"Mean topic diversity (unique-word proportion among all top-20 lists) per k, "
          f"{label}, N=66.", label, f"results/{label}/definitive_ksweep_runs.csv", THIS_SCRIPT)

    fig, ax = plt.subplots(figsize=(6.5, 4.3))
    red = runs.groupby("k")["mean_top20_jaccard"].mean()
    ax.plot(red.index, red.values, marker="o", color="#CCB974")
    ax.set_xlabel("k"); ax.set_ylabel("Mean pairwise top-20 Jaccard")
    ax.set_title(f"{prefix}5: {label} topic redundancy vs k (N=66)")
    _save(fig, FIG_DIR / label / f"{prefix}5_redundancy_vs_k",
          f"Mean pairwise top-20 Jaccard overlap per k (higher = more redundant), {label}, "
          f"N=66.", label, f"results/{label}/definitive_ksweep_runs.csv", THIS_SCRIPT)

    fig, ax = plt.subplots(figsize=(6.5, 4.3))
    zero = runs.groupby("k")["n_topics_0_studies"].mean()
    thin = runs.groupby("k")["n_topics_lt3_studies"].mean()
    ax.plot(zero.index, zero.values, marker="o", label="0-study (zero-dominance) topics", color="#C44E52")
    ax.plot(thin.index, thin.values, marker="s", label="<3-study topics", color="#DD8452")
    ax.set_xlabel("k"); ax.set_ylabel("Mean count per model"); ax.legend()
    ax.set_title(f"{prefix}6: {label} thin/zero-dominance topic diagnostics vs k (N=66)")
    _save(fig, FIG_DIR / label / f"{prefix}6_thin_zero_topics_vs_k",
          f"Mean number of zero-dominance and thin (<3-study) topics per k, {label}, N=66.",
          label, f"results/{label}/definitive_ksweep_runs.csv", THIS_SCRIPT)

    fig, axes = plt.subplots(2, 3, figsize=(15, 8))
    panels = [
        (means.index, runs.groupby("k")["c_v"].mean(), "C_v"),
        (means.index, runs.groupby("k")["c_npmi"].mean(), "C_NPMI"),
        (stab["k"], stab["js_similarity_mean"], "Cross-seed stability"),
        (div.index, div.values, "Topic diversity"),
        (red.index, red.values, "Topic redundancy (Jaccard)"),
        (zero.index, zero.values, "Zero-dominance topics"),
    ]
    for ax, (x, y, title) in zip(axes.flat, panels):
        ax.plot(x, y, marker="o"); ax.set_title(title); ax.set_xlabel("k")
    fig.suptitle(f"{prefix}7: {label} combined multi-metric model-selection overview (N=66)")
    fig.tight_layout()
    _save(fig, FIG_DIR / label / f"{prefix}7_combined_model_selection",
          f"Six-panel overview of all model-selection criteria vs. k, {label}, N=66.", label,
          f"results/{label}/{{definitive_ksweep_runs.csv,seed_stability_by_k.csv}}", THIS_SCRIPT)


def seed_similarity_and_confidence(label, k, seed, prefix):
    sim_path = RESULTS_DIR / label / f"seed_similarity_matrix_k{k:02d}.csv"
    sim = pd.read_csv(sim_path, index_col=0)
    fig, ax = plt.subplots(figsize=(7, 6))
    im = ax.imshow(sim.values, cmap="viridis")
    ax.set_xticks(range(len(sim.columns))); ax.set_xticklabels(sim.columns, rotation=90, fontsize=6)
    ax.set_yticks(range(len(sim.index))); ax.set_yticklabels(sim.index, fontsize=6)
    fig.colorbar(im, label="Mean aligned JS similarity")
    ax.set_xlabel("Seed"); ax.set_ylabel("Seed")
    ax.set_title(f"{prefix}10/F8: {label} k={k} seed-similarity heatmap (20 seeds, N=66)")
    _save(fig, FIG_DIR / label / f"{prefix}10_seed_similarity_heatmap",
          f"Pairwise mean aligned JS similarity among all 20 seeded models at the final k, "
          f"{label} k={k}.", label, f"results/{label}/seed_similarity_matrix_k{k:02d}.csv", THIS_SCRIPT)

    runs = pd.read_csv(RESULTS_DIR / label / "definitive_ksweep_runs.csv")
    row = runs[(runs.k == k) & (runs.seed == seed)].iloc[0]
    fig, ax = plt.subplots(figsize=(6, 4.3))
    bars = [row["prop_conf_lt_0.40"], row["prop_conf_0.40_0.60"], row["prop_conf_gt_0.60"]]
    ax.bar(["<0.40", "0.40-0.60", ">0.60"], bars, color=["#C44E52", "#DD8452", "#55A868"])
    for i, v in enumerate(bars):
        ax.text(i, v + 0.01, f"{v:.0%}", ha="center")
    ax.set_ylabel("Proportion of studies (of N=66)")
    ax.set_title(f"{prefix}15/F13: {label} k={k} seed={seed} dominant-topic confidence distribution")
    _save(fig, FIG_DIR / label / f"{prefix}15_dominant_topic_confidence",
          f"Proportion of the 66 studies whose dominant-topic probability falls in each "
          f"confidence band, {label} k={k} seed={seed}.", label,
          f"results/{label}/definitive_ksweep_runs.csv", THIS_SCRIPT)


def cross_representation_original():
    ct_path = RESULTS_DIR / "cross_representation" / "dominant_topic_contingency_matrix.csv"
    ct = pd.read_csv(ct_path, index_col=0)
    fig, ax = plt.subplots(figsize=(7, 6))
    im = ax.imshow(ct.values, cmap="magma")
    ax.set_xticks(range(len(ct.columns))); ax.set_xticklabels(ct.columns)
    ax.set_yticks(range(len(ct.index))); ax.set_yticklabels(ct.index)
    ax.set_xlabel("Full-text topic"); ax.set_ylabel("Metadata topic")
    for i in range(ct.shape[0]):
        for j in range(ct.shape[1]):
            ax.text(j, i, int(ct.values[i, j]), ha="center", va="center", color="white", fontsize=7)
    fig.colorbar(im, label="# studies (of N=66)")
    ax.set_title("C2: Dominant-topic contingency matrix (metadata x full-text)")
    _save(fig, FIG_DIR / "comparison" / "C2_dominant_topic_contingency",
          "Contingency table of dominant-topic assignment between the metadata (k=4) and "
          "full-text (k=8) models across all 66 shared studies.", "cross-representation",
          "results/cross_representation/dominant_topic_contingency_matrix.csv", THIS_SCRIPT)

    align_path = RESULTS_DIR / "cross_representation" / "topic_alignment.json"
    with open(align_path, encoding="utf-8") as f:
        align = json.load(f)
    matched = align["matched_topics"]
    fig, ax = plt.subplots(figsize=(7, 5))
    labels = [f"metaT{m['metadata_topic']}-fullT{m['fulltext_topic']}" for m in matched]
    sims = [m["js_similarity"] for m in matched]
    ax.bar(labels, sims, color="#4C72B0")
    ax.set_xticks(range(len(labels))); ax.set_xticklabels(labels, rotation=90, fontsize=8)
    ax.set_ylabel("JS similarity"); ax.set_ylim(0, 1)
    ax.set_title("C1: Metadata vs. full-text topic-alignment (JS similarity per matched pair)")
    _save(fig, FIG_DIR / "comparison" / "C1_topic_alignment_heatmap",
          "JS similarity for each rectangular-Hungarian-matched metadata-fulltext topic pair.",
          "cross-representation", "results/cross_representation/topic_alignment.json", THIS_SCRIPT)


if __name__ == "__main__":
    model_selection_figures("metadata", "M")
    model_selection_figures("fulltext", "F")
    seed_similarity_and_confidence("metadata", 4, 14, "M")
    seed_similarity_and_confidence("fulltext", 8, 2, "F")
    cross_representation_original()

    from generate_all_figures import REGISTRY
    with open(RESULTS_DIR / "figure_registry_partial3.json", "w", encoding="utf-8") as f:
        json.dump(REGISTRY, f, indent=2)
    print(f"Done: {len(REGISTRY)} figures in this batch's registry.")
