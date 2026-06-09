#!/usr/bin/env bash
# EXP-029 — cTrader per-bar streaming parity for the faithful AVWAP strategy.
#
# Runs ONLY the corrected AvwapBaseline strategy (pyramid bounces opened as
# independent positions; per-bar regime + per-bounce AVWAP detail serialized) over
# the 12 cells (4 instruments x {5m,1h,4h}), fenced by AnalysisEndUtc. Build the
# corrected robot first:  dotnet build Xen.csproj -c Debug
# A run is accepted only if it emits avwap_events.parquet (the corrected emission);
# the EXP-023 avwap_baseline_* runs lack it and are NOT reusable by EXP-029.
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

mkdir -p "$ROOT_DIR/data/strategy_runs" "$SCRIPT_DIR/reports" "$SCRIPT_DIR/data"

broker_args=()
if [[ -n "$BROKER" ]]; then
  broker_args=(--broker="$BROKER")
fi

symbols=(BTCUSD EURUSD USTEC XAUUSD)
declare -A analysis_end=(
  [BTCUSD]="2025-06-17T22:38:00Z"
  [EURUSD]="2025-05-09T16:55:00Z"
  [USTEC]="2025-05-12T04:54:00Z"
  [XAUUSD]="2025-05-12T03:35:00Z"
)
declare -A backtest_end=(
  [BTCUSD]="17/06/2025 22:39"
  [EURUSD]="09/05/2025 16:56"
  [USTEC]="12/05/2025 04:55"
  [XAUUSD]="12/05/2025 03:36"
)

domains=(5m 1h 4h)
strategies=(AvwapBaseline)
timeframes=(m1)

domain_minutes() {
  case "$1" in
    5m) echo 5 ;;
    1h) echo 60 ;;
    4h) echo 240 ;;
    *) echo "unknown domain: $1" >&2; return 1 ;;
  esac
}

strict_coverage() {
  [[ "$1" == "5m" ]] && echo true || echo false
}

min_coverage() {
  [[ "$1" == "5m" ]] && echo 0.0 || echo 0.9
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

prepare_cache_layout() {
  mkdir -p "$SCRIPT_DIR/data/$CACHE_ACCOUNT"

  if [[ -d "$SCRIPT_DIR/data/V1" ]]; then
    while IFS= read -r legacy_dir; do
      [[ -L "$legacy_dir" ]] && continue
      local timeframe
      local symbol
      local canonical_dir
      timeframe=$(basename "$legacy_dir")
      symbol=$(basename "$(dirname "$legacy_dir")")
      canonical_dir=$(canonical_cache_dir "$symbol" "$timeframe")
      if [[ -e "$canonical_dir" ]]; then
        if [[ -d "$canonical_dir" && -z "$(find "$canonical_dir" -mindepth 1 -print -quit)" ]]; then
          rmdir "$canonical_dir"
        else
          echo "Cache already exists at $canonical_dir; leaving existing $legacy_dir in place." >&2
          continue
        fi
      fi
      mkdir -p "$(dirname "$canonical_dir")"
      mv "$legacy_dir" "$canonical_dir"
      ln -s "$(legacy_cache_link_target "$symbol" "$timeframe")" "$legacy_dir"
    done < <(find "$SCRIPT_DIR/data/V1" -mindepth 3 -maxdepth 3 -type d | sort)
  fi

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

print_cache_layout() {
  echo "Canonical cache root: $SCRIPT_DIR/data/$CACHE_ACCOUNT"
  find "$SCRIPT_DIR/data" -maxdepth 4 \( -type d -o -type l \) | sort
}

strategy_value() {
  case "$1" in
    AvwapBaseline) echo 1 ;;
    Donchian20) echo 2 ;;
    *) echo "unknown strategy: $1" >&2; return 1 ;;
  esac
}

strategy_prefix() {
  case "$1" in
    AvwapBaseline) echo avwap_baseline ;;
    Donchian20) echo donchian_20 ;;
    *) echo "unknown strategy: $1" >&2; return 1 ;;
  esac
}

latest_run_dir() {
  local strategy="$1"
  local symbol="$2"
  local domain="$3"
  local prefix
  prefix=$(strategy_prefix "$strategy")
  find "$ROOT_DIR/data/strategy_runs" -maxdepth 1 -type d \
    -name "${prefix}_$(printf '%s' "$symbol" | tr '[:upper:]' '[:lower:]')_${domain}_*" \
    | sort \
    | tail -1
}

run_complete() {
  local strategy="$1"
  local symbol="$2"
  local domain="$3"
  local report="$4"
  local run_dir
  run_dir=$(latest_run_dir "$strategy" "$symbol" "$domain")
  [[ -n "$run_dir" ]] \
    && [[ -s "$run_dir/run_metadata.json" ]] \
    && [[ -s "$run_dir/positions.parquet" ]] \
    && [[ -s "$run_dir/trade_blotter.parquet" ]] \
    && [[ -s "$run_dir/avwap_events.parquet" ]] \
    && [[ -s "$report" ]]
}

run_backtest() {
  local symbol="$1"
  local domain="$2"
  local strategy="$3"
  local run_id="${strategy}_${symbol}_${domain}"
  local report="$SCRIPT_DIR/reports/${run_id}.json"
  local container="ctrader-exp029-$(printf '%s' "$run_id" | tr '[:upper:]' '[:lower:]' | tr '_' '-')-$$"
  local max_wait="${CTRADER_RUN_MAX_WAIT_SECONDS:-14400}"
  local start
  local cid
  local log_pid=""

  rm -f "$report"
  echo "Running $run_id"
  cid=$(docker run --rm -d \
    --name "$container" \
    --platform "$PLATFORM" \
    --mount "type=bind,src=$ROOT_DIR,dst=/workspace" \
    --mount "type=bind,src=$PWD_FILE_HOST,dst=/secrets/ctrader-cli.pwd,readonly" \
    "$IMAGE" backtest /workspace/bin/Debug/net6.0/Xen.algo \
      --start="02/01/2023 00:00" \
      --end="${backtest_end[$symbol]}" \
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
      --Mode=0 \
      --Strategy="$(strategy_value "$strategy")" \
      --AnalysisEndUtc="${analysis_end[$symbol]}" \
      --StrategyOutputDirectory=/workspace/data/strategy_runs \
      --DomainMinutes="$(domain_minutes "$domain")" \
      --StrictCoverage="$(strict_coverage "$domain")" \
      --MinCoverage="$(min_coverage "$domain")" \
      --FastMa=20 \
      --SlowMa=50)

  docker logs -f "$cid" | sed -u "s/^/[$run_id] /" &
  log_pid=$!
  start=$(date +%s)

  while docker ps -q --filter "id=$cid" | grep -q .; do
    if run_complete "$strategy" "$symbol" "$domain" "$report"; then
      sleep 2
      docker stop "$cid" >/dev/null || true
      break
    fi
    if (( $(date +%s) - start > max_wait )); then
      docker logs --tail 80 "$cid" >&2 || true
      docker stop "$cid" >/dev/null || true
      echo "Timed out waiting for $run_id after ${max_wait}s" >&2
      return 1
    fi
    sleep 5
  done

  if [[ -n "$log_pid" ]]; then
    wait "$log_pid" 2>/dev/null || true
  fi
  if ! run_complete "$strategy" "$symbol" "$domain" "$report"; then
    echo "$run_id did not produce complete strategy-run artifacts." >&2
    return 1
  fi
  echo "Completed $run_id -> $(latest_run_dir "$strategy" "$symbol" "$domain")"
}

run_symbol_worker() {
  local symbol="$1"
  for domain in "${domains[@]}"; do
    for strategy in "${strategies[@]}"; do
      run_backtest "$symbol" "$domain" "$strategy"
    done
  done
}

if [[ "${1:-}" == "cache-layout" ]]; then
  prepare_cache_layout
  print_cache_layout
  exit 0
fi

if [[ "${1:-}" == "one" ]]; then
  if [[ $# -ne 4 ]]; then
    echo "Usage: $0 one <SYMBOL> <DOMAIN:5m|1h|4h> <STRATEGY:AvwapBaseline>" >&2
    exit 2
  fi
  symbols=("$2")
  domains=("$3")
  strategies=("$4")
fi

if [[ "${1:-}" == "parallel" ]]; then
  prepare_cache_layout
  pids=()
  status=0
  for symbol in "${symbols[@]}"; do
    run_symbol_worker "$symbol" &
    pids+=("$!")
  done
  for pid in "${pids[@]}"; do
    if ! wait "$pid"; then
      status=1
    fi
  done
  if [[ "$status" -eq 0 ]]; then
    echo "Done. Strategy-host outputs should be under $ROOT_DIR/data/strategy_runs"
  fi
  exit "$status"
fi

prepare_cache_layout
for symbol in "${symbols[@]}"; do
  run_symbol_worker "$symbol"
done

echo "Done. Strategy-host outputs should be under $ROOT_DIR/data/strategy_runs"
