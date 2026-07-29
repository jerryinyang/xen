"""Executed-code dependency provenance for SPDR-020."""

from __future__ import annotations

import ast
import hashlib
from pathlib import Path


def _sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def build_dependency_manifest(
    paths: list[Path],
    *,
    repo_root: Path,
    tracked_paths: set[str],
    dirty_paths: set[str] | None = None,
) -> dict:
    """Hash every executed dependency and record its repository status."""
    rows = []
    dirty = dirty_paths or set()
    for raw in paths:
        path = Path(raw).resolve()
        try:
            relative = path.relative_to(repo_root.resolve()).as_posix()
        except ValueError:
            relative = str(path)
        exists = path.is_file()
        tracked = relative in tracked_paths
        rows.append({
            "path": relative,
            "sha256": _sha256(path) if exists else None,
            "exists": exists,
            "tracked": tracked,
            "clean": relative not in dirty,
        })
    return {
        "dependencies": rows,
        "complete": bool(rows) and all(
            row["exists"] and row["sha256"] and row["tracked"] and row["clean"]
            for row in rows
        ),
    }


def expand_local_import_closure(
    paths: list[Path],
    *,
    repo_root: Path,
) -> list[Path]:
    """Resolve repository-local Python imports transitively from explicit roots."""
    repo_root = repo_root.resolve()
    source_root = repo_root / "python" / "src"
    pending = [Path(path).resolve() for path in paths]
    closure: set[Path] = set()

    def resolve_module(module: str, current: Path, level: int = 0) -> Path | None:
        parts = module.split(".") if module else []
        candidates = []
        if level:
            base = current.parent
            for _ in range(max(0, level - 1)):
                base = base.parent
            candidates.extend([
                base.joinpath(*parts).with_suffix(".py"),
                base.joinpath(*parts, "__init__.py"),
            ])
        else:
            candidates.extend([
                source_root.joinpath(*parts).with_suffix(".py"),
                source_root.joinpath(*parts, "__init__.py"),
                current.parent.joinpath(*parts).with_suffix(".py"),
                current.parent.joinpath(*parts, "__init__.py"),
            ])
        for candidate in candidates:
            resolved = candidate.resolve()
            if resolved.is_file() and resolved.is_relative_to(repo_root):
                return resolved
        return None

    while pending:
        path = pending.pop()
        if path in closure or not path.is_file():
            continue
        closure.add(path)
        try:
            tree = ast.parse(path.read_text(), filename=str(path))
        except (OSError, SyntaxError):
            continue
        for node in ast.walk(tree):
            imported: list[Path | None] = []
            if isinstance(node, ast.Import):
                imported.extend(
                    resolve_module(alias.name, path) for alias in node.names
                )
            elif isinstance(node, ast.ImportFrom):
                imported.append(
                    resolve_module(node.module or "", path, node.level)
                )
            pending.extend(item for item in imported if item is not None)
    return sorted(closure)
