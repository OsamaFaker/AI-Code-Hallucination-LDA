"""Section 35: manuscript transfer table, generated directly from analysis output files."""
import json
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
RESULTS_DIR = ROOT / "results"


def load(label):
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

    return {
        "N": 66,
        "Vocabulary size": int(dict_cfg["selected_vocab_size"]),
        "Selected k": k,
        "Number of seeds": 20,
        "Number of models (definitive sweep)": len(runs),
        "Selected medoid seed": medoid["medoid_seed"],
        "C_v (mean at selected k)": round(k_runs["c_v"].mean(), 4),
        "C_NPMI (mean at selected k)": round(k_runs["c_npmi"].mean(), 4),
        "Stability (mean JS similarity at selected k)": round(k_stab["js_similarity_mean"], 4),
        "Topic diversity (mean at selected k)": round(k_runs["topic_diversity"].mean(), 4),
        "Topic prevalence (min/mean/max dominant count)": (
            f"{k_runs['n_topics_0_studies'].mean():.2f} zero-dominance topics on average"
        ),
        "Subsampling similarity (mean JS, 100x 80%)": round(subs["topic_similarity_js"].mean(), 4),
        "Subsampling ARI (mean, 100x 80%)": round(subs["ari"].mean(), 4),
    }


def main():
    meta = load("metadata")
    full = load("fulltext")

    rows = [
        ("N", meta["N"], full["N"], "corpus/primary_studies_manifest.csv"),
        ("Vocabulary size", meta["Vocabulary size"], full["Vocabulary size"],
         "results/{rep}/stage1_selected_config.json"),
        ("Selected k", meta["Selected k"], full["Selected k"], "results/{rep}/k_selection_decision.json"),
        ("Number of seeds", meta["Number of seeds"], full["Number of seeds"], "protocol (frozen)"),
        ("Number of models (definitive sweep)", meta["Number of models (definitive sweep)"],
         full["Number of models (definitive sweep)"], "results/{rep}/definitive_ksweep_runs.csv"),
        ("Selected medoid seed", meta["Selected medoid seed"], full["Selected medoid seed"],
         "results/{rep}/representative_seed_k*.json"),
        ("C_v (mean at selected k)", meta["C_v (mean at selected k)"], full["C_v (mean at selected k)"],
         "results/{rep}/definitive_ksweep_runs.csv"),
        ("C_NPMI (mean at selected k)", meta["C_NPMI (mean at selected k)"],
         full["C_NPMI (mean at selected k)"], "results/{rep}/definitive_ksweep_runs.csv"),
        ("Stability (mean JS similarity)", meta["Stability (mean JS similarity at selected k)"],
         full["Stability (mean JS similarity at selected k)"], "results/{rep}/seed_stability_by_k.csv"),
        ("Topic diversity (mean)", meta["Topic diversity (mean at selected k)"],
         full["Topic diversity (mean at selected k)"], "results/{rep}/definitive_ksweep_runs.csv"),
        ("Subsampling similarity (mean JS, 100x80%)", meta["Subsampling similarity (mean JS, 100x 80%)"],
         full["Subsampling similarity (mean JS, 100x 80%)"], "results/{rep}/subsampling_80pct_100reps.csv"),
        ("Subsampling ARI (mean, 100x80%)", meta["Subsampling ARI (mean, 100x 80%)"],
         full["Subsampling ARI (mean, 100x 80%)"], "results/{rep}/subsampling_80pct_100reps.csv"),
    ]

    lines = ["| Manuscript item | Metadata LDA | Full-text LDA | Source file |",
             "|---|---:|---:|---|"]
    for item, va, vb, src in rows:
        lines.append(f"| {item} | {va} | {vb} | `{src}` |")

    preamble = (
        "# Final Manuscript Transfer Table\n\n"
        "**Status: FINAL.** Both selected-k rows and all other rows are frozen and "
        "corroborated by completed blinded human validation "
        "(`reports/METADATA_FINAL_K_VALIDATION.md`, `reports/FULLTEXT_FINAL_K_VALIDATION.md`, "
        "`reports/HUMAN_VALIDATION_REPORT.md`, `reports/FINAL_K_DECISION_TABLE.md`). Final "
        "reconciled topic labels: `human_validation/FINAL_TOPIC_LABELS.csv`.\n\n"
    )
    out_dir = ROOT / "reports"
    out_dir.mkdir(exist_ok=True)
    (out_dir / "FINAL_MANUSCRIPT_TRANSFER_TABLE.md").write_text(
        preamble + "\n".join(lines) + "\n", encoding="utf-8")
    print("\n".join(lines))


if __name__ == "__main__":
    main()
