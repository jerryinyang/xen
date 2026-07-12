#!/bin/bash
# 12 production restarts, budget 16000 (operator direction 2026-07-11).
# 3-way parallel, niced: the earlier 6-way run exhausted the machine (16GB) and
# froze it — keep headroom for the OS.
set -u
MAX=3
for rid in 0 1 2 3 4 5 6 7 8 9 10 11; do
  while (( $(jobs -rp | wc -l) >= MAX )); do wait -n || true; done
  nice -n 15 python3 run_search.py full-one $rid 16000 &
done
wait
echo "ALL RESTARTS DONE"
ls ../results/search_restart_*.json
