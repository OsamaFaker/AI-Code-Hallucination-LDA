"""Section 21: representative seed = structural medoid (max mean aligned JS similarity to all
other seeded models at the selected k), never the max-coherence seed.
"""
import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parent))
from lda_core import align_topics_hungarian, js_similarity

ROOT = Path(__file__).resolve().parents[1]
RESULTS_DIR = ROOT / "results"
MODELS_DIR = ROOT / "models"


def select_medoid(label: str, k: int, seeds=range(20)):
    mats = {}
    for seed in seeds:
        p = MODELS_DIR / label / f"k{k:02d}_seed{seed:02d}_topicword.npy"
        if p.exists():
            mats[seed] = np.load(p)

    seed_list = list(mats.keys())
    n = len(seed_list)
    sim_matrix = np.zeros((n, n))
    for i in range(n):
        for j in range(i + 1, n):
            row_ind, col_ind = align_topics_hungarian(mats[seed_list[i]], mats[seed_list[j]])
            sims = [js_similarity(mats[seed_list[i]][r], mats[seed_list[j]][c])
                    for r, c in zip(row_ind, col_ind)]
            s = float(np.mean(sims))
            sim_matrix[i, j] = sim_matrix[j, i] = s
    mean_sim = sim_matrix.sum(axis=1) / (n - 1) if n > 1 else np.zeros(n)
    ranking = sorted(zip(seed_list, mean_sim.tolist()), key=lambda x: -x[1])
    medoid_seed, medoid_score = ranking[0]

    out_dir = RESULTS_DIR / label
    pd.DataFrame(sim_matrix, index=seed_list, columns=seed_list).to_csv(
        out_dir / f"seed_similarity_matrix_k{k:02d}.csv")
    pd.DataFrame(ranking, columns=["seed", "mean_structural_similarity"]).to_csv(
        out_dir / f"seed_ranking_k{k:02d}.csv", index=False)
    decision = {
        "representation": label, "k": k,
        "medoid_seed": int(medoid_seed), "medoid_mean_similarity": float(medoid_score),
        "n_seeds_considered": n,
    }
    with open(out_dir / f"representative_seed_k{k:02d}.json", "w", encoding="utf-8") as f:
        json.dump(decision, f, indent=2)
    print(f"[{label}] k={k}: medoid seed={medoid_seed} (mean sim={medoid_score:.3f})")
    return decision


if __name__ == "__main__":
    label, k = sys.argv[1], int(sys.argv[2])
    select_medoid(label, k)
