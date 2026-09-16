"""Section 8: lemmatization quality audit. Surfaces candidate systematic lemmatization
errors (dominant surface form far from the assigned lemma) for manual review, and applies
only deterministic, corpus-wide, pre-documented corrections.
"""
import json
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
PREP_DIR = ROOT / "preprocessing"

# Deterministic, corpus-wide corrections identified by manual review of the top candidates
# below. Applied identically to every occurrence, in every study, in both representations.
# Format: erroneous_lemma -> corrected_lemma
LEMMA_CORRECTIONS = {
    "datum": "data",  # spaCy over-singularizes "data" -> "datum"; "data" is the standard
                        # form in this software-engineering corpus and "datum" never occurs
                        # as a surface form.
}


def levenshtein(a: str, b: str) -> int:
    if a == b:
        return 0
    m, n = len(a), len(b)
    dp = list(range(n + 1))
    for i in range(1, m + 1):
        prev, dp[0] = dp[0], i
        for j in range(1, n + 1):
            cur = dp[j]
            dp[j] = min(dp[j] + 1, dp[j - 1] + 1, prev + (a[i - 1] != b[j - 1]))
            prev = cur
    return dp[n]


def audit_one(label: str, rows_out: list[dict]):
    d = PREP_DIR / label
    with open(d / "lemma_surface_map.json", encoding="utf-8") as f:
        lemma_map = json.load(f)

    candidates = []
    for lemma, surfaces in lemma_map.items():
        total = sum(surfaces.values())
        dominant_surface = max(surfaces, key=surfaces.get)
        dist = levenshtein(lemma, dominant_surface)
        # Flag only cases where the lemma is not a simple suffix-trim/pluralization of the
        # dominant surface form (i.e. genuinely surprising, not routine morphology).
        if dist >= 3 and not dominant_surface.startswith(lemma[: max(3, len(lemma) - 2)]):
            candidates.append({
                "representation": label,
                "lemma": lemma,
                "dominant_surface": dominant_surface,
                "edit_distance": dist,
                "total_occurrences": total,
                "n_studies_affected": None,  # filled below if needed
            })
    candidates.sort(key=lambda r: -r["total_occurrences"])
    rows_out.extend(candidates[:60])  # top 60 by frequency for manual review


def apply_corrections():
    rows = []
    for label in ["metadata", "fulltext"]:
        d = PREP_DIR / label
        with open(d / "lemmatized_tokens.json", encoding="utf-8") as f:
            doc_tokens = json.load(f)
        n_docs_affected = 0
        n_occurrences = 0
        for sid, toks in doc_tokens.items():
            new_toks = []
            affected_here = False
            for t in toks:
                if t in LEMMA_CORRECTIONS:
                    new_toks.append(LEMMA_CORRECTIONS[t])
                    n_occurrences += 1
                    affected_here = True
                else:
                    new_toks.append(t)
            doc_tokens[sid] = new_toks
            if affected_here:
                n_docs_affected += 1
        with open(d / "lemmatized_tokens_corrected.json", "w", encoding="utf-8") as f:
            json.dump(doc_tokens, f)
        for orig, corrected in LEMMA_CORRECTIONS.items():
            rows.append({
                "representation": label,
                "original_token": orig,
                "erroneous_lemma": orig,
                "corrected_lemma": corrected,
                "affected_studies": n_docs_affected,
                "occurrences": n_occurrences,
                "justification": (
                    "Deterministic, corpus-wide: spaCy's lemmatizer maps the common English "
                    "noun 'data' to the classical-Latin singular 'datum', which never occurs "
                    "as a surface form in this software-engineering corpus and would "
                    "fragment a high-frequency, topically important term across two lemmas."
                ),
            })
    return rows


def main():
    review_rows = []
    for label in ["metadata", "fulltext"]:
        audit_one(label, review_rows)
    pd.DataFrame(review_rows).to_csv(PREP_DIR / "lemma_audit_review_candidates.csv", index=False)

    correction_rows = apply_corrections()
    pd.DataFrame(correction_rows).to_csv(PREP_DIR / "lemma_corrections.csv", index=False)
    print(f"Reviewed {len(review_rows)} candidate lemmas; applied {len(LEMMA_CORRECTIONS)} "
          f"deterministic corrections.")


if __name__ == "__main__":
    main()
