#!/usr/bin/env bash
# INFR-011 — pull remote run artifacts/bars from the EC2 instance to a local
# mirror (does NOT touch the authoritative local parquets in data/staging/bars).
# Usage:
#   pull_results.sh <instance-ip>            one-shot artifacts-only pull
#   pull_results.sh <instance-ip> --bars     also pull parquet bars (big)
#   pull_results.sh <instance-ip> --loop     artifacts pull every 10 min (nohup-able)
set -euo pipefail
IP="${1:?usage: pull_results.sh <ip> [--bars|--loop]}"
MODE="${2:-}"
PEM="$HOME/.ssh/xena-run.pem"
HERE="$(cd "$(dirname "$0")" && pwd)"
EXP="$(cd "$HERE/../.." && pwd)"
DEST="$EXP/data/remote-mirror"
mkdir -p "$DEST/artifacts" "$DEST/bars"
RS="rsync -az --timeout=60 --partial -e \"ssh -i $PEM -o StrictHostKeyChecking=accept-new\""

pull_art() { eval $RS "ec2-user@$IP:/data/infr011/x/INFR-011/artifacts/" "$DEST/artifacts/"; }
pull_bars() { eval $RS "ec2-user@$IP:/data/infr011/x/INFR-011/data/staging/bars/" "$DEST/bars/"; }

case "$MODE" in
  --loop) while true; do pull_art && date -u +"synced %FT%TZ"; sleep 600; done ;;
  --bars) pull_art; pull_bars ;;
  *) pull_art ;;
esac
