"""Section 10: per-token frequency / document-frequency profiling for both representations,
independent of any dictionary-threshold decision.
"""
import json
from collections import Counter
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
PREP_DIR = ROOT / "preprocessing"

# Domain terms called out explicitly in protocol Section 12 for controlled sensitivity
# analysis (never auto-treated as stopwords).
DOMAIN_TERMS = {
    "code", "coding", "model", "llm", "language", "generation", "generate", "ai",
    "artificial", "intelligence", "software", "developer", "programming", "study",
    "result", "approach", "method", "system",
}


def profile(label: str):
    with open(PREP_DIR / label / "lemmatized_tokens_corrected.json", encoding="utf-8") as f:
        doc_tokens = json.load(f)
    n_docs = len(doc_tokens)

    corpus_freq = Counter()
    doc_freq = Counter()
    for toks in doc_tokens.values():
        corpus_freq.update(toks)
        doc_freq.update(set(toks))

    with open(PREP_DIR / label / "spacy_stopwords.txt", encoding="utf-8") as f:
        stopwords = set(f.read().split("\n"))

    rows = []
    for term, cfreq in corpus_freq.items():
        dfreq = doc_freq[term]
        dfreq_pct = dfreq / n_docs
        is_domain = term in DOMAIN_TERMS
        candidate = dfreq_pct >= 0.5
        reason = ""
        if is_domain:
            reason = "substantive domain term (Section 12 list) - retained by default, evaluated via HF-A/B/C"
        elif candidate:
            reason = f"appears in {dfreq_pct:.0%} of documents - candidate for high-frequency review"
        rows.append({
            "term": term,
            "corpus_frequency": cfreq,
            "document_frequency": dfreq,
            "document_frequency_pct": round(dfreq_pct, 4),
            "standard_stopword": term in stopwords,
            "domain_specific": is_domain,
            "candidate_for_removal": candidate and not is_domain,
            "reason": reason,
        })
    df = pd.DataFrame(rows).sort_values("document_frequency", ascending=False)
    out_name = "metadata_high_frequency_terms.csv" if label == "metadata" else "fulltext_high_frequency_terms.csv"
    df.to_csv(PREP_DIR / out_name, index=False)
    print(f"[{label}] vocab(pre-dictionary-filter)={len(df)} "
          f"terms>=50% docs={int(df['document_frequency_pct'].ge(0.5).sum())}")


if __name__ == "__main__":
    profile("metadata")
    profile("fulltext")
