# EXP-014c — CF-MR-004/HYP-004: lean bracket exit-set (trade the measured two-barrier object)

**Family:** CF-MR-004 · **Phase:** 004 · **Type:** tradability screen, TRAIN, price-primary
(native cTrader orders, m1 fills) · **Date:** 2026-07-03
**Verdict (binding, per-stratum): CREDIBLE_NEGATIVE_RETIRE** — both prespecified primaries
(JP225, EURUSD; e3/none/z20) are powered, bite-non-vacuous, and net-fail. The CF-MR-004
fixed-parameter thesis retires (operator decision D1, 2026-07-03).
Separate disclosure lines: 4 REJECT_LEAK cells (extend/z15 arms) + the extend-field discovery
(§6). Note: `results/verdict.json` prints `REJECT_LEAK_DISCLOSURE` as its headline string — the
audit (W1) corrected the label ordering; the per-cell statuses in that file are binding and
unchanged. Slots/reads: **0 candidate slots, 0 counted TEST reads**; holdout sealed; frozen 4h
referee untuned (L-12).

Artifacts: [design.md](design.md) · [code/](code/) · [results/verdict.json](results/verdict.json)
· [audit.md](audit.md) (PASS, 0 Critical, 3 Warnings) · [plots/](plots/) · operator decision
record `.ignore/temp/d1/exp-014c-findings-and-decisions.md` (D1–D6).

## 1. Question

Does the exit-set that reproduces the measured two-barrier race — TP frozen at the entry-time
anchor, SL at the symmetric outward barrier, time-stop ⌈3·HL⌉ (E3) — extract a net-positive
per-stratum edge on the availability-confirmed 4h cells (JP225 p_inward 0.696, EURUSD 0.589),
and which exit rule (E0→E1→E2→E3) moves the outcome, across reentry {none,allow,extend} and
z\* {2.0,1.5} characterisation axes?

## 2. Scope

S8_RVINDEX only, 4h only, single-leg, 11 cells (7 FX + 4 IDX). Entry unchanged from EXP-014b
(resting band limits from ≤t-1 bars, breach-skip). E0 = reused 014b emissions (read-only);
E1–E3 = 198 new native runs + 3 shift-twin waves (33 runs). Fence = EXP-013 first-49% TRAIN
cutoffs verbatim (audit diff-verified). PRIMARY = (e3, none, z2.0) on JP225 + EURUSD,
prespecified before any 014c data existed. Everything else disclosure/characterisation.

## 3. Method

Frozen 4h referee (`referee_pstar.gate_stack_pstar`, q\*=0.75, seed frozen) on engine-realized
per-bar NET (intra-position MTM L-09; frozen RT cost once/entry L-02); cross-cell Holm per
(exit, arm, z\*) family; per-admitting-cell peer-feed phase-shift (60h) leak tripwire + +8 bps
bite plant; post-C1 label logic (UNPOWERED never FAIL). M2 attribution, M3 traded-vs-measured
consistency, M4 session, M4b same-bar races, M5 exit-reason split, M6 regime slices.

## 4. Binding result — the primaries fail credibly

| Cell (e3/none/z20) | trades | episodes | net bps/bar | ci_low | bite | status |
|---|---|---|---|---|---|---|
| **JP225** | 85 | 19 | +0.26 | −1.84 | pass | NOT_TRADABLE |
| **EURUSD** | 67 | 18 | +0.28 | −0.46 | pass | NOT_TRADABLE |

All 9 other cells ≈0 or negative (availability-NULL/unpowered). 0 Holm admits in the binding
family. Full-family census (262 cells): AVAILABILITY_NULL 218 · UNPOWERED 22 · NOT_TRADABLE 14
· NET_ADMIT_AVAIL_NULL 4 · REJECT_LEAK 4.

**Mechanism — the loss is at the entry seam, not the exits (audit §5.2, raw-data traced):**
- The 014b measurement enters at the bar open after a **confirmed close-breach** (depth ≥
  band); the strategy fills a **resting limit at the band touch** — a shallower, earlier,
  adversely-selected conditioning event (D = z\*σ exactly, the marginal dislocation).
- M3: JP225 realized TP-share **0.52** (CI 0.39–0.66) vs measured p_inward **0.696** —
  inconsistent. EURUSD 0.51 vs 0.589 (CI-consistent, ~coin-flip). A symmetric ±D race at ~52%
  pays the spread: JP225 tp_anchor +266 bps/leg × 32 vs sl_outward −280 × 29; time_stop +25 × 24.
- Price-space/spread-space decoupling: 20/32 JP225 TP fills occurred **without** spread
  reversion; 15/24 time-stopped legs saw the spread revert while the frozen price TP never
  filled; EURUSD 0/20 stop-outs coincided with a spread reversion (the SL fires exactly when
  the basket signal is jointly wrong).

## 5. Exit attribution (M2, none/z20 — the decomposition worked as an instrument)

| Cell | E0 (moving) | E1 (frozen TP) | E2 (+SL) | E3 (+time-stop) |
|---|---|---|---|---|
| JP225 | −0.58 (ci −2.49) | +0.33 | +0.04 | +0.26 (ci −1.84) |
| EURUSD | +0.30 | (n=1, vacuous) | −0.26 | +0.28 |
| US500 | −1.53 | −0.47 | −1.27 | −1.10 |

Freezing the TP removes most of E0's moving-target loss engine; the SL subtracts value; the
time-stop is benign (recycles capital, +2…+25 bps/leg). **No exit rule unlocks the entry** —
the follow-up lever, if any, is the entry object (confirmed-breach market entry), not exits.
e1/none arms are structurally vacuous (no SL/time-stop + reentry-none ⇒ one open leg blocks
re-arming; EURUSD: 1 trade in 5y) — excluded from attribution narrative (audit I1).

## 6. Discovery — the extend-arm field (disclosure; operator decisions D2/D3)

Deweighting the leak test and ranking all 262 cells by net ci_low: **61 cells > 0, of which 53
never Holm-admitted — and every one is an extend/allow arm; no `none` arm is positive.** The
field spans all 11 instruments (10 powered), both z\*, all four exit sets, and the three strongest cells are
**positive every year 2021–2024** (US2000 e3/extend/z15 +10.7/+17.5/+5.3/+9.2 bps/active-bar;
AUDUSD, NZDUSD similar shape). Per-leg P&L fattens with ladder depth (US2000 L2 +26.3 bps/leg).
Execution clean (fills in-range, gap slippage charged, provenance traced). Cost stress: NZDUSD
survives 3× cost, AUDUSD 2×, US2000 1× only.

One mechanism expressed everywhere: **ladder scale-in on 4h dislocations harvesting
short-horizon own-price mean reversion.** Under the 60h phase-shift it retains 50–85% of its
edge — the basket supplies a trigger, not the harvest. Hence inadmissible as CF-MR-004
evidence (attribution), while robust on its own terms. **Operator decision D2: register a
dedicated candidate family (CF-MR-005)** — basket-free trigger, cost-stressed,
ladder-depth-aware, mechanism-characterisation first; mindful that CF-MR-001/002/003 died on
cost-vs-capture and P-02 bars exit-stack rescues. D3: the phase-shift control's semantics on
mixed P&L are investigated only after the mechanism is characterised.

Leak/attribution detail (audit §5.3–5.4): AUDUSD/NZDUSD e3/extend/z15 and NZDUSD/US2000
e0/extend/z15 survive their own shift → REJECT_LEAK (own-price). US2000 e2/e3/extend/z15
"collapse" is **not a zeroing** — shift nets stay CI-positive (+0.48/+0.49 ci_low) and fail
only the 3.0-bps L5 materiality leg, while e0/z15 passes the full stack under shift. Per W3:
US2000 is **not** claimed construction-specific; future shift-based attribution claims must
disclose the collapse fraction, not just the binary admit (KB lesson-candidate).

## 7. Other reads

- **M4 JP225 session:** decided P&L concentrates in Asia slots 00–08h (+4,159 bps) vs negative
  US hours. JP225's residual availability is session-structural; no gate action (never
  admitted). The `session_flag` normalisation itself is noisy (audit W2) — slot data sound.
- **M4b:** same-bar TP+SL races are a US500-only phenomenon (14/309 primary), m1-resolved
  SL-first 13:1; ambiguity ≈ 0 elsewhere, matching the availability read's assumption.
- **M6:** regime slices informative-only; no gating.
- 2 missing US500 emissions (e2/extend/z15, e3/allow/z20 — run-level failure; Holm m=10 in two
  disclosure families; not verdict-material, audit I2). Re-emit before any promotion of those
  families (moot under D1/D2 routing).

## 8. Audit summary

`audit.md`: **PASS — 0 Critical, 3 Warnings, 5 Info.** All key cells re-derived exactly from
raw emissions (fresh referee calls); shift twins independently re-adjudicated; frozen-bracket
invariants exact (SL symmetry 1e-15, TP=anchor 1.9e-7, horizons respected); zero forbidden exit
reasons in 198 frozen-arm cells; fence byte-identical to EXP-013; causal-provenance pass clean
(≤t-1 arming, m1 fills, next-open time-stop); leak tripwire shipped and binding per admitting
cell. W1 = headline relabel (applied here); W2 = session-flag normalisation; W3 = collapse-
fraction disclosure rule.

## 9. Conclusion & dispositions (operator record D1–D6)

1. **CF-MR-004 RETIRED** (D1). The measurement-matched bracket was the family's best shot; the
   confirmed availability does not convert to tradability because the traded entry is a
   different conditioning event than the measured one. Fourth consecutive MR family closed by
   the capture-vs-cost/attribution seam (CF-MR-001/002/003 precedent).
2. **CF-MR-005 registered** (D2): 4h ladder scale-in own-price MR harvest, basket-free trigger;
   mechanism characterisation first. See `docs/signal-registry/candidate-families/cf-mr-005.md`.
3. Phase-shift-control semantics study deferred behind CF-MR-005 characterisation (D3).
4. Per-cell statuses retained unchanged; refuted/leak items stay in the registry (D4).
5. W3 filed as KB lesson-candidate (D5). No TEST read spent; holdout sealed (D6).

## GATE: APPROVE (orchestrator inline post-exec, 2026-07-03)

Verdict forensics ✓ (per-stratum re-derivation, masking check — no pooled headline does work;
mechanism stated; gate-shape checked, bite non-vacuous on both primaries). Causal-provenance &
leak pass ✓ (provenance traced to named lines; tripwire binding per admitting cell; shift twins
emitted for all admitting arms; price-primary in-engine). Verdict-material findings: none —
no fix-and-rerun required (W1 is a label-ordering correction applied in this report; W2/W3
shown non-material in audit). Registry disposition recorded ✓ (CF-MR-004 RETIRED, CF-MR-005
REGISTERED, multiplicity rows entered, 0 counted TEST reads). Indexes updated ✓. Holdout ✓.
**Status: EXP-014c CLOSED.**
