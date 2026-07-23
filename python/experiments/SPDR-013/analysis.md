# SPDR-013 — data analysis (binding read)

- **Family:** `CF-VOLDIR-001` / **HYP-B** · **Checkpoint:** 017 · **Lane:** SPDR (TRAIN-only)
- **Question (design §1 / RAW §3B):** do fast, simple direction policies (mid-term SMA benchmark;
  ATR ZigZag structure) deliver positive **expectancy in bps** — scored by availability-when-right
  / damage-when-wrong, **not win-rate** — under frozen cut-loser/let-winner capture geometry?
- **Status:** binding read; supersedes `screen.md`. **Authored in-context** at operator direction
  2026-07-23 ("hand me numbers first … present all the facts in all relevant documents"), which
  supersedes the SPDR-lane fresh-context-subagent default for this leg. Every number is re-derived
  from the emitted parquets/JSON in `results/` (not from `screen_code` narrative).
- **No verdict, no family status change, no tradability claim.** The direction-readiness call is the
  operator's at Reflection C.

```
SPREAD-COST-DISCLOSURE
  spread_cost_status: UNAVAILABLE_NOT_CHARGED
  spread_rt_bps: null
  cost_scope: PARTIAL_FEES_FUNDING_ONLY
  implication: partial_net understates true cost; reported expectancy overstated vs full cost
  prohibited_claims: fully-net, cost-complete, tradable, deployable
```

Run: 25-symbol top-volume universe × (6 D-SMA cells + D-ZZ) × 5 exit modes × 2 clocks × 2 bands =
**2940 cells, 1,639,125 episodes**. Cost = fee 11.0 + funding 1.0×stamps + allowance 2.0
(governing). Bands are labels, never gates. DESIGN primary; CONFIRM verify. Integrity self-check
**PASS**. Amendments (operator-signed 2026-07-23): DEV-1/T1 (tripwire→informative), A3 (exit modes),
E1 (medians).

---

## 0. Read for Reflection C (the highest-value output)

> Step B asked whether a simple, fast **signed** direction product clears an honest expectancy bar.
> The answer across every frozen arm is **no — not signed, and not because the exit is the only
> problem.** Three facts carry it:

1. **Signed net expectancy is cost-fatal and shows no net timing edge.** 0 of 2940 cells SUPPORTED.
   Trend arms net ≈ −9 to −17 bps ≈ the ~13.5 cost floor. Against the side-deranged null the live
   signal sits at the ~50th percentile on H1 and **below** it on M15 — the sign call adds no net
   edge over shuffling sides.
2. **The favourable move the geometry gives back is AMBIENT, not signal-granted.** Arms reach real
   favourable excursion then round-trip it (give-back 60–280 bps), but signal horizon-MFE ÷
   random-timing horizon-MFE ≈ **1.0** on every arm. Redefining the exit would lift the signal and
   random entries **equally** → it captures ambient volatility, not a directional edge.
3. **The one clean, powered positive is direction-agnostic:** the ZZ **next-swing magnitude**
   forecast (OOS IC 0.34–0.46, ridge ≥ AR1, M15 > H1, all 25 symbols). The **vol/path-noise**
   forecast is null.

**Hand-off:** signed direction is **not adequate** for a signed vol×direction combination. The
availability that exists is **ambient / magnitude-shaped**, which — with SPDR-012 (a range-based
vol *level* is reliable on H1/H4) — points to the **direction-agnostic** branch (RAW §5.2 / §3
Step C conditional), not a signed product. The operator takes the call.

---

## 1. Integrity (re-derived)

| Check | Result | Source |
|---|---|---|
| TRAIN-only; max episode exit < `train_end` (2023-12-18); no holdout | PASS (strict `<`) | `integrity_selfcheck.json` |
| Entry strictly after the signal bar; features ≤ signal bar; ATR[t−1] | PASS (construction) | `capture.simulate_signal` |
| Engine parity (sequential live == vectorised batch, §4 rules) | PASS `max_rel 0.0` | golden `engine_parity_BTC_H1` |
| Universe top-25 pin recompute == both pin files | PASS | `universe_recomputed.json` |
| Golden G1 (SMA flip) / G2 (stop next-open) / G3 (ZZ features 1e-6) + independent fixture | PASS | `golden_traces.json` |
| Derangements fixed-point-free (L-28) | PASS | `controls._derangement` |
| Parallel `--jobs` == sequential | PASS (2256 fields, 0 mismatch; spawn) | determinism check |

**Causality rests on construction + parity + predictor-side controls**, not on the future-destroy
tripwire (DEV-1). The tripwire is INFORMATIVE only: 1 of 100 powered D-SMA14 cells "survives" the
destroy (SOL SMA14 H1 CONFIRM, live −2.23), and it is **not** a positive-edge claim, so the
applicability-correct residual HARD check (no positive-edge survivor) passes.

## 2. Direction net expectancy per stratum (primary object, §5)

Bands over all 2940 cells: **UNPOWERED 2617, CONTRADICTED 323, SUPPORTED 0, WASH 0.** No stratum
clears the SUPPORTED bar (mean ≥ +5 bps, CI-low > 0, sign in ≥2/3 thirds).

DESIGN, combined arm, H1, powered cells (n≥80), median over symbols (exact):

| signal | cells | net | gross | p_right | avail_right | damage_wrong | n_ep |
|---|---:|---:|---:|---:|---:|---:|---:|
| SMA14 off | 16 | −12.5 | +1.2 | 0.29 | 241 | −98 | 811 |
| SMA14 on | 16 | −14.4 | −0.9 | 0.38 | 176 | −104 | 801 |
| **SMA25 off** | 16 | **−8.7** | **+5.1** | 0.31 | 263 | −106 | 548 |
| SMA25 on | 16 | −12.6 | +1.0 | 0.40 | 194 | −117 | 480 |
| SMA50 off | 16 | −11.9 | +1.9 | 0.30 | 259 | −111 | 368 |
| SMA50 on | 15 | −13.6 | +0.1 | 0.40 | 204 | −115 | 274 |
| D-ZZ | 15 | −9.6 | +4.9 | 0.47 | 244 | −200 | 231 |

(M15 combined: net −14 to −17, gross −2 to −3, `p_right` 0.28–0.43, avail 84–131, damage −47 to
−105, n 1.1k–3.4k.)

- **Shape:** low hit-rate (`p_right` ≈ 0.29–0.47) with large availability when right (≈ 176–263 bps
  H1) and smaller damage when wrong — the intended let-winners-run profile. **Gross is breakeven-to-
  slightly-positive on H1** (SMA25 off +5.1, D-ZZ +4.9 the best); **net is cost-fatal** (≈ the 13.5
  cost floor).
- **Best net cell family:** SMA25 off H1 (−8.7, gross +5.1) — still negative after partial cost.
- **CONFIRM does not hold the thin gross edge:** combined H1 gross +1.6 (DESIGN) → −0.6 (CONFIRM);
  net −12.0 → −14.3.

## 3. Expectancy decomposition & fat tails (§5 + AMENDMENT-E1)

Mean vs median (bps), combined SMA14 SOL H1 (illustrative): mean −2 vs **median −47** — the mean is
propped by rare large winners; the typical episode is a larger loser. This mean/median gap recurs;
`stop`/`trail` arms are one-tailed (a single runaway winner drives a positive mean on a handful of
episodes → all UNPOWERED). **Win-rate is disclosure-only and never drove a band.**

## 4. Exit-mode decomposition (AMENDMENT-A3)

DESIGN, median over symbols (powered where labelled):

| exit_mode | H1 net | M15 net | note |
|---|---:|---:|---|
| combined | −12.0 | −15.3 | full §4 stack |
| signalflip (= ZZ structural leg) | −12.6 | −16.6 | signal-flip only |
| time | −30.1 | −24.8 | symmetric avail≈|damage| (~450 each), p_right≈0.48 → coin-flip gross |
| stop | −294 / n=1 | −131 | winners run to band edge; tiny n; ALL UNPOWERED |
| trail | — | +66 (n=28) | one-tail; ALL UNPOWERED |

- `combined ≈ signalflip` on net → the signal-flip exit dominates; stop/trail/time rarely bind on
  the trend arms. **`stop`/`trail`/`time` are 100% UNPOWERED** (degenerate episode counts / fat
  tails) — not interpretable as expectancy.
- **Gross** structural leg (signalflip) > risk-managed combined: the risk cuts reduce gross (they
  trade a bit of the fat right tail for smaller drawdown) but neither clears cost.

## 5. MFE / capture geometry (operator question — the decisive section)

Per-episode MFE/MAE emitted (`mfe_oo_bps`, `mae_oo_bps`, `mfe_hi_bps`, `horizon_*`). **All MFE reads
are non-tradable ceilings** (peek at the within-window peak). `analysis_code/mfe_capture.py` →
`results/mfe_capture_by_arm.parquet`, `mfe_signal_vs_random.parquet`.

**(a) The geometry gives back reached favourable ground** (DESIGN, median over symbols):

| arm (H1) | reached MFE_oo | realized gross | give-back | net ceiling (MFE−13.5) |
|---|---:|---:|---:|---:|
| SMA14 combined | +25 | −40 | 64 | +11 |
| SMA25 combined | +30 | −40 | 71 | +17 |
| **D-ZZ signalflip (structural leg)** | **+194** | −86 | **280** | **+180** |

Arms reach favourable excursion, then round-trip it into losses; worst on the ZZ structural leg and
long-hold arms. Taken alone this looks like a capture-geometry failure (Mode B/C).

**(b) But the favourable excursion is AMBIENT, not signal-granted** — the decisive control:

| signal horizon-MFE ÷ random-timing horizon-MFE | H1 | M15 |
|---|---:|---:|
| every arm (`sig_over_rand`) | **0.95–1.03** | 0.97–0.99 |

Signal entries reach **no more** forward favourable excursion (~300–370 bps over the cap window)
than random-timing entries with random sides. The horizon availability is ambient crypto
volatility. This matches the derangement percentile ≈ 0.5.

**Conclusion (the operator's question, answered):** the give-back is real, but it is **ambient
volatility the direction signal fails to select**, not a directional edge the exit is squandering. A
redefined exit would lift the signal **and** random entries equally. So this is **not** "available
[directionally] but capture geometry needs redefinition"; capturing the give-back is a
**direction-agnostic / volatility-harvest (straddle-class)** proposition, not a rescue of signed
direction. It aligns with the RAW §5.2 direction-agnostic branch and SPDR-012's reliable vol level.

## 6. Controls (§6)

| Control | Read (combined arm, median over powered cells) |
|---|---|
| DIRECTION-DERANGEMENT | live percentile vs side-shuffled null: H1 DESIGN 0.57 / CONFIRM 0.48; **M15 0.20–0.28** (worse than shuffled). +20 bps bite plant detected. → **no net sign-timing edge.** |
| MATCHED-RANDOM-ENTRY | live percentile 0.52–0.60 — marginally above random timing; +20 bps bite detected. |
| SMA-BENCHMARK Δ (ZZ − SMA14/25) | median Δ ≈ 0 (+0.2 to −2.2 bps) — **ZigZag does not beat the dumb SMA** on expectancy. |
| PATH-FUTURE-DESTROY tripwire | INFORMATIVE (DEV-1); 1 non-positive-edge survivor of 100 D-SMA14 cells. |

## 7. ZZ next-move forecast heads (§3.3, mandatory) — OOS IC, median over 25 symbols

| target | AR(1) H1 | AR(1) M15 | ridge H1 | ridge M15 |
|---|---:|---:|---:|---:|
| next-swing **magnitude** (bps) | 0.343 | 0.436 | 0.372 | **0.457** |
| next-swing **path_noise** (vol) | −0.037 | −0.022 | −0.002 | −0.000 |

- **Next-swing magnitude is forecastable** — the single clearest powered positive in the screen
  (IC 0.34–0.46; ridge ≥ AR1; M15 > H1; all 25 symbols). Direction-agnostic (magnitude, not sign).
- **Next-swing path_noise/volatility is not** (IC ≈ 0 both models, both clocks).

## 8. ZZ structural leg (signalflip) per symbol — DESIGN H1 (all UNPOWERED)

Net (partial) positive on the majors, but **UNPOWERED via MDE (fat tails), not trade count** (n ≈
230–250): SOL +32.5, OP +28.1, AVAX +24.8, BTC +8.5, ETH +5.5; negative on BNB −28.5, INJ −30.1,
1000LUNC −54.6, 1000BONK −166 (n=49). Gross higher throughout. Interpretation: the raw structure
reaches sizeable favourable excursion on the majors, but the per-symbol variance is too large to
certify and — per §5(b) — the availability is not signal-selected.

## 9. Evidence FOR vs AGAINST signed-direction adequacy

**FOR (weak):**
- Gross ≈ breakeven on H1 trend arms (+1.6 median); avail-when-right ≫ |damage-when-wrong| in
  magnitude (220–310 vs ~100 bps) — the let-winners-run shape exists.
- ZZ structural-leg net positive on several majors (SOL/OP/AVAX/BTC/ETH), though UNPOWERED.

**AGAINST (strong):**
- 0 of 2940 cells SUPPORTED; net cost-fatal ≈ cost floor.
- No net sign-timing edge (derangement ≈ 0.5 H1, <0.5 M15).
- ZigZag ≈ SMA (benchmark Δ ≈ 0) — the "smarter" object does not beat the dumb one.
- The reached favourable excursion is **ambient** (signal MFE ≈ random MFE) — no directional
  availability to capture.
- Thin gross edge does not survive DESIGN→CONFIRM.

## 10. Recommended read for Reflection C (operator decides; not a verdict)

1. **Signed direction: not adequate** for a signed vol×direction combination (SPDR-014). It is
   cost-fatal, shows no net timing edge, its availability is ambient, and the ZigZag adds nothing
   over the SMA benchmark.
2. **The permitted forward path is direction-agnostic** (RAW §5.2 / §3 Step C conditional): the real
   ingredients are (i) SPDR-012's reliable range-based **vol level** on H1/H4, (ii) the ambient
   favourable excursion any entry sees over an intraday horizon, and (iii) the **ZZ next-swing
   magnitude** forecast (IC 0.34–0.46). A both-side / straddle-class or magnitude-conditioned
   structure is the object worth freezing at Reflection C — **if** risk can be managed and only
   under the partial-cost caveat.
3. **Do not** freeze a signed combination on these results. **Do not** read any positive mean cell
   as an edge — all are UNPOWERED and the MFE control shows the availability is ambient.

## 11. Reproducibility & compliance

- Full clause map + amendments: `results/compliance_trace.md`. Interpretation notes IN-1..IN-4
  (per-clock ATR, open-HWM, stop-exit price, DESIGN-primary) weaken no clause.
- Deterministic: fixed seeds; `--jobs` parallel bit-identical to sequential.
- Artifacts (§10): `episodes.parquet` (incl. MFE/MAE + `right`), `expectancy_by_cell.parquet`,
  `zz_features.parquet` (incl. next-swing targets), `zz_forecast.json`, `controls.json`,
  `golden_traces.json`, `integrity_selfcheck.json`, `mfe_capture_by_arm.parquet`,
  `mfe_signal_vs_random.parquet`, `numeric_dump.md`.
