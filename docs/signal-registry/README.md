# Signal Registry

The signal registry is the programme-level file-drawer control for real signal
exploration. A candidate family must be registered here before any candidate
screening, cTrader run, result interpretation, or suite qualification.

## Directory Layout

```text
docs/signal-registry/
├── README.md
├── multiplicity-registry.md
├── candidate-families/
│   └── avwap.md
└── components/
    └── global-techniques.md
```

## Registry Objects

| Object | Meaning | Required before |
| --- | --- | --- |
| Candidate family | A related signal thesis with fixed first-branch definitions and explicit variants. | Any experiment scope. |
| Hypothesis | One falsifiable question inside a candidate family. | Any EXP using that question. |
| Component | Reusable entry, exit, risk, or position-management idea. | Any strategy that uses it. |
| Experiment | A pipeline EXP-ID that tests exactly one hypothesis or readiness question. | Any implementation. |

## Status Values

| Status | Meaning |
| --- | --- |
| `DRAFT` | Notes exist, but the item is not eligible for experiments. |
| `REGISTERED` | Definitions are fixed enough to create a scope. |
| `SCOPED` | A pipeline scope exists, but no result exists. |
| `SCREENED` | The frozen suite or scoped experiment has produced results. |
| `RETIRED` | The item is closed and cannot be silently reused as a fresh candidate. |

## Candidate-Family Document Requirements

Each file in `candidate-families/` must define:

- candidate-family ID and status;
- thesis summary;
- brainstorming provenance when the family is promoted from prior notes;
- fixed first-branch definitions;
- explicit parameters and allowed domains;
- hypotheses, with the EXP-ID that will test each one;
- exclusions, registered non-baseline branches, and any deferred variants;
- implementation path: Python characterization first when needed, cTrader
  strategy-host screening only after the component is defined;
- real-price outcome discipline and holdout exclusion.

## Multiplicity Rules

1. A candidate family, variant, detector choice, parameter branch, or follow-up
   candidate is countable once it is considered for screening.
2. Countable items must be listed in `multiplicity-registry.md` before any
   result-producing code or cTrader run.
3. Failed, refuted, blocked, and inconclusive items remain in the ledger. They
   are not deleted or renamed away.
4. A parameter change after seeing results is a new registered branch, not a
   revision of the old branch.
5. The frozen qualification suite is not tuned during Phase 004. It remains:
   strict gate stack, EXP-012 ratified-loose referee, and EXP-018 revised
   portfolio-fitness unit.

## Current Registered Batch

Registered candidate families (full per-phase batches in `multiplicity-registry.md`):

- `CF-LIQSWP-001` — Liquidity Sweeps. **REGISTERED — 2026-08-11, checkpoint-019.**
  Causal online level/raid/sweep characterisation across cTrader’s three assets and the
  Bybit TRAIN top-10 universe. Observation timeframes are 15m/30m/1h; Family A includes previous
  completed 1D/1W/4H/1H levels;
  confirmation references are 1H for 15m/30m and 1D for 1h. The value-gap arm uses a 1m TPO
  profile, 70% VA, at-least-30% low-density VA TPO mass, and tightness `gap_span < 0.30*(VAH-VAL)`.
  TRAIN only, zero-cost, no deployability claim. See `candidate-families/cf-liqswp-001.md`.
- `CF-VOLDIR-001` — Structural Volatility + Direction Programme. **REGISTERED — 2026-07-23,
  checkpoint-017.** Ordered claims: (A) vol reliability, (B) direction expectancy bps (not win-rate;
  SMA + ZigZag ATR), mid reflection, (D) combination / conditional direction-agnostic extraction,
  (E) XENA only if D graduates a base. Route `SPDR-012 → SPDR-013 → reflection → SPDR-014 →
  XENA-VOLDIR-001`. TRAIN only; 0 counted reads; holdout sealed; partial-cost / no-spread caveat.
  **Not** a reopening of CF-VOLCONV-001. See `candidate-families/cf-voldir-001.md`.
- `CF-VOLCONV-001` — Volatility-to-Direction Conversion. **REGISTERED — 2026-07-22,
  checkpoint-016** (SPDR-011 L1 closed NOT SUPPORTED 2026-07-23; family retrospective pending).
  One fixed five-symbol, four-hour conversion object: lagged daily volatility
  supplies magnitude state and a completed prior-day-range break supplies direction. Route is
  `SPDR-011 → EXP-099` if separately authorised; no XENA, historical TEST or holdout. Spread cost
  is unavailable/not charged, so all net reporting is explicitly partial. See
  `candidate-families/cf-volconv-001.md`.
- `CF-HTFDI-001` — Higher-Timeframe DI Conditioning (MTF continuation). **REGISTERED — 2026-07-08,
  G0 PENDING; CORRECTED same day** (promoted from the SPDR CTRL-01/02/03 series, WORTH_EXPLORING,
  operator-signed; independent audit + correction probe in the Phase-010 checkpoint `correction/`);
  0 slots, 0 counted TEST reads, holdout sealed. Last-closed HTF ±DI conditions the sign of the LTF
  forward return; edge is magnitude-weighted; high-vol ATR regime amplifies (not sign-sets).
  **Single thread (corrected):** A — continuation, **USTEC 1h/5min** (replicated on random+momentum
  blind bases, CI-clear under hold-matched blocks, corrected breadth 9+/0−); EURUSD 1d/1h carried
  only as a power-up stratum. **Former Thread B (XAUUSD fade) WITHDRAWN — NOT SUPPORTED** (fade
  fingerprint was an under-blocking artifact; the −0.86 cell was a mislabelled side-signed
  interaction, raw-move n.s.). Domains 1h/5min primary (**4h/1h NOT SUPPORTED**). Control apparatus
  carried from the SPDR legs (25-seed random battery + random-entry reference arm + null sentinels)
  — the random base is a **control, not a candidate**. Design constraints (corrected): vol-regime
  amplifier measured, uncapped/horizon exits, per-instrument max-stat, raw-bps dispersion,
  USTEC-continuation sign the only a-priori sign, dependence-matched blocks (block ≥ H). Separate
  log line (not this family): tail-managed naive base. Prior evidence: Phase 010 checkpoint
  `2026-07-08-010-htf-di-conditioning-spdr-series/`. See `candidate-families/cf-htfdi-001.md`.
- `CF-CSRR-001` — Cross-Sectional Consensus-Residual Reversion (basket). **RETIRED — 2026-07-07**
  (operator-signed, checkpoint-009 retrospective; availability — EXP-021/022/024 all NOT SUPPORTED);
  0 slots, 0 counted TEST reads, holdout sealed. Fades a
  member's deviation from the basket's cross-sectional consensus (median / equal-wt / weighted-implied),
  reversion endpoint on the open cross-sectional cell of the availability 2×2. 5 registered variants
  (4 suggested + the V5 active-entry/passive-exit remodel) decomposed onto 7 component axes;
  characterise each, construct one model. Baskets: Currencies (ready) + Indices (**Indices arm
  gated on INFR-005/VAL-007**); **4h only**; USD-strength consensus on Currencies; V5 execution
  (active entry / passive rolling-consensus exit / time-only stop) as the tradability vehicle;
  three-twin control battery mandatory. See `candidate-families/cf-csrr-001.md` +
  `docs/experiments-docs/families/cf-csrr-001/origin.md`.
- `CF-MR-004` — Cross-domain mean-reversion (fixed-parameter cross-instrument spreads). **REGISTERED —
  G0 RATIFIED** (Chapter-02 Phase 004, 2026-07-01); 0 slots, 0 counted TEST reads. Renewal of the MR
  thesis with 3 new cross-instrument spread designs (fixed-ratio pair, fixed-weight basket,
  relative-value index) + S5 redo (rolling-β basket, from scratch). Full-strategy-first (precalc
  limit orders, set-and-forget, no lower-domain); informative-not-gating MR screen; cTrader
  price-primary. Targets the untested cross-section/magnitude cell in the availability 2×2. See
  `candidate-families/cf-mr-004.md`.
- `CF-MR-002` — Causal RSI-2 mean-reversion fade (cTrader-primary; `rct[di-1]` exit). **REGISTERED —
  G0 PENDING** (Chapter-02 Phase 001, 2026-06-27); 0 slots, 0 counted TEST reads. Successor to the
  CLOSED/REFUTED CF-MR-001 under a new D0 after the causal fix (KB L-01). Benchmark vehicle for the
  referee-adaptivity renew (KB L-12). See `candidate-families/cf-mr-002.md`.
- `CF-MR-001` — RSI-2 fade + EXIT-RCT exit. **CLOSED — REFUTED** (2026-06-26; one-bar EXIT-RCT
  look-ahead; G-021/G-022 retracted). Not reopenable by re-parameterization. See
  `candidate-families/cf-mr-001.md`.
- `CF-AVWAP-001` — Anchored VWAP on regime pivots. **CLOSED** (Phase 013, ANCHOR_MOVE_FLAT).
- `CF-HA-HARAMI-001` — HA harami at trend exhaustion. **CLOSED** (Phase 016, CLOSE_FAMILY).
- `CF-CAPGEO-001` — Data-derived exit / capture geometry on frozen entries. **RETIRED** (Phase 018,
  G-018 `NOT_CONFIRM`; no net-tradable OOS capture geometry — the exit lever is exonerated, the
  bottleneck is upstream signal-conditional availability). See `candidate-families/cf-capgeo-001.md`.
- **Phase 019 — Family-Selection Availability Screen** (family-agnostic; NOT a CF). Screens untested
  entry-side *information axes* — `CF-VOLEXP-001` (single-series magnitude), `CF-XSECT-001`
  (cross-sectional), `CF-FLOW-001` (order-flow) — by TRAIN-only availability vs a multiplicity-adjusted
  permuted-axis null, to **select** the next family to open. **DRAFT — G0 PENDING** (2026-06-22); 0 slots,
  0 counted TEST reads. Candidate families under consideration:
  `candidate-families/family-selection-phase-019.md`; phase: the Phase 019 checkpoint + batch.

The active batch and gating preconditions are documented in `multiplicity-registry.md`.
