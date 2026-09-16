"""Section 11 / Section 15 Stage 1: systematic no_above x no_below dictionary-threshold grid,
evaluated at a representative pilot k-set and several seeds, per representation independently.
Parallelized across combinations with ProcessPoolExecutor (20 cores available).
"""
import itertools
import json
import sys
import time
from concurrent.futures import ProcessPoolExecutor, as_completed
from pathlib import Path

import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parent))
from lda_core import (align_topics_hungarian, build_bow_corpus, build_dictionary, coherence_scores,
                        fit_lda, js_similarity, pairwise_redundancy, prevalence_and_thin_topics,
                        topic_diversity, topic_word_matrix)

ROOT = Path(__file__).resolve().parents[1]
PREP_DIR = ROOT / "preprocessing"
RESULTS_DIR = ROOT / "results"

NO_ABOVE_GRID = [0.50, 0.60, 0.70, 0.75, 0.80, 0.85, 0.90, 0.95, 1.00]
NO_BELOW_GRID = [2, 3, 4, 5]
PILOT_K = [5, 10, 15]
PILOT_SEEDS = [0, 1, 2, 3, 4]
PILOT_PASSES = 10
PILOT_ITER = 200

_TOKEN_LISTS = None
_STUDY_IDS = None


def _init_worker(label: str):
    global _TOKEN_LISTS, _STUDY_IDS
    with open(PREP_DIR / label / "lemmatized_tokens_corrected.json", encoding="utf-8") as f:
        d = json.load(f)
    _STUDY_IDS = list(d.keys())
    _TOKEN_LISTS = [d[s] for s in _STUDY_IDS]


def _run_combo(args):
    no_below, no_above = args
    global _TOKEN_LISTS
    token_lists = _TOKEN_LISTS
    dictionary = build_dictionary(token_lists, no_below=no_below, no_above=no_above)
    bow = build_bow_corpus(token_lists, dictionary)
    doc_lens = [sum(c for _, c in b) for b in bow]
    n_removed_hf = None  # computed relative to no_above=1.00 baseline outside

    rows = []
    for k in PILOT_K:
        seed_mats = []
        cv_list, npmi_list, div_list, red_list, thin_list, zero_list = [], [], [], [], [], []
        for seed in PILOT_SEEDS:
            model = fit_lda(bow, dictionary, k=k, seed=seed, passes=PILOT_PASSES,
                             iterations=PILOT_ITER)
            coh = coherence_scores(model, token_lists, dictionary, bow)
            cv_list.append(coh["c_v"])
            npmi_list.append(coh["c_npmi"])
            div_list.append(topic_diversity(model))
            prev = prevalence_and_thin_topics(model, bow)
            thin_list.append(prev["n_topics_lt3_studies"])
            zero_list.append(prev["n_topics_0_studies"])
            red = pairwise_redundancy(model)
            red_list.append(red["mean_top20_jaccard"])
            seed_mats.append(topic_word_matrix(model))

        # cross-seed stability: mean pairwise JS similarity after Hungarian alignment
        sims = []
        for i in range(len(seed_mats)):
            for j in range(i + 1, len(seed_mats)):
                row_ind, col_ind = align_topics_hungarian(seed_mats[i], seed_mats[j])
                pair_sims = [js_similarity(seed_mats[i][r], seed_mats[j][c])
                             for r, c in zip(row_ind, col_ind)]
                sims.append(np.mean(pair_sims))
        stability = float(np.mean(sims)) if sims else float("nan")

        rows.append({
            "no_below": no_below, "no_above": no_above, "k": k,
            "vocab_size": len(dictionary),
            "total_tokens": int(sum(doc_lens)),
            "mean_tokens_per_doc": float(np.mean(doc_lens)),
            "median_tokens_per_doc": float(np.median(doc_lens)),
            "min_tokens_per_doc": int(np.min(doc_lens)),
            "max_tokens_per_doc": int(np.max(doc_lens)),
            "n_empty_docs": int(sum(1 for l in doc_lens if l == 0)),
            "mean_c_v": float(np.mean(cv_list)),
            "mean_c_npmi": float(np.mean(npmi_list)),
            "stability_js_similarity": stability,
            "mean_topic_diversity": float(np.mean(div_list)),
            "mean_topic_redundancy_jaccard": float(np.mean(red_list)),
            "mean_thin_topic_count_lt3": float(np.mean(thin_list)),
            "mean_zero_dominance_topic_count": float(np.mean(zero_list)),
        })
    return rows


def run_for_representation(label: str):
    t0 = time.time()
    combos = list(itertools.product(NO_BELOW_GRID, NO_ABOVE_GRID))
    all_rows = []
    with ProcessPoolExecutor(max_workers=12, initializer=_init_worker, initargs=(label,)) as ex:
        futs = {ex.submit(_run_combo, c): c for c in combos}
        done = 0
        for fut in as_completed(futs):
            all_rows.extend(fut.result())
            done += 1
            if done % 6 == 0:
                print(f"[{label}] {done}/{len(combos)} combos done "
                      f"({time.time()-t0:.0f}s elapsed)")
    df = pd.DataFrame(all_rows).sort_values(["no_below", "no_above", "k"])
    out_dir = RESULTS_DIR / label
    out_dir.mkdir(parents=True, exist_ok=True)
    df.to_csv(out_dir / "stage1_dictionary_threshold_sweep.csv", index=False)
    print(f"[{label}] DONE in {time.time()-t0:.0f}s -> "
          f"{out_dir/'stage1_dictionary_threshold_sweep.csv'}")
    return df


if __name__ == "__main__":
    rep = sys.argv[1] if len(sys.argv) > 1 else "both"
    if rep in ("metadata", "both"):
        run_for_representation("metadata")
    if rep in ("fulltext", "both"):
        run_for_representation("fulltext")
