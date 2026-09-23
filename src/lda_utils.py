"""
Shared LDA fitting / alignment / stability utilities.

Per PRE_EXECUTION_ANALYSIS_PLAN.md SS6: gensim.models.LdaModel only
(single-threaded, never LdaMulticore) for strict reproducibility under a
fixed seed. Per SS9/SS10/SS19: all cross-seed stability computations use
Hungarian-aligned Jensen-Shannon similarity on FULL topic-word probability
distributions, never raw pairwise comparison without alignment (topic labels
permute arbitrarily between independent fits).
"""

from __future__ import annotations

import numpy as np
from gensim.models import LdaModel
from gensim.models.coherencemodel import CoherenceModel
from scipy.optimize import linear_sum_assignment
from scipy.spatial.distance import jensenshannon


def fit_lda(corpus, dictionary, num_topics, seed, passes, iterations, alpha, eta) -> LdaModel:
    return LdaModel(
        corpus=corpus,
        id2word=dictionary,
        num_topics=num_topics,
        random_state=seed,
        passes=passes,
        iterations=iterations,
        alpha=alpha,
        eta=eta,
        eval_every=None,
    )


def topic_word_matrix(model: LdaModel) -> np.ndarray:
    """k x V row-normalized topic-word probability matrix."""
    return model.get_topics()


def coherence(model: LdaModel, texts, dictionary, corpus, measure: str) -> float:
    # processes=1: gensim's default spawns multiprocessing workers for the
    # sliding-window probability estimator, which requires an
    # `if __name__ == "__main__":` guard on Windows (spawn start method) and
    # is not worth the overhead for a 66-document corpus anyway.
    # Only 'u_mass' uses the BoW corpus; 'c_v'/'c_uci'/'c_npmi' all require
    # the tokenized texts (sliding-window co-occurrence estimation).
    cm = CoherenceModel(
        model=model,
        texts=None if measure == "u_mass" else texts,
        corpus=corpus if measure == "u_mass" else None,
        dictionary=dictionary, coherence=measure, processes=1,
    )
    return cm.get_coherence()


def hungarian_align_js_similarity(mat_a: np.ndarray, mat_b: np.ndarray) -> float:
    """Align topics of two (k x V) topic-word matrices (same V, same k) via
    Hungarian matching on JS distance, then return mean JS similarity
    (1 - JS distance) over the matched pairs."""
    k = mat_a.shape[0]
    cost = np.zeros((k, k))
    for i in range(k):
        for j in range(k):
            cost[i, j] = jensenshannon(mat_a[i], mat_b[j], base=2)
    # scipy's jensenshannon can return NaN for near-identical distributions
    # (floating-point underflow to a tiny negative value before the sqrt);
    # this arises exactly when the true distance is ~0, so treat NaN as 0.
    cost = np.nan_to_num(cost, nan=0.0)
    row_ind, col_ind = linear_sum_assignment(cost)
    distances = cost[row_ind, col_ind]
    return float(1.0 - distances.mean())


def mean_pairwise_stability(matrices: list[np.ndarray]) -> tuple[float, float]:
    """Mean and SD of Hungarian-aligned JS similarity over all pairs of
    topic-word matrices (e.g. across seeds at a fixed k)."""
    sims = []
    n = len(matrices)
    for i in range(n):
        for j in range(i + 1, n):
            sims.append(hungarian_align_js_similarity(matrices[i], matrices[j]))
    arr = np.array(sims)
    return float(arr.mean()), float(arr.std(ddof=1)) if len(arr) > 1 else 0.0


def top_n_diversity(matrices: list[np.ndarray], top_n: int = 25) -> float:
    """Mean, over the given models, of (unique words among all topics' top-N)
    / (top_n * k) -- a standard topic-diversity metric."""
    scores = []
    for mat in matrices:
        top_words = set()
        total = 0
        for row in mat:
            idx = np.argsort(-row)[:top_n]
            top_words.update(idx.tolist())
            total += top_n
        scores.append(len(top_words) / total)
    return float(np.mean(scores))


def structural_medoid_index(matrices: list[np.ndarray]) -> int:
    """Index of the seed whose topic-word matrix has the highest mean
    Hungarian-aligned JS similarity to all other seeds' matrices (plan SS19:
    never the highest-coherence seed, always the structural medoid)."""
    n = len(matrices)
    sim_sum = np.zeros(n)
    for i in range(n):
        for j in range(n):
            if i == j:
                continue
            sim_sum[i] += hungarian_align_js_similarity(matrices[i], matrices[j])
    return int(np.argmax(sim_sum))
