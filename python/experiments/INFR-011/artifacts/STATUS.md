# INFR-011 Phase A Execution Status

**Current (2026-07-16): PHASE A COMPLETE — verify block PASS.** A5 PASS_WITH_EXCLUSIONS (894 ADMITTED + 9 SPEC_INCOMPLETE, 672.14M bars), A6 fence PINNED (sha `35d3375e…`), A4 catalog ingested + reconciled (903 instruments, bar counts match ledger 903/903, BTC/ETH TRAIN hourly-return corr 0.858, HOLDOUT reads refused). Day-hole repair COMPLETED via EC2 emit run (see close-out). Phase D unblocked.

## Spot reclaim + recovery (2026-07-15)
- **Event:** original spot instance `i-0c7468d5a90738f34` (m7g.4xlarge) was reclaimed at ~2026-07-15T18:57Z. Pass-1 had in fact completed cleanly (`RUN_COMPLETE.pass1`: exit_code=0 at 18:55:50Z, 798 parquets); the reclaim hit just as the retry-watcher relaunched the retry pass. Data survived on the persistent root volume `vol-070e63f9c46704118` (250 GB gp3, us-east-1d): 798 parquets + manifests (799 ok / 110 error / 1 no_bars of 910).
- **Recovery instance:** `i-0971a502c3d4db92b` — m7g.2xlarge **spot** (one-time, terminate on interrupt), us-east-1d, same AMI `ami-02e447f4c654c7179`, key `xena-run`, SG `xena-ssh`. New 30 GB root (DeleteOnTermination=**true**). Public IP `3.85.80.242`.
- **Volume attach:** `vol-070e63f9c46704118` attached at `/dev/sdf` (DeleteOnTermination=**false** — safe on new-instance termination), mounted `-o nouuid` at `/mnt/oldroot` (fstab entry with `nofail`), with `/data → /mnt/oldroot/data` symlink so all hardcoded `/data/infr011` paths + venv work unchanged (plus `~/.local/share/uv` symlink for the venv's uv-managed python).
- **Relaunch:** `nohup /data/infr011/remote_run.sh` restarted 2026-07-15T19:05:40Z; manifest resume confirmed — `102 todo / 910 selected (808 already complete)`, procs=10 workers=3 (env.sh), **0 HTTP 403s** since restart (vs the 96-connection 403 storm). `retry_after_complete.sh` watcher is NOT running on the new instance (moot: this single combined pass covers stragglers + error retries).
- **Completion path unchanged:** pipeline finishes → `parquet-checksums.sha256` + `RUN_COMPLETE` → 12 h grace → `shutdown -h now`, which **terminates only the new instance** (spot one-time); `vol-070e63f9c46704118` persists (attached with DeleteOnTermination=false).
- Mirror loop restarted locally against `3.85.80.242` (`pull_results.sh 3.85.80.242 --loop`); first sync verified 19:07Z. Post-completion pull: `pull_results.sh 3.85.80.242 --bars` (remote paths resolve through the `/data` symlink — verified).
- Note: old instance's watcher renamed pass-1 marker to `RUN_COMPLETE.pass1`; final marker of the combined pass is `RUN_COMPLETE`.

## AWS bulk run (launched 2026-07-15T00:12:30Z; superseded by recovery above — original instance reclaimed)
- Instance: `i-0c7468d5a90738f34` — m7g.4xlarge **spot**, us-east-1d, AMI al2023 arm64 (`ami-02e447f4c654c7179`)
- Access: `ssh -i ~/.ssh/xena-run.pem ec2-user@54.224.112.249` (key pair `xena-run`, SG `xena-ssh` sg-045e97c7969392f65, XENA-era conventions reused)
- Run: `remote_run.sh` detached via nohup; `stream_pipeline.py --procs 10 --workers 3` (≤30 HTTP conns), commit `404d1d2` recorded per-symbol with `produced_on`; determinism pinned (POLARS_MAX_THREADS=1 + maintain_order)
- **S3 deviation:** `xeno-admin` is denied `s3:CreateBucket`/IAM — no bucket possible from CLI. Substitute: root EBS 250 GB gp3 with `DeleteOnTermination=false` (data survives spot interruption/termination) + local rsync mirror loop (`scripts/aws/pull_results.sh <ip> --loop`, running, → `data/remote-mirror/`). `remote_run.sh` auto-enables S3 sync if the operator creates a bucket (console) and sets `XEN_S3_BUCKET`.
- Completion: instance writes `artifacts/RUN_COMPLETE` + `parquet-checksums.sha256`, then self-terminates after a 12 h retrieval grace period (spot shutdown ⇒ terminate; root volume persists).
- Commands:
  - Progress: `ssh -i ~/.ssh/xena-run.pem ec2-user@3.85.80.242 'tail -5 /data/infr011/x/INFR-011/artifacts/bulk-run.log'`
  - Done check: `ssh ... 'cat /data/infr011/x/INFR-011/artifacts/RUN_COMPLETE'`
  - Download all results: `python/experiments/INFR-011/scripts/aws/pull_results.sh 3.85.80.242 --bars` (→ `data/remote-mirror/`, verify with `parquet-checksums.sha256`; merge into `data/staging/bars/` after checksum verify — do NOT overwrite the 10 local-authoritative parquets)
  - Teardown (revised, ONLY after bars pulled + checksums verified locally):
    1. `aws ec2 terminate-instances --region us-east-1 --instance-ids i-0971a502c3d4db92b` — its 30 GB root `vol-063cb26f6a738f108` auto-deletes (DeleteOnTermination=true); the run also self-terminates 12 h after RUN_COMPLETE
    2. wait for the data volume to detach: `aws ec2 wait volume-available --region us-east-1 --volume-ids vol-070e63f9c46704118`
    3. delete the persistent data volume (this IS the reclaimed original instance's root — the only surviving volume): `aws ec2 delete-volume --region us-east-1 --volume-id vol-070e63f9c46704118`
    4. verify nothing left: `aws ec2 describe-volumes --region us-east-1 --filters Name=tag:Project,Values=INFR-011 --query 'Volumes[].VolumeId' --output text` → empty
- Est. cost: ~$2 compute (spot $0.269/h × ~6 h) + <$1 EBS + ~$4–6 egress on pull ≈ **$7–9 total**

## Constraints (binding)
- 910 symbols, *USDT only
- Trailing 4y cap
- ZERO permanent raw (incl. BTC/ETH/SOL — keep-forever deferred)
- Peak raw = one day-file in flight
- Delist reconciliation done (blocks A5 if incomplete — currently complete)
- Step 4 blocked on Phase B Nautilus pin

## Steps
1. Census → **DONE** (910)
2+3. Streaming pipeline → **RUNNING on EC2** (see AWS section above; 10 symbols complete locally)
4. Catalog ingest → **blocked** (Phase B)
5. Admission → pending full invariants after bulk
6. Fence → pending

## Resume
```bash
cd python && uv run python experiments/INFR-011/scripts/stream_pipeline.py --workers 12
```
Skips symbols already in `symbol-status.jsonl` with status=ok; day-level resume via `checksum-manifest.jsonl` when parquet exists.

Artifacts: checksum-manifest.jsonl, symbol-status.jsonl, gap-ledger.jsonl, delist-reconciliation.*, data/staging/bars/*.parquet

## Final collection state (2026-07-16, operator-signed)

- **895/910 symbols collected** (894 EC2 + SOLUSDT local), 24 GB parquet, sha256 894/894 verified locally at `data/remote-mirror/bars/`.
- **OMITTED (operator decision 2026-07-16, non-detrimental):** 14 symbols failed both EC2 passes with HTTP 403 (CDN block, K-cluster + others): KAITOUSDT KASUSDT KAVAUSDT KDAUSDT KLACUSDT KLAYUSDT KMNOUSDT KNCUSDT KOMAUSDT MYRIAUSDT SFPUSDT TACUSDT TRIAUSDT UNIUSDT. Operator rationale: none pass the intended instrument-universe selection rules (e.g. 24h traded volume), so omission is equivalent to selection-rule exclusion. Retryable later from any IP if ever needed (archives persist at Bybit).
- **DATAOLD01USDT:** `no_bars` — dead placeholder archive, legitimately empty.
- A5 admission gate must carry these 15 as explicit `OMITTED_OPERATOR` / `NO_BARS` rows (not silent absence).
- AWS teardown complete 2026-07-16: i-0971a502c3d4db92b terminated, vol-070e63f9c46704118 deleted, no Project=INFR-011 volumes remain.

## Phase A close-out (2026-07-16)

### Collection-hole discovery + partial repair
- Post-collection audit found the EC2 run left **23,450 day-files as HTTP-403 `error`
  across 740 symbols** while marking the symbols `ok` (day-level failures were never
  retried; gaps were exact whole-day midnight-aligned blocks, e.g. BTCUSDT missing 13
  multi-day windows). 403s were transient CDN/IP blocks — files download fine locally.
- Operator approved a full local repair (`scripts/patch_missing_days.py`), then **stopped
  it mid-flight** (bandwidth budget: >120 GB already spent on this INFR). Fully patched
  before the stop: BTCUSDT, ANCUSDT, LPTUSDT, MASKUSDT, MANAUSDT, LUNA2USDT (+BTC now
  hole-free). Remaining ~21k missing days stay as explicit **COLLECTION_GAP** minutes in
  the admission ledger (no-trade vs collection vs outage split per symbol).
- 9 "K-cluster" symbols (KAITO/KAS/KAVA/KDA/KLAC/KLAY/KMNO/KNC/KOMA) turned out to have
  complete verified data — the 'failed both passes' premise was a duplicate worker's .tmp
  rename error row. **Operator admitted them** (2026-07-16), shrinking OMITTED_OPERATOR
  to 5: MYRIA SFP TAC TRIA UNI.

### A5 admission (COMPLETE)
- `admission-report.md`: **PASS_WITH_EXCLUSIONS**. Census 910 = 893 ADMITTED +
  10 SPEC_INCOMPLETE (return-level only) + 5 OMITTED_OPERATOR + 1 NO_BARS +
  1 FAIL_CORRUPT (KASUSDT — parquet corrupt at source, checksum matches EC2 manifest;
  operator declined re-download).
- 645,074,830 bars total. Delist tails all intact (vs last *traded* archive day —
  archives carry empty trailing day-files after halts, e.g. LUNA 2022-05-12).
- Specs: 612 API + 281 SPEC_INFERRED (tick from price grid, lot from volume-GCD,
  confidence ≥0.995) in `instrument-specs.json`.

### A6 fence (PINNED)
- `fence-manifest.json` sha256 `35d3375ec5ec18b3c6e4c5eec814ade4d492bd60e3fb694fed19e16bc2c00448`:
  analysis_start 2021-06-29T06:53Z | train_end 2023-12-18 | holdout_start 2025-01-08 |
  data_end 2026-07-14T23:59Z (nested 70/30, floored to UTC days).
- Wrapper `xen.nautilus.catalog_fence`: `fenced_bar_query` (TRAIN/TEST bands only,
  HOLDOUT refused unconditionally), `fence_attestation_payload` (status=PINNED +
  manifest_sha256 — satisfies estimand gate v2). code-conventions.md placeholder
  replaced (all 9 skill-dir copies synced).

### A4 catalog ingest (running 2026-07-16)
- `fence_and_catalog.py ingest`: 903 readable symbols → `data/catalog/`
  ParquetDataCatalog, nautilus_trader==1.230.0, CryptoPerpetual + 1m Bars,
  `{sym}-LINEAR.BYBIT`, ts_event=CloseTime, engine costless (fees 0 — costs
  analyst-injected). Resume manifest: `catalog-ingest.jsonl`.
- Pseudo-quote spread columns stay in the per-symbol bar parquets (retained as the
  T1 spread source; not Nautilus Bar fields).

### Repair completion via EC2 (2026-07-16, supersedes "stopped mid-flight" above)
- Operator redirected the download to EC2 (local bandwidth budget): `patch_missing_days.py`
  gained an **emit-only mode** (`--days-file --patch-dir`) writing per-symbol patch parquets
  of ONLY the missing days' bars; local merge via `--from-patch-dir`.
- Run history: spot m7g.2xlarge reclaimed after 43 min (44 symbols pulled via incremental
  rsync loop survived); relaunched **on-demand m7g.4xlarge** (`XEN_ONDEMAND=1`) — 698
  symbols / 16,671 days in **13 min**, exit 0. Local pull 1.2 GB (vs ~140 GB local
  download), checksums 694/694 OK. All instances terminated, volumes auto-deleted.
- Merge result: **+27.06M bars** (645.07M → 672.14M); ADMITTED 893→894, SPEC_INCOMPLETE
  10→9. Remaining truly-missing: **1,205 days (~0.26%)** — 268 CDN-blocked from both EC2
  IPs + range-edge days; carried as explicit COLLECTION_GAP minutes (grounded against the
  parquets themselves — a manifest 'error' day whose minutes exist in data counts resolved).
- Catalog: 733 changed symbols purged + re-ingested (`catalog-ingest.jsonl` reconciled).
- Fence re-pinned same dates (analysis_start 2021-06-29T06:53Z / train_end 2023-12-18 /
  holdout_start 2025-01-08 / data_end 2026-07-14T23:59Z), new file sha
  `35d3375ec5ec18b3c6e4c5eec814ade4d492bd60e3fb694fed19e16bc2c00448`.

### Phase A verify block (2026-07-16) — PASS
- Census 910 presented ✓; admission PASS_WITH_EXCLUSIONS with explicit non-admitted rows ✓
- V1 catalog↔ledger bar counts: 903/903 match ✓
- V2 instruments: 903/903 present ✓
- V3 cross-symbol sanity: BTC/ETH TRAIN hourly log-return corr **0.858** ✓
- V4 fence: HOLDOUT read refused by wrapper ✓; TRAIN/TEST band bounds enforced ✓
- Storage: catalog 23 GB; INFR-011 bar parquets ~25 GB retained (spread source); zero raw ✓
- Total cost of EC2 repair: ≈ $1 (13 min on-demand m7g.4xlarge + spot attempts + egress)
