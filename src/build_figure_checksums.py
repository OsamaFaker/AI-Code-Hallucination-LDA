"""Freeze task Section 21: SHA-256 checksums for every figure file (PNG+PDF), keyed by
POSIX-style relative path (forward slashes) so the registry is portable and matches
`git ls-files` / GitHub raw URLs exactly - a prior version of this script used
`str(Path)` directly on Windows, producing backslash-separated paths that silently failed to
match against git/GitHub paths during remote verification (values were correct; only the key
format was wrong).
"""
import hashlib
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parents[1]


def main():
    registry = pd.read_csv(ROOT / "results" / "figure_registry_full.csv")
    rows = []
    for r in registry.itertuples():
        for ext in [".png", ".pdf"]:
            p = Path(r.Filename).with_suffix(ext)
            full = ROOT / p
            if full.exists():
                h = hashlib.sha256(full.read_bytes()).hexdigest()
                rows.append({
                    "Figure": p.as_posix(), "SHA-256": h,
                    "Source_script": r.Script, "Source_data": r._5,
                })
    df = pd.DataFrame(rows)
    df.to_csv(ROOT / "figures" / "FIGURE_SHA256.csv", index=False)
    print(f"{len(df)} files hashed (POSIX paths)")


if __name__ == "__main__":
    main()
