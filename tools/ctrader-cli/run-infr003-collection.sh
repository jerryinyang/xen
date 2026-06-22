#!/usr/bin/env bash
# INFR-003 — 5-year 1-minute time-bar collection (full-universe re-collection).
#
# Runs the Xen robot in TimeBars mode (Mode=1, CollectTimeBars=true) over the
# 16-instrument CF-CAPGEO-001 universe (the VAL-003 universe minus DE30, dropped
# by operator ratification 2026-06-21 — see the INFR-003 checkpoint design §3.1):
#   EURUSD GBPUSD USDJPY USDCHF USDCAD AUDUSD NZDUSD EURJPY GBPJPY AUDJPY
#   XAUUSD BTCUSD USTEC US500 US2000 JP225
# This is a FULL re-collection: unlike INFR-002 (new-universe only), INFR-003
# re-collects the original core (EURUSD/XAUUSD/BTCUSD/USTEC) too, because their
# existing analysis70_* files are only ~3.3y. Existing files are RETAINED for
# closed-family reproducibility; the new timestamped files become canonical for
# CF-CAPGEO-001 (latest-glob convention).
#
# HOLDOUT POLICY (binding from the moment each file lands): the final 30% of
# each instrument's chronologically ordered new dataset is GLOBAL HOLDOUT,
# sealed under the standard rules on THAT file's own (longer) timeline; the
# first 70% splits 70/30 TRAIN/TEST on the 1-minute-row timestamp convention.
# NO experiment reads any new 5-year row before VAL-005
# (python/experiments/VAL-005/) passes. The TEST-read ledger is re-materialized
# on the new strata (all 0 counted reads) at VAL-005 PASS.
#
# Execution model: the cTrader console backtest does not exit on its own after
# the run completes (same behaviour the EXP-029 script worked around), so each
# container is started detached, polled for completion (report JSON present +
# the new timebars parquet carrying its final "PAR1" footer), then stopped.
# Symbols run concurrently through a worker pool (default 4; see
# INFR003_MAX_PARALLEL).
#
# Usage:
#   ./run-infr003-collection.sh              # all 16 symbols, pool of 4
#   ./run-infr003-collection.sh one EURUSD   # single symbol
#   ./run-infr003-collection.sh metadata     # robot parameter listing
#   INFR003_MAX_PARALLEL=2 ./run-infr003-collection.sh
#
# Output: data/timebars/timebars_<symbol>_<start>_<collected>.parquet — written
# by the robot to the OutputDirectory constant compiled into Xen.cs, so the
# host data/timebars directory is bind-mounted at that exact absolute path
# inside the container (XEN_TIMEBARS_DST below must match Xen.cs).
#
# Broker symbol names for the index CFDs vary (e.g. US500 vs SPX500). If a
# symbol is rejected, find the broker's name with the cTrader app and run:
#   ./run-infr003-collection.sh one <BROKER_SYMBOL>
#
# Build the robot first:  dotnet build Xen.csproj -c Debug
set -euo pipefail

SCRIPT_DIR=$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)
ROOT_DIR=$(cd "$SCRIPT_DIR/../.." && pwd)

ENV_FILE="${CTRADER_ENV_FILE:-$SCRIPT_DIR/.env}"
if [[ -f "$ENV_FILE" ]]; then
  # shellcheck disable=SC1090
  source "$ENV_FILE"
fi

IMAGE="${CTRADER_IMAGE:-ghcr.io/spotware/ctrader-console:latest}"
PLATFORM="${CTRADER_PLATFORM:-linux/amd64}"
CTID="${CTRADER_CTID:-}"
ACCOUNT="${CTRADER_ACCOUNT:-}"
CACHE_ACCOUNT="${CTRADER_CACHE_ACCOUNT:-${CTRADER_ACCOUNT:-}}"
PWD_FILE_HOST="${CTRADER_PWD_FILE:-$SCRIPT_DIR/ctrader-cli.pwd}"
BROKER="${CTRADER_BROKER:-}"
MAX_PARALLEL="${INFR003_MAX_PARALLEL:-4}"
# 5y of m1 is ~1.5x INFR-002's span; allow a longer per-symbol ceiling.
MAX_WAIT="${CTRADER_RUN_MAX_WAIT_SECONDS:-21600}"

# Must match the OutputDirectory constant in Xen.cs.
XEN_TIMEBARS_DST="/Users/jerryinyang/cAlgo/Sources/Robots/Xen/Xen/data/timebars"

# Collection window (operator ratification 2026-06-21, design §3.1 / D-span):
# ~5-year target starting 2021-06-01; the CLI begins wherever the broker's m1
# history actually starts if later (per-instrument truncation disclosed in
# VAL-005 G3). The end date defines where the sealed final-30% holdout boundary
# falls — record any override in the INFR-003 row.
COLLECT_START="${INFR003_START:-01/06/2021 00:00}"
COLLECT_END="${INFR003_END:-21/06/2026 00:00}"

if [[ "${1:-}" == "metadata" ]]; then
  exec docker run --rm \
    --platform "$PLATFORM" \
    --mount "type=bind,src=$ROOT_DIR,dst=/workspace" \
    "$IMAGE" metadata /workspace/bin/Debug/net6.0/Xen.algo
fi

if [[ -z "$CTID" || -z "$ACCOUNT" ]]; then
  echo "Set CTRADER_CTID and CTRADER_ACCOUNT in $ENV_FILE or the environment." >&2
  exit 2
fi
if [[ -z "$CACHE_ACCOUNT" ]]; then
  echo "Set CTRADER_CACHE_ACCOUNT or CTRADER_ACCOUNT in $ENV_FILE or the environment." >&2
  exit 2
fi
if [[ ! -f "$PWD_FILE_HOST" ]]; then
  echo "Password file not found: $PWD_FILE_HOST" >&2
  echo "Create it with only your cTrader password, no trailing notes." >&2
  exit 2
fi
if [[ ! -f "$ROOT_DIR/bin/Debug/net6.0/Xen.algo" ]]; then
  echo "Missing $ROOT_DIR/bin/Debug/net6.0/Xen.algo; run dotnet build Xen.csproj first." >&2
  exit 2
fi

mkdir -p "$ROOT_DIR/data/timebars" "$SCRIPT_DIR/reports" "$SCRIPT_DIR/data"

broker_args=()
if [[ -n "$BROKER" ]]; then
  broker_args=(--broker="$BROKER")
fi

# CF-CAPGEO-001 16-instrument universe (design §3.1 / D-instr; DE30 dropped).
# Override with INFR003_SYMBOLS (space-separated) for broker-specific names.
if [[ -n "${INFR003_SYMBOLS:-}" ]]; then
  read -r -a symbols <<<"$INFR003_SYMBOLS"
else
  symbols=(EURUSD GBPUSD USDJPY USDCHF USDCAD AUDUSD NZDUSD EURJPY GBPJPY AUDJPY
           XAUUSD BTCUSD USTEC US500 US2000 JP225)
fi

timeframes=(m1)

canonical_cache_dir() {
  local symbol="$1"
  local timeframe="$2"
  printf '%s/%s/%s/%s' "$SCRIPT_DIR/data" "$CACHE_ACCOUNT" "$symbol" "$timeframe"
}

legacy_cache_link_target() {
  local symbol="$1"
  local timeframe="$2"
  printf '../../../%s/%s/%s' "$CACHE_ACCOUNT" "$symbol" "$timeframe"
}

cache_providers() {
  {
    if [[ -n "${CTRADER_CACHE_PROVIDER:-}" ]]; then
      printf '%s\n' "$CTRADER_CACHE_PROVIDER"
    fi
    if [[ -d "$SCRIPT_DIR/data/V1" ]]; then
      find "$SCRIPT_DIR/data/V1" -mindepth 1 -maxdepth 1 -type d -exec basename {} \;
    fi
  } | awk 'NF && !seen[$0]++'
}

prepare_cache_layout() {
  mkdir -p "$SCRIPT_DIR/data/$CACHE_ACCOUNT"
  while IFS= read -r provider; do
    [[ -z "$provider" ]] && continue
    for symbol in "${symbols[@]}"; do
      for timeframe in "${timeframes[@]}"; do
        local canonical_dir
        local legacy_dir
        canonical_dir=$(canonical_cache_dir "$symbol" "$timeframe")
        legacy_dir="$SCRIPT_DIR/data/V1/$provider/$symbol/$timeframe"
        mkdir -p "$canonical_dir" "$(dirname "$legacy_dir")"
        if [[ -e "$legacy_dir" && ! -L "$legacy_dir" ]]; then
          echo "Cache path is a real directory, not a symlink: $legacy_dir" >&2
          continue
        fi
        ln -sfn "$(legacy_cache_link_target "$symbol" "$timeframe")" "$legacy_dir"
      done
    done
  done < <(cache_providers)
}

# Existing (pre-INFR-003) files for a symbol, EXCLUDING analysis70_* core files.
# Used to snapshot "before" state so the new collection file can be isolated.
symbol_output_files() {
  local symbol_lc
  symbol_lc=$(printf '%s' "$1" | tr '[:upper:]' '[:lower:]')
  find "$ROOT_DIR/data/timebars" -maxdepth 1 -type f \
    -name "timebars_${symbol_lc}_*.parquet" ! -name "timebars_analysis70_*"
}

newest_new_parquet() {
  local symbol="$1"
  local before="$2"
  comm -13 <(printf '%s\n' "$before") <(symbol_output_files "$symbol" | sort) \
    | awk 'NF' | tail -1
}

# Complete when the CLI has written its report AND the new parquet carries the
# final Parquet footer magic ("PAR1"), i.e. the robot's OnStop disposed the
# writer. The container itself never exits on its own; the caller stops it.
run_complete() {
  local symbol="$1"
  local report="$2"
  local before="$3"
  [[ -s "$report" ]] || return 1
  local newest
  newest=$(newest_new_parquet "$symbol" "$before")
  [[ -n "$newest" && -s "$newest" ]] || return 1
  [[ "$(tail -c 4 "$newest" 2>/dev/null)" == "PAR1" ]] || return 1
  return 0
}

run_collection() {
  local symbol="$1"
  local run_id="timebars_${symbol}"
  local report="$SCRIPT_DIR/reports/${run_id}.json"
  local container="ctrader-infr003-$(printf '%s' "$symbol" | tr '[:upper:]' '[:lower:]')-$$"
  local before_files
  local cid
  local log_pid=""
  local start

  before_files=$(symbol_output_files "$symbol" | sort)
  rm -f "$report"
  echo "Collecting $symbol ($COLLECT_START -> $COLLECT_END)"

  cid=$(docker run --rm -d \
    --name "$container" \
    --platform "$PLATFORM" \
    --mount "type=bind,src=$ROOT_DIR,dst=/workspace" \
    --mount "type=bind,src=$ROOT_DIR/data/timebars,dst=$XEN_TIMEBARS_DST" \
    --mount "type=bind,src=$PWD_FILE_HOST,dst=/secrets/ctrader-cli.pwd,readonly" \
    "$IMAGE" backtest /workspace/bin/Debug/net6.0/Xen.algo \
      --start="$COLLECT_START" \
      --end="$COLLECT_END" \
      --data-mode=m1 \
      --data-dir=/workspace/tools/ctrader-cli/data \
      --balance=10000 \
      --report-json="/workspace/tools/ctrader-cli/reports/${run_id}.json" \
      --ctid="$CTID" \
      --pwd-file=/secrets/ctrader-cli.pwd \
      --account="$ACCOUNT" \
      "${broker_args[@]}" \
      --symbol="$symbol" \
      --period=m1 \
      --full-access \
      --Mode=1 \
      --CollectTimeBars=true)

  docker logs -f "$cid" 2>&1 | sed -u "s/^/[$symbol] /" &
  log_pid=$!
  start=$(date +%s)

  while docker ps -q --filter "id=$cid" | grep -q .; do
    if run_complete "$symbol" "$report" "$before_files"; then
      sleep 2
      docker stop "$cid" >/dev/null 2>&1 || true
      break
    fi
    if (( $(date +%s) - start > MAX_WAIT )); then
      docker logs --tail 80 "$cid" >&2 || true
      docker stop "$cid" >/dev/null 2>&1 || true
      echo "Timed out waiting for $symbol after ${MAX_WAIT}s" >&2
      return 1
    fi
    sleep 5
  done

  if [[ -n "$log_pid" ]]; then
    wait "$log_pid" 2>/dev/null || true
  fi

  if ! run_complete "$symbol" "$report" "$before_files"; then
    echo "$symbol: container exited without a complete report + finalized parquet." >&2
    return 1
  fi

  local file
  file=$(newest_new_parquet "$symbol" "$before_files")
  echo "Completed $symbol -> $file"
  echo "HOLDOUT SEALED at first touch: final 30% of $(basename "$file") is global holdout."
}

# ---------------------------------------------------------------------------
# Entry points
# ---------------------------------------------------------------------------

# Worker invocation: `one <SYMBOL>` collects a single symbol. Used directly for
# broker-specific names and recursively by the parallel pool below. Cache
# layout preparation is skipped when the parent already did it.
if [[ "${1:-}" == "one" ]]; then
  if [[ $# -ne 2 ]]; then
    echo "Usage: $0 one <SYMBOL>" >&2
    exit 2
  fi
  symbols=("$2")
  if [[ -z "${INFR003_SKIP_CACHE_PREP:-}" ]]; then
    prepare_cache_layout
  fi
  run_collection "$2"
  exit $?
fi

# Default: run all symbols through a concurrent worker pool. xargs -P provides
# the pool portably (macOS bash 3.2 has no `wait -n`); each worker re-enters
# this script as `one <SYMBOL>`.
prepare_cache_layout
echo "Collecting ${#symbols[@]} symbols with up to $MAX_PARALLEL concurrent runs."

status=0
printf '%s\n' "${symbols[@]}" \
  | INFR003_SKIP_CACHE_PREP=1 xargs -n1 -P "$MAX_PARALLEL" "$0" one \
  || status=1

if [[ "$status" -eq 0 ]]; then
  echo "Done. 5-year time bars are under $ROOT_DIR/data/timebars."
  echo "Next: run VAL-005 (python/experiments/VAL-005/) before any experiment touches this data."
else
  echo "One or more symbols failed; see messages above. Re-run failed symbols with: $0 one <SYMBOL>" >&2
fi
exit "$status"
