#!/bin/bash
# Restarts 5-11, TOTAL live python workers capped at 5.
# Pattern "Python run_search" matches only real interpreter processes
# (shell wrappers say "python3", the exec'd binary path says "Python").
set -u
count() { pgrep -f "Python run_search.py full-one" | wc -l | tr -d ' '; }
for rid in 5 6 7 8 9 10 11; do
  while (( $(count) >= 5 )); do sleep 30; done
  nice -n 15 python3 run_search.py full-one $rid 16000 &
  sleep 10
done
while (( $(count) > 0 )); do sleep 60; done
echo "ALL RESTARTS DONE: $(ls ../results/search_restart_*.json 2>/dev/null | wc -l)/12"
