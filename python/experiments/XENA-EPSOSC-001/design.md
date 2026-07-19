# XENA-EPSOSC-001 — CF-EPSOSC-001 XENA Universe (Bybit, episode-harvest VOLARM fade)

**Lane:** XENA (default route) · **Family:** CF-EPSOSC-001 (REGISTERED 2026-07-16, ckpt-013)
**Status:** DESIGN — Stage 1 (quant-designer, 2026-07-18); QA + operator execution gate pending
**Binding input:** SPDR-005 WORTH_EXPLORING (2026-07-17, §9 caveats 1–6)
**Active CAL pin:** `python/experiments/INFR-015/results/bybit_pc_frozen_registry.json`
sha256 `abbb184229236a75f624537ca605668a73f6f85138c150e14a3609c4191bf786` — class
**CLS-EPISODE**, **LOW cadence only certified** (α̂ 0.030, cov 0.025; HIGH FAIL_COV) with
**binding acceptance caveats** (INFR-015 §9.3): (1) true α priced plausibly ≤ ~0.06;
(2) **n_legs_floor F\* = 16** — design must budget ≥16 gate-band legs (LOW out-of-domain
0.75); (3) any 4th CLS-EPISODE CAL cycle needs family-wise correction / doubled bank.

---

## 1. Question + mechanism

**Falsifiable question.** Under the pinned CLS-EPISODE binder (stage-1 net search → stage-2
overlap-blocked, floor-guarded gross leg-studentized LCB on an embargoed band), does a
portfolio drawn from the VOLARM episode-fade universe certify (stage-2 gross LCB > 0 with
n_legs ≥ 16), where the calibrated false-pass rate is α̂ ≈ 3% (priced ≤ ~6%)?

```
MECHANISM: After a confirmed vol-expansion-armed stretch (ATR(14)[t−1]/ATR(14×4 slow)[t−1]
  ≥ 1.25 AND |RealClose[t−1] − rolling-median-anchor(W)[t−1]| / ATR(14)[t−1] ≥ k), price
  tends to revert toward the rolling anchor WITHIN the episode; harvesting the reversion
  as a one-sided market-entry fade cleared endogenously (return-to-anchor, or hybrid with
  time cap H=W) yields positive gross bps/episode on high-turnover alts (SPDR-005 promote
  cluster: VOLARM×15m, 4 symbols, med lift +54–60 bps/episode, derangement collapse ≈0.95,
  on a NEGATIVE pooled median −11.4 — a concentrated cluster, not broad availability).
  P&L-bearing object: the EPISODE (entry → within-episode clear); event cadence episodic,
  LOW class (median duration ~19–20h, cap ≤48h; tens of episodes/candidate/band).
DERIVED: estimand = gross open-to-open bps/episode via xen.adjudication episode objects
    (shim on positions_ledger; L-16 episode-native); portfolio functional = pinned
    g_gross_ratio on admitted legs, bps/episode for disclosure
  null = pinned CLS-EPISODE calibration battery (episode-shaped nulls, overlap blocks,
    floor guard) + in-design episode-label derangement destroy
  horizon = endogenous clear (RET_ANCHOR) or hybrid cap H = W LTF bars; episodes ≤ 48h
    by construction at 15m×W≤192
  test = pinned two_stage_sample_split binder with block_legs = episode_overlap_rule_v1
    and n_legs_floor = 16 — this design NEVER re-derives thresholds
```

## 2. Object identity declarations

```
OBJECT-IDENTITY:
  measurement object == trading object: YES — both are the EPISODE: market entry at open
    of bar t after confirmed armed-stretch event → path → within-episode clear (RET_ANCHOR
    or HYBRID); single-name, one-sided, single-leg; adjudicated from positions_ledger.
    L-16 episode-native; per-leg CIs never read as conditioning evidence (P-11).
  measured conditioning event == traded entry event: YES — arm + stretch evaluated on
    CONFIRMED bars ≤ t−1; capital committed at next 15m bar open, market order; NO limit
    entries anywhere (limit_entry_cells = false; L-27 / P-10 not in play; pin_usage
    "limit_print_sole_certify_forbidden" honored trivially).
  effect-splitting windows non-overlapping: YES — no new entry on an arm while its episode
    is open; episodes within a candidate are disjoint in time. B-9.
```

## 3. Estimand

- Canonical: `xen.nautilus.adjudication_shim` → `xen.adjudication` (episode grouping from
  the ledger; gross open-to-open bps summed entry-open → exit-open, sign = fade direction).
- Emission contract v1 per candidate; finite synthetic `SlPrice` = EntryFill − side ×
  1.0 × k·ATR(14)[t−1] (sizing denominator only).
- Estimand gate v2 must pass before ANY read; L-29 anchor check
  (`EntryFillPrice == next-bar RealOpen ± 1 tick`).
- **Censoring:** episodes open at a band boundary are CENSORED by the oracle's segment-end
  censoring; censored fraction per cell disclosed (>20% flagged — clear-policy failure is
  itself evidence; silent drop banned).

## 4. Universe manifest (all cells enter — no per-cell quality gates)

### 4.1 Instruments — causal online membership (SPDR-005 caveat 3; D3 anti-survivorship)

- **Membership gate (code-asserted, causal):** a candidate may OPEN an episode on symbol S
  at 15m bar t only if S ∈ top-10 trailing-24h **volume** (pin metric `trailing_volume` =
  sum of 1m `volume` over `window_bars=1440` ending ≤ asof−ε) at t−1, daily 00:00 UTC
  rebalance, ADMITTED spec-complete instruments, tie-break lexicographic — ckpt-013 §5
  rule via `xen.nautilus.universe_selection` (selection_rule_default_hash in pin:
  `0dd53037…`). Point-in-time set INCLUDES delisted symbols (anti-survivorship binds fully
  at XENA). Open episodes may run to clear after membership exit (exit is
  episode-endogenous, not membership-driven).
- **Symbol axis of the grid:** all symbols with ≥90 TRAIN membership-days under the rule
  (computed deterministically from catalog TRAIN data before emission; list written into
  the universe manifest). Realized = **29 symbols** (the earlier "≈12–18" was a pre-
  computation estimate; manifest is authoritative) incl. SHIB1000/DOGE/GALA/JASMY
  (cleared names in-axis) and 1000BONK/1000BTT (counter-strata — cells ENTER per XENA
  principle; no BONK/BTT centring in any claim: strictly per-stratum, cluster reads
  exclude them as centre — caveat 2). Note: XRP is a top-10 member on <90 TRAIN days →
  below the axis floor, NOT traded (see §13 golden-trace note).

### 4.2 Candidate grid (seed scope = SPDR-005 caveat 2; frozen definitions §5.3 of SPDR-005)

| Axis | Values | n |
|---|---|---|
| Object | VOLARM only (vol_ratio 1.25 fixed — no retune) | 1 |
| Domain | 15m LTF only (1h VOLARM near-empty at screen; 5m not promoted) | 1 |
| Anchor window W (bars) | 96, 192 | 2 |
| Threshold k | 2.5, 3.0 | 2 |
| Clear | RET_ANCHOR, HYBRID (H = W) — TIME-only excluded (thesis = endogenous clear) | 2 |
| Side | LONG_ONLY, SHORT_ONLY | 2 |

Variants = 2×2×2×2 = **16 per symbol**. The ≥90-day membership rule (§4.1) computes the
symbol axis deterministically into `results/universe_manifest.json` — **that list is
authoritative and the counts here are derived from it**. Realized axis = **29 symbols**
(the earlier "≈14" was a pre-computation estimate) → **464 binding candidates** (16 × 29).
**Secondary probe (disclosure-only):** STRETCH × 1h × RET_ANCHOR × k{2.5,3.0} × W{96,192}
× side{L,S} = **8/symbol** on the same membership gate (caveat 2: XRP/PEPE-shaped tail;
disclosure stratum, never centred in a claim) → **232 disclosure candidates** (8 × 29;
**696 total** cells). Every cell enters the oracle universe.

### 4.3 Cadence + floor coverage (binding integrity attestations)

- Pin certifies CLS-EPISODE **LOW only** (generator analog: median duration 4h, cap 48h).
  VOLARM 15m episodes ran ~19–20h at screen — within cap, episodic LOW class. Attestation
  at candidate gate: per-candidate episode counts, median duration; a HIGH-shaped stream
  (median duration ~1h / dense) is outside certification → no gate spend on it.
- **F\* = 16 reachability (pin caveat 2 — mandatory):** stage-2/gate bands must be expected
  to contain ≥16 episodes for the certified subset. Budget in §10; if the certified top-1's
  gate-band n_legs < 16, the binder's floor guard refuses certification by construction
  (domain exit, not a discretionary call) — expected reachability disclosed (LOW ood 0.75
  in calibration; the design mitigates via multi-symbol subsets, which pool legs at the
  portfolio level).

## 5. Temporal mapping + pinned binder (cited, never re-derived)

- TRAIN 2021-06-29 → 2023-12-18; TEST 2023-12-18 → 2025-01-08 (fence manifest; catalog pin
  `35d3375e…`); holdout sealed. Effective VOLARM mass starts ~2022-07 (caveat 4 power note).
- Stage bands: pin fractions `search 0.5 / ranking 0.25 / embargo 0.2` via frozen band
  code; UTC boundaries written to the manifest BEFORE search, immutable.
- Binder (pin, CLS-EPISODE): `two_stage_sample_split`; stage-1 top-1 on **g_net**
  (charge_costs=true, `bybit_round_trip_cost_bps_v1`, **funding × episode duration
  binding**); stage-2 `lcb_g_leg_studentized(g_gross) > 0`, `block_legs =
  episode_overlap_rule_v1`, `n_legs_floor = 16`; pass event `stage2_gross_lcb_positive`;
  deployability `stage2_net_lcb_positive` (informational-binding per L-22); n_boot 200,
  alpha 0.05, one_subset.
- Search `run_restart` ×10–15 LAHC on TRAIN search band; certification `certify_and_rank`
  with `registry_path` = INFR-015 pin (hash-verified); final gate `run_final_gate` on TEST,
  **counted, cap 2**, operator-approved; `new_data_attestation` operator-only.
- Multiplicity: `evaluation_count` + `distinct_subsets` with every number; run registered
  in `docs/signal-registry/xena-runs.md` before search. Runners: L-30/L-31; S1 smoke
  multi-instrument single-node admissible.

## 6. Costs + pre-search floor

- Costs oracle/analyst-injected: `bybit_round_trip_cost_bps` (taker fees + per-symbol
  pseudo-quote spread + **funding scaled by episode hold_hours** — the family's binding
  funding decision; ~19–20h episodes ≈ 2–3 funding events).
- Meme-alt spread caution: SPDR floors ~14–20 bps at measured spreads; BONK/BTT-class
  spreads wider — per-symbol floors re-measured on the manifest symbol list, disclosed.
- **Pre-search gross floor (XENA-003):** per-cell TRAIN median gross bps/episode vs
  measured breakeven; entire-binding-mass sub-breakeven → park before search. Individual
  sub-floor cells still enter; floor table is disclosure.
- **Funding stress ladder (disclosure):** 1× and 2× funding GAP on finalist cells
  (SPDR-005 open probe).

## 7. Controls

```
CONTROL RAND-TIMING-BATTERY (per certified finalist cell, analysis stage):
  question answered: is bps/episode above cadence-matched random entries with the same
    clear policy (path-alignment vs episode-shape artifact)?
  population: random entry times matched per cell on episode count + duration profile +
    side + clear rules + non-overlap; 25 seeds; seeds never see stretch/arm labels.
    DISJOINT: entry timing decoupled from the armed-stretch event — it can show
    clear-policy/drift profit the signal series cannot separate (B-1).
  bite/MDE: battery percentile of treatment mean bps/episode (L-19 seed battery);
    SPDR-scale effect (+54–60 bps/ep) ≫ battery spread at n≥40 episodes; MDE per cell.
  non-vacuity: random timing moves the MEAN bps/episode directly (B-6).
  expected outcome if H true: finalist ≥ P95 battery; if H false: within battery IQR.
  disclosure: collapse fraction per cell.
  destroy form: independent random draw, not a permutation — L-28 n/a; percentile read.

CONTROL GRID-SHAPE IDENTITY (disclosure): structure identity vs P-12 dead grid — the
  traded object has NO hard inventory cap / banded rebalance; code inspection clause for
  QA (P-12 escape: within-episode clearing, rolling anchor). No GRID_TWIN arm at XENA.
```

## 8. Leak tripwire

```
TRIPWIRE: episode-label DERANGEMENT (alignment destroy; SPDR-005 Control B analog)
  Construction: for each certified finalist, derange the episode start-time assignments
  across the episode schedule (zero fixed points, code-asserted; episode duration + side +
  clear profile preserved, start times exchanged across ≥ episode-length-separated slots)
  and re-adjudicate on real prices.
  must collapse the edge; expected collapse fraction ≈ 0.9+ (SPDR-005 measured ≈ 0.95
  med on the promote cluster; 100% ≥ 0.5).
  vacuity check: moves the mean bps/episode (path alignment broken, mean-bearing metric);
  slot separation ≥ max episode duration prevents partial self-overlap. B-6 clean.
  derangement=YES (zero fixed points; L-28).
  HARD: finalist surviving the derangement (collapse < 0.5) = leak/artifact → REJECT,
  no operator override.
```

## 9. Interpretation bands (per stratum = symbol × clear × side; no binaries)

```
BANDS (informative except integrity):
  SUPPORTED:    stage2 gross LCB > 0 with n_legs ≥ 16 (pinned) AND net leg: g_net LCB > 0
                under fees + 1× spread + funding (L-22) — SUPPORTED-GROSS separately as
                selection-machinery verdict only
  WASH:         |median bps/episode| < battery noise scale (A≈B)
  CONTRADICTED: gross UCB < 0 on powered stratum
  UNPOWERED:    n_episodes < F07 floor (MDE ≤ shrunk TRAIN effect) — never a negative
POOLED: disclosure-only (pooled median was NEGATIVE at screen — caveat 1; concentration is
  expected and must be reported per-stratum). STRETCH×1h probe + BONK/BTT strata:
  disclosure-only regardless of band. True α priced ≤ ~0.06 on any certification claim
  (pin caveat 1) — stated alongside every gate result.
```

## 10. Power statement

```
POWER (VOLARM 15m, effective mass ~17 months of TRAIN — caveat 4):
  screen-observed: promote cells ~40–60 episodes/cell full-TRAIN → per-band expectation:
    search band (50%): ~20–30 · ranking (25%): ~10–15 · gate/stage-2 band: ~10–20
  multiplicity: search registers `evaluation_count` / `distinct_subsets` against the
    REALIZED manifest — **464 binding candidates (29 symbols), not the earlier ~224** (§4.2).
  F*=16 note: single-cell candidates may still fall under the floor on the stage-2 band
    (calibration LOW ood 0.75 mirrors this) — the single-cell-underfloor caveat stands;
    certified SUBSETS pool legs across symbols/cells. Under the 29-symbol axis F*
    reachability is STRENGTHENED, not assumed: pre-search attestation
    (`cadence_fstar_attestation.json`) measures **18 binding cells with gate_expected ≥ 16**
    and a **top-3 pool of 60.8 gate-band legs** (`portfolio_Fstar_reachable = true`).
    Subset-level gate-band legs expected ≥16 for K≥3-sized portfolios.
  MDE at n=16 episodes, σ_episode ≈ 150 bps: ≈ 75 bps — above cluster med lift (+54–60):
    single-cell stage-2 reads at the floor are UNDERPOWERED for SPDR-scale effects;
    portfolio pooling is the powered path (n≈50 → MDE ≈ 42 bps; n≈100 → ≈ 30 bps).
  strata predeclared UNPOWERED: any cell with < F07-floor episodes on its read band;
    STRETCH×1h probe cells (thin by construction); late-listed symbols (<6 months mass).
```

## 11. Screen-effect conversion pin (L-21)

```
CONVERSION-PIN:
  divisor object: NONE on the promote facet — SPDR-005 primary unit is "gross open-to-open
    bps/episode, no ATR divisor" (SPDR-005 results/unit_pin.json; design §L-21 block).
  measured value: n/a (native bps); disclosure ATR = domain LTF ATR(14)[t−1].
  resulting effect: carried native: +54–60 bps/episode med lift (VOLARM×15m cluster);
    cluster med means 36–119 bps/episode.
  cost floor: measured spreads + taker + funding GAP ≈ 14–20 bps per episode (SPDR-005
    money-floor table; re-measured per manifest symbol before search). Cluster medians
    clear the floor → tradability framing permitted; net leg still binds (L-22).
```

## 12. T1 spread-scale routing

```
SPREAD-SCALE-ROUTING (per certified finalist cell, before any verdict-bearing read):
  estimated_rt_spread_bps: xen.evaluation.t1_round_trip_spread_bps on the cell's symbol +
    TRAIN window (meme alts expected materially wider than majors)
  gross_edge_bps: cell TRAIN median gross bps/episode
  t1_undecidable: xen.evaluation.spread_scale_route (3× rule, not re-derived)
  if YES: AWAITING_MBP or T2 confirm (BTC/ETH/SOL only — NOT available for meme alts →
    park stands); pooled T1 reads disclosure-only; no tradability band on that cell
```

## 13. Golden-trace spec (QA derives; developer must not generate)

```
GOLDEN-TRACE (3 events, hand-derived from catalog + SPDR-005 §5.3 definitions):
  G1: GALAUSDT 15m, first VOLARM(1.25) armed-stretch k=2.5, W=96 confirmed event after
      2022-09-01T00:00Z with GALA ∈ causal top-10 at t−1 — verify arm ratio, stretch ≥ k,
      membership; expected market entry next 15m RealOpen, side = fade (stretch up →
      short); RET_ANCHOR clear at first confirmed re-cross < 0.25·k·ATR or anchor cross;
      SlPrice = entry − side × k·ATR(14)[t−1] finite.
      (in-axis member, 409 TRAIN membership-days; XRP was <90 days → not traded.)
  G2: DOGEUSDT 15m, HYBRID W=192 k=3.0 episode after 2023-01-01T00:00Z that reaches the
      time cap H=192 bars without RET_ANCHOR clear — expected exit at cap-bar RealOpen;
      verify no second entry while open.
  G3: negative trace — a GALAUSDT 15m bar where stretch ≥ k but GALA is OUT of causal
      top-10 at t−1 (membership gate): expected NO entry. Confirms selection causality
      (≤ t−1). Gating is symbol-agnostic; any in-axis member on an off-membership day works.
QA diffs all three against the emission before execution sign-off.
```

## 14. Integrity vs informative split

```
HARD (block): tripwire collapse (§8), holdout fence, causal provenance (≤ t−1 features +
  membership; fence attestation non-STUB), estimand reconciliation (gate v2), pin hash
  verification (abbb1842…), cadence/floor coverage attestations (§4.3), SlPrice finiteness,
  P-12 structure identity (no hard cap / banded rebalance in traded object).
INFORMATIVE (operator judges): all effect sizes, LCB/UCB, battery percentiles, collapse
  fractions, funding stress, floor tables, STRETCH×1h probe, BONK/BTT strata, net
  deployability. No auto-verdict thresholds. Gate spend + final verdict = operator gates.
```

## 15. Complexity budget + amendments

- Stat machinery: pinned binder + 2 controls — no new tests; no new accounting.
- New code: manifest builder (membership-day symbol list + band boundaries), Nautilus
  strategy (VOLARM/STRETCH episode fade + membership gate), batch runner cells,
  derangement/battery scripts in `analysis_code/`.
- Visualisations: ≤5. Amendment ledger (L-23): running **0 L / 0 T / 2 N**.
  - AMD-1 (NEUTRAL, 2026-07-17, QA run 2 Issue 1): §4.1/§4.2/§10 counts refreshed to the
    realized manifest (29 sym / 464 binding / 232 disclosure). No gate loosened/tightened — the
    ≥90-day axis rule is unchanged and authoritative; text aligned to its deterministic output.
  - AMD-2 (NEUTRAL, 2026-07-17, QA run 2 Issue 4): §13 golden-trace G1/G3 re-pointed XRP→GALA
    (XRP <90 membership-days, not in traded axis). Trace intent unchanged; no gate effect.
- No scope expansion after QA APPROVE. New questions (5m domain, TWO_SIDED, vol_ratio
  retune, grid-adjacent structures) = new designs. A 4th CLS-EPISODE CAL cycle, if ever
  needed, requires family-wise correction or doubled confirm bank (pin caveat 3).

## 16. Kill / park rows honored (family card §8)

Entire binding mass sub-breakeven pre-search → park. Noise-like under binder / only
cadence-print artifacts → negative outcome row at checkpoint. Meme-alt spread undecidable
(t1_undecidable everywhere, no T2 path) → park, don't book. Cannot emit causally or pin
costs → park.
