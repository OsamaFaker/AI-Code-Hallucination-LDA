import csv
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from preprocessing import write_lemma_audit, preprocess_variant, get_plural_merge_map

ROOT = Path(__file__).resolve().parents[1]


def load_metadata_texts():
    with open(ROOT / "corpus" / "metadata_documents.csv", newline="", encoding="utf-8") as f:
        rows = list(csv.DictReader(f))
    ids = [r["Study_ID"] for r in rows]
    texts = [r["combined_text"] for r in rows]
    return ids, texts


def load_fulltext_texts():
    with open(ROOT / "corpus" / "corpus_audit.csv", newline="", encoding="utf-8") as f:
        mapping = [r["Study_ID"] for r in csv.DictReader(f)]
    ids, texts = [], []
    for sid in sorted(mapping, key=lambda x: int(x[1:])):
        p = ROOT / "extraction" / "fulltext" / f"{sid}.txt"
        ids.append(sid)
        texts.append(p.read_text(encoding="utf-8"))
    return ids, texts


if __name__ == "__main__":
    meta_ids, meta_texts = load_metadata_texts()
    ft_ids, ft_texts = load_fulltext_texts()
    assert len(meta_ids) == 66 and len(ft_ids) == 66

    write_lemma_audit(ROOT / "preprocessing" / "lemma_audit_metadata.md", "Metadata (Analysis A)", meta_ids, meta_texts)
    write_lemma_audit(ROOT / "preprocessing" / "lemma_audit_fulltext.md", "Full text (Analysis B)", ft_ids, ft_texts)

    # Quick sanity: vocab size under each of the 4 preprocessing variants, both representations
    for rep_name, texts in [("metadata", meta_texts), ("fulltext", ft_texts)]:
        plural_map = get_plural_merge_map(texts)
        for hf in ("A", "B"):
            for bigrams in (False, True):
                toks = preprocess_variant(texts, hf, bigrams, plural_map)
                vocab = set(t for doc in toks for t in doc)
                avg_len = sum(len(d) for d in toks) / len(toks)
                print(f"{rep_name} HF-{hf} bigrams={bigrams}: vocab={len(vocab)} avg_doc_tokens={avg_len:.1f}")
