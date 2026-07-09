#!/usr/bin/env bash
# EXP-019 (CF-VOLHARV-001) campaign driver. Phases (operator-gated — do not run without the
# pipeline execution approval):
#   cal    — 16 calendar-emission runs (no orders; emits the engine 4h bar calendar; D1)
#   gen    — generate the seeded schedules from the calendars (no engine, no credentials)
#   live   — 16 instruments x 25 seeds = 400 runs (EXP-019.conf, EXP019_SEED sweep)
#   twin   — NZDUSD +1-bar delay tripwire x 25 seeds (EXP-019-delay1.conf)
#   all    — cal, gen, live, twin in order
# Usage: ./run-exp019-all.sh [cal|gen|live|twin|all] [seed_from] [seed_to]
set -euo pipefail
SCRIPT_DIR=$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)

PHASE="${1:-all}"
SEED_FROM="${2:-1}"
SEED_TO="${3:-25}"

phase_cal()  { "$SCRIPT_DIR/run-experiment.sh" EXP-019-cal parallel; }
phase_gen()  { python3 "$SCRIPT_DIR/experiments/gen_exp019_schedules.py"; }
# The cTrader console sporadically dies with "Message expected" at report-saving before the
# cBot even starts (transient; seen twice in ~180 runs). A failed cell must NOT abort the
# sweep — tolerate it, keep going, and let the repair phase re-run whatever is missing.
phase_live() {
  for seed in $(seq "$SEED_FROM" "$SEED_TO"); do
    echo "=== EXP-019 live seed $seed ==="
    EXP019_SEED="$seed" "$SCRIPT_DIR/run-experiment.sh" EXP-019 parallel \
      || echo "!!! seed $seed had failed cell(s) — repair phase will re-run them"
  done
}
phase_twin() {
  for seed in $(seq "$SEED_FROM" "$SEED_TO"); do
    echo "=== EXP-019 delay-twin seed $seed ==="
    EXP019_SEED="$seed" "$SCRIPT_DIR/run-experiment.sh" EXP-019-delay1 all \
      || echo "!!! twin seed $seed failed — repair phase will re-run it"
  done
}
# Inventory (symbol, seed) pairs from run_metadata.json; delete incomplete run dirs; re-run
# every missing pair as a targeted `one` cell. Rerunnable until clean.
phase_repair() {
  local root conf missing
  for arm in live twin; do
    if [[ "$arm" == "live" ]]; then root="EXP-019"; conf="EXP-019"; else root="EXP-019-delay1"; conf="EXP-019-delay1"; fi
    missing=$(python3 - "$SCRIPT_DIR/../../data/strategy_runs/$root" "$arm" <<'PYEOF'
import json, sys, glob, os, shutil
root, arm = sys.argv[1], sys.argv[2]
symbols = ["EURUSD","GBPUSD","USDJPY","USDCHF","USDCAD","AUDUSD","NZDUSD","EURJPY","GBPJPY",
           "AUDJPY","XAUUSD","BTCUSD","USTEC","US500","US2000","JP225"] if arm == "live" else ["NZDUSD"]
need = {(s, i) for s in symbols for i in range(1, 26)}
have = set()
for d in glob.glob(os.path.join(root, "random_hold_*")):
    complete = all(os.path.getsize(os.path.join(d, f)) > 0 for f in
                   ("run_metadata.json", "positions.parquet", "trade_blotter.parquet")
                   if os.path.exists(os.path.join(d, f))) and \
               all(os.path.exists(os.path.join(d, f)) for f in
                   ("run_metadata.json", "positions.parquet", "trade_blotter.parquet"))
    if not complete:
        print(f"# deleting incomplete {d}", file=sys.stderr)
        shutil.rmtree(d)
        continue
    m = json.load(open(os.path.join(d, "run_metadata.json")))
    p = m.get("parameters", {})
    sym = str(m.get("instrument", m.get("symbol", ""))).upper()
    if not sym:
        sym = os.path.basename(d).split("_")[2].upper()
    have.add((sym, int(p.get("schedule_seed", -1))))
for s, i in sorted(need - have):
    print(f"{s} {i}")
PYEOF
)
    while read -r sym seed; do
      [[ -z "${sym:-}" ]] && continue
      echo "=== EXP-019 repair ($arm): $sym seed $seed ==="
      EXP019_SEED="$seed" "$SCRIPT_DIR/run-experiment.sh" "$conf" one "$sym" 4h \
        || echo "!!! repair $arm $sym seed $seed failed again — re-run phase repair"
    done <<< "$missing"
  done
}

case "$PHASE" in
  cal) phase_cal;;
  gen) phase_gen;;
  live) phase_live;;
  twin) phase_twin;;
  repair) phase_repair;;
  all) phase_cal; phase_gen; phase_live; phase_twin; phase_repair;;
  *) echo "Unknown phase: $PHASE" >&2; exit 2;;
esac
echo "EXP-019 phase '$PHASE' done."
