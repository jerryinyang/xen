#!/usr/bin/env bash
# sync_skills.sh — single-source skill mirrors (INFR-016 follow-up, 2026-07-19)
#
# `.claude/skills` is the CANONICAL source. The other agent tools each expect their skills
# under `<tool>/skills`, so we mirror `.claude/skills` into them. The mirrors are byte-for-byte
# copies and are git-ignored (see .gitignore) — edit `.claude/skills` ONLY, then run this once.
#
# Rationale: the mirrors were hand-duplicated and hand-synced (a 9x diff on every skill edit);
# a generate-from-one-source script removes that drift/pollution without assuming any tool
# follows symlinks (some do not). Usage:  scripts/sync_skills.sh  (from repo root or anywhere).
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
SRC="$ROOT/.claude/skills"
MIRRORS=(.agents .cline .codex .cursor .grok .kilocode .opencode .windsurf)

[ -d "$SRC" ] || { echo "canonical source $SRC missing" >&2; exit 1; }

for m in "${MIRRORS[@]}"; do
  dst="$ROOT/$m/skills"
  mkdir -p "$dst"
  if command -v rsync >/dev/null 2>&1; then
    rsync -a --delete "$SRC/" "$dst/"
  else
    rm -rf "$dst" && mkdir -p "$dst" && cp -R "$SRC/." "$dst/"
  fi
  echo "synced .claude/skills -> $m/skills"
done
echo "done ($(find "$SRC" -name SKILL.md | wc -l | tr -d ' ') skills)"
