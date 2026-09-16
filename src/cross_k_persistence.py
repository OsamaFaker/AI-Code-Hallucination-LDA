"""Repair task Part 5: does the k=8 full-text topic structure persist as k increases through
the near-equivalent candidate region {9,12,13,14,15}? Align k=8's medoid topics to each higher
k's medoid topics via rectangular Hungarian matching on complete topic-word distributions
(same dictionary throughout, so no shared-vocab projection is needed).
"""
import json
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from gensim.models import LdaModel

import sys
sys.path.insert(0, str(Path(__file__).resolve().parent))
from lda_core import align_topics_hungarian, js_similarity, top_n_words, topic_word_matrix

ROOT = Path(__file__).resolve().parents[1]
RESULTS_DIR = ROOT / "results" / "fulltext"
MODELS_DIR = ROOT / "models" / "fulltext"
FIG_DIR = ROOT / "figures" / "fulltext"

REFERENCE_K = 8
HIGHER_KS = [9, 12, 13, 14, 15]


def load_medoid_model(k):
    with open(RESULTS_DIR / f"representative_seed_k{k:02d}.json", encoding="utf-8") as f:
        med = json.load(f)
    seed = med["medoid_seed"]
    model = LdaModel.load(str(MODELS_DIR / f"k{k:02d}_seed{seed:02d}.model"))
    return model, seed


def main():
    ref_model, ref_seed = load_medoid_model(REFERENCE_K)
    ref_mat = topic_word_matrix(ref_model)
    ref_words = top_n_words(ref_model, topn=20)

    rows = []
    heat = np.full((REFERENCE_K, len(HIGHER_KS)), np.nan)
    for col, k in enumerate(HIGHER_KS):
        model, seed = load_medoid_model(k)
        mat = topic_word_matrix(model)
        words = top_n_words(model, topn=20)
        row_ind, col_ind = align_topics_hungarian(ref_mat, mat)
        for r, c in zip(row_ind, col_ind):
            js_sim = js_similarity(ref_mat[r], mat[c])
            cos = float(np.dot(ref_mat[r], mat[c]) /
                        (np.linalg.norm(ref_mat[r]) * np.linalg.norm(mat[c]) + 1e-12))
            si, sj = set(ref_words[r]), set(words[c])
            jacc = len(si & sj) / len(si | sj) if (si or sj) else 0.0
            rows.append({
                "reference_k": REFERENCE_K, "reference_topic": int(r),
                "compared_k": k, "compared_topic": int(c),
                "js_similarity": round(js_sim, 4), "cosine": round(cos, 4),
                "top20_jaccard": round(jacc, 4),
            })
            heat[r, col] = js_sim

    df = pd.DataFrame(rows)
    df.to_csv(RESULTS_DIR / "cross_k_topic_persistence.csv", index=False)

    # persistence classification per reference (k=8) topic: mean JS similarity to its best
    # match at each higher k
    persist = df.loc[df.groupby(["reference_topic", "compared_k"])["js_similarity"].idxmax()]
    persist_summary = persist.groupby("reference_topic")["js_similarity"].agg(
        mean="mean", min="min", max="max").reset_index()

    def classify(m):
        if m >= 0.55:
            return "highly persistent"
        elif m >= 0.40:
            return "moderately persistent"
        else:
            return "unstable"
    persist_summary["persistence_class"] = persist_summary["mean"].apply(classify)
    persist_summary.to_csv(RESULTS_DIR / "cross_k_topic_persistence_summary.csv", index=False)

    fig, ax = plt.subplots(figsize=(6, 6))
    im = ax.imshow(heat, cmap="viridis", vmin=0, vmax=1, aspect="auto")
    ax.set_xticks(range(len(HIGHER_KS))); ax.set_xticklabels([f"k={k}" for k in HIGHER_KS])
    ax.set_yticks(range(REFERENCE_K)); ax.set_yticklabels([f"T{i}" for i in range(REFERENCE_K)])
    ax.set_xlabel("Compared model"); ax.set_ylabel("k=8 reference topic")
    for i in range(REFERENCE_K):
        for j in range(len(HIGHER_KS)):
            ax.text(j, i, f"{heat[i,j]:.2f}", ha="center", va="center", color="white", fontsize=8)
    fig.colorbar(im, label="Best-match JS similarity")
    ax.set_title("k=8 topic persistence across the near-equivalent candidate region")
    fig.tight_layout()
    FIG_DIR.mkdir(parents=True, exist_ok=True)
    fig.savefig(FIG_DIR / "cross_k_topic_persistence_heatmap.png", bbox_inches="tight")
    plt.close(fig)

    print(persist_summary.to_string(index=False))
    print(f"\nWrote {RESULTS_DIR/'cross_k_topic_persistence.csv'}, "
          f"{RESULTS_DIR/'cross_k_topic_persistence_summary.csv'}, "
          f"{FIG_DIR/'cross_k_topic_persistence_heatmap.png'}")
    return df, persist_summary


if __name__ == "__main__":
    main()
