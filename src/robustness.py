"""Section 17/23: robustness analyses on the final frozen model per representation.
- 80% document subsampling, 100 repetitions, same sampled studies used for every metric
  within a repetition (topic similarity, ARI, NMI) - never independently resampled per metric.
- Training-effort sensitivity (substantially increased passes/iterations vs frozen budget).
- Dictionary sensitivity (neighboring no_below/no_above).
"""
import argparse
import json
import random
import sys
import time
from concurrent.futures import ProcessPoolExecutor, as_completed
from pathlib import Path

import numpy as np
import pandas as pd
from sklearn.metrics import adjusted_rand_score, normalized_mutual_info_score

sys.path.insert(0, str(Path(__file__).resolve().parent))
from lda_core import (align_topics_hungarian, build_bow_corpus, build_dictionary, fit_lda,
                        js_similarity, project_pair_to_shared_vocab, topic_word_matrix)

ROOT = Path(__file__).resolve().parents[1]
PREP_DIR = ROOT / "preprocessing"
RESULTS_DIR = ROOT / "results"
MODELS_DIR = ROOT / "models"

N_SUBSAMPLE_REPS = 100
SUBSAMPLE_FRAC = 0.8

_FULL_STUDY_IDS = None
_FULL_TOKEN_LISTS = None
_NO_BELOW = None
_NO_ABOVE = None
_PASSES = None
_ITERATIONS = None
_K = None
_FULL_MODEL_MAT = None
_FULL_DOMINANT = None


def _init_subsample_worker(label, no_below, no_above, passes, iterations, k, full_model_path):
    global _FULL_STUDY_IDS, _FULL_TOKEN_LISTS, _NO_BELOW, _NO_ABOVE, _PASSES, _ITERATIONS, _K
    global _FULL_MODEL_MAT, _FULL_DOMINANT
    with open(PREP_DIR / label / "lemmatized_tokens_corrected.json", encoding="utf-8") as f:
        d = json.load(f)
    _FULL_STUDY_IDS = list(d.keys())
    _FULL_TOKEN_LISTS = [d[s] for s in _FULL_STUDY_IDS]
    _NO_BELOW, _NO_ABOVE, _PASSES, _ITERATIONS, _K = no_below, no_above, passes, iterations, k

    from gensim.models import LdaModel
    full_model = LdaModel.load(str(ROOT / full_model_path))
    _FULL_MODEL_MAT = full_model.get_topics()
    full_dict = build_dictionary(_FULL_TOKEN_LISTS, no_below, no_above)
    full_bow = build_bow_corpus(_FULL_TOKEN_LISTS, full_dict)
    dom = []
    for bow in full_bow:
        td = full_model.get_document_topics(bow, minimum_probability=0.0)
        dom.append(max(td, key=lambda x: x[1])[0])
    _FULL_DOMINANT = np.array(dom)


def _run_subsample_rep(args):
    rep_idx, seed = args
    rng = random.Random(seed)
    n = len(_FULL_STUDY_IDS)
    n_sample = int(round(SUBSAMPLE_FRAC * n))
    idx = sorted(rng.sample(range(n), n_sample))
    sub_study_ids = [_FULL_STUDY_IDS[i] for i in idx]
    sub_tokens = [_FULL_TOKEN_LISTS[i] for i in idx]

    dictionary = build_dictionary(sub_tokens, _NO_BELOW, _NO_ABOVE)
    bow = build_bow_corpus(sub_tokens, dictionary)
    model = fit_lda(bow, dictionary, k=_K, seed=1000 + seed, passes=_PASSES, iterations=_ITERATIONS)
    sub_mat = topic_word_matrix(model)

    # align subsample topics to full-corpus topics via SHARED dictionary re-projection
    full_dict = build_dictionary(_FULL_TOKEN_LISTS, _NO_BELOW, _NO_ABOVE)
    shared_vocab = {tok: tid for tid, tok in full_dict.items()}
    mapped_sub = np.zeros((_K, len(shared_vocab)))
    for local_id, tok in dictionary.items():
        if tok in shared_vocab:
            mapped_sub[:, shared_vocab[tok]] = sub_mat[:, local_id]
    row_ind, col_ind = align_topics_hungarian(mapped_sub, _FULL_MODEL_MAT)
    sims = [js_similarity(mapped_sub[r], _FULL_MODEL_MAT[c]) for r, c in zip(row_ind, col_ind)]
    topic_similarity = float(np.mean(sims))

    # SAME sampled studies used for ARI/NMI: full-corpus dominant-topic labels restricted
    # to the sampled studies, vs subsample-model dominant-topic labels (remapped via the
    # Hungarian alignment so topic IDs are comparable).
    remap = {int(r): int(c) for r, c in zip(row_ind, col_ind)}
    sub_dominant_raw = []
    for bow_doc in bow:
        td = model.get_document_topics(bow_doc, minimum_probability=0.0)
        sub_dominant_raw.append(max(td, key=lambda x: x[1])[0])
    sub_dominant_mapped = [remap.get(int(t), int(t)) for t in sub_dominant_raw]
    full_dominant_restricted = _FULL_DOMINANT[idx]

    ari = adjusted_rand_score(full_dominant_restricted, sub_dominant_mapped)
    nmi = normalized_mutual_info_score(full_dominant_restricted, sub_dominant_mapped)

    return {
        "rep": rep_idx, "seed": seed, "n_sampled": n_sample,
        "sampled_study_ids": ";".join(sub_study_ids),
        "topic_similarity_js": topic_similarity, "ari": float(ari), "nmi": float(nmi),
    }


def subsampling_robustness(label, no_below, no_above, passes, iterations, k, full_model_path,
                            n_reps=N_SUBSAMPLE_REPS, max_workers=12):
    t0 = time.time()
    rows = []
    with ProcessPoolExecutor(max_workers=max_workers, initializer=_init_subsample_worker,
                              initargs=(label, no_below, no_above, passes, iterations, k, full_model_path)) as ex:
        futs = {ex.submit(_run_subsample_rep, (i, i)): i for i in range(n_reps)}
        done = 0
        for fut in as_completed(futs):
            rows.append(fut.result())
            done += 1
            if done % 20 == 0:
                print(f"[{label}] subsampling {done}/{n_reps} ({time.time()-t0:.0f}s)")
    df = pd.DataFrame(rows).sort_values("rep")
    out_dir = RESULTS_DIR / label
    out_dir.mkdir(parents=True, exist_ok=True)
    df.to_csv(out_dir / "subsampling_80pct_100reps.csv", index=False)

    summary = {}
    for col in ["topic_similarity_js", "ari", "nmi"]:
        vals = df[col].values
        summary[col] = {
            "mean": float(vals.mean()), "sd": float(vals.std()), "median": float(np.median(vals)),
            "ci95_low": float(np.percentile(vals, 2.5)), "ci95_high": float(np.percentile(vals, 97.5)),
        }
    with open(out_dir / "subsampling_80pct_summary.json", "w", encoding="utf-8") as f:
        json.dump(summary, f, indent=2)
    print(f"[{label}] subsampling DONE {n_reps} reps in {time.time()-t0:.0f}s: "
          f"JS={summary['topic_similarity_js']['mean']:.3f} ARI={summary['ari']['mean']:.3f}")
    return df, summary


def training_effort_sensitivity(label, no_below, no_above, k, base_passes, base_iterations,
                                 medoid_seed, boosted_passes=100, boosted_iterations=2000):
    with open(PREP_DIR / label / "lemmatized_tokens_corrected.json", encoding="utf-8") as f:
        d = json.load(f)
    token_lists = list(d.values())
    dictionary = build_dictionary(token_lists, no_below, no_above)
    bow = build_bow_corpus(token_lists, dictionary)

    m_base = fit_lda(bow, dictionary, k=k, seed=medoid_seed, passes=base_passes, iterations=base_iterations)
    m_boost = fit_lda(bow, dictionary, k=k, seed=medoid_seed, passes=boosted_passes, iterations=boosted_iterations)

    mat_base, mat_boost = topic_word_matrix(m_base), topic_word_matrix(m_boost)
    row_ind, col_ind = align_topics_hungarian(mat_base, mat_boost)
    js_sims = [js_similarity(mat_base[r], mat_boost[c]) for r, c in zip(row_ind, col_ind)]
    cos_sims = [float(np.dot(mat_base[r], mat_boost[c]) /
                       (np.linalg.norm(mat_base[r]) * np.linalg.norm(mat_boost[c]) + 1e-12))
                for r, c in zip(row_ind, col_ind)]

    from lda_core import doc_topic_matrix
    dom_base = doc_topic_matrix(m_base, bow).argmax(axis=1)
    dom_boost_raw = doc_topic_matrix(m_boost, bow).argmax(axis=1)
    remap = {int(c): int(r) for r, c in zip(row_ind, col_ind)}
    dom_boost = np.array([remap.get(int(t), int(t)) for t in dom_boost_raw])
    ari = adjusted_rand_score(dom_base, dom_boost)
    nmi = normalized_mutual_info_score(dom_base, dom_boost)
    dominant_agreement = float((dom_base == dom_boost).mean())

    result = {
        "representation": label, "k": k, "seed": medoid_seed,
        "base_budget": {"passes": base_passes, "iterations": base_iterations},
        "boosted_budget": {"passes": boosted_passes, "iterations": boosted_iterations},
        "mean_topic_word_cosine": float(np.mean(cos_sims)),
        "mean_js_similarity": float(np.mean(js_sims)),
        "ari": float(ari), "nmi": float(nmi),
        "dominant_topic_agreement": dominant_agreement,
    }
    out_dir = RESULTS_DIR / label
    with open(out_dir / "training_effort_sensitivity.json", "w", encoding="utf-8") as f:
        json.dump(result, f, indent=2)
    print(f"[{label}] training-effort sensitivity: JS={result['mean_js_similarity']:.3f} "
          f"dominant_agree={dominant_agreement:.3f}")
    return result


def dictionary_sensitivity(label, no_below, no_above, k, passes, iterations, medoid_seed):
    with open(PREP_DIR / label / "lemmatized_tokens_corrected.json", encoding="utf-8") as f:
        d = json.load(f)
    token_lists = list(d.values())

    dict_base = build_dictionary(token_lists, no_below, no_above)
    bow_base = build_bow_corpus(token_lists, dict_base)
    m_base = fit_lda(bow_base, dict_base, k=k, seed=medoid_seed, passes=passes, iterations=iterations)
    mat_base = topic_word_matrix(m_base)

    neighbors = []
    for db in [-1, 1]:
        nb2 = max(2, no_below + db)
        if nb2 != no_below:
            neighbors.append(("no_below", nb2, no_above))
    for da in [-0.05, 0.05]:
        na2 = round(min(1.0, max(0.5, no_above + da)), 2)
        if na2 != no_above:
            neighbors.append(("no_above", no_below, na2))

    rows = []
    for kind, nb, na in neighbors:
        dict_n = build_dictionary(token_lists, nb, na)
        bow_n = build_bow_corpus(token_lists, dict_n)
        m_n = fit_lda(bow_n, dict_n, k=k, seed=medoid_seed, passes=passes, iterations=iterations)
        mat_n = topic_word_matrix(m_n)
        mat_base_p, mat_n_p = project_pair_to_shared_vocab(mat_base, dict_base, mat_n, dict_n)
        row_ind, col_ind = align_topics_hungarian(mat_base_p, mat_n_p)
        sims = [js_similarity(mat_base_p[r], mat_n_p[c]) for r, c in zip(row_ind, col_ind)]
        rows.append({
            "varied_param": kind, "no_below": nb, "no_above": na,
            "vocab_size": len(dict_n), "mean_js_similarity_to_base": float(np.mean(sims)),
        })
    df = pd.DataFrame(rows)
    out_dir = RESULTS_DIR / label
    df.to_csv(out_dir / "dictionary_sensitivity.csv", index=False)
    print(f"[{label}] dictionary sensitivity computed for {len(df)} neighbors")
    return df


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("mode", choices=["subsample", "training_effort", "dictionary"])
    ap.add_argument("label")
    ap.add_argument("no_below", type=int)
    ap.add_argument("no_above", type=float)
    ap.add_argument("passes", type=int)
    ap.add_argument("iterations", type=int)
    ap.add_argument("k", type=int)
    ap.add_argument("seed", type=int)
    ap.add_argument("--model_path", default=None)
    args = ap.parse_args()
    if args.mode == "subsample":
        subsampling_robustness(args.label, args.no_below, args.no_above, args.passes,
                                args.iterations, args.k, args.model_path)
    elif args.mode == "training_effort":
        training_effort_sensitivity(args.label, args.no_below, args.no_above, args.k,
                                     args.passes, args.iterations, args.seed)
    elif args.mode == "dictionary":
        dictionary_sensitivity(args.label, args.no_below, args.no_above, args.k, args.passes,
                                args.iterations, args.seed)
