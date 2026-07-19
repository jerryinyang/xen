# XENA-EPSOSC-002 — CF-EPSOSC-001 (Bybit VOLARM episode-fade, mass-aligned RET_ANCHOR)

**Lane:** XENA (default) · **Family:** CF-EPSOSC-001 · **Status:** FROZEN 2026-07-18 —
operator decisions RESOLVED (§16, all 3 recs accepted); all TODO(freeze) resolved from
DATA (see `results/{universe_manifest,stage_bands,freeze_diagnostics,power_table,
pre_search_gross_floor,golden_traces_spec}.json`). Ready for fresh-context QA + execution
gate. Holdout (final-30%, 2025-01-08→) CONFIRMED SEALED — never queried at freeze.
**Predecessor:** XENA-EPSOSC-001 (formal top-1 REJECT-class, leak collapse 0.395; only AKRO
dual RET_ANCHOR survived at 0.612 on a single-symbol drift pedestal).
**Active CAL pin (unchanged):** `python/experiments/INFR-015/results/bybit_pc_frozen_registry.json`
sha256 `abbb184229236a75f624537ca605668a73f6f85138c150e14a3609c4191bf786` — CLS-EPISODE, LOW
only, n_legs_floor F*=16, block_legs=episode_overlap_rule_v1, stage-1 g_net, α̂ priced ≤ ~0.06.

> **Skeleton scope.** This carries the four Tier-C structural fixes from 001's analysis and
> leaves TODO markers where a value must be computed from data at freeze time (never recalled).
> The pinned binder, thresholds, and band fractions are **cited, never re-derived** (L-12).

---

## 0. Why 002 exists — the four fixes (each traces to a 001 defect)

| # | 001 defect (evidence) | 002 fix | Mechanism |
|---|---|---|---|
| 1 | Search band 2021-06→2022-06 **predated VOLARM mass** (~2022-07+); 38% of cells 0 legs; only 18/29 symbols contributed | **Re-anchor TRAIN start to the mass**, so the pinned 50% search fraction lands ON the mass | §5 |
| 2 | HYBRID (time-cap) top-1 was **drift, failed tripwire**; RET_ANCHOR was the only survivor | **RET_ANCHOR-only grid** — drop HYBRID entirely | §4.2 |
| 3 | Winner = fragile **single-symbol n=25 singleton**; median-fold rule crowned it | **Portfolio-subset search bias**: min subset size K≥3, target pooled n≥50; disclose singleton finalists but do not certify them | §4.3 / §10 |
| 4 | Single-symbol AKRO 2023 downtrend → **directional-drift pedestal** floored derangement collapse (~half the "edge" survived) | **Cross-symbol subsets required + drift-twin control pair** (matched-drift twin vs coin-flip twin) to isolate and subtract the drift-carry component | §7 |

None of these loosens the pinned binder; all four operate on the **universe/substrate/control**
layer the design owns.

## 1. Question + mechanism

**Falsifiable question.** With the search band aligned to the VOLARM mass and the grid
restricted to endogenous-clear (RET_ANCHOR), does a **cross-symbol** portfolio (K≥3, pooled
n_legs ≥ 16, target ≥ 50) certify under the pinned CLS-EPISODE binder (stage-2 gross LCB > 0),
AND does its edge survive the derangement tripwire **after** the directional-drift pedestal is
subtracted (drift-adjusted collapse ≥ 0.5)?

```
MECHANISM: unchanged from 001 — after a confirmed vol-expansion-armed stretch (ATR(14)[t−1] /
  ATR(14×4 slow)[t−1] ≥ 1.25 AND |RealClose[t−1] − rolling-median-anchor(W)[t−1]| / ATR(14)[t−1]
  ≥ k), price reverts toward the anchor WITHIN the episode; harvest as a one-sided market-entry
  fade cleared ENDOGENOUSLY (return-to-anchor only — no time cap). P&L object = the EPISODE.
  002 refinement: the tradable regularity must be the SIGNAL-conditioned reversion, separable
  from unconditional single-name drift. A subset whose edge is drift (survives derangement)
  is REJECT-class by construction here, not merely disclosure.
DERIVED: estimand = gross open-to-open bps/episode via xen.adjudication episode objects (L-16);
    portfolio functional = pinned g_gross_ratio on admitted legs.
  null = pinned CLS-EPISODE battery + episode-label derangement destroy (drift-adjusted, §7).
  horizon = endogenous clear (RET_ANCHOR) only; episodes ≤ 48h by construction at 15m×W≤192.
  test = pinned two_stage_sample_split, block_legs = episode_overlap_rule_v1, n_legs_floor 16.
```

## 2. Object identity declarations

```
OBJECT-IDENTITY:
  measurement object == trading object: YES — both the EPISODE (market entry at open of bar t
    after confirmed armed-stretch → path → within-episode RET_ANCHOR clear); single-name,
    one-sided, single-leg; adjudicated from positions_ledger. L-16 episode-native.
  measured conditioning event == traded entry event: YES — arm+stretch on CONFIRMED bars ≤ t−1;
    capital committed next 15m bar open, market order; NO limit entries (limit_entry_cells=false).
  effect-splitting windows non-overlapping: YES — no new entry on an arm while its episode is
    open; episodes within a candidate disjoint in time. B-9.
```

## 3. Estimand

- Unchanged from 001: `xen.nautilus.adjudication_shim` → `xen.adjudication` episode objects;
  gross open-to-open bps entry-open→exit-open, sign = fade direction. Emission contract v1;
  finite synthetic `SlPrice = EntryFill − side × 1.0 × k·ATR(14)[t−1]` (sizing denominator).
- Estimand gate v2 must pass before ANY read; L-29 anchor (`EntryFillPrice == next-bar RealOpen
  ± 1 tick`). Censoring disclosed; >20% flagged.

## 4. Universe manifest

### 4.1 Instruments — causal online membership (unchanged rule, refreshed axis)

- Same code-asserted causal membership gate (top-10 trailing-24h volume at t−1, daily 00:00
  UTC rebalance, delisted included, rule_hash `0dd53037…`).
- **Symbol axis (FROZEN):** all symbols with ≥90 membership-days **within the 002 TRAIN
  window** [2022-07-01, 2023-12-18]. Computed by re-slicing 001's window-independent daily
  top-10 membership (rule 0dd53037…) to the shifted window ⇒ **19 symbols** (152 binding
  cells). Prediction confirmed: 10 early-only 001 names DROPPED
  (EOS/MATIC/LUNA/XEM/FTM/SRM/OMG/KEEP/CELR/10000NFT). 002 axis ⊆ 001 axis (asserted).
  Axis: SHIB1000, AKRO, GALA, DOGE, SPELL, 1000BONK, DENT, HOT, 1000PEPE, 10000LADYS, RSR,
  LINA, SLP, JASMY, STMX, REEF, 1000BTT, LEVER, FITFI. Authoritative in
  `results/universe_manifest.json`.

### 4.2 Candidate grid — RET_ANCHOR only (fix #2)

| Axis | Values | n |
|---|---|---|
| Object | VOLARM only (vol_ratio 1.25 fixed) | 1 |
| Domain | 15m LTF only | 1 |
| Anchor window W | 96, 192 | 2 |
| Threshold k | 2.5, 3.0 | 2 |
| Clear | **RET_ANCHOR only** (HYBRID dropped — 001 showed its edge was drift) | 1 |
| Side | LONG_ONLY, SHORT_ONLY | 2 |

Variants = 2×2×1×2 = **8 per symbol** (was 16). Binding cells = 8 × (002 axis size).
**No STRETCH/1h disclosure arm in 002** (001's was never emitted; drop to hold complexity).

### 4.3 Portfolio-subset search bias (fix #3)

- **Minimum subset size K ≥ 3 distinct SYMBOLS** enters the certified-subset constraint (not
  just K≥3 cells on one symbol). Rationale: 001's fragile winner was 1 symbol; pooling legs
  across symbols is the pinned power path (design-001 §10) AND the drift-decorrelation path (#4).
- Singleton / single-symbol subsets **still enter the search** (XENA no-per-candidate-gate
  principle) but are **disclosure-only**: they cannot be the certified one_subset top-1.
  **RESOLVED (freeze):** `xen.xena.certify.certify_and_rank` exposes `subset_size` (cell
  count) but **NO min-distinct-symbol param** — so the K≥3 distinct-SYMBOL constraint is
  enforced as a **predeclared post-rank filter** applied after `certify_and_rank`, before any
  gate spend (**AMENDMENT-1 TIGHTER**, §15). No binder threshold re-derived.
- Target pooled n_legs ≥ 50 on the stage-2 band (F*=16 floor still the hard pin; ≥50 is the
  design's power target, disclosure).

## 5. Temporal mapping — mass-aligned bands (fix #1, THE core change)

- **Constraint:** the pinned band fractions (search 0.5 / ranking 0.25 / embargo 0.2 → stage-2)
  are **immutable**. 001 applied them to TRAIN 2021-06→2023-12, so the 50% search band ended
  before the ~2022-07 mass. 002 fix = **shift the TRAIN window start forward to the mass onset**
  so the same 0.5 fraction lands on populated data.
- **RESOLVED (freeze) — TRAIN_START = 2022-07-01, TRAIN_END = 2023-12-18** (fence
  `train_end_utc`, UNCHANGED). Predeclared **X = search-band binding-cell coverage ≥ 0.80**
  (zero-leg ≤ 0.20). Verified on the pinned search band: **coverage 0.842 → PASS**
  (`freeze_diagnostics.json`). Pinned `SegmentLayout` (0.5/0.25/0.2) on [2022-07-01,
  2023-12-18]:
  - search  = 2022-07-01 → **2023-01-31**  (on the plateau)
  - ranking = 2023-01-31 → **2023-05-18**
  - stage2/gate = 2023-09-02 → **2023-12-18** (embargoed tail)
  - **Global holdout 2025-01-08→ SEALED** (final-30%; never touched). Counted TEST band
    [2023-12-18, 2025-01-08] reserved for the operator-gated final gate only.
- **Data-vs-recall note (ground-in-artifact).** The skeleton recalled "mass onset ~2022-07"
  from pin caveat 4. The emitted 001 data shows raw episode mass is actually present from
  **~2021-11** (72–80 active cells/month). 2022-07-01 is therefore chosen not as the *first*
  populated month but as a **plateau point that separates the search band from the 2021 ramp
  and the 2021/2023 single-name drift regimes** that produced 001's AKRO pedestal (fix #1/#4).
  It passes the predeclared coverage floor. Full monthly mass table in `freeze_diagnostics.json`.
- **Power tradeoff (realized):** shorter TRAIN ⇒ 19 symbols (vs 001's 29). Mitigated as
  designed — stage2 gate band is cross-symbol (top-3 = SHIB1000/SPELL/10000LADYS, pooled
  501 legs; AKRO now mid-pack at 63, NOT the top). Numbers in §10.
- Catalog pin `35d3375e…`; UTC boundaries in `results/stage_bands.json`, immutable.

## 6. Costs + pre-search floor

- `bybit_round_trip_cost_bps_v1` (taker + spread + funding × episode hold_hours). **Per-symbol
  spread RESOLVED (freeze): NOT measurable on T1** — the OHLCV-only catalog carries no
  pseudo-quote series; INFR-014 `cost_pins` pin **GAP 5.0 bps** for synthetic TRAIN banks;
  per-symbol medians deferred to pilot/T2 (consistent with §12 `t1_undecidable → AWAITING_MBP`).
- Pre-search gross floor (disclosure, `pre_search_gross_floor.json`): **135/152 cells above
  breakeven**, median gross **113 bps/episode** vs cost **18.5 bps** — entire-mass NOT
  sub-breakeven → **PROCEED**. Funding stress ladder 1×/2× on finalists.

## 7. Controls — drift-twin PAIR (fix #4, the deep one)

The 001 tripwire could only reach collapse 0.395–0.612 because a **single-symbol short in a
2023 downtrend carries an unconditional drift** that derangement cannot destroy. 002 isolates
and subtracts it with the codified drift-twin pair (KB L-19 "How to apply" (4)).

```
CONTROL DRIFT-TWIN-PAIR (per certified finalist subset, analysis stage):
  question answered: how much of the subset's gross bps/episode is SIGNAL-conditioned reversion
    vs unconditional single-name directional drift (the pedestal that floored 001's collapse)?
  population:
    (a) MATCHED-DRIFT twin — same symbols, same side, same episode count + duration profile,
        RANDOM entry times (decoupled from arm/stretch); E[gross] ≠ 0 by design = the drift
        carry benchmark. 25+ seeds, regenerable, byte-diff at QA.
    (b) COIN-FLIP twin — same schedule, side randomized per episode; E[gross] = 0 analytic null.
    DISJOINT from signal population: entry timing (and, for (b), side) decoupled from the event.
  drift-carry estimate = median gross of twin (a); signal component = live − twin(a) median.
  bite/MDE: seed battery percentile of live vs each twin; MDE per subset (L-19 seed battery).
  non-vacuity: random timing / side moves the MEAN bps/episode directly (B-6).
  expected if H true: live ≥ P95 of BOTH twins AND (live − matched-drift) > 0 with ci_low > 0.
  expected if H false (drift-only): live ≈ matched-drift twin; live − twin ≈ 0.
  disclosure: collapse fraction AND drift-adjusted collapse per subset.
  destroy form: independent random draw (not permutation) — L-28 n/a; percentile read.

CONTROL GRID-SHAPE IDENTITY (disclosure): unchanged from 001 — no hard cap / banded rebalance
  in the traded object; QA code-inspection clause (P-12 escape via within-episode clearing).
```

## 8. Leak tripwire — drift-adjusted derangement (fix #4 integrity leg)

```
TRIPWIRE: episode-label DERANGEMENT (alignment destroy), now DRIFT-ADJUSTED.
  Construction: as 001 §8 — derange episode start-time assignments (zero fixed points, L-28;
    duration + side preserved, slot separation ≥ max episode duration), re-adjudicate on real
    prices. 200 seeds.
  HARD rule (002): raw collapse ≥ 0.5 REMAINS required, AND the SIGNAL-CONDITIONED component
    must survive: (live_mean − matched_drift_twin_median) must collapse ≥ 0.5 under derangement.
    A subset whose signal component does NOT collapse = leak/artifact → REJECT, no override.
    A subset whose RAW edge is all drift (live ≈ twin) is REJECT-class here (was disclosure in 001).
  vacuity check: derangement moves the mean; drift subtraction removes the un-destroyable pedestal.
  Cross-symbol requirement (§4.3) structurally lowers the shared-drift pedestal (decorrelated
    single-name drifts partially cancel in the pooled mean).
  derangement = YES (zero fixed points; L-28).
```

## 9. Interpretation bands (per stratum = subset; no binaries)

```
BANDS (informative except integrity):
  SUPPORTED:    stage2 gross LCB > 0, pooled n_legs ≥ 16, K ≥ 3 symbols, AND net leg
                g_net LCB > 0 under fees+1×spread+funding (L-22), AND drift-adjusted collapse
                ≥ 0.5 (§8), AND live > matched-drift twin ci_low>0 (§7).
                SUPPORTED-GROSS reported separately as selection-machinery only.
  WASH:         |live − matched-drift twin| < battery noise scale (drift-only; A≈B).
  CONTRADICTED: gross UCB < 0 on a powered subset.
  UNPOWERED:    pooled n < F07 floor (MDE ≤ shrunk TRAIN effect) — never a negative.
POOLED-UNIVERSE: disclosure-only. Single-symbol subsets: disclosure-only regardless of band.
  True α ≤ ~0.06 stated alongside every gate result (pin caveat 1).
```

## 10. Power statement

```
POWER (VOLARM 15m RET_ANCHOR, MASS-ALIGNED window — FROZEN on 2022-07+ shifted TRAIN,
  from power_table.json; in-window re-slice of 001 emissions, disclosure):
  in-window episodes total: 7406 across all 152 cells.
  stage2 GATE band (2023-09-02 → 2023-12-18) legs, top symbols:
    SHIB1000 176 · SPELL 166 · 10000LADYS 159 · LEVER 152 · 1000PEPE 141 · 1000BONK 138 ·
    STMX 126 · GALA 119 · FITFI 119 · AKRO 63 · SLP 56 · DOGE 30 · ...  (AKRO no longer top)
  single cells reaching F*=16 on stage2: 42 of 152.
  pooled projections: top3 = 501 legs, top5 = 794 — both ≫ n≥50 target and F*=16 floor.
  F* = 16 hard floor (pin); design target pooled n ≥ 50 via K≥3 cross-symbol subsets — MET.
  MDE (σ≈150 bps): n=16 ≈ 75 bps · n=50 ≈ 42 bps · n=100 ≈ 30 bps · top3-pooled ≈ 13 bps.
    (drift-adjusted signal is SMALLER than raw, so target n≥50 — not the floor — is deliberate.)
  strata predeclared UNPOWERED: subsets < F* pooled; single-symbol subsets (disclosure);
    late-listed symbols with 0 search-band legs (LEVER/10000LADYS/1000PEPE search=0 but large
    stage2 — searchable only where they have search-band mass; disclosed).
```

## 11. Screen-effect conversion pin (L-21)

Unchanged from 001 §11 — native bps, no ATR divisor on the promote facet. **RESOLVED
(freeze):** cost floor = **18.5 bps/episode** (fee 11.0 + GAP spread 5.0 + funding ~2.5 at
~20h hold); per-symbol spread not measurable on T1 (§6). Median gross 113 bps ≫ floor.

## 12. T1 spread-scale routing

Unchanged from 001 §12 — per finalist, before any verdict-bearing read; meme alts likely
`t1_undecidable: YES` (no T2 path → park). Pooled T1 reads disclosure-only.

## 13. Golden-trace spec (QA derives; developer must not generate)

**RESOLVED (freeze):** 3 concrete in-window, in-axis anchors written to
`results/golden_traces_spec.json` (SPEC only — QA independently DERIVES expected values;
developer must NOT generate). T1 = SPELL W96 k2.5 RET_ANCHOR_S entry 2022-07-10 11:01Z →
endogenous clear 14:31Z (3.5h); T2 = SPELL W192 longest-hold episode → verify segment/censor
end, NOT a time cap (HYBRID gone); T3 = SPELL arm on 2023-06-28 (SPELL OUT of top-10) → NO
entry. Each carries the causal/L-29/SlPrice invariants QA must check.

## 14. Integrity vs informative split

```
HARD (block): tripwire collapse — RAW ≥0.5 AND drift-adjusted signal ≥0.5 (§8); holdout fence;
  causal provenance (≤ t−1 features + membership; non-STUB fence); estimand reconciliation
  (gate v2); pin hash abbb1842…; cadence/floor attestations; SlPrice finiteness; P-12 structure.
INFORMATIVE (operator judges): all effect sizes, LCB/UCB, battery percentiles, collapse
  fractions (raw + drift-adjusted), funding stress, floor tables, net deployability. No
  auto-verdict thresholds. Gate spend + final verdict = operator gates.
```

## 15. Complexity budget + amendments

- Stat machinery: pinned binder + drift-twin pair + derangement — no NEW tests, no new
  accounting. New code vs 001: RET_ANCHOR-only grid (subset of existing strategy), shifted-window
  manifest builder, drift-twin generator in `analysis_code/`, min-distinct-symbol post-rank filter.
- Grid SHRINKS (8/symbol vs 16); complexity down.
- Amendment ledger (L-23): running **0 L / 1 T / 0 N**.
  - AMENDMENT-1 (TIGHTER, 2026-07-18, operator decision §16.2): certified one_subset must
    contain ≥3 DISTINCT symbols — post-rank filter after `certify_and_rank` unless the pin
    natively supports the constraint. Tightens the certifiable set; no binder threshold changed.
  A one-directional streak is not yet ≥3; no operator flag triggered. **Freeze check (L-23):**
  AMENDMENT-1 is uni-directional TIGHTER (post-rank filter only REMOVES qualifiers, K≥3
  distinct symbols) ⇒ it cannot raise the expected false-qualifier count; net effect on the
  certifiable set is monotone-shrinking. Ledger stays 0 L / 1 T / 0 N.
- No scope expansion after QA APPROVE. A 4th CLS-EPISODE CAL cycle (if the pin itself needs the
  median-fold-vs-robustness fix surfaced in 001 §6) requires family-wise correction / doubled
  bank (pin caveat 3) — OUT of scope for 002; logged for INFR/CAL.

## 16. Operator decisions — RESOLVED (2026-07-18, all recommendations accepted)

1. **TRAIN_START = mass-aligned shift, ACCEPTED.** TRAIN_START set to VOLARM mass onset
   (candidate **2022-07-01**; exact value = §5 TODO(freeze) computed from the axis, must land
   ≤ the first month with ≥X populated binding cells). Total-episode cost accepted; power table
   §10 must be recomputed on the shifted window before freeze.
2. **K≥3 distinct-symbol = post-rank filter, ACCEPTED** (unless the pin natively supports a
   min-distinct-symbol constraint — §4.3 TODO to confirm). Predeclared, applied after
   `certify_and_rank`, before any gate spend. Logged as **AMENDMENT-1 TIGHTER**.
3. **Drift-adjusted collapse = HARD integrity, ACCEPTED.** §8 binds: a subset REJECTs unless
   BOTH raw derangement collapse ≥ 0.5 AND drift-subtracted signal collapse ≥ 0.5. The drift
   pedestal is REJECT-class, not disclosure.

These are design decisions, not gate loosenings — the pinned binder is untouched.
```
