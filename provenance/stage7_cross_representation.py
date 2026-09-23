"""
SUPERSEDED -- kept only as an audit-trail record, do not cite its output.

This script's union-vocabulary topic-word comparison (zero-padding both
topics onto the union of both dictionaries) was withdrawn after an internal
reporting audit (reports/POST_LDA_REPORTING_REPAIR_AUDIT.md) found its
"probability dilution" explanation for the resulting near-zero
similarities was not an adequate characterization of the method's own
limitation. Use stage7_cross_representation_v2.py (intersection-vocabulary
approach, with coverage reporting and a permutation test) instead -- that
is the version cited in every current report. This file's output is
preserved at
results/cross_representation/comparison_SUPERSEDED_union_vocab.md.

--- original docstring below ---

Cross-representation comparison (PRE_EXECUTION_ANALYSIS_PLAN.md SS15 /
Master Prompt SS30), run only after both representations are independently
frozen and human-rated.

Final selected k: metadata k=4, fulltext k=4 (see reports/HUMAN_VALIDATION_REPORT.md
for the reconciliation). Refits each representation's final medoid model,
projects topic-word distributions onto their shared vocabulary (rectangular
alignment -- both models happen to have the same k here, so this is a square
Hungarian match on the shared-vocab projection, not a same-vocabulary
assumption), and reports JS similarity, cosine similarity, top-20 Jaccard,
matched/unmatched topics, plus ARI/NMI and a dominant-topic contingency
matrix over the same 66 studies.
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
from stage5_robustness import project_to_shared_vocab

ROOT = Path(__file__).resolve().parents[1]

FINAL_K = {"metadata": 4, "fulltext": 4}
FINAL_MEDOID_SEED = {"metadata": 1212, "fulltext": 505}


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
    return {"ids": ids, "dictionary": dictionary, "matrix": topic_word_matrix(model),
            "doc_topic": doc_topic, "k": k}


def main():
    meta = get_final_model("metadata")
    ft = get_final_model("fulltext")

    assert meta["ids"] == ft["ids"], "study ID order must match between representations"
    ids = meta["ids"]

    mat_meta_proj, mat_ft_proj = project_to_shared_vocab(
        meta["matrix"], meta["dictionary"], ft["matrix"], ft["dictionary"])

    ka, kb = mat_meta_proj.shape[0], mat_ft_proj.shape[0]
    js_cost = np.array([[jensenshannon(mat_meta_proj[i], mat_ft_proj[j], base=2)
                          for j in range(kb)] for i in range(ka)])
    js_cost = np.nan_to_num(js_cost, nan=0.0)
    row_ind, col_ind = linear_sum_assignment(js_cost)

    cos_sims, jacc_sims = [], []
    for i, j in zip(row_ind, col_ind):
        a, b = mat_meta_proj[i], mat_ft_proj[j]
        cos_sims.append(float(np.dot(a, b) / (np.linalg.norm(a) * np.linalg.norm(b))))
        # top-20 Jaccard computed in each representation's OWN vocabulary index
        # space is meaningless across representations; use the shared-vocab
        # projection's top-20 instead so word identities are comparable.
        top_a = set(np.argsort(-mat_meta_proj[i])[:20].tolist())
        top_b = set(np.argsort(-mat_ft_proj[j])[:20].tolist())
        inter, union = len(top_a & top_b), len(top_a | top_b)
        jacc_sims.append(inter / union if union else 0.0)

    dom_meta = meta["doc_topic"].argmax(axis=1)
    dom_ft = ft["doc_topic"].argmax(axis=1)
    ari = adjusted_rand_score(dom_meta, dom_ft)
    nmi = normalized_mutual_info_score(dom_meta, dom_ft)

    contingency = np.zeros((ka, kb), dtype=int)
    for dm, df in zip(dom_meta, dom_ft):
        contingency[dm, df] += 1

    out_path = ROOT / "results" / "cross_representation" / "comparison.md"
    out_path.parent.mkdir(parents=True, exist_ok=True)
    with open(out_path, "w", encoding="utf-8") as f:
        f.write("# Cross-Representation Comparison -- metadata (k=4) vs full-text (k=4)\n\n")
        f.write("Rectangular Hungarian alignment on topic-word distributions projected onto the "
                "shared (union) vocabulary of both representations' frozen dictionaries.\n\n")
        f.write("## Topic alignment\n\n")
        f.write("| metadata topic | fulltext topic | JS similarity | cosine similarity | top-20 Jaccard |\n")
        f.write("|---|---|---|---|---|\n")
        for idx, (i, j) in enumerate(zip(row_ind, col_ind)):
            js_sim = 1 - js_cost[i, j]
            f.write(f"| {i} | {j} | {js_sim:.4f} | {cos_sims[idx]:.4f} | {jacc_sims[idx]:.4f} |\n")
        f.write(f"\nMatched topics: {len(row_ind)}/{ka}. Unmatched: "
                f"{ka - len(row_ind)} (metadata), {kb - len(col_ind)} (fulltext).\n\n")

        f.write("## Document-level agreement (dominant topic, same 66 studies)\n\n")
        f.write(f"- ARI = {ari:.4f}\n- NMI = {nmi:.4f}\n\n")

        f.write("## Dominant-topic contingency matrix (rows=metadata, cols=fulltext)\n\n")
        header = "| |" + "".join(f" ft{j} |" for j in range(kb))
        f.write(header + "\n")
        f.write("|" + "---|" * (kb + 1) + "\n")
        for i in range(ka):
            f.write(f"| meta{i} |" + "".join(f" {contingency[i,j]} |" for j in range(kb)) + "\n")
        f.write("\nDisagreement is not interpreted as model failure -- differences may reflect "
                "representation, stochastic variation, or genuinely different thematic granularity "
                "between what a title/abstract/keywords signal and what full-text methodological "
                "detail signals.\n")

    print(f"Wrote {out_path}")
    print(f"ARI={ari:.4f} NMI={nmi:.4f}, matched {len(row_ind)}/{ka} topics")
    for idx, (i, j) in enumerate(zip(row_ind, col_ind)):
        print(f"  meta{i} <-> ft{j}: JS={1-js_cost[i,j]:.3f} cos={cos_sims[idx]:.3f} jacc={jacc_sims[idx]:.3f}")


if __name__ == "__main__":
    main()
