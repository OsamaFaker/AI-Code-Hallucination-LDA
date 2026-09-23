"""
Apply the FROZEN Stage-1 selection rules (PRE_EXECUTION_ANALYSIS_PLAN.md SS9)
to a completed results/{representation}/dictionary_sweep.csv.

Dictionary-selection rule: a config is eligible only if (a) zero empty docs
and (b) it is not an isolated maximum -- its four immediate grid neighbours
(+/-1 step in no_below, +/-1 step in no_above) have mean C_v within 0.03
absolute and preliminary stability within 0.05 absolute of the candidate.
Among eligible configs forming a contiguous stable region, the most
parsimonious member (highest no_below, lowest no_above) is selected. If none
qualify, the neighbourhood tolerance is relaxed by one fixed step and the
rule is re-applied (documented, not a retune).

Bigram / HF-A-vs-B retention rule: retained only if mean C_v exceeds the
alternative by >0.02 absolute AND stability is not lower by >0.03 absolute,
both at each variant's own best-selected dictionary config. Bigram decision
made first (averaged over HF-A/HF-B), then HF-A-vs-B decided using only the
variants matching the chosen bigram setting.

No LDA fitting here -- this only reads and reasons over Stage 1's CSV.
"""

from __future__ import annotations

import csv
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

NO_BELOW_GRID = [2, 3, 4, 5, 6]
NO_ABOVE_GRID = [0.40, 0.50, 0.60, 0.70, 0.75, 0.80, 0.90, 1.00]


def load_sweep(representation: str) -> list[dict]:
    path = ROOT / "results" / representation / "dictionary_sweep.csv"
    with open(path, newline="", encoding="utf-8") as f:
        rows = list(csv.DictReader(f))
    for r in rows:
        r["bigrams"] = r["bigrams"] == "True"
        r["no_below"] = int(r["no_below"])
        r["no_above"] = float(r["no_above"])
        for k in ("vocab_size", "empty_docs"):
            r[k] = int(r[k]) if r[k] not in (None, "", "None") else None
        for k in ("mean_cv", "sd_cv", "mean_cnpmi", "sd_cnpmi", "mean_diversity",
                   "mean_stability", "sd_stability", "pct_vocab_removed", "avg_doc_vocab"):
            r[k] = float(r[k]) if r[k] not in (None, "", "None") else None
    return rows


def select_dictionary_config(cells: list[dict], neighbour_tol_step: int = 1) -> tuple[dict, str]:
    """cells: the 40 dictionary-grid rows for ONE (hf, bigram) variant.
    Returns (selected_row, note)."""
    by_key = {(c["no_below"], c["no_above"]): c for c in cells}

    def neighbours(nb, na, step):
        nb_idx = NO_BELOW_GRID.index(nb)
        na_idx = NO_ABOVE_GRID.index(na)
        out = []
        for d in range(-step, step + 1):
            if d == 0:
                continue
            if 0 <= nb_idx + d < len(NO_BELOW_GRID):
                out.append((NO_BELOW_GRID[nb_idx + d], na))
            if 0 <= na_idx + d < len(NO_ABOVE_GRID):
                out.append((nb, NO_ABOVE_GRID[na_idx + d]))
        return out

    for relax_step in (neighbour_tol_step, neighbour_tol_step + 1, neighbour_tol_step + 2):
        eligible = []
        for c in cells:
            if c["vocab_size"] is None or c["mean_cv"] is None:
                continue  # degenerate (vocab too small to fit) -- never eligible
            if c["empty_docs"] != 0:
                continue
            nbs = neighbours(c["no_below"], c["no_above"], relax_step)
            is_isolated = False
            checked_any = False
            for key in nbs:
                nb_cell = by_key.get(key)
                if nb_cell is None or nb_cell["mean_cv"] is None:
                    continue
                checked_any = True
                if (abs(nb_cell["mean_cv"] - c["mean_cv"]) > 0.03 or
                        abs(nb_cell["mean_stability"] - c["mean_stability"]) > 0.05):
                    is_isolated = True
                    break
            if checked_any and not is_isolated:
                eligible.append(c)
        if eligible:
            # most parsimonious: highest no_below, then lowest no_above
            eligible.sort(key=lambda c: (-c["no_below"], c["no_above"]))
            note = (f"selected from {len(eligible)} eligible configs at neighbour "
                    f"tolerance step={relax_step}" +
                    (f" (relaxed from base step={neighbour_tol_step})" if relax_step > neighbour_tol_step else ""))
            return eligible[0], note

    # Fallback: should not happen with a 5x8 grid, but guard anyway.
    valid = [c for c in cells if c["mean_cv"] is not None and c["empty_docs"] == 0]
    valid.sort(key=lambda c: (-c["no_below"], c["no_above"]))
    return valid[0], "FALLBACK: no eligible stable-region config found at any relaxation; " \
                      "used most parsimonious zero-empty-doc config (protocol note)"


def decide_variant(representation: str, rows: list[dict]) -> dict:
    variants = {}
    for hf in ("A", "B"):
        for bigrams in (False, True):
            cells = [r for r in rows if r["hf_variant"] == hf and r["bigrams"] == bigrams]
            assert len(cells) == 40, f"expected 40 cells, got {len(cells)} for HF-{hf} bigrams={bigrams}"
            best, note = select_dictionary_config(cells)
            variants[(hf, bigrams)] = {"config": best, "note": note}

    # Step 1: bigram vs unigram, averaged over HF-A and HF-B
    uni_cv = (variants[("A", False)]["config"]["mean_cv"] + variants[("B", False)]["config"]["mean_cv"]) / 2
    bi_cv = (variants[("A", True)]["config"]["mean_cv"] + variants[("B", True)]["config"]["mean_cv"]) / 2
    uni_stab = (variants[("A", False)]["config"]["mean_stability"] + variants[("B", False)]["config"]["mean_stability"]) / 2
    bi_stab = (variants[("A", True)]["config"]["mean_stability"] + variants[("B", True)]["config"]["mean_stability"]) / 2

    bigram_advantage = bi_cv - uni_cv
    bigram_stability_loss = uni_stab - bi_stab
    use_bigrams = bigram_advantage > 0.02 and bigram_stability_loss < 0.03

    # Step 2: HF-A vs HF-B, using only the variants matching the chosen bigram setting
    a_cell = variants[("A", use_bigrams)]["config"]
    b_cell = variants[("B", use_bigrams)]["config"]
    hf_advantage = b_cell["mean_cv"] - a_cell["mean_cv"]
    hf_stability_loss = a_cell["mean_stability"] - b_cell["mean_stability"]
    use_hf_b = hf_advantage > 0.02 and hf_stability_loss < 0.03
    chosen_hf = "B" if use_hf_b else "A"

    final = variants[(chosen_hf, use_bigrams)]
    return {
        "representation": representation,
        "variants": variants,
        "bigram_advantage": bigram_advantage,
        "bigram_stability_loss": bigram_stability_loss,
        "use_bigrams": use_bigrams,
        "hf_advantage": hf_advantage,
        "hf_stability_loss": hf_stability_loss,
        "chosen_hf": chosen_hf,
        "final_config": final["config"],
        "final_note": final["note"],
    }


def write_decision_report(decision: dict) -> None:
    rep = decision["representation"]
    out_path = ROOT / "results" / rep / "stage1_decision.md"
    with open(out_path, "w", encoding="utf-8") as f:
        f.write(f"# Stage 1 Decision -- {rep}\n\n")
        f.write("Per the frozen rules in PRE_EXECUTION_ANALYSIS_PLAN.md SS9.\n\n")

        f.write("## Per-variant best dictionary config (frozen selection rule)\n\n")
        f.write("| HF | bigrams | no_below | no_above | vocab | empty_docs | mean_cv | mean_stability | note |\n")
        f.write("|---|---|---|---|---|---|---|---|---|\n")
        for (hf, bigrams), v in decision["variants"].items():
            c = v["config"]
            f.write(f"| {hf} | {bigrams} | {c['no_below']} | {c['no_above']} | {c['vocab_size']} | "
                    f"{c['empty_docs']} | {c['mean_cv']:.4f} | {c['mean_stability']:.4f} | {v['note']} |\n")
        f.write("\n")

        f.write("## Step 1: unigram vs. bigram\n\n")
        f.write(f"- Bigram mean C_v advantage (averaged over HF-A/HF-B): {decision['bigram_advantage']:.4f} "
                f"(threshold: >0.02)\n")
        f.write(f"- Bigram stability loss: {decision['bigram_stability_loss']:.4f} (threshold: <0.03)\n")
        f.write(f"- **Decision: {'RETAIN bigrams' if decision['use_bigrams'] else 'unigram (default)'}**\n\n")

        f.write("## Step 2: HF-A vs. HF-B (at the chosen bigram setting)\n\n")
        f.write(f"- HF-B mean C_v advantage over HF-A: {decision['hf_advantage']:.4f} (threshold: >0.02)\n")
        f.write(f"- HF-B stability loss: {decision['hf_stability_loss']:.4f} (threshold: <0.03)\n")
        f.write(f"- **Decision: HF-{decision['chosen_hf']} "
                f"({'retain domain terms' if decision['chosen_hf']=='A' else 'remove HF-B filler list'})**\n\n")

        fc = decision["final_config"]
        f.write("## FINAL Stage 1 configuration\n\n")
        f.write(f"- HF variant: **HF-{decision['chosen_hf']}**\n")
        f.write(f"- Bigrams: **{decision['use_bigrams']}**\n")
        f.write(f"- no_below: **{fc['no_below']}**\n")
        f.write(f"- no_above: **{fc['no_above']}**\n")
        f.write(f"- Vocabulary size: **{fc['vocab_size']}**\n")
        f.write(f"- Empty documents: **{fc['empty_docs']}**\n")
        f.write(f"- Pilot mean C_v: **{fc['mean_cv']:.4f}** (SD {fc['sd_cv']:.4f})\n")
        f.write(f"- Pilot mean C_NPMI: **{fc['mean_cnpmi']:.4f}** (SD {fc['sd_cnpmi']:.4f})\n")
        f.write(f"- Pilot mean stability: **{fc['mean_stability']:.4f}** (SD {fc['sd_stability']:.4f})\n")
        f.write(f"- Pilot mean diversity: **{fc['mean_diversity']:.4f}**\n")
        f.write(f"- Selection note: {decision['final_note']}\n")

    print(f"Wrote {out_path}")
    print(f"[{rep}] FINAL: HF-{decision['chosen_hf']}, bigrams={decision['use_bigrams']}, "
          f"no_below={fc['no_below']}, no_above={fc['no_above']}, vocab={fc['vocab_size']}")


def main():
    reps = sys.argv[1:] or ["metadata", "fulltext"]
    for rep in reps:
        rows = load_sweep(rep)
        decision = decide_variant(rep, rows)
        write_decision_report(decision)


if __name__ == "__main__":
    main()
