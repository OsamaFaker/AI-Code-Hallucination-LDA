"""Shared LDA fitting, coherence, diversity/redundancy, and Hungarian-alignment utilities
used by every downstream stage (Stage 1/2 pilots, definitive k-sweep, robustness analyses,
cross-representation comparison).
"""
from __future__ import annotations

import numpy as np
from gensim import corpora
from gensim.models import LdaModel
from gensim.models.coherencemodel import CoherenceModel
from scipy.optimize import linear_sum_assignment

TOP_N = 20


def build_dictionary(token_lists: list[list[str]], no_below: int, no_above: float):
    dictionary = corpora.Dictionary(token_lists)
    dictionary.filter_extremes(no_below=no_below, no_above=no_above, keep_n=None)
    dictionary.compactify()
    return dictionary


def build_bow_corpus(token_lists: list[list[str]], dictionary):
    return [dictionary.doc2bow(toks) for toks in token_lists]


def fit_lda(bow_corpus, dictionary, k: int, seed: int, passes: int = 20,
            iterations: int = 400, alpha="auto", eta="auto") -> LdaModel:
    return LdaModel(
        corpus=bow_corpus,
        id2word=dictionary,
        num_topics=k,
        random_state=seed,
        passes=passes,
        iterations=iterations,
        alpha=alpha,
        eta=eta,
        eval_every=None,
        chunksize=max(len(bow_corpus), 1),
    )


def coherence_scores(model: LdaModel, token_lists: list[list[str]], dictionary,
                      bow_corpus=None) -> dict:
    scores = {}
    for cm_name, coh in [("c_v", "c_v"), ("c_npmi", "c_npmi")]:
        try:
            cm = CoherenceModel(model=model, texts=token_lists, dictionary=dictionary,
                                 coherence=coh, topn=TOP_N, processes=1)
            scores[cm_name] = cm.get_coherence()
        except Exception:  # noqa: BLE001
            scores[cm_name] = float("nan")
    try:
        cm = CoherenceModel(model=model, corpus=bow_corpus, dictionary=dictionary,
                             coherence="u_mass", topn=TOP_N, processes=1)
        scores["c_umass"] = cm.get_coherence()
    except Exception:  # noqa: BLE001
        scores["c_umass"] = float("nan")
    return scores


def topic_word_matrix(model: LdaModel) -> np.ndarray:
    """Full V-dim probability distribution per topic, shape (k, vocab_size)."""
    return model.get_topics()


def top_n_words(model: LdaModel, topn: int = TOP_N) -> list[list[str]]:
    out = []
    for i in range(model.num_topics):
        out.append([w for w, _ in model.show_topic(i, topn=topn)])
    return out


def topic_diversity(model: LdaModel, topn: int = TOP_N) -> float:
    tops = top_n_words(model, topn)
    all_words = [w for topic in tops for w in topic]
    if not all_words:
        return float("nan")
    return len(set(all_words)) / len(all_words)


def pairwise_redundancy(model: LdaModel, topn: int = TOP_N) -> dict:
    tops = top_n_words(model, topn)
    mat = topic_word_matrix(model)
    k = model.num_topics
    jaccards, cosines, jss = [], [], []
    for i in range(k):
        for j in range(i + 1, k):
            si, sj = set(tops[i]), set(tops[j])
            jacc = len(si & sj) / len(si | sj) if (si or sj) else 0.0
            jaccards.append(jacc)
            vi, vj = mat[i], mat[j]
            cos = float(np.dot(vi, vj) / (np.linalg.norm(vi) * np.linalg.norm(vj) + 1e-12))
            cosines.append(cos)
            jss.append(1.0 - js_similarity(vi, vj))
    return {
        "mean_top20_jaccard": float(np.mean(jaccards)) if jaccards else float("nan"),
        "mean_cosine": float(np.mean(cosines)) if cosines else float("nan"),
        "mean_js_distance": float(np.mean(jss)) if jss else float("nan"),
    }


def doc_topic_matrix(model: LdaModel, bow_corpus) -> np.ndarray:
    n_docs = len(bow_corpus)
    k = model.num_topics
    mat = np.zeros((n_docs, k))
    for i, bow in enumerate(bow_corpus):
        for topic_id, prob in model.get_document_topics(bow, minimum_probability=0.0):
            mat[i, topic_id] = prob
    return mat


def prevalence_and_thin_topics(model: LdaModel, bow_corpus) -> dict:
    dt = doc_topic_matrix(model, bow_corpus)
    dominant = dt.argmax(axis=1)
    k = model.num_topics
    counts = np.bincount(dominant, minlength=k)
    mean_prob = dt.mean(axis=0)
    thin = {
        "n_topics_0_studies": int((counts == 0).sum()),
        "n_topics_1_study": int((counts == 1).sum()),
        "n_topics_lt3_studies": int((counts < 3).sum()),
        "n_topics_lt5_studies": int((counts < 5).sum()),
    }
    margin = np.sort(dt, axis=1)[:, -1] - np.sort(dt, axis=1)[:, -2] if k > 1 else np.zeros(len(dt))
    top1 = dt.max(axis=1)
    conf_bins = {
        "prop_conf_lt_0.40": float((top1 < 0.40).mean()),
        "prop_conf_0.40_0.60": float(((top1 >= 0.40) & (top1 <= 0.60)).mean()),
        "prop_conf_gt_0.60": float((top1 > 0.60).mean()),
    }
    return {
        "dominant_counts": counts.tolist(),
        "mean_topic_prob": mean_prob.tolist(),
        "margin_mean": float(margin.mean()),
        **thin,
        **conf_bins,
    }


def compute_frex(model: LdaModel, weight: float = 0.7, topn: int = 20):
    """STM-style FREX: harmonic mean of within-topic frequency rank (ECDF) and exclusivity
    rank (ECDF), weight on exclusivity per Roberts et al.'s default (0.7)."""
    from scipy.stats import rankdata

    topics = model.get_topics()  # (k, V)
    col_sums = topics.sum(axis=0, keepdims=True) + 1e-12
    exclusivity = topics / col_sums
    freq_ecdf = np.apply_along_axis(lambda x: rankdata(x) / len(x), axis=1, arr=topics)
    excl_ecdf = np.apply_along_axis(lambda x: rankdata(x) / len(x), axis=1, arr=exclusivity)
    frex = 1.0 / ((weight / (excl_ecdf + 1e-12)) + ((1 - weight) / (freq_ecdf + 1e-12)))

    results = []
    for t in range(model.num_topics):
        order = np.argsort(-frex[t])[:topn]
        results.append([(model.id2word[int(i)], float(frex[t, i])) for i in order])
    return results, exclusivity


def js_similarity(p: np.ndarray, q: np.ndarray) -> float:
    """1 - Jensen-Shannon distance (base-2, so distance in [0,1]). Computed manually with
    epsilon-clipping rather than scipy.spatial.distance.jensenshannon directly, because on
    near-identical high-dimensional sparse topic-word distributions scipy's implementation can
    take sqrt() of a tiny negative float (pure floating-point underflow) and return NaN - which
    would otherwise be silently mis-scored as similarity 0 (maximally dissimilar) instead of
    the true ~1 (near-identical)."""
    p = np.clip(np.asarray(p, dtype=np.float64), 1e-12, None)
    q = np.clip(np.asarray(q, dtype=np.float64), 1e-12, None)
    p = p / p.sum()
    q = q / q.sum()
    m = 0.5 * (p + q)
    kl_pm = float(np.sum(p * np.log2(p / m)))
    kl_qm = float(np.sum(q * np.log2(q / m)))
    js_div = max(0.5 * kl_pm + 0.5 * kl_qm, 0.0)
    return 1.0 - float(np.sqrt(js_div))


def align_topics_hungarian(mat_a: np.ndarray, mat_b: np.ndarray) -> tuple[np.ndarray, np.ndarray]:
    """Align rows of mat_a to rows of mat_b (possibly different shapes[0]) by max JS similarity.
    Returns (row_ind, col_ind) from linear_sum_assignment on a rectangular cost matrix
    (cost = 1 - JS similarity), handling k_a != k_b via scipy's rectangular LSA support.
    """
    ka, kb = mat_a.shape[0], mat_b.shape[0]
    cost = np.zeros((ka, kb))
    for i in range(ka):
        for j in range(kb):
            cost[i, j] = 1.0 - js_similarity(mat_a[i], mat_b[j])
    row_ind, col_ind = linear_sum_assignment(cost)
    return row_ind, col_ind


def project_pair_to_shared_vocab(mat_a: np.ndarray, dict_a, mat_b: np.ndarray, dict_b):
    """Re-express two topic-word matrices built from different dictionaries over their
    combined shared vocabulary (zero-filled where a word is absent from one side), so
    cosine/JS comparisons between them are well-defined."""
    shared_vocab: dict[str, int] = {}
    for d in (dict_a, dict_b):
        for tok in d.values():
            if tok not in shared_vocab:
                shared_vocab[tok] = len(shared_vocab)
    V = len(shared_vocab)
    out = []
    for mat, d in ((mat_a, dict_a), (mat_b, dict_b)):
        mapped = np.zeros((mat.shape[0], V))
        for local_id, tok in d.items():
            mapped[:, shared_vocab[tok]] = mat[:, local_id]
        out.append(mapped)
    return out[0], out[1]


def pad_topic_matrix_to_common_vocab(models_and_dicts: list[tuple[LdaModel, "corpora.Dictionary"]]):
    """Build a shared vocabulary across several (model, dictionary) pairs and return each
    model's topic-word matrix re-expressed over that shared vocabulary (zero-filled for
    words absent from a given model's dictionary)."""
    shared_vocab: dict[str, int] = {}
    for _, d in models_and_dicts:
        for tok_id, tok in d.items():
            if tok not in shared_vocab:
                shared_vocab[tok] = len(shared_vocab)
    V = len(shared_vocab)
    out = []
    for model, d in models_and_dicts:
        raw = model.get_topics()  # (k, len(d))
        k = raw.shape[0]
        mapped = np.zeros((k, V))
        for local_id, tok in d.items():
            mapped[:, shared_vocab[tok]] = raw[:, local_id]
        out.append(mapped)
    return out, shared_vocab
