#!/usr/bin/env python3
"""Verify the post-rollover state of a Xen research chapter boundary.

Checks the acceptance criteria for all three rollover phases (Extract, Archive, Renew)
that can be verified deterministically from the filesystem and git. Phase-specific
semantic checks (e.g. that each lesson has a mechanism) are left to human/agent review.

Usage:
    python3 verify_rollover.py --root <repo-root> --chapter <NN>

Exit code 0 if all checks pass, 1 otherwise.
"""

from __future__ import annotations

import argparse
import subprocess
import sys
from pathlib import Path

KB_FILES = [
    "INDEX.md",
    "data-architecture.md",
    "evaluation-framework.md",
    "families-explored.md",
    "methodology-canon.md",
    "lessons-and-amendments.md",
    "pitfalls-ledger.md",
]


def _ok(label: str, passed: bool, detail: str = "") -> bool:
    mark = "PASS" if passed else "FAIL"
    line = f"[{mark}] {label}"
    if detail:
        line += f" — {detail}"
    print(line)
    return passed


def _git(root: Path, *args: str) -> str:
    try:
        out = subprocess.run(
            ["git", "-C", str(root), *args],
            capture_output=True, text=True, check=False,
        )
        return out.stdout.strip()
    except Exception:  # noqa: BLE001 - git absence is just a skipped check
        return ""


def verify(root: Path, chapter: str) -> bool:
    results: list[bool] = []

    # --- Extract -------------------------------------------------------------
    kb = root / "docs" / "knowledge-base"
    results.append(_ok("Extract: knowledge-base/ exists", kb.is_dir(), str(kb)))
    for name in KB_FILES:
        f = kb / name
        results.append(_ok(f"Extract: KB file {name}", f.is_file()))
    mem_index = kb / "memory" / "MEMORY.md"
    results.append(_ok("Extract: project memory MEMORY.md", mem_index.is_file()))

    registry = root / "docs" / "signal-registry"
    results.append(_ok("Extract/Archive: signal-registry still live", registry.is_dir()))

    # --- Archive -------------------------------------------------------------
    archive_glob = sorted((root / "archive").glob(f"chapter-{chapter}-*"))
    arch = archive_glob[0] if archive_glob else None
    non_empty = bool(arch and any(arch.rglob("*")))
    results.append(_ok(
        f"Archive: archive/chapter-{chapter}-* exists and is non-empty",
        non_empty, str(arch) if arch else "missing",
    ))

    experiments = root / "python" / "experiments"
    exp_dirs = sorted(experiments.glob("EXP-*")) if experiments.is_dir() else []
    results.append(_ok(
        "Archive: python/experiments/ has no EXP-* dirs",
        len(exp_dirs) == 0,
        f"{len(exp_dirs)} EXP-* dirs remain" if exp_dirs else "clean",
    ))
    results.append(_ok(
        "Archive: python/experiments/INDEX.md present",
        (experiments / "INDEX.md").is_file(),
    ))

    exp_docs = root / "docs" / "experiments-docs"
    results.append(_ok(
        "Archive: experiments-docs/INDEX.md present",
        (exp_docs / "INDEX.md").is_file(),
    ))
    checkpoints = exp_docs / "checkpoints"
    # A dir tracked by git via a placeholder (.gitkeep) still counts as "fresh".
    cp_contents = (
        [p for p in checkpoints.iterdir() if not p.name.startswith(".")]
        if checkpoints.is_dir() else []
    )
    results.append(_ok("Archive: checkpoints/ empty (fresh chapter)", not cp_contents))

    # --- git -----------------------------------------------------------------
    tags = _git(root, "tag", "--list", f"chapter-{chapter}-close")
    if tags or (root / ".git").exists():
        results.append(_ok(
            f"Archive: git tag chapter-{chapter}-close exists",
            bool(tags), tags or "not found",
        ))

    print()
    passed = all(results)
    print(f"{'ALL CHECKS PASSED' if passed else 'SOME CHECKS FAILED'} "
          f"({sum(results)}/{len(results)})")
    return passed


def main() -> int:
    ap = argparse.ArgumentParser(description="Verify post-rollover chapter state.")
    ap.add_argument("--root", required=True, type=Path, help="Repo root")
    ap.add_argument("--chapter", required=True, help="Chapter number, e.g. 01")
    args = ap.parse_args()
    return 0 if verify(args.root.resolve(), args.chapter) else 1


if __name__ == "__main__":
    sys.exit(main())
