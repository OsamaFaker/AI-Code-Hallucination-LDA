"""Repair task Part 2: blinded candidate-model packets for human rating. No AI-drafted labels
are shown; k values and prior model-selection decisions are not exposed. Model identity is
scrambled to random letters with a privately-held key.
"""
import json
import random
from pathlib import Path

import numpy as np
import pandas as pd
from gensim.models import LdaModel

import sys
sys.path.insert(0, str(Path(__file__).resolve().parent))
from lda_core import build_bow_corpus, build_dictionary, compute_frex, doc_topic_matrix

ROOT = Path(__file__).resolve().parents[1]
PREP_DIR = ROOT / "preprocessing"
DATA_DIR = ROOT / "data"
RESULTS_DIR = ROOT / "results"
MODELS_DIR = ROOT / "models"
HV_DIR = ROOT / "human_validation"

LETTERS = ["A", "B", "C", "D", "E", "F", "G", "H", "I", "J"]


def build_blinded_packets(label, k_values, no_below, no_above, key_seed=42):
    with open(PREP_DIR / label / "lemmatized_tokens_corrected.json", encoding="utf-8") as f:
        doc_tokens = json.load(f)
    study_ids = list(doc_tokens.keys())
    token_lists = [doc_tokens[s] for s in study_ids]
    dictionary = build_dictionary(token_lists, no_below, no_above)
    bow = build_bow_corpus(token_lists, dictionary)
    meta = pd.read_csv(DATA_DIR / "metadata_representation.csv").set_index("Study_ID")

    rng = random.Random(key_seed)
    shuffled_letters = LETTERS[:len(k_values)]
    rng.shuffle(shuffled_letters)
    model_key = {}

    out_dir = HV_DIR / f"{label}_candidate_blinded"
    out_dir.mkdir(parents=True, exist_ok=True)

    all_rows_by_model = {}
    for letter, k in zip(shuffled_letters, k_values):
        with open(RESULTS_DIR / label / f"representative_seed_k{k:02d}.json", encoding="utf-8") as f:
            med = json.load(f)
        seed = med["medoid_seed"]
        model = LdaModel.load(str(MODELS_DIR / label / f"k{k:02d}_seed{seed:02d}.model"))
        model_key[letter] = {"k": k, "medoid_seed": seed}

        dt = doc_topic_matrix(model, bow)
        frex_topics, _ = compute_frex(model)

        sheet_rows = []
        for t in range(model.num_topics):
            top_prob = [w for w, _ in model.show_topic(t, topn=20)]
            top_frex = [w for w, _ in frex_topics[t]]
            loadings = dt[:, t]
            top_idx = np.argsort(-loadings)[:10]
            top_studies = []
            for i in top_idx:
                sid = study_ids[i]
                title = meta.loc[sid, "title"] if sid in meta.index else ""
                abstract = meta.loc[sid, "abstract"] if sid in meta.index else ""
                top_studies.append({
                    "Study_ID": sid, "title": title,
                    "abstract": str(abstract)[:600],
                    "topic_probability": round(float(loadings[i]), 4),
                })
            packet = {
                "blinded_model": letter, "blinded_topic_id": t,
                "top_20_probability_terms": top_prob,
                "top_20_frex_terms": top_frex,
                "top_loading_studies": top_studies,
                "prevalence_mean_probability": round(float(loadings.mean()), 4),
            }
            with open(out_dir / f"Model_{letter}_topic_{t:02d}_packet.json", "w", encoding="utf-8") as f:
                json.dump(packet, f, indent=2)
            sheet_rows.append({
                "blinded_model": letter, "topic_id": t,
                "top_20_probability_terms": ", ".join(top_prob),
                "top_20_frex_terms": ", ".join(top_frex),
                "top_loading_studies": "; ".join(f"{s['Study_ID']} ({s['title']})" for s in top_studies),
                "proposed_label": "", "short_description": "",
                "coherence_1_5": "", "interpretability_1_5": "", "distinctiveness_1_5": "",
                "topic_validity_flag": "",  # coherent / partially coherent / incoherent
                "word_intrusion_correct": "", "document_intrusion_correct": "", "notes": "",
            })
        all_rows_by_model[letter] = sheet_rows

    # combined, shuffled-model-order rating sheet per rater (topics within each model kept
    # together and in order, but models are already letter-randomized so no k leaks through)
    combined = []
    for letter in shuffled_letters:
        combined.extend(all_rows_by_model[letter])
    for rater in ["rater1", "rater2"]:
        pd.DataFrame(combined).to_csv(out_dir / f"candidate_rating_sheet_{rater}.csv", index=False)

    # model-level question sheet (Part 2.3)
    model_level_rows = [{
        "blinded_model": letter,
        "rater_id": "",
        "contains_redundant_topics": "",
        "merges_different_themes": "",
        "splits_one_theme_unnecessarily": "",
        "every_topic_substantively_meaningful": "",
        "notes": "",
    } for letter in shuffled_letters]
    for rater in ["rater1", "rater2"]:
        pd.DataFrame(model_level_rows).to_csv(out_dir / f"model_level_questions_{rater}.csv", index=False)
    pd.DataFrame([{"rater_id": "", "clearest_balance_model": "", "reasoning": ""}]).to_csv(
        out_dir / "overall_preference_sheet_template.csv", index=False)

    # PRIVATE key - not for rater eyes. Kept directly under human_validation/ (sibling of the
    # blinded packet folder, not inside it) so it is not accidentally bundled with materials
    # handed to raters.
    key_path = HV_DIR / f"{label}_candidate_model_key.json"
    with open(key_path, "w", encoding="utf-8") as f:
        json.dump(model_key, f, indent=2)

    print(f"[{label}] blinded packets for k={k_values} written to {out_dir}")
    print(f"[{label}] PRIVATE key: {key_path} -> {model_key}")
    return model_key


if __name__ == "__main__":
    import argparse
    ap = argparse.ArgumentParser()
    ap.add_argument("label")
    ap.add_argument("k_values")
    ap.add_argument("no_below", type=int)
    ap.add_argument("no_above", type=float)
    args = ap.parse_args()
    ks = [int(x) for x in args.k_values.split(",")]
    build_blinded_packets(args.label, ks, args.no_below, args.no_above)
