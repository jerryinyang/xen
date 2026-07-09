# EXP-014b — CF-MR-004/HYP-003: S8 streamlined rerun (symmetry availability, 2 domains, both-leg)

**Family:** CF-MR-004 (REGISTERED) · **Phase:** 004 · **Hypothesis:** HYP-003 · **Type:** availability +
tradability screen (co-primary), TRAIN. **Classification:** **PRICE-PRIMARY** (in-engine native orders, m1
fills; L-01/P-09). **Slots/reads:** 0 candidate slots, **0 counted TEST reads** · **Holdout:** final-30%
sealed; first-49% TRAIN. Frozen referee — **never tuned** (L-12). **Origin:**
`checkpoints/2026-07-01-004-cross-domain-mr-renewal/amendment-003-streamlined-s8-symmetry-control.md`
(supersedes the amendment-002 EXP-014b results — archived). Reads: prior `design.md`/`audit.md` and
`.ignore/temp/dumps/{audit-2, finding-availability-control-degenerate.md}`.

## 1. Falsifiable question

*On S8 (basket−RollingMedian₉₀), at 1h and 4h, does a cross-instrument MR outlier (|z|≥2) revert toward the
anchor **beyond a coin flip** (availability, symmetry two-barrier, null=0.5) — and does any single-leg
(moving-mean exit) or both-leg (dual-side capture) configuration produce a net-positive per-stratum edge under
the frozen referee (tradability)? Conditional on trend/vol regime, and how does the read change 4h→1h
(sparsity)? If not, **which leg / domain / regime fails, where?***

## 2. Scope

| Field | Value |
|---|---|
| Series | **S8 only** — `S = (logP^A − Σ(1/n)logPᵢ) − Median₉₀(·)`, equal-weight class basket, W=90 domain-bars. Invertible `P^A=(ΠPᵢ^wᵢ)·e^(S+Cₜ)`. |
| Cells | 11: FX {EURUSD,GBPUSD,USDJPY,USDCHF,USDCAD,AUDUSD,NZDUSD}, IDX {USTEC,US500,US2000,JP225}. |
| Baskets | FX: other 6 majors (equal weight). IDX: other 3. Min-mate rule: full class membership present at exact `CloseTime` or **arm no new order** (no β/anchor drift). |
| **Domains** | **1h and 4h** (decision domains). m1 fill resolution unchanged. Windows domain-bar-native (`WZ=200`, `MedianW=90`, `Z*=2.0`) at both — identical structure, wall-clock differs (isolates the sparsity effect). |
| Stratum | **(cell, domain, arm, z\*)**, per-stratum binding (L-03); pooled = disclosure-only. |
| Time range | Full 5-year; first-49% TRAIN fence (`AnalysisEndUtc` = same UTC timestamp both domains). Final-30% **never loaded**. |
| Exclusions | S5/S6/S7 dropped; 15m/5m/1D out; no S recalc; no counted TEST read; no holdout. |

## 3. Configurations (matrix)

| Axis | Values | Emission? |
|---|---|---|
| Domain | 1h, 4h | 2 |
| Cell | 11 S8 | 11 |
| **Deviation magnitude z\*** | **2.0 (faithful default) / 1.5 (aggressive, less-extreme)** — entry band=z\*·σ; reentry ladder={z\*, z\*+0.5, z\*+1.0} | 2 |
| **Single-leg** exit | moving-mean form-2 (refresh) + form-1 (no horizon) | fixed |
| Reentry (single-leg) | none / allow / extend, **R only** | 3 |
| **Both-leg** (2 entry sub-axes) | short A + long equal-weight basket, joint form-1 exit, reentry=none. **limit** = rest limits on all N+1 legs, cancel-on-partial (faithful, desync=disclosure); **market** = market-fill all legs on the spread trigger (clean group, no desync) | 2 |
| Conditioners | trend-strength (**per-cell tercile**, §6) + vol-regime **per-bar columns → Python slices** | 0 (slice) |

Emissions = 2 domains × 11 cells × (3 single-leg + 2 both-leg) × 2 z\* = **220 native runs**.
**Binding PRIMARY = single-leg `none`, z\*=2.0.** Availability read once per (cell,domain) from the PRIMARY
`none` z\*=2.0 emission at both outlier thresholds |z|≥{2.0,1.5} (the emitted `Z` is band-independent —
verified byte-identical across z\* emissions, so no separate availability emission per z\*). allow/extend,
both-leg (both sub-axes), z\*=1.5, and conditioner slices = disclosure.

## 4. Availability — symmetry two-barrier first-passage (NEW; replaces the degenerate control)

Per outlier event `i` (`|z_lag[i]| ≥ 2`, decision inputs `≤ t-1`, **real intrabar Low/High** only):

- fade side `s = sign(dev_lag[i])`; entry ref `o = open[i]`; dislocation `D = |o − anchor_lag[i]| > 0`.
- **Inward** barrier = the anchor (distance `D` toward the mean). **Outward** barrier = `o + s·D` (distance
  `D` *away* from the mean).
- Horizon `H = min(H_cap, ⌈3·HL_lag[i]⌉)` **domain-bars**. First-passage **race** over `low[i..i+H-1]`,
  `high[i..i+H-1]`:
  - short (`s>0`): inward if `Low ≤ anchor`; outward if `High ≥ o+D`.
  - long (`s<0`): inward if `High ≥ anchor`; outward if `Low ≤ o−D`.
  - **earlier bar wins**; same-bar-both = *ambiguous* (drop; report rate); neither within `H` = *censored*
    (report rate).
- Per stratum (cell,domain): `p_inward = inward_first / (inward_first + outward_first)` over **decided**
  events. **Null = 0.5** (driftless symmetric-barrier first-passage; gambler's-ruin symmetry).
- **Availability holds ⇔ `ci_low(p_inward) > 0.5`** — bootstrap over events (resample decided events,
  `n_boot ≥ 10 000`), per stratum. Disclosure companion: continuous `frac_recovered_inward − outward`.
- **Slices:** partition events by trend bucket {counter-trend, with-trend, neutral} and vol tercile
  {low,mid,high}; recompute `p_inward` per slice (does availability live in a subpopulation).
- This read is **exit- and position-agnostic** — computed once per (cell,domain) from the `none` emission's
  per-bar OHLC/Anchor/Dev/Z/Hl; independent of the tradability arm.

**Availability leak tripwire (binding, cross-instrument specificity):** **peer-feed phase-shift** — recompute
the spread with a phase-decorrelated basket, re-identify outliers, re-run the two-barrier. `p_inward` **must
collapse to ≈0.5** (`ci_low ≤ 0.5`); survival ⇒ the "reversion" is the traded instrument's own auto-reversion,
not a cross-instrument edge ⇒ **REJECT** (S8 construction adds nothing). **Disclosure structural check:**
time-reversal (backward window `[i−H+1..i]`) `p_inward ≈ 0.5`.

## 5. Tradability — frozen referee (untuned, L-12), per (cell,domain,arm)

Per-domain-bar realized **net** series (engine exact m1 fill, intra-position MTM L-09, RT cost once/entry from
the frozen per-instrument **per-domain** cost map; **both-leg sums all N+1 legs**) → frozen
`referee_pstar.gate_stack_pstar` (domain∈{1h,4h}, q\*=0.75), per stratum. Censored `open_at_end` legs excluded
(RealizedBps NaN), disclosed as survival count + MTM. **Primaries:** single-leg `none`, and both-leg.
allow/extend disclosure.

**Both-leg exit/cost/MTM semantics (pinned):** the position is one **spread** position realized on N+1
instruments. Entry: on the S8 spread extreme, short A **and** long each basket mate (equal weight), armed at
the precalc levels (dual-side). Hold as a unit. **Exit:** joint **form-1** — when the spread reverts through
the mean (`sc = spread − anchor` crosses 0), close **all** legs at the next domain-bar open (open-to-open).
form-2-at-mean coincides with form-1 for the joint spread, so form-1 is the sole exit. MTM = summed per-leg
dir-signed return each bar; net = summed realized over all legs minus each leg's RT cost. (The per-leg
*separate* fixed-limit variant is more complex and **deferred** unless both-leg-form-1 shows promise.)

## 6. Conditioners (predeclared, informative-not-gating, L-12)

- **Trend** (traded instrument, per domain): `trend_z = (EMA₂₀ − EMA₅₀)/σ_close(WZ)`; direction=sign.
  Strength band is **per-cell data-driven** — "strong" = `|trend_z|` in its **top tercile** for that
  (cell,domain) (amendment-003 fix: the inherited fixed `≥1.0` was miscalibrated — `|trend_z|` caps <1
  because σ_close(200) is trend-inflated, structurally emptying the counter/with-trend slices). Matches
  the vol-regime tercile approach; adapts to each instrument's scale. Counter-trend = fade side opposite
  to trend direction, within the strong-trend tercile.
- **Vol regime:** tercile of current spread-σ over the trailing 500 domain-bars {low,mid,high}.
- Emitted per bar; Python slices on **both** availability events and tradability bars.

## 7. Power / multiplicity

- **Availability power:** decided-events floor — UNPOWERED if `decided_events < 30` (proportion CI too wide to
  resolve 0.5 vs ~0.6); never FAIL. (1h expected far above floor; a key sparsity read.)
- **Tradability power:** frozen per-domain `min_state_count` (**4h=8, 1h=20**; governs, L-12). Per-admitting-
  cell **bite-check** (planted +Δ must be detected; **scoped per admitting cell** — F2 fix), else UNPOWERED.
- **Multiplicity:** S8 only ⇒ strata = 11 cells within each (domain, arm, z\*) family. **Cross-cell Holm**
  per (domain, arm, z\*). The binding family is (domain, `none`, z\*=2.0) — 11 cells × 2 domains. Domains
  booked as **separate families** (sparsity comparison = disclosure). Reentry, both-leg (both sub-axes),
  **z\*=1.5**, conditioner slices = disclosure axes; a disclosure variant that flips the verdict becomes a
  follow-up primary with its own multiplicity (not booked here).

## 8. Cost (binding, L-02)

Frozen per-instrument **per-domain** `cost_bps` (referee map) on every completed round-trip → net. Both-leg
charges **each** of the N+1 legs. Disclosure: `{0.5,1,2}×`, limit-favourable. MTM intra-position per domain-bar.

## 9. Emission (rich; extend existing schema)

Per bar (both domains): armed sell/buy levels, σ, moving anchor px, spread, z, β, basket mate count + gap,
trend z/dir/strength, vol regime, breach-skip (≤t-1-close + live), MTM bps, refreshed form-2 level, form-1
flag. Per trade (`cis_trades`): entry/exit fill+time, dir, ladder level, exit reason {form1_reversion,
form2_favorable_limit, open_at_end}, bars held, realized bps, MAE/MFE, censored, entry z/spread/anchor/σ,
entry trend/vol. **Both-leg:** tag each leg's symbol (`LegSymbol`) + a `SpreadPositionId` grouping N+1 legs, so
Python can aggregate the joint position and split per-leg P&L. All `≤ t-1`; `CloseTime`/`SourceCloseTime`;
forming-bar OHLC never read.

## 10. Interpretation criteria (predeclared, frozen before outcome contact)

| Outcome | Condition |
|---|---|
| **Availability-CONFIRMED** (per stratum) | `ci_low(p_inward) > 0.5` AND collapses under peer-feed phase-shift (→≈0.5). Report which cells/domains/regimes; note 4h→1h change. |
| **Tradable-on-TRAIN** | Availability-CONFIRMED on a cell AND that cell's frozen-referee **net ci_low>0** (cross-cell Holm) AND per-cell bite-check detects the plant AND net collapses under phase-shift. → **operator-gated counted TEST read.** |
| **Not-tradable (credible)** | Availability may hold, net fails the powered majority (capture-vs-cost/dispersion wash). |
| **Availability-NULL** | `ci_low(p_inward) ≤ 0.5` on the powered majority → the S8 outlier does not revert beyond chance → reinforces retire of the fixed-parameter cross-instrument thesis. |
| **Inconclusive / UNPOWERED** | decided-events<30 (availability) or referee episodes<min_state(domain) (tradability), per (cell,domain) → UNPOWERED, never FAIL. |
| **REJECT** | availability **or** net survives peer-feed phase-shift → leak. |

**Per-leg reporting mandatory** — a null names exactly which leg/domain/regime failed, never a pooled wash.

## 11. Complexity budget

Tests: symmetry availability + frozen referee + peer-feed phase-shift tripwire + per-cell bite-check = **4**.
Plots (≤5): `p_inward` per cell×domain (vs 0.5); net-vs-gross per cell×domain; exit-leg split; availability
by trend×vol heatmap; single-vs-both-leg net. Code: C# native block (domain-parametrise + both-leg +
moving-mean exit + comment fix) + Python (symmetry control rewrite, per-(cell,domain,arm) adjudication,
slices). Within envelope.

## 12. Implementation safety (for experiment-developer)

- **Domain-parametrise the native block**: `DomainMinutes ∈ {60,240}`; `_nativeDomain = DomainLabel(...)`;
  `MarketData.GetBars(TimeFrame.Hour|Hour4)`; `AddMinutes(DomainMinutes)` everywhere; basket feed fetches
  mate bars at the matching TimeFrame; referee domain string threaded. Relax the `==240` assertion.
- **Single-leg exit = moving-mean**: force refreshing form-2 (drop the fixed/`_trail` split); form-1 unchanged;
  **no horizon** (remove/neutralise dormant planner horizon; **fix stale comments** — W3).
- **Both-leg**: multi-symbol order mgmt (short A + long each mate, equal weight), joint spread-reversion exit,
  per-leg fills → `SpreadPositionId`/`LegSymbol` emission; cost sums all legs.
- **Symmetry control (Python)**: two-barrier first-passage per §4 (reuse `measure_entry(reverse=)` for the
  time-reversal check); bootstrap CI vs 0.5; per-(cell,domain) + slices.
- **Audit fixes**: F1 per-stratum UNPOWERED labeling; F2 per-admitting-cell bite scope.
- **Causality/holdout/perf**: ≤ t-1, open-to-open, forming-bar OHLC unread, `HoldoutFence.AssertCanEmit`,
  streaming O(1)/O(n), bounded buffers, append-only parquet. No perf shortcut may break causality/denominators/
  metric defs/streaming.

## GATE: APPROVE (orchestrator inline pre-exec, 2026-07-02)

**Control fix (the core).** The degenerate dislocation-matched control (signal-vs-signal pool) is replaced by
the **symmetry two-barrier first-passage** (null=0.5, self-contained, holds the outlier fixed) — the valid
"does it revert beyond a coin flip" test. Binding availability = `ci_low(p_inward)>0.5`. ✓

**Exit faithfulness.** Single-leg exit = moving-mean form-2 + form-1, **no horizon** (audit W3 comment fix
required). The fixed entry-referential limit is dropped (M1: can't capture peer-side reversion). Both-leg is
the structural answer to M1, pinned to a joint-spread form-1 exit with all-leg cost (L-02). ✓

**Leak tripwire (L-01).** Peer-feed phase-shift is binding on **both** reads (availability p_inward→0.5 AND
net→gone); per-cell bite-check gates non-vacuity (F2 scope fix). Time-reversal disclosure. ✓

**Frozen/holdout/reads.** Referee untuned (1h+4h both frozen; per-domain min_state governs); holdout sealed;
0 counted reads, 0 slots; CF-MR-004 REGISTERED. ✓

**Multiplicity.** S8-only ⇒ per-(cell,domain) strata, cross-cell Holm per (domain,arm); domains separate
families; reentry/both-leg/conditioners disclosure. No scope creep beyond the operator change-set. ✓

**Status:** READY for Stage 2 (Implement — `experiment-developer`). **Credentialed cTrader-CLI run
(88 emissions × 2 domains, both-leg N+1 legs) is operator-gated** (cost/ETA — smoke one 4h + one 1h cell,
validate symmetry inputs + both-leg emission + schema, then the full matrix).
</content>
