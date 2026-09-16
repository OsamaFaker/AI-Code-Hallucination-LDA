"""Repair task Part 1.1/1.2: objective, non-arbitrary comparison of candidate k values using
the STRUCTURAL MEDOID model at each k (never a coherence-selected seed). Builds a per-k row
with quantitative diagnostics pulled from already-saved models/run tables - no refitting.
"""
import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd
from gensim.models import LdaModel

sys.path.insert(0, str(Path(__file__).resolve().parent))
from lda_core import build_bow_corpus, build_dictionary, doc_topic_matrix, pairwise_redundancy

ROOT = Path(__file__).resolve().parents[1]
PREP_DIR = ROOT / "preprocessing"
RESULTS_DIR = ROOT / "results"
MODELS_DIR = ROOT / "models"


def load_medoid(label, k):
    with open(RESULTS_DIR / label / f"representative_seed_k{k:02d}.json", encoding="utf-8") as f:
        med = json.load(f)
    return med["medoid_seed"], med["medoid_mean_similarity"]


def candidate_row(label, k, no_below, no_above):
    seed, medoid_sim = load_medoid(label, k)
    model = LdaModel.load(str(MODELS_DIR / label / f"k{k:02d}_seed{seed:02d}.model"))

    with open(PREP_DIR / label / "lemmatized_tokens_corrected.json", encoding="utf-8") as f:
        doc_tokens = json.load(f)
    token_lists = list(doc_tokens.values())
    dictionary = build_dictionary(token_lists, no_below, no_above)
    bow = build_bow_corpus(token_lists, dictionary)
    dt = doc_topic_matrix(model, bow)
    dominant = dt.argmax(axis=1)
    counts = np.bincount(dominant, minlength=k)
    top1 = dt.max(axis=1)

    runs = pd.read_csv(RESULTS_DIR / label / "definitive_ksweep_runs.csv")
    row = runs[(runs.k == k) & (runs.seed == seed)].iloc[0]

    stab = pd.read_csv(RESULTS_DIR / label / "seed_stability_by_k.csv")
    stab_row = stab[stab.k == k].iloc[0]

    red = pairwise_redundancy(model)

    return {
        "k": k,
        "medoid_seed": int(seed),
        "medoid_mean_structural_similarity": round(float(medoid_sim), 4),
        "c_v": round(float(row["c_v"]), 4),
        "c_npmi": round(float(row["c_npmi"]), 4),
        "cross_seed_js_stability_mean": round(float(stab_row["js_similarity_mean"]), 4),
        "cross_seed_js_stability_sd": round(float(stab_row["js_similarity_sd"]), 4),
        "topic_diversity": round(float(row["topic_diversity"]), 4),
        "mean_top20_jaccard_redundancy": round(red["mean_top20_jaccard"], 4),
        "mean_cosine_redundancy": round(red["mean_cosine"], 4),
        "n_topics_zero_dominant_studies": int((counts == 0).sum()),
        "n_topics_lt3_dominant_studies": int((counts < 3).sum()),
        "min_dominant_study_count": int(counts.min()),
        "max_dominant_study_count": int(counts.max()),
        "dominant_count_per_topic": counts.tolist(),
        "mean_topic_prevalence": round(float(dt.mean(axis=0).mean()), 4),
        "prevalence_per_topic": [round(v, 4) for v in dt.mean(axis=0).tolist()],
        "mean_dominant_topic_confidence": round(float(top1.mean()), 4),
        "prop_confidence_lt_0.40": round(float(row["prop_conf_lt_0.40"]), 4),
        "prop_confidence_0.40_0.60": round(float(row["prop_conf_0.40_0.60"]), 4),
        "prop_confidence_gt_0.60": round(float(row["prop_conf_gt_0.60"]), 4),
    }


def main(label, k_values, no_below, no_above, out_name):
    rows = [candidate_row(label, k, no_below, no_above) for k in k_values]
    df = pd.DataFrame(rows)
    out_path = RESULTS_DIR / label / out_name
    df.to_csv(out_path, index=False)
    print(df.to_string(index=False))
    print(f"\nWrote {out_path}")
    return df


if __name__ == "__main__":
    import argparse
    ap = argparse.ArgumentParser()
    ap.add_argument("label")
    ap.add_argument("k_values")  # comma-separated
    ap.add_argument("no_below", type=int)
    ap.add_argument("no_above", type=float)
    ap.add_argument("out_name")
    args = ap.parse_args()
    ks = [int(x) for x in args.k_values.split(",")]
    main(args.label, ks, args.no_below, args.no_above, args.out_name)
