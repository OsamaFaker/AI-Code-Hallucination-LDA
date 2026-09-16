"""Section 24: full-text-only length diagnostics + a length-balanced sensitivity model.
Balanced representation caps tokens per major section so no single long article dominates.
"""
import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd
from scipy.stats import f_oneway, pearsonr
from sklearn.metrics import adjusted_rand_score, normalized_mutual_info_score

sys.path.insert(0, str(Path(__file__).resolve().parent))
from lda_core import (align_topics_hungarian, build_bow_corpus, build_dictionary,
                        doc_topic_matrix, fit_lda, js_similarity, project_pair_to_shared_vocab,
                        topic_word_matrix)

ROOT = Path(__file__).resolve().parents[1]
PREP_DIR = ROOT / "preprocessing"
DATA_DIR = ROOT / "data"
RESULTS_DIR = ROOT / "results" / "fulltext"

MAX_TOKENS_PER_SECTION = 400  # balanced-model cap; documented sensitivity choice


def length_diagnostics(no_below, no_above, k, passes, iterations, medoid_seed):
    with open(PREP_DIR / "fulltext" / "lemmatized_tokens_corrected.json", encoding="utf-8") as f:
        doc_tokens = json.load(f)
    study_ids = list(doc_tokens.keys())
    token_lists = [doc_tokens[s] for s in study_ids]
    lengths = np.array([len(t) for t in token_lists])

    stats = {
        "mean": float(lengths.mean()), "median": float(np.median(lengths)),
        "sd": float(lengths.std()), "iqr": float(np.percentile(lengths, 75) - np.percentile(lengths, 25)),
        "min": int(lengths.min()), "max": int(lengths.max()),
        "ratio_max_to_min": float(lengths.max() / max(lengths.min(), 1)),
    }

    dictionary = build_dictionary(token_lists, no_below, no_above)
    bow = build_bow_corpus(token_lists, dictionary)
    model = fit_lda(bow, dictionary, k=k, seed=medoid_seed, passes=passes, iterations=iterations)
    dt = doc_topic_matrix(model, bow)
    dominant = dt.argmax(axis=1)

    # association between document length and topic assignment (one-way ANOVA of length by
    # dominant topic) + correlation between length and top-1 probability (over-long docs
    # artificially diluting confidence would show as negative correlation)
    groups = [lengths[dominant == t] for t in range(k) if (dominant == t).sum() > 1]
    anova_f, anova_p = (float("nan"), float("nan"))
    if len(groups) >= 2:
        anova_f, anova_p = f_oneway(*groups)
        anova_f, anova_p = float(anova_f), float(anova_p)
    top1_conf = dt.max(axis=1)
    corr_r, corr_p = pearsonr(lengths, top1_conf)

    diag = {
        "token_length_stats": stats,
        "length_vs_dominant_topic_anova_F": anova_f,
        "length_vs_dominant_topic_anova_p": anova_p,
        "length_vs_confidence_pearson_r": float(corr_r),
        "length_vs_confidence_pearson_p": float(corr_p),
        "top5_longest_studies": [study_ids[i] for i in np.argsort(-lengths)[:5]],
        "top5_shortest_studies": [study_ids[i] for i in np.argsort(lengths)[:5]],
    }
    with open(RESULTS_DIR / "length_diagnostics.json", "w", encoding="utf-8") as f:
        json.dump(diag, f, indent=2)
    print(f"[fulltext] length ratio max/min={stats['ratio_max_to_min']:.1f}, "
          f"length~confidence r={corr_r:.3f} (p={corr_p:.3f})")
    return diag, model, dictionary, bow, study_ids


def balanced_sensitivity_model(no_below, no_above, k, passes, iterations, medoid_seed,
                                 full_model, full_dictionary, full_bow, study_ids):
    ft_manifest = pd.read_csv(DATA_DIR / "fulltext_representation_manifest.csv").set_index("Study_ID")
    with open(PREP_DIR / "fulltext" / "lemmatized_tokens_corrected.json", encoding="utf-8") as f:
        doc_tokens = json.load(f)

    # Approximate section-balanced sampling: since section boundaries were not preserved
    # token-by-token in the saved lemma lists, apply a global per-document token cap
    # (MAX_TOKENS_PER_SECTION * 6 canonical sections ~= 2400 tokens) as a length-balancing
    # sensitivity check - documented as an approximation, not literal per-section capping.
    cap = MAX_TOKENS_PER_SECTION * 6
    balanced_tokens = {sid: (toks[:cap] if len(toks) > cap else toks)
                        for sid, toks in doc_tokens.items()}
    bal_list = [balanced_tokens[s] for s in study_ids]

    dictionary_b = build_dictionary(bal_list, no_below, no_above)
    bow_b = build_bow_corpus(bal_list, dictionary_b)
    model_b = fit_lda(bow_b, dictionary_b, k=k, seed=medoid_seed, passes=passes, iterations=iterations)

    mat_full, mat_bal = topic_word_matrix(full_model), topic_word_matrix(model_b)
    mat_full, mat_bal = project_pair_to_shared_vocab(mat_full, full_dictionary, mat_bal, dictionary_b)
    row_ind, col_ind = align_topics_hungarian(mat_full, mat_bal)
    js_sims = [js_similarity(mat_full[r], mat_bal[c]) for r, c in zip(row_ind, col_ind)]

    dom_full = doc_topic_matrix(full_model, full_bow).argmax(axis=1)
    dom_bal_raw = doc_topic_matrix(model_b, bow_b).argmax(axis=1)
    remap = {int(c): int(r) for r, c in zip(row_ind, col_ind)}
    dom_bal = np.array([remap.get(int(t), int(t)) for t in dom_bal_raw])
    ari = adjusted_rand_score(dom_full, dom_bal)
    nmi = normalized_mutual_info_score(dom_full, dom_bal)

    result = {
        "token_cap_per_document": cap,
        "mean_js_similarity_to_full": float(np.mean(js_sims)),
        "ari_vs_full": float(ari), "nmi_vs_full": float(nmi),
        "dominant_topic_agreement": float((dom_full == dom_bal).mean()),
    }
    with open(RESULTS_DIR / "length_balanced_sensitivity.json", "w", encoding="utf-8") as f:
        json.dump(result, f, indent=2)
    print(f"[fulltext] length-balanced sensitivity: JS={result['mean_js_similarity_to_full']:.3f} "
          f"dominant_agree={result['dominant_topic_agreement']:.3f}")
    return result


if __name__ == "__main__":
    import argparse
    ap = argparse.ArgumentParser()
    ap.add_argument("no_below", type=int)
    ap.add_argument("no_above", type=float)
    ap.add_argument("k", type=int)
    ap.add_argument("passes", type=int)
    ap.add_argument("iterations", type=int)
    ap.add_argument("seed", type=int)
    args = ap.parse_args()
    diag, model, dictionary, bow, study_ids = length_diagnostics(
        args.no_below, args.no_above, args.k, args.passes, args.iterations, args.seed)
    balanced_sensitivity_model(args.no_below, args.no_above, args.k, args.passes, args.iterations,
                                args.seed, model, dictionary, bow, study_ids)
