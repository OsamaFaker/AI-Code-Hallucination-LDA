"""
Apply the FROZEN Stage-2 prior and convergence selection rules
(PRE_EXECUTION_ANALYSIS_PLAN.md SS10) to completed
results/{representation}/{prior_sweep,convergence_sweep}.csv.

Convergence rule: smallest (passes, iterations) for which mean aligned JS
similarity >= 0.95 AND dominant-topic agreement >= 0.95 relative to the next
larger grid combination. If none qualifies before the largest cell, use the
largest cell and report non-convergence explicitly.

Prior rule: among priors within 0.02 absolute C_v and 0.03 absolute stability
of the single best-C_v prior, prefer alpha=eta='auto' if it is among them;
otherwise use the single best-C_v prior directly.
"""

from __future__ import annotations

import csv
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def select_convergence(representation: str) -> dict:
    path = ROOT / "results" / representation / "convergence_sweep.csv"
    with open(path, newline="", encoding="utf-8") as f:
        rows = list(csv.DictReader(f))
    for r in rows:
        r["passes"] = int(r["passes"])
        r["iterations"] = int(r["iterations"])
        r["effort"] = int(r["effort"])
        r["mean_js_vs_next"] = float(r["mean_js_vs_next"]) if r["mean_js_vs_next"] not in (None, "", "None") else None
        r["mean_dom_agreement_vs_next"] = (
            float(r["mean_dom_agreement_vs_next"]) if r["mean_dom_agreement_vs_next"] not in (None, "", "None") else None
        )
    rows.sort(key=lambda r: r["effort"])

    for r in rows:
        if r["mean_js_vs_next"] is None:
            continue  # last cell, nothing to compare against
        if r["mean_js_vs_next"] >= 0.95 and r["mean_dom_agreement_vs_next"] >= 0.95:
            return {"passes": r["passes"], "iterations": r["iterations"], "converged": True,
                     "js": r["mean_js_vs_next"], "dom_agree": r["mean_dom_agreement_vs_next"]}

    last = rows[-1]
    return {"passes": last["passes"], "iterations": last["iterations"], "converged": False,
             "js": None, "dom_agree": None}


def _coerce_prior(value: str):
    """CSV round-trips everything as a string; gensim's LdaModel only
    accepts the literal strings 'auto'/'symmetric' or an actual numeric
    type for alpha/eta -- a numeric-looking string like '1.0' is rejected."""
    if value in ("auto", "symmetric"):
        return value
    return float(value)


def select_priors(representation: str) -> dict:
    path = ROOT / "results" / representation / "prior_sweep.csv"
    with open(path, newline="", encoding="utf-8") as f:
        rows = list(csv.DictReader(f))
    for r in rows:
        r["mean_cv"] = float(r["mean_cv"])
        r["mean_stability"] = float(r["mean_stability"])

    best = max(rows, key=lambda r: r["mean_cv"])
    comparable = [
        r for r in rows
        if abs(r["mean_cv"] - best["mean_cv"]) <= 0.02 and abs(r["mean_stability"] - best["mean_stability"]) <= 0.03
    ]
    auto_row = next((r for r in comparable if r["alpha"] == "auto" and r["eta"] == "auto"), None)
    chosen = auto_row if auto_row is not None else best
    return {
        "alpha": _coerce_prior(chosen["alpha"]), "eta": _coerce_prior(chosen["eta"]),
        "mean_cv": chosen["mean_cv"], "mean_stability": chosen["mean_stability"],
        "best_alpha": best["alpha"], "best_eta": best["eta"], "best_cv": best["mean_cv"],
        "n_comparable": len(comparable), "used_auto_preference": auto_row is not None,
    }


def write_report(representation: str) -> None:
    conv = select_convergence(representation)
    priors = select_priors(representation)
    out_path = ROOT / "results" / representation / "stage2_decision.md"
    with open(out_path, "w", encoding="utf-8") as f:
        f.write(f"# Stage 2 Decision -- {representation}\n\n")
        f.write("## Priors\n\n")
        f.write(f"- Best-C_v prior: alpha={priors['best_alpha']}, eta={priors['best_eta']} "
                f"(C_v={priors['best_cv']:.4f})\n")
        f.write(f"- Priors within tolerance of best (comparable set): {priors['n_comparable']}\n")
        f.write(f"- auto/auto in comparable set: {priors['used_auto_preference']}\n")
        f.write(f"- **Selected: alpha={priors['alpha']}, eta={priors['eta']}** "
                f"(C_v={priors['mean_cv']:.4f}, stability={priors['mean_stability']:.4f})\n\n")

        f.write("## Convergence / training budget\n\n")
        if conv["converged"]:
            f.write(f"- Converged at passes={conv['passes']}, iterations={conv['iterations']} "
                    f"(JS vs next={conv['js']:.4f} >= 0.95, dominant-topic agreement={conv['dom_agree']:.4f} >= 0.95)\n")
        else:
            f.write(f"- **NON-CONVERGENCE**: no grid combination reached the 0.95/0.95 threshold before the "
                    f"largest cell. Using passes={conv['passes']}, iterations={conv['iterations']} "
                    f"(largest grid cell) and reporting this explicitly rather than extrapolating, "
                    f"per plan SS10.\n")
        f.write(f"- **Selected: passes={conv['passes']}, iterations={conv['iterations']}**\n\n")

        f.write("## FROZEN Stage 2 configuration\n\n")
        f.write(f"- alpha = **{priors['alpha']}**\n")
        f.write(f"- eta = **{priors['eta']}**\n")
        f.write(f"- passes = **{conv['passes']}**\n")
        f.write(f"- iterations = **{conv['iterations']}**\n\n")
        f.write("These four values are frozen and used, together with the Stage 1 dictionary/preprocessing "
                "config, for the Stage 3 definitive k-sweep. Not revisited except via a documented protocol "
                "amendment (plan SS35).\n")

    print(f"Wrote {out_path}")
    print(f"[{representation}] FROZEN: alpha={priors['alpha']} eta={priors['eta']} "
          f"passes={conv['passes']} iterations={conv['iterations']} (converged={conv['converged']})")


def main():
    reps = sys.argv[1:] or ["metadata", "fulltext"]
    for rep in reps:
        write_report(rep)


if __name__ == "__main__":
    main()
