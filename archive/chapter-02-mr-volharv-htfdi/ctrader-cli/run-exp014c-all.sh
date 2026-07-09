#!/usr/bin/env bash
# EXP-014c driver: run the 19 amendment-004 confs sequentially (11 symbols each = 209 runs).
set -uo pipefail
cd "$(dirname "${BASH_SOURCE[0]}")"
CONFS=(
  EXP-014c-4h-s8-e1-none-z20 EXP-014c-4h-s8-e1-none-z15
  EXP-014c-4h-s8-e1-allow-z20 EXP-014c-4h-s8-e1-allow-z15
  EXP-014c-4h-s8-e1-extend-z20 EXP-014c-4h-s8-e1-extend-z15
  EXP-014c-4h-s8-e2-none-z20 EXP-014c-4h-s8-e2-none-z15
  EXP-014c-4h-s8-e2-allow-z20 EXP-014c-4h-s8-e2-allow-z15
  EXP-014c-4h-s8-e2-extend-z20 EXP-014c-4h-s8-e2-extend-z15
  EXP-014c-4h-s8-e3-none-z20 EXP-014c-4h-s8-e3-none-z15
  EXP-014c-4h-s8-e3-allow-z20 EXP-014c-4h-s8-e3-allow-z15
  EXP-014c-4h-s8-e3-extend-z20 EXP-014c-4h-s8-e3-extend-z15
  EXP-014c-4h-s8-e3-none-z20-shift
)
total=${#CONFS[@]}
i=0
for c in "${CONFS[@]}"; do
  i=$((i+1))
  echo "=== [$i/$total] $c start $(date -u +%FT%TZ) ==="
  if ./run-experiment.sh "$c" parallel; then
    echo "=== [$i/$total] $c DONE $(date -u +%FT%TZ) ==="
  else
    echo "=== [$i/$total] $c FAILED $(date -u +%FT%TZ) — continuing ==="
  fi
done
echo "=== ALL CONFS PROCESSED $(date -u +%FT%TZ) ==="
