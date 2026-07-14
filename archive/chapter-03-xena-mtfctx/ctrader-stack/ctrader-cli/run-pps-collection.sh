#!/usr/bin/env bash
# PPS — EXP-095/096 portfolio instrument 1-minute time-bar collection.
#
# Runs the Xen robot in TimeBars mode (Mode=1, CollectTimeBars=true) over the
# 8 instruments that make up the EXP-095/096 deployment portfolio (the
# G-021-confirmed cells):
#   EURUSD XAUUSD USDCHF AUDJPY EURJPY GBPJPY USTEC US2000
#
# Collected from broker account 5167272 (different account, same broker as the
# main data). Output goes to data/timebars/pps/ to keep it separate from the
# primary INFR-003 dataset.
#
# Execution model: same as INFR-003 — containers run detached, polled for
# completion (report JSON + "PAR1" footer), then stopped. Symbols run
# concurrently through a worker pool (default 4; see PPS_MAX_PARALLEL).
#
# Usage:
#   ./run-pps-collection.sh              # all symbols, pool of 4
#   ./run-pps-collection.sh one EURUSD   # single symbol
#   ./run-pps-collection.sh metadata     # robot parameter listing
#   PPS_MAX_PARALLEL=2 ./run-pps-collection.sh
#
# Output: data/timebars/pps/timebars_<symbol>_<start>_<collected>.parquet
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
ACCOUNT="${CTRADER_ACCOUNT:-5167272}"
CACHE_ACCOUNT="${CTRADER_CACHE_ACCOUNT:-${ACCOUNT:-}}"
PWD_FILE_HOST="${CTRADER_PWD_FILE:-$SCRIPT_DIR/ctrader-cli.pwd}"
BROKER="${CTRADER_BROKER:-}"
MAX_PARALLEL="${PPS_MAX_PARALLEL:-4}"
MAX_WAIT="${CTRADER_RUN_MAX_WAIT_SECONDS:-21600}"

XEN_TIMEBARS_DST="/Users/jerryinyang/cAlgo/Sources/Robots/Xen/Xen/data/timebars"
PPS_OUTPUT_DIR="$ROOT_DIR/data/timebars/pps"

COLLECT_START="${PPS_START:-01/06/2021 00:00}"
COLLECT_END="${PPS_END:-21/06/2026 00:00}"

if [[ "${1:-}" == "metadata" ]]; then
  exec docker run --rm \
    --platform "$PLATFORM" \
    --mount "type=bind,src=$ROOT_DIR,dst=/workspace" \
    "$IMAGE" metadata /workspace/bin/Debug/net6.0/Xen.algo
fi

if [[ -z "$CTID" ]]; then
  echo "Set CTRADER_CTID in $ENV_FILE or the environment." >&2
  exit 2
fi
if [[ ! -f "$PWD_FILE_HOST" ]]; then
  echo "Password file not found: $PWD_FILE_HOST" >&2
  exit 2
fi
if [[ ! -f "$ROOT_DIR/bin/Debug/net6.0/Xen.algo" ]]; then
  echo "Missing $ROOT_DIR/bin/Debug/net6.0/Xen.algo; run dotnet build Xen.csproj first." >&2
  exit 2
fi

mkdir -p "$PPS_OUTPUT_DIR" "$SCRIPT_DIR/reports" "$SCRIPT_DIR/data"

broker_args=()
if [[ -n "$BROKER" ]]; then
  broker_args=(--broker="$BROKER")
fi

# EXP-095/096 portfolio instruments (8 G-021-confirmed cells).
if [[ -n "${PPS_SYMBOLS:-}" ]]; then
  read -r -a symbols <<<"$PPS_SYMBOLS"
else
  symbols=(EURUSD XAUUSD USDCHF AUDJPY EURJPY GBPJPY USTEC US2000)
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

symbol_output_files() {
  local symbol_lc
  symbol_lc=$(printf '%s' "$1" | tr '[:upper:]' '[:lower:]')
  find "$PPS_OUTPUT_DIR" -maxdepth 1 -type f \
    -name "timebars_${symbol_lc}_*.parquet"
}

newest_new_parquet() {
  local symbol="$1"
  local before="$2"
  comm -13 <(printf '%s\n' "$before") <(symbol_output_files "$symbol" | sort) \
    | awk 'NF' | tail -1
}

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
  local run_id="pps_timebars_${symbol}"
  local report="$SCRIPT_DIR/reports/${run_id}.json"
  local container="ctrader-pps-$(printf '%s' "$symbol" | tr '[:upper:]' '[:lower:]')-$$"
  local before_files
  local cid
  local log_pid=""
  local start

  before_files=$(symbol_output_files "$symbol" | sort)
  rm -f "$report"
  echo "Collecting $symbol ($COLLECT_START -> $COLLECT_END) -> pps/"

  cid=$(docker run --rm -d \
    --name "$container" \
    --platform "$PLATFORM" \
    --mount "type=bind,src=$ROOT_DIR,dst=/workspace" \
    --mount "type=bind,src=$PPS_OUTPUT_DIR,dst=$XEN_TIMEBARS_DST" \
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
}

if [[ "${1:-}" == "one" ]]; then
  if [[ $# -ne 2 ]]; then
    echo "Usage: $0 one <SYMBOL>" >&2
    exit 2
  fi
  symbols=("$2")
  if [[ -z "${PPS_SKIP_CACHE_PREP:-}" ]]; then
    prepare_cache_layout
  fi
  run_collection "$2"
  exit $?
fi

prepare_cache_layout
echo "Collecting ${#symbols[@]} PPS symbols with up to $MAX_PARALLEL concurrent runs."

status=0
printf '%s\n' "${symbols[@]}" \
  | PPS_SKIP_CACHE_PREP=1 xargs -n1 -P "$MAX_PARALLEL" "$0" one \
  || status=1

if [[ "$status" -eq 0 ]]; then
  echo "Done. PPS portfolio time bars are under $PPS_OUTPUT_DIR."
else
  echo "One or more symbols failed; see messages above. Re-run failed symbols with: $0 one <SYMBOL>" >&2
fi
exit "$status"
