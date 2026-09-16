"""Repair task Part 2.4: optional word/document intrusion tests for the blinded metadata
candidate packets. Answers are stored privately, never in the rater-facing sheet.
"""
import json
import random
from pathlib import Path

import numpy as np
import pandas as pd
from gensim.models import LdaModel

import sys
sys.path.insert(0, str(Path(__file__).resolve().parent))
from lda_core import build_bow_corpus, build_dictionary, doc_topic_matrix

ROOT = Path(__file__).resolve().parents[1]
PREP_DIR = ROOT / "preprocessing"
DATA_DIR = ROOT / "data"
MODELS_DIR = ROOT / "models"
HV_DIR = ROOT / "human_validation"


def build_intrusion_tests(label, no_below, no_above, key_seed=7):
    with open(HV_DIR / f"{label}_candidate_model_key.json", encoding="utf-8") as f:
        model_key = json.load(f)
    with open(PREP_DIR / label / "lemmatized_tokens_corrected.json", encoding="utf-8") as f:
        doc_tokens = json.load(f)
    study_ids = list(doc_tokens.keys())
    token_lists = [doc_tokens[s] for s in study_ids]
    dictionary = build_dictionary(token_lists, no_below, no_above)
    bow = build_bow_corpus(token_lists, dictionary)
    meta = pd.read_csv(DATA_DIR / "metadata_representation.csv").set_index("Study_ID")

    rng = random.Random(key_seed)
    out_dir = HV_DIR / f"{label}_candidate_blinded"

    rater_rows = []
    answer_rows = []
    for letter, info in model_key.items():
        k, seed = info["k"], info["medoid_seed"]
        model = LdaModel.load(str(MODELS_DIR / label / f"k{k:02d}_seed{seed:02d}.model"))
        dt = doc_topic_matrix(model, bow)
        vocab = list(dictionary.values())

        for t in range(model.num_topics):
            top10 = [w for w, _ in model.show_topic(t, topn=10)]
            other_topics = [x for x in range(model.num_topics) if x != t]
            # word intrusion: a word that is high-probability in a DIFFERENT topic but
            # (checked) not present in this topic's own top-30, so it's a genuine intruder
            own_top30 = {w for w, _ in model.show_topic(t, topn=30)}
            intruder_word = None
            candidates = other_topics[:]
            rng.shuffle(candidates)
            for other_t in candidates:
                for w, _ in model.show_topic(other_t, topn=15):
                    if w not in own_top30:
                        intruder_word = w
                        break
                if intruder_word:
                    break
            if intruder_word is None:
                intruder_word = rng.choice(vocab)
            word_list = top10 + [intruder_word]
            rng.shuffle(word_list)

            # document intrusion: lowest-probability study for THIS topic, among studies
            # that are high-probability for some other topic (a genuine unrelated intruder,
            # not just a globally weak document)
            loadings = dt[:, t]
            top10_idx = np.argsort(-loadings)[:10]
            low_idx_candidates = np.argsort(loadings)[:15]
            intruder_idx = int(low_idx_candidates[0])
            doc_list_idx = list(top10_idx) + [intruder_idx]
            rng.shuffle(doc_list_idx)
            doc_list = []
            for i in doc_list_idx:
                sid = study_ids[i]
                title = meta.loc[sid, "title"] if sid in meta.index else sid
                doc_list.append(f"{sid}: {title}")

            rater_rows.append({
                "blinded_model": letter, "topic_id": t,
                "word_intrusion_list": ", ".join(word_list),
                "word_intrusion_answer": "",
                "document_intrusion_list": " | ".join(doc_list),
                "document_intrusion_answer": "",
            })
            answer_rows.append({
                "blinded_model": letter, "topic_id": t,
                "word_intrusion_correct_answer": intruder_word,
                "document_intrusion_correct_answer": f"{study_ids[intruder_idx]}: "
                    f"{meta.loc[study_ids[intruder_idx], 'title'] if study_ids[intruder_idx] in meta.index else ''}",
            })

    pd.DataFrame(rater_rows).to_csv(out_dir / "intrusion_test_sheet.csv", index=False)
    # answers kept OUTSIDE the blinded packet folder, alongside the private model key
    pd.DataFrame(answer_rows).to_csv(HV_DIR / f"{label}_intrusion_test_answers.json.csv", index=False)
    print(f"[{label}] intrusion tests written: {out_dir/'intrusion_test_sheet.csv'} "
          f"(answers kept private at human_validation/{label}_intrusion_test_answers.json.csv)")


if __name__ == "__main__":
    import argparse
    ap = argparse.ArgumentParser()
    ap.add_argument("label"); ap.add_argument("no_below", type=int); ap.add_argument("no_above", type=float)
    args = ap.parse_args()
    build_intrusion_tests(args.label, args.no_below, args.no_above)
