"""Section 12: controlled sensitivity comparison of domain-term treatment.
HF-A: retain all substantive domain terms (= the frozen base corpus).
HF-B: remove extremely ubiquitous, low-discriminative domain terms (doc-freq >= 70% AND in
      the Section-12 domain-term list).
HF-C: same corpus as HF-A; interpretation lens changes to FREX/exclusivity instead of raw
      top-probability words (no separate model needed - computed directly on the HF-A fits).

Run as a controlled comparison at a single representative k (10, the pilot midpoint) x 5 seeds,
at the frozen Stage-1 dictionary configuration, on the frozen Stage-2 training budget.
"""
import argparse
import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd
from sklearn.metrics import adjusted_rand_score, normalized_mutual_info_score

sys.path.insert(0, str(Path(__file__).resolve().parent))
from hf_terms import DOMAIN_TERMS
from lda_core import (align_topics_hungarian, build_bow_corpus, build_dictionary,
                        coherence_scores, compute_frex, doc_topic_matrix, fit_lda, js_similarity,
                        pairwise_redundancy, project_pair_to_shared_vocab, topic_diversity,
                        topic_word_matrix)

ROOT = Path(__file__).resolve().parents[1]
PREP_DIR = ROOT / "preprocessing"
RESULTS_DIR = ROOT / "results"

REP_K = 10
SEEDS = [0, 1, 2, 3, 4]


def make_hf_b_tokens(doc_tokens: dict, hf_terms_csv: Path, no_above: float) -> dict:
    """HF-B removes domain terms that are ubiquitous *among those the dictionary actually
    retains* - i.e. terms whose document-frequency is high relative to no_above but still
    below it (terms at/above no_above are already excluded by dictionary filtering, so a
    fixed absolute cutoff like 0.70 can be a no-op once no_above <= 0.70, as happened here
    for both representations: no_above=0.50 and 0.75 respectively). The cutoff is therefore
    set relative to the frozen no_above: the top half of the [0, no_above) range."""
    relative_cutoff = no_above * 0.5
    hf = pd.read_csv(hf_terms_csv)
    ubiquitous_domain = set(
        hf.loc[(hf["domain_specific"]) & (hf["document_frequency_pct"] >= relative_cutoff)
               & (hf["document_frequency_pct"] < no_above), "term"]
    )
    return {sid: [t for t in toks if t not in ubiquitous_domain] for sid, toks in doc_tokens.items()}, ubiquitous_domain


def fit_config(token_lists, no_below, no_above, passes, iterations, seeds=SEEDS, k=REP_K):
    dictionary = build_dictionary(token_lists, no_below=no_below, no_above=no_above)
    bow = build_bow_corpus(token_lists, dictionary)
    models = []
    for seed in seeds:
        m = fit_lda(bow, dictionary, k=k, seed=seed, passes=passes, iterations=iterations)
        models.append(m)
    return dictionary, bow, models


def summarize(models, token_lists, dictionary, bow):
    cvs, npmis, divs, reds = [], [], [], []
    for m in models:
        coh = coherence_scores(m, token_lists, dictionary, bow)
        cvs.append(coh["c_v"]); npmis.append(coh["c_npmi"])
        divs.append(topic_diversity(m))
        reds.append(pairwise_redundancy(m)["mean_top20_jaccard"])
    mats = [topic_word_matrix(m) for m in models]
    sims = []
    for i in range(len(mats)):
        for j in range(i + 1, len(mats)):
            r, c = align_topics_hungarian(mats[i], mats[j])
            sims.append(np.mean([js_similarity(mats[i][a], mats[j][b]) for a, b in zip(r, c)]))
    return {
        "mean_c_v": float(np.mean(cvs)), "mean_c_npmi": float(np.mean(npmis)),
        "mean_diversity": float(np.mean(divs)), "mean_redundancy_jaccard": float(np.mean(reds)),
        "stability": float(np.mean(sims)) if sims else float("nan"),
    }


def run_for_representation(label: str, no_below: int, no_above: float, passes: int, iterations: int):
    with open(PREP_DIR / label / "lemmatized_tokens_corrected.json", encoding="utf-8") as f:
        doc_tokens_a = json.load(f)
    study_ids = list(doc_tokens_a.keys())
    tokens_a = [doc_tokens_a[s] for s in study_ids]

    hf_csv_name = "metadata_high_frequency_terms.csv" if label == "metadata" else "fulltext_high_frequency_terms.csv"
    doc_tokens_b, removed_terms = make_hf_b_tokens(doc_tokens_a, PREP_DIR / hf_csv_name, no_above)
    tokens_b = [doc_tokens_b[s] for s in study_ids]

    dict_a, bow_a, models_a = fit_config(tokens_a, no_below, no_above, passes, iterations)
    dict_b, bow_b, models_b = fit_config(tokens_b, no_below, no_above, passes, iterations)

    summary_a = summarize(models_a, tokens_a, dict_a, bow_a)
    summary_b = summarize(models_b, tokens_b, dict_b, bow_b)

    # document-assignment agreement between HF-A and HF-B (seed 0 representative pair)
    dt_a = doc_topic_matrix(models_a[0], bow_a).argmax(axis=1)
    dt_b = doc_topic_matrix(models_b[0], bow_b).argmax(axis=1)
    ari = adjusted_rand_score(dt_a, dt_b)
    nmi = normalized_mutual_info_score(dt_a, dt_b)

    mat_a0, mat_b0 = topic_word_matrix(models_a[0]), topic_word_matrix(models_b[0])
    mat_a0, mat_b0 = project_pair_to_shared_vocab(mat_a0, dict_a, mat_b0, dict_b)
    row_ind, col_ind = align_topics_hungarian(mat_a0, mat_b0)
    cos_sims = []
    for r, c in zip(row_ind, col_ind):
        va, vb = mat_a0[r], mat_b0[c]
        cos_sims.append(float(np.dot(va, vb) / (np.linalg.norm(va) * np.linalg.norm(vb) + 1e-12)))

    # HF-C: FREX-based interpretation of the HF-A model (seed 0), no separate corpus
    frex_topics, _ = compute_frex(models_a[0])

    out = {
        "representation": label,
        "k": REP_K,
        "removed_ubiquitous_domain_terms": sorted(removed_terms),
        "HF_A_retain_all": summary_a,
        "HF_B_remove_ubiquitous_domain_terms": summary_b,
        "HF_A_vs_HF_B_document_assignment_ARI": float(ari),
        "HF_A_vs_HF_B_document_assignment_NMI": float(nmi),
        "HF_A_vs_HF_B_mean_topic_word_cosine": float(np.mean(cos_sims)) if cos_sims else None,
        "HF_C_frex_top_terms_per_topic_from_HF_A_seed0": [
            [w for w, _ in topic] for topic in frex_topics
        ],
    }
    out_dir = RESULTS_DIR / label
    out_dir.mkdir(parents=True, exist_ok=True)
    with open(out_dir / "domain_term_sensitivity.json", "w", encoding="utf-8") as f:
        json.dump(out, f, indent=2)
    print(f"[{label}] HF-A cv={summary_a['mean_c_v']:.3f} vs HF-B cv={summary_b['mean_c_v']:.3f}; "
          f"ARI={ari:.3f} NMI={nmi:.3f}; removed {len(removed_terms)} terms")
    return out


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("label")
    ap.add_argument("no_below", type=int)
    ap.add_argument("no_above", type=float)
    ap.add_argument("passes", type=int)
    ap.add_argument("iterations", type=int)
    args = ap.parse_args()
    run_for_representation(args.label, args.no_below, args.no_above, args.passes, args.iterations)
