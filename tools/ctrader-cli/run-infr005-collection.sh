#!/usr/bin/env bash
# INFR-005 — 5-year 1-minute time-bar collection (indices-basket completion).
#
# Runs the Xen robot in TimeBars mode (Mode=1, CollectTimeBars=true) over the
# 6 index symbols missing from the INFR-003 5-year dataset, completing the
# 10-instrument Indices basket (AUS200 US30 EU50 GER40 HK50 UK100 + the 4
# already loaded by INFR-003: JP225 USTEC[=US100] US500 US2000):
#   AUS200 US30 EU50 GER40 HK50 UK100
# This adds NEW symbols only; it does NOT re-collect the 16 INFR-003 instruments.
# GER40 (DAX 40) is collected fresh as a live-history broker symbol — it is NOT
# the retired DE30 (broker m1 stale to 2026-01-16, dropped at INFR-003 §3.1).
# New timestamped files become canonical for the completed Indices basket
# (latest-glob convention); existing files are untouched.
#
# BROKER SYMBOL NAMES (this broker uses USTEC/US500/US2000/JP225/DE30). The 6
# names below are the operator's requested primaries; index-CFD names vary by
# broker. Known alternates: EU50→STOXX50/EUSTX50; GER40→DE40; US30→DJ30/WS30;
# UK100→FTSE100; AUS200→AU200; HK50→HK50/HSI50. If a symbol is REJECTED, find
# the broker's exact string in the cTrader app and run:
#   ./run-infr005-collection.sh one <BROKER_SYMBOL>
# or override the whole set:  INFR005_SYMBOLS="AU200 DJ30 ..." ./run-infr005-collection.sh
#
# HOLDOUT POLICY (binding from the moment each file lands): the final 30% of
# each instrument's chronologically ordered new dataset is GLOBAL HOLDOUT,
# sealed under the standard rules on THAT file's own timeline; the first 70%
# splits 70/30 TRAIN/TEST on the 1-minute-row timestamp convention. NO
# experiment reads any new index row before VAL-007
# (python/experiments/VAL-007/) passes. The TEST-read ledger is extended with
# the 6 new instrument×domain strata (all 0 counted reads) at VAL-007 PASS.
#
# Execution model: the cTrader console backtest does not exit on its own after
# the run completes (same behaviour the EXP-029 script worked around), so each
# container is started detached, polled for completion (report JSON present +
# the new timebars parquet carrying its final "PAR1" footer), then stopped.
# Symbols run concurrently through a worker pool (default 4; see
# INFR005_MAX_PARALLEL).
#
# Usage:
#   ./run-infr005-collection.sh              # all 6 index symbols, pool of 4
#   ./run-infr005-collection.sh one AUS200   # single symbol
#   ./run-infr005-collection.sh metadata     # robot parameter listing
#   INFR005_MAX_PARALLEL=2 ./run-infr005-collection.sh
#
# Output: data/timebars/timebars_<symbol>_<start>_<collected>.parquet — written
# by the robot to the OutputDirectory constant compiled into Xen.cs, so the
# host data/timebars directory is bind-mounted at that exact absolute path
# inside the container (XEN_TIMEBARS_DST below must match Xen.cs).
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
MAX_PARALLEL="${INFR005_MAX_PARALLEL:-4}"
# 5y of m1 is ~1.5x INFR-002's span; allow a longer per-symbol ceiling.
MAX_WAIT="${CTRADER_RUN_MAX_WAIT_SECONDS:-21600}"

# Must match the OutputDirectory constant in Xen.cs.
XEN_TIMEBARS_DST="/Users/jerryinyang/cAlgo/Sources/Robots/Xen/Xen/data/timebars"

# Collection window (operator ratification 2026-06-21, design §3.1 / D-span):
# ~5-year target starting 2021-06-01; the CLI begins wherever the broker's m1
# history actually starts if later (per-instrument truncation disclosed in
# VAL-007 G3). The end date defines where the sealed final-30% holdout boundary
# falls — record any override in the INFR-005 row.
COLLECT_START="${INFR005_START:-01/06/2021 00:00}"
COLLECT_END="${INFR005_END:-21/06/2026 00:00}"

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

# Indices-basket completion: the 6 index symbols missing from INFR-003.
# Override with INFR005_SYMBOLS (space-separated) for broker-specific names
# (see the BROKER SYMBOL NAMES note in the header for known alternates).
if [[ -n "${INFR005_SYMBOLS:-}" ]]; then
  read -r -a symbols <<<"$INFR005_SYMBOLS"
else
  symbols=(AUS200 US30 EU50 GER40 HK50 UK100)
fi

timeframes=(m1)

# Known broker-string alternates per canonical index symbol (design D-names +
# header note). collect_with_fallback tries these in order until one produces a
# finalized parquet, so a broker that rejects the primary name is handled
# automatically instead of requiring a manual `one <BROKER_SYMBOL>` re-run.
symbol_candidates() {
  case "$1" in
    AUS200) echo "AUS200 AU200 ASX200 AUS200.i" ;;
    US30)   echo "US30 DJ30 WS30 US30.i DJI30" ;;
    EU50)   echo "EU50 STOXX50 EUSTX50 STOXX50E EU50.i" ;;
    GER40)  echo "GER40 DE40 DAX40 GER40.i" ;;
    HK50)   echo "HK50 HSI50 HK50.i HSI" ;;
    UK100)  echo "UK100 FTSE100 UK100.i FTSE" ;;
    *)      echo "$1" ;;
  esac
}

RESOLVED_LOG="$SCRIPT_DIR/reports/infr005-resolved.txt"

# Try each known broker-string alternate for a canonical symbol until one lands
# a valid parquet; record the resolved mapping for the VAL-007 report.
collect_with_fallback() {
  local canonical="$1"
  local candidates
  read -r -a candidates <<<"$(symbol_candidates "$canonical")"
  local cand
  for cand in "${candidates[@]}"; do
    echo "[$canonical] trying broker symbol '$cand'"
    if run_collection "$cand"; then
      echo "RESOLVED $canonical -> $cand" | tee -a "$RESOLVED_LOG"
      return 0
    fi
    echo "[$canonical] candidate '$cand' failed; trying next alternate." >&2
  done
  echo "$canonical: all candidates failed (${candidates[*]})" >&2
  return 1
}

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

# Existing (pre-existing) files for a symbol, EXCLUDING analysis70_* core files.
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
  if [[ -z "${INFR005_SKIP_CACHE_PREP:-}" ]]; then
    prepare_cache_layout
  fi
  collect_with_fallback "$2"
  exit $?
fi

# Default: run all symbols through a concurrent worker pool. xargs -P provides
# the pool portably (macOS bash 3.2 has no `wait -n`); each worker re-enters
# this script as `one <SYMBOL>`.
prepare_cache_layout
echo "Collecting ${#symbols[@]} symbols with up to $MAX_PARALLEL concurrent runs."

status=0
printf '%s\n' "${symbols[@]}" \
  | INFR005_SKIP_CACHE_PREP=1 xargs -n1 -P "$MAX_PARALLEL" "$0" one \
  || status=1

if [[ "$status" -eq 0 ]]; then
  echo "Done. 5-year index time bars are under $ROOT_DIR/data/timebars."
  echo "Next: run VAL-007 (python/experiments/VAL-007/) before any experiment touches this data."
else
  echo "One or more symbols failed; see messages above. Re-run failed symbols with: $0 one <SYMBOL>" >&2
fi
exit "$status"
