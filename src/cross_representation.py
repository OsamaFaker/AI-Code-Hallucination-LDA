"""Section 25: compare Analysis A (metadata) and Analysis B (full text) only after each has
independently frozen its final model. Handles k_A != k_B via rectangular Hungarian matching.
"""
import json
from pathlib import Path

import numpy as np
import pandas as pd
from gensim.models import LdaModel
from scipy.optimize import linear_sum_assignment
from sklearn.metrics import adjusted_rand_score, normalized_mutual_info_score

import sys
sys.path.insert(0, str(Path(__file__).resolve().parent))
from lda_core import build_bow_corpus, build_dictionary, doc_topic_matrix, js_similarity

ROOT = Path(__file__).resolve().parents[1]
RESULTS_DIR = ROOT / "results"
MODELS_DIR = ROOT / "models"
PREP_DIR = ROOT / "preprocessing"
OUT_DIR = RESULTS_DIR / "cross_representation"


def load_final(label, k, seed):
    model = LdaModel.load(str(MODELS_DIR / label / f"k{k:02d}_seed{seed:02d}.model"))
    with open(PREP_DIR / label / "lemmatized_tokens_corrected.json", encoding="utf-8") as f:
        doc_tokens = json.load(f)
    return model, doc_tokens


def top_n_words(model, topn=20):
    return [set(w for w, _ in model.show_topic(i, topn=topn)) for i in range(model.num_topics)]


def compare(k_a, seed_a, k_b, seed_b, no_below_a, no_above_a, no_below_b, no_above_b):
    model_a, tokens_a = load_final("metadata", k_a, seed_a)
    model_b, tokens_b = load_final("fulltext", k_b, seed_b)
    study_ids = list(tokens_a.keys())  # same 66 studies, same order in both representations
    assert study_ids == list(tokens_b.keys())

    # Build a shared vocabulary spanning both models' dictionaries for cosine/JS comparison
    dict_a = build_dictionary(list(tokens_a.values()), no_below_a, no_above_a)
    dict_b = build_dictionary(list(tokens_b.values()), no_below_b, no_above_b)
    shared_vocab = {}
    for d in (dict_a, dict_b):
        for tok in d.values():
            if tok not in shared_vocab:
                shared_vocab[tok] = len(shared_vocab)
    V = len(shared_vocab)

    def project(model, dictionary):
        raw = model.get_topics()
        mapped = np.zeros((raw.shape[0], V))
        for local_id, tok in dictionary.items():
            mapped[:, shared_vocab[tok]] = raw[:, local_id]
        return mapped

    mat_a, mat_b = project(model_a, dict_a), project(model_b, dict_b)
    ka, kb = mat_a.shape[0], mat_b.shape[0]

    cost = np.zeros((ka, kb))
    cos = np.zeros((ka, kb))
    jacc = np.zeros((ka, kb))
    words_a, words_b = top_n_words(model_a), top_n_words(model_b)
    for i in range(ka):
        for j in range(kb):
            sim = js_similarity(mat_a[i], mat_b[j])
            cost[i, j] = 1.0 - sim
            cos[i, j] = float(np.dot(mat_a[i], mat_b[j]) /
                               (np.linalg.norm(mat_a[i]) * np.linalg.norm(mat_b[j]) + 1e-12))
            si, sj = words_a[i], words_b[j]
            jacc[i, j] = len(si & sj) / len(si | sj) if (si or sj) else 0.0

    row_ind, col_ind = linear_sum_assignment(cost)
    matched = [{
        "metadata_topic": int(r), "fulltext_topic": int(c),
        "js_similarity": float(1 - cost[r, c]), "cosine": float(cos[r, c]),
        "top20_jaccard": float(jacc[r, c]),
    } for r, c in zip(row_ind, col_ind)]
    unmatched_a = [i for i in range(ka) if i not in row_ind]
    unmatched_b = [j for j in range(kb) if j not in col_ind]

    dt_a = build_bow_corpus(list(tokens_a.values()), dict_a)
    dt_b = build_bow_corpus(list(tokens_b.values()), dict_b)
    dom_a = doc_topic_matrix(model_a, dt_a).argmax(axis=1)
    dom_b = doc_topic_matrix(model_b, dt_b).argmax(axis=1)
    ari = adjusted_rand_score(dom_a, dom_b)
    nmi = normalized_mutual_info_score(dom_a, dom_b)

    contingency = pd.crosstab(pd.Series(dom_a, name="metadata_topic"),
                               pd.Series(dom_b, name="fulltext_topic"))

    OUT_DIR.mkdir(parents=True, exist_ok=True)
    contingency.to_csv(OUT_DIR / "dominant_topic_contingency_matrix.csv")
    with open(OUT_DIR / "topic_alignment.json", "w", encoding="utf-8") as f:
        json.dump({
            "k_metadata": ka, "k_fulltext": kb,
            "matched_topics": matched,
            "unmatched_metadata_topics": unmatched_a,
            "unmatched_fulltext_topics": unmatched_b,
            "document_assignment_ari": float(ari),
            "document_assignment_nmi": float(nmi),
        }, f, indent=2)
    print(f"k_A={ka} k_B={kb}; ARI={ari:.3f} NMI={nmi:.3f}; "
          f"{len(unmatched_a)} unmatched-A, {len(unmatched_b)} unmatched-B")
    return matched, ari, nmi, contingency


if __name__ == "__main__":
    import argparse
    ap = argparse.ArgumentParser()
    ap.add_argument("k_a", type=int); ap.add_argument("seed_a", type=int)
    ap.add_argument("k_b", type=int); ap.add_argument("seed_b", type=int)
    ap.add_argument("no_below_a", type=int); ap.add_argument("no_above_a", type=float)
    ap.add_argument("no_below_b", type=int); ap.add_argument("no_above_b", type=float)
    args = ap.parse_args()
    compare(args.k_a, args.seed_a, args.k_b, args.seed_b,
            args.no_below_a, args.no_above_a, args.no_below_b, args.no_above_b)
