# EXP-013 — Audit (CF-MR-004 / HYP-001)

**Verdict:** `NOT_TRADABLE` (frozen 4h referee, per-stratum). **Audit disposition: CONFIRMED — no
verdict-material finding; no leak; no re-run required.** Type: price-primary, native cTrader pending
orders (Route A), analysis-only Python on emissions.

## 1. Verdict forensics (per-stratum re-derivation)

32 cells (S5/S7 = 11, S6/S8 = 5). Frozen referee `referee_pstar.gate_stack_pstar`, domain=4h, q\*=0.75,
n_boot=10 000, seed=20260702. Re-derived from `results/verdict.json`:

| Arm | cells | powered (L1 ∧ epi≥8) | gross admits | net Holm admits |
|---|---|---|---|---|
| S5 | 11 | 7 | 0 | 0 |
| S6 | 5 | 3 | 0 | 0 |
| S7 | 11 | 7 | 0 | 0 |
| S8 | 5 | 4 | 0 | 0 |
| **Σ** | **32** | **21** | **0** | **0** |

Every cell: `ci_low < 0` for **both** net and gross. Per-cell net mean ∈ [−2.07, +1.16] bps/active-bar;
Holm over 32 net p-values admits none (min p ≈ 0.088). **Per-stratum binding (L-03): no stratum clears.**

**Masking check (cost on/off — operator-requested).** The cTrader run infused **no** commission/spread
(`Commission=0`, exact limit fills), so cost was applied in Python: net = frozen `adaptive_cost_bps_for`
(1.0–5.0 bps RT), gross = 0. **Gross admits = 0 too** → the null is *not* a cost artifact; the edge is
absent at the referee level with or without cost. Cost only shifts per-cell means ~0.03–0.17 bps/bar.

## 2. Mechanism (why — not just the numbers) [corrected after deeper investigation]

Root cause: **the fixed-parameter cross-instrument spreads are only weakly mean-reverting** — median
variance ratio **VR ≈ 0.90–1.06** (near the random-walk line VR=1), AR(1) half-life ~17–32 4h-bars. So a
resting fade at the ±2σ band **frequently fails to revert to the anchor mean within the horizon**:

- **Favorable-target hit ≈ 30% (per-cell 2–58%), not 100%.** Re-derived from actual fill prices (exit
  fill reaching the entry-time anchor-mean TP on the favourable side). The other ~70% ride to **horizon
  and market-close, adverse**. When hit: +85…+320 bps; when not: −3…−256 bps → they cancel.
- **Per-trade P&L is a wash.** 16/32 cells net-positive, dispersed −68…+34 bps/trade; no series robustly
  positive. USTEC (VR ≥ 1.0, **not reverting**) is the clearest loser across all four series.
- **Not cost, not peer-sharing.** Gross (cost=0) is already a wash and cost (1–5 bps) ≪ the ±100–320 bps
  swings, so cost is not the blocker. An earlier reading ("100% anchor-hit; reversion shared with the
  peer") was an artifact of a C# exit-label bug (§3) — corrected: the spread simply does not reliably
  revert, so the extreme→mean completion the strategy needs happens too seldom.

Re-confirms the terminal-branch prior on genuinely new fixed-parameter constructions: **price-derived
cross-instrument spreads at 4h do not yield a tradable single-leg MR edge** (weak/incomplete reversion).

## 3. Causal-provenance & leak pass

- **Decision causality (≤ t-1):** enforced by construction. Native cTrader pending orders; the planner
  `Observe()` consumes only *completed* 4h bars, `CurrentBracket()` returns levels for the next period;
  orders are placed at the first m1 of the new period from ≤ t-1 anchor/σ; the forming bar's OHLC never
  informs its own decision. No Python edge/fill recompute (L-01/P-09).
- **Fills within bar range:** 13 isolated breaches across 32 cells (≤ 2 per cell, ≤ ~1.5% of a cell's
  fills), large ones (92–156 bps) **only on session-gap indices** (JP225/US500/US2000/USTEC), FX tiny
  (7–16 bps). Signature = resting-limit fills at session-reopen **gaps** (a real favourable fill you'd
  get live) vs the bid-based Hour4 OHLC. **Not systematic** (guard threshold 5%/leg not tripped) → not
  lookahead. Recorded per-cell in `verdict.json:provenance_breach` for transparency. Immaterial to the
  null verdict.
- **Holdout fence:** backtest `--end` = each file's first-49% cutoff = `AnalysisEndUtc`; all 32 cells'
  max `SourceCloseTime` < fence (verified). Final-30% global holdout never loaded. 0 counted TEST reads.
- **Exit-label bug (found here; fixed forward; verdict-immaterial).** The C# tagged all non-horizon
  closes `exit_anchor_tp` (`_closeReason` reset before cTrader's async close event) → a spurious
  "anchor-hit=1.00". Availability was re-derived from **actual fill prices** (favorable-target hit vs the
  entry-anchor TP) = ~30% median. Realized P&L always used real fills → net/gross verdict unchanged; no
  re-run. C# fixed via an async-safe `_horizonPending` flag.
- **Leak tripwires — both VACUOUS here (expected, disclosed):**
  - **T1 peer-feed phase-shift** (binding future-destroy): 0 shift survivors → `tripwire_pass=True`, but
    **vacuously** — it only screens *live-net-admitting* cells, of which there are 0. Nothing to destroy.
  - **F-2 block-permute destroy:** the +8 bps uniform plant is **permutation-invariant** on the mean-stat
    referee → cannot collapse (`f2_collapse_ok=False` is expected, **not** a leak). Reported, **not**
    gated (see memory `permutation_destroy_mean_invariant`; the earlier REJECT_LEAK was corrected to this).
  - **F-2 plant-detect** `False`: the referee did not pass a +8 bps uniform plant on all powered cells —
    a **power** note (4h referee at 8–39 episodes with long-hold MTM variance), not a leak.
  - **Gate-debt:** the tripwires are only meaningfully exercised on a powered-positive admit; none exists.
    If any future CF-MR-004 variant admits, T1 must be re-run on that cell before any booking.

## 4. Vehicle-fit note (non-blocking, flagged for follow-up)

The frozen per-bar/episode referee is designed for position-state strategies; this is a discrete
round-trip bracket (~50–150 trades/cell, long holds). Per-trade dispersion is large and the per-bar
referee admits none. The binding verdict correctly uses the **frozen** referee (L-12; no retune). But a
**per-trade** evaluation (not a per-bar MTM) might read differently — this is a *new-experiment*
question, not a retune, and does not change the current NOT_TRADABLE disposition. Ties to
`evaluation_vehicle_must_be_native`.

## 5. Materiality gate

No finding moves sample membership, a denominator, a metric, temporal/causal validity, or the verdict:
- 13 gap fills → isolated, index-only, non-systematic, favourable-side, verdict already null → immaterial.
- Both leak tripwires vacuous → correctly non-binding on a null edge; disclosed.
- Warmup gate (full WZ window), USTEC ruin-truncation (balance→100M), and Position=active-dir emission
  were all fixed **before** this final run (see report §method). Final emissions validated: 64/64 cells,
  fence-clean, warmup ~199–602.

**No re-execution required.** Verdict `NOT_TRADABLE` stands.
