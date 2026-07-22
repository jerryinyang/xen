#!/usr/bin/env bash
# INFR-011 remote bulk run — executed ON the EC2 instance (started detached by
# launch_infr011_ec2.sh via nohup). Streams Bybit day-files → 1m bars parquet.
# ZERO raw retention. Self-terminates after a retrieval grace period.
set -uo pipefail

ROOT=/data/infr011
EXP="$ROOT/x/INFR-011"
ART="$EXP/artifacts"
BARS="$EXP/data/staging/bars"
LOG="$ART/bulk-run.log"
VENVPY="$ROOT/venv/bin/python"
GRACE_HOURS="${XEN_GRACE_HOURS:-12}"

# Provenance env written by the launcher
[ -f "$ROOT/env.sh" ] && source "$ROOT/env.sh"
TOKEN=$(curl -s -X PUT "http://169.254.169.254/latest/api/token" -H "X-aws-ec2-metadata-token-ttl-seconds: 300" || true)
export XEN_INSTANCE_TYPE=$(curl -s -H "X-aws-ec2-metadata-token: $TOKEN" http://169.254.169.254/latest/meta-data/instance-type || echo ec2-unknown)

mkdir -p "$ART" "$BARS"
echo "[remote_run] start $(date -u +%FT%TZ) instance=$XEN_INSTANCE_TYPE commit=${XEN_GIT_COMMIT:-unset}" >> "$LOG"

# Optional S3 sync loop — only active if the operator provides a bucket
# (account IAM currently denies s3:CreateBucket; primary sync is rsync pull).
s3_sync() {
  aws s3 sync "$BARS" "s3://$XEN_S3_BUCKET/bars/" --exclude "*.tmp" --only-show-errors
  aws s3 sync "$ART" "s3://$XEN_S3_BUCKET/artifacts/" --only-show-errors
}
if [ -n "${XEN_S3_BUCKET:-}" ]; then
  ( while true; do sleep 300; s3_sync; done ) &
  SYNC_PID=$!
fi

"$VENVPY" "$EXP/scripts/stream_pipeline.py" --procs "${XEN_PROCS:-10}" --workers "${XEN_WORKERS:-3}" >> "$LOG" 2>&1
RC=$?
echo "[remote_run] pipeline exit_code=$RC $(date -u +%FT%TZ)" >> "$LOG"

# sha256 per parquet
( cd "$BARS" && sha256sum ./*.parquet > "$ART/parquet-checksums.sha256" ) 2>> "$LOG"

# End-of-run marker (rsync-pullable; also to S3 if enabled)
{
  echo "completed_utc=$(date -u +%FT%TZ)"
  echo "exit_code=$RC"
  echo "instance_type=$XEN_INSTANCE_TYPE"
  echo "git_commit=${XEN_GIT_COMMIT:-unset}"
  echo "n_parquet=$(ls "$BARS" | grep -c '\.parquet$')"
} > "$ART/RUN_COMPLETE"
if [ -n "${XEN_S3_BUCKET:-}" ]; then
  s3_sync
  aws s3 cp "$ART/RUN_COMPLETE" "s3://$XEN_S3_BUCKET/RUN_COMPLETE" --only-show-errors
  kill "${SYNC_PID:-0}" 2>/dev/null
fi

# Grace period for retrieval, then self-terminate.
# (one-time spot: OS shutdown == terminate; on-demand fallback launched with
#  --instance-initiated-shutdown-behavior terminate)
echo "[remote_run] RUN_COMPLETE written; shutdown in ${GRACE_HOURS}h" >> "$LOG"
sleep $(( GRACE_HOURS * 3600 ))
sudo shutdown -h now
