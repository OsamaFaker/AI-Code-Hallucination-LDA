"""
STAGE 1 -- Preprocessing x dictionary selection (PRE_EXECUTION_ANALYSIS_PLAN.md SS9).

For each representation (metadata, fulltext) independently:
  - 4 preprocessing variants: {HF-A, HF-B} x {unigram, unigram+bigram}
  - Dictionary grid: no_below in {2,3,4,5,6} x no_above in {0.40,...,1.00} (40 configs)
  - Each (variant, dict-config) cell: fit at pilot k-set {5,10,15} x 5 pilot
    seeds [42,101,202,303,404], fixed pilot budget passes=20/iterations=400/
    alpha=auto/eta=auto. gensim.models.LdaModel only (single-threaded).
  - Record vocab size, % vocab removed, empty-doc count, avg doc vocab,
    mean/SD C_v, mean/SD C_NPMI, preliminary top-25 diversity, preliminary
    seed stability (Hungarian-aligned JS on full topic-word distributions).
  - Apply the frozen dictionary-selection rule and bigram/HF-A-vs-B retention
    rule (see PRE_EXECUTION_ANALYSIS_PLAN.md SS9) to pick one config per
    representation.

Writes incrementally to results/{metadata,fulltext}/dictionary_sweep.csv so
progress can be inspected while running. No result-driven retuning: every
threshold used below is copied verbatim from the frozen plan.
"""

from __future__ import annotations

import csv
import sys
import time
from itertools import product
from pathlib import Path

import numpy as np
from gensim.corpora import Dictionary

sys.path.insert(0, str(Path(__file__).parent))
from preprocessing import preprocess_variant, get_plural_merge_map
from lda_utils import fit_lda, coherence, topic_word_matrix, mean_pairwise_stability, top_n_diversity

ROOT = Path(__file__).resolve().parents[1]

PILOT_K_SET = [5, 10, 15]
PILOT_SEEDS = [42, 101, 202, 303, 404]
PILOT_PASSES = 20
PILOT_ITERATIONS = 400
NO_BELOW_GRID = [2, 3, 4, 5, 6]
NO_ABOVE_GRID = [0.40, 0.50, 0.60, 0.70, 0.75, 0.80, 0.90, 1.00]
VARIANTS = [("A", False), ("A", True), ("B", False), ("B", True)]

FIELDNAMES = [
    "representation", "hf_variant", "bigrams", "no_below", "no_above",
    "vocab_size", "pct_vocab_removed", "empty_docs", "avg_doc_vocab",
    "mean_cv", "sd_cv", "mean_cnpmi", "sd_cnpmi",
    "mean_diversity", "mean_stability", "sd_stability",
    "n_fits", "wall_seconds",
]


def load_metadata_texts():
    with open(ROOT / "corpus" / "metadata_documents.csv", newline="", encoding="utf-8") as f:
        rows = list(csv.DictReader(f))
    return [r["Study_ID"] for r in rows], [r["combined_text"] for r in rows]


def load_fulltext_texts():
    with open(ROOT / "corpus" / "corpus_audit.csv", newline="", encoding="utf-8") as f:
        ids = sorted([r["Study_ID"] for r in csv.DictReader(f)], key=lambda x: int(x[1:]))
    texts = [(ROOT / "extraction" / "fulltext" / f"{sid}.txt").read_text(encoding="utf-8") for sid in ids]
    return ids, texts


def sweep_one_config(representation: str, hf: str, bigrams: bool, tokens: list[list[str]],
                      no_below: int, no_above: float) -> dict | None:
    t0 = time.time()
    full_vocab_size = len(Dictionary(tokens))
    dictionary = Dictionary(tokens)
    dictionary.filter_extremes(no_below=no_below, no_above=no_above)
    vocab_size = len(dictionary)
    if vocab_size < 20:
        return {
            "representation": representation, "hf_variant": hf, "bigrams": bigrams,
            "no_below": no_below, "no_above": no_above,
            "vocab_size": vocab_size, "pct_vocab_removed": 100 * (1 - vocab_size / full_vocab_size),
            "empty_docs": None, "avg_doc_vocab": None,
            "mean_cv": None, "sd_cv": None, "mean_cnpmi": None, "sd_cnpmi": None,
            "mean_diversity": None, "mean_stability": None, "sd_stability": None,
            "n_fits": 0, "wall_seconds": round(time.time() - t0, 1),
        }

    corpus = [dictionary.doc2bow(t) for t in tokens]
    empty_docs = sum(1 for bow in corpus if len(bow) == 0)
    doc_vocab_counts = [len(bow) for bow in corpus]
    avg_doc_vocab = float(np.mean(doc_vocab_counts))

    cv_all, cnpmi_all, diversity_per_k, stability_per_k = [], [], [], []
    n_fits = 0
    for k in PILOT_K_SET:
        matrices = []
        for seed in PILOT_SEEDS:
            model = fit_lda(corpus, dictionary, num_topics=k, seed=seed,
                             passes=PILOT_PASSES, iterations=PILOT_ITERATIONS,
                             alpha="auto", eta="auto")
            cv = coherence(model, tokens, dictionary, corpus, "c_v")
            cnpmi = coherence(model, tokens, dictionary, corpus, "c_npmi")
            cv_all.append(cv)
            cnpmi_all.append(cnpmi)
            matrices.append(topic_word_matrix(model))
            n_fits += 1
        mean_stab, _ = mean_pairwise_stability(matrices)
        stability_per_k.append(mean_stab)
        diversity_per_k.append(top_n_diversity(matrices, top_n=25))

    return {
        "representation": representation, "hf_variant": hf, "bigrams": bigrams,
        "no_below": no_below, "no_above": no_above,
        "vocab_size": vocab_size, "pct_vocab_removed": round(100 * (1 - vocab_size / full_vocab_size), 2),
        "empty_docs": empty_docs, "avg_doc_vocab": round(avg_doc_vocab, 2),
        "mean_cv": round(float(np.mean(cv_all)), 5), "sd_cv": round(float(np.std(cv_all, ddof=1)), 5),
        "mean_cnpmi": round(float(np.mean(cnpmi_all)), 5), "sd_cnpmi": round(float(np.std(cnpmi_all, ddof=1)), 5),
        "mean_diversity": round(float(np.mean(diversity_per_k)), 5),
        "mean_stability": round(float(np.mean(stability_per_k)), 5),
        "sd_stability": round(float(np.std(stability_per_k, ddof=1)), 5),
        "n_fits": n_fits, "wall_seconds": round(time.time() - t0, 1),
    }


def run_representation(representation: str, ids: list[str], texts: list[str]) -> None:
    out_csv = ROOT / "results" / representation / "dictionary_sweep.csv"
    out_csv.parent.mkdir(parents=True, exist_ok=True)

    done = set()
    write_header = not out_csv.exists()
    if out_csv.exists():
        with open(out_csv, newline="", encoding="utf-8") as f:
            for r in csv.DictReader(f):
                done.add((r["hf_variant"], r["bigrams"], r["no_below"], r["no_above"]))
        print(f"[{representation}] resuming: {len(done)} configs already completed")

    plural_map = get_plural_merge_map(texts)
    token_cache = {}
    for hf, bigrams in VARIANTS:
        t0 = time.time()
        token_cache[(hf, bigrams)] = preprocess_variant(texts, hf, bigrams, plural_map)
        print(f"[{representation}] tokenized HF-{hf} bigrams={bigrams} in {time.time()-t0:.1f}s")

    total_configs = len(VARIANTS) * len(NO_BELOW_GRID) * len(NO_ABOVE_GRID)
    done_count = len(done)
    with open(out_csv, "a", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=FIELDNAMES)
        if write_header:
            writer.writeheader()
        for (hf, bigrams), no_below, no_above in product(VARIANTS, NO_BELOW_GRID, NO_ABOVE_GRID):
            key = (hf, str(bigrams), str(no_below), str(no_above))
            if key in done:
                continue
            row = sweep_one_config(representation, hf, bigrams, token_cache[(hf, bigrams)], no_below, no_above)
            writer.writerow(row)
            f.flush()
            done_count += 1
            print(f"[{representation}] {done_count}/{total_configs} HF-{hf} bigrams={bigrams} "
                  f"no_below={no_below} no_above={no_above} -> vocab={row['vocab_size']} "
                  f"mean_cv={row['mean_cv']} mean_stability={row['mean_stability']} "
                  f"({row['wall_seconds']}s)")


def main():
    t_start = time.time()
    meta_ids, meta_texts = load_metadata_texts()
    run_representation("metadata", meta_ids, meta_texts)
    print(f"[metadata] DONE in {(time.time()-t_start)/60:.1f} min")

    t_ft = time.time()
    ft_ids, ft_texts = load_fulltext_texts()
    run_representation("fulltext", ft_ids, ft_texts)
    print(f"[fulltext] DONE in {(time.time()-t_ft)/60:.1f} min")

    print(f"STAGE 1 SWEEP COMPLETE in {(time.time()-t_start)/60:.1f} min total")


if __name__ == "__main__":
    main()
