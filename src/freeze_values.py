"""Freeze task Part 4: generate results/FROZEN_FINAL_VALUES.{json,csv} directly from
authoritative source files, verify against the expected table, and if any value disagrees,
stop and write reports/FROZEN_VALUE_DISCREPANCIES.md instead of silently freezing.
"""
import json
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
RESULTS_DIR = ROOT / "results"
REPORTS_DIR = ROOT / "reports"

EXPECTED = {
    "N": (66, 66),
    "Final k": (4, 8),
    "Vocabulary size": (397, 2626),
    "Seeds per k": (20, 20),
    "Definitive k-sweep models": (380, 380),
    "Structural-medoid seed": (14, 2),
    "Mean C_v at final k": (0.4035, 0.3958),
    "Mean C_NPMI": (-0.1042, -0.0432),
    "Mean cross-seed JS stability": (0.6610, 0.5432),
    "Mean topic diversity": (0.8425, 0.7669),
    "80% subsampling topic similarity": (0.5858, 0.5151),
    "80% subsampling ARI": (0.1287, 0.2192),
}
TOL = 1e-3


def compute_actual():
    out = {}
    for label, idx in [("metadata", 0), ("fulltext", 1)]:
        manifest = pd.read_csv(ROOT / "corpus" / "primary_studies_manifest.csv")
        with open(RESULTS_DIR / label / "stage1_selected_config.json", encoding="utf-8") as f:
            dict_cfg = json.load(f)
        with open(RESULTS_DIR / label / "k_selection_decision.json", encoding="utf-8") as f:
            ksel = json.load(f)
        k = ksel["selected_k"]
        with open(RESULTS_DIR / label / f"representative_seed_k{k:02d}.json", encoding="utf-8") as f:
            medoid = json.load(f)
        runs = pd.read_csv(RESULTS_DIR / label / "definitive_ksweep_runs.csv")
        k_runs = runs[runs.k == k]
        stab = pd.read_csv(RESULTS_DIR / label / "seed_stability_by_k.csv")
        k_stab = stab[stab.k == k].iloc[0]
        subs = pd.read_csv(RESULTS_DIR / label / "subsampling_80pct_100reps.csv")

        out.setdefault("N", [None, None])[idx] = int(len(manifest))
        out.setdefault("Final k", [None, None])[idx] = int(k)
        out.setdefault("Vocabulary size", [None, None])[idx] = int(dict_cfg["selected_vocab_size"])
        out.setdefault("Seeds per k", [None, None])[idx] = int(runs.groupby("k").size().iloc[0])
        out.setdefault("Definitive k-sweep models", [None, None])[idx] = int(len(runs))
        out.setdefault("Structural-medoid seed", [None, None])[idx] = int(medoid["medoid_seed"])
        out.setdefault("Mean C_v at final k", [None, None])[idx] = round(float(k_runs["c_v"].mean()), 4)
        out.setdefault("Mean C_NPMI", [None, None])[idx] = round(float(k_runs["c_npmi"].mean()), 4)
        out.setdefault("Mean cross-seed JS stability", [None, None])[idx] = round(float(k_stab["js_similarity_mean"]), 4)
        out.setdefault("Mean topic diversity", [None, None])[idx] = round(float(k_runs["topic_diversity"].mean()), 4)
        out.setdefault("80% subsampling topic similarity", [None, None])[idx] = round(float(subs["topic_similarity_js"].mean()), 4)
        out.setdefault("80% subsampling ARI", [None, None])[idx] = round(float(subs["ari"].mean()), 4)
    return out


def main():
    actual = compute_actual()
    discrepancies = []
    for metric, (exp_meta, exp_full) in EXPECTED.items():
        act_meta, act_full = actual[metric]
        for rep, exp, act in [("metadata", exp_meta, act_meta), ("fulltext", exp_full, act_full)]:
            if abs(act - exp) > TOL:
                discrepancies.append({
                    "metric": metric, "representation": rep,
                    "expected_value": exp, "computed_value": act,
                })

    if discrepancies:
        lines = ["# Frozen Value Discrepancies\n",
                 "Freeze process STOPPED. The following computed values differ from the "
                 "expected/previously-reported table by more than the tolerance "
                 f"({TOL}):\n",
                 "| Expected value | Computed value | Metric | Representation | Source file | Likely explanation |",
                 "|---|---|---|---|---|---|"]
        for d in discrepancies:
            lines.append(f"| {d['expected_value']} | {d['computed_value']} | {d['metric']} | "
                          f"{d['representation']} | results/{d['representation']}/ | "
                          f"*requires manual investigation* |")
        (REPORTS_DIR / "FROZEN_VALUE_DISCREPANCIES.md").write_text("\n".join(lines) + "\n", encoding="utf-8")
        print(f"STOPPED: {len(discrepancies)} discrepancies written to "
              f"reports/FROZEN_VALUE_DISCREPANCIES.md")
        return False

    frozen = {
        "freeze_status": "VERIFIED - all computed values match expected table within tolerance",
        "tolerance": TOL,
        "metrics": {metric: {"metadata": actual[metric][0], "fulltext": actual[metric][1]}
                    for metric in EXPECTED},
    }
    with open(RESULTS_DIR / "FROZEN_FINAL_VALUES.json", "w", encoding="utf-8") as f:
        json.dump(frozen, f, indent=2)

    rows = [{"Metric": m, "Metadata": actual[m][0], "Full_text": actual[m][1]} for m in EXPECTED]
    pd.DataFrame(rows).to_csv(RESULTS_DIR / "FROZEN_FINAL_VALUES.csv", index=False)

    print("VERIFIED: all values match. Frozen to results/FROZEN_FINAL_VALUES.{json,csv}")
    for m in EXPECTED:
        print(f"  {m}: metadata={actual[m][0]}, fulltext={actual[m][1]}")
    return True


if __name__ == "__main__":
    main()
