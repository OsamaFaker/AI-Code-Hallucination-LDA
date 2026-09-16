"""Freeze task Section 25: automated repository validator. Every check reports PASS/FAIL;
none are silently skipped. Writes results/validation_report.txt.
"""
import json
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
RESULTS_DIR = ROOT / "results"
HV_DIR = ROOT / "human_validation"

LINES = []


def check(label, condition, detail=""):
    status = "PASS" if condition else "FAIL"
    LINES.append(f"[{status}] {label}" + (f" - {detail}" if detail else ""))
    return bool(condition)


def main():
    all_pass = True

    manifest = pd.read_csv(ROOT / "corpus" / "primary_studies_manifest.csv")
    all_pass &= check("N = 66", len(manifest) == 66, f"N={len(manifest)}")
    all_pass &= check("No secondary studies in corpus",
                       (manifest["primary_secondary_classification"] == "Primary").all())

    meta = pd.read_csv(ROOT / "data" / "metadata_representation.csv")
    all_pass &= check("Metadata documents = 66", len(meta) == 66, f"N={len(meta)}")
    ft = pd.read_csv(ROOT / "data" / "fulltext_representation_manifest.csv")
    all_pass &= check("Full-text documents = 66", len(ft) == 66, f"N={len(ft)}")

    with open(RESULTS_DIR / "metadata" / "k_selection_decision.json", encoding="utf-8") as f:
        ksel_m = json.load(f)
    with open(RESULTS_DIR / "fulltext" / "k_selection_decision.json", encoding="utf-8") as f:
        ksel_f = json.load(f)
    all_pass &= check("Metadata final k = 4", ksel_m["selected_k"] == 4, f"k={ksel_m['selected_k']}")
    all_pass &= check("Full-text final k = 8", ksel_f["selected_k"] == 8, f"k={ksel_f['selected_k']}")

    with open(RESULTS_DIR / "metadata" / "representative_seed_k04.json", encoding="utf-8") as f:
        med_m = json.load(f)
    with open(RESULTS_DIR / "fulltext" / "representative_seed_k08.json", encoding="utf-8") as f:
        med_f = json.load(f)
    all_pass &= check("Metadata medoid seed = 14", med_m["medoid_seed"] == 14)
    all_pass &= check("Full-text medoid seed = 2", med_f["medoid_seed"] == 2)

    for label in ["metadata", "fulltext"]:
        runs = pd.read_csv(RESULTS_DIR / label / "definitive_ksweep_runs.csv")
        counts = runs.groupby("k").size()
        all_pass &= check(f"[{label}] 20 seeds per k", (counts == 20).all(),
                           f"min={counts.min()} max={counts.max()}")
        all_pass &= check(f"[{label}] 380 definitive models", len(runs) == 380, f"n={len(runs)}")

    all_pass &= check("Metadata candidate comparison (k=2-5) exists",
                       (RESULTS_DIR / "metadata" / "k2_k5_candidate_comparison.csv").exists())
    all_pass &= check("Full-text cross-k persistence exists",
                       (RESULTS_DIR / "fulltext" / "cross_k_topic_persistence.csv").exists())

    hv_files = [
        HV_DIR / "metadata_human_model_scores.csv",
        HV_DIR / "metadata_human_overall_preferences.csv",
        HV_DIR / "fulltext_human_ratings_per_topic.csv",
        HV_DIR / "FINAL_TOPIC_LABELS.csv",
    ]
    for p in hv_files:
        all_pass &= check(f"Human-validation file exists: {p.name}", p.exists())

    with open(RESULTS_DIR / "FROZEN_FINAL_VALUES.json", encoding="utf-8") as f:
        frozen = json.load(f)
    all_pass &= check("Frozen values verification status recorded",
                       frozen["freeze_status"].startswith("VERIFIED"))

    for label, k in [("metadata", 4), ("fulltext", 8)]:
        with open(RESULTS_DIR / label / f"representative_seed_k{k:02d}.json", encoding="utf-8") as f:
            med = json.load(f)
        seed = med["medoid_seed"]
        from gensim.models import LdaModel
        import sys
        sys.path.insert(0, str(ROOT / "src"))
        from lda_core import build_bow_corpus, build_dictionary, doc_topic_matrix
        with open(ROOT / "preprocessing" / label / "lemmatized_tokens_corrected.json", encoding="utf-8") as f:
            toks = json.load(f)
        no_below, no_above = (5, 0.50) if label == "metadata" else (4, 0.75)
        dictionary = build_dictionary(list(toks.values()), no_below, no_above)
        bow = build_bow_corpus(list(toks.values()), dictionary)
        model = LdaModel.load(str(ROOT / "models" / label / f"k{k:02d}_seed{seed:02d}.model"))
        dt = doc_topic_matrix(model, bow)
        dominant_counts = pd.Series(dt.argmax(axis=1)).value_counts().sum()
        all_pass &= check(f"[{label}] dominant-topic counts sum to 66", dominant_counts == 66,
                           f"sum={dominant_counts}")
        prevalence_sum = dt.mean(axis=0).sum()
        all_pass &= check(f"[{label}] topic prevalence sums to ~1", abs(prevalence_sum - 1.0) < 0.01,
                           f"sum={prevalence_sum:.4f}")

    n_figs = len(list((ROOT / "figures").rglob("*.png")))
    all_pass &= check("Figures exist", n_figs > 0, f"{n_figs} PNG files")
    fig_registry = pd.read_csv(RESULTS_DIR / "figure_registry_full.csv")
    missing_figs = [f for f in fig_registry.Filename if not (ROOT / f).exists()]
    all_pass &= check("All registered figures exist on disk", len(missing_figs) == 0,
                       f"{len(missing_figs)} missing" if missing_figs else "")
    all_pass &= check("Figure SHA-256 checksums exist",
                       (ROOT / "figures" / "FIGURE_SHA256.csv").exists())

    transfer = (ROOT / "reports" / "FINAL_MANUSCRIPT_TRANSFER_TABLE.md")
    all_pass &= check("Manuscript transfer table exists", transfer.exists())

    # --- Label reconciliation checks ---
    labels_df = pd.read_csv(HV_DIR / "FINAL_TOPIC_LABELS.csv")
    all_pass &= check("Final topic labels populated (4 metadata + 8 fulltext)",
                       len(labels_df) == 12, f"{len(labels_df)} rows")
    n_pending = (labels_df["Final_Reconciled_Label"] == "Pending researcher reconciliation").sum()
    all_pass &= check("No topic labels remain 'Pending researcher reconciliation'",
                       n_pending == 0, f"{n_pending} still pending")
    n_ai_draft_final = labels_df["Final_Reconciled_Label"].astype(str).str.contains(
        "AI-DRAFT", case=False).sum()
    all_pass &= check("No AI-DRAFT marker in final reconciled labels", n_ai_draft_final == 0)
    all_pass &= check("Reconciliation status correctly labeled (not 'Rater consensus')",
                       (labels_df["Reconciliation_Status"] ==
                        "Researcher reconciled after independent human rating").all())
    all_pass &= check("Label reconciliation report exists",
                       (ROOT / "reports" / "TOPIC_LABEL_RECONCILIATION.md").exists())

    # --- Raw human-rating files present and untouched by this task ---
    raw_rater_files = [
        HV_DIR / "Human_Result" / "Metadata" / "2" / "candidate_rating_sheet_rater1_completed.csv",
        HV_DIR / "Human_Result" / "Metadata" / "files" / "candidate_rating_sheet_rater2.csv",
        HV_DIR / "Human_Result" / "Full_Text" / "candidate_rating_sheet_rater1_evaluated.csv",
        HV_DIR / "Human_Result" / "Full_Text" / "files" / "candidate_rating_sheet_rater2.csv",
    ]
    for p in raw_rater_files:
        all_pass &= check(f"Raw rater file present: {p.name}", p.exists())

    # --- models/ intentionally git-ignored + regeneration command documented ---
    gitignore_text = (ROOT / ".gitignore").read_text(encoding="utf-8")
    all_pass &= check("models/ present in .gitignore", "models/" in gitignore_text)
    readme_text = (ROOT / "README.md").read_text(encoding="utf-8")
    all_pass &= check("README documents the models/ regeneration command",
                       "definitive_k_sweep.py" in readme_text and "git-ignored" in readme_text)
    provenance = (RESULTS_DIR / "RESULT_PROVENANCE.csv")
    if provenance.exists():
        prov_df = pd.read_csv(provenance)
        all_pass &= check("Result provenance file populated", len(prov_df) > 0, f"{len(prov_df)} rows")
    else:
        all_pass &= check("Result provenance file populated", False, "file not found")

    report = "# Repository Validation Report\n\n" + "\n".join(LINES) + \
             f"\n\nOVERALL: {'ALL CHECKS PASS' if all_pass else 'ONE OR MORE CHECKS FAILED'}\n"
    (RESULTS_DIR / "validation_report.txt").write_text(report, encoding="utf-8")
    print(report)
    return all_pass


if __name__ == "__main__":
    ok = main()
    raise SystemExit(0 if ok else 1)
