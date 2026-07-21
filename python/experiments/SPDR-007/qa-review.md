# SPDR-007 — QA review (append-only)

## QA run 1 — 2026-07-21T02:45Z — mode: subagent — HEAD 6b407c6fa3662042139bb53b37a1567012c3b27b

**Verdict: REVISE**

**Scope note — DESIGN-STAGE review.** No implementation exists yet
(`python/experiments/SPDR-007/screen_code/` is empty; the planned `xen.sigbar.spine`
module is not present). The clause-by-clause design→code fidelity trace that A-1 exists to
run therefore has nothing to trace against. This pass instead judges the **design** for
governance compliance, internal consistency, source fidelity, and defect-proneness, and
records the findings the implementation must then satisfy. **A second QA pass over
`screen_code/` (design→code fidelity trace, golden-trace diff of the emitted output,
code-asserted fences, derangement regeneration, `check_no_local_accounting`) is mandatory
before execution.** QA APPROVE of the design does not authorise a run.

Reviewed reads: design.md (471 lines); source `SIGNAL-SIGNED.md` S1/S2/§6/Appendix-B;
checkpoint-014 design; cf-sigauc-001 card; INFR-018 design/report/qa-review (runs 1–8);
INFR-017 `column_pins.json`; shared code `xen.sigbar.{sessions,acceptance,fences}`,
`xen.evaluation`; and the INFR-018 result artifacts. Numbers below were recomputed from
staging via `xen.sigbar.fences.load_bars`, not taken from the design.

---

### Verified-correct (independently recomputed — these are clean)

| Design claim | Check | Result |
|---|---|---|
| §6.3 CONVERSION-PIN DESIGN-median `ib_width_bps`: BTC 48.745 · ETH 69.958 · SOL 96.217 · DOGE 86.969 · XRP 60.753 | recomputed from staging (A-USOPEN, L=15, DESIGN) | **EXACT match** all five |
| §6.3 spread inputs (flip-pair): BTC 0.244 · ETH 0.305 · SOL 0.727 · DOGE 1.470 · XRP 1.929 | vs `column_pins.json` `candidate_C_flip_pair.median` | match (DOGE caveat → I-6) |
| §6.3 floor arithmetic (11.0 + spread + 3.0) and "TP1 must exceed" = floor/ibw_bps | recomputed: 14.24/0.292, 14.31/0.204, 14.73/0.153, 15.47/0.178, 15.93/0.262 | **arithmetically correct** |
| §6.3 spread convention: flip-pair passed **once** as round-trip `spread_bps`, not doubled | `t1_round_trip_spread_bps` returns `stress*spread_bps` (one full spread/RT); flip-pair |Δp| between side-flipping prints ≈ one crossed spread; buy-at-ask→sell-at-bid RT pays exactly one spread | **CORRECT** — the EXP-025/L-21 seam is handled right |
| §3.3 quantile direction: target hit w.p. `p` = the `(1−p)` quantile; `p=0.65→q=0.35`, `p=0.70→q=0.30`; guard raises for `q>0.5` | matches source S2 MECHANISM verbatim; GT-4(d) asserts the guard | **CORRECT** |
| §6.2 per-symbol sessions BTC 228 · ETH 228 · SOL 229 · DOGE 177 · XRP 225 | recomputed | **EXACT** |
| §6.2 DESIGN resolved pokes 4,909 / accept 2,594 | vs INFR-018 `hyp_i3` D4-t50-w30 δ=0 `separation` (`n`=4909, `n_yes`=2594) | match to the artifact cell (but wrong OBJECT → I-1) |
| Golden trace GT-1 (ETH 2022-11-09) | recomputed: IB 1228.05/1187.45 w40.60; poke 14:45 UP ext 1240.45; frac 0.5667 ACCEPT; entry 1226.80; MFE 97.80=2.4089 IBw, MAE 155.20=3.8227 IBw, asym −1.4138 | **EXACT** |
| Golden trace GT-3 (BTC 2023-01-11) | recomputed: IB 17419/17372 w47; poke 14:48 ext 17426; frac 0.3667 < 0.50 REJECT | **EXACT** (belongs in denominator, not population) |

The money-floor spine of the design is sound and derived from data, not memory. The defects
below are in the **event-population power table**, the **matched-control construction**, and
several **under-specified validity mechanisms**.

---

### Design-fidelity trace (design → source / frozen artifact; code column deferred to run 2)

| Design clause (§ref) | Source / artifact anchor | Verdict | Notes |
|---|---|---|---|
| §1/§4 master reads R1 (quantile reproduction), R3 (regime), R4 (Δ-coherence) | source Appendix-B Phase 4; falsifier #1 (§6.10) | **MATCHES** | The three Phase-4 sub-questions are answered head-on; no easier substitution. R1 = calib_err on CONFIRM is exactly falsifier #1. |
| §4 R5 matched control binding on every read; "reproduces only unconditionally = P-01 confirmation, recorded as one" | card §5 P-01 mitigation (operator-signed D6) | **MATCHES** | Distinctness obligation honoured in design intent. Construction defect → I-2. |
| §3.3 estimate q̂ on DESIGN, freeze+hash before any CONFIRM path | source S2 in-sample/out-of-sample; §7 refusal | **MATCHES** | Freeze-before-CONFIRM asserted HARD. |
| §0/§7 bands DESIGN `[2021-06-29,2023-03-01)`, CONFIRM `[…,2023-12-18)`; TEST/holdout never read | `fences.BANDS`; checkpoint-014 §5 D3 | **MATCHES** | Byte-identical to `fences.py`; `assert_band` raises on holdout. CONFIRM = train-internal (approved deviation). |
| §4.1 regime = trailing-60 strictly-prior percentile (≤t−1) | source S2 DEPENDS-ON | **MATCHES** (warmup wording → I-8) | Acausal full-band version is a disclosure probe only (§7). |
| §4.1 coherence = mean(`delta_ratio_resid`) over qualifying-window bars × side; residuals only | card ban 2; source Part 5 | **MATCHES** | Reads residuals, pre-entry window, per-bar not per-level. |
| §4.3 outcome_path_swap replaces outcome window, entry-and-earlier untouched; donor re-based to entry price | INFR-018 AMENDMENT-6/scope-limit-5 | **MATCHES** | The reads consume the outcome path, so the swap DOES move the consumed bars (unlike the INFR-018 I-3 defect). Statistic-per-read ambiguity → I-4. |
| §4.3 required positive control (leaky stratifier from donor outcome bars) MUST survive | INFR-018 AMENDMENT-6 | **MATCHES** | Genuinely able to fail: if the swap is a no-op the donor-outcome stratifier decorrelates and collapses. Well-specified. |
| §6.2 event-population counts | INFR-018 frozen D4-t50-w30 | **DEVIATES** | CONFIRM cited from the wrong discriminator, and the "accept" object is mis-mapped to `n_yes`. → **I-1**. |
| §4.2 matched-unconditional horizon | source §6.3 "session phase" | **DEVIATES** | Not horizon-matched → excursion contrast confounded by window length. → **I-2**. |
| §7 no value read gates; INFORMATIVE = report layers, no `pass` field | L-32 / INFR-016 | **MATCHES** | HARD set is validity-only (tripwire, fences, freeze-order, causal, hash, window-disjoint, no-per-level-delta, no-local-accounting). |
| §0 spread as verdict leg N/A; 1× spread binds the money floor | L-22 | **MATCHES** | No SUPPORTED/tradability band emitted. |
| §6.4 SPREAD-SCALE-ROUTING declared; `spread_scale_route` 3× threshold, no re-derivation | INFR-010 §4 | **MATCHES** | Routes the matched-unconditional contrast; AWAITING_MBP keeps T1 disclosure-only. |
| §10 amendment ledger 0L/0T/0N | L-23 | **MATCHES** | Empty at freeze. |

### Golden-trace diff

GT-1, GT-2 (DOWN branch — not re-run here; UP/DOWN symmetry and DST anchor logic verified in
`sessions.py`), and GT-3 are designer-derived. GT-1 and GT-3 reproduce **exactly** from
staging under the frozen rules (table above). GT-3 correctly lands as a REJECT
(closes-beyond 0.3667 < 0.50) that must appear in the accept-rate denominator, not the event
population. GT-4 fence/hash/quantile-guard behaviours are declared as raises. The golden
traces are trustworthy; the run-2 job is to diff the **implementation's** emission against
them, not to re-derive them.

### Governance & boundary

- **Fresh context:** satisfied — this session contains no SPDR-007 implementation.
- **Holdout / TEST:** never read; `assert_band` raises on `≥ 2025-01-08`; TEST `≥ 2023-12-18`
  untouched. **Clean.**
- **Causality ≤ t−1:** universe ranking day D→D+1 (`fences.build_universe`), regime percentile
  strictly prior, entry at `qualify_end` open. **Clean.**
- **No local accounting / no Python backtest:** SPDR vectorised lane; `check_no_local_accounting`
  listed HARD; no `BacktestNode` (N/A). Must be code-asserted at run 2.
- **Derangement destroys (L-28):** declared for outcome_path_swap and side_derangement (zero
  fixed points, asserted). Singleton/coverage rule missing for side_derangement → I-5.
- **Registry preconditions:** family REGISTERED; 0 slots / 0 counted reads / registers nothing.
  **Clean.**
- **L-21 CONVERSION-PIN:** present; divisor object stated verbatim; TRAIN-median recomputed
  (verified); floor arithmetic follows. **Clean** (DOGE nit I-6).
- **Amendment ledger (L-23):** empty, consistent.
- **Operator communication:** design prose is plain; bands labelled "labels, never gates".

**No REJECT-class defect** (no holdout contact, no causality violation, tripwire present,
freeze-order enforced, deviations operator-signed). Verdict is **REVISE**.

---

### Issues

**I-1 — MAJOR — §6.2 power table: CONFIRM count is from the wrong discriminator, and the
"accept" object is the wrong population. The whole power/UNPOWERED story rests on it.**
Design §6.2 cites "S1 confirmed breaks (= A6 accept calls) DESIGN 2,594; CONFIRM 1,524".
Two defects, both verified against the frozen artifacts:
- **Wrong cell (CONFIRM).** The frozen rule is **D4-t50-w30** (INFR-018 report §6: the pin
  uses the DESIGN freeze, *not* the CONFIRM full-grid re-rank). In
  `hyp_i3_a6_race_CONFIRM.json`, D4-t50-w30 (δ=0) has `n_yes = 1396`; the cited **1,524 is
  D3-w30**, the CONFIRM re-rank winner the pin explicitly discards. Off by the exact
  wrong-artifact-cell mechanism the brief warned about.
- **Wrong object (both bands).** The SPDR-007 event population is **every A6-accepted poke**
  (`says_accept`), independent of INFR-018's trap/acceptance/UNRESOLVED labelling (which was a
  Phase-2 *discriminator-scoring* device, not the spine's TP/STOP resolution). But `n_yes`
  counts only **resolved-AND-accept** pokes. Recomputed on the 5 majors under the frozen rule:
  DESIGN `says_accept = 556` vs `n_yes = 319`; CONFIRM `says_accept = 697` vs `n_yes = 424` —
  the true population is **~1.7×** the cited number. Extrapolated, the DESIGN population is
  ~4,500, not 2,594, and "median events per symbol ≈ 18" is nearer ~30. The error is
  *conservative* for power, but it is still wrong and it feeds every MDE floor and every
  UNPOWERED predeclaration.
- *Required change:* recompute the entire §6.2 table as the **`says_accept` population under
  D4-t50-w30 (δ=0)** on DESIGN and CONFIRM (total pokes, accepted pokes, per-symbol
  distribution), re-derive "median events per symbol", and re-anchor the UNPOWERED floors to
  the corrected n. State the number is `says_accept`, not `n_yes`. (design §6.2, §5.1, §5.3)

**I-2 — MAJOR — the matched-unconditional control is not horizon-matched; the master-gate
excursion contrast is confounded by outcome-window length.** §4.2 draws control entries at an
"arbitrary post-IB minute … same `session_end`, same `ib_width` divisor", excluding
`[poke_ts−30, qualify_end+30]`. Real events enter at `qualify_end` (`poke_ts+30`), which for a
first-boundary poke is typically early in the session → a **long** outcome window; control
entries spread across the whole post-IB session → on average a **shorter** window. MFE/MAE
(maxima over the window) and the TP-before-STOP race all grow with window length, so
`contrast = signal − control` is inflated by pure horizon asymmetry, not by the acceptance
event. This is exactly the confound source §6.3 pre-empts by matching **"session phase"** — a
requirement the design drops. B-1 non-degeneracy and L-24-F04 exit-matching are fine; the gap
is horizon.
- *Required change:* match the control draw to the real events' **entry-phase / remaining-horizon
  distribution** (e.g. draw control minutes to reproduce the per-session elapsed-since-anchor
  distribution of the real entries, or add remaining-horizon as an explicit matched covariate),
  so the contrast isolates acceptance, not window length. Specify the stratification variable of
  the "stratified seeded sample" — as written it is undefined. (design §4.2, §1 null)

**I-3 — MODERATE — R3 regime Spearman is mechanically confounded by the `ib_width` normaliser.**
`ρ(ib_width_pctl, mfe_norm)` with `mfe_norm = MFE / ib_width` induces a spurious **negative**
correlation whenever raw MFE is not itself proportional to `ib_width` — larger IB mechanically
shrinks `mfe_norm`, independent of any contraction→expansion mechanism. This is the
"dispersion = normaliser mechanic" that inverted the first-pass SPDR-001 conclusion (project
memory). The R5 contrast *largely* cancels it (both arms share the divisor), but the design
lists ρ as a **level** in the R3 row and only R5 (elsewhere) says "signal minus control".
- *Required change:* make R3 **contrast-only binding** (signal ρ − matched-control ρ), suppress
  any raw-ρ headline, and add an **un-normalised raw-MFE regime disclosure** so the
  contraction-expansion mechanism is separable from the normaliser mechanic. (design §4 R3, §5.3)

**I-4 — MODERATE — the HARD tripwire's collapse statistic is not defined per read.** §4.3
adjudicates "SURVIVAL := |collapse_fraction| > 0.25 with the SAME SIGN as **the raw contrast**"
(singular), but R1 (`calib_err`), R2 (`w`), R3 (`ρ`), R4 (tercile contrast) are heterogeneous
statistics on different supports. A single inherited 0.25 threshold cannot be applied without
saying **which statistic** `collapse_fraction` is computed on for each read. As written the HARD
gate is ambiguous for R1 and R2 (level reads, not contrasts).
- *Required change:* state the tripwire statistic and its collapse definition **per read**
  (most naturally on each read's R5-differenced contrast), so "survives / collapses" is
  unambiguous for all four. (design §4.3, §7)

**I-5 — MODERATE — side_derangement has no singleton/coverage rule, and the TP1 basis under
derangement is unpinned.** §4.2 deranges `side` "within calendar-day blocks … regenerated until
fixed-point count is EXACTLY 0". A day-block with one event (or an all-one-side block) cannot be
deranged to zero fixed points — the INFR-018 I-57 singleton-self-donor failure. The tripwire
block declares donor-coverage counting; this block does not. Also, deranging side flips
favourable/adverse, so the race read needs a stated TP1 basis (it should stay the **frozen
DESIGN q̂**, not be recomputed on the deranged arm).
- *Required change:* declare the singleton handling (drop + count, coverage reported beside the
  collapse fraction) and pin TP1 = frozen q̂ under derangement. Note: the control is genuinely
  non-vacuous (the ~50/50 sign-mixing drives the deranged asym/race toward the no-information
  expectation while the real arm retains its value — not antisymmetric-by-construction), so the
  B-6 argument holds; this is a robustness/coverage gap, not a validity hole. (design §4.2)

**I-6 — MINOR — DOGE money floor uses the flip-pair (1.470) where the stated rule
`max(tick_bps, flip-pair)` selects the tick (1.477).** For DOGE, `one_tick_bps = 1.47732` >
flip-pair `1.47037`, so the rule gives 1.477 → floor 15.48, not the cited 15.47. Immaterial to
the disposition (0.007 bps) but inconsistent with the design's own rule and the column label
"spread RT (flip-pair)". *Required change:* apply `max()` for DOGE (or annotate that the tick
dominates there). (design §6.3)

**I-7 — MINOR — "money floor computed FIRST" is only partly true.** The **cost** floor
(taker + spread + funding) and the data-only "TP1 must exceed X IB widths" thresholds
(floor/ibw_bps) are genuinely computable before estimation; the **TP1-vs-floor comparison**
needs `q̂` from DESIGN estimation and therefore cannot precede it. §9's execution order should
distinguish the two so the "binding first act" is not overclaimed. (design §6.3, §9)

**I-8 — MINOR — regime warmup wording.** §4.1 says the percentile is the rank within the
"trailing 60 sessions" but excludes sessions "with < 30 prior sessions". State whether a session
with 30–59 priors uses a shortened window or is excluded, so the percentile base is
reproducible. (design §4.1)

**I-9 — MINOR — R2 MDE plant units.** §4.2 injects "a proportional shift of TP1" for the R2
race plant; a TP1 shift maps non-linearly to the win-rate contrast `w`. Confirm the swept curve
yields the MDE in **`w`-contrast units** (the AMENDMENT-5 like-for-like requirement), not TP1
units. (design §4.2, §5.2)

---

### Standing limitations to carry to the operator (approved / not QA findings)

- **CONFIRM is TRAIN-INTERNAL**, not programme out-of-sample (checkpoint-014 D3, operator-signed).
  The master gate's "reproduction" is therefore weaker than source §6.7's strict-holdout intent;
  the design labels this in every artifact. Correct, but the operator should read the disposition
  with that ceiling in mind.
- **The frozen anchor's own asymmetry is unresolved** (INFR-018: A-USOPEN×15 `E=+0.100`, CI
  `[−0.282,+0.444]` contains zero, below its MDE 0.50; the four zero-excluding cells were all
  negative). SPDR-007 measures quantile *reproduction*, which can hold on a distribution whose
  mean asymmetry is ~0 — but no read may imply an established anchor effect. The design states
  this (§0); keep it in the headline.
- **Spread-regime layer UNAVAILABLE** — the source's volatility-AND-spread regime match (§6.3) runs
  on volatility only; every read must say so.

### Verdict routing

**REVISE**, to `quant-designer` — every finding is a design defect (power derivation, control
construction, tripwire/derangement specification), none an implementation bug. After the design
is corrected and re-frozen, the implementation of `xen.sigbar.spine` + `screen_code/` must go
through **QA run 2** (design→code fidelity trace + golden-trace diff of the emission) before the
operator's execution gate.
