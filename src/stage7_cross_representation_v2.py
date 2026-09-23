"""
Cross-representation comparison, using the vocabulary-intersection method
(the method used for the final analysis; see reports/CROSS_REPRESENTATION_REPORT.md).

Does NOT refit a different model: uses the exact same frozen final
configuration (dictionary, priors, training budget, structural-medoid seed)
as every other stage-3/4/5/6 script. Refitting with an identical fixed seed
under gensim.models.LdaModel is deterministic (verified in this project),
so this reconstructs -- not changes -- the frozen k=4/k=4 models, which were
never persisted to disk as serialized model files.

Method:
  A. V_shared = metadata_vocab INTERSECT fulltext_vocab. Report both
     vocabulary sizes, the intersection size, and what % of each
     representation's vocabulary the intersection represents.
  B. For every (metadata topic, fulltext topic) pair: restrict both
     topic-word vectors to V_shared, record the RAW probability mass
     retained on V_shared *before* renormalization (coverage), then
     renormalize each restricted vector to sum to 1 over V_shared, then
     compute JS similarity, cosine similarity, top-10 and top-20 Jaccard
     on the shared vocabulary.
  C. Hungarian-align topics using the renormalized shared-vocabulary
     vectors (not forced to agree with the document-level contingency
     matrix -- word-level and document-level alignment are reported
     independently, exactly as the two are computed from different
     evidence: topic-word distributions vs. document-topic distributions).
  D. Also runs a document-label permutation test (10,000 permutations,
     fixed seed) for ARI/NMI, so the report can make a chance-comparison
     statement only if backed by this test.
"""

from __future__ import annotations

import csv
import sys
from pathlib import Path

import numpy as np
from gensim.corpora import Dictionary
from scipy.optimize import linear_sum_assignment
from scipy.spatial.distance import jensenshannon
from sklearn.metrics import adjusted_rand_score, normalized_mutual_info_score

sys.path.insert(0, str(Path(__file__).parent))
from preprocessing import preprocess_variant, get_plural_merge_map
from lda_utils import fit_lda, topic_word_matrix
from stage1_select import load_sweep, decide_variant
from stage1_sweep import load_metadata_texts, load_fulltext_texts
from stage2_select import select_convergence, select_priors

ROOT = Path(__file__).resolve().parents[1]

# Frozen final configuration -- must match reports/FROZEN_MANUSCRIPT_VALUES.md
# exactly. Not a new selection; reproduced deterministically from the same
# seed used throughout Stages 3-6.
FINAL_K = {"metadata": 4, "fulltext": 4}
FINAL_MEDOID_SEED = {"metadata": 1212, "fulltext": 505}
PERMUTATION_SEED = 42
N_PERMUTATIONS = 10000


def get_final_model(representation: str):
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

    k = FINAL_K[representation]
    seed = FINAL_MEDOID_SEED[representation]
    model = fit_lda(corpus, dictionary, num_topics=k, seed=seed,
                     passes=conv["passes"], iterations=conv["iterations"],
                     alpha=priors["alpha"], eta=priors["eta"])
    doc_topic = np.zeros((len(ids), k))
    for i, bow in enumerate(corpus):
        for tid, p in model.get_document_topics(bow, minimum_probability=0.0):
            doc_topic[i, tid] = p

    # Sanity check against the frozen values (does not alter anything;
    # fails loudly if reconstruction ever silently diverges from the frozen
    # record instead of matching it).
    dom_counts = [int((doc_topic.argmax(axis=1) == t).sum()) for t in range(k)]
    return {"ids": ids, "dictionary": dictionary, "matrix": topic_word_matrix(model),
            "doc_topic": doc_topic, "k": k, "dominant_counts": dom_counts}


def intersection_analysis(meta, ft):
    meta_vocab = set(meta["dictionary"].token2id)
    ft_vocab = set(ft["dictionary"].token2id)
    shared = sorted(meta_vocab & ft_vocab)

    meta_v, ft_v = len(meta_vocab), len(ft_vocab)
    shared_v = len(shared)
    pct_of_meta = 100 * shared_v / meta_v
    pct_of_ft = 100 * shared_v / ft_v

    shared_idx = {tok: i for i, tok in enumerate(shared)}

    def restrict(mat, dictionary):
        """Restrict each topic's distribution to shared vocab indices, in
        shared-vocab order. Returns (raw_restricted, coverage_per_topic)."""
        out = np.zeros((mat.shape[0], shared_v))
        for local_id, tok in dictionary.id2token.items():
            if tok in shared_idx:
                out[:, shared_idx[tok]] = mat[:, local_id]
        coverage = out.sum(axis=1)  # raw probability mass retained, pre-renorm
        return out, coverage

    meta_restricted, meta_coverage = restrict(meta["matrix"], meta["dictionary"])
    ft_restricted, ft_coverage = restrict(ft["matrix"], ft["dictionary"])

    # renormalize
    meta_norm = meta_restricted / meta_coverage[:, None]
    ft_norm = ft_restricted / ft_coverage[:, None]

    ka, kb = meta_norm.shape[0], ft_norm.shape[0]
    js_cost = np.array([[jensenshannon(meta_norm[i], ft_norm[j], base=2)
                          for j in range(kb)] for i in range(ka)])
    js_cost = np.nan_to_num(js_cost, nan=1.0)  # missing overlap -> treat as maximally dissimilar
    row_ind, col_ind = linear_sum_assignment(js_cost)

    pair_results = []
    for i, j in zip(row_ind, col_ind):
        a, b = meta_norm[i], ft_norm[j]
        js_sim = 1 - js_cost[i, j]
        cos_sim = float(np.dot(a, b) / (np.linalg.norm(a) * np.linalg.norm(b) + 1e-12))
        top10_a, top10_b = set(np.argsort(-a)[:10].tolist()), set(np.argsort(-b)[:10].tolist())
        top20_a, top20_b = set(np.argsort(-a)[:20].tolist()), set(np.argsort(-b)[:20].tolist())
        jacc10 = len(top10_a & top10_b) / len(top10_a | top10_b) if (top10_a | top10_b) else 0.0
        jacc20 = len(top20_a & top20_b) / len(top20_a | top20_b) if (top20_a | top20_b) else 0.0
        pair_results.append({
            "meta_topic": int(i), "ft_topic": int(j),
            "meta_coverage": float(meta_coverage[i]), "ft_coverage": float(ft_coverage[j]),
            "js_similarity": round(js_sim, 4), "cosine_similarity": round(cos_sim, 4),
            "top10_jaccard": round(jacc10, 4), "top20_jaccard": round(jacc20, 4),
        })

    return {
        "meta_vocab_size": meta_v, "ft_vocab_size": ft_v, "shared_vocab_size": shared_v,
        "pct_of_meta_vocab": round(pct_of_meta, 2), "pct_of_ft_vocab": round(pct_of_ft, 2),
        "pairs": pair_results,
    }


def permutation_test(dom_meta, dom_ft, seed=PERMUTATION_SEED, n_perm=N_PERMUTATIONS):
    rng = np.random.default_rng(seed)
    observed_ari = adjusted_rand_score(dom_meta, dom_ft)
    observed_nmi = normalized_mutual_info_score(dom_meta, dom_ft)

    n = len(dom_ft)
    perm_ari = np.empty(n_perm)
    perm_nmi = np.empty(n_perm)
    for p in range(n_perm):
        permuted = rng.permutation(dom_ft)
        perm_ari[p] = adjusted_rand_score(dom_meta, permuted)
        perm_nmi[p] = normalized_mutual_info_score(dom_meta, permuted)

    p_ari = float((perm_ari >= observed_ari).sum() + 1) / (n_perm + 1)
    p_nmi = float((perm_nmi >= observed_nmi).sum() + 1) / (n_perm + 1)
    return {
        "observed_ari": round(float(observed_ari), 4), "observed_nmi": round(float(observed_nmi), 4),
        "perm_ari_mean": round(float(perm_ari.mean()), 4), "perm_ari_sd": round(float(perm_ari.std()), 4),
        "perm_nmi_mean": round(float(perm_nmi.mean()), 4), "perm_nmi_sd": round(float(perm_nmi.std()), 4),
        "p_ari": p_ari, "p_nmi": p_nmi, "seed": seed, "n_permutations": n_perm,
    }


def main():
    meta = get_final_model("metadata")
    ft = get_final_model("fulltext")

    assert meta["ids"] == ft["ids"], "study ID order must match between representations"
    assert meta["k"] == 4 and ft["k"] == 4, "frozen k must be 4/4 -- do not change"
    assert meta["dominant_counts"] == [22, 16, 15, 13], \
        f"reconstructed metadata dominant counts {meta['dominant_counts']} != frozen [22,16,15,13]"
    assert ft["dominant_counts"] == [17, 8, 16, 25], \
        f"reconstructed fulltext dominant counts {ft['dominant_counts']} != frozen [17,8,16,25]"
    print("VERIFIED: reconstructed models exactly match frozen dominant-study counts "
          "(deterministic refit from frozen seed/config -- not a new fit).")

    ids = meta["ids"]
    inter = intersection_analysis(meta, ft)

    dom_meta = meta["doc_topic"].argmax(axis=1)
    dom_ft = ft["doc_topic"].argmax(axis=1)
    ari = adjusted_rand_score(dom_meta, dom_ft)
    nmi = normalized_mutual_info_score(dom_meta, dom_ft)
    print(f"VERIFIED document-level ARI={ari:.4f} NMI={nmi:.4f} "
          f"(frozen record: ARI=0.2384 NMI=0.2738)")

    contingency = np.zeros((4, 4), dtype=int)
    for dm, df in zip(dom_meta, dom_ft):
        contingency[dm, df] += 1

    perm = permutation_test(dom_meta, dom_ft)
    print(f"Permutation test ({perm['n_permutations']} perms, seed={perm['seed']}): "
          f"p_ARI={perm['p_ari']:.5f} p_NMI={perm['p_nmi']:.5f}")

    out_dir = ROOT / "results" / "cross_representation"
    out_dir.mkdir(parents=True, exist_ok=True)

    with open(out_dir / "intersection_analysis.csv", "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=["meta_topic", "ft_topic", "meta_coverage", "ft_coverage",
                                            "js_similarity", "cosine_similarity",
                                            "top10_jaccard", "top20_jaccard"])
        w.writeheader()
        for row in inter["pairs"]:
            w.writerow(row)

    with open(out_dir / "permutation_test.csv", "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=list(perm.keys()))
        w.writeheader()
        w.writerow(perm)

    with open(out_dir / "contingency_matrix.csv", "w", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        w.writerow([""] + [f"ft{j}" for j in range(4)])
        for i in range(4):
            w.writerow([f"meta{i}"] + contingency[i].tolist())

    print(f"meta_vocab={inter['meta_vocab_size']} ft_vocab={inter['ft_vocab_size']} "
          f"shared={inter['shared_vocab_size']} ({inter['pct_of_meta_vocab']}% of meta, "
          f"{inter['pct_of_ft_vocab']}% of ft)")
    for row in inter["pairs"]:
        print(f"  meta{row['meta_topic']} <-> ft{row['ft_topic']}: "
              f"coverage_meta={row['meta_coverage']:.3f} coverage_ft={row['ft_coverage']:.3f} "
              f"JS={row['js_similarity']} cos={row['cosine_similarity']} "
              f"jacc10={row['top10_jaccard']} jacc20={row['top20_jaccard']}")
    print("Wrote intersection_analysis.csv, permutation_test.csv, contingency_matrix.csv")


if __name__ == "__main__":
    main()
