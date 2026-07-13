# XENA Run Ledger (INFR-006, item 5)

Live operational ledger for XENA portfolio runs — the portfolio-lane analogue of the
multiplicity registry + test-read ledger. **Append-only rows; never reset across
chapters.** One row per XENA run; gate spends also live in the per-universe
`xena_gate_ledger.json` (this table summarises them for cross-run accounting).

Rules (spec: `docs/references/xena-lane.md`):
- A run registers here at design time (before search) with its universe manifest +
  frozen-registry hash — registration-before-search, mirroring candidate registration.
- `eval_count` / `distinct_subsets` (§10.4) are mandatory at close: **no reported result
  without its evaluation counts.**
- Gate slots: cap 2/universe; second slot = materially different subset or new TEST data
  (operator attestation, recorded in the universe gate ledger verbatim).
- Universe status transitions (CERTIFIED/RETIRED) are operator-signed, checkpoint-level.

**Committed, pending design-time registration (checkpoint 011, CF-MTFCTX-001,
2026-07-10):** XENA-001 (MTFCTX-C1, CTRL-01 RANDOM) · XENA-002 (MTFCTX-C2, CTRL-02
MOMENTUM) · XENA-003 (MTFCTX-C3, CTRL-03 REVERSION) — 2,736 candidates each; rows land
here at each run's design completion (band pin required first).

| Run | Registered | Universe (N cands) | Registry sha256 (8) | Search band | Eval count | Distinct subsets | Certified | Gate slots spent | Outcome | Operator sign |
|---|---|---|---|---|---|---|---|---|---|---|
| XENA-001 | 2026-07-10 | MTFCTX-C1 CTRL-01 RANDOM (2,736) | 537d691a | 2021-06-02T00:01Z → 2023-03-08T00:00Z (ranking →2024-03-28; gate →2024-12-11T08:19Z) | **255,142** (search) + 2,190 (certify) | **255,142** | **4 / 12 finalists** | **0/2** | **MACHINERY-ALARM** (operator verdict 2026-07-13). Random-entry control certified 33% of finalists vs 0.75% WS-6 null finalist rate. Root cause PROVEN: `F_floor` 0.4302 is an absolute threshold on an *extensive* statistic, calibrated at 24 cands/400 budget (null F̂ median 0.19); at live scale (2,736 cands / budget 21,835) 12/12 finalists clear it 8.3–13.1× → plateau screen (passes 50.8% of pure noise) is the sole criterion. Evidence substantively noise-consistent (fold medians +0.100/+0.043/−0.098/−0.286; pbo_like 0.25). Battery v2: live median F̂ 4.27 vs permuted 5.94 → **no-structure bias −1.67** (live at 0th pctile). Emission layer clean (candidate gate 2,736/2,736; estimand 2,736/2,736; fence + provenance PASS). **No counted TEST read; TEST band never opened.** | pending (checkpoint-011) |
| XENA-002 | 2026-07-11 | MTFCTX-C2 CTRL-02 MOMENTUM (2,736) | 537d691a | 2021-06-02T00:01Z → 2023-03-08T00:00Z (ranking →2024-03-28; gate →2024-12-11T08:19Z) | **397,475** (search) + 1,851 (certify) | **397,475** | **7 / 12 finalists** (uninformative — F_floor defect above) | **0/2** | **NO DETECTABLE STRUCTURE** (operator verdict 2026-07-13). Live median F̂ 4.79 vs permuted 6.20 (0th pctile; delta **−1.41**); netted against XENA-001's −1.67 no-structure bias → **+0.26 above the random control, well inside restart dispersion 2.90**. pbo_like 0.50 (worse than the control's 0.25). One genuine difference: all 7 certified finalists have positive fold medians (+0.063…+0.246) — does not survive the battery comparison. Filter structure: V00 1.18× (no preference for filtered variants). Estimand 2,773/2,773 PASS. **Negative evidence for the CF-MTFCTX-001 arc.** **No counted TEST read; TEST band never opened.** | pending (checkpoint-011) |
| XENA-003 | 2026-07-11 | MTFCTX-C3 CTRL-03 REVERSION, native limit orders + m1 fills (2,736) | 537d691a | 2021-06-02T00:01Z → 2023-03-08T00:00Z (ranking →2024-03-28; gate →2024-12-11T08:19Z) | **322,803** (search) + 1,104 (certify) | **322,803** | **12 / 12 finalists** (uninformative — 79.9% of the universe is gross-profitable standalone; restart terminals near-disjoint, Jaccard median 0.108) | **0/2** | **NOT SUPPORTED (magnitude)** (operator verdict 2026-07-13). Gross **+1.958 bps/leg** [1.846, 2.073], n=195,056 — real, block/seed-stable; **breakeven RT spread 0.564–1.146 bps (median 0.705)**; 0/12 finalists survive 1.5 bps (all at F=−32.2 ruin) vs the pre-registered 20–40 bps "nets survive" band. **91.2% of the edge is the limit-print→next-grid-open mark**; registered snap-back mechanism contributes 0.172 bps (8.8%); forward path from the fill bar's open −5.54 bps. Discriminating control (price basis → adjacent grid open, timing/exits/sizing held): F̂ 23 → **0.09–1.93**, below the permuted null ⇒ the live≫permuted gap is the **limit print**, and the permutation battery is **CONFOUNDED** for limit-entry universes. Leak, grid seam, sizing-leverage all RULED OUT. Family thesis contradicted: V00 **4.0× over-represented**; search maximises cadence (1H5M 76%, H05X 53%). Evidence: `python/experiments/XENA-003/analysis.md`. **No counted TEST read; TEST band never opened.** | pending (checkpoint-011) |

## Close-out notes (2026-07-13)

- **All three universes closed with 0/2 gate slots consumed.** Search + certification +
  permutation battery complete on every universe; **no counted TEST read was taken on any of
  them** (`docs/signal-registry/test-read-ledger.md` is unchanged by XENA-001/002/003). The
  global 30% holdout was never loaded.
- **Adjudication-layer defect (blocking for future gate spends).** The frozen-registry v3 pin
  (X=0.70 / F_floor=0.4302 / gate=0.0558) was calibrated on 24-candidate / 400-budget null
  universes. `F_floor` is inoperative at live scale (cleared 8×–57× by 12/12 finalists in all
  three universes) and the gate threshold shares the same lineage, so a GROSS gate pass is
  arithmetically near-guaranteed at live F̂ scale. Framework audit:
  `.ignore/temp/new-referee/post-xena-infr-audit.md` (2026-07-13). **Recommendation on the record:
  no XENA universe should reach a counted gate until this is resolved.** Any change to the pin is
  a new predeclared calibration + new hash-pin (L-23), operator-signed — never a post-hoc tune.
- **Governance near-miss (recorded, not a violation):** design §4 spread pins were never set —
  `universe_manifest.json` carries `cost_bps = 0.0` for ten of twelve instruments in all three
  universes. A gate spend would have produced a binding GROSS pass with a **vacuous NET block**
  (the exact L-22 failure shape). Nothing in the pipeline blocked this; a code-enforced cost-pin
  precondition is proposed to the checkpoint.
- **Platform:** all three adjudicated on c8g.12xlarge (aarch64), Rust `xena_fold` kernel
  (INFR-007/008); one universe = one platform (1-ULP libm caveat). Pinned parity corpus 499/500
  cross-platform (`rand-146`), operator-review flagged; pins not regenerated.
- **Universe status transitions (CERTIFIED/RETIRED) and CF-MTFCTX-001 family status remain
  operator-signed, checkpoint-011.** Nothing in this close-out moves them.
