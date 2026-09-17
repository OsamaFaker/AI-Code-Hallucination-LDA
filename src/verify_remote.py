"""Freeze/deploy task Sections 16-17: download every tracked file directly from GitHub raw
content (independent of git's own object-equality guarantee, which was already separately
confirmed via `git diff main origin/main`) and compare SHA-256 hashes.
"""
import hashlib
import subprocess
import sys
import time
import urllib.error
import urllib.parse
import urllib.request
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
RAW_BASE = "https://raw.githubusercontent.com/OsamaFaker/AI-Code-Hallucination-LDA/main/"


def git_tracked_files():
    out = subprocess.run(["git", "ls-files"], cwd=ROOT, capture_output=True, text=True, check=True)
    return [line for line in out.stdout.splitlines() if line.strip()]


def local_blob_sha256(rel_path: str) -> str:
    """Hash the committed git BLOB content (what GitHub actually serves), not the raw
    working-tree file. Windows git here has core.autocrlf=true, so working-tree text files are
    checked out with CRLF while the stored blob (and GitHub's raw server) use LF - comparing
    raw working-tree bytes against the remote would incorrectly report every text file as a
    mismatch. Confirmed by spot check: `git show HEAD:<path>` output is byte-identical to the
    GitHub raw download for text files; only line-ending representation differs from the
    working-tree copy."""
    out = subprocess.run(["git", "show", f"HEAD:{rel_path}"], cwd=ROOT, capture_output=True, check=True)
    return hashlib.sha256(out.stdout).hexdigest()


def fetch_remote_bytes(rel_path: str, retries: int = 3) -> bytes | None:
    url = RAW_BASE + urllib.parse.quote(rel_path)
    for attempt in range(retries):
        try:
            req = urllib.request.Request(url, headers={"User-Agent": "verify-remote-script"})
            with urllib.request.urlopen(req, timeout=20) as resp:
                return resp.read()
        except urllib.error.HTTPError as e:
            if e.code == 404:
                return None
            time.sleep(1.5 * (attempt + 1))
        except Exception:
            time.sleep(1.5 * (attempt + 1))
    return None


def main():
    files = git_tracked_files()
    rows = []
    t0 = time.time()
    for i, rel in enumerate(files):
        lh = local_blob_sha256(rel)
        remote_bytes = fetch_remote_bytes(rel)
        remote_exists = remote_bytes is not None
        rh = hashlib.sha256(remote_bytes).hexdigest() if remote_bytes is not None else None
        status = "PASS" if (remote_exists and lh is not None and lh == rh) else "FAIL"
        rows.append({
            "Local file": rel, "Remote exists": remote_exists,
            "Local hash": lh, "Remote hash": rh, "Status": status,
        })
        if (i + 1) % 50 == 0:
            print(f"{i+1}/{len(files)} checked ({time.time()-t0:.0f}s)")

    df = pd.DataFrame(rows)
    df.to_csv(ROOT / "results" / "remote_file_verification.csv", index=False)
    n_fail = (df.Status == "FAIL").sum()
    n_missing = (~df["Remote exists"]).sum()
    print(f"DONE: {len(df)} files checked in {time.time()-t0:.0f}s. "
          f"Missing={n_missing} Mismatches={n_fail - n_missing if n_fail >= n_missing else n_fail}")
    print(df[df.Status == "FAIL"][["Local file", "Remote exists"]].to_string())
    return df


if __name__ == "__main__":
    main()
