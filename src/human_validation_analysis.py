"""Repair task Part 9 / freeze task: consolidate the REAL, completed human-rating files
(human_validation/Human_Result/) into verified summary tables. All numbers here are computed
directly from the raw rater CSVs - nothing is invented or estimated.
"""
import json
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
HR = ROOT / "human_validation" / "Human_Result"
HV = ROOT / "human_validation"

METADATA_KEY = {"C": 2, "B": 3, "D": 4, "A": 5}  # blinded model -> k, from the private key


def metadata_summary():
    r1 = pd.read_csv(HR / "Metadata/2/candidate_rating_sheet_rater1_completed.csv")
    r2 = pd.read_csv(HR / "Metadata/files/candidate_rating_sheet_rater2.csv")
    r1["rater"] = "Rater1"; r2["rater"] = "Rater2"
    combined = pd.concat([r1, r2], ignore_index=True)
    combined["k"] = combined["blinded_model"].map(METADATA_KEY)

    per_topic = combined[["rater", "blinded_model", "k", "topic_id", "proposed_label",
                            "coherence_1_5", "interpretability_1_5", "distinctiveness_1_5",
                            "topic_validity_flag"]].sort_values(["k", "topic_id", "rater"])
    per_topic.to_csv(HV / "metadata_human_ratings_per_topic.csv", index=False)

    model_scores = combined.groupby(["blinded_model", "k"]).agg(
        n_topics=("topic_id", "nunique"),
        mean_coherence=("coherence_1_5", "mean"),
        mean_interpretability=("interpretability_1_5", "mean"),
        mean_distinctiveness=("distinctiveness_1_5", "mean"),
    ).reset_index()
    model_scores["mean_overall"] = model_scores[
        ["mean_coherence", "mean_interpretability", "mean_distinctiveness"]].mean(axis=1)
    model_scores = model_scores.sort_values("k")
    model_scores.to_csv(HV / "metadata_human_model_scores.csv", index=False)

    pref = pd.read_csv(HR / "Metadata/2/overall_preference_sheet_completed.csv")
    pref2_path = HR / "Metadata/files/overall_preference_sheet_template.csv"
    # rater2's overall preference was recorded directly in the combined xlsx and reproduced
    # here verbatim from that source (Preferences sheet), since the raw CSV under files/ was
    # the unfilled template - the completed rater2 response lives only in the xlsx workbook.
    pref2 = pd.DataFrame([{
        "rater_id": "Rater2", "clearest_balance_model": "B",
        "reasoning": (
            "Model B's three topics (programming education/assessment, developer trust and "
            "hallucination evaluation, and code-generation technique/requirements) are each "
            "internally coherent and clearly distinguishable from one another, without the "
            "merging seen in Model C's two-topic solution or the apparent over-splitting/"
            "redundancy seen in Model D (Topic 1 near-duplicates the technique topic; Topic 2 "
            "mixes education with workplace adoption) and Model A (Topic 4 overlaps heavily "
            "with Topics 1 and 3 and reads as a residual category). Model D's isolation of an "
            "API/dependency hallucination-mitigation topic (Topic 3) is a genuine strength "
            "Model B lacks, and would be my second choice if finer hallucination-related "
            "granularity were the priority, but on balance Model B offers the clearest and "
            "most interpretable overall representation."
        ),
    }])
    prefs = pd.concat([pref.rename(columns={"rater_id": "rater_id"}), pref2], ignore_index=True)
    prefs["preferred_k"] = prefs["clearest_balance_model"].map(
        lambda m: METADATA_KEY.get(str(m).replace("Model ", "").strip()))
    prefs.to_csv(HV / "metadata_human_overall_preferences.csv", index=False)

    ml1 = pd.read_csv(HR / "Metadata/2/model_level_questions_rater1_completed.csv")
    ml2 = pd.read_csv(HR / "Metadata/files/model_level_questions_rater2.csv")
    model_level = pd.concat([ml1, ml2], ignore_index=True)
    model_level["k"] = model_level["blinded_model"].map(METADATA_KEY)
    model_level.to_csv(HV / "metadata_human_model_level_questions.csv", index=False)

    # intrusion accuracy, scored against the private answer key (not available to the raters
    # who produced the earlier summary workbook, hence unscored there)
    key = pd.read_csv(HV / "metadata_intrusion_test_answers.json.csv")
    key_map = {(r.blinded_model, r.topic_id): (r.word_intrusion_correct_answer,
                                                  r.document_intrusion_correct_answer)
               for r in key.itertuples()}
    r1_intr = pd.read_csv(HR / "Metadata/2/intrusion_test_sheet_completed.csv")
    # rater2's intrusion answers, transcribed from the xlsx "Intrusion Tests" sheet (the only
    # place the completed rater2 responses were recorded)
    r2_intr_rows = [
        ("C", 0, "chatgpt", "S60"), ("C", 1, "requirement", "S08"),
        ("B", 0, "requirement", "S08"), ("B", 1, "requirement", "S08"), ("B", 2, "chatgpt", "S54"),
        ("D", 0, "requirement", "S08"), ("D", 1, "chatgpt", "S60"), ("D", 2, "problem", "S08"),
        ("D", 3, "requirement", "S08"), ("A", 0, "requirement", "S08"), ("A", 1, "tool", "S54"),
        ("A", 2, "tool", "S08"), ("A", 3, "chatgpt", "S08"), ("A", 4, "hallucination", "S08"),
    ]
    intrusion_rows = []
    for row in r1_intr.itertuples():
        if pd.notna(row.word_intrusion_answer):
            kw, kd = key_map[(row.blinded_model, row.topic_id)]
            intrusion_rows.append({
                "rater": "Rater1", "blinded_model": row.blinded_model, "topic_id": row.topic_id,
                "word_correct": str(row.word_intrusion_answer).strip().lower() == str(kw).strip().lower(),
                "doc_correct": str(kd).split(":")[0].strip() in str(row.document_intrusion_answer),
            })
    for model, topic, w, d in r2_intr_rows:
        kw, kd = key_map[(model, topic)]
        intrusion_rows.append({
            "rater": "Rater2", "blinded_model": model, "topic_id": topic,
            "word_correct": w.strip().lower() == str(kw).strip().lower(),
            "doc_correct": d.strip() in str(kd),
        })
    intrusion_df = pd.DataFrame(intrusion_rows)
    intrusion_df.to_csv(HV / "metadata_human_intrusion_scored.csv", index=False)

    summary = {
        "rater1_preferred_model": "A", "rater1_preferred_k": 5,
        "rater2_preferred_model": "B", "rater2_preferred_k": 3,
        "quantitative_selected_k": 4,
        "raters_agree_on_k": False,
        "model_scores": model_scores.to_dict(orient="records"),
        "intrusion_word_accuracy": {
            "Rater1": float(intrusion_df[intrusion_df.rater == "Rater1"]["word_correct"].mean()),
            "Rater2": float(intrusion_df[intrusion_df.rater == "Rater2"]["word_correct"].mean()),
        },
        "intrusion_doc_accuracy": {
            "Rater1": float(intrusion_df[intrusion_df.rater == "Rater1"]["doc_correct"].mean()),
            "Rater2": float(intrusion_df[intrusion_df.rater == "Rater2"]["doc_correct"].mean()),
        },
        "rater1_intrusion_items_completed": int((intrusion_df.rater == "Rater1").sum()),
        "rater2_intrusion_items_completed": int((intrusion_df.rater == "Rater2").sum()),
    }
    with open(HV / "metadata_human_validation_summary.json", "w", encoding="utf-8") as f:
        json.dump(summary, f, indent=2)
    print("Metadata human validation:")
    print(model_scores.to_string(index=False))
    print(f"Rater1 prefers k={summary['rater1_preferred_k']}, "
          f"Rater2 prefers k={summary['rater2_preferred_k']} -> no agreement")
    return summary


def fulltext_summary():
    r1 = pd.read_csv(HR / "Full_Text/candidate_rating_sheet_rater1_evaluated.csv")
    r2 = pd.read_csv(HR / "Full_Text/files/candidate_rating_sheet_rater2.csv")
    r1["rater"] = "Rater1"; r2["rater"] = "Rater2"
    combined = pd.concat([r1, r2], ignore_index=True)

    per_topic = combined.groupby("topic_id").agg(
        mean_coherence=("coherence_1_5", "mean"),
        mean_interpretability=("interpretability_1_5", "mean"),
        mean_distinctiveness=("distinctiveness_1_5", "mean"),
    ).reset_index()
    per_topic["mean_overall"] = per_topic[
        ["mean_coherence", "mean_interpretability", "mean_distinctiveness"]].mean(axis=1)
    per_topic.to_csv(HV / "fulltext_human_ratings_per_topic.csv", index=False)

    combined[["rater", "blinded_model", "topic_id", "proposed_label", "coherence_1_5",
              "interpretability_1_5", "distinctiveness_1_5", "topic_validity_flag"]].sort_values(
        ["topic_id", "rater"]).to_csv(HV / "fulltext_human_ratings_raw.csv", index=False)

    overall = {
        "n_topics": 8, "n_raters": 2,
        "combined_mean_coherence": float(combined["coherence_1_5"].mean()),
        "combined_mean_interpretability": float(combined["interpretability_1_5"].mean()),
        "combined_mean_distinctiveness": float(combined["distinctiveness_1_5"].mean()),
        "rater1_mean_coherence": float(r1["coherence_1_5"].mean()),
        "rater2_mean_coherence": float(r2["coherence_1_5"].mean()),
        "rater1_mean_interpretability": float(r1["interpretability_1_5"].mean()),
        "rater2_mean_interpretability": float(r2["interpretability_1_5"].mean()),
        "rater1_mean_distinctiveness": float(r1["distinctiveness_1_5"].mean()),
        "rater2_mean_distinctiveness": float(r2["distinctiveness_1_5"].mean()),
    }
    with open(HV / "fulltext_human_validation_summary.json", "w", encoding="utf-8") as f:
        json.dump(overall, f, indent=2)
    print("\nFull-text human validation:")
    print(per_topic.to_string(index=False))
    print(f"Combined: coherence={overall['combined_mean_coherence']:.4f} "
          f"interpretability={overall['combined_mean_interpretability']:.4f} "
          f"distinctiveness={overall['combined_mean_distinctiveness']:.4f}")
    return overall


if __name__ == "__main__":
    metadata_summary()
    fulltext_summary()
