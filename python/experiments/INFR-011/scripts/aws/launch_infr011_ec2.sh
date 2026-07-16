#!/usr/bin/env bash
# INFR-011 — provision + launch the bulk Bybit collection on one EC2 spot
# instance (on-demand fallback). Reuses XENA-era conventions: us-east-1,
# key pair xena-run (~/.ssh/xena-run.pem), SG xena-ssh.
#
# Account limits (xeno-admin): no IAM role creation, no s3:CreateBucket →
# no instance profile / SSM; durability via root EBS (DeleteOnTermination=false)
# and rsync-over-SSH pull. If the operator creates a bucket from the console,
# set XEN_S3_BUCKET before launching to enable on-instance S3 sync.
set -euo pipefail

REGION=us-east-1
AMI=ami-02e447f4c654c7179            # al2023-ami-2023.12.20260710.0-kernel-6.1-arm64
ITYPE="${XEN_ITYPE:-m7g.4xlarge}"    # 16 vCPU / 64 GB, Graviton
KEY=xena-run
PEM="$HOME/.ssh/xena-run.pem"
SG=sg-045e97c7969392f65              # xena-ssh (22 from 102.91.0.0/16)
NAME=xen-infr011-bulk
VOL_GB=250

HERE="$(cd "$(dirname "$0")" && pwd)"          # .../INFR-011/scripts/aws
EXP="$(cd "$HERE/../.." && pwd)"               # .../INFR-011
REPO="$(cd "$EXP/../../.." && pwd)"            # repo root
COMMIT=$(git -C "$REPO" rev-parse HEAD)

echo "== launching $ITYPE (spot first) in $REGION =="
set +e
IID=$(aws ec2 run-instances --region $REGION \
  --image-id $AMI --instance-type "$ITYPE" \
  --key-name $KEY --security-group-ids $SG \
  --instance-market-options 'MarketType=spot,SpotOptions={SpotInstanceType=one-time,InstanceInterruptionBehavior=terminate}' \
  --block-device-mappings "[{\"DeviceName\":\"/dev/xvda\",\"Ebs\":{\"VolumeSize\":$VOL_GB,\"VolumeType\":\"gp3\",\"DeleteOnTermination\":false}}]" \
  --tag-specifications "ResourceType=instance,Tags=[{Key=Name,Value=$NAME},{Key=Project,Value=INFR-011}]" "ResourceType=volume,Tags=[{Key=Name,Value=$NAME-data},{Key=Project,Value=INFR-011}]" \
  --query 'Instances[0].InstanceId' --output text 2>/tmp/xen-launch-err)
if [ -z "${IID:-}" ] || [ "$IID" = "None" ]; then
  echo "spot failed ($(cat /tmp/xen-launch-err | head -2)); falling back to on-demand"
  IID=$(aws ec2 run-instances --region $REGION \
    --image-id $AMI --instance-type "$ITYPE" \
    --key-name $KEY --security-group-ids $SG \
    --instance-initiated-shutdown-behavior terminate \
    --block-device-mappings "[{\"DeviceName\":\"/dev/xvda\",\"Ebs\":{\"VolumeSize\":$VOL_GB,\"VolumeType\":\"gp3\",\"DeleteOnTermination\":false}}]" \
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
$SSH 'sudo mkdir -p /data/infr011 && sudo chown ec2-user:ec2-user /data/infr011 && sudo dnf -q install -y rsync tmux >/dev/null && curl -LsSf https://astral.sh/uv/install.sh | sh >/dev/null && ~/.local/bin/uv venv --python 3.13.1 /data/infr011/venv -q && ~/.local/bin/uv pip install --python /data/infr011/venv/bin/python -q polars==1.41.2 tqdm==4.68.4'

echo "== ship code + resume manifests (local-complete symbols will be skipped) =="
$SSH 'mkdir -p /data/infr011/x/INFR-011/scripts /data/infr011/x/INFR-011/artifacts /data/infr011/x/INFR-011/data/staging/bars'
scp -i "$PEM" -q \
  "$EXP/scripts/stream_pipeline.py" \
  ec2-user@$IP:/data/infr011/x/INFR-011/scripts/
scp -i "$PEM" -q \
  "$EXP/artifacts/candidate_symbols.txt" \
  "$EXP/artifacts/symbol-status.jsonl" \
  "$EXP/artifacts/checksum-manifest.jsonl" \
  ec2-user@$IP:/data/infr011/x/INFR-011/artifacts/
scp -i "$PEM" -q "$HERE/remote_run.sh" ec2-user@$IP:/data/infr011/
$SSH "chmod +x /data/infr011/remote_run.sh && printf 'export XEN_GIT_COMMIT=%s\nexport XEN_S3_BUCKET=%s\nexport XEN_PROCS=%s\nexport XEN_WORKERS=%s\n' '$COMMIT' '${XEN_S3_BUCKET:-}' '${XEN_PROCS:-10}' '${XEN_WORKERS:-3}' > /data/infr011/env.sh"

echo "== start detached run =="
$SSH 'nohup /data/infr011/remote_run.sh > /data/infr011/nohup.out 2>&1 < /dev/null & echo started pid=$!'

echo
echo "DONE. instance=$IID ip=$IP type=$ITYPE"
echo "progress:  ssh -i $PEM ec2-user@$IP 'tail -5 /data/infr011/x/INFR-011/artifacts/bulk-run.log'"
