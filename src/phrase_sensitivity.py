"""Section 13: phrase-treatment sensitivity - unigrams-only vs unigrams+bigrams, at the frozen
dictionary/training configuration, representative k x 5 seeds. Bigrams are discovered by
gensim's NPMI-scored Phrases detector, never manually forced.
"""
import argparse
import json
import sys
from pathlib import Path

import numpy as np
from sklearn.metrics import adjusted_rand_score, normalized_mutual_info_score

sys.path.insert(0, str(Path(__file__).resolve().parent))
from domain_term_sensitivity import fit_config, summarize
from lda_core import (align_topics_hungarian, doc_topic_matrix, project_pair_to_shared_vocab,
                        topic_word_matrix)
from phrase_detection import detect_bigrams, discovered_phrase_vocab

ROOT = Path(__file__).resolve().parents[1]
PREP_DIR = ROOT / "preprocessing"
RESULTS_DIR = ROOT / "results"
REP_K = 10


def run_for_representation(label: str, no_below: int, no_above: float, passes: int, iterations: int,
                            min_count: int = 3, threshold: float = 0.4):
    with open(PREP_DIR / label / "lemmatized_tokens_corrected.json", encoding="utf-8") as f:
        doc_tokens = json.load(f)
    study_ids = list(doc_tokens.keys())
    unigram_tokens = [doc_tokens[s] for s in study_ids]

    bigram_tokens, phraser = detect_bigrams(unigram_tokens, min_count=min_count, threshold=threshold)
    phrase_vocab = discovered_phrase_vocab(bigram_tokens)

    dict_u, bow_u, models_u = fit_config(unigram_tokens, no_below, no_above, passes, iterations)
    dict_b, bow_b, models_b = fit_config(bigram_tokens, no_below, no_above, passes, iterations)

    summary_u = summarize(models_u, unigram_tokens, dict_u, bow_u)
    summary_b = summarize(models_b, bigram_tokens, dict_b, bow_b)

    dt_u = doc_topic_matrix(models_u[0], bow_u).argmax(axis=1)
    dt_b = doc_topic_matrix(models_b[0], bow_b).argmax(axis=1)
    ari = adjusted_rand_score(dt_u, dt_b)
    nmi = normalized_mutual_info_score(dt_u, dt_b)

    mat_u0, mat_b0 = topic_word_matrix(models_u[0]), topic_word_matrix(models_b[0])
    mat_u0, mat_b0 = project_pair_to_shared_vocab(mat_u0, dict_u, mat_b0, dict_b)
    row_ind, col_ind = align_topics_hungarian(mat_u0, mat_b0)
    cos_sims = []
    for r, c in zip(row_ind, col_ind):
        va, vb = mat_u0[r], mat_b0[c]
        cos_sims.append(float(np.dot(va, vb) / (np.linalg.norm(va) * np.linalg.norm(vb) + 1e-12)))

    out = {
        "representation": label, "k": REP_K,
        "min_count": min_count, "npmi_threshold": threshold,
        "n_discovered_phrases_in_vocab": len(phrase_vocab),
        "example_discovered_phrases": sorted(phrase_vocab)[:40],
        "unigram_only": summary_u,
        "unigram_plus_bigram": summary_b,
        "unigram_vs_bigram_document_assignment_ARI": float(ari),
        "unigram_vs_bigram_document_assignment_NMI": float(nmi),
        "unigram_vs_bigram_mean_topic_word_cosine": float(np.mean(cos_sims)) if cos_sims else None,
    }
    out_dir = RESULTS_DIR / label
    out_dir.mkdir(parents=True, exist_ok=True)
    with open(out_dir / "phrase_sensitivity.json", "w", encoding="utf-8") as f:
        json.dump(out, f, indent=2)
    print(f"[{label}] unigram cv={summary_u['mean_c_v']:.3f} vs bigram cv={summary_b['mean_c_v']:.3f}; "
          f"{len(phrase_vocab)} phrases discovered; ARI={ari:.3f}")
    return out, bigram_tokens


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("label")
    ap.add_argument("no_below", type=int)
    ap.add_argument("no_above", type=float)
    ap.add_argument("passes", type=int)
    ap.add_argument("iterations", type=int)
    args = ap.parse_args()
    run_for_representation(args.label, args.no_below, args.no_above, args.passes, args.iterations)
