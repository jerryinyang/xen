# SPDR-007 — Report: the statistical spine (S1+S2), CF-SIGAUC-001 master gate

**Item:** SPDR-007 · **Family:** CF-SIGAUC-001 · **Checkpoint:** 014 §4 seq 3 · **Lane:** SPDR (TRAIN-only)
**Run:** 2026-07-21 · **Bands:** DESIGN estimate → CONFIRM verify (both TRAIN-INTERNAL) · **0 counted reads · TEST untouched · holdout SEALED**
**Artifacts:** [design.md](design.md) · [qa-review.md](qa-review.md) (runs 1–3) · [screen.md](screen.md) · [analysis.md](analysis.md) · [analysis_code/analyze_spine.py](analysis_code/analyze_spine.py) · `results/*` · `plots/*`

---

## 1. Operator verdict (recorded)

**`NOT_WORTH` — for the price-only S1/S2 spine (a P-01 confirmation).** Operator, 2026-07-21.
Experiment-level disposition only — **no family status change** (that is a checkpoint-retrospective act). Analyst recommendation (analysis.md §6): `NOT_WORTH` — matches.

**Plain meaning:** the anchored-breakout target level (the Protection quantile) does reproduce out-of-band, but that reproduction is a property of price paths having quantiles, not an edge of the acceptance conditioning. Against a matched unconditional entry the accepted breaks add ≈ nothing, and the target-before-stop race sits at gross breakeven and **loses after costs** on every major. This is exactly the P-01 pattern the family card §5 anticipated for the *price-only* spine.

## 2. Question + mechanism

**Falsifiable question:** does the DESIGN-estimated Protection quantile reproduce on the next band, **and** does conditioning on an accepted anchored break beat a matched, same-phase, same-side unconditional entry (R5 binding)? Money floor computed first.
**Mechanism (price-only spine):** an anchored 15-min balance fixes the session reference; the first side to force acceptance beyond an edge is claimed to win the session, so the remainder resolves asymmetrically. Single-leg, session-horizon object. **No Δ (signed flow) is used here** — the family's signed warrant is deferred to checkpoint-015.

## 3. Method

Frozen INFR-018 pin (registry `5c386984…`): anchor **A-USOPEN**, IB **L=15 min**, A6 **D4-t50-w30, δ=0**. Event = every A6-accepted poke (DESIGN **7,070** / CONFIRM **11,375**). Protection Level = the (1−p) quantile of favourable excursion in IB-width units, estimated on DESIGN, frozen (`protection_freeze.json` pin `a45eac44…`), verified once on CONFIRM. Reads R0–R5 each measured **signal minus a matched cross-session control** (D-1). Day-clustered block bootstrap (source §6b). One entry-evaluator serves real/control/tripwire arms (exit-matched, L-24 F04).

## 4. Key evidence (per-stratum; pooled disclosure-only — L-03)

**R0 money floor (computed first, not the killer):** cost floor ≈ 14–16 bps RT; TP1 (pooled p70) = 1.796 IB widths ≈ 88–173 bps on the majors — **ABOVE_FLOOR** everywhere. Target *size* clears cost.

**R1 master gate — the quantile reproduces:**

| p | q̂ (DESIGN, IBw) | CONFIRM hit | calib_err |
|---|---|---|---|
| 0.65 | 2.175 | 0.680 | **+0.030** |
| 0.70 | 1.796 | 0.728 | **+0.028** |

Pooled |err| ≤ 0.05 → REPRODUCES. Source framework-falsifier #1 (“no anchor reproduces a ~65–70% Protection quantile”) is **not** triggered on reproduction grounds. **But per-symbol is heterogeneous** — SOL p70 calib_err **+0.105 (BROKEN)**; label census 51 REPRODUCES / 25 DRIFTED / 21 BROKEN of 97 symbols — pooling masks this.

**R2–R5 — the conditioning adds ≈ nothing over the matched control (the binding reads):**

| Read | Contrast (signal − control) | Uncertainty | Read |
|---|---|---|---|
| R2 race win-rate (p70) | **−0.010** (w_sig 0.333, w_ctl 0.343) | MDE 0.03 in w-units | at gross breakeven, no lift |
| R2 vs **cost-adjusted** breakeven (majors) | w − p0ᶜ = **−0.05 to −0.14** | well-powered | **below cost breakeven on all 5 majors** |
| R5 excursion asym (day-clustered) | **+0.090** | 95% CI **[−0.231, +0.320]**, MDE 0.50 | WASH (includes zero) |
| R3 regime ρ-contrast | ≈ **−0.04** (finite-only) | — | no positive regime edge |
| R4 Δ-coherence tercile | **+0.077 IBw** / **+0.012 w** | n=6,961 | negligible stratification |

**P-01 (the null that kills the price-spine story):** the control's own Protection quantile (1.62 IBw) is within ~10% of the signal's (1.80), and control paths hit the signal's level 67.5% (≈ p). Reproduction is what price paths do — not acceptance skill.

## 5. Integrity gates (HARD — all clean)

| Gate | Result |
|---|---|
| Future-destroy tripwire (outcome-path-swap) | **NO_MATERIAL_EDGE** — no material raw edge to leak-test; not a hard fail (design §4.3 material-edge precondition) |
| Tripwire positive-control bite | **corr 0.77** — the swap genuinely installs the donor outcome (real teeth) |
| Freeze-before-CONFIRM · band fences · causal ≤ t−1 · no per-level Δ · no local accounting | asserted (raise, not warn), clean; QA run 3 APPROVE |

## 6. Analysis caveats (from analysis.md)

- **R3 screen bug (non-decisive):** `r3_regime` used `drop_nulls`, which does not drop float `NaN`; 1,930 warmup NaN (27%) polluted the Spearman, reporting ρ-contrast +0.130. Finite-only recompute is **−0.040** (sign flip). R3 ≈ 0 either way; fix `is_finite` before any graduation.
- **Side-derangement control UNPOWERED (B-5, not a negative):** only 60 of 7,070 events were derangeable within calendar-day blocks (2,694 singleton + 4,316 one-side-dominant dropped and counted).
- **Per-symbol R5 not day-pairable** (control calendar day = donor’s, disjoint from signal event days); event-level medians used as disclosure — per-symbol R5 inference is weaker.
- **Anchor prior unresolved:** INFR-018’s A-USOPEN×15 selection contrast E=+0.10, CI contains 0, below MDE — SPDR-007 sits on an unresolved Stage-I pin and assumes no established anchor effect.

## 7. Scope / limitations (binding on any read of this result)

- **One timeframe tested — daily session only.** Everything ran on **1-minute bars** (no higher-timeframe resampling). The only higher-timeframe structure was the **daily ~24h session anchored at the US open, 15-minute initial balance, single-session hold (~23h)**. This result does **not** speak to: the **8h funding-session cadence** (a candidate at INFR-018, not frozen), **micro** (1–10 bar) holds, **structural** (1–5 session) holds, or any 1h/4h/weekly bar timeframe. The card §2 lists micro / session / structural horizons; only the middle one was exercised.
- **Price-only.** No signed flow (Δ) — the family’s central warrant (signed value over the unsigned base: S3 trap-load, S9 absorption, S14 CVD) is **untested** here.
- **CONFIRM is TRAIN-INTERNAL** (checkpoint §5 D3), not programme out-of-sample.
- **Survivorship-shaped panel** (140 DESIGN / 187 CONFIRM symbols from the DESIGN-bank-covered set), not the full admitted universe.
- **Two developer deviations, operator-ratified 2026-07-21:** D-1 cross-session matched control (within-session phase match infeasible); D-2 material-edge precondition on the HARD tripwire. Folded into design.md (amendments 10–11; ledger 0L/6T/5N).

## 8. Framework-falsifier #1 reading

- **Strict source reading:** not triggered — the Protection quantile reproduces (~68–73% on CONFIRM).
- **Binding programme reading (P-01 + R5 + cost):** the master go/no-go fails on the **matched-unconditional contrast**, not on the existence of quantiles. The price-only spine is characterisation-complete, not a strategy candidate.

## 9. Registry disposition

- **Family status:** unchanged (**REGISTERED**). No open/retire/promote — retrospective act only.
- **Evidence row** appended to [`candidate-families/cf-sigauc-001.md`](../../../docs/signal-registry/candidate-families/cf-sigauc-001.md) (SPDR-007 NOT_WORTH, price-only spine, P-01 confirmation, daily-session-only scope).
- **multiplicity-registry:** evidence row (screen; no counted read).
- **test-read-ledger:** **no entry** — SPDR spends no counted read; TEST untouched.

## 10. Next

**SPDR-008 (signed-trap breadth, S1+S3 across the 296 TRAIN-readable instruments).** S3 (failed-break trap with Δ+ trap-load) is a **signed-flow** mechanism distinct from the S1/S2 price spine; the ruler it needs (the Protection quantile) reproduced and is valid. Runs on a pre-set bar: the signed lift must be large enough to plausibly clear the ~0.40 cost-adjusted breakeven, or it is characterisation-only. The full signed battery (S9/S14/models) remains deferred to checkpoint-015. Family close/keep is decided at the checkpoint-014 retrospective, operator-signed.
