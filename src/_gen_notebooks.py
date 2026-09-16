"""One-off generator for notebooks/*.ipynb - thin wrappers calling the already-tested src/
scripts (not a duplicate reimplementation), matching the freeze task's requested notebook set.
"""
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def nb(cells):
    return {
        "cells": cells,
        "metadata": {"kernelspec": {"display_name": "Python 3 (.venv)", "language": "python", "name": "python3"}},
        "nbformat": 4, "nbformat_minor": 5,
    }


def md(text):
    return {"cell_type": "markdown", "metadata": {}, "source": text.splitlines(keepends=True)}


def code(text):
    return {"cell_type": "code", "execution_count": None, "metadata": {}, "outputs": [],
            "source": text.splitlines(keepends=True)}


SETUP = (
    "import subprocess, sys\n"
    "from pathlib import Path\n"
    "ROOT = Path.cwd().parent if Path.cwd().name == 'notebooks' else Path.cwd()\n"
    "PY = str(ROOT / '..' / '.venv' / 'Scripts' / 'python.exe')\n"
    "def run(*args):\n"
    "    print('$', *args)\n"
    "    subprocess.run([PY, *args], cwd=ROOT, check=True)\n"
)

NOTEBOOKS = {}

NOTEBOOKS["01_corpus_audit.ipynb"] = nb([
    md("# 01 - Corpus Audit\n\nBuilds and validates the 66-primary-study manifest from the "
       "master reference spreadsheet and the PDF folders. Thin wrapper around the tested "
       "`src/` scripts - see `README.md` for the full documented pipeline."),
    code(SETUP),
    code("run('src/corpus_audit.py')"),
    md("Output: `corpus/primary_studies_manifest.csv`, `corpus/corpus_audit.md`."),
])

NOTEBOOKS["02_metadata_analysis.ipynb"] = nb([
    md("# 02 - Metadata LDA Analysis (Analysis A, primary RQ5 representation)\n\n"
       "Extraction -> preprocessing -> dictionary/training pilots -> definitive k-sweep -> "
       "selection, for the metadata (title+abstract+keywords) representation."),
    code(SETUP),
    code("run('src/extraction.py')"),
    code("run('src/preprocess_corpus.py')"),
    code("run('src/lemma_quality_audit.py')"),
    code("run('src/hf_terms.py')"),
    code("run('src/stage1_dictionary_sweep.py', 'metadata')"),
    code("run('src/select_stage1_config.py', 'metadata')"),
    code("run('src/stage2_convergence_pilot.py', 'metadata', '5', '0.50')"),
    code("run('src/domain_term_sensitivity.py', 'metadata', '5', '0.50', '30', '800')"),
    code("run('src/phrase_sensitivity.py', 'metadata', '5', '0.50', '30', '800')"),
    code("# Expensive step (~9 min on a 20-core machine): the definitive k=2-20 x 20-seed sweep\n"
         "run('src/definitive_k_sweep.py', 'metadata', '5', '0.50', '30', '800',\n"
         "    '--alpha', 'auto', '--eta', 'auto', '--kmax', '20')"),
    code("run('src/cross_seed_stability.py', 'metadata')"),
    code("run('src/model_selection.py', 'metadata')"),
    code("run('src/representative_seed.py', 'metadata', '4')"),
    code("run('src/candidate_k_comparison.py', 'metadata', '2,3,4,5', '5', '0.50',\n"
         "    'k2_k5_candidate_comparison.csv')"),
    md("Output: `results/metadata/`, `reports/METADATA_LDA_REPORT.md`, "
       "`reports/METADATA_FINAL_K_VALIDATION.md`. Final model: k=4, medoid seed 14."),
])

NOTEBOOKS["03_fulltext_analysis.ipynb"] = nb([
    md("# 03 - Full-Text LDA Analysis (Analysis B, secondary representation-sensitivity "
       "analysis)\n\nSame pipeline as Notebook 02, run independently on the cleaned full-text "
       "representation."),
    code(SETUP),
    code("run('src/stage1_dictionary_sweep.py', 'fulltext')"),
    code("run('src/select_stage1_config.py', 'fulltext')"),
    code("run('src/stage2_convergence_pilot.py', 'fulltext', '4', '0.75')"),
    code("run('src/domain_term_sensitivity.py', 'fulltext', '4', '0.75', '30', '800')"),
    code("run('src/phrase_sensitivity.py', 'fulltext', '4', '0.75', '30', '800')"),
    code("# Expensive step (~21 min on a 20-core machine)\n"
         "run('src/definitive_k_sweep.py', 'fulltext', '4', '0.75', '30', '800',\n"
         "    '--alpha', 'auto', '--eta', 'auto', '--kmax', '20')"),
    code("run('src/cross_seed_stability.py', 'fulltext')"),
    code("run('src/model_selection.py', 'fulltext')"),
    code("run('src/representative_seed.py', 'fulltext', '8')"),
    code("for k in ['9', '12', '13', '14', '15']:\n    run('src/representative_seed.py', 'fulltext', k)"),
    code("run('src/candidate_k_comparison.py', 'fulltext', '8,9,12,13,14,15', '4', '0.75',\n"
         "    'fulltext_k_candidate_comparison.csv')"),
    code("run('src/cross_k_persistence.py')"),
    code("run('src/fulltext_length_diagnostics.py', '4', '0.75', '8', '30', '800', '2')"),
    md("Output: `results/fulltext/`, `reports/FULLTEXT_LDA_REPORT.md`, "
       "`reports/FULLTEXT_FINAL_K_VALIDATION.md`. Final model: k=8, medoid seed 2."),
])

NOTEBOOKS["04_robustness.ipynb"] = nb([
    md("# 04 - Robustness Analyses\n\nTraining-effort, dictionary-neighbor, and 80%x100 "
       "subsampling robustness, for both final models."),
    code(SETUP),
    code("run('src/robustness.py', 'subsample', 'metadata', '5', '0.50', '30', '800', '4', '14',\n"
         "    '--model_path', 'models/metadata/k04_seed14.model')"),
    code("run('src/robustness.py', 'subsample', 'fulltext', '4', '0.75', '30', '800', '8', '2',\n"
         "    '--model_path', 'models/fulltext/k08_seed02.model')"),
    code("import sys; sys.path.insert(0, 'src')\n"
         "from robustness import training_effort_sensitivity, dictionary_sensitivity\n"
         "training_effort_sensitivity('metadata', 5, 0.50, 4, 30, 800, 14)\n"
         "dictionary_sensitivity('metadata', 5, 0.50, 4, 30, 800, 14)\n"
         "training_effort_sensitivity('fulltext', 4, 0.75, 8, 30, 800, 2)\n"
         "dictionary_sensitivity('fulltext', 4, 0.75, 8, 30, 800, 2)"),
    md("Output: `results/{metadata,fulltext}/subsampling_80pct_*`, "
       "`training_effort_sensitivity.json`, `dictionary_sensitivity.csv`. Consolidated: "
       "`reports/ROBUSTNESS_REPORT.md`."),
])

NOTEBOOKS["05_human_validation.ipynb"] = nb([
    md("# 05 - Human Validation\n\nGenerates blinded rating materials, then (after raters "
       "complete them outside this notebook) consolidates the real rater responses into "
       "verified summary tables. The consolidation step was run against the actual completed "
       "rater files in `human_validation/Human_Result/` - see "
       "`reports/HUMAN_VALIDATION_REPORT.md`."),
    code(SETUP),
    code("run('src/human_validation_packets.py', 'metadata', '4', '14', '5', '0.50')"),
    code("run('src/human_validation_packets.py', 'fulltext', '8', '2', '4', '0.75')"),
    code("run('src/blinded_candidate_packets.py', 'metadata', '2,3,4,5', '5', '0.50')"),
    code("import sys; sys.path.insert(0, 'src')\n"
         "from blinded_candidate_packets import build_blinded_packets\n"
         "build_blinded_packets('fulltext', [8], 4, 0.75, key_seed=99)  "
         "# single-model blind, final topics"),
    code("run('src/intrusion_tests.py', 'metadata', '5', '0.50')"),
    code("# Raters complete the sheets in human_validation/*_blinded/ OUTSIDE this notebook.\n"
         "# Once done, consolidate their real responses:\n"
         "run('src/human_validation_analysis.py')"),
    md("Output: `human_validation/metadata_human_*.csv`, `human_validation/fulltext_human_*.csv`, "
       "`human_validation/FINAL_TOPIC_LABELS.csv`, `reports/HUMAN_VALIDATION_REPORT.md`."),
])

NOTEBOOKS["06_cross_representation.ipynb"] = nb([
    md("# 06 - Cross-Representation Comparison\n\nRun only after both representations "
       "independently froze their final models (k=4 metadata, k=8 full text)."),
    code(SETUP),
    code("run('src/cross_representation.py', '4', '14', '8', '2', '5', '0.50', '4', '0.75')"),
    md("Output: `results/cross_representation/`, `reports/CROSS_REPRESENTATION_REPORT.md`."),
])


if __name__ == "__main__":
    out_dir = ROOT / "notebooks"
    out_dir.mkdir(exist_ok=True)
    for name, content in NOTEBOOKS.items():
        (out_dir / name).write_text(json.dumps(content, indent=1), encoding="utf-8")
    print(f"wrote {len(NOTEBOOKS)} notebooks to {out_dir}")
