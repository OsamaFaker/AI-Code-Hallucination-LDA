"""
STAGE 5b -- Full-text document-length sensitivity (MANDATORY,
PRE_EXECUTION_ANALYSIS_PLAN.md SS13). Full text only.

1. Correlation between raw document length and dominant-topic confidence /
   topic probability (finalist medoid models).
2. Length-balanced representation: documents exceeding the frozen cap
   (extraction/document_length_audit.md -- 15500 tokens, fixed before this
   run) are resampled via deterministic, section-proportional systematic
   sampling: tokens are drawn from each detected section (Introduction,
   Background/Related Work, Methodology, Results, Discussion, Conclusion) in
   proportion to that section's share of the document, using fixed-stride
   sampling within each section (never head-truncation). Documents whose
   section structure can't be detected are sampled evenly across the whole
   body with the same fixed-stride method. Documents under the cap are
   unchanged.
3. Refit each finalist k (frozen dictionary/priors/budget, finalist's own
   medoid seed) on the length-balanced corpus; compare to the original via
   JS similarity, dominant-topic agreement (ARI/NMI), prevalence change.
   Reported even if it shows sensitivity to length -- never suppressed.
"""

from __future__ import annotations

import csv
import re
import sys
from pathlib import Path

import numpy as np
from gensim.corpora import Dictionary
from scipy.stats import pearsonr, spearmanr

sys.path.insert(0, str(Path(__file__).parent))
from preprocessing import preprocess_variant, get_plural_merge_map
from lda_utils import fit_lda
from stage1_select import load_sweep, decide_variant
from stage1_sweep import load_fulltext_texts
from stage2_select import select_convergence, select_priors
from stage4_select import load_k_summary, pareto_optimal_set, reduce_to_finalists
from stage5_robustness import dominant_topics_and_matrix, aligned_metrics
from extract_fulltext import START_RES, merge_split_heading_numbers

ROOT = Path(__file__).resolve().parents[1]

SECTION_ORDER = ["introduction", "background", "related_work", "methodology", "results", "discussion", "conclusion"]
SECTION_RES = {name: START_RES[name] for name in SECTION_ORDER if name in START_RES}


def get_frozen_cap() -> int:
    audit = (ROOT / "extraction" / "document_length_audit.md").read_text(encoding="utf-8")
    m = re.search(r"Frozen Stage-5 length cap.*?\*\*(\d+)\*\*", audit)
    assert m, "could not find frozen length cap in document_length_audit.md"
    return int(m.group(1))


def segment_document(text: str) -> list[tuple[str, str]]:
    """Return [(section_name, section_text), ...] using the same heading
    regexes as extract_fulltext.py. Falls back to a single 'body' segment if
    no internal headings are found."""
    text = merge_split_heading_numbers(text)
    matches = []
    for name, pat in SECTION_RES.items():
        for m in pat.finditer(text):
            matches.append((m.start(), name))
    matches.sort()
    if not matches:
        return [("body", text)]

    segments = []
    for i, (pos, name) in enumerate(matches):
        end = matches[i + 1][0] if i + 1 < len(matches) else len(text)
        segments.append((name, text[pos:end]))
    return segments


def fixed_stride_sample(tokens: list[str], n_target: int) -> list[str]:
    if n_target >= len(tokens) or n_target <= 0:
        return tokens
    stride = len(tokens) / n_target
    idx = [int(i * stride) for i in range(n_target)]
    return [tokens[i] for i in idx]


def length_balance_document(raw_text: str, cap: int) -> str:
    words = raw_text.split()
    if len(words) <= cap:
        return raw_text

    segments = segment_document(raw_text)
    total = sum(len(seg_text.split()) for _, seg_text in segments)
    if total == 0:
        return raw_text

    out_words = []
    for name, seg_text in segments:
        seg_words = seg_text.split()
        share = len(seg_words) / total
        n_target = max(1, int(round(cap * share)))
        out_words.extend(fixed_stride_sample(seg_words, n_target))
    return " ".join(out_words)


def main():
    representation = "fulltext"
    cap = get_frozen_cap()
    print(f"Frozen length cap: {cap} tokens")

    with open(ROOT / "corpus" / "corpus_audit.csv", newline="", encoding="utf-8") as f:
        raw_lengths = {r["Study_ID"]: int(r["raw_token_count"]) for r in csv.DictReader(f)}

    ids, texts = load_fulltext_texts()
    balanced_texts = [length_balance_document(t, cap) for t in texts]
    n_balanced = sum(1 for orig, bal in zip(texts, balanced_texts) if orig != bal)
    print(f"{n_balanced}/{len(texts)} documents exceeded the cap and were length-balanced")

    rows = load_sweep(representation)
    d1 = decide_variant(representation, rows)
    fc = d1["final_config"]
    priors = select_priors(representation)
    conv = select_convergence(representation)

    plural_map_orig = get_plural_merge_map(texts)
    tokens_orig = preprocess_variant(texts, d1["chosen_hf"], d1["use_bigrams"], plural_map_orig)
    dict_orig = Dictionary(tokens_orig)
    dict_orig.filter_extremes(no_below=fc["no_below"], no_above=fc["no_above"])
    corpus_orig = [dict_orig.doc2bow(t) for t in tokens_orig]

    # Length-balanced corpus: SAME dictionary (projecting balanced docs onto
    # the already-frozen vocabulary), not a refit dictionary -- isolates the
    # effect of length balancing from the effect of a different vocabulary.
    plural_map_bal = get_plural_merge_map(balanced_texts)
    tokens_bal = preprocess_variant(balanced_texts, d1["chosen_hf"], d1["use_bigrams"], plural_map_bal)
    corpus_bal = [dict_orig.doc2bow(t) for t in tokens_bal]

    k_rows = load_k_summary(representation)
    finalists = reduce_to_finalists(pareto_optimal_set(k_rows))

    correlation_rows = []
    comparison_rows = []
    for r in finalists:
        k, medoid_seed = r["k"], int(r["medoid_seed"])

        model_orig = fit_lda(corpus_orig, dict_orig, num_topics=k, seed=medoid_seed,
                              passes=conv["passes"], iterations=conv["iterations"],
                              alpha=priors["alpha"], eta=priors["eta"])
        max_probs = []
        for bow in corpus_orig:
            dist = model_orig.get_document_topics(bow, minimum_probability=0.0)
            max_probs.append(max(p for _, p in dist))
        lengths = [raw_lengths[sid] for sid in ids]
        pear_r, pear_p = pearsonr(lengths, max_probs)
        spear_r, spear_p = spearmanr(lengths, max_probs)
        correlation_rows.append({
            "k": k, "pearson_r": round(pear_r, 4), "pearson_p": round(pear_p, 5),
            "spearman_r": round(spear_r, 4), "spearman_p": round(spear_p, 5),
        })

        mat_orig, dom_orig = dominant_topics_and_matrix(
            corpus_orig, dict_orig, k, medoid_seed, conv["passes"], conv["iterations"],
            priors["alpha"], priors["eta"])
        mat_bal, dom_bal = dominant_topics_and_matrix(
            corpus_bal, dict_orig, k, medoid_seed, conv["passes"], conv["iterations"],
            priors["alpha"], priors["eta"])
        js_sim, ari, nmi = aligned_metrics(
            mat_orig, mat_bal, dom_orig, dom_bal,
            ids_overlap_idx_a=np.arange(len(ids)), ids_overlap_idx_b=np.arange(len(ids)))

        # prevalence: mean topic probability across docs, for each model
        def mean_prevalence(model, corpus, k):
            mat = np.zeros((len(corpus), k))
            for i, bow in enumerate(corpus):
                for tid, p in model.get_document_topics(bow, minimum_probability=0.0):
                    mat[i, tid] = p
            return mat.mean(axis=0)

        model_bal = fit_lda(corpus_bal, dict_orig, num_topics=k, seed=medoid_seed,
                             passes=conv["passes"], iterations=conv["iterations"],
                             alpha=priors["alpha"], eta=priors["eta"])
        prev_orig_vec = mean_prevalence(model_orig, corpus_orig, k)
        prev_bal_vec = mean_prevalence(model_bal, corpus_bal, k)
        prevalence_change = float(np.abs(prev_orig_vec - prev_bal_vec).mean())

        comparison_rows.append({
            "k": k, "js_similarity": round(js_sim, 5),
            "dominant_topic_agreement_ari": round(ari, 5), "dominant_topic_agreement_nmi": round(nmi, 5),
            "mean_abs_prevalence_change": round(prevalence_change, 5),
        })
        print(f"k={k}: length-confidence pearson_r={pear_r:.3f} (p={pear_p:.4f}), "
              f"balanced-vs-original JS={js_sim:.3f} ARI={ari:.3f} NMI={nmi:.3f}")

    out_dir = ROOT / "results" / "fulltext"
    with open(out_dir / "length_sensitivity_correlation.csv", "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=["k", "pearson_r", "pearson_p", "spearman_r", "spearman_p"])
        w.writeheader()
        for row in correlation_rows:
            w.writerow(row)

    with open(out_dir / "length_sensitivity_comparison.csv", "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=["k", "js_similarity", "dominant_topic_agreement_ari",
                                            "dominant_topic_agreement_nmi", "mean_abs_prevalence_change"])
        w.writeheader()
        for row in comparison_rows:
            w.writerow(row)

    print(f"Wrote {out_dir / 'length_sensitivity_correlation.csv'}")
    print(f"Wrote {out_dir / 'length_sensitivity_comparison.csv'}")
    print(f"{n_balanced}/{len(texts)} documents length-balanced at cap={cap}")


if __name__ == "__main__":
    main()
