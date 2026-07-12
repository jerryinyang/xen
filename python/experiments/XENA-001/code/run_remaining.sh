#!/bin/bash
# Restarts 3-11 at budget 16000, capped so TOTAL live workers (incl. the 3
# orphaned rid-0/1/2 processes) stays at 5 — the 16GB machine's safe memory
# frontier with macOS+Docker overhead. All niced.
set -u
TOTAL_CAP=5
for rid in 3 4 5 6 7 8 9 10 11; do
  while (( $(pgrep -f "run_search.py full-one" | wc -l) >= TOTAL_CAP )); do sleep 30; done
  nice -n 15 python3 run_search.py full-one $rid 16000 &
  sleep 5
done
# wait for ALL workers (incl. orphans) to finish
while pgrep -f "run_search.py full-one" >/dev/null; do sleep 60; done
echo "ALL RESTARTS DONE"
ls ../results/search_restart_*.json 2>/dev/null | wc -l
