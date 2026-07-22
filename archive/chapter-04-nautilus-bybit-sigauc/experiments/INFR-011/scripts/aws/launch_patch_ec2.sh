#!/usr/bin/env bash
# INFR-011 day-hole patch run on EC2 (2026-07-16). Downloads the 22,694 missing
# day-files on INSTANCE internet (inbound free) and emits ONLY the new bars as
# per-symbol patch parquets (~1 GB total to pull). Reuses INFR-011 conventions:
# us-east-1, key xena-run, SG xena-ssh, al2023 arm64 AMI.
#
# Root volume DeleteOnTermination=TRUE (patch output is small + rerun-cheap;
# no persistent volume to clean up this time). Self-terminates after grace.
set -euo pipefail

REGION=us-east-1
AMI=ami-02e447f4c654c7179            # al2023 arm64 (same as bulk run)
ITYPE="${XEN_ITYPE:-m7g.2xlarge}"    # 8 vCPU — download-bound, ~1h
KEY=xena-run
PEM="$HOME/.ssh/xena-run.pem"
SG=sg-045e97c7969392f65              # xena-ssh
NAME=xen-infr011-patch
VOL_GB=30

HERE="$(cd "$(dirname "$0")" && pwd)"
EXP="$(cd "$HERE/../.." && pwd)"
REPO="$(cd "$EXP/../../.." && pwd)"
COMMIT=$(git -C "$REPO" rev-parse HEAD)

echo "== launching $ITYPE (spot first unless XEN_ONDEMAND=1) in $REGION =="
set +e
IID=""
if [ -z "${XEN_ONDEMAND:-}" ]; then
IID=$(aws ec2 run-instances --region $REGION \
  --image-id $AMI --instance-type "$ITYPE" \
  --key-name $KEY --security-group-ids $SG \
  --instance-market-options 'MarketType=spot,SpotOptions={SpotInstanceType=one-time,InstanceInterruptionBehavior=terminate}' \
  --block-device-mappings "[{\"DeviceName\":\"/dev/xvda\",\"Ebs\":{\"VolumeSize\":$VOL_GB,\"VolumeType\":\"gp3\",\"DeleteOnTermination\":true}}]" \
  --tag-specifications "ResourceType=instance,Tags=[{Key=Name,Value=$NAME},{Key=Project,Value=INFR-011}]" \
  --query 'Instances[0].InstanceId' --output text 2>/tmp/xen-patch-launch-err)
fi
if [ -z "${IID:-}" ] || [ "$IID" = "None" ]; then
  echo "spot failed ($(head -2 /tmp/xen-patch-launch-err)); falling back to on-demand"
  IID=$(aws ec2 run-instances --region $REGION \
    --image-id $AMI --instance-type "$ITYPE" \
    --key-name $KEY --security-group-ids $SG \
    --instance-initiated-shutdown-behavior terminate \
    --block-device-mappings "[{\"DeviceName\":\"/dev/xvda\",\"Ebs\":{\"VolumeSize\":$VOL_GB,\"VolumeType\":\"gp3\",\"DeleteOnTermination\":true}}]" \
    --tag-specifications "ResourceType=instance,Tags=[{Key=Name,Value=$NAME},{Key=Project,Value=INFR-011}]" \
    --query 'Instances[0].InstanceId' --output text)
fi
set -e
echo "instance: $IID"

aws ec2 wait instance-running --region $REGION --instance-ids "$IID"
IP=$(aws ec2 describe-instances --region $REGION --instance-ids "$IID" \
  --query 'Reservations[0].Instances[0].PublicIpAddress' --output text)
echo "public ip: $IP"

SSH="ssh -i $PEM -o StrictHostKeyChecking=accept-new -o ConnectTimeout=10 ec2-user@$IP"
echo "== waiting for SSH =="
for i in $(seq 1 40); do $SSH true 2>/dev/null && break; sleep 10; done

echo "== bootstrap (deps + venv) =="
$SSH 'sudo mkdir -p /data/infr011 && sudo chown ec2-user:ec2-user /data/infr011 && sudo dnf -q install -y rsync >/dev/null && curl -LsSf https://astral.sh/uv/install.sh | sh >/dev/null && ~/.local/bin/uv venv --python 3.13.1 /data/infr011/venv -q && ~/.local/bin/uv pip install --python /data/infr011/venv/bin/python -q polars==1.41.2 tqdm==4.68.4'

echo "== ship code + days file =="
$SSH 'mkdir -p /data/infr011/x/INFR-011/scripts /data/infr011/x/INFR-011/artifacts /data/infr011/x/INFR-011/data/patch'
scp -i "$PEM" -q \
  "$EXP/scripts/stream_pipeline.py" \
  "$EXP/scripts/patch_missing_days.py" \
  ec2-user@$IP:/data/infr011/x/INFR-011/scripts/
DAYS_FILE="${XEN_DAYS_FILE:-patch-days.json}"
scp -i "$PEM" -q "$EXP/artifacts/$DAYS_FILE" ec2-user@$IP:/data/infr011/x/INFR-011/artifacts/patch-days.json

echo "== start detached run =="
$SSH "cat > /data/infr011/patch_run.sh" <<'REMOTE'
#!/usr/bin/env bash
set -uo pipefail
ROOT=/data/infr011
EXP="$ROOT/x/INFR-011"
ART="$EXP/artifacts"
PATCH="$EXP/data/patch"
LOG="$ART/patch-run.log"
GRACE_HOURS="${XEN_GRACE_HOURS:-6}"
echo "[patch_run] start $(date -u +%FT%TZ)" >> "$LOG"
"$ROOT/venv/bin/python" "$EXP/scripts/patch_missing_days.py" \
  --days-file "$ART/patch-days.json" --patch-dir "$PATCH" \
  --procs "${XEN_PROCS:-10}" --workers "${XEN_WORKERS:-3}" >> "$LOG" 2>&1
RC=$?
echo "[patch_run] exit_code=$RC $(date -u +%FT%TZ)" >> "$LOG"
( cd "$PATCH" && sha256sum ./*.parquet > "$ART/patch-checksums.sha256" ) 2>> "$LOG"
{
  echo "completed_utc=$(date -u +%FT%TZ)"
  echo "exit_code=$RC"
  echo "n_parquet=$(ls "$PATCH" | grep -c '\.parquet$')"
  du -sh "$PATCH"
} > "$ART/PATCH_COMPLETE"
echo "[patch_run] PATCH_COMPLETE; shutdown in ${GRACE_HOURS}h" >> "$LOG"
sleep $(( GRACE_HOURS * 3600 ))
sudo shutdown -h now
REMOTE
$SSH 'chmod +x /data/infr011/patch_run.sh && nohup /data/infr011/patch_run.sh > /data/infr011/nohup.out 2>&1 < /dev/null & echo started pid=$!'

echo
echo "DONE. instance=$IID ip=$IP type=$ITYPE"
echo "progress:  ssh -i $PEM ec2-user@$IP 'tail -3 /data/infr011/x/INFR-011/artifacts/patch-run.log'"
echo "done chk:  ssh -i $PEM ec2-user@$IP 'cat /data/infr011/x/INFR-011/artifacts/PATCH_COMPLETE'"
echo "pull:      rsync -az -e 'ssh -i $PEM' ec2-user@$IP:/data/infr011/x/INFR-011/data/patch/ <local-patch-dir>/"
echo "terminate: aws ec2 terminate-instances --region $REGION --instance-ids $IID  (root vol auto-deletes)"
