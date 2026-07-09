# EXP-007 — E6: P*-capable Referee Variant — Report

**Phase:** 001 (referee renew, D-referee). **Classification:** analysis-only. **Reads/slots:** 0/0;
global holdout sealed. **Verdict:** **FROZEN (2026-06-29)** — ADOPT ratified at operator freeze sign-off; `gate_stack_pstar`
hash-pinned in `results/freeze_manifest.json` (`referee_pstar.py sha256=1fd06b28…4f23`; prior suites
byte-unchanged, hashes == E5).
**Audit:** PASS, 0 Critical (`audit.md`).

## Question

Can an **additive** P*-capable adjudication path — §10.3a's exact leg logic with the **signal leg
sourced from an injected engine-realized per-bar net series** instead of `position·market-return` — be
FPR-recalibrated to match-or-better the frozen suite's dogfood-negative FPR while keeping finite power on
a realized positive, and frozen before any live read? **Answer: YES (constructible).**

## Why it exists (architecture problem)

Both frozen gates score `position·market-return` only: §10.3a (`referee_adaptive.gate_stack_adaptive`,
hash-frozen at E5) hardcodes the signal leg as `strategy_return_bps_turnover(returns, positions)` with
**no `strategy_fn` seam**; the frozen Chapter-01 suite hardcodes `strategy_return_bps(returns,
positions)`. CF-MR-002's faithful exit (EXP-006) is an intrabar **engine-realized `P*` favourable-limit
fill** — a realized series ≠ `position·market-return` — which the frozen gates structurally cannot
consume, and the E5 freeze forbids editing them (same architecture limit that forced CF-MR-001's bespoke
intrabar fill engine, the L-01 leak site). E6 supplies the missing path **additively** so D-benchmark can
report a faithful realized-fill verdict. Cross-ref: EXP-006 amendments A1 (faithful `P*` fill ratified) /
A2 (defer + build E6), checkpoint AMENDMENT (2026-06-29).

## Method

New module `python/src/xen/referee_pstar.py`:
- `gate_stack_pstar(returns, positions, realized_bps, …)` — faithful mirror of `gate_stack_adaptive`
  with **exactly one** computational change (`strategy = realized_bps` instead of
  `strategy_return_bps_turnover(...)`); every sub-primitive (L1 floor, L3 vs-naive on the frozen
  market-return reference, L5 pooled + studentized sub-pop, block bootstrap, split) imported from the
  frozen modules and reused unchanged; same dict schema → `adaptive_row` consumes it unedited. No new
  threshold/knob/constant.
- `make_realized_fill(...)` — causal resting-bracket realized net series for **synthetic calibration
  substrates only** (the analog of the engine's `ExitFillPrice`); both bracket limits rested `≤ t-1`.

Substrate: the EXP-002 32-strata grid (16 instruments × {1h,4h}, 2021-era files = the §10.3a calibration
grid), open-to-open `≤ t-1` real returns, first-70% slice; holdout never loaded. Three arms per stratum,
**per-stratum binding** (L-03; pooled = disclosure-only). N_BOOTSTRAP=500, N_NULL=80, N_PLANT=20.

## Results (per-stratum; 32/32 unless noted)

| Arm | Test | Result | Bar | Pass |
|-----|------|--------|-----|------|
| **R** | reduction identity: `pstar(realized:=turnover)` vs §10.3a | core **bit-identical 32/32**; verdict identical 32/32 | byte-identical | ✓ |
| **R** | frozen modules byte-hash (pre==post) | `referee_adaptive b4fd6cb1…ae847` (== E5 freeze), `referee_calibration 04f933f6…7994` unchanged | unchanged | ✓ |
| **N1** | symmetric-limit (fav=adv) on block-permuted no-edge returns → must REJECT | **0/32** passes | ≤ §10.3a (0) | ✓ |
| **N2** | future-destroy (permute market returns, then realize) → must collapse | max **0.0125** (5×4h strata at 1/80; 27/32 = 0) | ≤ 2α=0.10 | ✓ |
| **N3** | dogfood-negative (Donchian/MA lagged) via realized path → must REJECT | **0/32** passes | ≤ §10.3a (0) | ✓ |
| **P** | realized positive (planted drift through wide bracket) → finite power | **32/32 finite**, MDE 0.5–4.0 bps | finite | ✓ |

Per-stratum table: `results/per_stratum.csv`. Plots: `plots/arm_r_agreement.png`,
`plots/arm_n_fpr.png`, `plots/arm_p_mde.png`. **No pooling** — "32/32" is the per-stratum minimum, not an
average; the audit's masking check confirms no stratum flips.

## Interpretation (anchored to the predeclared DET-dominance adoption rule)

Adoption rule (design): ADOPT iff Arm-R byte-identical ∧ Arm-N FPR ≤ §10.3a dogfood FPR ∧ Arm-P finite
power, per stratum. **All three met on all 32 strata → ADOPT.**

**Mechanism (why ADOPT):**
1. **Source-swap equivalence (R).** The `inspect`-diff confirms one change; the reduction identity proves
   that when `realized := strategy_return_bps_turnover(...)` the path is a no-op over §10.3a → it inherits
   §10.3a's earned FPR control by construction for any position-state input.
2. **Symmetric-truncation no-phantom (N1).** The genuinely new FPR risk is a realized series that ≠
   `position·return` manufacturing a phantom edge (the L-01/L-02 favourable-only asymmetry). The binding
   N1 **symmetric** bracket truncates favourable and adverse tails equally → expectancy ≈ 0 on a
   martingale → the unchanged L1/L3/L5 legs reject (0/32; independently re-derived held-mean −0.215 bps).
   The leak class is exactly what N1 controls, and it does not pass.

**Honest caveat (not buried).** In returns-space the bracket **caps** (clips the per-bar net return); it
**cannot capture an intrabar excursion the close misses** (that needs intrabar High/Low). So the realized
series never exceeds position-state magnitude here, and **Arm P validates finite power on a realized
series — the binding criterion — NOT capture-beyond-position-state.** The true intrabar `P*` capture (the
property that made CF-MR-001 *look* tradable) is exercised by the **real cTrader engine in EXP-006**, not
in this calibration. The P*-capable gate is agnostic to how `realized_bps` is produced; E6 validates the
gate's *statistical* behaviour (equivalence + FPR control + power) on realized series.

**N2 artifacts.** The 5×4h strata at 1/80 are the E4-characterized `wilson_lower(1,N)>0` single-pass label
artifacts (true FPR ≤ 0.0125 ≪ 2α; Wilson-lower ≈ 0.002). Under the E4-derived freeze-adjudication rule
(`MIN_FPR_PASSES=2` / `2α`) adopted candidate-blind at E5, a single 1/80 pass is **not** an FPR-control
failure; the strong planted edge collapsed from power≈1.0 → the future-destroy tripwire held.

## Audit caveats (from `audit.md`, PASS)

- Causal-provenance pass clean: `make_realized_fill` output `[:t]` is byte-invariant to future bars (no
  look-ahead); no `rct[di]` own-close-as-limit pattern (P-09); analysis-only (no price→signal).
- Leak tripwires all held: T1 (N1 symmetric 0/32), T2 (N2 future-destroy collapse — **fixed+rerun**: an
  earlier control permuted the realized P&L output, preserving its mean → FPR 1.000; corrected to permute
  the market returns at the **input** per L-07, re-ran clean), T3 (byte-freeze + reduction identity).
- 1 Warning (N2 1/80 artifacts, non-material); 3 Info (Arm-P caveat above, bracket path-ordering
  simplification, matplotlib deprecation).

## Conclusion & next step

**ADOPT** — `referee_pstar.gate_stack_pstar` is §10.3a plus a leak-safe signal-leg source swap; it is
constructible with FPR control and finite power, frozen-suite byte-unchanged. **Next (operator-gated):**
FREEZE + hash-pin `gate_stack_pstar` (own `freeze_manifest.json`, recording the prior suites' unchanged
hashes) **before** any CF-MR-002 read (L-12). Then **EXP-006 (D-benchmark) resumes**: run `RsiFadeModel`
in-engine and adjudicate CF-MR-002 under the frozen old suite + §10.3a (position-state proxy) + the new
E6 P*-gate (realized fill) — parallel disclosure.

## Links
`design.md` · `code/run_experiment.py` · `python/src/xen/referee_pstar.py` · `audit.md` ·
`results/per_stratum.csv` · `results/byte_freeze_check.json` · `plots/`

## Registry disposition
**Not applicable (referee-method experiment)** — no candidate family adjudicated, no slot consumed, 0
counted TEST reads. CF-MR-002 untouched and **not** tuned (L-12 guard honored). E6 adds an adjudication
path only; the candidate screen is D-benchmark (EXP-006).

---

## GATE: APPROVE (orchestrator inline post-exec, 2026-06-29)

Checked against `references/governance-constraints.md`:
- **Verdict forensics present** (`audit.md`): per-stratum re-derivation + masking check (no pooling —
  32/32 is the per-stratum minimum), mechanism (source-swap equivalence + symmetric no-phantom),
  gate-shape check (no mismatch; honest returns-space caveat recorded). ✓
- **Causal-provenance & leak pass present**: provenance trace (realized series `≤ t-1`; future-invariance
  verified), leak tripwires T1/T2/T3 held, shared-module contract verified, no `rct[di]`/P-09 pattern. ✓
- **Every verdict-material finding fixed-and-rerun**: the N2 control bug (permuted realized output →
  FPR 1.000) was fixed (permute market-return input, L-07) and the full 32-strata run re-executed clean. ✓
- **Additive freeze respected**: frozen modules byte-unchanged (hash == E5); §10.3a/`adaptive_row` reused
  unedited; reduction identity 32/32. ✓
- **Per-stratum binding** (L-03); UNPOWERED-not-FAIL semantics; **not tuned on CF-MR-002** (L-12). ✓
- **Registry disposition recorded** (referee-method; not applicable). ✓
- **Holdout** sealed; first-70% only; 0 reads/slots. ✓

No REVISE/REJECT issues. **ADOPT — pending operator freeze sign-off** (the freeze hash-pin is the
operator-gated act; not written here). On sign-off: write `results/freeze_manifest.json`, advance status,
then resume EXP-006.

**FREEZE SIGN-OFF (operator, 2026-06-29).** Ratified. `results/freeze_manifest.json` written —
`gate_stack_pstar` hash-pinned (`referee_pstar.py sha256=1fd06b28df463535da7e750a1c7baa0bc02fb445442b206d1765413d0ada4f23`),
prior suites recorded byte-unchanged (`referee_adaptive b4fd6cb1…ae847` == E5, `referee_calibration
04f933f6…7994`). **Status → FROZEN.** D-benchmark (EXP-006) resumes.
