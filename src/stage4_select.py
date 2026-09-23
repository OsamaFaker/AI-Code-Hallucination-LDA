"""
STAGE 4 -- Diagnostics and multi-criterion candidate selection
(PRE_EXECUTION_ANALYSIS_PLAN.md SS12), reading results/{representation}/k_sweep_summary.csv.

Pareto dominance over: maximize {mean_cv, mean_cnpmi, mean_stability,
mean_diversity, mean_assignment_confidence, normalized_entropy}, minimize
{redundancy_jaccard_mean, zero_dominance_topics, topics_lt5,
largest_topic_proportion, k (parsimony)}. A k is Pareto-optimal if no other k
is at least as good on every criterion and strictly better on at least one.
Entropy/concentration are included with their generically-safer direction but,
because Pareto dominance requires unanimous agreement across ALL criteria to
eliminate a k, no single criterion (including these two) can alone decide an
outcome -- consistent with plan SS16's caution against optimizing balance in
isolation.

Frozen reduction rule: if the Pareto-optimal set has >4 members, rank by
mean_stability (descending), keep the top 4; ties broken by smaller k.

Mega-/thin-/zero-topic flags (SS17) are reported for every k as inspection
triggers, not automatic rejections. Cross-k persistence (SS20) is computed
among the finalists via rectangular Hungarian alignment of medoid topic-word
matrices.

No LDA fitting here -- reads Stage 3's CSV outputs and (for persistence) the
already-fitted medoid models are NOT re-loaded (gensim models aren't
persisted to disk by Stage 3); persistence is instead computed by refitting
just the finalists' medoid seeds, which is cheap (<=4 fits per representation).
"""

from __future__ import annotations

import ast
import csv
import sys
from pathlib import Path

import numpy as np
from gensim.corpora import Dictionary
from scipy.optimize import linear_sum_assignment
from scipy.spatial.distance import jensenshannon

sys.path.insert(0, str(Path(__file__).parent))
from preprocessing import preprocess_variant, get_plural_merge_map
from lda_utils import fit_lda, topic_word_matrix
from stage1_select import load_sweep, decide_variant
from stage1_sweep import load_metadata_texts, load_fulltext_texts
from stage2_select import select_convergence, select_priors

ROOT = Path(__file__).resolve().parents[1]

MAXIMIZE = ["mean_cv", "mean_cnpmi", "mean_stability", "mean_diversity",
            "mean_assignment_confidence", "normalized_entropy"]
MINIMIZE = ["redundancy_jaccard_mean", "zero_dominance_topics", "topics_lt5",
            "largest_topic_proportion", "k"]


def load_k_summary(representation: str) -> list[dict]:
    path = ROOT / "results" / representation / "k_sweep_summary.csv"
    with open(path, newline="", encoding="utf-8") as f:
        rows = list(csv.DictReader(f))
    for r in rows:
        r["k"] = int(r["k"])
        for field in MAXIMIZE + MINIMIZE:
            if field == "k":
                continue
            r[field] = float(r[field])
        r["dominant_counts"] = ast.literal_eval(r["dominant_counts_json"])
    rows.sort(key=lambda r: r["k"])
    return rows


def dominates(a: dict, b: dict) -> bool:
    """True if k-row `a` dominates k-row `b` (>= on all, > on >=1)."""
    at_least_as_good = True
    strictly_better = False
    for f in MAXIMIZE:
        if a[f] < b[f]:
            at_least_as_good = False
            break
        if a[f] > b[f]:
            strictly_better = True
    if at_least_as_good:
        for f in MINIMIZE:
            if a[f] > b[f]:
                at_least_as_good = False
                break
            if a[f] < b[f]:
                strictly_better = True
    return at_least_as_good and strictly_better


def pareto_optimal_set(rows: list[dict]) -> list[dict]:
    return [r for r in rows if not any(dominates(o, r) for o in rows if o["k"] != r["k"])]


def reduce_to_finalists(pareto: list[dict], max_n: int = 4) -> list[dict]:
    if len(pareto) <= max_n:
        return sorted(pareto, key=lambda r: r["k"])
    ranked = sorted(pareto, key=lambda r: (-r["mean_stability"], r["k"]))
    return sorted(ranked[:max_n], key=lambda r: r["k"])


def mega_thin_flags(r: dict) -> list[str]:
    flags = []
    if r["zero_dominance_topics"] > 0:
        flags.append(f"ZERO-DOMINANCE topics: {int(r['zero_dominance_topics'])}")
    if int(r.get("topics_lt3", 0)) > 0:
        flags.append(f"VERY THIN (<3 studies) topics: {int(r['topics_lt3'])}")
    if int(r["topics_lt5"]) > 0:
        flags.append(f"THIN (<5 studies) topics: {int(r['topics_lt5'])}")
    if r["largest_topic_proportion"] > 0.40:
        flags.append(f"large topic proportion: {r['largest_topic_proportion']:.1%}")
    return flags


def refit_medoid(representation: str, k: int, medoid_seed: int):
    """Refit exactly the medoid model for a finalist k, using the same
    frozen Stage1+Stage2 config, to obtain its topic-word matrix for
    cross-k persistence comparison (medoid matrices aren't persisted by
    Stage 3)."""
    rows = load_sweep(representation)
    d1 = decide_variant(representation, rows)
    fc = d1["final_config"]
    priors = select_priors(representation)
    conv = select_convergence(representation)

    if representation == "metadata":
        _, texts = load_metadata_texts()
    else:
        _, texts = load_fulltext_texts()
    plural_map = get_plural_merge_map(texts)
    tokens = preprocess_variant(texts, d1["chosen_hf"], d1["use_bigrams"], plural_map)
    dictionary = Dictionary(tokens)
    dictionary.filter_extremes(no_below=fc["no_below"], no_above=fc["no_above"])
    corpus = [dictionary.doc2bow(t) for t in tokens]

    model = fit_lda(corpus, dictionary, num_topics=k, seed=medoid_seed,
                     passes=conv["passes"], iterations=conv["iterations"],
                     alpha=priors["alpha"], eta=priors["eta"])
    return topic_word_matrix(model), dictionary


def cross_k_persistence(representation: str, finalists: list[dict]) -> list[dict]:
    """Rectangular Hungarian alignment of medoid topic-word matrices between
    each pair of consecutive finalist k values, projected onto their shared
    vocabulary (dictionaries may differ trivially only if refit nondeterminism
    existed, which it should not under LdaModel with a fixed seed -- same
    dictionary is reused here so vocab is identical across finalists)."""
    matrices = {}
    dictionary = None
    for r in finalists:
        mat, dictionary = refit_medoid(representation, r["k"], int(r["medoid_seed"]))
        matrices[r["k"]] = mat

    results = []
    ks = sorted(matrices.keys())
    for i in range(len(ks) - 1):
        k1, k2 = ks[i], ks[i + 1]
        m1, m2 = matrices[k1], matrices[k2]
        n1, n2 = m1.shape[0], m2.shape[0]
        cost = np.array([[jensenshannon(m1[a], m2[b], base=2) for b in range(n2)] for a in range(n1)])
        cost = np.nan_to_num(cost, nan=0.0)
        row_ind, col_ind = linear_sum_assignment(cost)
        js_sims = 1 - cost[row_ind, col_ind]

        jacc_sims = []
        for a, b in zip(row_ind, col_ind):
            top1 = set(np.argsort(-m1[a])[:20].tolist())
            top2 = set(np.argsort(-m2[b])[:20].tolist())
            inter, union = len(top1 & top2), len(top1 | top2)
            jacc_sims.append(inter / union if union else 0.0)

        results.append({
            "k1": k1, "k2": k2,
            "n_matched": len(row_ind),
            "mean_js_similarity": round(float(js_sims.mean()), 4),
            "mean_top20_jaccard": round(float(np.mean(jacc_sims)), 4),
            "unmatched_in_k2": n2 - len(row_ind),
        })
    return results


def write_report(representation: str) -> None:
    rows = load_k_summary(representation)
    pareto = pareto_optimal_set(rows)
    finalists = reduce_to_finalists(pareto)

    out_path = ROOT / "results" / representation / "stage4_candidates.md"
    with open(out_path, "w", encoding="utf-8") as f:
        f.write(f"# Stage 4 Candidate Selection -- {representation}\n\n")

        f.write("## Mega-/thin-/zero-topic flags, all k (inspection triggers, not rejections)\n\n")
        f.write("| k | flags |\n|---|---|\n")
        for r in rows:
            flags = mega_thin_flags(r)
            f.write(f"| {r['k']} | {'; '.join(flags) if flags else '(none)'} |\n")
        f.write("\n")

        f.write(f"## Pareto-optimal set: {len(pareto)} k value(s)\n\n")
        f.write(f"k = {sorted(r['k'] for r in pareto)}\n\n")

        f.write(f"## Finalists after frozen reduction rule (max 4, ranked by stability): "
                f"{len(finalists)} k value(s)\n\n")
        f.write("| k | mean_cv | mean_cnpmi | mean_stability | mean_diversity | redundancy_jaccard | "
                "zero_dom | thin<5 | entropy | assign_conf |\n")
        f.write("|---|---|---|---|---|---|---|---|---|---|\n")
        for r in finalists:
            f.write(f"| {r['k']} | {r['mean_cv']:.4f} | {r['mean_cnpmi']:.4f} | {r['mean_stability']:.4f} | "
                    f"{r['mean_diversity']:.4f} | {r['redundancy_jaccard_mean']:.4f} | "
                    f"{int(r['zero_dominance_topics'])} | {int(r['topics_lt5'])} | "
                    f"{r['normalized_entropy']:.4f} | {r['mean_assignment_confidence']:.4f} |\n")
        f.write("\n")

        if len(finalists) >= 2:
            f.write("## Cross-k persistence among finalists (rectangular Hungarian alignment)\n\n")
            persistence = cross_k_persistence(representation, finalists)
            f.write("| k1 | k2 | matched topics | mean JS similarity | mean top-20 Jaccard | unmatched in k2 |\n")
            f.write("|---|---|---|---|---|---|\n")
            for p in persistence:
                f.write(f"| {p['k1']} | {p['k2']} | {p['n_matched']} | {p['mean_js_similarity']} | "
                        f"{p['mean_top20_jaccard']} | {p['unmatched_in_k2']} |\n")
            f.write("\n")
            f.write("High JS similarity / Jaccard between consecutive finalists suggests the larger k "
                    "mostly subdivides or duplicates themes already present at the smaller k; low values "
                    "suggest genuinely new themes emerge. Interpreted qualitatively in the final report, "
                    "not used as an automatic elimination rule.\n")
        else:
            f.write("Only one finalist -- cross-k persistence not applicable.\n")

    print(f"Wrote {out_path}")
    print(f"[{representation}] Pareto-optimal: {sorted(r['k'] for r in pareto)} -> "
          f"finalists: {sorted(r['k'] for r in finalists)}")


def main():
    reps = sys.argv[1:] or ["metadata", "fulltext"]
    for rep in reps:
        write_report(rep)


if __name__ == "__main__":
    main()
