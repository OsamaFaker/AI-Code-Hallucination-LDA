"""Section 11/15: select the frozen no_below/no_above per representation from the Stage-1
grid, using a documented, auditable rule - never the max-C_v cell.

Rule:
1. Aggregate each (no_below, no_above) cell over its 3 pilot k values (mean).
2. Restrict to the "stable region": stability >= (max_stability - 0.05) AND
   mean_thin_topic_count_lt3 <= (min_thin_topic_count + 1.0) AND
   mean_topic_diversity >= (max_diversity - 0.10).
   (Coherence, C_v, is deliberately excluded from the admissibility filter - it is reported
   but never used to gate candidates, per the explicit prohibition on coherence-only or
   max-coherence selection.)
3. Among admissible cells, select the one closest (Euclidean, min-max normalized over the
   full grid) to the conventional gensim defaults (no_below=5, no_above=0.5), breaking ties
   by higher stability. This operationalizes "prefer a parsimonious and conventional
   configuration when several neighboring configurations are equivalent" without hand-picking.
"""
import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
RESULTS_DIR = ROOT / "results"
PREP_DIR = ROOT / "preprocessing"

CONVENTIONAL = {"no_below": 5, "no_above": 0.50}


def select(label: str):
    df = pd.read_csv(RESULTS_DIR / label / "stage1_dictionary_threshold_sweep.csv")
    agg = df.groupby(["no_below", "no_above"]).agg(
        vocab_size=("vocab_size", "mean"),
        mean_c_v=("mean_c_v", "mean"),
        mean_c_npmi=("mean_c_npmi", "mean"),
        stability=("stability_js_similarity", "mean"),
        diversity=("mean_topic_diversity", "mean"),
        redundancy=("mean_topic_redundancy_jaccard", "mean"),
        thin_topics=("mean_thin_topic_count_lt3", "mean"),
        zero_dominance=("mean_zero_dominance_topic_count", "mean"),
    ).reset_index()

    max_stab, min_thin, max_div = agg.stability.max(), agg.thin_topics.min(), agg.diversity.max()
    admissible = agg[
        (agg.stability >= max_stab - 0.05)
        & (agg.thin_topics <= min_thin + 1.0)
        & (agg.diversity >= max_div - 0.10)
    ].copy()
    if admissible.empty:
        admissible = agg.copy()  # fallback: should not happen given wide margins above

    nb_range = agg.no_below.max() - agg.no_below.min()
    na_range = agg.no_above.max() - agg.no_above.min()
    admissible["dist_to_conventional"] = np.sqrt(
        ((admissible.no_below - CONVENTIONAL["no_below"]) / nb_range) ** 2
        + ((admissible.no_above - CONVENTIONAL["no_above"]) / na_range) ** 2
    )
    admissible = admissible.sort_values(["dist_to_conventional", "stability"],
                                         ascending=[True, False])
    chosen = admissible.iloc[0]

    decision = {
        "representation": label,
        "grid_cells_total": int(len(agg)),
        "grid_cells_admissible_stable_region": int(len(admissible)),
        "max_stability_in_grid": float(max_stab),
        "min_thin_topics_in_grid": float(min_thin),
        "max_diversity_in_grid": float(max_div),
        "selected_no_below": int(chosen.no_below),
        "selected_no_above": float(chosen.no_above),
        "selected_vocab_size": float(chosen.vocab_size),
        "selected_mean_c_v": float(chosen.mean_c_v),
        "selected_mean_c_npmi": float(chosen.mean_c_npmi),
        "selected_stability": float(chosen.stability),
        "selected_diversity": float(chosen.diversity),
        "selected_thin_topics": float(chosen.thin_topics),
        "rule": (
            "Admissible = within 0.05 of max stability, within 1.0 thin-topic of the "
            "grid minimum, within 0.10 of max diversity (coherence excluded from "
            "admissibility). Among admissible cells, closest (normalized Euclidean) to "
            "conventional defaults no_below=5/no_above=0.50, tie-broken by higher stability."
        ),
    }
    out_dir = RESULTS_DIR / label
    with open(out_dir / "stage1_selected_config.json", "w", encoding="utf-8") as f:
        json.dump(decision, f, indent=2)
    agg.to_csv(out_dir / "stage1_dictionary_grid_aggregated.csv", index=False)
    print(f"[{label}] selected no_below={decision['selected_no_below']} "
          f"no_above={decision['selected_no_above']} "
          f"(vocab={decision['selected_vocab_size']:.0f}, "
          f"stability={decision['selected_stability']:.3f}, "
          f"{decision['grid_cells_admissible_stable_region']}/{decision['grid_cells_total']} admissible)")
    return decision


if __name__ == "__main__":
    label = sys.argv[1] if len(sys.argv) > 1 else "metadata"
    select(label)
