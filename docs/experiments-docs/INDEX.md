# Xen Experiments — Master Index (Chapter 04 — opens after INFR-010 Phase D)

Live status + family navigation for the current chapter. Chapter 03 is archived at
`archive/chapter-03-xena-mtfctx/experiments-docs/`; Chapter 02 at
`archive/chapter-02-mr-volharv-htfdi/experiments-docs/`; Chapter 01 at
`archive/chapter-01-price-geometry-referee/experiments-docs/`. Distilled canon:
`docs/knowledge-base/` (read first). Live ledgers: `docs/signal-registry/`.

## Current Checkpoint Status

**INFR-010 Phase D PASSED 2026-07-16 (VAL-008, operator verdict SUPPORTED) — Chapter 04
research may open.** Checkpoint-013 open (HTFCAP/EPSOSC + CAL). **INFR-014 COMPLETE
2026-07-17 — operator ACCEPTED partial pin (QA run 4 APPROVE)** — CLS-FILTER
LOW_ONLY_CERTIFY; CLS-EPISODE TERMINAL; active pin sha256 `ac8a1eb6…`. XENA-HTFCAP may
design on CLS-FILTER low; EPSOSC blocked pending new CAL. **INFR-015 COMPLETE
2026-07-18 — operator ACCEPTED amended pin `abbb1842…` (supersedes `ac8a1eb6…`; audit
CERTIFICATION SOUND). Active certified set: CLS-FILTER low + CLS-EPISODE low. XENA-EPSOSC
unblocked LOW-only — binding caveats: ≥16 gate-band legs (F*), α priced ≤~0.06, 4th
CLS-EPISODE cycle needs family-wise correction.** ch03 pin still VOID.
SPDR-004/005/006 complete (three WORTH_EXPLORING). INFR-013 COMPLETE.
**Checkpoint-013 CLOSED 2026-07-19 (operator-signed retrospective).** Both registered families
closed: **CF-EPSOSC-001 RETIRED (REFUTED)** — refuted twice at XENA (001+002), AKRO drift
pedestal reproduced; **CF-HTFCAP-001 CLOSED (CHARACTERISED, not refuted)** — real gross BTC edge,
sub-cost at 8–16h holds; re-open path = new design. Holdout SEALED throughout; EPSOSC 0/2 slots,
HTFCAP 1/2 (exploratory TEST spend). Chapter at a natural rollover boundary.

**Checkpoint-014 OPENED 2026-07-20 — DESIGN SIGNED (D1–D6 approved; 6 source-adherence
resolutions signed).** New family **CF-SIGAUC-001 — Signed Auction Structure** REGISTERED: session-anchored
auction events plus located signed-flow triggers, on 1m bars carrying **exact taker buy/sell
volume**. Scope = instrument build → statistical spine (master go/no-go) → breadth sweep:
**INFR-017** (signed-bar catalog lane + A8 provenance audit + seasonal baselines), **INFR-018**
(anchor race, A6 discriminator race, proxy validation → hash-pinned instrument registry),
**SPDR-007** (spine, master gate), **SPDR-008** (breadth). Signal tests + model assembly deferred
to checkpoint-015. **0 counted TEST reads; no TEST contact; holdout SEALED.** Chapter rollover
remains available and deferred — operator's call, not a blocker.

**INFR-017 COMPLETE 2026-07-20 — QA APPROVE (run 4).** Kill-gate **HYP-I1 PASS**: the taker split
reproduces bit-exactly from raw Bybit trades and the archive `side` column is confirmed the
**aggressor** side — the family's founding measurement is verified. **`SpreadBps` pinned UNUSABLE**
(a mean-print differential, negative in 32.4%/39.9% of BTC/ETH TRAIN minutes; the shared
`t1_round_trip_spread_bps` passes it through unfloored ⇒ negative cost — flagged for the
retrospective, blast radius NOT investigated). Frozen for INFR-018: `seasonal_baselines.parquet`
`1b7244c8…`, `column_pins.json` `e3b9fd9b…`, `SignedBar` + `data/catalog_sigbar/`.
**Two operator decisions OPEN:** (1) adjudicate a disclosed holdout touch behind the design's
original headline figures (corrected; one data-quality column's distribution; no shot spent);
(2) baseline coverage — only 296 of 894 admitted instruments have TRAIN data and 197 reach the
DESIGN bank, a survivorship-shaped subset, against a family whose thesis is cross-sectional breadth.
**INFR-018 COMPLETE 2026-07-21 — operator accepted instrument registry.** Stage I freeze:
anchor **A-USOPEN · L=15**, A6 rule **D4-t50-w30 · δ=0**, kernel **K-UNIFORM** (calibrated),
class residual thresholds pinned; registry `pin_sha256 5c386984…`. Integrity tripwires clean
(I2 future-shift + I3 path-swap collapse; both positive-control leak plants fire). CONFIRM
train-internal recorded (not OOS). Spread regime still **UNAVAILABLE**. QA runs 1–7 REVISE →
run 8 APPROVE. **0 counted TEST reads; holdout SEALED.** Next: **SPDR-007** (statistical spine
— master go/no-go) then **SPDR-008** (breadth).

**SPDR-007 COMPLETE 2026-07-21 — operator disposition NOT_WORTH (price-only S1/S2 spine; a
P-01 confirmation).** The anchored-breakout Protection quantile **reproduces** on CONFIRM
(pooled calib_err +0.030/+0.028 — source framework-falsifier #1 not triggered on reproduction),
**but adds ≈0 over a matched cross-session unconditional entry**: the target-before-stop race
sits at gross breakeven (contrast −0.010) and is **below cost-adjusted breakeven on all 5
majors** (w−p0ᶜ −0.05 to −0.14); excursion-asym contrast +0.090 CI [−0.23,+0.32] WASH. P-01
confirmed. Integrity clean (tripwire NO_MATERIAL_EDGE, bite 0.77; freeze/fence/causal asserted).
QA run 1 REVISE→resolved, runs 2–3 APPROVE; deviations D-1 (cross-session control) + D-2
(material-edge tripwire) ratified. **Signed flow (Δ) UNTESTED — family warrant deferred to
ckpt-015; tested the daily US-open session / 15-min IB / single-session hold only.** Family
status **unchanged (REGISTERED)** — retrospective decides close/keep. **0 counted reads; holdout
SEALED.** Next: **SPDR-008** (signed-trap breadth, S1+S3).

## Current Infrastructure Tasks

| Item | Status | Detail |
|------|--------|--------|
| INFR-010 | Phases 0/A/B/C/D/E **COMPLETE 2026-07-16** | all phases closed (Phase E = INFR-013) |
| INFR-011 | Phase A COMPLETE 2026-07-16 | 894 ADMITTED, 672M bars, fence PINNED `35d3375e…`, catalog at `data/catalog/` |
| INFR-012 | Phase C COMPLETE 2026-07-15 | governance rebind verified 10/10 (`results/phase_c_verify.json`) |
| VAL-008 | COMPLETE 2026-07-16 — **Phase D PASS** | `python/experiments/VAL-008/report.md` |
| INFR-013 | Phase E COMPLETE 2026-07-16 — verify PASS | `xen.orderflow` contracts + skeleton; NO collection/detectors; spec `docs/references/orderflow-feature-store.md`; sample-day report `INFR-013/results/sample_day_report.json` |
| INFR-014 | **COMPLETE 2026-07-17 — pin ACCEPTED (partial)** | QA run 4 APPROVE; CLS-FILTER LOW_ONLY_CERTIFY; CLS-EPISODE TERMINAL; active pin sha256 `ac8a1eb6…`; S1 A-vs-B PASS; `python/experiments/INFR-014/report.md` |
| INFR-015 | **COMPLETE 2026-07-18 — pin `abbb1842…` ACCEPTED** | n_legs_floor F*=16 atop overlap blocks; LOW CERTIFIED (0.025/0.030, ood 0.75), HIGH FAIL_COV; audit SOUND; EPSOSC unblocked LOW-only; `python/experiments/INFR-015/report.md` §9.3 |

## Family Indexes

| Family | Range | Status |
|--------|-------|--------|
| [infrastructure-validation](families/infrastructure-validation/INDEX.md) | VAL-008 | Phase D PASS 2026-07-16 |
| CF-SIGAUC-001 (card: [`cf-sigauc-001.md`](../signal-registry/candidate-families/cf-sigauc-001.md)) | INFR-017/018, SPDR-007/008 | **REGISTERED 2026-07-20** (ckpt-014 D1) — INFR-017/018 COMPLETE; **SPDR-007 COMPLETE — NOT_WORTH** (price-only spine, P-01 confirmation; signed warrant untested); next **SPDR-008** (signed-trap breadth) |

New candidate families register at `docs/signal-registry/candidate-families/` when research
opens.

## Checkpoint Retrospectives

| Checkpoint | Closed | Outcome |
|---|---|---|
| [014 — Signed Auction Structure](checkpoints/2026-07-20-014-signed-auction-structure/design.md) | OPEN (2026-07-20) | **DESIGN SIGNED** — D1–D6 approved; CF-SIGAUC-001 REGISTERED. **INFR-017/018 COMPLETE** (registry pin `5c386984…`). **SPDR-007 COMPLETE — NOT_WORTH** (price-only spine reproduces but no edge over matched entry, loses after cost; P-01 confirmation; signed warrant untested). Next: **SPDR-008** breadth (S1+S3 signed-trap). |
| [013 — Chapter 04 Open: HTFCAP + EPSOSC + Fresh XENA CAL](checkpoints/2026-07-16-013-chapter04-open-htfcap-epsosc-cal/retrospective.md) | 2026-07-19 | Both families closed — CF-EPSOSC-001 RETIRED (refuted 2×, drift pedestal); CF-HTFCAP-001 CLOSED (characterised — real sub-cost gross BTC edge). Apparatus rebuilt on Bybit (fresh CAL pin `abbb1842…`, report-layer framework INFR-016). Holdout SEALED. |
