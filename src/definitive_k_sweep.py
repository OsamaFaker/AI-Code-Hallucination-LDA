"""Sections 16-19: the definitive k-sweep. k=2..20 (optionally 21-25), 20 seeds (0-19), at the
frozen Stage-1 dictionary configuration and frozen Stage-2 training budget, per representation
independently. Saves every model's per-seed metrics plus cross-seed (Hungarian/JS) stability
per k. Parallelized across (k, seed) with ProcessPoolExecutor.
"""
import argparse
import json
import pickle
import sys
import time
from concurrent.futures import ProcessPoolExecutor, as_completed
from pathlib import Path

import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parent))
from lda_core import (build_bow_corpus, build_dictionary, coherence_scores, fit_lda,
                        pairwise_redundancy, prevalence_and_thin_topics, topic_diversity,
                        topic_word_matrix)

ROOT = Path(__file__).resolve().parents[1]
PREP_DIR = ROOT / "preprocessing"
RESULTS_DIR = ROOT / "results"
MODELS_DIR = ROOT / "models"

SEEDS = list(range(20))
K_RANGE = list(range(2, 21))

_TOKEN_LISTS = None
_STUDY_IDS = None
_DICTIONARY = None
_BOW = None
_PASSES = None
_ITERATIONS = None
_ALPHA = None
_ETA = None
_LABEL = None


def _init_worker(label, no_below, no_above, passes, iterations, alpha, eta):
    global _TOKEN_LISTS, _STUDY_IDS, _DICTIONARY, _BOW, _PASSES, _ITERATIONS, _ALPHA, _ETA, _LABEL
    with open(PREP_DIR / label / "lemmatized_tokens_corrected.json", encoding="utf-8") as f:
        d = json.load(f)
    _STUDY_IDS = list(d.keys())
    _TOKEN_LISTS = [d[s] for s in _STUDY_IDS]
    _DICTIONARY = build_dictionary(_TOKEN_LISTS, no_below=no_below, no_above=no_above)
    _BOW = build_bow_corpus(_TOKEN_LISTS, _DICTIONARY)
    _PASSES, _ITERATIONS, _ALPHA, _ETA, _LABEL = passes, iterations, alpha, eta, label


def _run_one(args):
    k, seed = args
    model = fit_lda(_BOW, _DICTIONARY, k=k, seed=seed, passes=_PASSES, iterations=_ITERATIONS,
                     alpha=_ALPHA, eta=_ETA)
    coh = coherence_scores(model, _TOKEN_LISTS, _DICTIONARY, _BOW)
    div = topic_diversity(model)
    red = pairwise_redundancy(model)
    prev = prevalence_and_thin_topics(model, _BOW)
    mat = topic_word_matrix(model)

    model_path = MODELS_DIR / _LABEL / f"k{k:02d}_seed{seed:02d}.model"
    model_path.parent.mkdir(parents=True, exist_ok=True)
    model.save(str(model_path))

    row = {
        "k": k, "seed": seed,
        "c_v": coh["c_v"], "c_npmi": coh["c_npmi"], "c_umass": coh["c_umass"],
        "topic_diversity": div,
        "mean_top20_jaccard": red["mean_top20_jaccard"],
        "mean_cosine_redundancy": red["mean_cosine"],
        "mean_js_distance_redundancy": red["mean_js_distance"],
        "n_topics_0_studies": prev["n_topics_0_studies"],
        "n_topics_1_study": prev["n_topics_1_study"],
        "n_topics_lt3_studies": prev["n_topics_lt3_studies"],
        "n_topics_lt5_studies": prev["n_topics_lt5_studies"],
        "margin_mean": prev["margin_mean"],
        "prop_conf_lt_0.40": prev["prop_conf_lt_0.40"],
        "prop_conf_0.40_0.60": prev["prop_conf_0.40_0.60"],
        "prop_conf_gt_0.60": prev["prop_conf_gt_0.60"],
        "model_path": str(model_path.relative_to(ROOT)),
    }
    mat_path = MODELS_DIR / _LABEL / f"k{k:02d}_seed{seed:02d}_topicword.npy"
    np.save(mat_path, mat)
    return row


def run_for_representation(label, no_below, no_above, passes, iterations, alpha="auto", eta="auto",
                            k_range=None, seeds=None, max_workers=12):
    k_range = k_range or K_RANGE
    seeds = seeds or SEEDS
    t0 = time.time()
    tasks = [(k, s) for k in k_range for s in seeds]
    rows = []
    with ProcessPoolExecutor(max_workers=max_workers, initializer=_init_worker,
                              initargs=(label, no_below, no_above, passes, iterations, alpha, eta)) as ex:
        futs = {ex.submit(_run_one, t): t for t in tasks}
        done = 0
        for fut in as_completed(futs):
            rows.append(fut.result())
            done += 1
            if done % 20 == 0:
                print(f"[{label}] {done}/{len(tasks)} models done ({time.time()-t0:.0f}s)")
    df = pd.DataFrame(rows).sort_values(["k", "seed"])
    out_dir = RESULTS_DIR / label
    out_dir.mkdir(parents=True, exist_ok=True)
    df.to_csv(out_dir / "definitive_ksweep_runs.csv", index=False)
    print(f"[{label}] DEFINITIVE SWEEP DONE: {len(df)} models in {time.time()-t0:.0f}s")
    return df


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("label")
    ap.add_argument("no_below", type=int)
    ap.add_argument("no_above", type=float)
    ap.add_argument("passes", type=int)
    ap.add_argument("iterations", type=int)
    ap.add_argument("--alpha", default="auto")
    ap.add_argument("--eta", default="auto")
    ap.add_argument("--kmax", type=int, default=20)
    args = ap.parse_args()
    run_for_representation(args.label, args.no_below, args.no_above, args.passes, args.iterations,
                            args.alpha, args.eta, k_range=list(range(2, args.kmax + 1)))
