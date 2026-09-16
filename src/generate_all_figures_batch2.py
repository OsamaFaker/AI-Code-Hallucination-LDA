"""Batch 2: robustness (R1-R8), human-validation (HM1-3, HF1-5), cross-representation (C1-C6)."""
import json
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

import sys
sys.path.insert(0, str(Path(__file__).resolve().parent))
from generate_all_figures import _save, THIS_SCRIPT  # reuse save/registry helper

ROOT = Path(__file__).resolve().parents[1]
RESULTS_DIR = ROOT / "results"
FIG_DIR = ROOT / "figures"
HV_DIR = ROOT / "human_validation"

plt.rcParams.update({
    "figure.dpi": 150, "savefig.dpi": 300, "font.size": 10,
    "axes.spines.top": False, "axes.spines.right": False,
})


# ---------------------------------------------------------------------------
# Robustness
# ---------------------------------------------------------------------------
def fig_subsampling_distributions():
    for metric, code, label in [("topic_similarity_js", "R1", "Topic similarity (JS)"),
                                  ("ari", "R2", "Adjusted Rand Index"),
                                  ("nmi", "R3", "Normalized Mutual Information")]:
        fig, axes = plt.subplots(1, 2, figsize=(9, 4), sharey=True)
        for ax, rep in zip(axes, ["metadata", "fulltext"]):
            df = pd.read_csv(RESULTS_DIR / rep / "subsampling_80pct_100reps.csv")
            ax.hist(df[metric], bins=20, color="#4C72B0" if rep == "metadata" else "#DD8452",
                    edgecolor="white")
            ax.axvline(df[metric].mean(), color="black", linestyle="--", label="mean")
            ax.set_title(f"{rep} (N=66, 100 reps)")
            ax.set_xlabel(label)
        axes[0].set_ylabel("Repetitions (n)")
        axes[0].legend()
        fig.suptitle(f"{code}: 100x 80% subsampling - {label} distribution")
        fig.tight_layout()
        _save(fig, FIG_DIR / "robustness" / f"{code}_subsampling_{metric}",
              f"Distribution of {label} across 100 repetitions of 80% document subsampling, "
              "both representations.", "robustness",
              "results/{metadata,fulltext}/subsampling_80pct_100reps.csv", THIS_SCRIPT)


def fig_training_effort():
    rows = []
    for rep in ["metadata", "fulltext"]:
        with open(RESULTS_DIR / rep / "training_effort_sensitivity.json", encoding="utf-8") as f:
            d = json.load(f)
        rows.append({"representation": rep, "JS similarity": d["mean_js_similarity"],
                      "Dominant-topic agreement": d["dominant_topic_agreement"]})
    df = pd.DataFrame(rows).set_index("representation")
    fig, ax = plt.subplots(figsize=(6, 4))
    df.plot(kind="bar", ax=ax, color=["#4C72B0", "#DD8452"])
    ax.set_ylim(0, 1.05); ax.set_ylabel("Value"); ax.set_xticklabels(df.index, rotation=0)
    ax.set_title("R4: Training-effort sensitivity (frozen budget vs. 3x boosted budget)")
    for c in ax.containers:
        ax.bar_label(c, fmt="%.3f", fontsize=8)
    fig.tight_layout()
    _save(fig, FIG_DIR / "robustness" / "R4_training_effort_sensitivity",
          "Topic-word JS similarity and dominant-topic agreement between the frozen training "
          "budget (passes=30, iterations=800) and a 3x boosted budget, both representations.",
          "robustness", "results/{metadata,fulltext}/training_effort_sensitivity.json", THIS_SCRIPT)


def fig_dictionary_sensitivity():
    fig, axes = plt.subplots(1, 2, figsize=(10, 4))
    for ax, rep in zip(axes, ["metadata", "fulltext"]):
        df = pd.read_csv(RESULTS_DIR / rep / "dictionary_sensitivity.csv")
        labels = [f"{r.varied_param}\n({r.no_below},{r.no_above})" for r in df.itertuples()]
        ax.bar(labels, df["mean_js_similarity_to_base"], color="#55A868")
        ax.set_ylim(0, 1); ax.set_ylabel("JS similarity to frozen config")
        ax.set_title(rep); ax.tick_params(axis="x", labelsize=7)
    fig.suptitle("R5: Dictionary-neighbor sensitivity")
    fig.tight_layout()
    _save(fig, FIG_DIR / "robustness" / "R5_dictionary_sensitivity",
          "Topic-word similarity between the frozen dictionary config and each neighboring "
          "no_below/no_above value, both representations.", "robustness",
          "results/{metadata,fulltext}/dictionary_sensitivity.csv", THIS_SCRIPT)


def fig_hf_term_sensitivity():
    fig, axes = plt.subplots(1, 2, figsize=(9, 4))
    for ax, rep in zip(axes, ["metadata", "fulltext"]):
        with open(RESULTS_DIR / rep / "domain_term_sensitivity.json", encoding="utf-8") as f:
            d = json.load(f)
        cats = ["HF-A\n(retain all)", "HF-B\n(remove ubiquitous)"]
        cv = [d["HF_A_retain_all"]["mean_c_v"], d["HF_B_remove_ubiquitous_domain_terms"]["mean_c_v"]]
        ax.bar(cats, cv, color=["#4C72B0", "#C44E52"])
        ax.set_ylabel("Mean C_v"); ax.set_title(f"{rep}\nARI={d['HF_A_vs_HF_B_document_assignment_ARI']:.3f}")
        for i, v in enumerate(cv):
            ax.text(i, v + 0.005, f"{v:.3f}", ha="center", fontsize=8)
    fig.suptitle("R6: High-frequency domain-term sensitivity (HF-A vs. HF-B)")
    fig.tight_layout()
    _save(fig, FIG_DIR / "robustness" / "R6_hf_term_sensitivity",
          "Coherence and document-assignment agreement between retaining vs. removing "
          "ubiquitous domain terms, both representations.", "robustness",
          "results/{metadata,fulltext}/domain_term_sensitivity.json", THIS_SCRIPT)


def fig_phrase_sensitivity():
    fig, axes = plt.subplots(1, 2, figsize=(9, 4))
    for ax, rep in zip(axes, ["metadata", "fulltext"]):
        with open(RESULTS_DIR / rep / "phrase_sensitivity.json", encoding="utf-8") as f:
            d = json.load(f)
        cats = ["Unigram only", "Unigram+bigram"]
        cv = [d["unigram_only"]["mean_c_v"], d["unigram_plus_bigram"]["mean_c_v"]]
        ax.bar(cats, cv, color=["#4C72B0", "#8172B2"])
        ax.set_ylabel("Mean C_v")
        ax.set_title(f"{rep}\n{d['n_discovered_phrases_in_vocab']} phrases discovered, "
                     f"ARI={d['unigram_vs_bigram_document_assignment_ARI']:.3f}")
        for i, v in enumerate(cv):
            ax.text(i, v + 0.005, f"{v:.3f}", ha="center", fontsize=8)
    fig.suptitle("R7: Phrase-detection sensitivity (unigram vs. unigram+bigram)")
    fig.tight_layout()
    _save(fig, FIG_DIR / "robustness" / "R7_phrase_sensitivity",
          "Coherence and document-assignment agreement between unigram-only and "
          "unigram+bigram tokenization, both representations.", "robustness",
          "results/{metadata,fulltext}/phrase_sensitivity.json", THIS_SCRIPT)


def fig_robustness_matrix():
    rows = []
    for rep in ["metadata", "fulltext"]:
        with open(RESULTS_DIR / rep / "training_effort_sensitivity.json", encoding="utf-8") as f:
            te = json.load(f)
        subs = pd.read_csv(RESULTS_DIR / rep / "subsampling_80pct_100reps.csv")
        dict_s = pd.read_csv(RESULTS_DIR / rep / "dictionary_sensitivity.csv")
        rows.append({
            "Representation": rep,
            "Training-effort JS": round(te["mean_js_similarity"], 3),
            "Training-effort dom. agree.": round(te["dominant_topic_agreement"], 3),
            "Subsample JS (mean)": round(subs["topic_similarity_js"].mean(), 3),
            "Subsample ARI (mean)": round(subs["ari"].mean(), 3),
            "Dictionary-neighbor JS (mean)": round(dict_s["mean_js_similarity_to_base"].mean(), 3),
        })
    df = pd.DataFrame(rows).set_index("Representation")
    fig, ax = plt.subplots(figsize=(9, 2.2))
    ax.axis("off")
    tbl = ax.table(cellText=df.values, rowLabels=df.index, colLabels=df.columns,
                    cellLoc="center", loc="center")
    tbl.auto_set_font_size(False); tbl.set_fontsize(8); tbl.scale(1, 1.8)
    ax.set_title("R8: Robustness evidence matrix (actual values, not scored)", pad=20)
    fig.tight_layout()
    _save(fig, FIG_DIR / "robustness" / "R8_robustness_evidence_matrix",
          "Consolidated robustness metrics for both representations, reported as actual "
          "values (no subjective good/bad scoring).", "robustness",
          "results/{metadata,fulltext}/*", THIS_SCRIPT)
    df.to_csv(RESULTS_DIR / "robustness_evidence_matrix.csv")


# ---------------------------------------------------------------------------
# Human validation (now uses REAL data)
# ---------------------------------------------------------------------------
def fig_human_metadata():
    df = pd.read_csv(HV_DIR / "metadata_human_model_scores.csv")
    fig, ax = plt.subplots(figsize=(7, 4.5))
    x = np.arange(len(df)); w = 0.25
    ax.bar(x - w, df.mean_coherence, w, label="Coherence", color="#4C72B0")
    ax.bar(x, df.mean_interpretability, w, label="Interpretability", color="#55A868")
    ax.bar(x + w, df.mean_distinctiveness, w, label="Distinctiveness", color="#DD8452")
    ax.set_xticks(x); ax.set_xticklabels([f"Model {m}\n(k={k})" for m, k in zip(df.blinded_model, df.k)])
    ax.set_ylim(0, 5); ax.set_ylabel("Mean rating (1-5)")
    ax.legend()
    ax.set_title("HM1: Human ratings across blinded candidate models (2 raters, N=66 studies)")
    fig.tight_layout()
    _save(fig, FIG_DIR / "human_validation" / "HM1_ratings_by_candidate_model",
          "Combined (2-rater) mean coherence/interpretability/distinctiveness per blinded "
          "metadata candidate model (k=2,3,4,5).", "metadata human validation",
          "human_validation/metadata_human_model_scores.csv", THIS_SCRIPT)

    raw = pd.read_csv(HV_DIR / "metadata_human_ratings_per_topic.csv")
    per_rater_model = raw.groupby(["rater", "blinded_model", "k"])[
        ["coherence_1_5", "interpretability_1_5", "distinctiveness_1_5"]].mean().reset_index()
    per_rater_model["overall"] = per_rater_model[
        ["coherence_1_5", "interpretability_1_5", "distinctiveness_1_5"]].mean(axis=1)
    pivot = per_rater_model.pivot(index="k", columns="rater", values="overall")
    fig, ax = plt.subplots(figsize=(6, 4))
    pivot.plot(kind="bar", ax=ax, color=["#4C72B0", "#C44E52"])
    ax.set_ylabel("Mean overall rating (1-5)"); ax.set_xlabel("k")
    ax.set_xticklabels(pivot.index, rotation=0)
    ax.set_title("HM2: Rater comparison by candidate model")
    fig.tight_layout()
    _save(fig, FIG_DIR / "human_validation" / "HM2_rater_comparison_by_model",
          "Per-rater mean overall rating by candidate k, showing Rater 1 scoring "
          "systematically higher than Rater 2.", "metadata human validation",
          "human_validation/metadata_human_ratings_per_topic.csv", THIS_SCRIPT)

    prefs = pd.read_csv(HV_DIR / "metadata_human_overall_preferences.csv")
    fig, ax = plt.subplots(figsize=(6, 4))
    ks = [2, 3, 4, 5]
    r1_pref = [1 if prefs[prefs.rater_id.str.contains("1")].preferred_k.iloc[0] == k else 0 for k in ks]
    r2_pref = [1 if prefs[prefs.rater_id.str.contains("2")].preferred_k.iloc[0] == k else 0 for k in ks]
    x = np.arange(len(ks)); w = 0.35
    ax.bar(x - w / 2, r1_pref, w, label="Rater 1", color="#4C72B0")
    ax.bar(x + w / 2, r2_pref, w, label="Rater 2", color="#C44E52")
    ax.set_xticks(x); ax.set_xticklabels([f"k={k}" for k in ks])
    ax.set_ylabel("Preferred (1) / not preferred (0)")
    ax.set_ylim(0, 1.3)
    ax.axvline(1.5, color="gray", linestyle=":", alpha=0.5)
    ax.text(x[np.array(ks) == 4][0], 1.1, "quantitatively\nselected (k=4)\nwas neither\nrater's pick",
            ha="center", fontsize=7, style="italic")
    ax.legend()
    ax.set_title("HM3: Preferred topic count - raters DISAGREE (R1->k=5, R2->k=3)")
    fig.tight_layout()
    _save(fig, FIG_DIR / "human_validation" / "HM3_preferred_topic_count",
          "Each rater's single preferred candidate model, making explicit that the two "
          "raters preferred different k values and neither chose k=4.", "metadata human validation",
          "human_validation/metadata_human_overall_preferences.csv", THIS_SCRIPT,
          "Main manuscript (candidate: Main Figure A, paired with M8)")


def fig_human_fulltext():
    df = pd.read_csv(HV_DIR / "fulltext_human_ratings_per_topic.csv")
    fig, axes = plt.subplots(1, 3, figsize=(13, 4), sharey=True)
    for ax, col, title in zip(axes, ["mean_coherence", "mean_interpretability", "mean_distinctiveness"],
                                ["HF1: Coherence", "HF2: Interpretability", "HF3: Distinctiveness"]):
        ax.bar(df.topic_id, df[col], color="#4C72B0")
        ax.set_xlabel("Topic"); ax.set_title(title); ax.set_xticks(df.topic_id)
        ax.set_ylim(0, 5)
    axes[0].set_ylabel("Combined mean rating (1-5)")
    fig.suptitle("HF1-3: Full-text (k=8) human ratings by topic (2 raters)")
    fig.tight_layout()
    _save(fig, FIG_DIR / "human_validation" / "HF1_3_ratings_by_topic",
          "Combined mean coherence, interpretability, and distinctiveness per full-text final "
          "topic (k=8).", "fulltext human validation",
          "human_validation/fulltext_human_ratings_per_topic.csv", THIS_SCRIPT,
          "Main manuscript (candidate: supports Main Figure B/D)")

    raw = pd.read_csv(HV_DIR / "fulltext_human_ratings_raw.csv")
    raw["overall"] = raw[["coherence_1_5", "interpretability_1_5", "distinctiveness_1_5"]].mean(axis=1)
    pivot = raw.pivot(index="topic_id", columns="rater", values="overall")
    fig, ax = plt.subplots(figsize=(7, 4))
    pivot.plot(kind="bar", ax=ax, color=["#4C72B0", "#C44E52"])
    ax.set_ylabel("Mean overall rating (1-5)"); ax.set_xlabel("Topic")
    ax.set_xticklabels(pivot.index, rotation=0)
    ax.set_title("HF4: Rater comparison by topic")
    fig.tight_layout()
    _save(fig, FIG_DIR / "human_validation" / "HF4_rater_comparison",
          "Per-rater mean overall rating by full-text topic.", "fulltext human validation",
          "human_validation/fulltext_human_ratings_raw.csv", THIS_SCRIPT)

    fig, ax = plt.subplots(figsize=(6, 6), subplot_kw={"polar": True})
    cats = [f"T{t}" for t in df.topic_id]
    n = len(cats)
    angles = np.linspace(0, 2 * np.pi, n, endpoint=False).tolist()
    for col, color, label in [("mean_coherence", "#4C72B0", "Coherence"),
                                ("mean_interpretability", "#55A868", "Interpretability"),
                                ("mean_distinctiveness", "#DD8452", "Distinctiveness")]:
        vals = df[col].tolist(); vals += vals[:1]; ang = angles + angles[:1]
        ax.plot(ang, vals, label=label, color=color)
        ax.fill(ang, vals, color=color, alpha=0.1)
    ax.set_xticks(angles); ax.set_xticklabels(cats)
    ax.set_ylim(0, 5)
    ax.set_title("HF5: Combined human-validation profile (k=8)")
    ax.legend(loc="upper right", bbox_to_anchor=(1.3, 1.1), fontsize=8)
    fig.tight_layout()
    _save(fig, FIG_DIR / "human_validation" / "HF5_combined_profile",
          "Radar plot of combined coherence/interpretability/distinctiveness across all 8 "
          "full-text topics.", "fulltext human validation",
          "human_validation/fulltext_human_ratings_per_topic.csv", THIS_SCRIPT)


# ---------------------------------------------------------------------------
# Cross-representation
# ---------------------------------------------------------------------------
def fig_cross_representation():
    with open(RESULTS_DIR / "cross_representation" / "topic_alignment.json", encoding="utf-8") as f:
        align = json.load(f)
    matched = pd.DataFrame(align["matched_topics"])

    fig, ax = plt.subplots(figsize=(7, 4.5))
    x = np.arange(len(matched)); w = 0.25
    ax.bar(x - w, matched.js_similarity, w, label="JS similarity", color="#4C72B0")
    ax.bar(x, matched.cosine, w, label="Cosine", color="#55A868")
    ax.bar(x + w, matched.top20_jaccard, w, label="Top-20 Jaccard", color="#DD8452")
    ax.set_xticks(x)
    ax.set_xticklabels([f"metaT{m}\n-fullT{f}" for m, f in
                          zip(matched.metadata_topic, matched.fulltext_topic)], fontsize=8)
    ax.set_ylim(0, 1); ax.legend()
    ax.set_title(f"C3: Matched-topic similarity (JS, cosine, Jaccard); "
                 f"ARI={align['document_assignment_ari']:.3f}, NMI={align['document_assignment_nmi']:.3f}")
    fig.tight_layout()
    _save(fig, FIG_DIR / "comparison" / "C3_similarity_comparison",
          "JS similarity, cosine, and top-20 Jaccard for each matched metadata-fulltext "
          "topic pair.", "cross-representation",
          "results/cross_representation/topic_alignment.json", THIS_SCRIPT)

    from gensim.models import LdaModel
    with open(ROOT / "preprocessing/metadata/lemmatized_tokens_corrected.json", encoding="utf-8") as f:
        toks_m = json.load(f)
    with open(ROOT / "preprocessing/fulltext/lemmatized_tokens_corrected.json", encoding="utf-8") as f:
        toks_f = json.load(f)
    sys.path.insert(0, str(Path(__file__).resolve().parent))
    from lda_core import build_bow_corpus, build_dictionary, doc_topic_matrix
    dict_m = build_dictionary(list(toks_m.values()), 5, 0.50)
    dict_f = build_dictionary(list(toks_f.values()), 4, 0.75)
    bow_m = build_bow_corpus(list(toks_m.values()), dict_m)
    bow_f = build_bow_corpus(list(toks_f.values()), dict_f)
    model_m = LdaModel.load(str(ROOT / "models/metadata/k04_seed14.model"))
    model_f = LdaModel.load(str(ROOT / "models/fulltext/k08_seed02.model"))
    prev_m = doc_topic_matrix(model_m, bow_m).mean(axis=0)
    prev_f = doc_topic_matrix(model_f, bow_f).mean(axis=0)

    fig, ax = plt.subplots(figsize=(7, 4.5))
    ax.bar(x - w / 2, prev_m[matched.metadata_topic], w, label="Metadata prevalence", color="#4C72B0")
    ax.bar(x + w / 2, prev_f[matched.fulltext_topic], w, label="Full-text prevalence", color="#DD8452")
    ax.set_xticks(x)
    ax.set_xticklabels([f"metaT{m}\n-fullT{f}" for m, f in
                          zip(matched.metadata_topic, matched.fulltext_topic)], fontsize=8)
    ax.set_ylabel("Mean topic probability"); ax.legend()
    ax.set_title("C4: Aligned-topic prevalence comparison")
    fig.tight_layout()
    _save(fig, FIG_DIR / "comparison" / "C4_aligned_prevalence_comparison",
          "Mean topic prevalence for each matched metadata-fulltext topic pair.",
          "cross-representation", "models/{metadata,fulltext}/*.model", THIS_SCRIPT)

    rows = []
    for rep in ["metadata", "fulltext"]:
        stab = pd.read_csv(RESULTS_DIR / rep / "seed_stability_by_k.csv")
        k = 4 if rep == "metadata" else 8
        runs = pd.read_csv(RESULTS_DIR / rep / "definitive_ksweep_runs.csv")
        with open(RESULTS_DIR / rep / "training_effort_sensitivity.json", encoding="utf-8") as f:
            te = json.load(f)
        subs = pd.read_csv(RESULTS_DIR / rep / "subsampling_80pct_100reps.csv")
        rows.append({
            "Representation": rep,
            "Cross-seed stability": stab[stab.k == k]["js_similarity_mean"].iloc[0],
            "Topic diversity": runs[runs.k == k]["topic_diversity"].mean(),
            "Subsampling similarity": subs["topic_similarity_js"].mean(),
            "Training-effort stability": te["mean_js_similarity"],
        })
    df = pd.DataFrame(rows).set_index("Representation")
    fig, ax = plt.subplots(figsize=(7, 4.5))
    df.T.plot(kind="bar", ax=ax, color=["#4C72B0", "#DD8452"])
    ax.set_ylabel("Value"); ax.set_ylim(0, 1)
    ax.tick_params(axis="x", rotation=25)
    ax.set_title("C5: Representation-level robustness metrics comparison")
    fig.tight_layout()
    _save(fig, FIG_DIR / "comparison" / "C5_representation_metrics_comparison",
          "Cross-seed stability, topic diversity, subsampling similarity, and training-effort "
          "stability compared across representations.", "cross-representation",
          "results/{metadata,fulltext}/*", THIS_SCRIPT,
          "Main manuscript (candidate: Main Figure D)")

    fig, ax = plt.subplots(figsize=(8, 6))
    meta_pos = {i: (0, i) for i in range(4)}
    full_pos = {i: (2, i * 4 / 7) for i in range(8)}
    for i, (x0, y0) in meta_pos.items():
        ax.scatter(*[x0, y0], s=400, color="#4C72B0", zorder=3)
        ax.text(x0 - 0.15, y0, f"metaT{i}", ha="right", va="center", fontsize=8)
    for j, (x0, y0) in full_pos.items():
        ax.scatter(*[x0, y0], s=300, color="#DD8452", zorder=3)
        ax.text(x0 + 0.15, y0, f"fullT{j}", ha="left", va="center", fontsize=8)
    for row in matched.itertuples():
        x0, y0 = meta_pos[row.metadata_topic]
        x1, y1 = full_pos[row.fulltext_topic]
        ax.plot([x0, x1], [y0, y1], color="gray", alpha=min(1.0, row.js_similarity * 3),
                 linewidth=1 + row.js_similarity * 6)
    ax.set_xlim(-1, 3); ax.axis("off")
    ax.set_title("C6: Topic correspondence network (edge width/opacity = JS similarity;\n"
                 "unmatched full-text topics 0,1,4,7 shown unconnected)")
    fig.tight_layout()
    _save(fig, FIG_DIR / "comparison" / "C6_topic_correspondence_network",
          "Network diagram of metadata-to-fulltext topic correspondence, edge weight scaled "
          "by JS similarity (weak connections shown thin/faint, not exaggerated).",
          "cross-representation", "results/cross_representation/topic_alignment.json", THIS_SCRIPT)


if __name__ == "__main__":
    print("Robustness figures...")
    fig_subsampling_distributions()
    fig_training_effort()
    fig_dictionary_sensitivity()
    fig_hf_term_sensitivity()
    fig_phrase_sensitivity()
    fig_robustness_matrix()

    print("Human validation figures...")
    fig_human_metadata()
    fig_human_fulltext()

    print("Cross-representation figures...")
    fig_cross_representation()

    from generate_all_figures import REGISTRY
    with open(RESULTS_DIR / "figure_registry_partial2.json", "w", encoding="utf-8") as f:
        json.dump(REGISTRY, f, indent=2)
    print(f"Done: {len(REGISTRY)} total figures in registry so far.")
