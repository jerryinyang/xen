# EXP-013 — Report (CF-MR-004 / HYP-001)

**Question (one):** on the 4h anchor domain, does the complete precalc resting-bracket cross-instrument
MR-fade strategy (4 series S5/S6/S7/S8; native cTrader pending orders) produce a per-stratum edge that
(a) is available (reversion-to-anchor) and (b) survives cost under the frozen 4h referee — or not?

**Answer:** **NOT_TRADABLE.** Reversion is highly available (anchor-hit = 1.00 everywhere) but is **not
monetisable by a single-leg fade**; per-trade P&L is a dispersed wash and **0/32 cells** clear the frozen
referee (net or gross, per stratum). No leak. Honest prior was LOW; confirmed.

## Result (per-arm, TRAIN, first-49% fence)

| Arm | series | cells | powered | net admits | gross admits | net bps/bar range |
|---|---|---|---|---|---|---|
| S5 | rolling-β basket | 11 | 7 | 0 | 0 | −0.68 … +1.02 |
| S6 | fixed-ratio pair (β=1) | 5 | 3 | 0 | 0 | −1.75 … +0.86 |
| S7 | fixed-weight basket | 11 | 7 | 0 | 0 | −2.07 … +0.95 |
| S8 | pair − rolling median | 5 | 4 | 0 | 0 | −1.61 … +0.90 |

- **Availability (favorable-target hit, fill-based):** the anchor-mean TP is reached on only **~30% of
  round trips** (per-cell 2–58%); the other ~70% ride to **horizon and market-close, adverse**. Reversion
  is *weak and often incomplete*, not "always" (an earlier "anchor-hit=1.00" was a C# exit-label bug —
  see §method; corrected from actual fills).
- **MR screen (informative, L-12):** the spreads are only **weakly mean-reverting** — median variance
  ratio **VR ≈ 0.90–1.06** (near the random-walk line VR=1), AR(1) half-life ~17–32 4h-bars. Pairs
  (S6/S8, VR 0.90–0.99) revert slightly more than baskets (S5/S7); **USTEC VR ≥ 1.0 (not reverting)** →
  worst P&L across all series.
- **Tradability:** 0/32 admit under the frozen referee (q\*=0.75, domain=4h), per stratum; Holm over 32
  net p-values admits none. **Cost is NOT the blocker** — gross (cost=0) also admits 0/32, and cost
  (1–5 bps) is tiny vs the ±100–320 bps per-trade swings.
- **Per-trade wash:** 16/32 net-positive, dispersed −68 … +34 bps/trade; no series robustly positive.
  When the target is hit: +85…+320 bps; when not (horizon): −3…−256 bps → they cancel.

## Mechanism (why) — corrected after deeper investigation

The fixed-parameter cross-instrument spreads are **only weakly mean-reverting** (VR ≈ 0.9–1.0, barely
below the random-walk line). So a resting fade at the ±2σ band frequently does **not** revert to the
anchor mean within the horizon: the favorable target completes on **only ~30% of trades**. Those winners
pay well (+85…+320 bps), but the ~70% that don't revert exit at **horizon, adverse** (−3…−256 bps), and
the two roughly cancel → a per-trade wash, `ci_low < 0` on every cell. **It is not a cost problem** (gross
is already a wash) and **not "reversion shared with the peer"** (my earlier reading, based on the buggy
100%-hit metric). It is simply that **the spread is not reliably mean-reverting**, so the extreme→mean
completion the strategy depends on happens too seldom. USTEC (VR ≥ 1.0, not reverting) is the clearest
loser across all four series. This re-confirms — on genuinely new fixed-parameter constructions — the
programme's terminal-branch prior: price-derived cross-instrument spreads at 4h do not yield a tradable
single-leg MR edge.

## Leak tripwires (both vacuous on the null edge — disclosed)

- **T1 peer-feed phase-shift** (binding): 0 survivors, but vacuous (0 live admits to destroy).
- **F-2 block-permute destroy:** vacuous — a uniform +8 bps plant is permutation-invariant on the
  mean-stat referee (`permutation_destroy_mean_invariant`); reported, not gated.
- Neither binds without a powered-positive admit; **gate-debt carries** to any future admitting variant.

## Method notes / deviations (all before the final run; logged)

- **Route A (native orders).** Replaced the initial self-adjudicating 4h-OHLC model (a vectorized
  residue that couldn't capture intrabar reversion) with real cTrader pending orders; m1 backtester owns
  fills. Fresh 4h basket feed (exact-CloseTime, no carry-forward — fixes the CF-MR-003 F-1 artifact).
- **Resting bracket, no z-gate** (operator-ratified): band level is the trigger; z is provenance only.
- **Emission convention fix:** `Position` = direction active during the bar (entry bar carries entered
  dir) — required for correct realized-bps assembly + episode counts.
- **Warmup gate:** full WZ=200 window required before trading (was ~2 for S6/S7/S8).
- **Ruin-truncation fix:** backtest balance → 100M (fixed-volume on high-notional indices wiped a 10k
  account, truncating USTEC); bps analysis is balance-independent.
- **Referee floor:** used the **frozen** 4h `min_state_count = 8` (design predeclared 20; the frozen
  referee value governs — no retune, L-12).
- **Cost on/off** (operator instruction): net (frozen cost map) + gross (0); both admit 0.
- **Exit-label bug (fixed forward; verdict unaffected).** The C# tagged every non-horizon close
  `exit_anchor_tp` because `_closeReason` was reset before cTrader's async close event fired → a bogus
  "anchor-hit=1.00". Fixed (async-safe `_horizonPending` flag). Availability was **re-derived from actual
  fill prices** in Python (favorable-target hit vs entry-anchor TP), which is authoritative; realized P&L
  always used real fills, so the NOT_TRADABLE verdict is unchanged (no re-run).

## MR-screen characterization (per series, informative — L-12, not gating)

| Series | construction | VR median (range) | HL median 4h-bars | favorable-hit |
|---|---|---|---|---|
| S5 | rolling-β basket | 0.97 (0.95–1.00) | ~21 | 0.17–0.51 |
| S6 | fixed-ratio pair | 0.93 (0.90–1.01) | ~27 | 0.09–0.47 |
| S7 | fixed-weight basket | 0.97 (0.93–1.01) | ~27 | 0.02–0.46 |
| S8 | pair − rolling median | 0.98 (0.95–1.06) | ~20 | 0.18–0.58 |

All series sit **near VR=1 (random walk)** — pairs (S6/S8) revert marginally more than baskets; no series
is strongly mean-reverting. This is the informative root cause of the null tradability: the anchor series
are not reliably reverting, so the fade's extreme→mean completion is rare (~30%).

## Registry disposition

CF-MR-004 → **SCREENED / NOT-TRADABLE on TRAIN** (retain; never deleted). Availability real, single-leg
capture null. 0 counted TEST reads; holdout sealed. Terminal-branch prior reinforced. Follow-up (new
experiment, not a re-parameterisation): a **spread/both-leg** vehicle or a **per-trade** evaluation — the
per-bar referee may mis-fit a discrete-RT bracket (vehicle note, audit §4).

## GATE: APPROVE (orchestrator inline post-exec, 2026-07-02)

**Reviewed:** `audit.md`, this `report.md`, `results/verdict.json`, registry/index updates vs
`references/governance-constraints.md`.

**Confirmed:** verdict forensics + causal-provenance/leak pass present (audit §1–3) · per-stratum masking
check done (net+gross, cost on/off) · no verdict-material finding (audit §5 — all fixes were pre-final-run;
13 gap fills isolated/immaterial) · signal-registry disposition recorded (NOT-TRADABLE, retained) ·
0 counted TEST reads (ledger unchanged) · holdout sealed · leak-tripwire vacuity disclosed, gate-debt
noted · frozen referee not tuned (L-12).

**Verdict: APPROVE.** EXP-013 complete; CF-MR-004 screened NOT-TRADABLE on TRAIN.
