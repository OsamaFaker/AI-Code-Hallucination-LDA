"""Section 19: mandatory cross-seed stability. For each k, pairwise-align all 20 seeded models
(Hungarian algorithm on full topic-word JS distance), report mean/SD/median/min/max of the
primary (JS similarity), secondary (cosine), and supporting (top-20 Jaccard) metrics.
"""
import sys
from pathlib import Path

import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parent))
from lda_core import align_topics_hungarian, js_similarity

ROOT = Path(__file__).resolve().parents[1]
RESULTS_DIR = ROOT / "results"
MODELS_DIR = ROOT / "models"
TOP_N = 20


def top_n_indices(mat: np.ndarray, n=TOP_N) -> list[set]:
    return [set(np.argsort(-row)[:n].tolist()) for row in mat]


def run_for_representation(label: str, k_range=range(2, 21), seeds=range(20)):
    rows = []
    for k in k_range:
        mats = []
        for seed in seeds:
            p = MODELS_DIR / label / f"k{k:02d}_seed{seed:02d}_topicword.npy"
            if not p.exists():
                continue
            mats.append(np.load(p))
        if len(mats) < 2:
            continue
        js_sims, cos_sims, jacc_sims = [], [], []
        top_sets = [top_n_indices(m) for m in mats]
        for i in range(len(mats)):
            for j in range(i + 1, len(mats)):
                row_ind, col_ind = align_topics_hungarian(mats[i], mats[j])
                for r, c in zip(row_ind, col_ind):
                    js_sims.append(js_similarity(mats[i][r], mats[j][c]))
                    vi, vj = mats[i][r], mats[j][c]
                    cos_sims.append(float(np.dot(vi, vj) / (np.linalg.norm(vi) * np.linalg.norm(vj) + 1e-12)))
                    si, sj = top_sets[i][r], top_sets[j][c]
                    jacc_sims.append(len(si & sj) / len(si | sj) if (si or sj) else 0.0)
        def stats(a):
            a = np.array(a)
            return dict(mean=float(a.mean()), sd=float(a.std()), median=float(np.median(a)),
                        min=float(a.min()), max=float(a.max()))
        row = {"k": k, "n_seed_pairs": len(js_sims), "n_seeds_available": len(mats)}
        for name, vals in [("js_similarity", js_sims), ("cosine", cos_sims), ("top20_jaccard", jacc_sims)]:
            s = stats(vals)
            for stat_name, v in s.items():
                row[f"{name}_{stat_name}"] = v
        rows.append(row)
    df = pd.DataFrame(rows).sort_values("k")
    out_dir = RESULTS_DIR / label
    out_dir.mkdir(parents=True, exist_ok=True)
    df.to_csv(out_dir / "seed_stability_by_k.csv", index=False)
    print(f"[{label}] stability computed for {len(df)} k values")
    return df


if __name__ == "__main__":
    label = sys.argv[1] if len(sys.argv) > 1 else "metadata"
    run_for_representation(label)
