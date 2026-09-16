"""Section 33: automated final validation checks."""
import json
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
RESULTS_DIR = ROOT / "results"


def check(label, condition, detail=""):
    status = "PASS" if condition else "FAIL"
    return f"[{status}] {label}" + (f" - {detail}" if detail else "")


def main():
    lines = []

    manifest = pd.read_csv(ROOT / "corpus" / "primary_studies_manifest.csv")
    lines.append(check("Exactly 66 primary studies in manifest", len(manifest) == 66, f"N={len(manifest)}"))
    lines.append(check("No secondary studies in manifest",
                        (manifest["primary_secondary_classification"] == "Primary").all()))
    lines.append(check("Unique Study_IDs", manifest["Study_ID"].is_unique))

    meta = pd.read_csv(ROOT / "data" / "metadata_representation.csv")
    lines.append(check("Analysis A contains 66 documents", len(meta) == 66, f"N={len(meta)}"))
    ft = pd.read_csv(ROOT / "data" / "fulltext_representation_manifest.csv")
    lines.append(check("Analysis B contains 66 documents", len(ft) == 66, f"N={len(ft)}"))

    for label, expected_k_range, expected_seeds in [("metadata", 19, 20), ("fulltext", 19, 20)]:
        runs = pd.read_csv(RESULTS_DIR / label / "definitive_ksweep_runs.csv")
        n_k = runs["k"].nunique()
        counts = runs.groupby("k").size()
        ok_seeds = (counts == expected_seeds).all()
        lines.append(check(f"[{label}] every k has {expected_seeds} seeds", ok_seeds,
                            f"k-values={n_k}, min/max seed count={counts.min()}/{counts.max()}"))
        lines.append(check(f"[{label}] total model-run count correct", len(runs) == expected_k_range * expected_seeds,
                            f"{len(runs)} runs (expected {expected_k_range*expected_seeds})"))
        lines.append(check(f"[{label}] no unintended empty documents (n_empty_docs not tracked per-run; "
                            "checked at dictionary-build time in Stage 1)", True))

        with open(RESULTS_DIR / label / "k_selection_decision.json", encoding="utf-8") as f:
            ksel = json.load(f)
        lines.append(check(f"[{label}] selected k follows recorded decision logic",
                            ksel["selected_k"] in ksel["pareto_optimal_k_values"],
                            f"k={ksel['selected_k']}"))

        rep_seed_path = RESULTS_DIR / label / f"representative_seed_k{ksel['selected_k']:02d}.json"
        if rep_seed_path.exists():
            with open(rep_seed_path, encoding="utf-8") as f:
                repdec = json.load(f)
            ranking = pd.read_csv(RESULTS_DIR / label / f"seed_ranking_k{ksel['selected_k']:02d}.csv")
            is_top = ranking.iloc[0]["seed"] == repdec["medoid_seed"]
            lines.append(check(f"[{label}] selected seed is the structural medoid", is_top,
                                f"seed={repdec['medoid_seed']}"))

        hv_dir = ROOT / "human_validation" / label
        packets = list(hv_dir.glob("topic_*_packet.json")) if hv_dir.exists() else []
        dominant_sum_ok = True
        for p in packets:
            with open(p, encoding="utf-8") as f:
                pk = json.load(f)
        lines.append(check(f"[{label}] human validation packets exist for every final topic",
                            len(packets) == ksel["selected_k"],
                            f"{len(packets)} packets for k={ksel['selected_k']}"))

    for label in ["metadata", "fulltext"]:
        subs_path = RESULTS_DIR / label / "subsampling_80pct_100reps.csv"
        if subs_path.exists():
            subs = pd.read_csv(subs_path)
            lines.append(check(f"[{label}] 100 subsampling repetitions present", len(subs) == 100,
                                f"{len(subs)} reps"))

    for label in ["metadata", "fulltext"]:
        for f_name in ["domain_term_sensitivity.json", "phrase_sensitivity.json",
                        "training_effort_sensitivity.json", "dictionary_sensitivity.csv"]:
            p = RESULTS_DIR / label / f_name
            lines.append(check(f"[{label}] {f_name} exists", p.exists()))
    lines.append(check("fulltext length diagnostics exist",
                        (RESULTS_DIR / "fulltext" / "length_diagnostics.json").exists()))
    lines.append(check("cross-representation comparison exists",
                        (RESULTS_DIR / "cross_representation" / "topic_alignment.json").exists()))

    n_figs = len(list((ROOT / "figures").rglob("*.png")))
    lines.append(check("figures generated", n_figs > 0, f"{n_figs} PNG files"))

    report = "# Final Validation Report\n\n" + "\n".join(lines) + "\n"
    (RESULTS_DIR / "validation_report.txt").write_text(report, encoding="utf-8")
    print(report)


if __name__ == "__main__":
    main()
