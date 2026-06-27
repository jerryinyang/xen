# EXP-094 — Audit (Stage 5, verdict forensics)

**Phase 021 · CF-MR-001/HYP-002 · `D0-amendment-004`+`005`.** Experiment verdict as run:
**`HALT_BITE_NOT_GREEN`** (binding verdict withheld). Audit scope: code, results, scope/plan compliance,
holdout/real-price/determinism integrity, and **verdict forensics** (per-stratum re-derivation + masking check,
mechanism statement, gate-shape check) on the legs that *would* drive the verdict if the bite-check were GREEN.

## 0. Headline

The implementation is **sound** and the substantive finding is **well-supported on the powered set**: on the
**6 powered 4h members**, real EXIT-RCT **beats the matched-distance oscillation null 6/6** (binding §4(c)),
and the net screen passes 6/6 (leg b). **But the binding verdict is correctly HALTED** by a **verdict-material
bite-check miscalibration** (the power leg planted an effect ~10× below the statistic's detection threshold).
Per the materiality gate this must be **fixed and re-run** before a binding `ADMIT_4H` can be issued. **Audit
verdict: INCOMPLETE-AS-BINDING → return to `experiment-developer` for the bite-check power-leg fix (+ a
disclosed fairness sensitivity), then RE-RUN.**

## 1. Integrity (clean)

- **Determinism PASS** (replay EURUSD-4h, GBPUSD-4h; net_ci_low / net_clear / delta_lo / beats_random
  frame-identical). Headline CSVs SHA-256-pinned; `cost_table_hash = fa7c887…` (= the `D0-amendment-003` table;
  shared `COST_CONSTANTS` not mutated).
- **Holdout sealed** (`holdout_untouched=true`; TRAIN sub-split only via the reused EXP-090 loader). **0 counted
  TEST reads, 0 candidate slots.** Real OHLC throughout (real touched fill levels + real ATR; no HA/Renko).
- Resolution fractions 0.986–0.993; min n_resolved 855 (XAUUSD-4h) — no thin-cell power concern on the members.

## 2. Per-stratum re-derivation + masking check (LESSON-001)

**The pooled headline does NOT mask heterogeneity — but it corrects a prior over-claim.**

| 4h cell | readiness | real RCT net_mean | null net_mean | Δ_cell | Δ_lo | beats? |
|---|---|---|---|---|---|---|
| AUDJPY | MEMBER | +0.138 | −0.144 | +0.282 | **+0.234** | yes |
| EURUSD | MEMBER | +0.158 | −0.117 | +0.275 | **+0.226** | yes |
| GBPJPY | MEMBER | +0.108 | −0.168 | +0.276 | **+0.229** | yes |
| XAUUSD | MEMBER | +0.144 | −0.104 | +0.248 | **+0.193** | yes |
| USDCHF | MEMBER | +0.144 | −0.102 | +0.246 | **+0.200** | yes |
| EURJPY | MEMBER | +0.075 | −0.203 | +0.278 | **+0.226** | yes |

All 6 powered cells beat the null with `Δ_lo` ∈ [0.19, 0.23] — **homogeneous, not carried by one cell** (drop
any single cell and the quorum still holds at 5/5). EURJPY has the smallest real net (+0.075) but the *largest*
gap (null most negative) — no boundary-fragile cell.

**Masking correction (verdict-material context):** the readiness gate (leg a) returns **6 MEMBER / 7
COVERAGE_EXCLUDED**. Six of TEMP-091's twelve "net-clearing" 4h cells — **AUDUSD, GBPUSD, NZDUSD, US2000,
USDJPY, USTEC-4h** — have **no finite RCT MDE** (cannot bound a confirmation) and JP225-4h fails to build.
**TEMP-091's "RCT net-clears 12/12" was an over-claim:** half those cells are unpowered. The honest powered
breadth is **6 cells (6 instruments)**, and — notably — the **indices TEMP-091 highlighted (USTEC-4h, US2000-4h)
are excluded**; the powered set is JPY-cross / EUR-GBP-CHF major / gold. This is exactly why the readiness leg
was mandated; it caught a naive-screen over-claim.

## 3. Mechanism statement (why real beats the oscillation null)

A **completion-rate** mechanism, not a magnitude artifact. Both arms rest a favourable limit at the **same target
distance** (μ_mean ≈ 0.51–0.55 ATR, resampled from the real cell's RCT target multiples) with the **same**
2×ATR stop + MR-tempo cap + 1m fill + cost. The difference is *when* the limit is placed:

- **Real (fade extreme):** RCT target hit on **~99% of events** (`terminal_fav` 0.98–0.99) → net **positive**
  (+0.07…+0.16).
- **Matched-distance null (random times):** the *same-distance* limit is hit on only **~64–67%** of events
  (`rand_terminal_fav`) → the ~1/3 that miss run to the 2×ATR stop / cap → net **negative** (−0.10…−0.20).

So entering at a genuine RSI extreme lifts the reversion-completion rate **~65% → ~99%** for an identical target
geometry. The 4h edge is **the entry signal, not generic oscillation harvesting** — the EXP-089 dead-by-absence
(1/14) is, on the powered cells, a metric-specific false negative of the ~3-bar MFE_med availability statistic,
which did not see the RCT-capturable completion geometry. *(This is the substantive finding the corrected
bite-check rerun would let the verdict express.)*

## 4. Gate-shape check + the binding finding (the RED bite-check)

**The binding gate can see the effect's shape** (matched-distance paired-Δ quorum: 6/6 cells, Δ_lo well clear of
0). **The gate's calibration (bite-check) is RED — and this is the verdict-material finding (CRITICAL).**

- **FPR leg = 0.000** (≤ 0.10): under a same-distribution null the quorum never falsely fires → **no
  false-admission risk**. The leg that actually protects against a spurious ADMIT *passes decisively*.
- **Power leg = 0.000** (< 0.80): the leg failed to **exactly zero**, a structural tell. **Diagnosis
  (quantitative):** the power leg planted the per-cell single-arm MDE = **0.025 ATR**, but the two-sample
  difference statistic has one-sided SE ≈ **0.029 ATR** (read directly off `Δ_cell − Δ_lo ≈ 0.048 = 1.645·SE` on
  every cell), so its per-cell detection threshold is ~**0.048 ATR**. Planting 0.025 < 0.048 makes
  `Δ_lo(planted) < 0` **by construction** → 0/300 → power 0. The planted effect is ~10× below the **real**
  effect (~0.27 ATR), which the statistic detects ~5× over threshold.
- **Empirical power is in fact present** — the statistic detects real effects on **6/6** 4h members (Δ_lo
  0.19–0.23) and on **5/5** 1h positive-control cells (Δ_lo 0.25–0.30). The question the power leg was meant to
  answer ("can the gate see a true signal?") is answered **yes** by the data; the RED is a **mis-specified
  power-leg calibration** (wrong planted-effect scale + quorum-compounded rather than per-cell evaluation), not a
  defective binding statistic.

**Materiality (blocking).** The bite-check gates the verdict (HALT → would-be ADMIT). It is therefore
**verdict-material**: it must be **fixed and re-run**, not down-classified. **Prescribed fix (route to
`experiment-developer`):**
1. Power leg: evaluate **per-cell** detection rate (not the compounded ≥5/≥3 quorum-fire), and plant a
   **two-sample-appropriate** effect — a small grid `g ∈ {0.05, 0.10, 0.15, 0.20}` ATR — reporting the
   **two-sample per-cell MDE** (smallest g with mean per-cell TPR ≥ 0.80). GREEN-power iff that MDE is finite and
   **≤ the observed real−null Δ** (the gate can detect the real effect). Keep the FPR leg unchanged (per-cell ≤ α
   ∧ quorum-fire ≤ α).
2. Re-run. Leg (a) readiness is the expensive step (~47 min); legs (b)/(c)/(d)/(e) are seconds — consider
   caching the resolved arrays so only (e) recomputes, but a full re-run is acceptable and preserves
   determinism.

## 5. Warning (non-verdict-flipping) — matched-distance is mildly anti-conservative

The static null places the favourable limit at the **entry-bar** RCT target multiple (μ_mean ≈ 0.51–0.55 ATR),
which exceeds the real RCT **realized gross capture** (~0.27 ATR; the trailing target captures less than the
entry-bar nominal). A farther favourable target is **harder** for the null to hit → null nets worse → mildly
**favours admission (anti-conservative)**. The completion-rate mechanism (§3, 99% vs 65%) is about *timing* not
distance, and the margins are large (Δ_lo ≈ 0.2), so a flip is unlikely — but the rerun should add a **disclosed
sensitivity** matching the null distance to the *realized* capture (not the entry-bar target) to bound this.
Classified **Warning** (disclose + sensitivity), not blocking.

## 6. Disclosed deviations (reviewed, non-material)

- **PARTIAL-TRAIL omitted** from leg (b) (5 engine arms screened); net-cleared 0 cells in EXP-091 and TEMP-091 →
  immaterial to the binding RCT verdict. Accept.
- **Random draw from EXP-090 `eligible_pool`** (look-ahead-safe, real-entry-fenced) rather than `random_entries`
  over all bars — a correctness-consistent choice. Accept.

## Audit verdict

**INCOMPLETE-AS-BINDING (HALT confirmed correct).** Integrity clean; the substantive finding (4h edge is
signal-driven on 6 powered cells, via a 65%→99% completion-rate lift) is well-supported and well-explained; the
masking re-derivation corrects TEMP-091's over-claim (6 powered, not 12). **One CRITICAL verdict-material
finding:** the bite-check power leg is mis-calibrated (planted effect below the two-sample threshold), gating the
verdict. **Route to `experiment-developer` for the §4 fix (+ §5 sensitivity) and RE-RUN; the binding `ADMIT_4H`
vs `4H_CLOSED_OSCILLATION` verdict cannot be issued until the corrected bite-check returns GREEN.** No verdict-
material number may be acted on (no registry advancement to ADMIT, no EXP-092 4h carry) until then.

---

## Re-audit (corrected bite-check + realized-capture sensitivity rerun, 2026-06-24)

The Stage-3 fix (per-cell power leg at a fixed 0.10-ATR reference; exact `Δ_lo(null+g,null)=Δ_lo(null,null)+g`
grid identity; +realized-capture sensitivity; content-keyed readiness cache) was applied and the experiment
**re-run**. The CRITICAL finding is **resolved**; all verdict forensics re-confirm.

- **Bite-check GREEN** (`bite_check.json`): FPR per-cell 0.052 ≤ 0.10, quorum-fire 0.000; **per-cell power at
  the 0.10-ATR reference 0.857 ≥ 0.80**; two-sample per-cell MDE **0.10 ATR**, well below the observed median
  real−null Δ **0.276** (the gate detects the real effect ~2.8× over its MDE). The earlier RED is confirmed a
  power-leg miscalibration, now corrected. *(Per-cell power at the reference is comfortably but not hugely above
  the 0.80 floor — non-limiting since the gate's MDE 0.10 ≪ the ~0.27 real effect; disclosed.)*
- **Binding verdict `ADMIT_4H`** — leg (b) RCT net-clear **6/6 cells / 6 instruments**; leg (c) matched-distance
  falsification **6/6** (`delta_lo` 0.19–0.27); 1h positive control **5/5**. Per-stratum re-derivation, masking
  correction (6 powered, not TEMP-091's 12), and the 65%→99% completion-rate mechanism are **unchanged** from
  §2–§3 (determinism byte-identical; replay PASS).
- **§5 Warning closed.** The realized-capture sensitivity null (limit distance resampled from the realized
  favourable capture `{κ_k}`, mean ~0.36–0.38 ATR, nearer than the entry-bar target ~0.51–0.55) **also nets
  negative on all 6 cells** (rand_realized_net_mean −0.07…−0.20) and real beats it **6/6** (`delta_lo_realized`
  0.17–0.30, `beats_realized` true ∀). Admission is **robust to the matched-distance choice** — the
  anti-conservatism flagged in §5 does not move the verdict.
- **Robustness note (strengthens the EXP-092 carry):** all 6 4h members are **mean *and* median net-positive**
  (net_median +0.016…+0.132) — unlike the 1h EXP-091 pass (3/5 median-negative). The powered 4h set is a
  defensible robust core, not a tail-carried one.
- **Safe-optimization integrity.** Readiness cache: `use_cache=true`, **0/13 hits this run** (cold — computed
  fresh and wrote the cache; deterministic, content-keyed; holdout untouched). Bite-check `d+g` identity is an
  exact algebraic equivalence (no result change). Determinism replay PASS; `cost_table_hash` unchanged
  (`fa7c887…`); shared `COST_CONSTANTS` not mutated.

**Re-audit verdict: PASS.** Integrity clean; the binding `ADMIT_4H` is sound, FPR-controlled, robust to the null
distance, and well-explained mechanistically; the one CRITICAL finding is fixed-and-rerun (not down-classified).
Cleared to Stage 6/7/8: advance the registry to **4h ADMITTED (domain expansion, 0 new slots)** and carry the 6
powered cells to EXP-092 — TRAIN-only, **0 counted TEST reads**, 4h strata stay 0/2.
