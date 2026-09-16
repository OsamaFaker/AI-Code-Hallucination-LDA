"""Section 20: multi-criterion, Pareto-front-based k selection. No coherence-only selection,
no post-hoc numerical weighting. Parsimony (smallest k) breaks ties among Pareto-optimal k.
"""
import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
RESULTS_DIR = ROOT / "results"

# direction: 1 = higher is better, -1 = lower is better
CRITERIA = {
    "mean_c_v": 1, "mean_c_npmi": 1, "stability": 1, "diversity": 1,
    "redundancy_jaccard": -1, "thin_topics_lt3": -1, "zero_dominance": -1,
}


def build_k_table(label: str) -> pd.DataFrame:
    runs = pd.read_csv(RESULTS_DIR / label / "definitive_ksweep_runs.csv")
    stab = pd.read_csv(RESULTS_DIR / label / "seed_stability_by_k.csv")

    agg = runs.groupby("k").agg(
        mean_c_v=("c_v", "mean"), sd_c_v=("c_v", "std"),
        mean_c_npmi=("c_npmi", "mean"),
        diversity=("topic_diversity", "mean"),
        redundancy_jaccard=("mean_top20_jaccard", "mean"),
        thin_topics_lt3=("n_topics_lt3_studies", "mean"),
        zero_dominance=("n_topics_0_studies", "mean"),
        margin_mean=("margin_mean", "mean"),
    ).reset_index()
    agg = agg.merge(stab[["k", "js_similarity_mean"]].rename(columns={"js_similarity_mean": "stability"}),
                     on="k", how="left")
    return agg


def pareto_front(df: pd.DataFrame, criteria: dict) -> list[int]:
    ks = df["k"].tolist()
    vals = {c: df[c].values for c in criteria}
    dominated = set()
    for i, ki in enumerate(ks):
        for j, kj in enumerate(ks):
            if i == j:
                continue
            at_least_as_good_all = all(
                (vals[c][j] - vals[c][i]) * criteria[c] >= 0 for c in criteria
            )
            strictly_better_one = any(
                (vals[c][j] - vals[c][i]) * criteria[c] > 0 for c in criteria
            )
            if at_least_as_good_all and strictly_better_one:
                dominated.add(ki)
                break
    return sorted(k for k in ks if k not in dominated)


def composite_scores(df: pd.DataFrame, criteria: dict) -> pd.Series:
    """Unweighted (equal-weight) min-max normalized average across the same criteria used for
    the Pareto front, normalized over the FULL k range (not just the front) so distances are
    meaningful. This is not a post-hoc weighting scheme (all weights are equal and fixed a
    priori) - it exists only to identify which Pareto-optimal points are genuinely close to
    the front's best point, so that parsimony is applied among *substantively equivalent*
    k values rather than licensing a jump to a degenerate small-k solution that trivially
    dominates on redundancy/thin-topic metrics by having almost nothing to be redundant with."""
    norm = pd.DataFrame(index=df.index)
    for c, direction in criteria.items():
        v = df[c].values.astype(float)
        rng = v.max() - v.min()
        n = (v - v.min()) / rng if rng > 0 else np.zeros_like(v)
        norm[c] = n if direction == 1 else 1 - n
    return norm.mean(axis=1)


def select_k(label: str, equivalence_tolerance: float = 0.05, min_k: int = 4):
    df = build_k_table(label).reset_index(drop=True)
    front = pareto_front(df, CRITERIA)

    df["composite_score"] = composite_scores(df, CRITERIA)
    front_df = df[df.k.isin(front)]

    # The k>=min_k floor is applied FIRST and unconditionally - it defines the admissible
    # candidate pool before any "best point" or "equivalence" is computed, so a k below the
    # floor can never re-enter through the tolerance fallback. Only within that floored pool
    # does parsimony (smallest k within `equivalence_tolerance` of the pool's best composite
    # point) apply.
    floored = front_df[front_df["k"] >= min_k]
    if floored.empty:  # protocol's own k-range never makes this possible, but stay explicit
        floored = front_df
    best_composite = floored["composite_score"].max()
    equivalent = floored[floored["composite_score"] >= best_composite - equivalence_tolerance]
    selected_k = int(equivalent["k"].min())

    decision = {
        "representation": label,
        "criteria_used": list(CRITERIA.keys()),
        "pareto_optimal_k_values": front,
        "best_composite_k": int(floored.loc[floored.composite_score.idxmax(), "k"]),
        "best_composite_score": float(best_composite),
        "equivalence_tolerance": equivalence_tolerance,
        "min_k_floor": min_k,
        "k_values_equivalent_to_best": sorted(equivalent["k"].tolist()),
        "selected_k": selected_k,
        "selection_rule": (
            "Pareto front over mean C_v, mean C_NPMI, cross-seed stability (mean JS "
            "similarity), topic diversity, topic redundancy (top-20 Jaccard, minimized), "
            "thin-topic incidence (minimized), zero-dominance-topic count (minimized). No "
            "single metric (including C_v) is used alone. An unweighted (equal-weight) "
            "min-max-normalized composite of the same criteria identifies the front's best "
            "point; parsimony (smallest k) is then applied only among Pareto-optimal k within "
            f"{equivalence_tolerance} composite-score of that best point and at or above a "
            f"documented floor of k={min_k} (below which a topic model cannot plausibly "
            "resolve distinct sub-themes in a multi-theme corpus, so apparent dominance from "
            "near-zero redundancy/thin-topic counts at very small k is not treated as "
            "genuine equivalence)."
        ),
        "note_on_interpretability": (
            "Human/qualitative interpretability and topic prevalence balance are evaluated "
            "after this quantitative selection (Section 22) and may motivate a documented "
            "protocol amendment if the selected k proves uninterpretable, per protocol "
            "amendment rules."
        ),
    }
    out_dir = RESULTS_DIR / label
    df.to_csv(out_dir / "k_selection_table.csv", index=False)
    with open(out_dir / "k_selection_decision.json", "w", encoding="utf-8") as f:
        json.dump(decision, f, indent=2)
    print(f"[{label}] Pareto front: {front} -> selected k={selected_k}")
    return decision


if __name__ == "__main__":
    label = sys.argv[1] if len(sys.argv) > 1 else "metadata"
    select_k(label)
