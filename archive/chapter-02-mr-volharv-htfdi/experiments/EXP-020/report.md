# EXP-020 — CF-VOLHARV-001/HYP-002: structure-borne oscillation harvest (rebalance + grid)

**Status:** COMPLETED 2026-07-05 — **NOT SUPPORTED (operator verdict), USDCAD flagged exception.**
**Family:** CF-VOLHARV-001. **Checkpoint:** `2026-07-05-008-cf-volharv-001-structure-harvest`.
**Reads:** 0 slots, 0 counted TEST reads, TRAIN only, holdout sealed.
Artifacts: [design](design.md) · [qa-review](qa-review.md) · [analysis](analysis.md) ·
[code](code/) · [analysis_code](analysis_code/) · [results](results/) · [plots](plots/).

---

## 1. Question + mechanism

Does a rebalancing/crossing structure convert the measured FX-block oscillation (EXP-019:
VR 0.76–0.92 at H=6–48) into positive **net** expectation at capped inventory — where EXP-019
proved the unconditioned fixed-hold object cannot (E[gross]=0)? Two arms, both two-sided, no
directional forecast:

- **ARM R** — banded 50/50 constant-mix rebalance (volatility pumping) vs a never-rebalanced
  same-mix B&H twin. Estimand: per-bar Δ net log return (the classical rebalancing premium).
- **ARM G** — symmetric monthly-anchored grid (MR: limits toward anchor) vs a direction-
  inverted momentum grid twin. Estimand: per-round-trip net bps + month-episode net incl.
  censored-inventory MTM.

Discriminating prediction: premium > costs possible only on the MR block (NZDUSD, AUDUSD,
GBPUSD, USDCAD); on VR≈1 RW instruments the same structure must earn ≈ −costs. A positive
RW-block cell = artifact alarm.

## 2. Scope

16 instruments (universe minus DE30), 4h decisions (ARM G fills m1, native pending orders);
TRAIN only, EXP-019 per-instrument fences. 64 runs (R/R-twin/G/G-invert × 16) + 4 delay twins
(NZDUSD/USDCAD × both arms) = **68 cells**. All structure parameters candidate-blind from
EXP-019 (`code/derive_exp020_params.py`, amendment A1; byte-reproducible — tripwire 2).
Cost framing: engine fills are gross (bid=ask); reads at gross / gross-minus-commission /
weekend-ceiling stress. **Net-at-live-spread BLOCKED** (live-session spread pin outstanding;
EURJPY spread unpinned even at ceiling).

## 3. Integrity gate — OPEN (all blocking checks pass)

| Check | Result |
|---|---|
| Estimand validation, 68/68 cells | **PASS** (0 failing; `results/estimand_validation_*.json`) |
| ARM R causal provenance (decisions ≤ t−1) | **PASS** — 0 trigger violations / 2,119 trade-bars; fill = next open 99.95%; weight restored 100% |
| ARM G m1 fill causality (tripwire 3) | **PASS** — 1,900 fills, 2 benign USDCAD anomalies ≤3.8 bps (session-gap fills), disclosed |
| Tripwire 1 (+1-bar delay, both arms, NZDUSD/USDCAD) | **PASS (graceful)** — RT/premium object ratios 1.01–1.06; totals move within fill-count noise → no fill-seam edge, no seam inflation |
| Plant (+2 bps/rebalance, analysis-side) detected before real read | **PASS** — expected +0.2221, observed +0.2221 (NZDUSD); premium read sensitive at scale |
| Holdout untouched / price-primary / no local accounting | **PASS** all cells |

## 4. Key evidence (per stratum; pooled disclosure-only, L-03)

### ARM R — rebalancing premium vs never-rebalanced twin (block bootstrap, block=60)

| Sym | Blk | gross bps/bar [95% CI] | MDE | theory | Read |
|---|---|---|---|---|---|
| NZDUSD | MR | +0.0048 [−0.019,+0.029] | 0.024 | 0.0077 | UNPOWERED |
| AUDUSD | MR | +0.0055 [−0.014,+0.025] | 0.019 | 0.0074 | UNPOWERED |
| GBPUSD | MR | +0.0064 [−0.009,+0.022] | 0.016 | 0.0041 | UNPOWERED |
| USDCAD | MR | +0.0029 [−0.0017,+0.0073] | 0.0045 | 0.0027 | UNPOWERED |
| US2000 | mid | **+0.0455 [+0.0121,+0.0767]** | 0.033 | 0.034 | CI-positive (disclosure) |

All 4 MR cells positive with the right sign but **MDE > effect ⇒ UNPOWERED, not absence.**
Design §8 over-stated the classical `w(1−w)σ²` premium ~100×: the true scale is ~0.04–0.07%/yr
— real-looking but economically negligible. Costs never material for ARM R (drag ≤4e-4 bps/bar).
MR-vs-RW contrast unresolvable at this power. Only US2000 (mid, disclosure) is CI-positive.

### ARM G — MR grid vs momentum-grid twin (drift-robust twin spread, gross incl. censored MTM)

Realized round-trip mean = **+g in every cell** (mechanism real, artifact check PASS) but
fills are **rare**. MR-block twin-spread scoreboard = **1/4 positive**:

| Sym | Blk | twin spread /mo [CI] | Robustness |
|---|---|---|---|
| **USDCAD** | MR | **+132 [+43,+257]** | survives commission, weekend ×4 stress, top-3 removal, both halves — **BUT** momentum twin +3,491 (sign-flip prediction FAILS) and 2022 = 67% of funding (>60% cleanliness fail) |
| NZDUSD | MR | −56 | negative |
| GBPUSD | MR | +12 (sign-flips on top-3 removal) | wash |
| AUDUSD | MR | −104 | momentum twin BEATS the MR grid |
| USDCHF | RW | CI-negative | (control) |
| BTCUSD | RW | level-read drift-contaminated; only twin-spread robust | (control) |

The MR block does not act as a block; the inverted-twin sign-flip prediction fails everywhere
(including USDCAD); MR-vs-RW does not separate.

### Artifact alarms (why it mostly did not monetise — structure failure)

1. **Cadence collapse** — fills at 5–28% of A1-implied crossings; 3/4 MR cells cap-locked at
   the 8-leg cap most of the band; **NZDUSD traded nothing after 2022-04** (cap-lock + stale
   monthly anchor). The "oscillation harvester" is in fact ~98–100% in-market, largely frozen.
2. **Censored-inventory dominance** — the ≤8 open legs at the fence erase 100–155% of realized
   harvest on NZDUSD/AUDUSD; the month-net object is mostly an inventory-MTM object, not a
   harvest object (VAL-006 survivorship discipline).
3. **Drift contamination** — BTCUSD RW level reads +78k(MR)/+69k(momentum); only the twin
   spread is drift-robust.

### Re-run under hardened `block_bootstrap_ci` (INFR-004/L-20 seed battery + F1 sparse fix)

Verdict unchanged. Integrity re-ran identical (68/68, plant detected). Two borderline
temporal-half flips, both verdict-immaterial: USDCAD half-1 → CI-positive (strengthens USDCAD,
now positive in both halves); US2000 half-2 → straddles 0 (weakens US2000's robustness to
one-sided, consistent with 89%-in-2021/22 attribution). All load-bearing cells stable; seed
ranges ±~0.01 of the bound (see `analysis.md` §9 addendum).

## 5. Verdict

**Analyst recommendation and operator verdict agree: NOT SUPPORTED, USDCAD flagged exception.**

> **Operator verdict (2026-07-05): NOT SUPPORTED.** The MR block does not act as a block, the
> inverted-twin sign-flip prediction fails everywhere (including USDCAD), MR-vs-RW does not
> separate, and ARM R is structurally UNPOWERED. This is largely a **structure failure**
> (cap-lock / cadence collapse to 5–28% of implied crossings), **not clean substrate absence**
> — under UNPOWERED discipline it does **not** license "no oscillation harvest exists." The
> only survivors (USDCAD, US2000-disclosure) are single-stratum, attribution-flagged, and
> cost-unpinned.

Family disposition (retire / iterate structure to fix cap-lock+cadence / next-hypothesis) is
reserved for the **checkpoint-008 retrospective, operator-signed** — not booked by this
experiment.

## 6. Follow-up candidates (separate experiments, not scoped here)

- Structure iteration to break cap-lock/cadence collapse (dynamic anchor / larger cap / spacing
  re-derivation) — would re-open HYP-002, not amend EXP-020.
- USDCAD anchor-luck probe (is +132/mo a monthly-anchor placement artifact?).
- US2000 cross-arm anomaly (ARM R CI-positive + ARM G positive on a mid-block instrument).
- **Prerequisite for any net/deployable read: live-session FTMO spread pin** (carried blocker).

## 7. Registry disposition (evidence only — no status transition)

Evidence row appended to `docs/signal-registry/candidate-families/cf-volharv-001.md`; HYP-002
row set to the EXP-020 result (family status unchanged — transitions are operator-signed at the
checkpoint retrospective). No counted TEST read (TRAIN-only disclosure) → no
`test-read-ledger.md` entry. `multiplicity-registry.md` CF-VOLHARV-001 HYP-002 disposition
updated to the experiment outcome.

## 8. Infra note

`tools/ctrader-cli/run-experiment.sh` `parallel` mode bounded to 4 workers + 10s stagger
(`CTRADER_MAX_PARALLEL`; EXP-020 op-note) after an unbounded 16-container burst triggered
cTrader console startup crashes ("Message expected", stuck at 0.00%) on a fraction of cells —
absent on all pre-EXP-019 (≤2-symbol) confs. 7 EXP-020-G cells were re-run for parquet
corruption caused by mid-sweep container kills; full-file integrity scan clean afterward.
