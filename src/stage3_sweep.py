"""
STAGE 3 -- Definitive k-sweep (PRE_EXECUTION_ANALYSIS_PLAN.md SS11), fully
frozen configuration from Stage 1 (dictionary/preprocessing) and Stage 2
(priors/training budget).

k = 2..20 (19 values, no skipping), 20 seeds per k (first 20 of the master
seed list), gensim.models.LdaModel only (single-threaded).

Per individual fit: C_v, C_NPMI coherence, topic-word matrix, document-topic
distribution. Per k, aggregated across the 20 seeds: cross-seed stability
(Hungarian-aligned JS, mean/SD over all 190 seed pairs), structural medoid
(plan SS19: the seed with highest mean aligned similarity to all others --
never the highest-coherence seed). All population/prevalence/diagnostic
metrics in SS15-17 computed on the medoid model.

Writes incrementally to results/{representation}/k_sweep_by_seed.csv
(individual fits) and results/{representation}/k_sweep_summary.csv
(per-k aggregates). No model-selection decision here -- that is Stage 4.
"""

from __future__ import annotations

import csv
import sys
import time
from pathlib import Path

import numpy as np
from gensim.corpora import Dictionary

sys.path.insert(0, str(Path(__file__).parent))
from preprocessing import preprocess_variant, get_plural_merge_map
from lda_utils import (
    fit_lda, coherence, topic_word_matrix, mean_pairwise_stability, top_n_diversity,
    structural_medoid_index,
)
from stage1_select import load_sweep, decide_variant
from stage1_sweep import load_metadata_texts, load_fulltext_texts
from stage2_select import select_convergence, select_priors

ROOT = Path(__file__).resolve().parents[1]

K_RANGE = list(range(2, 21))  # 2..20
MASTER_SEED_LIST = [
    42, 101, 202, 303, 404, 505, 606, 707, 808, 909,
    1010, 1111, 1212, 1313, 1414, 1515, 1616, 1717, 1818, 1919,
    2020, 2121, 2222, 2323, 2424, 2525, 2626, 2727, 2828, 2929,
]
DEFINITIVE_SEEDS = MASTER_SEED_LIST[:20]


def get_frozen_config(representation: str):
    rows = load_sweep(representation)
    d1 = decide_variant(representation, rows)
    fc = d1["final_config"]
    hf, bigrams = d1["chosen_hf"], d1["use_bigrams"]
    priors = select_priors(representation)
    conv = select_convergence(representation)

    if representation == "metadata":
        ids, texts = load_metadata_texts()
    else:
        ids, texts = load_fulltext_texts()

    plural_map = get_plural_merge_map(texts)
    tokens = preprocess_variant(texts, hf, bigrams, plural_map)
    dictionary = Dictionary(tokens)
    dictionary.filter_extremes(no_below=fc["no_below"], no_above=fc["no_above"])
    corpus = [dictionary.doc2bow(t) for t in tokens]

    config = {
        "hf": hf, "bigrams": bigrams, "no_below": fc["no_below"], "no_above": fc["no_above"],
        "alpha": priors["alpha"], "eta": priors["eta"],
        "passes": conv["passes"], "iterations": conv["iterations"],
    }
    return ids, tokens, dictionary, corpus, config


def doc_topic_matrix(model, corpus, k) -> np.ndarray:
    """n_docs x k matrix of topic probabilities."""
    n = len(corpus)
    mat = np.zeros((n, k))
    for i, bow in enumerate(corpus):
        for topic_id, prob in model.get_document_topics(bow, minimum_probability=0.0):
            mat[i, topic_id] = prob
    return mat


def run_k_sweep(representation: str, ids, tokens, dictionary, corpus, config):
    by_seed_csv = ROOT / "results" / representation / "k_sweep_by_seed.csv"
    summary_csv = ROOT / "results" / representation / "k_sweep_summary.csv"

    by_seed_fields = ["representation", "k", "seed", "cv", "cnpmi", "wall_seconds"]
    summary_fields = [
        "representation", "k", "mean_cv", "sd_cv", "mean_cnpmi", "sd_cnpmi",
        "mean_stability", "sd_stability", "mean_diversity",
        "medoid_seed_index", "medoid_seed",
        "redundancy_jaccard_mean", "redundancy_cosine_mean",
        "dominant_counts_json", "zero_dominance_topics", "topics_lt3", "topics_lt5",
        "min_dominant_count", "max_dominant_count",
        "prevalence_json", "mean_assignment_confidence",
        "prop_conf_lt40", "prop_conf_40_60", "prop_conf_gt60",
        "cv_dominant_counts", "normalized_entropy", "gini", "largest_topic_proportion",
        "smallest_topic_proportion", "max_min_ratio",
        "n_fits", "wall_seconds",
    ]

    # Resumption granularity is whole-k only: an individual fit's full
    # topic-word matrix isn't persisted to by_seed_csv (impractical size), so
    # partially-resuming a k would silently drop seeds from the aggregation.
    # A k is only ever skipped if it's already in k_sweep_summary.csv.
    write_header_bs = not by_seed_csv.exists()

    done_summary = set()
    write_header_sum = not summary_csv.exists()
    if summary_csv.exists():
        with open(summary_csv, newline="", encoding="utf-8") as f:
            done_summary = {r["k"] for r in csv.DictReader(f)}

    bs_file = open(by_seed_csv, "a", newline="", encoding="utf-8")
    bs_writer = csv.DictWriter(bs_file, fieldnames=by_seed_fields)
    if write_header_bs:
        bs_writer.writeheader()

    sum_file = open(summary_csv, "a", newline="", encoding="utf-8")
    sum_writer = csv.DictWriter(sum_file, fieldnames=summary_fields)
    if write_header_sum:
        sum_writer.writeheader()

    for k in K_RANGE:
        if str(k) in done_summary:
            continue
        t0 = time.time()
        matrices, doc_topics_list, cv_list, cnpmi_list = [], [], [], []
        for seed in DEFINITIVE_SEEDS:
            tf0 = time.time()
            model = fit_lda(corpus, dictionary, num_topics=k, seed=seed,
                             passes=config["passes"], iterations=config["iterations"],
                             alpha=config["alpha"], eta=config["eta"])
            cv = coherence(model, tokens, dictionary, corpus, "c_v")
            cnpmi = coherence(model, tokens, dictionary, corpus, "c_npmi")
            bs_writer.writerow({
                "representation": representation, "k": k, "seed": seed,
                "cv": round(cv, 5), "cnpmi": round(cnpmi, 5),
                "wall_seconds": round(time.time() - tf0, 1),
            })
            bs_file.flush()
            matrices.append(topic_word_matrix(model))
            doc_topics_list.append(doc_topic_matrix(model, corpus, k))
            cv_list.append(cv)
            cnpmi_list.append(cnpmi)

        # Cross-seed stability + structural medoid (over ALL 20 seeds' matrices)
        mean_stab, sd_stab = mean_pairwise_stability(matrices)
        medoid_idx = structural_medoid_index(matrices)
        medoid_seed = DEFINITIVE_SEEDS[medoid_idx]
        medoid_mat = matrices[medoid_idx]
        medoid_doc_topics = doc_topics_list[medoid_idx]
        diversity = top_n_diversity(matrices, top_n=25)

        # Redundancy on the medoid model: pairwise top-20 Jaccard + cosine
        top20_sets = [set(np.argsort(-row)[:20].tolist()) for row in medoid_mat]
        jacc_scores, cos_scores = [], []
        for i in range(k):
            for j in range(i + 1, k):
                inter = len(top20_sets[i] & top20_sets[j])
                union = len(top20_sets[i] | top20_sets[j])
                jacc_scores.append(inter / union if union else 0.0)
                a, b = medoid_mat[i], medoid_mat[j]
                cos_scores.append(float(np.dot(a, b) / (np.linalg.norm(a) * np.linalg.norm(b))))
        redund_jaccard = float(np.mean(jacc_scores)) if jacc_scores else 0.0
        redund_cosine = float(np.mean(cos_scores)) if cos_scores else 0.0

        # Dominant-topic counts + population diagnostics (medoid model)
        dominant = medoid_doc_topics.argmax(axis=1)
        counts = np.array([int((dominant == t).sum()) for t in range(k)])
        zero_dom = int((counts == 0).sum())
        topics_lt3 = int((counts < 3).sum())
        topics_lt5 = int((counts < 5).sum())

        # Probabilistic prevalence: mean topic probability across all docs
        prevalence = medoid_doc_topics.mean(axis=0)

        # Assignment confidence
        max_probs = medoid_doc_topics.max(axis=1)
        mean_conf = float(max_probs.mean())
        prop_lt40 = float((max_probs < 0.40).mean())
        prop_40_60 = float(((max_probs >= 0.40) & (max_probs <= 0.60)).mean())
        prop_gt60 = float((max_probs > 0.60).mean())

        # Balance diagnostics (plan SS16)
        p = counts / counts.sum() if counts.sum() > 0 else counts.astype(float)
        with np.errstate(divide="ignore", invalid="ignore"):
            entropy_terms = np.where(p > 0, p * np.log(p), 0.0)
        H = -entropy_terms.sum()
        H_norm = float(H / np.log(k)) if k > 1 else 0.0
        cv_counts = float(counts.std(ddof=1) / counts.mean()) if counts.mean() > 0 else float("nan")
        sorted_counts = np.sort(counts)
        n = len(counts)
        cum = np.cumsum(sorted_counts)
        gini = float((n + 1 - 2 * (cum.sum() / cum[-1])) / n) if cum[-1] > 0 else 0.0
        largest_prop = float(counts.max() / counts.sum()) if counts.sum() > 0 else 0.0
        smallest_prop = float(counts.min() / counts.sum()) if counts.sum() > 0 else 0.0
        max_min_ratio = float(counts.max() / counts.min()) if counts.min() > 0 else float("inf")

        row = {
            "representation": representation, "k": k,
            "mean_cv": round(float(np.mean(cv_list)), 5), "sd_cv": round(float(np.std(cv_list, ddof=1)), 5),
            "mean_cnpmi": round(float(np.mean(cnpmi_list)), 5), "sd_cnpmi": round(float(np.std(cnpmi_list, ddof=1)), 5),
            "mean_stability": round(mean_stab, 5), "sd_stability": round(sd_stab, 5),
            "mean_diversity": round(diversity, 5),
            "medoid_seed_index": medoid_idx, "medoid_seed": medoid_seed,
            "redundancy_jaccard_mean": round(redund_jaccard, 5), "redundancy_cosine_mean": round(redund_cosine, 5),
            "dominant_counts_json": str(counts.tolist()),
            "zero_dominance_topics": zero_dom, "topics_lt3": topics_lt3, "topics_lt5": topics_lt5,
            "min_dominant_count": int(counts.min()), "max_dominant_count": int(counts.max()),
            "prevalence_json": str([round(x, 5) for x in prevalence.tolist()]),
            "mean_assignment_confidence": round(mean_conf, 5),
            "prop_conf_lt40": round(prop_lt40, 5), "prop_conf_40_60": round(prop_40_60, 5),
            "prop_conf_gt60": round(prop_gt60, 5),
            "cv_dominant_counts": round(cv_counts, 5) if not np.isnan(cv_counts) else None,
            "normalized_entropy": round(H_norm, 5), "gini": round(gini, 5),
            "largest_topic_proportion": round(largest_prop, 5), "smallest_topic_proportion": round(smallest_prop, 5),
            "max_min_ratio": round(max_min_ratio, 5) if max_min_ratio != float("inf") else None,
            "n_fits": len(DEFINITIVE_SEEDS), "wall_seconds": round(time.time() - t0, 1),
        }
        sum_writer.writerow(row)
        sum_file.flush()
        print(f"[{representation}] k={k} DONE mean_cv={row['mean_cv']} mean_stability={row['mean_stability']} "
              f"zero_dom={zero_dom} thin<5={topics_lt5} entropy={row['normalized_entropy']} "
              f"({row['wall_seconds']:.0f}s)")

    bs_file.close()
    sum_file.close()


def main():
    reps = sys.argv[1:] or ["metadata", "fulltext"]
    for rep in reps:
        t0 = time.time()
        ids, tokens, dictionary, corpus, config = get_frozen_config(rep)
        print(f"[{rep}] FROZEN CONFIG: {config} vocab={len(dictionary)}")
        run_k_sweep(rep, ids, tokens, dictionary, corpus, config)
        print(f"[{rep}] STAGE 3 DONE in {(time.time()-t0)/60:.1f} min")


if __name__ == "__main__":
    main()
