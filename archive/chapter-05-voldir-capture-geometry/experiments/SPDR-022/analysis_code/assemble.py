"""Splice generated markdown tables into prose.md -> ../analysis.md."""

from __future__ import annotations

import pathlib
import re

HERE = pathlib.Path(__file__).resolve().parent
text = (HERE / "prose.md").read_text()


def sub(m: re.Match[str]) -> str:
    p = HERE / "tables" / m.group(1)
    if not p.exists():
        raise FileNotFoundError(p)
    return p.read_text().rstrip()


out = re.sub(r"\{\{TABLE:([^}]+)\}\}", sub, text)
missing = re.findall(r"\{\{TABLE:[^}]+\}\}", out)
assert not missing, missing
(HERE.parent / "analysis.md").write_text(out + "\n")
print("wrote", HERE.parent / "analysis.md", len(out.splitlines()), "lines")
