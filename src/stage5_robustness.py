"""
STAGE 5 -- Robustness, finalists only (PRE_EXECUTION_ANALYSIS_PLAN.md SS13).

For each finalist k (from Stage 4):
  1. Subsampling: 80% of studies, no replacement, 100 repetitions. Every
     repetition's LdaModel uses the finalist's OWN structural-medoid seed as
     random_state (isolates document-removal sensitivity from
     initialization variance); the 100 sampling seeds (which 80% is drawn)
     are the fixed integers 1..100 via numpy.random.default_rng. Metrics:
     aligned JS similarity, ARI, NMI (dominant-topic assignments on the
     overlapping documents, full-corpus medoid model vs each subsample
     refit, Hungarian-aligned first), prevalence/size/entropy variability,
     thin-topic emergence frequency.
  2. Training-effort sensitivity: frozen budget vs passes=100/iterations=2000,
     same medoid seed and dictionary.
  3. Dictionary sensitivity: refit at each immediately-neighbouring
     (no_below +/-1, no_above +/-1-step) threshold from the Stage-1 grid.

(Full text only) Length sensitivity is in stage5_length_sensitivity.py
(separate script, mandatory, plan SS13).

gensim.models.LdaModel only (single-threaded).
"""

from __future__ import annotations

import csv
import sys
import time
from pathlib import Path

import numpy as np
from gensim.corpora import Dictionary
from sklearn.metrics import adjusted_rand_score, normalized_mutual_info_score
from scipy.optimize import linear_sum_assignment
from scipy.spatial.distance import jensenshannon

sys.path.insert(0, str(Path(__file__).parent))
from preprocessing import preprocess_variant, get_plural_merge_map
from lda_utils import fit_lda, topic_word_matrix
from stage1_select import load_sweep, decide_variant, NO_BELOW_GRID, NO_ABOVE_GRID
from stage1_sweep import load_metadata_texts, load_fulltext_texts
from stage2_select import select_convergence, select_priors
from stage4_select import load_k_summary, pareto_optimal_set, reduce_to_finalists

ROOT = Path(__file__).resolve().parents[1]
N_SUBSAMPLE_REPS = 100
SUBSAMPLE_FRACTION = 0.8


def get_representation_context(representation: str):
    rows = load_sweep(representation)
    d1 = decide_variant(representation, rows)
    fc = d1["final_config"]
    priors = select_priors(representation)
    conv = select_convergence(representation)

    if representation == "metadata":
        ids, texts = load_metadata_texts()
    else:
        ids, texts = load_fulltext_texts()

    plural_map = get_plural_merge_map(texts)
    tokens = preprocess_variant(texts, d1["chosen_hf"], d1["use_bigrams"], plural_map)
    dictionary = Dictionary(tokens)
    dictionary.filter_extremes(no_below=fc["no_below"], no_above=fc["no_above"])
    corpus = [dictionary.doc2bow(t) for t in tokens]

    return {
        "ids": ids, "tokens": tokens, "dictionary": dictionary, "corpus": corpus,
        "hf": d1["chosen_hf"], "bigrams": d1["use_bigrams"],
        "no_below": fc["no_below"], "no_above": fc["no_above"],
        "alpha": priors["alpha"], "eta": priors["eta"],
        "passes": conv["passes"], "iterations": conv["iterations"],
        "texts_raw": texts,
    }


def project_to_shared_vocab(mat_a, dict_a, mat_b, dict_b):
    """Two topic-word matrices whose dictionaries differ (e.g. neighbouring
    dictionary-sensitivity thresholds) can't be compared element-wise --
    project both onto the union of their vocabularies (zero-fill for a
    word absent from one dictionary; each topic's probability mass, which
    already summed to ~1 over its own vocabulary, is preserved exactly by
    this zero-fill, so no renormalization is needed)."""
    shared_tokens = sorted(set(dict_a.token2id) | set(dict_b.token2id))
    idx = {tok: i for i, tok in enumerate(shared_tokens)}
    v = len(shared_tokens)

    def project(mat, dictionary):
        out = np.zeros((mat.shape[0], v))
        for local_id, tok in dictionary.id2token.items():
            out[:, idx[tok]] = mat[:, local_id]
        return out

    return project(mat_a, dict_a), project(mat_b, dict_b)


def aligned_metrics(mat_a, mat_b, dom_a, dom_b, ids_overlap_idx_a, ids_overlap_idx_b,
                     dict_a=None, dict_b=None):
    """Hungarian-align topics of A onto B; return (mean JS similarity,
    ARI, NMI) of dominant-topic labels on the given overlapping document
    index sets (already remapped through the alignment). If dict_a/dict_b
    are given and differ, both matrices are first projected onto their
    shared vocabulary (see project_to_shared_vocab)."""
    if dict_a is not None and dict_b is not None and mat_a.shape[1] != mat_b.shape[1]:
        mat_a, mat_b = project_to_shared_vocab(mat_a, dict_a, mat_b, dict_b)
    ka, kb = mat_a.shape[0], mat_b.shape[0]
    cost = np.array([[jensenshannon(mat_a[i], mat_b[j], base=2) for j in range(kb)] for i in range(ka)])
    cost = np.nan_to_num(cost, nan=0.0)
    row_ind, col_ind = linear_sum_assignment(cost)
    js_sim = float((1 - cost[row_ind, col_ind]).mean())
    a_to_b = dict(zip(row_ind, col_ind))

    labels_a = [a_to_b.get(dom_a[i], -1) for i in ids_overlap_idx_a]
    labels_b = [dom_b[i] for i in ids_overlap_idx_b]
    ari = adjusted_rand_score(labels_b, labels_a)
    nmi = normalized_mutual_info_score(labels_b, labels_a)
    return js_sim, ari, nmi


def dominant_topics_and_matrix(corpus, dictionary, k, seed, passes, iterations, alpha, eta):
    model = fit_lda(corpus, dictionary, num_topics=k, seed=seed, passes=passes,
                     iterations=iterations, alpha=alpha, eta=eta)
    mat = topic_word_matrix(model)
    dom = []
    for bow in corpus:
        dist = model.get_document_topics(bow, minimum_probability=0.0)
        dom.append(max(dist, key=lambda x: x[1])[0])
    return mat, np.array(dom)


def run_subsampling(representation: str, ctx: dict, k: int, medoid_seed: int) -> None:
    out_csv = ROOT / "results" / representation / f"subsampling_k{k}.csv"
    seeds_csv = ROOT / "results" / representation / f"subsampling_seeds_k{k}.csv"
    n = len(ctx["corpus"])

    full_mat, full_dom = dominant_topics_and_matrix(
        ctx["corpus"], ctx["dictionary"], k, medoid_seed,
        ctx["passes"], ctx["iterations"], ctx["alpha"], ctx["eta"])
    full_counts = np.array([int((full_dom == t).sum()) for t in range(k)])
    p_full = full_counts / full_counts.sum()
    with np.errstate(divide="ignore", invalid="ignore"):
        full_entropy = -np.sum(np.where(p_full > 0, p_full * np.log(p_full), 0.0)) / np.log(k)

    done = set()
    write_header = not out_csv.exists()
    if out_csv.exists():
        with open(out_csv, newline="", encoding="utf-8") as f:
            done = {int(r["rep"]) for r in csv.DictReader(f)}

    fieldnames = ["representation", "k", "rep", "sampling_seed", "n_sampled",
                  "js_similarity", "ari", "nmi", "thin_topics_lt5", "zero_topics",
                  "normalized_entropy", "entropy_delta", "wall_seconds"]
    with open(out_csv, "a", newline="", encoding="utf-8") as f, \
         open(seeds_csv, "a", newline="", encoding="utf-8") as sf:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        if write_header:
            writer.writeheader()
            sf.write("rep,sampling_seed,sampled_indices\n")

        for rep in range(1, N_SUBSAMPLE_REPS + 1):
            if rep in done:
                continue
            t0 = time.time()
            rng = np.random.default_rng(rep)
            sample_idx = np.sort(rng.choice(n, size=int(round(n * SUBSAMPLE_FRACTION)), replace=False))
            sub_corpus = [ctx["corpus"][i] for i in sample_idx]

            sub_mat, sub_dom_local = dominant_topics_and_matrix(
                sub_corpus, ctx["dictionary"], k, medoid_seed,
                ctx["passes"], ctx["iterations"], ctx["alpha"], ctx["eta"])

            js_sim, ari, nmi = aligned_metrics(
                full_mat, sub_mat, full_dom, sub_dom_local,
                ids_overlap_idx_a=sample_idx, ids_overlap_idx_b=np.arange(len(sample_idx)))

            sub_counts = np.array([int((sub_dom_local == t).sum()) for t in range(k)])
            thin = int((sub_counts < 5).sum())
            zero = int((sub_counts == 0).sum())
            p_sub = sub_counts / sub_counts.sum() if sub_counts.sum() > 0 else sub_counts.astype(float)
            with np.errstate(divide="ignore", invalid="ignore"):
                sub_entropy = -np.sum(np.where(p_sub > 0, p_sub * np.log(p_sub), 0.0)) / np.log(k)

            writer.writerow({
                "representation": representation, "k": k, "rep": rep, "sampling_seed": rep,
                "n_sampled": len(sample_idx), "js_similarity": round(js_sim, 5),
                "ari": round(ari, 5), "nmi": round(nmi, 5),
                "thin_topics_lt5": thin, "zero_topics": zero,
                "normalized_entropy": round(float(sub_entropy), 5),
                "entropy_delta": round(float(sub_entropy - full_entropy), 5),
                "wall_seconds": round(time.time() - t0, 1),
            })
            f.flush()
            sf.write(f"{rep},{rep},\"{sample_idx.tolist()}\"\n")
            sf.flush()
            if rep % 10 == 0:
                print(f"[{representation}] k={k} subsampling {rep}/{N_SUBSAMPLE_REPS} "
                      f"js={js_sim:.3f} ari={ari:.3f} nmi={nmi:.3f} ({time.time()-t0:.1f}s)")


def run_training_effort_sensitivity(representation: str, ctx: dict, k: int, medoid_seed: int) -> dict:
    baseline_mat, baseline_dom = dominant_topics_and_matrix(
        ctx["corpus"], ctx["dictionary"], k, medoid_seed,
        ctx["passes"], ctx["iterations"], ctx["alpha"], ctx["eta"])
    enhanced_mat, enhanced_dom = dominant_topics_and_matrix(
        ctx["corpus"], ctx["dictionary"], k, medoid_seed, 100, 2000, ctx["alpha"], ctx["eta"])
    js_sim, ari, nmi = aligned_metrics(
        baseline_mat, enhanced_mat, baseline_dom, enhanced_dom,
        ids_overlap_idx_a=np.arange(len(ctx["corpus"])), ids_overlap_idx_b=np.arange(len(ctx["corpus"])))
    return {"k": k, "js_similarity": round(js_sim, 5), "dominant_topic_agreement_ari": round(ari, 5),
            "dominant_topic_agreement_nmi": round(nmi, 5)}


def run_dictionary_sensitivity(representation: str, ctx: dict, k: int, medoid_seed: int) -> list[dict]:
    base_mat, base_dom = dominant_topics_and_matrix(
        ctx["corpus"], ctx["dictionary"], k, medoid_seed,
        ctx["passes"], ctx["iterations"], ctx["alpha"], ctx["eta"])

    nb_idx = NO_BELOW_GRID.index(ctx["no_below"])
    na_idx = NO_ABOVE_GRID.index(ctx["no_above"])
    neighbours = []
    if nb_idx > 0:
        neighbours.append((NO_BELOW_GRID[nb_idx - 1], ctx["no_above"]))
    if nb_idx < len(NO_BELOW_GRID) - 1:
        neighbours.append((NO_BELOW_GRID[nb_idx + 1], ctx["no_above"]))
    if na_idx > 0:
        neighbours.append((ctx["no_below"], NO_ABOVE_GRID[na_idx - 1]))
    if na_idx < len(NO_ABOVE_GRID) - 1:
        neighbours.append((ctx["no_below"], NO_ABOVE_GRID[na_idx + 1]))

    results = []
    for nb, na in neighbours:
        d2 = Dictionary(ctx["tokens"])
        d2.filter_extremes(no_below=nb, no_above=na)
        c2 = [d2.doc2bow(t) for t in ctx["tokens"]]
        mat2, dom2 = dominant_topics_and_matrix(
            c2, d2, k, medoid_seed, ctx["passes"], ctx["iterations"], ctx["alpha"], ctx["eta"])
        js_sim, ari, nmi = aligned_metrics(
            base_mat, mat2, base_dom, dom2,
            ids_overlap_idx_a=np.arange(len(ctx["corpus"])), ids_overlap_idx_b=np.arange(len(ctx["corpus"])),
            dict_a=ctx["dictionary"], dict_b=d2)
        counts2 = np.array([int((dom2 == t).sum()) for t in range(k)])
        results.append({
            "k": k, "no_below": nb, "no_above": na, "vocab_size": len(d2),
            "js_similarity": round(js_sim, 5), "dominant_topic_agreement_ari": round(ari, 5),
            "dominant_topic_agreement_nmi": round(nmi, 5),
            "topic_size_distribution": str(counts2.tolist()),
        })
    return results


def main():
    reps = sys.argv[1:] or ["metadata", "fulltext"]
    for representation in reps:
        k_rows = load_k_summary(representation)
        pareto = pareto_optimal_set(k_rows)
        finalists = reduce_to_finalists(pareto)
        ctx = get_representation_context(representation)

        te_results, dict_results = [], []
        for r in finalists:
            k, medoid_seed = r["k"], int(r["medoid_seed"])
            print(f"[{representation}] Stage 5: k={k} medoid_seed={medoid_seed}")

            run_subsampling(representation, ctx, k, medoid_seed)

            te = run_training_effort_sensitivity(representation, ctx, k, medoid_seed)
            te_results.append(te)
            print(f"[{representation}] k={k} training-effort sensitivity: {te}")

            dict_res = run_dictionary_sensitivity(representation, ctx, k, medoid_seed)
            dict_results.extend(dict_res)
            print(f"[{representation}] k={k} dictionary sensitivity: {len(dict_res)} neighbours checked")

        out_te = ROOT / "results" / representation / "training_effort_sensitivity.csv"
        with open(out_te, "w", newline="", encoding="utf-8") as f:
            w = csv.DictWriter(f, fieldnames=["k", "js_similarity", "dominant_topic_agreement_ari",
                                                "dominant_topic_agreement_nmi"])
            w.writeheader()
            for row in te_results:
                w.writerow(row)

        out_dict = ROOT / "results" / representation / "dictionary_sensitivity.csv"
        with open(out_dict, "w", newline="", encoding="utf-8") as f:
            w = csv.DictWriter(f, fieldnames=["k", "no_below", "no_above", "vocab_size",
                                                "js_similarity", "dominant_topic_agreement_ari",
                                                "dominant_topic_agreement_nmi", "topic_size_distribution"])
            w.writeheader()
            for row in dict_results:
                w.writerow(row)

        print(f"[{representation}] STAGE 5 (subsampling + training-effort + dictionary sensitivity) DONE")


if __name__ == "__main__":
    main()
