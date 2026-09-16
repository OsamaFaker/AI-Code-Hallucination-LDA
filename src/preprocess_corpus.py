"""Section 7-9: common spaCy preprocessing pipeline (tokenize + lemmatize + POS filter),
applied independently to Analysis A (metadata) and Analysis B (full text). Produces the raw
lemma-token lists that all downstream dictionary/threshold/phrase experiments reuse, so spaCy
itself only runs once per representation.
"""
import json
import re
import unicodedata
from pathlib import Path

import pandas as pd
import spacy

ROOT = Path(__file__).resolve().parents[1]
DATA_DIR = ROOT / "data"
PREP_DIR = ROOT / "preprocessing"

SPACY_MODEL = "en_core_web_sm"
POS_KEEP = {"NOUN", "PROPN", "VERB", "ADJ"}
MIN_TOKEN_LEN = 3

URL_RE = re.compile(r"https?://\S+")
EMAIL_RE = re.compile(r"\b[\w.+-]+@[\w-]+\.[\w.-]+\b")
NUM_RE = re.compile(r"^\d+([.,]\d+)?$")


def basic_clean(text: str) -> str:
    text = unicodedata.normalize("NFKC", str(text))
    text = URL_RE.sub(" ", text)
    text = EMAIL_RE.sub(" ", text)
    text = re.sub(r"[ \t]+", " ", text)
    return text


def run_pipeline(texts: list[str], study_ids: list[str], out_dir: Path, label: str):
    nlp = spacy.load(SPACY_MODEL, disable=["parser", "ner"])
    nlp.max_length = 3_000_000

    stopwords = sorted(nlp.Defaults.stop_words)
    (out_dir / "spacy_stopwords.txt").write_text("\n".join(stopwords), encoding="utf-8")

    cleaned = [basic_clean(t) for t in texts]

    doc_tokens: dict[str, list[str]] = {}
    lemma_pairs: dict[str, dict[str, int]] = {}  # lemma -> {surface_token: count}

    for sid, doc in zip(study_ids, nlp.pipe(cleaned, batch_size=8)):
        toks = []
        for tok in doc:
            if tok.pos_ not in POS_KEEP:
                continue
            if not tok.is_alpha:
                continue
            if tok.is_stop or tok.lower_ in nlp.Defaults.stop_words:
                continue
            lemma = tok.lemma_.lower().strip()
            if len(lemma) < MIN_TOKEN_LEN:
                continue
            if NUM_RE.match(lemma):
                continue
            toks.append(lemma)
            surface = tok.text.lower()
            lemma_pairs.setdefault(lemma, {}).setdefault(surface, 0)
            lemma_pairs[lemma][surface] += 1
        doc_tokens[sid] = toks

    out_dir.mkdir(parents=True, exist_ok=True)
    with open(out_dir / "lemmatized_tokens.json", "w", encoding="utf-8") as f:
        json.dump(doc_tokens, f)
    with open(out_dir / "lemma_surface_map.json", "w", encoding="utf-8") as f:
        json.dump(lemma_pairs, f)

    meta = {
        "spacy_version": spacy.__version__,
        "language_model": SPACY_MODEL,
        "language_model_version": nlp.meta.get("version"),
        "retained_pos_categories": sorted(POS_KEEP),
        "min_token_length": MIN_TOKEN_LEN,
        "stopword_source": "spaCy en_core_web_sm Defaults.stop_words",
        "n_stopwords": len(stopwords),
        "n_documents": len(doc_tokens),
        "mean_tokens_per_doc": sum(len(v) for v in doc_tokens.values()) / len(doc_tokens),
        "why_spacy": (
            "spaCy provides an integrated, versioned, industrial-strength tokenizer + "
            "statistical POS tagger + rule/lookup lemmatizer in one pipeline, avoiding the "
            "tokenization/lemmatization mismatches that arise from combining separate tools "
            "(e.g. NLTK tokenizer + WordNet lemmatizer, which requires manually mapping "
            "Penn Treebank POS tags to WordNet POS and does not disambiguate morphology as "
            "reliably). Its lemmatizer is context-aware (uses the tagged POS), which stemming "
            "(e.g. Porter/Snowball) cannot do, so it was preferred over stemming as the "
            "primary pipeline per protocol Section 7."
        ),
    }
    with open(out_dir / "preprocessing_meta.json", "w", encoding="utf-8") as f:
        json.dump(meta, f, indent=2)
    print(f"[{label}] docs={len(doc_tokens)} mean_tokens/doc={meta['mean_tokens_per_doc']:.1f}")


def main():
    manifest_meta = pd.read_csv(DATA_DIR / "metadata_representation.csv")
    study_ids_a = manifest_meta["Study_ID"].tolist()
    texts_a = manifest_meta["combined_text"].fillna("").tolist()
    run_pipeline(texts_a, study_ids_a, PREP_DIR / "metadata", "metadata")

    ft_manifest = pd.read_csv(DATA_DIR / "fulltext_representation_manifest.csv")
    study_ids_b = ft_manifest["Study_ID"].tolist()
    texts_b = []
    for sid in study_ids_b:
        texts_b.append((DATA_DIR / "fulltext_texts" / f"{sid}.txt").read_text(encoding="utf-8"))
    run_pipeline(texts_b, study_ids_b, PREP_DIR / "fulltext", "fulltext")


if __name__ == "__main__":
    main()
