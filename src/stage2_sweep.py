"""
STAGE 2 -- Priors and convergence (PRE_EXECUTION_ANALYSIS_PLAN.md SS10).

Requires Stage 1 to be complete (reads results/{representation}/stage1_decision.md
-- actually re-derives the same frozen dictionary/preprocessing config
programmatically via stage1_select.py rather than parsing markdown).

At the frozen Stage-1 dictionary/preprocessing config, pilot k-set {5,10,15}
x 5 pilot seeds [42,101,202,303,404]:

  - Prior grid: alpha in {auto, symmetric, 0.05, 0.10, 0.25, 0.50, 1.00} x
    eta in {auto, symmetric} = 14 combos. Fixed training budget while sweeping
    priors: passes=20, iterations=400 (Stage-1 pilot budget; the convergence
    grid below determines the FINAL budget separately, applied only after
    both pilots are frozen, per plan SS10).
  - Convergence grid: passes in {10,20,30,50} x iterations in {200,400,800,1200}
    = 16 combos, at fixed priors alpha=eta='auto' (Stage-1 pilot default).
    Consecutive combos (ordered by passes*iterations) compared via
    Hungarian-aligned JS similarity + dominant-topic agreement, same seed
    and same dictionary, averaged over pilot k-set x 5 seeds.

gensim.models.LdaModel only (single-threaded). Writes incrementally to
results/{representation}/{prior_sweep,convergence_sweep}.csv.
"""

from __future__ import annotations

import csv
import sys
import time
from itertools import product
from pathlib import Path

import numpy as np
from gensim.corpora import Dictionary

sys.path.insert(0, str(Path(__file__).parent))
from preprocessing import preprocess_variant, get_plural_merge_map
from lda_utils import (
    fit_lda, coherence, topic_word_matrix, mean_pairwise_stability, top_n_diversity,
    hungarian_align_js_similarity,
)
from stage1_select import load_sweep, decide_variant
from stage1_sweep import load_metadata_texts, load_fulltext_texts, PILOT_K_SET, PILOT_SEEDS

PRIOR_ALPHAS = ["auto", "symmetric", 0.05, 0.10, 0.25, 0.50, 1.00]
PRIOR_ETAS = ["auto", "symmetric"]
CONVERGENCE_GRID = [(p, i) for p in (10, 20, 30, 50) for i in (200, 400, 800, 1200)]
CONVERGENCE_GRID.sort(key=lambda pi: pi[0] * pi[1])

PILOT_ALPHA_DEFAULT = "auto"
PILOT_ETA_DEFAULT = "auto"
PILOT_PASSES = 20
PILOT_ITERATIONS = 400

ROOT = Path(__file__).resolve().parents[1]


def get_frozen_stage1_tokens_and_dict(representation: str):
    rows = load_sweep(representation)
    decision = decide_variant(representation, rows)
    fc = decision["final_config"]
    hf, bigrams = decision["chosen_hf"], decision["use_bigrams"]

    if representation == "metadata":
        ids, texts = load_metadata_texts()
    else:
        ids, texts = load_fulltext_texts()

    plural_map = get_plural_merge_map(texts)
    tokens = preprocess_variant(texts, hf, bigrams, plural_map)
    dictionary = Dictionary(tokens)
    dictionary.filter_extremes(no_below=fc["no_below"], no_above=fc["no_above"])
    corpus = [dictionary.doc2bow(t) for t in tokens]
    return tokens, dictionary, corpus, decision


def dominant_topics(model, corpus) -> list[int]:
    out = []
    for bow in corpus:
        dist = model.get_document_topics(bow, minimum_probability=0.0)
        out.append(max(dist, key=lambda x: x[1])[0])
    return out


def aligned_dominant_topic_agreement(mat_a, mat_b, doms_a, doms_b) -> float:
    """Hungarian-align topics of A onto B, remap A's dominant-topic labels,
    then compute the fraction of documents where the remapped dominant topic
    matches B's dominant topic."""
    from scipy.optimize import linear_sum_assignment
    from scipy.spatial.distance import jensenshannon

    k = mat_a.shape[0]
    cost = np.array([[jensenshannon(mat_a[i], mat_b[j], base=2) for j in range(k)] for i in range(k)])
    cost = np.nan_to_num(cost, nan=0.0)
    row_ind, col_ind = linear_sum_assignment(cost)
    a_to_b = dict(zip(row_ind, col_ind))
    remapped_a = [a_to_b[d] for d in doms_a]
    agree = sum(1 for x, y in zip(remapped_a, doms_b) if x == y)
    return agree / len(doms_b)


def run_prior_sweep(representation, tokens, dictionary, corpus):
    out_csv = ROOT / "results" / representation / "prior_sweep.csv"
    fieldnames = ["representation", "alpha", "eta", "mean_cv", "sd_cv", "mean_cnpmi", "sd_cnpmi",
                  "mean_diversity", "mean_stability", "sd_stability", "n_fits", "wall_seconds"]
    done = set()
    write_header = not out_csv.exists()
    if out_csv.exists():
        with open(out_csv, newline="", encoding="utf-8") as f:
            done = {(r["alpha"], r["eta"]) for r in csv.DictReader(f)}
        print(f"[{representation}] prior sweep resuming: {len(done)} done")

    with open(out_csv, "a", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        if write_header:
            writer.writeheader()
        for alpha, eta in product(PRIOR_ALPHAS, PRIOR_ETAS):
            if (str(alpha), str(eta)) in done:
                continue
            t0 = time.time()
            cv_all, cnpmi_all, stability_per_k, diversity_per_k = [], [], [], []
            for k in PILOT_K_SET:
                matrices = []
                for seed in PILOT_SEEDS:
                    model = fit_lda(corpus, dictionary, num_topics=k, seed=seed,
                                     passes=PILOT_PASSES, iterations=PILOT_ITERATIONS,
                                     alpha=alpha, eta=eta)
                    cv_all.append(coherence(model, tokens, dictionary, corpus, "c_v"))
                    cnpmi_all.append(coherence(model, tokens, dictionary, corpus, "c_npmi"))
                    matrices.append(topic_word_matrix(model))
                mean_stab, _ = mean_pairwise_stability(matrices)
                stability_per_k.append(mean_stab)
                diversity_per_k.append(top_n_diversity(matrices, top_n=25))
            row = {
                "representation": representation, "alpha": alpha, "eta": eta,
                "mean_cv": round(float(np.mean(cv_all)), 5), "sd_cv": round(float(np.std(cv_all, ddof=1)), 5),
                "mean_cnpmi": round(float(np.mean(cnpmi_all)), 5), "sd_cnpmi": round(float(np.std(cnpmi_all, ddof=1)), 5),
                "mean_diversity": round(float(np.mean(diversity_per_k)), 5),
                "mean_stability": round(float(np.mean(stability_per_k)), 5),
                "sd_stability": round(float(np.std(stability_per_k, ddof=1)), 5),
                "n_fits": len(PILOT_K_SET) * len(PILOT_SEEDS), "wall_seconds": round(time.time() - t0, 1),
            }
            writer.writerow(row)
            f.flush()
            print(f"[{representation}] prior alpha={alpha} eta={eta} -> mean_cv={row['mean_cv']} "
                  f"mean_stability={row['mean_stability']} ({row['wall_seconds']}s)")


def run_convergence_sweep(representation, tokens, dictionary, corpus):
    out_csv = ROOT / "results" / representation / "convergence_sweep.csv"
    fieldnames = ["representation", "passes", "iterations", "effort",
                  "mean_js_vs_next", "mean_dom_agreement_vs_next", "n_fits", "wall_seconds"]

    # Fit every grid cell once per (k, seed); cache matrices+dominant topics.
    fits: dict[tuple, dict] = {}
    for (passes, iterations) in CONVERGENCE_GRID:
        t0 = time.time()
        for k in PILOT_K_SET:
            for seed in PILOT_SEEDS:
                model = fit_lda(corpus, dictionary, num_topics=k, seed=seed,
                                 passes=passes, iterations=iterations,
                                 alpha=PILOT_ALPHA_DEFAULT, eta=PILOT_ETA_DEFAULT)
                fits[(passes, iterations, k, seed)] = {
                    "matrix": topic_word_matrix(model),
                    "dominant": dominant_topics(model, corpus),
                }
        print(f"[{representation}] convergence fits done for passes={passes} iterations={iterations} "
              f"({time.time()-t0:.1f}s)")

    done = set()
    write_header = not out_csv.exists()
    if out_csv.exists():
        with open(out_csv, newline="", encoding="utf-8") as f:
            done = {(r["passes"], r["iterations"]) for r in csv.DictReader(f)}

    with open(out_csv, "a", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        if write_header:
            writer.writeheader()
        for idx, (passes, iterations) in enumerate(CONVERGENCE_GRID):
            if (str(passes), str(iterations)) in done:
                continue
            t0 = time.time()
            if idx == len(CONVERGENCE_GRID) - 1:
                # largest cell: nothing larger to compare against
                row = {
                    "representation": representation, "passes": passes, "iterations": iterations,
                    "effort": passes * iterations, "mean_js_vs_next": None, "mean_dom_agreement_vs_next": None,
                    "n_fits": len(PILOT_K_SET) * len(PILOT_SEEDS), "wall_seconds": round(time.time() - t0, 1),
                }
            else:
                next_passes, next_iterations = CONVERGENCE_GRID[idx + 1]
                js_list, agree_list = [], []
                for k in PILOT_K_SET:
                    for seed in PILOT_SEEDS:
                        a = fits[(passes, iterations, k, seed)]
                        b = fits[(next_passes, next_iterations, k, seed)]
                        js_list.append(hungarian_align_js_similarity(a["matrix"], b["matrix"]))
                        agree_list.append(aligned_dominant_topic_agreement(
                            a["matrix"], b["matrix"], a["dominant"], b["dominant"]))
                row = {
                    "representation": representation, "passes": passes, "iterations": iterations,
                    "effort": passes * iterations,
                    "mean_js_vs_next": round(float(np.mean(js_list)), 5),
                    "mean_dom_agreement_vs_next": round(float(np.mean(agree_list)), 5),
                    "n_fits": len(PILOT_K_SET) * len(PILOT_SEEDS), "wall_seconds": round(time.time() - t0, 1),
                }
            writer.writerow(row)
            f.flush()
            print(f"[{representation}] convergence passes={passes} iterations={iterations} -> "
                  f"JS_vs_next={row['mean_js_vs_next']} dom_agree_vs_next={row['mean_dom_agreement_vs_next']}")


def main():
    reps = sys.argv[1:] or ["metadata", "fulltext"]
    for rep in reps:
        t0 = time.time()
        tokens, dictionary, corpus, decision = get_frozen_stage1_tokens_and_dict(rep)
        print(f"[{rep}] Stage 1 frozen config: HF-{decision['chosen_hf']} bigrams={decision['use_bigrams']} "
              f"no_below={decision['final_config']['no_below']} no_above={decision['final_config']['no_above']} "
              f"vocab={len(dictionary)}")
        run_prior_sweep(rep, tokens, dictionary, corpus)
        run_convergence_sweep(rep, tokens, dictionary, corpus)
        print(f"[{rep}] STAGE 2 DONE in {(time.time()-t0)/60:.1f} min")


if __name__ == "__main__":
    main()
