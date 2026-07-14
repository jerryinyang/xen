#!/usr/bin/env bash
# Generic cTrader-CLI experiment runner for Xen Chapter-02 price-primary experiments.
#
# This is the reusable harness entry point. Per-experiment specifics (strategy, cells,
# holdout-fence timestamps, model parameters) live in a sourced config:
#     tools/ctrader-cli/experiments/<EXP-ID>.conf
# so this script never changes between experiments. It generalizes the Chapter-01
# run-exp029-backtests.sh (archived) — same cache/docker/poll/fence machinery, parameterized.
#
# Causal guarantee: strategies run bar-by-bar in cTrader's engine (StrategyHost mode). A model's
# OnBar() sees only the current and past bars; HoldoutFence refuses to emit any row at/after
# AnalysisEndUtc. Look-ahead is impossible by construction — this is the structural fix for the
# Chapter-01 rct[di] leak (see docs/knowledge-base/lessons-and-amendments.md L-01).
#
# Usage:
#   ./run-experiment.sh <EXP-ID> [all|parallel|one <SYMBOL> <DOMAIN>|cache-layout|metadata]
# Build the robot first:  dotnet build Xen.csproj -c Debug
set -euo pipefail

SCRIPT_DIR=$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)
ROOT_DIR=$(cd "$SCRIPT_DIR/../.." && pwd)

EXP_ID="${1:-}"
if [[ -z "$EXP_ID" ]]; then
  echo "Usage: $0 <EXP-ID> [all|parallel|one <SYMBOL> <DOMAIN>|cache-layout|metadata]" >&2
  exit 2
fi
shift || true

CONF="$SCRIPT_DIR/experiments/${EXP_ID}.conf"
if [[ ! -f "$CONF" ]]; then
  echo "Missing per-experiment config: $CONF" >&2
  echo "Create it from experiments/EXAMPLE.conf (defines STRATEGY, STRATEGY_VALUE, SYMBOLS," >&2
  echo "DOMAINS, ANALYSIS_END[symbol], BACKTEST_END[symbol], and optional MODEL_ARGS)." >&2
  exit 2
fi

# --- per-experiment config (declares the assoc arrays below) -----------------------------
declare -A ANALYSIS_END BACKTEST_END
# MODEL_ARGS_BY_SYMBOL[symbol] = extra per-symbol cBot args (space-separated), e.g. a multi-symbol
# experiment's per-cell basket declaration (EXP-010 CONC-1: --BasketMates=A;B;C). Word-split on
# expansion; values must not contain spaces within a single arg.
declare -A MODEL_ARGS_BY_SYMBOL
SYMBOLS=(); DOMAINS=(); MODEL_ARGS=()
STRATEGY=""; STRATEGY_VALUE=""
# shellcheck disable=SC1090
source "$CONF"

# Xen robot Mode ordinal: 0=StrategyHost (default, self-adjudicated replay), 3=NativeOrders
# (EXP-013/CF-MR-004 native cTrader pending orders, m1 fills). Confs may override via MODE=.
MODE="${MODE:-0}"

# Backtest starting balance. Large values prevent ruin-truncation (equity→0 abort) on high-notional
# instruments with fixed volume; the referee judges bps (balance-independent). Confs may override.
BALANCE="${BALANCE:-10000}"

# --- credentials / image (shared .env) ---------------------------------------------------
ENV_FILE="${CTRADER_ENV_FILE:-$SCRIPT_DIR/.env}"
[[ -f "$ENV_FILE" ]] && { # shellcheck disable=SC1090
  source "$ENV_FILE"; }
IMAGE="${CTRADER_IMAGE:-ghcr.io/spotware/ctrader-console:latest}"
PLATFORM="${CTRADER_PLATFORM:-linux/amd64}"
CTID="${CTRADER_CTID:-}"; ACCOUNT="${CTRADER_ACCOUNT:-}"
CACHE_ACCOUNT="${CTRADER_CACHE_ACCOUNT:-${CTRADER_ACCOUNT:-}}"
PWD_FILE_HOST="${CTRADER_PWD_FILE:-$SCRIPT_DIR/ctrader-cli.pwd}"
BROKER="${CTRADER_BROKER:-}"
OUT_DIR="$ROOT_DIR/data/strategy_runs/$EXP_ID"

if [[ "${1:-}" == "metadata" ]]; then
  exec docker run --rm --platform "$PLATFORM" \
    --mount "type=bind,src=$ROOT_DIR,dst=/workspace" \
    "$IMAGE" metadata /workspace/bin/Debug/net6.0/Xen.algo
fi

for v in CTID ACCOUNT CACHE_ACCOUNT; do
  [[ -z "${!v}" ]] && { echo "Set CTRADER_${v#CTID} in $ENV_FILE" >&2; exit 2; }
done
[[ -f "$PWD_FILE_HOST" ]] || { echo "Password file not found: $PWD_FILE_HOST" >&2; exit 2; }
[[ -f "$ROOT_DIR/bin/Debug/net6.0/Xen.algo" ]] || {
  echo "Missing Xen.algo build; run: dotnet build Xen.csproj -c Debug" >&2; exit 2; }

mkdir -p "$OUT_DIR" "$SCRIPT_DIR/reports/$EXP_ID"
broker_args=(); [[ -n "$BROKER" ]] && broker_args=(--broker="$BROKER")

domain_minutes() { case "$1" in 5m) echo 5;; 15m) echo 15;; 30m) echo 30;; 1h) echo 60;; 2h) echo 120;; 4h) echo 240;; *) echo "unknown domain: $1" >&2; return 1;; esac; }
strict_coverage() { [[ "$1" == "5m" ]] && echo true || echo false; }
min_coverage()    { [[ "$1" == "5m" ]] && echo 0.0  || echo 0.9; }

# --- canonical cache layout (provider-dir symlink shim; unchanged from Chapter-01) --------
cache_providers() { { [[ -n "${CTRADER_CACHE_PROVIDER:-}" ]] && printf '%s\n' "$CTRADER_CACHE_PROVIDER"
  [[ -d "$SCRIPT_DIR/data/V1" ]] && find "$SCRIPT_DIR/data/V1" -mindepth 1 -maxdepth 1 -type d -exec basename {} \; ; } | awk 'NF && !seen[$0]++'; }
canonical_cache_dir() { printf '%s/%s/%s/%s' "$SCRIPT_DIR/data" "$CACHE_ACCOUNT" "$1" "$2"; }
prepare_cache_layout() {
  mkdir -p "$SCRIPT_DIR/data/$CACHE_ACCOUNT"
  while IFS= read -r provider; do
    [[ -z "$provider" ]] && continue
    for symbol in "${SYMBOLS[@]}"; do
      local cdir ldir; cdir=$(canonical_cache_dir "$symbol" m1); ldir="$SCRIPT_DIR/data/V1/$provider/$symbol/m1"
      mkdir -p "$cdir" "$(dirname "$ldir")"
      [[ -e "$ldir" && ! -L "$ldir" ]] && { echo "Cache path is a real dir, not a symlink: $ldir" >&2; continue; }
      # Race-tolerant (EXP-006 O3 op-note): concurrent bounded `one` cells re-run this prep and can
      # collide on `ln -sfn` ("File exists") for a shared symbol. The link content is identical
      # regardless of which racer wins, so tolerating the collision is safe (idempotent).
      ln -sfn "../../../$CACHE_ACCOUNT/$symbol/m1" "$ldir" 2>/dev/null || true
    done
  done < <(cache_providers)
}

# The StrategyRunParquetWriter appends a UTC timestamp suffix to the run dir
# (`{strategy}_{symbol}_{domain}_{stamp}`), so resolve the NEWEST matching dir rather
# than an exact unsuffixed path (else run_complete never matches -> 4h max_wait hang).
run_dir_for()  { { ls -dt "$OUT_DIR/${STRATEGY}_$(echo "$1" | tr 'A-Z' 'a-z')_${2}_"*/ 2>/dev/null || true; } | head -1; }
# Gate on the StrategyHost emissions only (the binding artifacts). The cTrader `--report-json`
# ($3) is a diagnostic the Python suite never consumes, and cTrader's console can crash on shutdown
# AFTER the parquet is flushed (state-machine exception) — gating on the report then hangs the worker
# for the full max_wait. positions/trade_blotter/run_metadata are written together at Dispose.
run_complete() { local d; d=$(run_dir_for "$1" "$2"); [[ -n "$d" && "$d" != "${3:-}" && -s "${d}run_metadata.json" && -s "${d}positions.parquet" && -s "${d}trade_blotter.parquet" ]]; }

run_backtest() {
  local symbol="$1" domain="$2"
  # EXP-019: the same cell may be run repeatedly (seeded schedule sweeps). Gate completion on a
  # run dir NEWER than the newest one existing before this container started, else the previous
  # seed's finished artifacts satisfy run_complete and the new container is stopped prematurely.
  local baseline; baseline=$(run_dir_for "$symbol" "$domain")
  local run_id="${EXP_ID}_${STRATEGY}_${symbol}_${domain}"
  local report="$SCRIPT_DIR/reports/$EXP_ID/${STRATEGY}_${symbol}_${domain}.json"
  local container; container="ctrader-$(echo "$run_id" | tr 'A-Z_' 'a-z-')-$$"
  local max_wait="${CTRADER_RUN_MAX_WAIT_SECONDS:-14400}" start cid
  rm -f "$report"; echo "Running $run_id"
  cid=$(docker run --rm -d --name "$container" --platform "$PLATFORM" \
    --mount "type=bind,src=$ROOT_DIR,dst=/workspace" \
    --mount "type=bind,src=$PWD_FILE_HOST,dst=/secrets/ctrader-cli.pwd,readonly" \
    "$IMAGE" backtest /workspace/bin/Debug/net6.0/Xen.algo \
      --start="02/01/2021 00:00" --end="${BACKTEST_END[$symbol]}" \
      --data-mode=m1 --data-dir=/workspace/tools/ctrader-cli/data --balance="$BALANCE" \
      --report-json="/workspace/tools/ctrader-cli/reports/$EXP_ID/${STRATEGY}_${symbol}_${domain}.json" \
      --ctid="$CTID" --pwd-file=/secrets/ctrader-cli.pwd --account="$ACCOUNT" "${broker_args[@]}" \
      --symbol="$symbol" --period=m1 --full-access --Mode="$MODE" \
      --Strategy="$STRATEGY_VALUE" --AnalysisEndUtc="${ANALYSIS_END[$symbol]}" \
      --StrategyOutputDirectory=/workspace/data/strategy_runs/$EXP_ID \
      --DomainMinutes="$(domain_minutes "$domain")" \
      --StrictCoverage="$(strict_coverage "$domain")" --MinCoverage="$(min_coverage "$domain")" \
      "${MODEL_ARGS[@]}" ${MODEL_ARGS_BY_SYMBOL[$symbol]:-})
  docker logs -f "$cid" | sed -u "s/^/[$run_id] /" & local log_pid=$!
  start=$(date +%s)
  while docker ps -q --filter "id=$cid" | grep -q .; do
    run_complete "$symbol" "$domain" "$baseline" && { sleep 2; docker stop "$cid" >/dev/null || true; break; }
    (( $(date +%s) - start > max_wait )) && { docker logs --tail 80 "$cid" >&2 || true; docker stop "$cid" >/dev/null || true; echo "Timed out: $run_id" >&2; return 1; }
    sleep 5
  done
  wait "$log_pid" 2>/dev/null || true
  # Close the flush race: a container that exits on its own may write positions/trade_blotter/report
  # a moment after the while-loop sees it gone — give the artifacts a few seconds to land.
  for _ in 1 2 3 4 5 6; do run_complete "$symbol" "$domain" "$baseline" && break; sleep 2; done
  run_complete "$symbol" "$domain" "$baseline" || { echo "$run_id produced incomplete artifacts." >&2; return 1; }
  echo "Completed $run_id -> $(run_dir_for "$symbol" "$domain")"
}

run_symbol_worker() { local s="$1"; for d in "${DOMAINS[@]}"; do run_backtest "$s" "$d"; done; }

case "${1:-all}" in
  cache-layout) prepare_cache_layout; find "$SCRIPT_DIR/data" -maxdepth 4 \( -type d -o -type l \) | sort; exit 0;;
  one) [[ $# -eq 3 ]] || { echo "Usage: $0 <EXP-ID> one <SYMBOL> <DOMAIN>" >&2; exit 2; }
       prepare_cache_layout; run_backtest "$2" "$3"; exit $?;;
  # Bounded parallelism (EXP-020 op-note): an unbounded 16-way container burst makes the
  # cTrader console crash at startup ("Message expected", backtest stuck at 0.00%) on a
  # fraction of cells — a login/startup race that never appeared on the 1-2 symbol confs
  # pre-EXP-019. Default bound 4; override with CTRADER_MAX_PARALLEL. Also stagger starts.
  parallel) prepare_cache_layout; status=0
            max_par="${CTRADER_MAX_PARALLEL:-4}"
            for s in "${SYMBOLS[@]}"; do
              while (( $(jobs -rp | wc -l) >= max_par )); do wait -n || status=1; done
              run_symbol_worker "$s" &
              sleep 10   # stagger container/login startup
            done
            while (( $(jobs -rp | wc -l) > 0 )); do wait -n || status=1; done
            exit "$status";;
  all|"") prepare_cache_layout; for s in "${SYMBOLS[@]}"; do run_symbol_worker "$s"; done;;
  *) echo "Unknown command: $1" >&2; exit 2;;
esac
echo "Done. Strategy-host outputs under $OUT_DIR"
