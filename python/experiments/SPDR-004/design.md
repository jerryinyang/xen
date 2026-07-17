# SPDR-004 — Design (CF-HTFCAP-001 TRAIN-only availability screen)

**Lane:** SPDR (speed-run) — `docs/references/spdr-lane.md` · pack
`docs/references/spdr-pack-htfcap-001.md` · family D0
`docs/signal-registry/candidate-families/cf-htfcap-001.md`.
**NOT** a Nautilus price-primary experiment: TRAIN-only, **vectorised Python**, disposition-only.
**No** QA subagent (SPDR stage-2 = code-asserted self-check). **No** estimand gate, **no**
counted TEST read, **no** tradability/deployability claim.
**Route if promote:** full **XENA** (XENA-HTFCAP-001) — EXP lane not used (D0 / Q freeze).
**Checkpoint:** `docs/experiments-docs/checkpoints/2026-07-16-013-chapter04-open-htfcap-epsosc-cal/`.
**Designed:** 2026-07-16 · **Status:** DESIGN COMPLETE — screen execution is a separate go.

---

## 0. Registration precondition (HARD — before any screen code)

| Item | State |
|---|---|
| Family | **CF-HTFCAP-001 REGISTERED** 2026-07-16 (checkpoint-013 D2, operator-signed) |
| Multiplicity row | `docs/signal-registry/multiplicity-registry.md` § Chapter 04 · CF-HTFCAP-001 |
| Candidate card | `docs/signal-registry/candidate-families/cf-htfcap-001.md` status `REGISTERED` |
| Slots / reads | **0 slots; 0 counted TEST reads**; SPDR screen is **uncounted** |
| XENA gate | blocked until INFR-014 fresh CAL pin |
| This design | freezes grid + §5 selection rule/frequency; does not re-register or change family status |

Registration-before-screening satisfied. Screen code must refuse to run if the family card
status is not `REGISTERED` or the multiplicity row is missing (self-check §10).

---

## 1. Question + mechanism

**Falsifiable question (pack §3).** On TRAIN Bybit (rule-selected 10), do one or more
**coherent clusters** of (HTF state × LTF base × hold × domain) show **signal-conditional lift**
over matched baselines in **gross open-to-open bps/trade**, under causal `t−1` rules?

```
MECHANISM: Higher-timeframe (HTF) market state (direction via ±DI, strength via ADX gate,
optional vol regime as disclosure) conditions the quality and/or economic scale of
lower-timeframe (LTF) entries. Capture scale (hold as multiple of HTF span) is a first-class
axis: longer holds are the intended escape from sub-cost short-grain conditioning (P-14).
P&L-bearing object at SPDR = single-leg per-trade open-to-open forward return over hold H
(no multi-leg episode — L-16 N/A). Bases are rulers (unfiltered / naive momentum / random-sign),
not strategies to rescue (spdr-lane base-conditional interpretation).
DERIVED: estimand = mean gross bps/trade + lift vs matched baseline;
         null = matched unfiltered twin + random-sign seed battery + HTF phase-shift destroy;
         horizon = H ∈ {0.5,1,2,4}× HTF-span in LTF bars;
         test = dependence-honest block-bootstrap (block ≥ H) + cluster K≥3 promote rule.
```

---

## 2. P-14 distinctness (binding — not a CF-HTFDI re-run)

| | Closed vehicle (P-14 / CF-HTFDI-001 / EXP-025) | This vehicle (CF-HTFCAP-001 / SPDR-004) |
|---|---|---|
| Claim closed | HTF-DI **continuation as a tradable edge** at **1h→5min** | Family **justification** screen only (WORTH_EXPLORING → XENA) |
| Measured edge | True effect **≈1–4 bps/trade** (h48), **< cost**; 0/440 SEL-NEIGHBOR | Unknown on Bybit — re-measure; no tradability claim |
| Grain | Fixed short domain 1h/5min primary | **Multi-domain** incl. longer grain: 1h/5m, **4h/15m**, **1d/1h** |
| Capture | Short holds; unit-pin failure inflated graduation target 4.1× (L-21) | **Hold axis mandatory 2× and 4× HTF span** (plus 0.5×, 1×); L-21 pin **at screen** |
| Universe | USTEC / FX legacy | **Bybit USDT-perp**, online top-10 volume |
| Adjudication path | EXP graduation gates | **SPDR → XENA** (cost-aware portfolio; EXP unused) |
| Family | CF-HTFDI-001 retired magnitude-closed | **NEW family** CF-HTFCAP-001 (own D0) |

**Why per-trade capture can escape the 1–4 bps sub-cost trap (P-14 re-open clause).**
P-14 re-opens only for a vehicle whose per-trade capture is **≥10× larger** (longer holds /
different granularity) via a **new family** with L-21 applied at design time. This screen:

1. **New family + new stack + new universe** — not a re-parameterisation of CF-HTFDI.
2. **Capture scale is mandatory:** holds include **2× and 4× HTF span**. Example on 1h/5m:
   H=24 (1×) = 2h calendar; H=48 (2×) = 4h; H=96 (4×) = 8h — vs EXP-025's sub-cost ~4 bps at
   short grain. On 1d/1h, H=48 (2×) = 2d and H=96 (4×) = 4d calendar — different granularity
   class entirely.
3. **Multi-modality HTF state** (DI ± ADX gate; vol disclosure) and **three LTF bases** —
   mechanism class is conditioning × capture, not "DI continuation alone is tradable."
4. **L-21 unit pin at this screen** (§5) — primary unit is raw bps; no ATR→money conversion
   from memory; money-unit floor disclosed before disposition.
5. **Promote = cluster K≥3 justification**, not a deployability or single-cell lottery win.

If the best cluster's median gross bps sits at/below the cost floor, disposition must say so
(L-21 money-unit floor); operator may still graduate only as characterisation/apparatus, never
as tradability.

---

## 3. Object identity

```
OBJECT-IDENTITY:
  measurement object == trading object: YES — both = single-leg open-to-open return over H
    (screen availability metric, not xen.adjudication P&L).
  measured conditioning event == traded entry event: YES — entry at LTF bar t open; HTF state
    from last fully closed HTF bar with CloseTime < Open(t); base signal from LTF data ≤ t−1.
  effect-splitting windows non-overlapping: active-hold prevents overlapping opens within an
    arm/seed; one forward window per trade.
```

**MTF bar-boundary hazard (primary leak risk).** At LTF entry `t`, every HTF feature
(±DI, ADX, ATR-vol) must come from the **most recent HTF bar with CloseTime < Open(t)** —
never the forming HTF bar. Code-asserted + golden-trace checked.

---

## 4. Estimand (availability/lift — no P&L verdict)

Primary (binding facet for promote):

```
r_bps = s · (RealOpen[t+H] − RealOpen[t]) / RealOpen[t] · 1e4
```

- `s ∈ {−1,+1}` from base + HTF polarity (with-HTF: long iff +DI>−DI on last closed HTF bar;
  short opposite; unfiltered base uses base sign only).
- **Open-to-open**, real prices only (catalog 1m → aggregated LTF via `xen.bar_aggregator`).
- Per-stratum statistic: **mean `r_bps`** over trades; **lift** = treatment − matched baseline
  (same base, HTF filter removed / unfiltered twin).
- Random base: **≥25-seed battery** (L-19); report percentile/rank of treatment vs battery mean
  + CI on battery-aggregated lift — never a single-twin verdict.
- Uncertainty: `xen.evaluation.block_bootstrap_ci` with **block ≥ H** (or non-overlapping trade
  series); `block_sensitivity` ½×/1×/2× + `ci_low_seed_range` disclosed (L-20). Report
  "bootstrap 95% CI excludes zero", not a p-value.
- **No local accounting primitives** (L-18); no `xen.adjudication` P&L for disposition.
- Funding: **disclose** per hold (Q5) — not a SPDR gate; binds at XENA only.
- Pooled figures: **disclosure-only** (L-03).

---

## 5. L-21 unit pin AT THE SCREEN (binding)

Primary estimand is already **money-unit bps** (no ATR divisor on the promote facet). Still pin
every normaliser used for disclosure and the cost floor — filled from **TRAIN data at screen
start**, never from memory (L-21 / P-15).

```
UNIT-PIN (SPDR-004):
  primary unit:     gross open-to-open bps/trade  (formula §4) — NO ATR divisor on promote facet
  disclosure ATR:   LTF ATR(14)[t−1] on the domain LTF bar series (Wilder/standard as in
                    xen indicator used by screen_code — name file:line at implement)
  measured value:   TRAIN-median of disclosure ATR in bps of price
                    = median(ATR_LTF(14)[t−1] / RealOpen[t] · 1e4) per (instrument × domain)
                    → write results/unit_pin.json at screen start (never pre-assert numbers)
  resulting effect: for any ATR-normalised disclosure cell: r_norm · measured_ATR_bps = bps/trade
                    (promote uses raw r_bps only; this pin exists so no seam re-asserts a divisor)
  money-unit floor: per instrument, RT cost proxy at disposition:
                    xen.evaluation.bybit_round_trip_cost_bps(
                      symbol, entry_px,
                      liquidity="taker",          # 2 × 5.5 = 11 bps fees RT
                      spread_bps=<TRAIN-median T1 pseudo-quote RT spread if available,
                                   else GAP + conservative disclosed assumption>,
                      funding_bps_per_8h=<disclosed; Q5 not binding at SPDR>,
                      hold_hours=H_calendar_hours
                    ).total_bps
                    + one-sided capture dilution note (≈ gap/2) if applicable
  floor rule:       if best cluster median gross bps/trade ≤ floor → disposition text MUST state
                    sub-floor; operator may still graduate only as characterisation/apparatus
```

```
SPREAD-SCALE-ROUTING (informative at SPDR; binding language for any later T1 tradability read):
  estimated_rt_spread_bps: <from TRAIN pseudo-quote via t1_round_trip_spread_bps — measured>
  gross_edge_bps: <cluster median gross bps>
  t1_undecidable: YES if |gross| < 3× rt_spread (spread_scale_route)
  SPDR disposition is NEVER a T1 tradability band — this block is disclosure + graduation prior
```

---

## 6. Scope + frozen thin grid

### 6.1 Instrument selection (§5 checkpoint-013 — binding block)

```
INSTRUMENT-SELECTION (online, D5; AMENDMENT-2):
  n: 10
  rule: at each rebalance point, select ADMITTED, listed Bybit USDT linear perps with the
        highest trailing 24h **USDT notional volume** =
          sum_i (catalog_1m_volume_i × close_i)
        over the prior 1440 1m bars with CloseTime in [rebalance−24h, rebalance)
        (last bar strictly < rebalance_ts ≡ ≤ t−1 of rebalance).
        NOT raw base-asset unit volume (pre-A2 bug: cheap high-unit names dominated).
  rebalance frequency: every 1 UTC calendar day at 00:00 UTC (first LTF bar of that day is the
        membership epoch until next rebalance).
  causality: selection at t uses volume/price data ≤ t−1 only — code-asserted.
  tie-break: lexicographic InstrumentId ascending.
  SPDR anti-survivorship (D3): membership pool = symbols ADMITTED and not delisted as of the
        rebalance time (currently-most-liquid justification; full delisted-inclusive PIT is
        XENA characterisation — D3).
  reproducibility: membership series written to results/membership.parquet (rebalance_ts,
        symbol, rank, trailing_24h_notional_usdt, trailing_24h_base_volume); no fixed pre-run
        ticker list.
  cell strata (AMENDMENT-3): membership is time-varying for eligibility; the 720-cell table uses
        the fixed top-10 symbols by **membership-days** over TRAIN (tenure ranking) so cell
        count stays 10×…; disclosed in results/summary.json.
  effective data window (disclosure): many symbols' catalog bars begin ~2022-07-15; fence still
        [analysis_start, train_end); empty-overlap symbols contribute 0 membership days.
  codified selector: xen.nautilus.universe_selection may follow — not blocking.
```

### 6.2 Data + fence

| Item | Value |
|---|---|
| Catalog | `data/catalog/` ParquetDataCatalog |
| Fence | `xen.nautilus.catalog_fence` — PINNED manifest `python/experiments/INFR-011/artifacts/fence-manifest.json` |
| TRAIN band | `[analysis_start_utc, train_end_utc)` = **2021-06-29 → 2023-12-18** |
| TEST / HOLDOUT | **never queried** (`band="TRAIN"` only; holdout_start 2025-01-08 sealed) |
| Aggregation | `xen.bar_aggregator` clock-aligned OHLC from 1m → LTF/HTF |
| Engine | vectorised Python screen (SPDR carve-out); Nautilus reserved for XENA graduation |

### 6.3 Grid (frozen)

| Axis | Levels | n |
|---|---|---|
| Symbols | online top-10 (§6.1) — stratum by symbol at membership | 10 (time-varying) |
| Domain (HTF/LTF) | **1h/5m**, **4h/15m**, **1d/1h** (≥1 longer-grain pair) | 3 |
| Hold multiple | **0.5×, 1×, 2×, 4×** HTF span in LTF bars | 4 |
| LTF base | **UNF** (unfiltered / every non-overlapping LTF bar), **MOM** (naive momentum breakout), **RAND** (random sign) | 3 |
| HTF filter | **NONE** (baseline), **DI** (±DI continuation), **DI_ADX** (DI + ADX≥25) | 3 |
| Polarity | **with-HTF** for DI/DI_ADX; against-HTF optional disclosure only | 1 binding |

**Hold H in LTF bars (HTF/LTF ratio × multiple):**

| Domain | ratio | H @ 0.5× | 1× | 2× | 4× |
|---|---:|---:|---:|---:|---:|
| 1h / 5m | 12 | 6 | 12 | 24 | 48 |
| 4h / 15m | 16 | 8 | 16 | 32 | 64 |
| 1d / 1h | 24 | 12 | 24 | 48 | 96 |

**Params (fixed):** ADX/DI/ATR period **14** on HTF bars; ADX gate **≥25**; MOM lookback
**N = 1 HTF-span in LTF bars** (sign of `RealClose[t−1] − RealClose[t−1−N]`); RAND seeds
**{1000..1024}** (25 seeds); active-hold non-overlap within arm/seed.

**UNF baseline sign (AMENDMENT-1):** UNF has no intrinsic sign, so a `UNF × NONE` cell is
undefined — the matched baseline (Control A) for `UNF × {DI, DI_ADX}` treatment cells is the
**RAND battery at UNF cadence** (25-seed random-sign ruler; lift = treatment vs battery mean,
rank read per L-19). `MOM`/`RAND` treatments keep their `NONE` twins as designed. No
`UNF × NONE` cell is emitted as a treatment or baseline.

**Cell count (signal):** 10 × 3 × 4 × 3 bases × 2 HTF filters (DI, DI_ADX) = **720** treatment
cells + matched NONE baselines. Multiplicity disclosed; promote = **cluster**, not max cell.

**Hard exclusions:** no passive-limit MR primary cell (P-10); no forming-bar HTF; no TEST/holdout.

**Complexity budget:** 1 screen module, ≤5 plot families, seed battery on RAND only, no local P&L.

---

## 7. Controls (validity proofs)

```
CONTROL A — matched unfiltered baseline (isolates HTF filter):
  question: is lift from HTF direction/strength, or only from base cadence/bar selection?
  population: same base × domain × hold × symbol; HTF filter = NONE. DISJOINT construction
    (filter on vs off) — different answer possible when HTF carries directional value (B-1).
  bite/MDE: paired lift CI; MDE from per-cell n (block ≥ H).
  non-vacuity: removing DI/ADX reassigns entry set and/or sign → moves mean (B-6).
  expected if H true: treatment mean > baseline; if false: ≈ baseline.
  disclosure: collapse fraction = baseline / treatment (B-2 / L-15).
  destroy form: N/A (not a permutation destroy).

CONTROL B — random-sign seed battery (RAND base; L-19):
  question: does any HTF overlay beat direction-random at same cadence?
  population: ≥25 seeds, regenerable from (seed, bar calendar); seeds do not read price path
    for timing (timing = base cadence; sign random).
  bite/MDE: battery percentile of treatment; battery mean vs MDE.
  non-vacuity: randomising sign zeros E[s·r] under independence → moves mean.
  expected if H true: treatment rank high in battery + CI lift > 0; if false: ~median rank.
  destroy form: N/A for sign draws; if any schedule permutation used → DERANGEMENT (L-28).

CONTROL C — HTF phase-shift future-destroy (leak tripwire):
  question: does edge need causal HTF alignment with this bar's forward window?
  destroy: shift HTF feature stream by K HTF bars, K ≫ max hold / HTF ratio (freeze K=50 HTF bars),
    before assigning DI/ADX labels.
  non-vacuity: reassigns signs/gates → moves mean (not mean-preserving multiset shuffle).
  MUST collapse edge on any promote-candidate cell; expected collapse fraction ≈ 1.
  destroy form: if implemented via index permutation of HTF labels → **DERANGEMENT (L-28)** —
    zero fixed points; regenerate draws with any fixed point. Plain permutation banned
    (VAL-008: fixed blocks leak plant/true signal).
```

---

## 8. Promote rule + interpretation bands

Pack §6 normative (**K = 3** frozen):

**WORTH_EXPLORING** iff **all** of:
1. **Cluster:** ≥ **K=3** cells in a connected region (same domain family and HTF modality,
   varying hold and/or symbol) show positive lift vs matched baseline on primary **bps**, with
   dependence-honest uncertainty not obviously null (ci_low>0 on lift, or rank clearly above
   battery for RAND).
2. **Neighbourhood:** best cell is not the sole positive in its neighbourhood (same domain ×
   HTF modality: at least one adjacent hold multiple or peer symbol also positive lift).
3. **Money-relevant:** report cluster median gross bps/trade; apply §5 money-unit floor
   disclosure (sub-floor allowed only with explicit characterisation framing).

**NOT_WORTH:** no K≥3 cluster; lift is a single lottery cell under multiplicity.  
**INCONCLUSIVE:** underpowered / data gap — never folded into NOT_WORTH (B-5).

```
BANDS (per stratum — informative magnitudes for analyst; promote uses pack rule above):
  SUPPORTED_LIFT:  lift ci_low > 0 (block≥H) AND survives Control C collapse
  WASH:            CI straddles 0 / |lift| < MDE — report ≈0, not refutation
  CONTRADICTED:    lift ci_high < 0
  UNPOWERED:       n below block floor or MDE > plausible — excluded from negatives
POOLED: disclosure-only.
HARD: TRAIN fence; causal t−1; HTF CloseTime < Open(t); Control C on promote cells;
      derangement on permutation destroys (L-28); registration present.
INFORMATIVE: all effect sizes, clusters, floors, funding disclose, SPREAD-SCALE-ROUTING.
```

---

## 9. Power + diagnostics

```
POWER:
  expected trades/cell: dense on 1h/5m UNF; thinner on 1d/1h H=96 and DI_ADX tails.
  MDE: reported per cell from block bootstrap (block≥H).
  predeclared UNPOWERED (never negatives): ADX-gated tails with n < max(30, 2·H);
    1d/1h × H=96 on short membership windows; any cell with n < 2·block.
```

**Diagnostics (always report, not gates — pack §7):** hold ladder in **bps**; drift/beta on
directional bases; lift over unfiltered not absolute return of a broken base; cell count +
multiplicity; membership churn summary; funding accrual disclosure by hold.

**Fresh-context analysis (stage 5, mandatory):** after `screen.md`, spawn `data-analyst` on raw
screen outputs — quantify-not-qualify, per-stratum magnitudes (spdr-lane). Operator disposition
after `analysis.md` only.

---

## 10. Integrity checklist (code-asserted — replaces QA subagent)

Screen script prints PASS/FAIL for each **before** writing promote-facing results:

1. **Registration** — CF-HTFCAP-001 card `REGISTERED` + multiplicity Chapter 04 row present; 0 slots.
2. **TRAIN fence** — all catalog reads via `fenced_bar_query(..., band="TRAIN")` (or
   `assert_within_fence`); max entry+hold timestamp < `train_end_utc`; 0 TEST/HOLDOUT rows.
3. **Causal t−1** — every base/HTF input ≤ t−1; HTF `CloseTime < Open(t)` for all entries.
4. **Online selection causality** — membership volume windows end ≤ t−1 of rebalance.
5. **Matched control + seed battery** — NONE twin present for every treatment cell; RAND ≥25
   seeds regenerable byte-identical from (seed, calendar).
6. **Per-stratum emission** — full cell table to `results/` (no pooled-only headline).
7. **L-28** — any permutation destroy is a derangement (0 fixed points).
8. **L-21** — `results/unit_pin.json` written from TRAIN measurements before disposition text.
9. **Block ≥ H** on overlapping forward-window CIs.
10. **Golden trace** G1–G3 reproduced within tolerance.
11. **No local adjudication P&L** for verdict; screen metrics only.

Any FAIL blocks the screen disposition path.

---

## 11. Golden trace (self-check)

```
GOLDEN-TRACE (fill timestamps from TRAIN at implement; hand-derive expected values):
  G1 (1h/5m, membership symbol rank-1 on a mid-TRAIN day): LTF 5m entry t; last 1h bar with
      CloseTime < Open(t); record +DI/−DI/ADX(14); expected DI sign; verify no forming 1h bar used;
      r_bps for H=12 hand-check vs Open[t+12]/Open[t].
  G2 (4h/15m): DI_ADX entry; verify ADX≥25 from last closed 4h only; H=32 exit still < train_end.
  G3 (membership): one 00:00 UTC rebalance; recompute top-10 trailing 24h volume from 1m bars
      with ts ≤ t−1; must match results/membership.parquet row (tie-break lex).
```

---

## 12. Ratified stack lessons (L-28..L-31) — cite, do not re-litigate

KB `docs/knowledge-base/lessons-and-amendments.md` (checkpoint-013 D1, VAL-008 §5):

| ID | Rule | Binding on SPDR-004? |
|---|---|---|
| **L-28** | Destroy permutations must be **derangements** (0 fixed points) | **Yes** — Control C / any label shuffle |
| **L-29** | Nautilus fill-ts = decision-bar close; naive close-axis searchsorted off-by-one | **Cite only** — vectorised open-to-open screen has no Nautilus fill path; binds at XENA emission |
| **L-30** | `BacktestRunConfig(dispose_on_completion=False)` for node report capture | **Cite only** — XENA/Nautilus runners |
| **L-31** | One BacktestNode per process (subprocess-per-cell) | **Cite only** — XENA/Nautilus runners |

Also in force: L-03 per-stratum · L-19 seed battery · L-20 CI hygiene · L-21 unit pin · L-22
spread as later verdict leg · L-26 costless filter theater banned at XENA · P-10/P-14/P-15.

---

## 12b. Amendment ledger (L-23)

```
AMENDMENT-1 (2026-07-16, pre-execution): UNF×{DI,DI_ADX} matched baseline = RAND battery at
  UNF cadence (UNF×NONE undefined — UNF carries no sign; gap-fill, pack silent; pack already
  names random-sign as a ruler). DIRECTION: NEUTRAL (defines an unimplementable cell; no
  gate/threshold change).

AMENDMENT-2 (2026-07-16, post-exec QA + operator): membership rank key =
  trailing 24h USDT notional (volume×close), not raw catalog base volume. DIRECTION: NEUTRAL
  (corrects liquid-major intent; does not loosen integrity). Requires full screen re-run.

AMENDMENT-3 (2026-07-16, post-exec QA): cell table strata = fixed top-10 by membership-days
  over TRAIN; eligibility still online time-varying membership. DIRECTION: NEUTRAL
  (documents prior interpretive choice for 720-cell count).

AMENDMENT-4 (2026-07-16, post-exec QA fidelity): lift uncertainty = two-sample block-bootstrap
  CI of mean(treatment)−mean(baseline) with block ≥ H (or block=1 on non-overlapping trade
  series + block_sensitivity + ci_low_seed_range emitted to results/). Replaces unpaired
  "treatment CI − fixed baseline mean". DIRECTION: TIGHTER on promote-facing CI (anti-
  conservative unpaired CI removed).

AMENDMENT-5 (2026-07-16, QA-2): UNF vs RAND-battery lift CI must bootstrap **both** arms —
  treatment trade series (block ≥ H) and battery seed means (block=1) — each draw
  (method `two_sample_block_vs_battery`). Bans prior `battery_minus_seeds` which held the
  treatment mean fixed (omitted treatment SE; inflated UNF CI+ mass). DIRECTION: TIGHTER.

running count: 0 looser / 2 tighter (A4, A5) / 3 neutral (A1–A3).
```

## 13. Artifacts + stop condition

```
python/experiments/SPDR-004/
  design.md       # this file — DESIGN COMPLETE
  screen_code/    # (next go) TRAIN-only vectorised screen
  results/ plots/
  screen.md       # neutral quantification
  analysis.md     # fresh-context data-analyst (mandatory)
```

**Stop:** design + registration complete. **Do not run screen** until operator execution go.
On WORTH_EXPLORING → separate XENA-HTFCAP-001 design after INFR-014 pin (not this artifact).
