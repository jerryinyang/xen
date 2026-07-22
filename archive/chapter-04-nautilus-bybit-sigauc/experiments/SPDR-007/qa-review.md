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

## QA run 2 — 2026-07-21T03:45:24Z — mode: subagent — HEAD ab1cf56c1061587ace99e0ee4ed6ec22e3633ff9

**Verdict: REVISE**

**Scope:** code-stage design→code fidelity + golden-trace recompute + governance/boundary.
Fresh context (this subagent did not implement SPDR-007). Read-only on design/code/results;
append-only here.

**Dirty:** `M python/experiments/SPDR-007/design.md` (amendments 1–11 + D-1/D-2 text; not staged).

**Artifacts reviewed (hashes):**
- `python/src/xen/sigbar/spine.py` sha256 prefix `d32f531a9359a707`
- `python/experiments/SPDR-007/screen_code/spine_screen.py` `234c631b1242bdf3`
- emission: `protection_freeze.json` `13d0a720…`, `tripwire.json` `bfd03988…`, `layers.json` `a19e0a0e…`,
  `spine_events_DESIGN.parquet` `08919ba5…`, `spine_events_CONFIRM.parquet` `f169f6d9…`

**Independent recompute path:** `python/.venv/bin/python` + `xen.sigbar.fences.load_bars` with
`python/src` on `sys.path`. Numbers below are recomputed or re-read from emission, not taken from
developer narrative.

---

### Design-fidelity trace

| Design clause (§ref) | Code (file:line) | Verdict | Notes |
|---|---|---|---|
| §3.1 A6 = D4-t50-w30, δ=0; pop = `says_accept` | `spine.py:36-39,146-147` | **MATCHES** | Frozen disc; accepted = join on `says_accept`. |
| §3.2 entry = open at `qualify_end`; outcome strictly after entry | `spine.py:151-171,269-271` | **MATCHES** | `assert_entry_after_qualify`; `searchsorted(..., side="right")`. |
| §3.2 MFE/MAE real prices; `mfe_norm = MFE/ib_width`; STOP=TP1/2; same-bar → STOP | `spine.py:41-42,284-308,315-319` | **MATCHES** | Pessimistic `first_stop <= first_tp → STOP`. |
| §3.3 Protection = (1−p) quantile; raise if q>0.5 | `spine.py:74-92` | **MATCHES** | GT-4d raises; freeze `p65.q=0.35`, `p70.q=0.30`. |
| §3.3 freeze DESIGN q̂ before CONFIRM | `spine_screen.py:222-252,504-512` | **MATCHES** | `require_freeze` raises if missing/tampered; CONFIRM only after. |
| §4 R1 calib_err on CONFIRM | `spine_screen.py:258-270` | **MATCHES** (pooled only) | Emission: p65 err +0.030, p70 +0.028. No per-symbol R1 in `layers.json` despite freeze `per_symbol` → see I-2. |
| §4 R2 race w vs gross + **cost-adjusted** breakeven | `spine_screen.py:273-287` | **DEVIATES** | Gross `p0=1/3` only; **no `p0ᶜ`**. → I-3. |
| §4 R3 contrast-only ρ + raw-MFE disclosure | `spine_screen.py:290-305` | **MATCHES** | Binding = `rho_contrast`; raw disclosure present. |
| §4 R4 coh tercile contrast in mfe_norm **and w** | `spine_screen.py:309-322` | **DEVIATES** | mfe_norm only; no race-rate tercile contrast. → I-4. |
| §4.1 regime trailing-60, ≥30 priors, ≤t−1 | `spine.py:326-362` | **MATCHES** | Shortened window; null if <30 priors. |
| §4.1 coh = mean residual × side over qualify window | `spine.py:365-384`; residualise in `spine_screen.py:136-143` | **MATCHES** | Residuals only; pre-entry window. |
| §4.2 D-1 cross-session phase/side matched control, n=30 | `spine.py:406-499` | **MATCHES** | Verified horizons median 1391 vs 1391; 0 entries inside event session. |
| §4.2 horizon-match disclosure side-by-side | — | **MISSING** | Not in `layers.json` / control artifact summary. → I-5. |
| §4.2 side_derangement zero FP; singleton drop+count; TP1=frozen q̂ | `spine.py:512-552`; `spine_screen.py:490-500` | **MATCHES** | Coverage emitted; fixed_point_rate 0; race uses freeze q̂. Power-starved (60/7070) — disclosed in screen.md. |
| §4.3 outcome_path_swap derangement + re-base; material-edge D-2; bite corr>0.5 | `spine.py:577-701`; `spine_screen.py:440-487` | **MATCHES** core; **DEVIATES** scope | Bite corr=0.771, n=3561. Status `NO_MATERIAL_EDGE…`. Collapse adjudicates **R5 asym only** — not R2/R3/R4 per §4.3 / AMENDMENT-4. → I-6. |
| §6.1 universe top-20 quote turnover, causal D→D+1; hash f11dd7f0… | `fences.build_universe`; `spine_screen.py:357-374` | **MATCHES** | Byte-equal to INFR-018 membership; `membership_sha256` = `f11dd7f0aea42f82…`. **Hash not written into SPDR artifacts** (parquet only). |
| §6.2 power table says_accept DESIGN 7,148 / CONFIRM 11,453 | diagnostics + events | **MATCHES** accepts; evaluable lower | DESIGN accepts 7,148 (−78 missing entry → **7,070** events). CONFIRM events **11,375**. Design table omits missing-entry drop. → I-7 (NOTE). |
| §6.3 CONVERSION-PIN DESIGN-median session `ib_width_bps` | `spine_screen.py:391-396,113-130` | **DEVIATES** | Pin uses **all-session** medians (recomputed BTC 48.745 · ETH 69.958 · …). Floor uses **accept-event** medians (ETH 66.22 · SOL 103.03). → I-1 **MAJOR**. |
| §6.3 DOGE max(tick, flip)=1.477 | `spine_screen.py:85-89` | **MATCHES** | `max(1.477, 1.470)` → floor 15.477. |
| §6.4 SPREAD-SCALE-ROUTING per symbol | import only `spine_screen.py:63` | **MISSING** | `spread_scale_route` never called; not in layers. → I-8. |
| §5.3 / L-24 F02 chronological thirds | — | **MISSING** | No thirds in emission. → I-9. |
| §7 band fences raise | `fences.load_bars` → `assert_band` | **MATCHES** | Every bar path fenced; TEST band name refused. |
| §7 freeze-before-CONFIRM raise | `require_freeze` | **MATCHES** | Re-tested: raises when freeze removed. |
| §7 causal ≤t−1 | universe + regime + entry open | **MATCHES** | By construction. |
| §7 `assert_windows_disjoint` | `acceptance.find_pokes:186` | **MATCHES** | Called on every poke set. |
| §7 `assert_no_per_level_delta` raise | — | **MISSING** | Never invoked on SPDR-007 path. → I-10. |
| §7 `check_no_local_accounting` raise | — | **MISSING** | Never invoked; **substantive** scan ok `{ok:true}` on `screen_code/` + `xen/sigbar`. → I-10. |
| §7 no value-read gates / no `pass` field (L-32) | `layers.json` | **MATCHES** | No `pass`/`blocking_pass`; tripwire is validity HARD only. |
| §8 GT-4(e) control-in-exclusion raises | `CONTROL_EXCLUSION_MIN` unused | **MISSING / stale** | Dead after D-1 (cross-session). Design §8 still claims raise. → I-11. |
| DEVIATIONS D-1/D-2 | module header + design AMENDMENT-10/11 | **MATCHES** | Operator-ratified 2026-07-21 in dirty design.md. |

---

### Golden-trace diff

Independent recompute from staging (not design copy-paste). Compare design §8 expected vs implementation emission.

| Trace | Design expected | Independent recompute | Emission | Verdict |
|---|---|---|---|---|
| **GT-1** ETH 2022-11-09 14:30Z UP ACCEPT | IB 1228.05/1187.45 w40.60; poke 14:45 ext 1240.45; frac 0.5667 ACCEPT; entry 1226.80; MFE 97.80=2.4089; MAE 155.20=3.8227; asym −1.4138; n_post 1394 | **exact** (frac 0.5667, mfe_norm 2.408867, mae_norm 3.822660, asym −1.413793, n_post 1394) | same row in `spine_events_DESIGN` | **MATCH** |
| **GT-2** SOL 2022-07-17 13:30Z DOWN ACCEPT | IB 39.800/39.475 w0.325; poke 13:46 DOWN 39.445; frac 0.90; entry 39.25; MFE 0.990=3.0462; MAE 3.425=10.5385; asym −7.4923 | **exact** (DST anchor 13:30Z; side −1; all numbers) | same | **MATCH** |
| **GT-3** BTC 2023-01-11 14:30Z REJECT | frac 0.3667 < 0.50; not in population | frac 0.3667; `says_accept=false`; events height 0 | not in emission | **MATCH** (in poke denom via BTC n_pokes 227) |
| **GT-4a** band ≥2023-12-18 / holdout | raise | `load_bars`/`assert_band` raise; no TEST band | N/A | **MATCH** |
| **GT-4b** CONFIRM before freeze | raise | `require_freeze` → RuntimeError | N/A | **MATCH** |
| **GT-4c** frozen pin mismatch | raise | `assert_frozen` / `assert_frozen_inputs` | emission frozen pins match 5c386984… / 1b7244c8… / e3b9fd9b… | **MATCH** |
| **GT-4d** q>0.5 | raise | raises ValueError | N/A | **MATCH** |
| **GT-4e** control in [poke−30, qualify+30] | raise | **not implemented** (D-1 cross-session; constant unused) | N/A | **FAIL / stale design** → I-11 |

Design-stated GT numbers are correct (no design-number errors on GT-1..3). Code emission matches recompute bit-for-bit on the three path traces.

---

### D-1 / D-2 / integrity assertions

**D-1 (cross-session control)** — sound on data:
- phase/side matched by construction (`entry_phase` φ, side d on donor session).
- remaining_horizon: signal median/mean **1391 / 1381.39** vs control **1391 / 1381.44**; q10/q50/q90 identical (1364/1391/1395).
- disjoint: 0/198,597 control rows inside the event's session window; 0 same `entry_ts` as event.
- unconditional: donors drawn from session pool without A6 filter (`spine.matched_unconditional`).
- n_control≈28.1 mean (30 draws minus missing entry bars).

**D-2 (tripwire material-edge + bite)**:
- raw excursion contrast median 0.0899; day-clustered CI **[−0.231, +0.320]** includes 0 → `material_edge=false` → status `NO_MATERIAL_EDGE_TRIPWIRE_UNINFORMATIVE` (not a hard fail). Correct under D-2.
- bite: `corr(swapped price MFE, donor real price MFE) = 0.771` on n=3561 > 0.5 — genuine, non-tautological (donor's own real MFE, not swapped-vs-self). Matches design "measured 0.77".
- survives rule requires material edge ∧ |cf|>0.25 same sign ∧ swapped CI excl 0 — not fired.

**Population (checklist):**
| | Design §6.2 | Emission / recompute |
|---|---|---|
| DESIGN panel | 140 | 140 |
| DESIGN pokes | 13,802 | 13,802 |
| DESIGN `says_accept` | 7,148 | 7,148 |
| DESIGN evaluable events | (not stated) | **7,070** (= 7148 − 78 missing entry) |
| CONFIRM events | 11,453 accepts | **11,375** evaluable |
| Majors DESIGN accepts | 114/113/126/85/118 | exact match |

**Quantile direction:** freeze q = 1−p; DESIGN self-hit rates 0.6499 @ p65 and 0.7000 @ p70 (by construction). Guard raises for q>0.5.

**L-32:** value reads are report layers; only tripwire/freeze/band raise validity.

---

### Governance & boundary

| Check | Result | Evidence |
|---|---|---|
| Fresh context | PASS | subagent; no implementation in this conversation |
| Holdout / TEST | PASS | `BANDS` DESIGN/CONFIRM only; `assert_band` holdout-first |
| Causality ≤ t−1 | PASS | universe shift, regime priors, entry open |
| No Python backtest / BacktestNode | PASS | vectorised SPDR |
| Derangement (L-28) | PASS | side + path-swap; zero fixed points asserted/regenerated |
| `check_no_local_accounting` substantive | PASS | `{ok:true}` both dirs |
| `check_no_local_accounting` code-asserted | **FAIL** | never called in runner (design §7 HARD) |
| `assert_no_per_level_delta` code-asserted | **FAIL** | never called |
| CONVERSION-PIN (L-21) | **FAIL** | session medians in design; event medians in floor code |
| SPREAD-SCALE-ROUTING declared | declared | not emitted |
| Amendment ledger L-23 | PASS | 0L/6T/5N; D-1/D-2 ratified in design |
| Registry / 0 counted reads | PASS | layers `counted_reads:0`, `test_touched:false`, `holdout_touched:false` |
| Universe hash f11dd7f0… | PASS | recomputed equal INFR-018 |
| Silent deviations | none beyond DEVIATIONS block | D-1/D-2 documented + dirty design |

---

### Issues

**I-1 — MAJOR — §6.3 L-21 CONVERSION-PIN: money floor uses accept-event median `ib_width_bps`, not the pinned DESIGN session medians.**
Design pins session-level DESIGN medians (recomputed here: BTC **48.745** · ETH **69.958** · SOL **96.217** · DOGE **86.969** · XRP **60.753**).
Code (`spine_screen.py:391-396`) takes median over **A6-accept events only** → ETH **66.22**, SOL **103.03**, etc. "TP1 must exceed X IB widths" and any bps conversion from the floor table therefore use the wrong divisor object.
- *Required change:* compute `ib_width_bps` median from all DESIGN sessions with `ib_width>0` (same object as design CONVERSION-PIN / QA run-1 verification), not from the accept-event frame. Re-emit `floor_table.json` / money-floor plot. Route: **experiment-developer**.

**I-2 — MAJOR — §4 / §4.1 / L-03: R1 (and most layers) are pooled-only; per-symbol Protection exists in freeze but is never verified or labelled.**
`freeze_protection` writes `per_symbol` q̂; `r1_calibration` only hits pooled. Independent CONFIRM hit rates at frozen per-symbol p70: BTC +0.032, ETH +0.034, **SOL +0.105 (BROKEN label)**, DOGE −0.045, XRP +0.004. Pooled REPRODUCES can mask a broken major.
- *Required change:* emit per-symbol (and predeclared UNPOWERED) R1 calib_err + n; do not leave SOL-class drift only in analyst parquet archaeology. Route: **experiment-developer**.

**I-3 — MAJOR — §5.2 / §6.3: R2 cost-adjusted breakeven `p0ᶜ` never computed.**
Design requires w beside gross `p0=1/3` **and** cost-adjusted `p0ᶜ = (STOP+cost_rt)/(TP1+STOP)` per symbol. Code only emits `gross_breakeven`. Sample with emission floor (even on wrong ibw): BTC p0ᶜ≈0.44 vs gross 0.33 — the race read is mis-framed without it.
- *Required change:* add per-symbol `p0_cost` into R2 / layers; report w vs both. Route: **experiment-developer**.

**I-4 — MINOR — §4 R4: race-rate (`w`) tercile contrast missing.**
Only `mfe_norm` top−bottom contrast emitted.
- *Required change:* add `w` contrast between coh terciles (same TP1). Route: **experiment-developer**.

**I-5 — MAJOR — §4.2: horizon-match disclosure not emitted.**
Design requires realised remaining-horizon distributions of signal vs control "side by side per stratum, so the match is auditable, not asserted." Match is true when recomputed here, but the emission does not show it.
- *Required change:* emit horizon summary (quantiles / per-stratum) for both arms in `layers.json` or a small parquet. Route: **experiment-developer**.

**I-6 — MAJOR — §4.3 / AMENDMENT-4: HARD tripwire adjudicates only R5 excursion contrast, not R2/R3/R4.**
Design: collapse_fraction defined per effect-contrast (R5 primary + R2 race, R3 ρ, R4 tercile); R1 excluded by freeze-order. Code (`spine_screen.py:443-467`) only pairs day-contrast on `asym`.
- *Required change:* compute material-edge + collapse for each adjudicated contrast; HARD-fail if any material read survives. Route: **experiment-developer**.

**I-7 — NOTE — §6.2 power table is `says_accept` (7,148 / 11,453); evaluable spine is 7,070 / 11,375 after missing entry bars.**
Not a code bug; design should state the drop (DESIGN missing_entry sum=78). Power/UNPOWERED floors should cite evaluable n where MDE is built on events. Route: **quant-designer** (one-line clarity) optional.

**I-8 — MAJOR — §6.4 SPREAD-SCALE-ROUTING not emitted.**
`spread_scale_route` imported and unused. Design: per-symbol `t1_undecidable` from 3× threshold on contrast bps vs RT spread.
- *Required change:* emit routing per symbol into layers/floor; keep T1 disclosure-only when YES. Route: **experiment-developer**.

**I-9 — MAJOR — §5.3 / L-24 F02: chronological thirds (time stability) not reported.**
Design: every read repeated on three DESIGN thirds + CONFIRM; sign consistency + n published.
- *Required change:* emit third-split contrasts for R1–R5 (even if UNPOWERED). Route: **experiment-developer**.

**I-10 — MAJOR — §7 HARD validity asserts claimed but not invoked: `check_no_local_accounting`, `assert_no_per_level_delta`.**
Mandatory checklist item 5 requires these **code-asserted (raise, not warn)**. Substantive accounting scan is clean; per-level ban holds by construction (no profile path). Still the design's HARD "asserted" guarantee is not machine-checked on this run path — same shape as INFR-018 I-18.
- *Required change:* call both at runner entry (accounting on `screen_code/` + `xen/sigbar`; per-level on any signed column that could enter a kernel, or a deliberate contract call). Fail closed. Route: **experiment-developer**.

**I-11 — MINOR — §8 GT-4(e) still requires a raise on within-session exclusion; D-1 made that path dead.**
`CONTROL_EXCLUSION_MIN = 30` is unused. Either implement an equivalent D-1 integrity raise (e.g. donor == event session) or amend GT-4(e) to the cross-session disjoint assert already true by construction.
- *Required change:* design §8 update **or** assert donor∉event session. Route: **quant-designer** or **experiment-developer**.

**I-12 — MINOR — §4.2 / I-9 residual: R2 MDE plant in w-contrast units not emitted.**
Only R5 asym MDE curve is present (`mde=0.5` planted). Design AMENDMENT-9 wants R2 MDE in w units.
- *Required change:* publish R2 plant curve / MDE beside race contrast. Route: **experiment-developer**.

---

### Prior-run disposition (QA run 1)

| Run-1 finding | Status after design amendments 1–11 + code |
|---|---|
| I-1 power table wrong object/cell | **RESOLVED** — says_accept under D4; numbers recompute |
| I-2 control not horizon-matched | **RESOLVED** (D-1) — horizons match; residual = missing disclosure (new I-5) |
| I-3 R3 normaliser mechanic | **RESOLVED** — contrast-only + raw disclosure |
| I-4 tripwire statistic per read | **PARTIALLY RESOLVED** in design text; **code still R5-only** → new I-6 |
| I-5 side_derangement singleton/TP1 | **RESOLVED** in code |
| I-6 DOGE max(tick,flip) | **RESOLVED** |
| I-7 money floor timing split | **RESOLVED** in design order; cost first in code |
| I-8 regime warmup wording | **RESOLVED** in code (≥30 shortened window) |
| I-9 R2 MDE units | **PARTIALLY** — declared; R2 MDE not emitted → new I-12 |

No run-1 REJECT-class defect remains open. New issues are code-stage fidelity / incomplete emission vs the amended design.

### Verdict routing

**REVISE** → **experiment-developer** (I-1..I-6, I-8..I-10, I-12); optional **quant-designer** (I-7, I-11 design text).

Not APPROVE: CONVERSION-PIN drift, missing HARD asserts, missing mandatory emissions (spread-scale, thirds, tripwire-per-read, horizon disclosure, cost breakeven, per-symbol R1) block treating the current emission as execution-gate clean.

Not REJECT: no holdout contact, no causality break, tripwire present with working bite, D-1/D-2 documented and ratified, golden path traces match.

**After fix:** re-run screen (do not accept current floor/layers as final without re-emission), then QA run 3.


## QA run 3 — 2026-07-21T04:00:27Z — mode: subagent — HEAD ab1cf56c1061587ace99e0ee4ed6ec22e3633ff9

**Verdict: APPROVE**

**Scope:** code-stage re-review after QA run 2 REVISE + developer fix + screen re-emission.
Fresh context (this conversation did not implement SPDR-007 or its fixes). Independent recompute
from staging via `xen.sigbar.fences.load_bars` + `sessions` / `spine` / emission parquets.

**Dirty:** `M design.md`, `spine.py`, `spine_screen.py`, `screen.md`, `qa-review.md`,
`results/{floor_table,layers,protection_freeze,tripwire}.json` (+ event parquets / plots
re-emitted 2026-07-21 ~03:54–03:56Z). Uncommitted implementation + emission is the review object.

---

### Design-fidelity trace

| Design clause (§ref) | Code (file:line) | Verdict | Notes |
|---|---|---|---|
| §3.1 A6 = D4-t50-w30 δ=0; pop = `says_accept` | `spine.py:36-39,140-146` | **MATCHES** | Diagnostics: DESIGN accepts **7,148** (−78 miss entry → **7,070** evaluable); CONFIRM evaluable **11,375**. |
| §3.2 MFE/MAE; STOP=TP1/2; same-bar → STOP | `spine.py:210-320` | **MATCHES** | Unchanged from QA2. |
| §3.3 Protection = (1−p) quantile; raise if q>0.5 | `spine.py:74-92` | **MATCHES** | Freeze `p65.q=0.35`, `p70.q=0.30`; GT-4d raises. |
| §4 R1 calib_err CONFIRM pooled **+ per-symbol** | `spine_screen.py:356-391` | **MATCHES** | Emission: pooled p65 +0.030 / p70 +0.028; SOL p70 **+0.105 BROKEN** labelled; 97 DESIGN-covered symbols. |
| §4 R2 w vs gross + **cost-adjusted p0ᶜ** | `spine_screen.py:341-350,394-429` | **MATCHES** | Majors p0ᶜ recompute exact (BTC 0.4418 …); pooled median p0ᶜ 0.380; MDE_w=0.03. |
| §4 R3 contrast-only ρ + raw-MFE disclosure | `spine_screen.py:432-452` | **MATCHES** | ρ_contrast +0.130; raw disclosure present. |
| §4 R4 mfe_norm **and w** tercile contrast | `spine_screen.py:455-482` | **MATCHES** | mfe +0.077 IBw; **w_contrast +0.012**. |
| §4 R5 binding under every read | layers R2/R3/R5 contrasts | **MATCHES** | Signal − control reported. |
| §4.2 D-1 cross-session phase/side control | `spine.py:406-503` | **MATCHES** | Horizons median **1391 / 1391**; q10/q50/q90 match; 0 control entries in event session. |
| §4.2 horizon-match disclosure | `spine_screen.py:297-320`; layers `R5…horizon_match_disclosure` | **MATCHES** | Pooled + per-symbol emitted. |
| §4.3 tripwire per-read R2/R3/R4/R5 + D-2 material edge + bite | `spine_screen.py:570-818`; `tripwire.json` | **MATCHES** | `per_read` has R5, R2, R3, R4_mfe, R4_w; status `NO_MATERIAL_EDGE…`; bite corr **0.771** n=3561. |
| §5.3 / L-24 F02 chronological thirds | `spine_screen.py:485-536`; layers `time_stability_thirds` | **MATCHES** | DESIGN thirds n=2356/2357/2357; R1–R5 fields; not gated. |
| §6.3 CONVERSION-PIN session median ib_width_bps | `spine_screen.py:281-294,685-695` | **MATCHES** | Independent recompute: BTC **48.745** · ETH **69.958** · SOL **96.217** · DOGE **86.969** · XRP **60.753** — emission bit-identical; **not** accept-event medians (ETH accept-event 66.22 still differs — pin correctly ignores it). |
| §6.4 SPREAD-SCALE-ROUTING | `spine_screen.py:539-567` | **MATCHES** | 140 symbols; **2** `t1_undecidable`; route fields present. |
| §7 freeze-before-CONFIRM / band fences | `require_freeze`, `load_bars` band set | **MATCHES** | TEST/HOLDOUT unknown-band raise; CONFIRM after freeze. |
| §7 `check_no_local_accounting` + `assert_no_per_level_delta` **invoked** | `spine_screen.py:259-278,636-638` | **MATCHES** | Called at runner entry; raise on fail; layers `hard_integrity` `{ok:true}` both dirs. |
| §7 no value-read gates (L-32) | layers.json | **MATCHES** | No `pass` / `blocking_pass` keys; interpretation states report layers only. |
| §8 GT-4(e) control integrity raise | `spine.py:506-528` | **MATCHES** (semantics) | D-1 `assert_control_cross_session_disjoint` raises on entry ∈ [event.anchor, session_end). Design §8 still prints old within-session wording → residual NOTE. |
| DEVIATIONS D-1/D-2 | design AMENDMENT-10/11; module headers | **MATCHES** | Operator-ratified 2026-07-21; 0L/6T/5N ledger. |

---

### Golden-trace diff

| Trace | Design expected | Independent recompute | Emission | Verdict |
|---|---|---|---|---|
| **GT-1** ETH 2022-11-09 UP ACCEPT | IB 1228.05/1187.45 w40.60; poke/entry path; mfe_norm 2.4089; mae_norm 3.8227; asym −1.4138; n_post 1394 | **exact** same figures | same row in `spine_events_DESIGN` | **MATCH** |
| **GT-2** SOL 2022-07-17 DOWN ACCEPT | IB 39.800/39.475 w0.325; side −1; mfe_norm 3.0462; mae_norm 10.5385; asym −7.4923 | **exact** (DST anchor 13:30Z) | same | **MATCH** |
| **GT-3** BTC 2023-01-11 REJECT | frac < 0.50; not in population | poke 14:48 extreme 17426; `says_accept=false`; events height 0; denom via BTC n_pokes 227 | absent from emission | **MATCH** |
| **GT-4a** band ≥2023-12-18 / holdout | raise | only DESIGN/CONFIRM loadable | N/A | **MATCH** |
| **GT-4b** CONFIRM before freeze | raise | `require_freeze` RuntimeError | N/A | **MATCH** |
| **GT-4c** frozen pins | match registry/baselines/column_pins | freeze carries 5c386984… / 1b7244c8… / e3b9fd9b… | match | **MATCH** |
| **GT-4d** q>0.5 | raise | ValueError reversed-quantile trap | N/A | **MATCH** |
| **GT-4e** control disjoint | raise on violation | D-1 assert raises on synthetic in-session entry; full emission **0** violations | clean | **MATCH** (D-1 form; see NOTE on design wording) |

---

### QA run 2 disposition table (I-1..I-12)

| ID | Severity (QA2) | Disposition | Evidence |
|---|---|---|---|
| **I-1** CONVERSION-PIN session vs accept-event median | MAJOR | **RESOLVED** | Floor uses `session_median_ibw_bps`; majors match design pin to 3dp; independent staging recompute exact. |
| **I-2** R1 per-symbol calibration (SOL drift) | MAJOR | **RESOLVED** | `R1…per_symbol` emitted; SOL p70 calib_err **+0.105** label **BROKEN**. |
| **I-3** R2 cost-adjusted p0ᶜ | MAJOR | **RESOLVED** | Per-symbol `p0_cost`; majors arithmetic recompute match. |
| **I-4** R4 race-rate (w) tercile | MINOR | **RESOLVED** | `w_contrast` +0.012 in layers R4. |
| **I-5** horizon-match disclosure | MAJOR | **RESOLVED** | Signal/control median 1391/1391 + quantiles in layers. |
| **I-6** tripwire adjudicates R2/R3/R4/R5 | MAJOR | **RESOLVED** | `tripwire.per_read` keys R5, R2, R3, R4_mfe, R4_w. |
| **I-7** power table says_accept vs evaluable n | NOTE | **RESOLVED (documented)** | Diagnostics 7,148 accepts; layers/screen state evaluable 7,070 / 11,375. |
| **I-8** SPREAD-SCALE-ROUTING emitted | MAJOR | **RESOLVED** | layers `spread_scale_routing` n=140, undecidable=2. |
| **I-9** chronological thirds L-24 F02 | MAJOR | **RESOLVED** | `time_stability_thirds` with R1–R5. |
| **I-10** accounting + per-level asserts invoked | MAJOR | **RESOLVED** | `assert_hard_integrity()` at run start; raise path; emission attestation. |
| **I-11** GT-4(e) / D-1 cross-session assert | MINOR | **RESOLVED** | `assert_control_cross_session_disjoint` implemented + invoked; design §8 text still old wording → non-blocking NOTE. |
| **I-12** R2 MDE plant in w-contrast units | MINOR | **RESOLVED** | `mde_curve_w_units` mde=0.03. |

**Score:** 8/8 MAJOR resolved · 3/3 MINOR resolved · 1/1 NOTE closed as documented · 0 OPEN blocking.

---

### D-1 / D-2 / integrity

**D-1 (cross-session control)** — rechecked on emission:
- remaining_horizon signal/control median **1391 / 1391**; mean 1381.39 / 1381.44; q10/q50/q90 identical.
- Control entries inside event session window: **0** (full panel assert PASS).
- Control n = 198,597 (≈30× events) — phase/side matched, unconditional on accept.

**D-2 (tripwire material-edge + bite)**:
- R5 raw contrast median 0.090; day-clustered CI **[−0.231, +0.320]** includes 0 → no material edge.
- All `per_read` material_edge=false → status `NO_MATERIAL_EDGE_TRIPWIRE_UNINFORMATIVE` (not HARD fail). Correct under D-2.
- Positive-control bite: corr(**0.771**) > 0.5, n=3561 — genuine price-MFE correlation (non-tautological).
- Note: R3/R4 HARD legs use global stats without day CI → structurally cannot claim material_edge under D-2; they are still adjudicated and reported (collapse fractions present). R2/R5 carry day-clustered CI.

**Population:**

| Quantity | Value |
|---|---|
| DESIGN pokes / accepts / missing entry | 13,802 / 7,148 / 78 |
| DESIGN evaluable spine | **7,070** |
| CONFIRM evaluable | **11,375** |
| Panel DESIGN / CONFIRM | 140 / 187 |

**L-32:** value reads are report layers; only tripwire / freeze / band / accounting asserts raise validity.

**Quantile direction:** (1−p) throughout; q>0.5 guard raises.

---

### Governance & boundary

| Check | Result | Evidence |
|---|---|---|
| Fresh context | PASS | subagent; no implementation work in this conversation |
| Holdout / TEST | PASS | bands only DESIGN/CONFIRM; `test_touched=false`, `holdout_touched=false` |
| Causality ≤ t−1 | PASS | universe ranking D→D+1; regime trailing prior; entry at qualify_end open |
| Derangement (L-28) | PASS | outcome_path_swap + side_derangement zero fixed points (`fixed_point_rate=0`); side-derange n_deranged=60 UNPOWERED power note |
| No Python BacktestNode | PASS | SPDR vectorised lane |
| No local accounting | PASS | scan ok + **invoked** raise |
| No per-level Δ | PASS | assert barred signed columns + **invoked** |
| CONVERSION-PIN L-21 | PASS | session medians recomputed match design |
| SPREAD-SCALE-ROUTING | PASS | emitted; 2 undecidable — no T1-alone SUPPORTED claim |
| Amendment ledger L-23 | PASS | 0L/6T/5N; D-1/D-2 ratified |
| Registry pins | PASS | 5c386984… / 1b7244c8… / e3b9fd9b… |
| Counted reads | PASS | 0 |
| Silent deviations | none | D-1/D-2 documented |

---

### Issues

None blocking.

**NOTE-1 (non-blocking) — design §8 GT-4(e) wording still describes the pre-D-1 within-session exclusion window** (`[poke−30, qualify+30]`), while code enforces the stronger D-1 rule (control entry ∉ event session). Integrity is enforced and independently verified. Optional quant-designer cleanup of §8 GT-4(e) text to name `assert_control_cross_session_disjoint` — does **not** block analysis.

**NOTE-2 (non-blocking) — R3/R4 tripwire material-edge cannot fire under day-CI D-2** because those contrasts are global scalars. Collapse is still computed and reported; R2/R5 remain the day-clustered HARD-capable legs. Acceptable given D-2 ratification; analyst should not over-read R3/R4 tripwire status as a validity pass beyond “no material edge to test.”

---

### Verdict routing

**APPROVE** — design→code fidelity holds after re-emission; all QA run 2 MAJOR/MINOR findings are independently verified fixed; golden traces GT-1..GT-4 match; CONVERSION-PIN, HARD asserts, tripwire-per-read, horizon disclosure, thirds, spread-scale, per-symbol R1, p0ᶜ, and R2 MDE-w are present and correct.

Route next: **operator analysis gate** (SPDR lane → fresh-context `analysis.md` / disposition — **not** Nautilus execute). QA APPROVE does not launch anything.

No REJECT-class defect. Residual notes are documentation / interpretation hygiene only.
