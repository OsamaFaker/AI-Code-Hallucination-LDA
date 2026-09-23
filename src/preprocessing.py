"""
Base preprocessing pipeline (PRE_EXECUTION_ANALYSIS_PLAN.md SS5).

spaCy en_core_web_sm: tokenize, lemmatize, lower-case. Retain NOUN/PROPN/VERB/
ADJ. Remove standard stopwords, punctuation, purely numeric/non-alphabetic
tokens, single-character tokens -- but RETAIN tokens containing digits or
`+ # _ . -` alongside at least one alphabetic character (C++, C#, GPT-4,
Python3, versioned model names, package/API identifiers). Corpus-wide,
deterministic, not topic-specific. RQ1-RQ4 categories never consulted here.

SS5a: HF-A (retain domain terms) vs HF-B (remove a fixed, corpus-agnostic
list of generic academic filler terms) -- frozen list, chosen before seeing
this corpus's frequency table.

SS5b: unigram vs unigram+bigram (gensim Phrases, min_count=5, threshold=10.0,
default scoring) -- frozen parameters.

No LDA fitting in this module -- text-to-tokens preparation only.
"""

from __future__ import annotations

import re
from pathlib import Path

import spacy
from gensim.models.phrases import Phrases, ENGLISH_CONNECTOR_WORDS

ROOT = Path(__file__).resolve().parents[1]

RETAIN_POS = {"NOUN", "PROPN", "VERB", "ADJ"}

# Frozen HF-B list (PRE_EXECUTION_ANALYSIS_PLAN.md SS5a) -- generic academic
# filler terms that survive POS filtering, chosen from general scholarly-
# writing genre knowledge, not from this corpus's frequency table. Explicitly
# excludes domain terms named in Master Prompt SS8 (code, LLM, model,
# programming, developer, hallucination).
HF_B_TERMS = {
    "paper", "study", "studies", "research", "result", "results", "finding",
    "findings", "approach", "method", "methods", "methodology", "work",
    "author", "authors", "researcher", "researchers", "section", "figure",
    "table", "example", "examples", "case", "et", "al",
}

# Bigram parameters, frozen a priori (plan SS5b).
BIGRAM_MIN_COUNT = 5
BIGRAM_THRESHOLD = 10.0

_TECHNICAL_CHARS = set("+#_.-")

# Fixed, deterministic, corpus-wide lemma corrections (plan SS7: "Any manual
# lemma correction must be deterministic, corpus-wide, documented, and not
# topic-specific"). Found via preprocessing/lemma_audit_*.md:
#  - "coding" -> spaCy's rule-based lemmatizer maps it to "cod" (the fish /
#    an unrelated irregular-verb-table collision), never a genuine lemma.
#  - "datum" -> technically-correct singular of "data" that no CS/ML paper
#    actually uses; standardized to the universally-used "data".
FIXED_LEMMA_OVERRIDES = {
    "cod": "code",
    "datum": "data",
}

_nlp = None


def get_nlp():
    global _nlp
    if _nlp is None:
        _nlp = spacy.load("en_core_web_sm", disable=["parser", "ner"])
    return _nlp


def _is_technical_token(text: str) -> bool:
    """Contains a digit or one of + # _ . - alongside >=1 alphabetic char."""
    has_alpha = any(c.isalpha() for c in text)
    has_digit_or_symbol = any(c.isdigit() or c in _TECHNICAL_CHARS for c in text)
    return has_alpha and has_digit_or_symbol


def _keep_token(token) -> bool:
    if token.pos_ not in RETAIN_POS:
        return False
    if token.is_stop or token.is_punct or token.is_space:
        return False
    text = token.text
    if len(text) > 40:  # malformed/garbage guard
        return False
    has_alpha = any(c.isalpha() for c in text)
    if not has_alpha:
        return False  # purely numeric / symbol-only
    lemma = token.lemma_.lower().strip()
    if len(lemma) <= 1:
        return False  # single-character noise
    if not re.match(r"^[a-z0-9+#_.\-]+$", lemma):
        return False  # malformed token (residual non-ASCII/garbage)
    return True


def _raw_tokenize(texts: list[str]) -> list[list[str]]:
    """Tokenize + lemmatize + apply FIXED_LEMMA_OVERRIDES only (no HF filter,
    no plural merge, no bigrams) -- the canonical baseline used to derive
    build_plural_merge_map() for a representation."""
    nlp = get_nlp()
    out = []
    for doc in nlp.pipe(texts, batch_size=16):
        tokens = []
        for token in doc:
            if not _keep_token(token):
                continue
            lemma = token.lemma_.lower().strip()
            lemma = FIXED_LEMMA_OVERRIDES.get(lemma, lemma)
            tokens.append(lemma)
        out.append(tokens)
    return out


def build_plural_merge_map(token_lists: list[list[str]]) -> dict[str, str]:
    """Deterministic, corpus-wide plural/singular merge: if lemma L ends in
    's' and L[:-1] also occurs in the same corpus's lemma vocabulary, map L ->
    L[:-1]. Fixes spaCy POS-tagger-driven lemmatization inconsistency (e.g.
    'llms' sometimes left unlemmatized while 'llm' is the dominant form) --
    found via preprocessing/lemma_audit_*.md, not chosen to favour any topic."""
    from collections import Counter

    counts = Counter(t for doc in token_lists for t in doc)
    mapping = {}
    for lemma in counts:
        if lemma.endswith("s") and len(lemma) > 2:
            singular = lemma[:-1]
            if singular in counts and singular != lemma:
                mapping[lemma] = singular
    return mapping


def get_plural_merge_map(texts: list[str]) -> dict[str, str]:
    """Computed once per representation from its own canonical (HF-A,
    unigram) baseline, then reused across that representation's HF-A/HF-B and
    unigram/bigram variants -- keeps each representation's pipeline
    self-contained per plan SS1, while remaining deterministic and corpus-wide
    within it."""
    return build_plural_merge_map(_raw_tokenize(texts))


def tokenize_documents(
    texts: list[str], hf_variant: str, plural_merge_map: dict[str, str] | None = None
) -> list[list[str]]:
    """hf_variant: 'A' (retain domain terms) or 'B' (remove HF_B_TERMS)."""
    assert hf_variant in ("A", "B")
    nlp = get_nlp()
    plural_merge_map = plural_merge_map or {}
    out = []
    for doc in nlp.pipe(texts, batch_size=16):
        tokens = []
        for token in doc:
            if not _keep_token(token):
                continue
            lemma = token.lemma_.lower().strip()
            lemma = FIXED_LEMMA_OVERRIDES.get(lemma, lemma)
            lemma = plural_merge_map.get(lemma, lemma)
            if hf_variant == "B" and lemma in HF_B_TERMS:
                continue
            tokens.append(lemma)
        out.append(tokens)
    return out


def add_bigrams(token_lists: list[list[str]]) -> list[list[str]]:
    phrases = Phrases(
        token_lists,
        min_count=BIGRAM_MIN_COUNT,
        threshold=BIGRAM_THRESHOLD,
        connector_words=ENGLISH_CONNECTOR_WORDS,
    )
    return [phrases[tokens] for tokens in token_lists]


def preprocess_variant(
    texts: list[str], hf_variant: str, use_bigrams: bool,
    plural_merge_map: dict[str, str] | None = None,
) -> list[list[str]]:
    tokens = tokenize_documents(texts, hf_variant, plural_merge_map)
    if use_bigrams:
        tokens = add_bigrams(tokens)
    return tokens


def write_lemma_audit(
    out_path: Path,
    representation_name: str,
    ids: list[str],
    texts: list[str],
) -> None:
    """Corpus-level lemmatization-error audit (plan SS5): surface forms that
    lemmatize inconsistently, and a top-term list for manual eyeball review.
    Deterministic; no manual correction applied unless a systematic error is
    found (documented here if so)."""
    nlp = get_nlp()
    surface_to_lemmas: dict[str, dict[str, int]] = {}
    for doc in nlp.pipe(texts, batch_size=16):
        for token in doc:
            if not _keep_token(token):
                continue
            surf = token.text.lower()
            lem = token.lemma_.lower().strip()
            surface_to_lemmas.setdefault(surf, {}).setdefault(lem, 0)
            surface_to_lemmas[surf][lem] += 1

    inconsistent_raw = {
        surf: lemmas for surf, lemmas in surface_to_lemmas.items() if len(lemmas) > 1
    }

    # Post-correction state: FIXED_LEMMA_OVERRIDES + this representation's own
    # plural-merge map (built from its HF-A/unigram baseline, per SS5/SS7).
    plural_map = get_plural_merge_map(texts)
    corrected_tokens = tokenize_documents(texts, "A", plural_map)
    corrected_lemma_counts: dict[str, int] = {}
    for doc_tokens in corrected_tokens:
        for lem in doc_tokens:
            corrected_lemma_counts[lem] = corrected_lemma_counts.get(lem, 0) + 1
    top_terms = sorted(corrected_lemma_counts.items(), key=lambda kv: -kv[1])[:60]

    out_path.parent.mkdir(parents=True, exist_ok=True)
    with open(out_path, "w", encoding="utf-8") as f:
        f.write(f"# Lemmatization Audit -- {representation_name}\n\n")
        f.write(f"- Documents: {len(texts)}\n")
        f.write(f"- Distinct surface forms (post-filter, pre-correction): {len(surface_to_lemmas)}\n")
        f.write(f"- Distinct lemmas after correction: {len(corrected_lemma_counts)}\n")
        f.write(f"- Surface forms with raw (pre-correction) lemmatization inconsistency: "
                f"{len(inconsistent_raw)}\n\n")

        f.write("## Applied deterministic corrections (plan SS7)\n\n")
        f.write("Fixed overrides (spaCy lemmatizer errors / non-standard-usage normalization):\n\n")
        for wrong, right in FIXED_LEMMA_OVERRIDES.items():
            f.write(f"- `{wrong}` -> `{right}`\n")
        f.write(f"\nPlural-merge map, derived from this representation's own HF-A/unigram baseline "
                f"vocabulary (lemma `X` -> `Xs` merged into `X` when both occur): "
                f"**{len(plural_map)} mappings**.\n\n")
        if plural_map:
            f.write("| plural | -> singular |\n|---|---|\n")
            for plural, singular in sorted(plural_map.items()):
                f.write(f"| {plural} | {singular} |\n")
            f.write("\n")

        if inconsistent_raw:
            f.write("## Raw (pre-correction) inconsistent lemmatization, for reference\n\n")
            f.write("| surface form | lemma : count |\n|---|---|\n")
            for surf, lemmas in sorted(inconsistent_raw.items(), key=lambda kv: -sum(kv[1].values()))[:40]:
                lem_str = ", ".join(f"{l}:{c}" for l, c in sorted(lemmas.items(), key=lambda kv: -kv[1]))
                f.write(f"| {surf} | {lem_str} |\n")
            f.write("\n")
            f.write("The plural-merge map above resolves the great majority of these (e.g. "
                    "llms/llm, models/model, tools/tool). Remaining residual cases are genuine "
                    "part-of-speech-dependent inflections (a word used as both noun and verb "
                    "across different documents, or an irregular plural the +s suffix rule does "
                    "not cover) rather than lemmatizer errors, and are left uncorrected.\n\n")

        f.write("## Top 60 terms by frequency, after correction (manual eyeball review)\n\n")
        f.write("| lemma | count |\n|---|---|\n")
        for lem, cnt in top_terms:
            f.write(f"| {lem} | {cnt} |\n")

    print(f"Wrote {out_path} ({len(texts)} docs, {len(corrected_lemma_counts)} distinct lemmas post-correction, "
          f"{len(inconsistent_raw)} raw inconsistent surface forms, {len(plural_map)} plural merges applied)")
