"""Check that the saved answers reproduce every published number. Model-free, under a minute.

    uv run python scripts/verify.py

1. Every file in data/ matches data/SHA256SUMS.
2. The helper modules in src/lfm3lab/ are byte-identical to the ones the GPU runs used
   (their hashes are recorded in each run_config.json).
3. Re-running both reports on copies of the saved answers rewrites analysis.json and findings.md
   byte for byte.
4. The palette grid, the answer mosaic and the README table match the data.
"""

from __future__ import annotations

import hashlib
import json
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "data"
OUTPUTS = ("analysis.json", "findings.md")
UNLISTED = {"README.md", "LICENSE", "SHA256SUMS"}


def sha(p: Path) -> str:
    return hashlib.sha256(p.read_bytes()).hexdigest()


def check_manifest() -> bool:
    listed = {}
    for line in (DATA / "SHA256SUMS").read_text().splitlines():
        h, name = line.split(maxsplit=1)
        listed[name] = h
    present = {str(p.relative_to(DATA)) for p in DATA.rglob("*") if p.is_file() and p.name not in UNLISTED and not p.name.startswith(".")}
    bad = [n for n, h in listed.items() if not (DATA / n).is_file() or sha(DATA / n) != h]
    extra = sorted(present - set(listed))
    for n in bad:
        print(f"  hash mismatch or missing: data/{n}")
    for n in extra:
        print(f"  not in SHA256SUMS: data/{n}")
    return not bad and not extra


def check_helpers() -> bool:
    ok = True
    for run in ("battery_v1", "battery_v2"):
        recorded = json.loads((DATA / run / "run_config.json").read_text())["source_hashes"]
        for name, h in recorded.items():
            if name.startswith("src/") and sha(ROOT / name) != h:
                print(f"  {name} differs from the version {run} ran with")
                ok = False
    return ok


def check_reports() -> bool:
    ok = True
    with tempfile.TemporaryDirectory() as tmp:
        for run in ("battery_v1", "battery_v2"):
            out = Path(tmp) / run
            shutil.copytree(DATA / run, out)
            for name in OUTPUTS:
                (out / name).unlink()
            proc = subprocess.run([sys.executable, str(ROOT / "scripts" / f"{run}.py"), "--stage", "report",
                                   "--output", str(out)], capture_output=True, text=True)
            if proc.returncode:
                print(proc.stderr)
                return False
            for name in OUTPUTS:
                if (out / name).read_bytes() != (DATA / run / name).read_bytes():
                    print(f"  data/{run}/{name} is not reproduced")
                    ok = False
    return ok


def check_figure() -> bool:
    proc = subprocess.run([sys.executable, str(ROOT / "scripts/figure.py"), "--check"], capture_output=True, text=True)
    if proc.returncode:
        print("  " + (proc.stdout + proc.stderr).strip())
    return proc.returncode == 0


def main():
    checks = [("data files match SHA256SUMS", check_manifest),
              ("helper modules match the versions used for the runs", check_helpers),
              ("reports reproduce analysis.json and findings.md byte for byte", check_reports),
              ("figures and README table match the data", check_figure)]
    failed = 0
    for label, fn in checks:
        ok = fn()
        failed += not ok
        print(f"{'pass' if ok else 'FAIL'}  {label}")
    raise SystemExit(1 if failed else 0)


if __name__ == "__main__":
    main()
