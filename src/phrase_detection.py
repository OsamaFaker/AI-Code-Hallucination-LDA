"""Section 13: phrase detection (unigrams-only vs unigrams+bigrams), data-driven via gensim's
NPMI-scored Phrases detector - phrases are never manually forced.
"""
from __future__ import annotations

from gensim.models.phrases import Phrases, ENGLISH_CONNECTOR_WORDS


def detect_bigrams(token_lists: list[list[str]], min_count: int = 3, threshold: float = 0.4):
    """threshold is on gensim's npmi scorer scale (roughly -1..1; higher = more restrictive)."""
    phrases = Phrases(
        token_lists, min_count=min_count, threshold=threshold,
        scoring="npmi", connector_words=ENGLISH_CONNECTOR_WORDS,
    )
    phraser = phrases.freeze()
    return [phraser[doc] for doc in token_lists], phraser


def discovered_phrase_vocab(bigram_token_lists: list[list[str]]) -> set[str]:
    vocab = set()
    for doc in bigram_token_lists:
        for tok in doc:
            if "_" in tok:
                vocab.add(tok)
    return vocab
