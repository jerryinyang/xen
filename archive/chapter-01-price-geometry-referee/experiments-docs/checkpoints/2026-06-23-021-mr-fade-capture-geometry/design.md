# Phase 021 — RSI-2 Fade Capture-Geometry & Tradability (CF-MR-001, batch 2)

**Status:** **CLOSED — G-021 ADJUDICATED TRADABLE (2026-06-24).** Phase 021 ran EXP-090→094 (TRAIN) → EXP-093
(one-shot TEST): the bare RSI-2 fade with EXIT-RCT **confirms net-tradable OOS on 8/11 carried cells** (six 4h
mean-AND-median-positive + USTEC-1h/US2000-1h mean-carried) — the programme's first net-positive price entry. See
[`G-021-gate-review.md`](G-021-gate-review.md) and [`retrospective.md`](retrospective.md). 11 counted TEST reads
spent (each carried stratum 0→1); final-30% global holdout never loaded; 0 additional candidate slots. *(History:
OPEN — G0 RATIFIED 2026-06-23, D0 FROZEN; the binding D0-predeclarations + G-021 gate criteria were frozen before
EXP-090 ran.)*

**Family:** [`CF-MR-001`](../../../signal-registry/candidate-families/cf-mr-001.md) — RSI-2 mean-reversion
(fade) entry. **Lever (admitted at G-020):** the **bare RSI-2 fade (CORE)**, intraday.
**Predecessor checkpoint:** [`2026-06-23-020-mean-reversion-entry-availability`](../2026-06-23-020-mean-reversion-entry-availability/G-020-gate-review.md)
(G-020 **ADMITTED**; first candidate slot consumed).
**Slot status:** CF-MR-001's **first candidate slot is consumed** (at G-020). Phase 021 spends counted TEST
reads only at its terminal confirmation, under the 2-lifetime-per-stratum cap.

---

## 0. What G-020 handed this phase (and the scope it forbids)

G-020 admitted **one lever only — the bare RSI-2 fade (CORE)** — on a **TRAIN-only availability** verdict:
favourable `MFE_med` ≈ 0.75 ATR vs ≈ 0.69 random (Δ̂ ≈ 0.06 ATR), positive in ~87% of cells, over an effective
**~3-bar** horizon, **intraday** (15m 16/16, 1h 11/16, 4h 1/14; all 16 instruments). That verdict is
**availability, not tradability**: gross, no exit, no cost. This phase asks the one question G-020 left open.

**Explicitly out of scope (carried from the G-020 routing — not re-litigated here):**

- **The vol-regime partition** — *inert* at the screen (passed only by inheriting CORE's edge). Not a Phase 021
  lever; a low-priority future amendment, if ever.
- **The TREND / RSI-FILTER variants** — *dead-by-absence* (S=0, 1). Mechanistically self-contradicting on a
  fade. Closed; not reopened by re-parameterization.
- **The contrarian arm, the 25/75 regime scheme, regime×variant cross-cuts, parameter tuning, instrument /
  domain expansion** — all **registered-but-deferred** in the multiplicity ledger. **Each requires its own
  dated `D0-amendment-*` and an explicit slot decision.** None enters Phase 021.
- **4h** — dead-by-absence in EXP-089 (1/14). Phase 021 is scoped to **15m and 1h**; 4h is not carried (carrying
  it would reopen a cell the screen found empty). A future frequency-boundary study is a separate scope.

The entry is **frozen as admitted** — `RSI(2)` Wilder, long `RSI₂<10` / short `RSI₂>90` (2 / 10 / 90), inherited
byte-for-byte from the Phase 020 D0 / `xen.mean_reversion`. **No entry re-tuning in Phase 021** (premature-
optimisation prohibition). The only open axis is **capture geometry**: the exit + cost layer.

## 1. The phase question (availability → tradability)

**Does the bare RSI-2 fade's gross ~0.75-ATR / ~3-bar favourable availability survive a real exit rule, net of
conservative cost, as a positive expectancy that clears the frozen referee suite — and does it hold on a
counted TEST read?**

Decomposed into the falsifiable legs each experiment owns (§3). The honest prior, carried from the programme:
**availability ≠ capturable edge.** The short ~3-bar horizon means cost/slippage bite hardest exactly where the
edge lives — this phase is a genuine falsification attempt, not a victory lap. A NOT_TRADABLE outcome closes the
lever (and, with the regime/variants already dead, effectively the family) and returns the programme to the
G-019 non-price frontier; a TRADABLE outcome is the programme's first net-positive price entry.

## 2. Binding gates inherited (not re-derived)

- **Referee suite (binding):** the **frozen qualification suite** — strict gate stack + EXP-012 ratified-loose
  referee + EXP-018 revised incremental/fitness unit — is the binding tradability gate, exactly as it remained
  binding for Phase 018 after G-017 `DISCOVERY_ONLY`. The `ASS` qualifier is **non-binding discovery overlay**
  only (G-017). No new referee is built or tuned in Phase 021.
- **Cost model (binding):** the **EXP-085 conservative round-trip + bar-count financing** model
  (`xen.capgeo_cost`, `xen.financing`), applied unchanged. Costs are not re-estimated to suit the fade.
- **Holdout / TEST discipline:** the final-30% global holdout is **never** read in any screening, training, or
  characterisation. Counted TEST reads (the analysis-TEST stratum, last 30% of the analysis set) are spent
  **only at the terminal confirmation (§3, EXP-093)**, under the **2-lifetime-counted-reads-per-stratum cap**;
  all 48 strata are currently 0/2 open. A *global-holdout* one-shot release (à la EXP-032) is **a separate,
  later gate**, not part of Phase 021.

## 3. Exit families — the capture-geometry slate (native MR pair + conventional contrast)

The operator's concern is correct and is the phase's organizing hypothesis: the **conventional exits are
reactive and bar-close-bound**, which structurally under-captures a fast intrabar reversion. So the slate is
**two native, proactive, intrabar-filled reversion targets** (§3.1 — the primary hypothesis) measured against
the **conventional exits as the falsifiable contrast** (§3.2).

### 3.1 Native MR exits (proactive resting target, intrabar 1m fill) — the primary hypothesis

**EXIT-RCT — Reversion-Completion Target (operator-proposed).**
- *Idea.* Precompute the favourable price at which the mean-reverting **signal** registers reversion complete
  (RSI₂ back to neutral 50) and rest it as a proactive take-profit limit — **not** an exit-on-close.
- *Derivation (RSI Wilder, frozen `n=2`).* At domain bar *t* with Wilder average gain `AG_t` / loss `AL_t`, the
  next-bar price change that returns RSI₂ to 50 is `ΔP* = (n−1)(AL_t − AG_t)`; for `n=2`, **`P*_t = Close_t +
  (AL_t − AG_t)`** for a long (oversold ⟹ `AL>AG` ⟹ `P*>Close`), short symmetric. Recomputed each domain bar
  after entry as the Wilder state evolves → a **trailing reversion-completion target**.
- *Fill.* `P*_t` rests as a limit; filled on the first **1-minute** bar (real OHLC) whose high (long) / low
  (short) touches it. **Honest caveat (frozen in interpretation):** this is a model-derived target *price* — RSI
  is **not** recomputed intrabar; the claim is "price reached the reversion-completion level," and the limit
  fill is realistic. Not a synthetic-price metric — the fill price is real.

**EXIT-ERT — Equilibrium-Return Target (Claude-designed, complementary).**
- *Idea.* Mean reversion *literally* means reversion to a mean, so the native completion is **price returning to
  its local equilibrium**, independent of any oscillator quirk. Target = the local equilibrium reference `M_t`
  (a frozen rolling-mean / EMA of domain `Close` — the same stretch reference that justifies a fade entry),
  rested as a proactive limit and updated each domain bar → a **trailing equilibrium-return target**.
- *Fill.* Identical 1m intrabar touch logic on `M_t`.
- *Why it complements RCT.* RCT reads completion off the **signal** (oscillator-neutralizes; tends nearer /
  faster, consistent with the ~3-bar horizon); ERT reads it off the **price's distance to equilibrium** (tends
  farther / standardized, robust to RSI path-dependence). Measuring both isolates whether reversion is better
  captured from the indicator or from price-to-mean — a genuinely native A/B, not two flavours of the same rule.

**Shared native-exit construction (frozen at D0):**
- **Intrabar 1m fill engine** — timestamp-aligned domain→1m mapping with **causal order-of-touch resolution**
  between the favourable target and the adverse stop (the reason 1m is required: it resolves which barrier was
  hit first *within* a domain bar — exactly the EXP-054 fill-model question, answered with real data instead of
  a worst-case tie-break). One new module (`xen.intrabar_fill`, or an extension of `position_exits`), reused by
  the ATR-barrier arm too. The 1m slice is read **only within the TRAIN region (clip by timestamp at the TRAIN
  edge, never by 1m index)**; real 1m OHLC; the final-30% holdout stays sealed.
- **Adverse side held fixed across all arms** — a frozen ATR-multiple adverse stop + the MR-tempo (~3-bar)
  max-hold with exit-on-cap-close fallback. Holding the adverse side identical across the native and
  conventional arms **isolates the favourable-capture mechanism** (EXP-057 ADV-NONE isolation discipline), so a
  win is attributable to the target, not the stop.

### 3.2 Conventional exits (contrast arms — tested, not expected to dominate)

- **RSI-revert-on-close** — exit at the domain close when RSI₂ crosses 50. The **reactive, non-intrabar analog
  of RCT**: the contrast that quantifies exactly what proactive resting + intrabar fill buys.
- **Fixed-bar** — close at the ~3-bar horizon.
- **ATR triple-barrier** — target / stop, intrabar-filled via the same 1m engine.
- **Favourable partial / trail** — EXP-059 V2A-style, as the existing primitives allow.

## 4. Planned experiments (proposed; IDs assigned, scope frozen at each G0/D0)

The phase follows the established availability→tradability lifecycle (CF-AVWAP-001 Phases 006–013, CF-CAPGEO-001
Phase 018), TRAIN-only until the single terminal TEST read.

| EXP | Role | Reads / slots | One-line falsifiable leg |
| --- | --- | --- | --- |
| **EXP-090** | **Exit-substrate readiness & per-cell inference calibration** (TRAIN-only) | 0 / 0 | The bare-fade exit substrate is constructible and powered on the 15m/1h member cells: event coverage, determinism, and per-cell event-level MDE / FPR-coverage under the frozen referee are established (analog EXP-043/044, EXP-080). Defines the Phase 021 member set; a cell with no finite MDE is excluded with record. |
| **EXP-091** | **TRAIN-only exit / capture-geometry screen** (gross + conservative cost) | 0 / 0 | Over the §3 slate — the **native pair EXIT-RCT + EXIT-ERT** (primary) vs the **conventional contrast** (RSI-revert-on-close, fixed-bar, ATR-barrier, partial/trail) — does any exit clear the frozen floor+margin in a quorum of cells over multiple instruments, **net of EXP-085 cost**, and **do the native intrabar targets beat the reactive contrast** (esp. RCT vs RSI-revert-on-close, the clean intrabar-vs-on-close A/B)? (analog EXP-039/045/056–059). If none clears gross-then-net, the capture lever is empty → G-021 NOT_TRADABLE without spending a read. |
| **EXP-092** | **Per-instrument cost-bearing tradability screen** (TRAIN-only, A1-style sequence) | 0 / 0 | For the surviving exit(s) from EXP-091, which specific (instrument, domain) cells reach a TRAIN-only `SEQUENCE_PASS` (net CI_low > 0 at the predeclared α, power-confirmed)? Produces the **hash-pinned candidate set + Holm rule** eligible for a TEST read (analog EXP-034/083). Necessary-but-not-sufficient for TEST. |
| **EXP-093** | **One-shot TEST confirmation** under the phase Holm + margin rule | **counted reads (≤ cap) / slot already consumed** | Do the EXP-092 candidates confirm on the analysis-TEST stratum under the frozen referee, phase Holm, and margin condition — spending counted TEST reads recorded in `test-read-ledger.md` in the same change (2/stratum cap; all currently 0/2)? The binding tradability read (analog EXP-037/038). |

EXP-091→093 are **conditional**: an empty EXP-091 closes the phase at G-021 with **0 TEST reads spent**; only a
non-empty exit screen advances to the cost-screen and the counted TEST contact. The exact instruments/domains
carried to TEST, and how many reads that costs, are **G0/D0 decisions** (operator-ratified), not fixed here.

## 5. Complexity budget (per experiment; phase-level guidance)

| Item | Budget |
| --- | --- |
| Binding statistical tests | EXP-090 0 (readiness/calibration); EXP-091 ≤ 2; EXP-092 1 (sequence); EXP-093 1 (the binding confirm) + descriptive companions |
| Visualisations | ≤ 4 per experiment |
| New code modules | **Target 1–2.** One justified new module — `xen.intrabar_fill` (the timestamp-aligned domain→1m intrabar fill engine with causal order-of-touch) — required by the §3.1 native targets and reused by the ATR-barrier arm. The two native targets (RCT closed-form from the Wilder state; ERT from the equilibrium reference) are small additions to `xen.mean_reversion` / `xen.exit_rules`. Reuse `xen.capgeo_cost` / `xen.financing` (cost), `xen.expectancy`, the frozen referee (`xen.incremental_referee`, `referee_calibration`), `xen.position_exits` / `xen.capture_barriers` / `xen.third_barrier` / `xen.favourable_targets` / `xen.adverse_targets`, and `xen.wf`. |

## 6. Verdict and routing (G-021 — terminal gate; mechanical rule frozen at G0)

| Adjudicated state | Consequence |
| --- | --- |
| **TRADABLE** (EXP-093 confirms under the frozen referee + phase Holm + margin) | The bare RSI-2 fade is the programme's **first net-positive price entry**. Next: a sanctioned **global-holdout release** decision (separate gate) and/or deployment-readiness; the deferred levers (regime, contrarian, 25/75) become candidate expansions, each under its own slot/D0. |
| **NOT_TRADABLE** (exit screen empty, or TEST fails the margin/Holm) | The fade's availability does not convert to a net edge on this dataset. The lever closes; with regime inert and variants dead, **CF-MR-001 is effectively exhausted**. The programme returns to the **G-019 non-price-data frontier** (operator decision). Reads spent are recorded and permanent; the file drawer retains every cell. |
| **INCONCLUSIVE** (power-limited at the realized counts / TEST CI spans zero, à la EXP-032) | Disclosed; the candidate is neither confirmed nor refuted; any further read is a separate decision under the remaining per-stratum cap. |

## 7. Discipline (binding throughout Phase 021)

- **Real-price outcomes only.** All P&L, expectancy, and exit evaluation on real domain OHLC
  (`RealOpen/High/Low/Close`); HA / brick prices never enter a metric. MR exits resolved causally — only bars
  at/after entry, no look-ahead. The **1m intrabar fill** reads real 1-minute OHLC **within the TRAIN region
  only** (the slice is clipped by **timestamp** at the TRAIN edge, never by 1m index — cross-view alignment is
  by `CloseTime`/`SourceCloseTime`, never bar count); the fill price is a real touched price, not a synthetic
  one; the final-30% global holdout 1m bars are never loaded.
- **No premature optimisation.** The entry is frozen as admitted; no entry/exit parameter is tuned against any
  TEST or holdout data. Exit *selection* on TRAIN is permitted (that is the phase's job); the selection rule is
  predeclared and the TEST read is one-shot.
- **TRAIN-only until the terminal read.** EXP-090–092 read only the TRAIN sub-split; EXP-093 spends counted
  TEST reads recorded in `test-read-ledger.md` in the same change, under the 2/stratum cap. The final-30%
  global holdout stays sealed.
- **Per-stratum doctrine (LESSON-001).** No collapsed cross-cell boolean is binding; pooled counts are
  disclosure, the per-(instrument, domain) reads are the verdict.
- **Deviation handling.** A frozen-design confound is corrected by a dated `D0-amendment-*` + hard-delete +
  full rerun (programme norm), not a silent follow-up.
- **File drawer.** Every exit-family and cell outcome — survives, dies, inconclusive — is retained in the
  registry and the Phase 021 multiplicity batch; a refuted exit is not silently reopened by re-parameterization.

---

## 8. G0 decisions — operator-ratified direction (to be frozen at D0)

The following reflect the operator's 2026-06-23 direction and stand as the working decisions; they are made
**binding** when written into `D0-predeclarations.md` at G0 (no result-producing code runs before that freeze).

1. **Exit family slate for EXP-091 — RATIFIED with the native pair mandated.** The slate is the **two native
   intrabar reversion targets EXIT-RCT (operator-proposed) + EXIT-ERT (Claude-designed)** as the primary
   hypothesis, plus the conventional contrast arms (RSI-revert-on-close, fixed-bar, ATR-barrier, partial/trail).
   **Single frozen parameter point each, no grid** (keeps the multiplicity small, matching the screen's
   discipline). The adverse stop + ~3-bar MR-tempo cap are held **identical across all arms** (favourable-
   capture isolation). D0 fixes: the ERT equilibrium reference (rolling-mean/EMA window), the ATR adverse-stop
   multiple, and the cap fallback.
2. **Cost model — RATIFIED as-is.** The EXP-085 conservative round-trip + bar-count financing
   (`xen.capgeo_cost` / `xen.financing`) is adopted unchanged for the intraday 15m/1h horizon; a faster-turnover
   sensitivity is a disclosed companion, not a re-estimation.
3. **TEST plan for EXP-093 — RATIFIED: smallest defensible set.** Best **1–2 cells per surviving exit** carried
   to a counted TEST read, phase Holm sized to that set, under the 2-lifetime-per-stratum cap (preserve reads
   for any future confirmation). Exact cells fixed at D0 from the EXP-092 hash-pinned candidate set.
4. **Domain scope — RATIFIED: 15m + 1h only.** 4h excluded (dead-by-absence at EXP-089, 1/14); not carried as a
   control (carrying it would reopen an empty cell). A 4h / frequency-boundary study is a separate future scope.

**Parameter values set (FROZEN in `D0-predeclarations.md`, G0-RATIFIED 2026-06-23):** ERT reference =
`wilder_ema(Close,10)`; adverse stop = `2.0×ATR(14)`; hold cap = the reused EXP-089 MR-tempo cap; EXP-091
net-clear `ci_low_1s>0` with a ≥5-cell/≥3-instrument quorum; EXP-092 sequence α=0.05; EXP-093 TEST PASS = Holm-adj
p≤0.05 ∧ `ci_low_1s` > EXP-090 MDE. Justifications in the D0 ratified-parameter table.

*Companion docs **FROZEN** (G0-RATIFIED): [`D0-predeclarations.md`](D0-predeclarations.md) ·
[`G-021-gate-criteria.md`](G-021-gate-criteria.md). No new gate statistic is introduced — the binding gate is
the existing frozen referee suite — so **no bite-check is required** (if EXP-091/092 later introduce a novel
selection statistic, it must be bite-checked GREEN first). Family spec:
[`../../../signal-registry/candidate-families/cf-mr-001.md`](../../../signal-registry/candidate-families/cf-mr-001.md).*
