"""Publication figures for the RQ5 LDA analysis (frozen models, k=4).

Reads every plotted number directly from the frozen result files under
`results/` and `reports/FROZEN_MANUSCRIPT_VALUES.md`; nothing here re-fits
or approximates an LDA model. See `figures/LDA_FIGURE_INDEX.md` for the
mapping from output file to source data file.
"""

from __future__ import annotations

import json
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from matplotlib.patches import Patch

ROOT = Path(__file__).resolve().parent.parent
RESULTS = ROOT / "results"
FIGURES = ROOT / "figures"

# ---------------------------------------------------------------------------
# Style: grayscale, serif, print-safe
# ---------------------------------------------------------------------------

GRAY_1 = "#262626"  # near-black -- primary series / metadata
GRAY_2 = "#8c8c8c"  # mid gray -- secondary series / full text
GRAY_GRID = "#d9d9d9"
BLACK = "#000000"

plt.rcParams.update(
    {
        "font.family": "serif",
        "font.serif": ["Times New Roman", "Nimbus Roman", "DejaVu Serif"],
        "mathtext.fontset": "stix",
        "font.size": 9,
        "axes.titlesize": 9,
        "axes.labelsize": 9,
        "xtick.labelsize": 8,
        "ytick.labelsize": 8,
        "legend.fontsize": 8,
        "figure.facecolor": "white",
        "axes.facecolor": "white",
        "savefig.facecolor": "white",
        "axes.edgecolor": "black",
        "axes.linewidth": 0.8,
        "pdf.fonttype": 42,
        "ps.fonttype": 42,
        "axes.grid": False,
    }
)


def save(fig: plt.Figure, stub: Path) -> None:
    stub.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(stub.with_suffix(".pdf"), bbox_inches="tight", pad_inches=0.04)
    fig.savefig(stub.with_suffix(".png"), dpi=450, bbox_inches="tight", pad_inches=0.04)
    plt.close(fig)
    print(f"saved {stub.with_suffix('.pdf').relative_to(ROOT)}")


# ---------------------------------------------------------------------------
# Figure A / S1: topic prevalence bar charts
# ---------------------------------------------------------------------------


def prevalence_bar(labels: list[str], pct_values: list[float], out_stub: Path) -> None:
    n = len(labels)
    fig, ax = plt.subplots(figsize=(6.3, 0.62 * n + 0.9))

    order = list(range(n))[::-1]  # first label ends up on top
    y = np.arange(n)
    vals_plot = [pct_values[i] for i in order]
    labels_plot = [labels[i] for i in order]

    ax.barh(y, vals_plot, height=0.55, color=GRAY_1, edgecolor="black", linewidth=0.7, zorder=3)
    ax.set_yticks(y)
    ax.set_yticklabels(labels_plot)
    ax.set_xlabel("Topic prevalence (%)")
    xmax = max(pct_values) * 1.20
    ax.set_xlim(0, xmax)

    for yi, v in zip(y, vals_plot):
        ax.text(v + xmax * 0.012, yi, f"{v:.1f}%", va="center", ha="left", fontsize=8)

    ax.spines["top"].set_visible(False)
    ax.spines["right"].set_visible(False)
    ax.spines["left"].set_visible(False)
    ax.tick_params(axis="y", length=0)
    ax.xaxis.grid(True, color=GRAY_GRID, linewidth=0.6, zorder=0)
    ax.set_axisbelow(True)

    fig.tight_layout(pad=0.3)
    save(fig, out_stub)


def make_figure_a() -> None:
    df = pd.read_csv(RESULTS / "metadata" / "k_sweep_summary.csv")
    row = df[df["k"] == 4].iloc[0]
    prevalence = json.loads(row["prevalence_json"])
    assert row["dominant_counts_json"] == "[22, 16, 15, 13]"
    pct = [round(p * 100, 1) for p in prevalence]

    labels = [
        "T0  Hallucination benchmarks & mitigation",
        "T1  Programming education feedback",
        "T2  Developer trust & experience",
        "T3  Correctness, testing & non-determinism",
    ]
    prevalence_bar(labels, pct, FIGURES / "metadata" / "topic_prevalence")


def make_figure_s1() -> None:
    df = pd.read_csv(RESULTS / "fulltext" / "k_sweep_summary.csv")
    row = df[df["k"] == 4].iloc[0]
    prevalence = json.loads(row["prevalence_json"])
    assert row["dominant_counts_json"] == "[17, 8, 16, 25]"
    pct = [round(p * 100, 1) for p in prevalence]

    labels = [
        "FT0  Programming education",
        "FT1  Repair & verification",
        "FT2  Package hallucination & security",
        "FT3  Iterative/retrieval mitigation",
    ]
    prevalence_bar(labels, pct, FIGURES / "fulltext" / "topic_prevalence")


# ---------------------------------------------------------------------------
# Figure B: metadata model-selection diagnostics (k = 2..20)
# ---------------------------------------------------------------------------


def make_figure_b() -> None:
    df = pd.read_csv(RESULTS / "metadata" / "k_sweep_summary.csv").sort_values("k")
    k = df["k"].to_numpy()
    selected_k = 4
    finalists = [2, 3, 4, 5]

    fig, axes = plt.subplots(2, 2, figsize=(7.0, 5.6), sharex=True)

    def style_axis(ax, ylabel, panel_label):
        ax.set_ylabel(ylabel)
        ax.set_xlim(1, 21)
        ax.set_xticks(range(2, 21, 2))
        ax.spines["top"].set_visible(False)
        ax.spines["right"].set_visible(False)
        ax.axvline(selected_k, color="black", linestyle="--", linewidth=1.0, zorder=1)
        ax.text(
            0.02,
            0.96,
            panel_label,
            transform=ax.transAxes,
            fontsize=9,
            fontweight="bold",
            va="top",
            ha="left",
        )

    # Panel A: mean C_v
    ax = axes[0, 0]
    ax.errorbar(
        k, df["mean_cv"], yerr=df["sd_cv"], color=GRAY_1, marker="o", markersize=4,
        linewidth=1.1, capsize=2.5, elinewidth=0.8, ecolor=GRAY_2,
    )
    style_axis(ax, r"Mean $C_v$ coherence", "A")

    # Panel B: mean C_NPMI
    ax = axes[0, 1]
    ax.errorbar(
        k, df["mean_cnpmi"], yerr=df["sd_cnpmi"], color=GRAY_1, marker="o", markersize=4,
        linewidth=1.1, capsize=2.5, elinewidth=0.8, ecolor=GRAY_2,
    )
    style_axis(ax, r"Mean $C_{NPMI}$ coherence", "B")

    # Panel C: cross-seed stability
    ax = axes[1, 0]
    ax.errorbar(
        k, df["mean_stability"], yerr=df["sd_stability"], color=GRAY_1, marker="o",
        markersize=4, linewidth=1.1, capsize=2.5, elinewidth=0.8, ecolor=GRAY_2,
    )
    style_axis(ax, "Cross-seed stability", "C")
    ax.set_xlabel("Number of topics (k)")

    # Panel D: topic-population diagnostics
    ax = axes[1, 1]
    ax.plot(
        k, df["zero_dominance_topics"], color=GRAY_1, marker="o", markersize=4,
        linewidth=1.1, linestyle="-", label="Zero-dominance topics",
    )
    ax.plot(
        k, df["topics_lt5"], color=GRAY_2, marker="s", markersize=4,
        linewidth=1.1, linestyle="--", label="Thin topics (<5 dominant studies)",
    )
    style_axis(ax, "Topic count", "D")
    ax.set_xlabel("Number of topics (k)")
    ax.legend(loc="upper left", bbox_to_anchor=(0.0, 0.90), frameon=False, handlelength=2.4)

    # "selected k" annotation on panel A only, to avoid clutter
    axes[0, 0].annotate(
        "selected k",
        xy=(selected_k, axes[0, 0].get_ylim()[1]),
        xytext=(selected_k + 0.6, axes[0, 0].get_ylim()[0] + 0.82 * (axes[0, 0].get_ylim()[1] - axes[0, 0].get_ylim()[0])),
        fontsize=7.5,
        ha="left",
    )

    fig.text(
        0.5, -0.01,
        f"Finalists after Pareto filtering and the pre-specified stability-based reduction: k = {', '.join(map(str, finalists))}",
        ha="center", va="top", fontsize=7.5, style="italic",
    )

    fig.tight_layout(pad=0.5, h_pad=1.6, w_pad=1.8)
    save(fig, FIGURES / "metadata" / "model_selection_diagnostics")


# ---------------------------------------------------------------------------
# Figure C: cross-representation contingency heatmap
# ---------------------------------------------------------------------------


def make_figure_c() -> None:
    ctab = pd.read_csv(RESULTS / "cross_representation" / "contingency_matrix.csv", index_col=0)
    mat = ctab.to_numpy(dtype=int)
    assert mat.tolist() == [[1, 1, 3, 17], [9, 2, 2, 3], [7, 1, 7, 0], [0, 4, 4, 5]]

    perm = pd.read_csv(RESULTS / "cross_representation" / "permutation_test.csv").iloc[0]
    ari, nmi, p_ari = perm["observed_ari"], perm["observed_nmi"], perm["p_ari"]

    row_labels = [
        "T0\nHallucination/mitigation",
        "T1\nEducation/feedback",
        "T2\nDeveloper trust",
        "T3\nCorrectness/testing",
    ]
    col_labels = [
        "FT0\nEducation",
        "FT1\nRepair/verification",
        "FT2\nPackage/security",
        "FT3\nMitigation",
    ]

    _heatmap(
        mat, row_labels, col_labels,
        annotation=f"ARI = {ari:.3f}     NMI = {nmi:.3f}     Permutation test (10,000 reps): empirical p ≈ {p_ari:.4f}",
        out_stub=FIGURES / "cross_representation" / "topic_contingency",
        cell_fmt=lambda v: f"{v:d}",
        cbar_label="No. of studies",
    )

    # Optional supplementary version: row percentages
    row_sums = mat.sum(axis=1, keepdims=True)
    pct_mat = 100.0 * mat / row_sums
    _heatmap(
        pct_mat, row_labels, col_labels,
        annotation="Cell values are row percentages (share of each metadata topic's studies by full-text dominant topic).",
        out_stub=FIGURES / "cross_representation" / "topic_contingency_rowpct",
        cell_fmt=lambda v: f"{v:.0f}%",
        cbar_label="Row %",
        vmax=100.0,
    )


def _heatmap(mat, row_labels, col_labels, annotation, out_stub, cell_fmt, cbar_label, vmax=None):
    fig, ax = plt.subplots(figsize=(5.6, 4.9))
    vmax = mat.max() if vmax is None else vmax
    im = ax.imshow(mat, cmap="Greys", vmin=0, vmax=vmax, aspect="equal")

    ax.set_xticks(range(len(col_labels)))
    ax.set_xticklabels(col_labels, fontsize=7.8)
    ax.set_yticks(range(len(row_labels)))
    ax.set_yticklabels(row_labels, fontsize=7.8)
    ax.set_xlabel("Full-text dominant topic")
    ax.set_ylabel("Metadata dominant topic")

    ax.set_xticks(np.arange(-0.5, mat.shape[1], 1), minor=True)
    ax.set_yticks(np.arange(-0.5, mat.shape[0], 1), minor=True)
    ax.grid(which="minor", color="white", linewidth=2.2)
    ax.tick_params(which="minor", length=0)
    ax.tick_params(which="major", length=0)
    for spine in ax.spines.values():
        spine.set_visible(False)

    for i in range(mat.shape[0]):
        for j in range(mat.shape[1]):
            val = mat[i, j]
            color = "white" if val > 0.55 * vmax else "black"
            ax.text(j, i, cell_fmt(val), ha="center", va="center", fontsize=9.5, color=color)

    cbar = fig.colorbar(im, ax=ax, fraction=0.046, pad=0.04)
    cbar.set_label(cbar_label, fontsize=8)
    cbar.ax.tick_params(labelsize=7.5)

    fig.text(0.5, -0.06, annotation, ha="center", va="top", fontsize=7.8, wrap=True)
    fig.tight_layout(pad=0.4)
    save(fig, out_stub)


# ---------------------------------------------------------------------------
# Supplementary Figure S2: robustness summary
# ---------------------------------------------------------------------------


def make_figure_s2() -> None:
    sub_meta = pd.read_csv(RESULTS / "metadata" / "subsampling_k4.csv")
    sub_ft = pd.read_csv(RESULTS / "fulltext" / "subsampling_k4.csv")
    te_meta = pd.read_csv(RESULTS / "metadata" / "training_effort_sensitivity.csv")
    te_ft = pd.read_csv(RESULTS / "fulltext" / "training_effort_sensitivity.csv")
    dict_meta = pd.read_csv(RESULTS / "metadata" / "dictionary_sensitivity.csv")
    dict_ft = pd.read_csv(RESULTS / "fulltext" / "dictionary_sensitivity.csv")

    panelA_meta = [sub_meta["js_similarity"].mean(), sub_meta["ari"].mean(), sub_meta["nmi"].mean()]
    panelA_ft = [sub_ft["js_similarity"].mean(), sub_ft["ari"].mean(), sub_ft["nmi"].mean()]

    te_meta4 = te_meta[te_meta["k"] == 4].iloc[0]
    te_ft4 = te_ft[te_ft["k"] == 4].iloc[0]
    panelB_meta = [te_meta4["js_similarity"], te_meta4["dominant_topic_agreement_ari"], te_meta4["dominant_topic_agreement_nmi"]]
    panelB_ft = [te_ft4["js_similarity"], te_ft4["dominant_topic_agreement_ari"], te_ft4["dominant_topic_agreement_nmi"]]

    dm4 = dict_meta[dict_meta["k"] == 4].sort_values(["no_below", "no_above"])
    df4 = dict_ft[dict_ft["k"] == 4].sort_values(["no_below", "no_above"])
    panelC_meta = [
        dm4.iloc[0]["js_similarity"], dm4.iloc[0]["dominant_topic_agreement_ari"],
        dm4.iloc[1]["js_similarity"], dm4.iloc[1]["dominant_topic_agreement_ari"],
    ]
    panelC_ft = [
        df4.iloc[0]["js_similarity"], df4.iloc[0]["dominant_topic_agreement_ari"],
        df4.iloc[1]["js_similarity"], df4.iloc[1]["dominant_topic_agreement_ari"],
    ]

    fig, axes = plt.subplots(1, 3, figsize=(9.4, 3.6), sharey=True)

    def grouped_bars(ax, cats, meta_vals, ft_vals, title):
        x = np.arange(len(cats))
        w = 0.34
        ax.bar(x - w / 2, meta_vals, width=w, color=GRAY_1, edgecolor="black", linewidth=0.6, label="Metadata", zorder=3)
        ax.bar(
            x + w / 2, ft_vals, width=w, color="white", edgecolor="black", linewidth=0.6,
            hatch="////", label="Full text", zorder=3,
        )
        ax.set_xticks(x)
        ax.set_xticklabels(cats, fontsize=7.8)
        ax.set_ylim(0, 1.0)
        ax.set_title(title, fontsize=8.6, fontweight="bold", loc="left")
        ax.spines["top"].set_visible(False)
        ax.spines["right"].set_visible(False)
        ax.yaxis.grid(True, color=GRAY_GRID, linewidth=0.6, zorder=0)
        ax.set_axisbelow(True)

    grouped_bars(axes[0], ["JS", "ARI", "NMI"], panelA_meta, panelA_ft, "A  Subsampling (80%, n=100 draws)")
    grouped_bars(axes[1], ["JS", "ARI", "NMI"], panelB_meta, panelB_ft, "B  Training-effort sensitivity")
    grouped_bars(
        axes[2],
        ["JS\n(nbr. 1)", "ARI\n(nbr. 1)", "JS\n(nbr. 2)", "ARI\n(nbr. 2)"],
        panelC_meta, panelC_ft,
        "C  Dictionary-threshold sensitivity",
    )
    axes[0].set_ylabel("Score")
    for ax in axes[1:]:
        ax.tick_params(labelleft=False)

    handles = [
        Patch(facecolor=GRAY_1, edgecolor="black", label="Metadata"),
        Patch(facecolor="white", edgecolor="black", hatch="////", label="Full text"),
    ]
    fig.legend(handles=handles, loc="upper center", ncol=2, frameon=False, bbox_to_anchor=(0.5, 1.06), fontsize=8.5)

    fig.text(
        0.5, -0.05,
        "Dictionary nbr. 1: no_below=5, no_above=0.4; nbr. 2: no_below=6, no_above=0.5 "
        "(both neighbour thresholds of the frozen no_below=6, no_above=0.4 dictionary).",
        ha="center", va="top", fontsize=7.2, style="italic",
    )

    fig.tight_layout(pad=0.5, w_pad=1.2)
    save(fig, FIGURES / "robustness" / "robustness_summary")


# ---------------------------------------------------------------------------

if __name__ == "__main__":
    make_figure_a()
    make_figure_s1()
    make_figure_b()
    make_figure_c()
    make_figure_s2()
