"""Section 15 Stage 2: training/convergence pilot + prior (alpha/eta) pilot, run at the frozen
Stage-1 preprocessing configuration for each representation. Two staged 1-D sweeps (not a full
factorial) per the source protocol's own "staged design" instruction:
  (a) fixed iterations=400, vary passes in {10,20,30,40}
  (b) fixed passes=20 (or the convergence-pilot winner), vary iterations in {200,400,800}
followed by a small alpha x eta grid at the winning budget.
Convergence is assessed as the mean aligned (Hungarian, JS-similarity) topic-word agreement
between same-seed models at adjacent budget levels; the frozen budget is the smallest at which
further increases change mean agreement by < 0.02.
"""
import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parent))
from lda_core import (align_topics_hungarian, build_bow_corpus, build_dictionary, fit_lda,
                        js_similarity, topic_word_matrix)

ROOT = Path(__file__).resolve().parents[1]
PREP_DIR = ROOT / "preprocessing"
RESULTS_DIR = ROOT / "results"

PILOT_K = [5, 10, 15]
PILOT_SEEDS = [0, 1, 2, 3, 4]

PASSES_GRID = [10, 20, 30, 40]
ITER_GRID = [200, 400, 800]
ALPHA_GRID = ["auto", "symmetric", "asymmetric"]
ETA_GRID = ["auto", "symmetric"]


def load_tokens(label):
    with open(PREP_DIR / label / "lemmatized_tokens_corrected.json", encoding="utf-8") as f:
        d = json.load(f)
    return list(d.values())


def fit_grid(token_lists, dictionary, bow, budgets: list[tuple[int, int]]):
    """budgets: list of (passes, iterations). Returns dict[(passes,iter,k,seed)] -> topic matrix,
    and a dataframe of per-budget mean self-consistency across seeds."""
    mats = {}
    for passes, iters in budgets:
        for k in PILOT_K:
            for seed in PILOT_SEEDS:
                m = fit_lda(bow, dictionary, k=k, seed=seed, passes=passes, iterations=iters)
                mats[(passes, iters, k, seed)] = topic_word_matrix(m)
    return mats


def adjacent_agreement(mats, ordered_budgets):
    rows = []
    for i in range(1, len(ordered_budgets)):
        b_prev, b_cur = ordered_budgets[i - 1], ordered_budgets[i]
        sims = []
        for k in PILOT_K:
            for seed in PILOT_SEEDS:
                ma = mats[(*b_prev, k, seed)]
                mb = mats[(*b_cur, k, seed)]
                row_ind, col_ind = align_topics_hungarian(ma, mb)
                pair_sims = [js_similarity(ma[r], mb[c]) for r, c in zip(row_ind, col_ind)]
                sims.append(np.mean(pair_sims))
        rows.append({
            "budget_prev": b_prev, "budget_cur": b_cur,
            "mean_agreement": float(np.mean(sims)),
        })
    return pd.DataFrame(rows)


def run_for_representation(label: str, no_below: int, no_above: float):
    token_lists = load_tokens(label)
    dictionary = build_dictionary(token_lists, no_below=no_below, no_above=no_above)
    bow = build_bow_corpus(token_lists, dictionary)

    # (a) passes sweep at fixed iterations=400
    passes_budgets = [(p, 400) for p in PASSES_GRID]
    mats_p = fit_grid(token_lists, dictionary, bow, passes_budgets)
    agree_p = adjacent_agreement(mats_p, passes_budgets)
    agree_p["sweep"] = "passes"

    # (b) iterations sweep at fixed passes=20
    iter_budgets = [(20, it) for it in ITER_GRID]
    mats_i = fit_grid(token_lists, dictionary, bow, iter_budgets)
    agree_i = adjacent_agreement(mats_i, iter_budgets)
    agree_i["sweep"] = "iterations"

    convergence_df = pd.concat([agree_p, agree_i], ignore_index=True)

    # frozen budget: smallest passes/iterations combo at/after agreement stabilizes (<0.02 delta)
    frozen_passes = PASSES_GRID[-1]
    for i, r in agree_p.iterrows():
        if r["mean_agreement"] >= (agree_p["mean_agreement"].iloc[-1] - 0.02):
            frozen_passes = r["budget_cur"][0]
            break
    frozen_iters = ITER_GRID[-1]
    for i, r in agree_i.iterrows():
        if r["mean_agreement"] >= (agree_i["mean_agreement"].iloc[-1] - 0.02):
            frozen_iters = r["budget_cur"][1]
            break

    # alpha/eta pilot at frozen budget
    prior_rows = []
    prior_mats = {}
    for alpha in ALPHA_GRID:
        for eta in ETA_GRID:
            for k in PILOT_K:
                seed_mats = []
                for seed in PILOT_SEEDS:
                    m = fit_lda(bow, dictionary, k=k, seed=seed, passes=frozen_passes,
                                iterations=frozen_iters, alpha=alpha, eta=eta)
                    seed_mats.append(topic_word_matrix(m))
                sims = []
                for i in range(len(seed_mats)):
                    for j in range(i + 1, len(seed_mats)):
                        row_ind, col_ind = align_topics_hungarian(seed_mats[i], seed_mats[j])
                        pair_sims = [js_similarity(seed_mats[i][r], seed_mats[j][c])
                                     for r, c in zip(row_ind, col_ind)]
                        sims.append(np.mean(pair_sims))
                prior_rows.append({
                    "alpha": alpha, "eta": eta, "k": k,
                    "mean_seed_stability": float(np.mean(sims)) if sims else float("nan"),
                })
    prior_df = pd.DataFrame(prior_rows)

    out_dir = RESULTS_DIR / label
    out_dir.mkdir(parents=True, exist_ok=True)
    convergence_df.to_csv(out_dir / "stage2_convergence_pilot.csv", index=False)
    prior_df.to_csv(out_dir / "stage2_prior_pilot.csv", index=False)

    frozen = {
        "representation": label, "no_below": no_below, "no_above": no_above,
        "frozen_passes": int(frozen_passes), "frozen_iterations": int(frozen_iters),
        "frozen_alpha": "auto", "frozen_eta": "auto",
    }
    prior_agg = prior_df.groupby(["alpha", "eta"])["mean_seed_stability"].mean().reset_index()
    best_prior = prior_agg.sort_values("mean_seed_stability", ascending=False).iloc[0]
    if best_prior["mean_seed_stability"] >= prior_agg[
            (prior_agg.alpha == "auto") & (prior_agg.eta == "auto")]["mean_seed_stability"].iloc[0] + 0.02:
        frozen["frozen_alpha"] = best_prior["alpha"]
        frozen["frozen_eta"] = best_prior["eta"]

    with open(out_dir / "stage2_frozen_training_config.json", "w", encoding="utf-8") as f:
        json.dump(frozen, f, indent=2)
    print(f"[{label}] frozen training config: {frozen}")
    return frozen


if __name__ == "__main__":
    # placeholder defaults; real invocation passes the Stage-1-selected no_below/no_above
    import argparse
    ap = argparse.ArgumentParser()
    ap.add_argument("label")
    ap.add_argument("no_below", type=int)
    ap.add_argument("no_above", type=float)
    args = ap.parse_args()
    run_for_representation(args.label, args.no_below, args.no_above)
