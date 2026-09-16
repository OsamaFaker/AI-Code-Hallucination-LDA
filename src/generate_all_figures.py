"""Freeze task Sections 13-21: regenerate every final figure from frozen numerical outputs.
Every figure here is built directly from a results/ or human_validation/ file - nothing is
hand-edited. PNG (300dpi) + PDF saved for each. Captions/axis labels/units included in-figure
where practical; full captions are recorded in reports/FIGURE_INDEX.md.
"""
import json
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from gensim.models import LdaModel
from scipy.stats import entropy

import sys
sys.path.insert(0, str(Path(__file__).resolve().parent))
from lda_core import build_bow_corpus, build_dictionary, compute_frex, doc_topic_matrix

ROOT = Path(__file__).resolve().parents[1]
RESULTS_DIR = ROOT / "results"
FIG_DIR = ROOT / "figures"
MODELS_DIR = ROOT / "models"
PREP_DIR = ROOT / "preprocessing"
DATA_DIR = ROOT / "data"
HV_DIR = ROOT / "human_validation"

plt.rcParams.update({
    "figure.dpi": 150, "savefig.dpi": 300, "font.size": 10,
    "axes.spines.top": False, "axes.spines.right": False,
    "axes.titlesize": 11, "axes.labelsize": 10,
})

REGISTRY = []  # populated as figures are saved; written to FIGURE_INDEX.md at the end


def _save(fig, path: Path, caption: str, analysis: str, source_data: str, script: str,
          destination: str = "Repository only"):
    path.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(path.with_suffix(".png"), bbox_inches="tight")
    fig.savefig(path.with_suffix(".pdf"), bbox_inches="tight")
    plt.close(fig)
    REGISTRY.append({
        "Figure ID": path.stem, "Filename": path.with_suffix(".png").relative_to(ROOT).as_posix(),
        "Analysis": analysis, "Purpose": caption, "Source data": source_data,
        "Script": script, "Recommended destination": destination,
    })


THIS_SCRIPT = "src/generate_all_figures.py"


# ---------------------------------------------------------------------------
# M8/M9 + F-equivalent not needed for fulltext (candidate comparison is metadata-only)
# ---------------------------------------------------------------------------
def fig_candidate_comparison():
    df = pd.read_csv(RESULTS_DIR / "metadata" / "k2_k5_candidate_comparison.csv")
    fig, axes = plt.subplots(1, 4, figsize=(14, 4), sharey=True)
    for ax, row in zip(axes, df.itertuples()):
        counts = eval(row.dominant_count_per_topic)
        colors = ["#C44E52" if c < 3 else "#4C72B0" for c in counts]
        ax.bar(range(len(counts)), counts, color=colors)
        ax.set_title(f"k={row.k} (medoid seed {row.medoid_seed})")
        ax.set_xlabel("Topic")
        ax.set_xticks(range(len(counts)))
    axes[0].set_ylabel("Dominant-study count (n)")
    fig.suptitle("M8: Metadata k=2-5 candidate comparison - dominant-study count per topic\n"
                 "(red = <3 dominant studies; mega-topic pattern visible at k=2,3)", y=1.08)
    fig.tight_layout()
    _save(fig, FIG_DIR / "metadata" / "M8_candidate_comparison_dominant_counts",
          "Dominant-study count per topic for the structural-medoid model at each candidate "
          "k=2,3,4,5, making the low-k mega-topic behavior visible (N=66 studies).",
          "metadata", "results/metadata/k2_k5_candidate_comparison.csv", THIS_SCRIPT,
          "Main manuscript (candidate: Main Figure A)")

    fig, axes = plt.subplots(1, 4, figsize=(14, 4))
    for ax, row in zip(axes, df.itertuples()):
        prev = eval(row.prevalence_per_topic)
        ax.pie(prev, labels=[f"T{i}\n{p:.0%}" for i, p in enumerate(prev)],
               colors=plt.cm.tab10.colors[:len(prev)])
        ax.set_title(f"k={row.k}")
    fig.suptitle("M9: Metadata k=2-5 dominant-topic prevalence (% of corpus per topic)", y=1.05)
    fig.tight_layout()
    _save(fig, FIG_DIR / "metadata" / "M9_candidate_prevalence",
          "Probabilistic topic prevalence (% of corpus) for each candidate k, N=66.",
          "metadata", "results/metadata/k2_k5_candidate_comparison.csv", THIS_SCRIPT)


# ---------------------------------------------------------------------------
# Final-model figures shared logic (metadata k=4 / fulltext k=8)
# ---------------------------------------------------------------------------
def load_final(label, k, seed, no_below, no_above):
    model = LdaModel.load(str(MODELS_DIR / label / f"k{k:02d}_seed{seed:02d}.model"))
    with open(PREP_DIR / label / "lemmatized_tokens_corrected.json", encoding="utf-8") as f:
        doc_tokens = json.load(f)
    study_ids = list(doc_tokens.keys())
    token_lists = [doc_tokens[s] for s in study_ids]
    dictionary = build_dictionary(token_lists, no_below, no_above)
    bow = build_bow_corpus(token_lists, dictionary)
    dt = doc_topic_matrix(model, bow)
    return model, dt, study_ids


def fig_topic_prevalence(label, k, seed, no_below, no_above, prefix):
    model, dt, study_ids = load_final(label, k, seed, no_below, no_above)
    dominant = dt.argmax(axis=1)
    counts = np.bincount(dominant, minlength=k)
    prevalence = dt.mean(axis=0)

    fig, axes = plt.subplots(1, 2, figsize=(11, 4.2))
    axes[0].bar(range(k), counts, color="#4C72B0")
    for i, c in enumerate(counts):
        axes[0].text(i, c + 0.5, f"n={c}\n({c/66:.0%})", ha="center", fontsize=8)
    axes[0].set_xlabel("Topic"); axes[0].set_ylabel(f"Dominant-study count (of N=66)")
    axes[0].set_title("Dominant-study count and % of corpus")
    axes[0].set_xticks(range(k))

    axes[1].bar(range(k), prevalence, color="#55A868")
    axes[1].set_xlabel("Topic"); axes[1].set_ylabel("Mean topic probability")
    axes[1].set_title("Probabilistic topic prevalence")
    axes[1].set_xticks(range(k))
    fig.suptitle(f"{prefix}11/F9: {label} final topic prevalence (k={k}, seed={seed}, N=66)")
    fig.tight_layout()
    _save(fig, FIG_DIR / label / f"{prefix}_topic_prevalence",
          f"Dominant-study count (n and %) and mean probabilistic prevalence per final topic, "
          f"{label} k={k}, N=66.", label,
          f"models/{label}/k{k:02d}_seed{seed:02d}.model", THIS_SCRIPT,
          "Main manuscript (candidate: Main Figure B)" if label == "metadata" else "Supplementary material")
    return model, dt, study_ids, dominant


def fig_top_terms(label, k, seed, prefix, model):
    frex_topics, _ = compute_frex(model, topn=15)
    fig, axes = plt.subplots(2, k, figsize=(2.6 * k, 7))
    for t in range(k):
        prob_terms = model.show_topic(t, topn=15)
        words, probs = zip(*prob_terms)
        axes[0, t].barh(range(len(words))[::-1], probs, color="#4C72B0")
        axes[0, t].set_yticks(range(len(words))[::-1]); axes[0, t].set_yticklabels(words, fontsize=7)
        axes[0, t].set_title(f"T{t} probability", fontsize=9)
        axes[0, t].set_xlabel("P(word|topic)")

        frex_words = [w for w, _ in frex_topics[t]]
        axes[1, t].barh(range(len(frex_words))[::-1], range(len(frex_words), 0, -1), color="#C44E52")
        axes[1, t].set_yticks(range(len(frex_words))[::-1]); axes[1, t].set_yticklabels(frex_words, fontsize=7)
        axes[1, t].set_title(f"T{t} FREX", fontsize=9)
        axes[1, t].set_xticks([])
    fig.suptitle(f"{label} final topics (k={k}, seed={seed}): top-15 probability terms (top row) "
                 f"and top-15 FREX/exclusive terms (bottom row)")
    fig.tight_layout()
    dest = "Main manuscript (candidate: Main Figure B)" if label == "metadata" else "Supplementary material"
    _save(fig, FIG_DIR / label / f"{prefix}_top_terms",
          f"Top-15 probability and FREX/exclusive terms per final topic, {label} k={k}.",
          label, f"models/{label}/k{k:02d}_seed{seed:02d}.model", THIS_SCRIPT, dest)


def fig_doc_topic_heatmap(label, k, seed, dt, study_ids, prefix):
    order = np.argsort(-dt.argmax(axis=1))
    fig, ax = plt.subplots(figsize=(6, max(6, 66 * 0.09)))
    im = ax.imshow(dt[order], aspect="auto", cmap="viridis", vmin=0, vmax=1)
    ax.set_xlabel("Topic"); ax.set_ylabel(f"Study (N=66, sorted by dominant topic)")
    ax.set_xticks(range(k))
    ax.set_yticks([])
    fig.colorbar(im, label="Topic probability")
    ax.set_title(f"{label} document-topic matrix (66 x {k}), k={k} seed={seed}")
    fig.tight_layout()
    _save(fig, FIG_DIR / label / f"{prefix}_document_topic_heatmap",
          f"Full 66 x {k} document-topic probability matrix, sorted by dominant topic, "
          f"{label} k={k}.", label, f"models/{label}/k{k:02d}_seed{seed:02d}.model", THIS_SCRIPT)


def fig_confidence_margin_entropy(label, k, seed, dt, prefix):
    sorted_probs = np.sort(dt, axis=1)[:, ::-1]
    top1 = sorted_probs[:, 0]
    margin = sorted_probs[:, 0] - sorted_probs[:, 1] if k > 1 else np.zeros(len(dt))
    ent = np.array([entropy(row + 1e-12, base=2) for row in dt])

    fig, axes = plt.subplots(1, 3, figsize=(13, 4))
    axes[0].hist(top1, bins=15, color="#4C72B0", edgecolor="white")
    axes[0].set_xlabel("Dominant-topic probability (top-1)"); axes[0].set_ylabel("Studies (n)")
    axes[0].set_title("Assignment-confidence distribution")

    axes[1].hist(margin, bins=15, color="#DD8452", edgecolor="white")
    axes[1].set_xlabel("p1 - p2 (probability margin)"); axes[1].set_ylabel("Studies (n)")
    axes[1].set_title("Probability-margin distribution")

    axes[2].hist(ent, bins=15, color="#55A868", edgecolor="white")
    axes[2].set_xlabel("Document-topic entropy (bits)"); axes[2].set_ylabel("Studies (n)")
    axes[2].set_title("Document-topic entropy distribution")
    fig.suptitle(f"{label} k={k} seed={seed}: assignment confidence, margin, and entropy (N=66)")
    fig.tight_layout()
    _save(fig, FIG_DIR / label / f"{prefix}_confidence_margin_entropy",
          f"Distribution of dominant-topic confidence, top1-top2 probability margin, and "
          f"document-topic entropy across all 66 studies, {label} k={k}.", label,
          f"models/{label}/k{k:02d}_seed{seed:02d}.model", THIS_SCRIPT)


def fig_topic_similarity_matrix(label, k, seed, model, prefix):
    mat = model.get_topics()
    from lda_core import js_similarity
    sim = np.zeros((k, k))
    for i in range(k):
        for j in range(k):
            vi, vj = mat[i], mat[j]
            cos = float(np.dot(vi, vj) / (np.linalg.norm(vi) * np.linalg.norm(vj) + 1e-12))
            sim[i, j] = cos
    fig, ax = plt.subplots(figsize=(5, 4.5))
    im = ax.imshow(sim, cmap="magma", vmin=0, vmax=1)
    ax.set_xticks(range(k)); ax.set_yticks(range(k))
    ax.set_xlabel("Topic"); ax.set_ylabel("Topic")
    for i in range(k):
        for j in range(k):
            ax.text(j, i, f"{sim[i,j]:.2f}", ha="center", va="center",
                     color="white" if sim[i, j] < 0.6 else "black", fontsize=8)
    fig.colorbar(im, label="Cosine similarity")
    ax.set_title(f"{label} k={k}: topic-word cosine similarity matrix")
    fig.tight_layout()
    _save(fig, FIG_DIR / label / f"{prefix}_topic_similarity_matrix",
          f"Pairwise topic-word cosine similarity among the {k} final topics, {label}.",
          label, f"models/{label}/k{k:02d}_seed{seed:02d}.model", THIS_SCRIPT)


def fig_representative_studies(label, k, seed, dt, study_ids, prefix):
    meta = pd.read_csv(DATA_DIR / "metadata_representation.csv").set_index("Study_ID")
    fig, axes = plt.subplots(k, 1, figsize=(9, 1.3 * k))
    if k == 1:
        axes = [axes]
    for t, ax in enumerate(axes):
        top_idx = np.argsort(-dt[:, t])[:3]
        labels, probs = [], []
        for i in top_idx:
            sid = study_ids[i]
            title = meta.loc[sid, "title"] if sid in meta.index else sid
            labels.append(f"{sid}: {str(title)[:55]}")
            probs.append(dt[i, t])
        ax.barh(range(len(labels))[::-1], probs, color="#8172B2")
        ax.set_yticks(range(len(labels))[::-1]); ax.set_yticklabels(labels, fontsize=7)
        ax.set_xlim(0, 1)
        ax.set_ylabel(f"T{t}", fontsize=8)
    axes[-1].set_xlabel("Topic probability")
    fig.suptitle(f"{label} k={k}: top-3 representative studies per topic")
    fig.tight_layout()
    _save(fig, FIG_DIR / label / f"{prefix}_representative_studies",
          f"Top-3 highest-loading studies per final topic with their topic probability, "
          f"{label} k={k}.", label, "data/metadata_representation.csv", THIS_SCRIPT)


# ---------------------------------------------------------------------------
# Full-text-only: length figures
# ---------------------------------------------------------------------------
def fig_fulltext_length():
    with open(RESULTS_DIR / "fulltext" / "length_diagnostics.json", encoding="utf-8") as f:
        diag = json.load(f)
    with open(PREP_DIR / "fulltext" / "lemmatized_tokens_corrected.json", encoding="utf-8") as f:
        doc_tokens = json.load(f)
    lengths = np.array([len(v) for v in doc_tokens.values()])

    fig, ax = plt.subplots(figsize=(6, 4))
    ax.hist(lengths, bins=20, color="#4C72B0", edgecolor="white")
    ax.axvline(diag["token_length_stats"]["mean"], color="#C44E52", linestyle="--", label="mean")
    ax.axvline(diag["token_length_stats"]["median"], color="#55A868", linestyle="--", label="median")
    ax.set_xlabel("Retained token count per document"); ax.set_ylabel("Studies (n)")
    ax.set_title(f"F19: Full-text document-length distribution (N=66, "
                 f"max/min ratio={diag['token_length_stats']['ratio_max_to_min']:.1f}x)")
    ax.legend()
    fig.tight_layout()
    _save(fig, FIG_DIR / "fulltext" / "F19_length_distribution",
          "Distribution of retained token counts across the 66 full-text documents.",
          "fulltext", "results/fulltext/length_diagnostics.json", THIS_SCRIPT)

    model, dt, study_ids = load_final("fulltext", 8, 2, 4, 0.75)
    top1 = dt.max(axis=1)
    fig, ax = plt.subplots(figsize=(6, 4.5))
    ax.scatter(lengths, top1, color="#4C72B0", alpha=0.7)
    z = np.polyfit(lengths, top1, 1)
    xs = np.linspace(lengths.min(), lengths.max(), 50)
    ax.plot(xs, np.polyval(z, xs), color="#C44E52", linestyle="--")
    r, p = diag["length_vs_confidence_pearson_r"], diag["length_vs_confidence_pearson_p"]
    ax.text(0.05, 0.95, f"r={r:.3f}, p={p:.3f}", transform=ax.transAxes, va="top",
            bbox=dict(boxstyle="round", facecolor="white", alpha=0.8))
    ax.set_xlabel("Document length (tokens)"); ax.set_ylabel("Dominant-topic probability")
    ax.set_title("F20: Document length vs. topic-assignment confidence (N=66)")
    fig.tight_layout()
    _save(fig, FIG_DIR / "fulltext" / "F20_length_vs_confidence",
          "Scatter of document length against dominant-topic assignment confidence, with "
          "Pearson r and p-value annotated.", "fulltext",
          "results/fulltext/length_diagnostics.json", THIS_SCRIPT,
          "Main manuscript (candidate: supports Main Figure D / limitations)")

    with open(RESULTS_DIR / "fulltext" / "length_balanced_sensitivity.json", encoding="utf-8") as f:
        bal = json.load(f)
    fig, ax = plt.subplots(figsize=(5, 4))
    metrics = ["JS similarity\nto full model", "Dominant-topic\nagreement"]
    vals = [bal["mean_js_similarity_to_full"], bal["dominant_topic_agreement"]]
    ax.bar(metrics, vals, color=["#4C72B0", "#DD8452"])
    for i, v in enumerate(vals):
        ax.text(i, v + 0.02, f"{v:.3f}", ha="center")
    ax.set_ylim(0, 1)
    ax.set_ylabel("Value")
    ax.set_title("F21: Full model vs. length-balanced sensitivity model")
    fig.tight_layout()
    _save(fig, FIG_DIR / "fulltext" / "F21_length_balanced_similarity",
          "Topic-word similarity and dominant-topic agreement between the full-text model "
          "and its length-balanced (token-capped) sensitivity variant.", "fulltext",
          "results/fulltext/length_balanced_sensitivity.json", THIS_SCRIPT,
          "Main manuscript (candidate: supports Main Figure D / limitations)")


# ---------------------------------------------------------------------------
# Cross-k persistence summary (F17)
# ---------------------------------------------------------------------------
def fig_cross_k_summary():
    df = pd.read_csv(RESULTS_DIR / "fulltext" / "cross_k_topic_persistence_summary.csv")
    colors = {"highly persistent": "#55A868", "moderately persistent": "#DD8452", "unstable": "#C44E52"}
    fig, ax = plt.subplots(figsize=(7, 4))
    bars = ax.bar(df.reference_topic, df["mean"], color=[colors[c] for c in df.persistence_class])
    ax.errorbar(df.reference_topic, df["mean"], yerr=[df["mean"] - df["min"], df["max"] - df["mean"]],
                fmt="none", ecolor="black", capsize=3)
    ax.set_xlabel("k=8 reference topic"); ax.set_ylabel("Mean best-match JS similarity (k=9..15)")
    ax.set_xticks(df.reference_topic)
    ax.set_title("F17: Per-topic persistence across the k=8-15 candidate region")
    handles = [plt.Rectangle((0, 0), 1, 1, color=c) for c in colors.values()]
    ax.legend(handles, colors.keys(), fontsize=8)
    fig.tight_layout()
    _save(fig, FIG_DIR / "fulltext" / "F17_cross_k_persistence_summary",
          "Mean (with min-max range) best-match JS similarity of each k=8 topic to its "
          "counterpart at k=9,12,13,14,15.", "fulltext",
          "results/fulltext/cross_k_topic_persistence_summary.csv", THIS_SCRIPT,
          "Main manuscript (candidate: Main Figure C)")


if __name__ == "__main__":
    print("Generating metadata final-model figures...")
    fig_candidate_comparison()
    model_m, dt_m, sids_m, dom_m = fig_topic_prevalence("metadata", 4, 14, 5, 0.50, "M")
    fig_top_terms("metadata", 4, 14, "M", model_m)
    fig_doc_topic_heatmap("metadata", 4, 14, dt_m, sids_m, "M")
    fig_confidence_margin_entropy("metadata", 4, 14, dt_m, "M")
    fig_topic_similarity_matrix("metadata", 4, 14, model_m, "M")
    fig_representative_studies("metadata", 4, 14, dt_m, sids_m, "M")

    print("Generating fulltext final-model figures...")
    model_f, dt_f, sids_f, dom_f = fig_topic_prevalence("fulltext", 8, 2, 4, 0.75, "F")
    fig_top_terms("fulltext", 8, 2, "F", model_f)
    fig_doc_topic_heatmap("fulltext", 8, 2, dt_f, sids_f, "F")
    fig_confidence_margin_entropy("fulltext", 8, 2, dt_f, "F")
    fig_topic_similarity_matrix("fulltext", 8, 2, model_f, "F")
    fig_representative_studies("fulltext", 8, 2, dt_f, sids_f, "F")
    fig_fulltext_length()
    fig_cross_k_summary()

    with open(RESULTS_DIR / "figure_registry_partial1.json", "w", encoding="utf-8") as f:
        json.dump(REGISTRY, f, indent=2)
    print(f"Done: {len(REGISTRY)} figures written (batch 1).")
