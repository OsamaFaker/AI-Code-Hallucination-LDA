# Environment Snapshot

Exact environment used to produce every frozen result in this repository (captured at freeze
time via `uv pip list --python .venv`). A local `uv`-managed virtual environment (Python 3.11)
was used because, at the time of this analysis, `gensim` had no prebuilt wheel for very new
CPython minor versions, and the base system Python was a newer release.

| Package | Version |
|---|---|
| Python | 3.11.15 |
| gensim | 4.4.0 |
| spacy | 3.8.16 |
| en-core-web-sm | 3.8.0 |
| numpy | 2.4.6 |
| pandas | 3.0.5 |
| scipy | 1.17.1 |
| scikit-learn | 1.9.1 |
| matplotlib | 3.11.2 |
| seaborn | 0.13.2 |
| pymupdf | 1.28.2 |
| nltk | 3.10.3 |
| pyLDAvis | 3.4.1 |
| openpyxl | 3.1.5 |
| tabulate | 0.10.0 |

These exact versions are pinned in `requirements.txt` and `environment.yml`. Platform: Windows
11 (win32), 20 logical CPUs (used for parallelized model fitting via
`concurrent.futures.ProcessPoolExecutor`, `max_workers=12`).

## Reproduction

```bash
uv venv --python 3.11 .venv
uv pip install --python .venv -r requirements.txt
.venv/Scripts/python -m spacy download en_core_web_sm
```

or, with conda:

```bash
conda env create -f environment.yml
conda activate lda66-dual-representation
```
