# EXP-010 — CF-MR-003 CONC-1: form-2 limit-at-anchor tradability screen

**Family:** CF-MR-003 (SCREENED-ADMIT, EXP-009) · **Phase:** 003 · **Type:** tradability screen (net, TRAIN)
**Classification:** **PRICE-PRIMARY** (in-engine; L-01) · **Slots/reads:** consume **1 candidate slot**, **0
counted TEST reads** · **Holdout:** final-30% sealed; emit over **first-49% TRAIN sub-split only** · Frozen
referee — **never tuned** (L-12).

## 0. Mandate

EXP-009 SCREENED-ADMIT CF-MR-003 on the native reversion-to-anchor vehicle (36 leak-clean passes). That is
**availability, not tradability**. CONC-1 is the family's first **net** test: does the concretized
**form-2 limit-at-anchor** strategy (`/TARGET`=mean, `/DIRECTION`=fade, `/REENTRY`=none, live-limit entries
precalc on `≤ t-1` anchor levels, engine-realized **exact** intra-bar limit fill) survive **binding-leg cost**
under the **frozen** referee, per stratum? Honest prior: **LOW** (same broad reversion mechanism as the
EXONERATED CF-MR-002; the burden is on net-survival). Roadmap: `cf-mr-003.md §Concretization roadmap` CONC-1.

## 1. Falsifiable question (one)

*On the EXP-009-admitted strata, does the form-2 limit-at-anchor fade — entry as a live limit at the `≤ t-1`
extreme, exit as a precalculated favourable limit at the higher-domain anchor (mean), no re-entry — produce a
**net-positive** per-bar realized edge (binding-leg cost charged) that clears the frozen renewed referee
(§10.3a q\*=0.75 + E6 `referee_pstar.gate_stack_pstar`) on a predeclared majority of powered strata — or not
(honest prior: not)?* Edge = referee-adjudicated net, per stratum (L-03); a gross pass is never a tradability
claim (L-04).

## 2. Decision cadence = exec-domain grid (corrected 2026-07-01) → CONC-1 (S3) BLOCKED on E7

**Correction of an earlier design error.** EXP-009's construction (`run_experiment.py` `extreme_screen` +
`cross_domain_mr`) computes the **MR screen** (`VR∧HL`, `W_S=200`) and the **extreme** (`|z|≥2`, `W_Z=200`) —
the *entry information* — on the **exec-domain grid** (15m for every admitted S3 cell); the 4h anchor is only
*mapped forward* onto that grid. Fills are exact (limit prices — the operator's point holds), but
**decisions/entries occur at the 15m cadence**, so positions book at 15m. (The earlier "exec domain is just a
fill-resolution artifact → referee domain = anchor 4h" claim was wrong: the exec grid is the decision grid.)
The frozen referee's `DomainSpec`/cost/materiality are **1h/4h only**; a 15m-cadence strategy cannot be validly
booked at 4h (intra-4h round-trips collapse; 4h cost/materiality mis-scale the turnover). **⇒ the S3 arm needs
a 15m referee domain** = an L-12 referee change → the **E7 referee-15m extension (EXP-011)**: add 15m cost map
+ `DomainSpec` + materiality, FPR-recalibrate on the dogfood-negative + synthetic-positive battery, **freeze +
hash-pin before it adjudicates CF-MR-003**. **The S3 (T2a) + S5-exec-15m (T2b) arms are BLOCKED on E7** and run
only after E7 freezes; **T1 (S5 exec-1h) is not blocked** — it books at 1h under the untouched frozen referee
and is the executable CONC-1 arm now (§3/§4). Operator-ratified program 2026-07-01: **both tracks parallel** —
Track 1 = T1 build now; Track 2 = E7 → T2a/T2b.

**S5 feasibility note (operator 2026-07-01).** Multi-symbol in-engine is a **proven** pattern — the sibling
`XRSI-V1` project runs 8 symbols from one cBot via `MarketData.GetBars(tf, sym)` + `Symbols.GetSymbol` + per-cell
`BarOpened`. So the S5 basket anchor **can** be built in-engine (the S5 arm is a build, not a hard blocker; the
earlier "unvalidatable" read was too pessimistic). The **5 distinct** S5 **exec-1h** cells are additionally
**frozen-referee-ready** (domain=1h, no E7).

## 3. Member set + arms (EXP-009 admitted cells by DECISION/exec domain; no re-screening, P-02)

Admitted `any_pass` cells keyed by **exec (decision) domain** = the grid the screen+extreme run on (§2), which
sets the referee domain. Multi-symbol feed feasible in-engine (XRSI-V1 pattern, operator 2026-07-01).

| Arm | Series | Exec/referee domain | Distinct cells | Feed | Ready when |
|---|---|---|---|---|---|
| **T1** (this experiment, first) | S5_SPREAD (exec-grid rolling-β basket) | **1h** | **5** | multi-symbol | **now** — frozen referee (1h, untouched); needs multi-symbol build |
| **T2a** (after E7 freeze) | S3_DETREND (rolling-OLS residual) | **15m** | **14** | single-symbol | after **E7 (EXP-011)** referee-15m freeze |
| **T2b** (after E7 freeze) | S5_SPREAD | **15m** | **10** | multi-symbol | after E7 + multi-symbol build |

*(**S5 anchor-label degeneracy — substrate-verified, corrected 2026-07-01.** For S5 the anchor is fit on the
**exec grid** (`cross_domain_mr.anchor_series` S5 branch: `rolling_beta_fit` over `W_Z=200` **exec** bars);
the anchor domain (1D/4h) **never enters** the S5 signal — S5 ignores the `anchor` dict, no `map_prev`. So the
two exec-1h axes `S5_SPREAD|1D/1h` and `S5_SPREAD|4h/1h` are the **identical strategy**: `EXP-009/per_cell.parquet`
gives **max|Δn_events| = 0** across all instruments (the availability `delta` differs by ≤0.022, an artifact of
the random dislocation-matched control draw, not the entries). ⇒ T1 = **5 distinct** exec-1h cells, not 10. The
"20 S5 admits" in `cf-mr-003.md` = 5 (1D/1h) + 5 (4h/1h, duplicate) + 10 (4h/15m) → **15 distinct** S5 strategies
(5 exec-1h + 10 exec-15m). T2b's 10 exec-15m are distinct — single axis `S5_SPREAD|4h/15m`, no duplication.)*

**Program (operator-ratified 2026-07-01, "both tracks parallel"):**
- **Track 1 = T1** — **5 distinct S5_SPREAD exec-1h** cells (substrate-confirmed `any_pass` on both exec-1h axes):
  **AUDUSD, GBPUSD, NZDUSD** (FX_MAJORS basket) + **US2000, US500** (INDICES basket). Multi-symbol StrategyHost
  build (XRSI-V1 pattern) → frozen referee `domain="1h"` (**no referee change**, L-12 clean). First net read.
  *(The design's earlier "5 × {1D-anchor, 4h-anchor} = 10" split is dropped: for S5 there is no anchor-domain
  distinction — both labels compute the identical exec-grid-β entries.)*
- **Track 2 = E7 (EXP-011) → T2a + T2b** — E7 extends the referee to a **15m domain** (cost map + `DomainSpec`
  + materiality), FPR-recalibrates on the dogfood-negative + synthetic-positive battery, **freezes + hash-pins
  before adjudicating CF-MR-003** (L-12). Then T2a (14 S3 single-symbol) + T2b (10 S5 exec-15m multi-symbol).

Availability Δ (E1 anchor-hit / E2 frac-recovered) per cell carried from `EXP-009/results/per_cell.parquet`
(finest screened grid; NZDUSD/US2000 admitted via E2 — both bear on the form-2 mean-target exit). All arms
adjudicated per-stratum + phase Holm (L-03); member set = admitted cells only (P-02).

## 4. Strategy concretization — TRACK 1 (executable now): S5_SPREAD exec-1h, in-engine multi-symbol

The **executable CONC-1 arm** is **T1** (frozen referee `domain="1h"`, no referee change). T2a (S3) + T2b
(S5 exec-15m) are **BLOCKED on E7/EXP-011** (§2/§3) — do **not** build them now. All decision inputs `≤ t-1`,
fills engine-realized exact-limit intrabar. Constants frozen to the EXP-009 selector that admitted these cells
(`xen.cross_domain_mr`: `W_S=200`, `W_Z=200`, `VR_Q=4`, `VR_DELTA=0.10`, `Z_STAR=2.0`, HL∈(0,48]).

| Axis | T1 setting |
|---|---|
| `/SERIES` anchor | **S5_SPREAD — exec-grid rolling-β** (admitted construction, `cross_domain_mr.anchor_series` S5 branch; **NOT** anchor-domain-fit — that was an S1–S4-pattern error, corrected 2026-07-01). **Basket** `b_t` = equal-weight mean over **asset-class mates (class minus self**, `S5_CLASSES`/`_S5_MATES`) of `log(Close)`, each mate built on the **1h exec grid** and joined by `CloseTime` (drop-to-available mates; no mate → NaN → flat). **Anchor** `a_t = β·b_t + α`, where `(β,α)` = OLS `log(price) ~ b` over the trailing **`W_Z=200` exec(1h)** bars, evaluated at the current basket. **Deviation** `d_t = log(price) − a_t`. All `≤ t-1`. The anchor domain (1D/4h) does **not** enter S5. **Computed IN-ENGINE** via a multi-symbol feed (XRSI-V1 `MarketData.GetBars`/`Symbols.GetSymbol` pattern); basket mates per cell: AUDUSD/GBPUSD/NZDUSD → {EURUSD,USDJPY,USDCHF,USDCAD + the other two majors}; US2000/US500 → {USTEC,JP225 + the other index}. |
| `/EXTREME` | **std-z** on `d_t` over the trailing `W_Z=200` **1h** bars, `|z|≥Z_STAR=2.0`; selector = 2-leg **VR∧HL** (`VR(4)<0.90 ∧ HL∈(0,48]`) on the trailing `W_S=200` **1h**-bar deviation, `≤ t-1`. |
| `/DIRECTION` | **fade** the extreme (extreme-primary). |
| entry | **live limit** at the `≤ t-1` extreme-deviation price level (the `z=±2` band mapped to price); refreshed per **1h exec** bar; **exact** intra-bar fill (engine, 1-min/tick). `/REENTRY`=**none** (≤1 fill per exec bar). |
| `/TARGET` / `/EXIT` | **form-2**: precalc favourable **limit at the anchor mean** `a_target=a[t-1]` (fixed at entry); **fallback** = horizon stop at `H_i=min(48,3·HL_i)` **exec(1h)** bars (native EXP-009 horizon) → market close (pays cost). |

Real emitted OHLC only; **open-to-open** booking per **1h exec** bar with **intra-position mark-to-market**
(L-09) for positions held across 1h boundaries; no synthetic prices (the basket anchor is a `≤t-1` decision
input, not a P&L price — all returns on the traded instrument's real OHLC); `AnalysisEndUtc` = each file's
first-49% cutoff (§10 fence).

## 5. Cost model (analyst-derived; ratified fork) — binding-leg discipline (L-02)

Form-2 = **both legs limit** (favourable-price fills) + a **market fallback** on the exit only.

- **Baseline (binding, conservative):** charge the **frozen per-instrument 1h round-trip `cost_bps`** (the
  referee's own cost map — EURUSD 1.0 … BTCUSD 10.0; T1 domain=1h) on **every completed round-trip**, applied to the engine
  gross fill P&L → `realized_bps` (already net) fed to the referee; the naive control leg uses the **same**
  `cost_bps` (frozen contract). Treats both limit legs as if they paid a full market RT — deliberately
  pessimistic for a limit strategy, so a net pass is robust.
- **Fallback leg:** an exit reaching `H_i` un-filled closes at market (full half-spread+commission, inside the
  RT `cost_bps`); an un-filled **entry** books **no trade** (no cost/P&L — a selection effect T-diag tests).
- **Sensitivity (disclosure):** `cost∈{0.5,1,2}×` RT + a **limit-favourable** variant (commission-only on
  filled legs, half-spread only on the market fallback). Reported beside the binding baseline; never moves the
  verdict.

## 6. Endpoint, adjudication, multiplicity, power

- **Per-1h-exec-bar realized net series** `realized_bps` (engine exact-fill, MTM, cost-charged §5) → **frozen
  referee**: `referee_pstar.gate_stack_pstar(returns, positions, realized_bps, domain="1h", cost_bps=<1h map>,
  n_bootstrap≥10 000, seed=<fixed>)` → `referee_adaptive.adaptive_row(...)` for the per-cell ADMIT/REJECT.
  Referee internal train/test split operates **within** the first-49% emission (analysis-TEST band + holdout
  untouched). **No referee module edited** (L-12); P*-gate is the frozen hash-pinned E6 module (EXP-007).
- **Binding verdict per stratum** (L-03). **Multiplicity:** phase **Holm** across the **5 distinct T1 cells**
  (α=0.05; the exec-1h anchor-label duplicate is collapsed — Holm over 10 would double-count 5 identical
  strategies and mis-specify FWER); any pooled/portfolio figure = **disclosure-only** until cross-stratum
  homogeneity is shown. (T2a/T2b's 24 exec-15m cells are adjudicated under E7's frozen 15m referee in a later
  run — separate Holm.)
- **Power / MDE:** referee L1 readiness (`min_effective_n`, `min_state_count`) + block-bootstrap MDE on the
  test-split `realized_bps`. A cell failing L1 or with `MDE>` the smallest economically-meaningful net =
  **UNPOWERED** (reported, never FAIL — L-12 §2). Low-turnover limit fills may thin episodes → expect some
  UNPOWERED; per-cell episode counts reported.

## 7. Leak tripwires (L-01) — must collapse the edge

- **Binding future-destroy (T1).** Re-run the identical in-engine model on a **block-shuffled/phase-randomized**
  price feed (destroys the cross-domain deviation structure, preserves marginal vol) — VR∧HL + limit fills then
  key off noise. Net per-cell edge **must collapse** to within referee FPR (≤2α; EXP-006 T1 0.000/34). A
  surviving net edge ⇒ leak ⇒ **REJECT**.
- **Binding provenance trace (T2).** Audit traces every verdict-bearing column (`realized_bps`, entry limit
  price, exit fill price, anchor `a_target`, `z`, VR, HL, S5 β) to input timestamps: `≤ t-1` for every
  decision, `≤ t` only for the engine's intra-bar fill of a limit **resting from `t-1`**. Any value from `> t`
  ⇒ leak ⇒ REJECT (EXP-006 T2 34/34).
- **Diagnostic (non-binding):** entry-selection label permutation (which extreme bars are "selected") —
  reported for transparency.

## 8. Interpretation criteria (predeclared; frozen before outcome contact)

- **TRADABLE-ON-TRAIN:** ≥ **50% of powered cells** ADMIT under the frozen referee (net `ci_low>0`,
  Holm-controlled) **and** both binding tripwires (T1/T2) collapse the edge on the admitting cells. ⇒
  concretize the **counted TEST read** (analysis-TEST band) as a new dated-D0 (0 counted reads until then).
- **NOT-TRADABLE:** < majority ADMIT / cost-dominated / referee-REJECT on the powered cells. Availability edge
  does **not** survive to net. Record; family retained; terminal-branch prior reinforced.
- **INCONCLUSIVE / UNPOWERED:** < the powered-cell eligibility threshold, or T1/T2 ambiguous. Report absolute
  effect sizes regardless of verdict (L-11); no goalpost move (inverted-inference predeclaration).

## 9. Complexity budget

- **Stat tests (frozen, reused):** referee gate stack (§10.3a + P*), block-bootstrap net CI, Holm — **no new
  statistic**. ✓
- **Code (T1):** the **multi-symbol StrategyHost extension** (synchronized cross-instrument feeds, XRSI-V1
  pattern) + 1 C# `ISignalModel` (`CrossDomainMrLimitModel`, S5_SPREAD **exec-grid-β** basket anchor in-engine)
  + `EXP-010.conf` (**5 distinct S5 exec-1h cells** + their basket mates); Python **ingest/validate +
  frozen-referee adjudication only** (`xen.signals` + frozen referee, `domain="1h"`). No new Python edge/outcome
  module. (T2a S3 single-symbol + T2b S5 exec-15m are built later, after E7.) ✓
- **Plots (~4):** per-cell net + referee-CI forest; net vs cost-sensitivity band; T1 future-destroy
  before/after; availability-Δ (EXP-009) vs realized-net scatter. ✓

## 10. Implementation safety constraints (for `experiment-developer`)

- **In-engine only.** No Python re-generation of signal/anchor/edge (L-01/P-09). The **S5 basket anchor is
  computed in the C# model** from each basket member's bars at `≤ t-1` (multi-symbol feed); never a
  Python-precomputed anchor. **Fallback:** if the multi-symbol StrategyHost extension cannot be built cleanly,
  **STOP and report** — do not fake a feed or substitute a Python anchor (REJECT-class); with T2a/T2b blocked on
  E7, nothing else is executable, so this is a hard gate on T1.
- **Fence.** `AnalysisEndUtc` per file = **first-49% cutoff** (`int(int(total·0.7)·0.7)` — TRAIN sub-split,
  seals the analysis-TEST band too); emit no row at/after; `HoldoutFence` enforced; analysis-TEST band +
  final-30% holdout never emitted or loaded. (Checkpoint §Sequencing reconciled to 49%.)
- **Causality.** Decide at the **1h exec-bar open** on `≤ t-1` confirmed bars; limit prices rest from `t-1`;
  only the engine's exact intra-bar fill uses `≤ t`. No forming-bar OHLC in any decision. Open-to-open booking
  with intra-position MTM (L-09).
- **Determinism / provenance.** Fixed seeds; emit the provenance columns T2 needs; real OHLC only; align by
  timestamp (`SourceCloseTime`), never bar index; explicit NaN/warmup/degenerate-HL → flat, no propagation.

## 11. Registry / governance disposition

CF-MR-003 `SCREENED-ADMIT → CONC-1 {TRADABLE-ON-TRAIN | NOT-TRADABLE | INCONCLUSIVE}` (net, TRAIN). Consume
**1 candidate slot**; **0 counted TEST reads**; holdout sealed; referee untouched (L-12). Cells partitioned by
**exec/referee domain** (§3), S5 anchor-label duplicate collapsed:
- **T1 (this run):** **5 distinct S5_SPREAD exec-1h cells** (AUDUSD, GBPUSD, NZDUSD, US2000, US500) under phase
  Holm(5), frozen referee `domain="1h"`.
- **T2a / T2b (after E7/EXP-011 freeze):** 14 S3_DETREND exec-15m + 10 S5_SPREAD exec-15m (distinct), under E7's
  frozen 15m referee (separate later run + separate Holm; recorded, never deleted).

Multiplicity-registry: T1's **5** distinct S5 exec-1h cells now (Holm over 5); T2a/T2b's 24 exec-15m cells
reserved pending E7. **Registry honesty note:** `cf-mr-003.md`'s "S5_SPREAD 20 admits" double-counts the exec-1h
anchor-label duplicate — **15 distinct** S5 strategies (5 exec-1h + 10 exec-15m); update the family index on the
next family-doc touch. The counted TEST read + holdout release remain **DEFERRED** to a separate dated-D0, gated
on TRADABLE-ON-TRAIN.

---

## GATE: APPROVE — T1 only (pre-exec, re-issued 2026-07-01 after the exec-grid-β + member-set correction)

**Supersedes both prior GATE blocks:** (1) the retracted anchor-domain frame (domain="4h", 24 cells — void); and
(2) the exec-domain-correction GATE that still carried the **10-cell** T1 and an **anchor-domain-fit S5 anchor**.
Scope now adjudicated on the **substrate-verified admitted vehicle**: S5 anchor = **exec-grid rolling-β**
(anchor domain does not enter S5), and the exec-1h anchor-label duplicate is **collapsed** (max|Δn_events|=0,
`EXP-009/per_cell.parquet`).

**APPROVE — Track 1 (executable arm): 5 distinct S5_SPREAD exec-1h cells** (AUDUSD, GBPUSD, NZDUSD, US2000,
US500), **exec-grid-β basket anchor** (§4, admitted construction), frozen referee `domain="1h"` (untouched,
L-12), multi-symbol in-engine anchor (L-01; no Python anchor), T1/T2 tripwires (§7), per-stratum + **Holm(5)**
(L-03), member set = admitted cells only, no re-screen (P-02), binding-leg cost (L-02, §5), holdout sealed,
0 counted reads, 1 slot, first-49% fence.

**T2a (14 S3) + T2b (10 S5 exec-15m) are NOT approved for build** — BLOCKED on **E7/EXP-011** (referee-15m
extension, frozen before it adjudicates CF-MR-003, L-12). Building them now = building the blocked arm.

**Carried conditions to Stage 2 (T1):** (i) the multi-symbol StrategyHost extension must build cleanly (XRSI-V1
pattern) — if not, **STOP and report**, do not fake a feed / substitute a Python anchor (with T2a/T2b blocked on
E7, nothing else is executable); (ii) build the anchor as **exec-grid β** (`W_Z=200` 1h; basket = class-mate
exec-grid mean log-close, class-minus-self) — **not** an anchor-domain fit; (iii) the credentialed/cost-bearing
cTrader run (Stage 3) is operator-gated — re-confirm before executing. → **Stage 2 (Implement): build the
5-cell S5 exec-grid-β multi-symbol model, NOT S3, NOT an anchor-domain fit.**
