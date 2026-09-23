"""
STAGE 6 -- Semantic interpretation packets and blinded human-evaluation
packets (PRE_EXECUTION_ANALYSIS_PLAN.md SS14).

INTERNAL interpretation packets (analyst-facing, not shown to raters): per
finalist topic, top-20 probability terms, top-20 FREX/exclusive terms, 10
highest-loading studies (title, abstract, probability), probability-based
prevalence, neutral Topic 0/1/... labels.

RATER-FACING blinded comparison packets: derived from the internal packets
with prevalence and ALL quantitative information stripped -- only top-20
probability terms, top-20 FREX terms, and the 10 highest-loading studies'
titles/abstracts. Withheld: the numeric k label, seed, dictionary/prior/
training configuration, all quantitative metrics, and model identity (models
randomized to Model A/B/C, extended to D for a 4th finalist; topics
randomized in order within each model). What is NOT claimed to be hidden:
the number of topics in a given candidate model is inherently visible by
counting the packet's sections -- only the *label* k and the metrics behind
it are withheld, not the observable topic count (see plan SS14).

The Model-A/B/C/D <-> real-k mapping is written to a SEPARATE, analyst-only
answer key, never included in the rater-facing file.

FREX score (Roberts et al. 2014 convention): harmonic mean of a word's
frequency-percentile and exclusivity-percentile within a topic, weighted
0.3/0.7 toward exclusivity.

No LDA fitting beyond refitting each finalist's own medoid seed (already
fitted in Stage 4/5; refit here since gensim models aren't persisted to disk
between stages).
"""

from __future__ import annotations

import csv
import sys
import random
from pathlib import Path

import numpy as np
from gensim.corpora import Dictionary

sys.path.insert(0, str(Path(__file__).parent))
from preprocessing import preprocess_variant, get_plural_merge_map
from lda_utils import fit_lda, topic_word_matrix
from stage1_select import load_sweep, decide_variant
from stage1_sweep import load_metadata_texts, load_fulltext_texts
from stage2_select import select_convergence, select_priors
from stage4_select import load_k_summary, pareto_optimal_set, reduce_to_finalists

ROOT = Path(__file__).resolve().parents[1]
TOP_N_TERMS = 20
TOP_N_STUDIES = 10
FREX_EXCLUSIVITY_WEIGHT = 0.7
PACKET_RANDOM_SEED = 2024


def load_titles_abstracts():
    with open(ROOT / "corpus" / "metadata_documents.csv", newline="", encoding="utf-8") as f:
        rows = {r["Study_ID"]: r for r in csv.DictReader(f)}
    return rows


def percentile_rank(values: np.ndarray) -> np.ndarray:
    order = values.argsort()
    ranks = np.empty_like(order, dtype=float)
    ranks[order] = np.arange(len(values))
    return ranks / (len(values) - 1) if len(values) > 1 else np.zeros_like(ranks)


def frex_scores(topic_word: np.ndarray) -> np.ndarray:
    """topic_word: k x V row-normalized. Returns k x V FREX score matrix."""
    k, v = topic_word.shape
    col_sums = topic_word.sum(axis=0, keepdims=True)
    col_sums[col_sums == 0] = 1e-12
    exclusivity = topic_word / col_sums  # P(topic | word)

    frex = np.zeros((k, v))
    for t in range(k):
        freq_pct = percentile_rank(topic_word[t])
        excl_pct = percentile_rank(exclusivity[t])
        denom = (FREX_EXCLUSIVITY_WEIGHT / np.clip(excl_pct, 1e-6, 1)) + \
                ((1 - FREX_EXCLUSIVITY_WEIGHT) / np.clip(freq_pct, 1e-6, 1))
        frex[t] = 1.0 / denom
    return frex


def build_packet_data(representation: str, k: int, medoid_seed: int):
    rows = load_sweep(representation)
    d1 = decide_variant(representation, rows)
    fc = d1["final_config"]
    priors = select_priors(representation)
    conv = select_convergence(representation)

    if representation == "metadata":
        ids, texts = load_metadata_texts()
    else:
        ids, texts = load_fulltext_texts()
    plural_map = get_plural_merge_map(texts)
    tokens = preprocess_variant(texts, d1["chosen_hf"], d1["use_bigrams"], plural_map)
    dictionary = Dictionary(tokens)
    dictionary.filter_extremes(no_below=fc["no_below"], no_above=fc["no_above"])
    corpus = [dictionary.doc2bow(t) for t in tokens]

    model = fit_lda(corpus, dictionary, num_topics=k, seed=medoid_seed,
                     passes=conv["passes"], iterations=conv["iterations"],
                     alpha=priors["alpha"], eta=priors["eta"])
    tw = topic_word_matrix(model)
    frex = frex_scores(tw)

    doc_topic = np.zeros((len(ids), k))
    for i, bow in enumerate(corpus):
        for tid, p in model.get_document_topics(bow, minimum_probability=0.0):
            doc_topic[i, tid] = p
    prevalence = doc_topic.mean(axis=0)

    meta = load_titles_abstracts()

    topics = []
    for t in range(k):
        top_prob_idx = np.argsort(-tw[t])[:TOP_N_TERMS]
        top_prob_terms = [dictionary.id2token[i] for i in top_prob_idx]
        top_frex_idx = np.argsort(-frex[t])[:TOP_N_TERMS]
        top_frex_terms = [dictionary.id2token[i] for i in top_frex_idx]

        loadings = doc_topic[:, t]
        top_doc_idx = np.argsort(-loadings)[:TOP_N_STUDIES]
        top_studies = []
        for di in top_doc_idx:
            sid = ids[di]
            m = meta.get(sid, {})
            top_studies.append({
                "Study_ID": sid, "title": m.get("title", ""), "abstract": m.get("abstract", ""),
                "probability": round(float(loadings[di]), 4),
            })

        topics.append({
            "topic_index": t, "top_prob_terms": top_prob_terms, "top_frex_terms": top_frex_terms,
            "top_studies": top_studies, "prevalence": round(float(prevalence[t]), 5),
        })
    return topics


def write_internal_packet(representation: str, k: int, medoid_seed: int, topics: list[dict]) -> None:
    out_path = ROOT / "results" / representation / f"interpretation_packet_k{k}.md"
    with open(out_path, "w", encoding="utf-8") as f:
        f.write(f"# Internal Interpretation Packet -- {representation}, k={k} "
                f"(medoid seed={medoid_seed})\n\n")
        f.write("Analyst-facing only -- NOT shown to raters (contains prevalence/quantitative info).\n\n")
        for topic in topics:
            f.write(f"## Topic {topic['topic_index']}\n\n")
            f.write(f"- Probability-based prevalence: {topic['prevalence']:.4f}\n")
            f.write(f"- Top-{TOP_N_TERMS} probability terms: {', '.join(topic['top_prob_terms'])}\n")
            f.write(f"- Top-{TOP_N_TERMS} FREX terms: {', '.join(topic['top_frex_terms'])}\n\n")
            f.write(f"### Top-{TOP_N_STUDIES} highest-loading studies\n\n")
            f.write("| Study_ID | probability | title |\n|---|---|---|\n")
            for s in topic["top_studies"]:
                f.write(f"| {s['Study_ID']} | {s['probability']} | {s['title']} |\n")
            f.write("\n")
    print(f"Wrote {out_path}")


def main():
    reps = sys.argv[1:] or ["metadata", "fulltext"]
    rng = random.Random(PACKET_RANDOM_SEED)

    for representation in reps:
        k_rows = load_k_summary(representation)
        finalists = reduce_to_finalists(pareto_optimal_set(k_rows))

        model_labels = ["Model A", "Model B", "Model C", "Model D"][:len(finalists)]
        shuffled_finalists = finalists[:]
        rng.shuffle(shuffled_finalists)
        label_map = dict(zip(model_labels, shuffled_finalists))

        all_topics_by_k = {}
        for r in finalists:
            k, medoid_seed = r["k"], int(r["medoid_seed"])
            topics = build_packet_data(representation, k, medoid_seed)
            write_internal_packet(representation, k, medoid_seed, topics)
            all_topics_by_k[k] = topics

        # Answer key (analyst-only)
        hv_dir = ROOT / "human_validation" / representation
        hv_dir.mkdir(parents=True, exist_ok=True)
        answer_key_path = hv_dir / "ANSWER_KEY_do_not_share_with_raters.md"
        with open(answer_key_path, "w", encoding="utf-8") as f:
            f.write(f"# Answer Key -- {representation} (analyst-only, NOT for raters)\n\n")
            f.write(f"Randomization seed: {PACKET_RANDOM_SEED}\n\n")
            f.write("| Blinded label | Real k | medoid seed | mean_cv | mean_stability |\n")
            f.write("|---|---|---|---|---|\n")
            for label, r in label_map.items():
                f.write(f"| {label} | {r['k']} | {r['medoid_seed']} | {r['mean_cv']:.4f} | "
                        f"{r['mean_stability']:.4f} |\n")
        print(f"Wrote {answer_key_path} (analyst-only)")

        # Rater-facing blinded packet
        blinded_path = hv_dir / "blinded_comparison_packet.md"
        with open(blinded_path, "w", encoding="utf-8") as f:
            f.write(f"# Blinded Model Comparison Packet -- {representation}\n\n")
            f.write("For independent rater use. Model identity, seed, configuration, and all quantitative "
                    "metrics (coherence, stability, prevalence, topic-size counts) are withheld. The number "
                    "of topics shown for a given model is inherently observable by counting the sections "
                    "below -- only the numeric k *label* and the metrics behind it are hidden, not the "
                    "topic count itself.\n\n")
            f.write("For each topic: top-20 probability terms, top-20 FREX terms, and the 10 "
                    "highest-loading study titles/abstracts, in no particular order of importance.\n\n")
            for label in model_labels:
                r = label_map[label]
                topics = all_topics_by_k[r["k"]]
                topic_order = list(range(len(topics)))
                rng.shuffle(topic_order)
                f.write(f"## {label}\n\n")
                for display_i, orig_i in enumerate(topic_order):
                    topic = topics[orig_i]
                    f.write(f"### {label} -- Topic {display_i + 1}\n\n")
                    f.write(f"- Top-{TOP_N_TERMS} probability terms: {', '.join(topic['top_prob_terms'])}\n")
                    f.write(f"- Top-{TOP_N_TERMS} FREX terms: {', '.join(topic['top_frex_terms'])}\n\n")
                    f.write(f"Highest-loading studies:\n\n")
                    for s in topic["top_studies"]:
                        abstract_excerpt = (s["abstract"][:300] + "...") if len(s["abstract"]) > 300 else s["abstract"]
                        f.write(f"- **{s['title']}** -- {abstract_excerpt}\n")
                    f.write("\n")
        print(f"Wrote {blinded_path}")
        print(f"[{representation}] Stage 6 packets complete for finalists k={sorted(f_['k'] for f_ in finalists)}")


if __name__ == "__main__":
    main()
