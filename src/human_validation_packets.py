"""Section 22: human interpretation packets + blank rating sheets. The system generating this
(Claude, an AI) is not a substitute for independent human raters and does not fabricate
ratings. It drafts the interpretation material and a provisional label explicitly marked as
an AI draft; the coherence/interpretability/distinctiveness ratings and word/document
intrusion results are left blank for at least two independent human evaluators to complete.
"""
import json
from pathlib import Path

import numpy as np
import pandas as pd
from gensim.models import LdaModel

import sys
sys.path.insert(0, str(Path(__file__).resolve().parent))
from lda_core import build_bow_corpus, build_dictionary, compute_frex, doc_topic_matrix

ROOT = Path(__file__).resolve().parents[1]
MODELS_DIR = ROOT / "models"
PREP_DIR = ROOT / "preprocessing"
DATA_DIR = ROOT / "data"
HV_DIR = ROOT / "human_validation"


def build_packets(label: str, k: int, seed: int, no_below: int, no_above: float, top_loading_n=10):
    model = LdaModel.load(str(MODELS_DIR / label / f"k{k:02d}_seed{seed:02d}.model"))
    with open(PREP_DIR / label / "lemmatized_tokens_corrected.json", encoding="utf-8") as f:
        doc_tokens = json.load(f)
    study_ids = list(doc_tokens.keys())
    token_lists = [doc_tokens[s] for s in study_ids]
    dictionary = build_dictionary(token_lists, no_below, no_above)
    bow = build_bow_corpus(token_lists, dictionary)
    dt = doc_topic_matrix(model, bow)

    meta = pd.read_csv(DATA_DIR / "metadata_representation.csv").set_index("Study_ID")
    frex_topics, _ = compute_frex(model)

    out_dir = HV_DIR / label
    out_dir.mkdir(parents=True, exist_ok=True)

    sheet_rows = []
    for t in range(model.num_topics):
        top_prob_terms = [w for w, _ in model.show_topic(t, topn=20)]
        top_frex_terms = [w for w, _ in frex_topics[t]]
        loadings = dt[:, t]
        top_idx = np.argsort(-loadings)[:top_loading_n]
        top_studies = [(study_ids[i], meta.loc[study_ids[i], "title"] if study_ids[i] in meta.index else "",
                        float(loadings[i])) for i in top_idx]
        prevalence = float(loadings.mean())

        packet = {
            "representation": label, "topic_id": t, "k": k, "medoid_seed": seed,
            "top_20_probability_terms": top_prob_terms,
            "top_20_frex_terms": top_frex_terms,
            "top_loading_studies": [
                {"Study_ID": sid, "title": ti, "topic_probability": round(p, 4)}
                for sid, ti, p in top_studies
            ],
            "prevalence_mean_probability": round(prevalence, 4),
            "ai_draft_label": "[AI-DRAFT - NOT A VALIDATED HUMAN LABEL]",
            "ai_draft_description": (
                "[AI-DRAFT - NOT A VALIDATED HUMAN LABEL] Provisional reading based on the "
                "top probability/FREX terms and top-loading study titles above, provided only "
                "to speed up human rater orientation. Must not be used in the manuscript until "
                "ratified or replaced by human raters."
            ),
        }
        with open(out_dir / f"topic_{t:02d}_packet.json", "w", encoding="utf-8") as f:
            json.dump(packet, f, indent=2)

        sheet_rows.append({
            "topic_id": t,
            "top_20_probability_terms": ", ".join(top_prob_terms),
            "top_20_frex_terms": ", ".join(top_frex_terms),
            "top_loading_studies": "; ".join(f"{sid} ({ti})" for sid, ti, _ in top_studies),
            "rater_id": "", "proposed_label": "", "short_description": "",
            "coherence_rating_1_5": "", "interpretability_rating_1_5": "",
            "distinctiveness_rating_1_5": "", "incoherent_topic_flag": "",
            "word_intrusion_result": "", "document_intrusion_result": "", "notes": "",
        })

    sheet_df = pd.DataFrame(sheet_rows)
    for rater in ["rater1", "rater2"]:
        sheet_df.to_csv(out_dir / f"topic_rating_sheet_{rater}.csv", index=False)

    print(f"[{label}] wrote {model.num_topics} topic packets + rating sheets to {out_dir}")
    return sheet_df


if __name__ == "__main__":
    import argparse
    ap = argparse.ArgumentParser()
    ap.add_argument("label"); ap.add_argument("k", type=int); ap.add_argument("seed", type=int)
    ap.add_argument("no_below", type=int); ap.add_argument("no_above", type=float)
    args = ap.parse_args()
    build_packets(args.label, args.k, args.seed, args.no_below, args.no_above)
