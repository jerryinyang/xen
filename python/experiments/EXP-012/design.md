# EXP-012 — CF-MR-003 CONC-1 Track 2: form-2 limit-at-anchor, exec-15m tradability

**Class:** PRICE-PRIMARY, cTrader in-engine (L-01). **Phase:** 003 CONC-1, Track 2. **Governs:** the
exec-15m arms EXP-010 deferred behind E7. **Prereq DONE:** E7/EXP-011 — 15m referee FROZEN + hash-pinned
(`referee_adaptive 96c940b5…`, `pstar 1fd06b28…==E6`). **Budget:** 0 counted TEST reads, 0 new candidate
slots (same CF-MR-003 tradability exploration EXP-010 opened), holdout sealed. Informal: "EXP-010b".

## 0. Mandate

EXP-009 SCREENED-ADMIT CF-MR-003 (availability). EXP-010 (T1, 5 S5 exec-1h) returned **NOT-TRADABLE
(UNPOWERED)** — the VR∧HL∧|z|≥2 reversion-episode count (10–32) fell below the 1h floor of 20, so net
could not be tested at power. EXP-012 tests the **exec-15m** admitted cells under the now-frozen 15m
referee: 15m has ~4× the bars, so more reversion episodes may clear the (higher) 15m floor. **Honest
prior LOW** — not a rescue (P-02): higher 15m floors (min_state 25 vs 20) partly cancel the extra
episodes; shorter-horizon reversion captures a smaller move against the **same** per-instrument
round-trip cost (net likely worse); sister family CF-MR-002 was EXONERATED. **A powered NOT-TRADABLE
is a definitive close**, not a failure to test.

## 1. Falsifiable question (one)

*On the EXP-009-admitted exec-15m cells, does the form-2 limit-at-anchor fade — entry a live limit at
the ≤t-1 `|z|≥2` band edge, exit a precalculated favourable limit at the higher-domain-anchor mean, no
re-entry — produce a **net-positive** per-15m-bar realized edge (binding-leg cost charged) that clears
the **frozen 15m referee** (`gate_stack_pstar`, domain="15m"), **per stratum**? Or is it
cost-dominated / referee-REJECT / still under-powered?*

## 2. Member set (EXP-009 admitted exec-15m cells only — no re-screening, P-02)

Source: `EXP-009/results/per_cell.parquet`, axis `…|4h/15m`, `any_pass=True`. **24 cells, one Holm
family, two explicit sub-families.**

| Arm | Axis | Feed | # | Instruments |
|---|---|---|---|---|
| **T2a** | `S3_DETREND\|4h/15m` | single-symbol | **14** | AUDJPY, AUDUSD, BTCUSD, EURJPY, EURUSD, GBPJPY, GBPUSD, NZDUSD, US2000, USDCAD, USDCHF, USDJPY, USTEC, XAUUSD |
| **T2b** | `S5_SPREAD\|4h/15m` | multi-symbol basket | **10** | AUDUSD, EURUSD, GBPUSD, NZDUSD, US2000, US500, USDCAD, USDCHF, USDJPY, USTEC |

`n_events` (availability dislocations, 15m grid) 2028–3030 (S3) / 4048–7180 (S5) — but the binding
count is **completed reversion episodes** after VR∧HL∧|z|≥2 ∧ limit-fill, which is the power question
(§5). No cell is added or dropped on any in-experiment read.

## 3. Strategy concretization (both arms — identical form-2 logic; ≤t-1 decision inputs)

Same concretization as EXP-010, re-pointed to exec-15m. All decision inputs on confirmed bars ≤t-1;
evaluate at the action bar's **open**; engine-realized **exact** intra-bar limit fill; open-to-open
realized returns; intra-position MTM across 15m boundaries (L-09).

| Component | Spec |
|---|---|
| `/SERIES` **T2a** (S3_DETREND) | **single-symbol** rolling-OLS-trendline residual. Anchor `a_t` = `rolling_ols_fit(log(price), W=200 exec-15m)` fitted value `α+β·(W−1)` (the trendline at t); deviation `d_t=log(price)−a_t`; robust-z over `W_Z=200`. **In-engine, no basket** — the admitted `cross_domain_mr.anchor_series` S3 branch, unchanged. |
| `/SERIES` **T2b** (S5_SPREAD) | **multi-symbol** exec-grid rolling-β class-mate basket (admitted S5 branch, **unchanged** from EXP-010): basket `b_t`=mean log(Close) over class-mates (class−self), each on the 15m exec grid, joined by `CloseTime`; `(β,α)`=OLS over trailing `W_Z=200` exec-15m bars; `a_t=β·b_t+α`; `d_t=log(price)−a_t`. In-engine via `CrossDomainMrLimitModel.cs`/`IBasketFeed` (`MarketData.GetBars`), domain=15m. |
| Selector (`≤t-1`) | VR(q=4)<0.90 ∧ half-life∈(0,48] (the admitted 2-leg screen); extreme `|robust-z[t-1]|≥2`. |
| `/DIRECTION` | fade (short at +z extreme, long at −z). |
| Entry | live **limit** at the `z=±2` band-edge price, precalc on `a[t-1]` + scale; fill exact intra-bar or expire (un-filled ⇒ **no trade**, no cost/P&L — a selection effect, tracked). |
| `/TARGET`,`/EXIT` (**form-2**) | precalc favourable **limit at the anchor mean** `a_target=a[t-1]` (fixed at entry); **fallback** horizon stop at `H_i=min(48,3·HL_i)` exec-15m bars → market close (pays cost). |
| `/REENTRY` | none. |

## 4. Cost model (binding-leg, conservative — L-02; inherits EXP-010 §5 at 15m)

- **Binding (conservative):** the frozen **15m** per-instrument round-trip `cost_bps` (= the 1h value,
  E7-frozen: EURUSD 1.0 … BTCUSD 10.0) on **every completed round-trip**; both limit legs charged a
  full market RT (deliberately pessimistic — a resting limit would often earn spread). Un-filled entry
  = no trade.
- **Sensitivity (disclosure only):** `cost∈{0.5,1,2}×` RT + a **limit-favourable** variant
  (commission-only on the limit legs). Non-binding; frames the cost cliff.

## 5. Endpoint, adjudication, multiplicity, power

- **Per-15m-exec-bar realized net series** `realized_bps` (engine exact-fill, MTM, cost §4) →
  **frozen 15m referee**: `referee_pstar.gate_stack_pstar(returns, positions, realized_bps,
  domain="15m", cost_bps=<15m map>, …)`. **Never tuned** (L-12; hashes pinned).
- **Binding verdict per stratum** (L-03). **Multiplicity:** phase **Holm** across the **24 cells**
  (α=0.05), with **T2a (14) / T2b (10) reported as explicit sub-families**; a pooled/arm-level figure
  is disclosure-only until cross-stratum homogeneity is shown.
- **Power:** the 15m floor is `min_state_count=25` episodes/direction (`min_effective_n=90`). A cell
  with <25 completed reversion episodes/direction is **UNPOWERED** — recorded as *could-not-test*, **not
  a refutation** (EXP-010 discipline). Report per-cell episode counts vs 25 (the central power read).

## 6. Gate-debt discharge (EXP-010 F-1/F-2 — BINDING before any powered-positive booking)

- **F-1 vehicle fidelity.** EXP-010's in-engine z-selector was loose (corr 0.67, |z|≥2 Jaccard 0.30)
  vs the EXP-009 screen — real-bar + basket carry-forward vs exact-join. **Predeclare a per-cell
  fidelity check:** in-engine `z[t-1]` + VR∧HL pass vs the EXP-009 screen `z`/pass on matched
  `CloseTime`; **tolerance: z corr ≥0.90 ∧ |z|≥2 selection Jaccard ≥0.70** (tightened from the loose
  0.67/0.30). Remedy if breached: exact-join basket (T2b) / documented carry-forward; **T2a
  single-symbol has no basket carry-forward** → expected clean. **A powered-positive on a cell failing
  the fidelity tolerance is NOT bookable** (recorded VEHICLE_UNFIT).
- **F-2 non-vacuous leak-resistance.** EXP-010's future-shuffle was vacuous on a null edge. **Predeclare
  a two-sided control that is informative regardless of live sign:** (a) **planted-positive injection**
  — add a known favourable drift to the realized series on the true positions; the referee **must PASS**
  it (proves the vehicle *can* detect a real edge at 15m at this episode count — power sanity); (b)
  **future-destroy** the same planted series (block-permute returns) — it **must collapse** to REJECT.
  So even a null live edge yields a meaningful leak-resistance + power read (detect-real ∧ reject-shuffled).

## 7. Leak tripwire(s) (mandatory)

1. **Future-destroy (both arms):** block-permute the exec-15m returns / phase-shift the S5 basket
   (destroy position↔return + price↔basket alignment) → any live edge **must collapse** to the
   referee's null pass-rate. Applied to the live series AND (F-2) the planted-positive series.
2. **Provenance:** every verdict-bearing column (anchor `a`, deviation `d`, z-selector, entry-limit,
   exit-limit `a_target`, realized fill, cost) traces to inputs `≤t-1`; **no `rct[di]`** (a bar's own
   close as its own intra-bar limit — the exit limit is `a[t-1]`, fixed at entry, never `a[t]`).
3. **Price-primary:** all edge logic in the cTrader engine; Python ingests `data/strategy_runs/EXP-012/`
   only — no vectorized Python backtest (REJECT).

## 8. Success / failure / inconclusive (predeclared)

- **Tradable-on-TRAIN:** net-positive per-stratum edge (binding cost) clearing the frozen 15m referee on
  a predeclared **majority of powered cells within an arm** (≥⌈powered/2⌉, T2a and T2b judged
  separately), **fidelity-clean (F-1)**, leak-clean (F-2/§7). → gate a **later** counted TEST read (new
  dated D0). *(Given the LOW prior, treat any positive as provisional pending the gate-debt discharge.)*
- **NOT-TRADABLE:** on the powered majority, net is cost-dominated / referee-REJECT / CI covers 0. →
  record; family retained; terminal-branch prior reinforced; **exec-15m branch closed with powered
  evidence**.
- **UNPOWERED:** too few cells reach ≥25 episodes/direction, or direction mixed. → record as
  could-not-test (not a refutation). If T2a powers but T2b does not (or vice-versa), report per-arm.

## 9. Fences / holdout (binding)

Per-symbol `ANALYSIS_END` = **first-49% TRAIN cutoff** `int(int(N_m1·0.7)·0.7)` (seals the analysis-TEST
band **and** the final-30% global holdout); the host emits **no** 15m bar at/after it. TRAIN-only, **0
counted TEST reads** (honest-prior tradability screen = disclosure, EXP-006/010 precedent). Multi-symbol
basket mates (T2b) are read only ≤ the exec bar's `CloseTime` and clipped at the same fence. No holdout
touch; `CloseTime` alignment, no bar-index.

## 10. Complexity budget (comparative)

- **C# model:** T2a = extend `CrossDomainMrLimitModel.cs` with a **single-symbol S3 rolling-OLS-residual
  anchor** mode (no basket feed); T2b = the existing S5 multi-symbol path at domain=15m. One `.conf`
  (`EXP-012.conf`, 24 cells) + the F-1 fidelity + shuffle-control confs.
- **Python (ingest/validate only):** reuse EXP-010's ingest; add the F-1 fidelity join (in-engine z vs
  EXP-009 screen) + the F-2 planted/destroy adjudication + per-stratum Holm. No vectorized strategy.
- **Stat/plots:** per-cell net + referee verdict + episode-count-vs-floor (power); F-1 fidelity scatter;
  F-2 planted-pass/shuffle-collapse; cost-sensitivity curve. ~4 plots; within comparative.

## 11. Implementation safety (for `experiment-developer`)

- Price-primary: S3/S5 anchor + form-2 limit in C# `ISignalModel`; Python never regenerates a signal.
- `≤t-1` everywhere; exit limit `a_target=a[t-1]` fixed at entry (no self-close leak); open-to-open;
  intra-15m MTM (L-09). Un-filled entry books nothing.
- Frozen 15m referee consumed **as-is** (domain="15m", hashes pinned); never re-tuned (L-12).
- TRAIN fence per symbol; holdout never emitted. Basket mates ≤ `CloseTime`, clipped at the fence.
- Deterministic; the shuffle/plant controls use fixed seeds. Reuse EXP-010 model/ingest; keep the S3
  single-symbol anchor a bounded rolling-OLS (W=200) matching `cross_domain_mr.rolling_ols_fit`.

*(The Stage-3 cTrader run is credentialed + cost-bearing — an operator-gated critical decision; the
orchestrator re-confirms before running. This design does not itself trigger the run.)*

---

## GATE: APPROVE (orchestrator inline pre-exec, 2026-07-01)

Checked against `references/governance-constraints.md` + the Phase-003 checkpoint + EXP-010's design:

- **Single falsifiable question** — net-positive per-stratum edge clearing the frozen 15m referee on the
  exec-15m admitted cells: yes / not-tradable / unpowered. One question, two arms (sub-families). ✓
- **Classification** price-primary — correct: the S3/S5 anchor + form-2 limit generate the edge → **must
  run in the cTrader engine** (C# `ISignalModel`, emit `data/strategy_runs/EXP-012/` under the
  `AnalysisEndUtc` fence); Python ingest/validate only. A vectorized Python backtest would be REJECT. ✓
- **Registry precondition** — CF-MR-003 registered (SCREENED-ADMIT); CONC-1 tradability exploration slot
  already opened by EXP-010 → **0 new slots**; TRAIN-only **0 counted TEST reads** (disclosure,
  EXP-006/010 precedent); holdout sealed. Member set = **EXP-009 admitted exec-15m cells only** (24,
  enumerated) — no re-screening dead cells, no downstream-stack tuning to rescue a dead entry (P-02). ✓
- **Frozen referee (L-12)** — `gate_stack_pstar` domain="15m" consumed as-is, hashes pinned (E7/EXP-011),
  never tuned on CF-MR-003. Power floor min_state_count=25 honored; UNPOWERED ≠ refutation. ✓
- **Per-stratum binding (L-03)** — net verdict per cell; Holm(24) with T2a/T2b explicit; pooled/arm =
  disclosure-only until homogeneity shown. Intra-position MTM (L-09). ✓
- **Cost model** — binding-leg conservative per-instrument 15m round-trip (E7-frozen map), both legs a
  full market RT (pessimistic); sensitivity {0.5,1,2}× + limit-favourable as disclosure (L-02). Predeclared,
  frozen before outcome contact. ✓
- **Gate-debt discharge (binding)** — F-1 vehicle-fidelity tolerance **tightened + data-justified** (z corr
  ≥0.90 ∧ |z|≥2 Jaccard ≥0.70 vs EXP-010's loose 0.67/0.30; a powered-positive on a fidelity-failing cell
  is non-bookable). F-2 leak-resistance made **non-vacuous** (planted-positive must PASS ∧ future-destroy
  must collapse) so a null live edge still yields a leak/power read. Not a magic constant — tightened from
  the observed EXP-010 values. ✓
- **Leak tripwire(s)** — future-destroy (block-permute returns / phase-shift S5 basket) must collapse the
  edge; provenance trace `≤t-1` with the exit limit `a[t-1]` fixed at entry (no `rct[di]`). ✓
- **Fences** — per-symbol `ANALYSIS_END` = first-49% TRAIN cutoff seals analysis-TEST + final-30% holdout;
  basket mates clipped at the fence; `CloseTime` alignment. ✓
- **Budget** — extend `CrossDomainMrLimitModel.cs` (S3 single-symbol mode) + reuse S5 path; `EXP-012.conf`
  + control confs; ingest reuse; ~4 plots. Within comparative. ✓

**Info (non-blocking):**
1. Honest **LOW prior** recorded (referee prereq done; higher 15m floors partly cancel more-episodes;
   shorter-horizon net worse; CF-MR-002 exonerated). EXP-012 is **not a P-02 rescue** — a powered
   NOT-TRADABLE is a definitive close. Framing correct; keep it in the report.
2. The binding power question is **completed-reversion-episode count vs 25** (not the thousands of
   availability `n_events`). If most cells land <25 like EXP-010's 1h cells, the outcome is UNPOWERED —
   surface that honestly rather than over-reading a thin positive.

No REVISE issues. **Proceed to Stage 2 (implement):** T2a S3 single-symbol rolling-OLS-residual anchor mode
+ T2b S5 multi-symbol at domain=15m + `EXP-012.conf` (24 cells) + F-1 fidelity / F-2 plant-destroy controls;
Python ingest/validate only. **Stage 3 (the cTrader run) is operator-gated — re-confirm before running.**
