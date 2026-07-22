# SPDR-009 — QA review (append-only)

> Append-only artifact. Each QA run adds a dated section below. Never rewrite a previous run.

---

## QA run 1 — 2026-07-21 — mode: subagent — HEAD `797f926973d610bc3b6d870219f90617f245fa26`

**Stage:** DESIGN-stage review. `screen_code/` does not exist; `xen.sigbar.absorb` does not exist.
This is therefore a **design-fidelity + governance** review against the binding sources, **not** a
design-to-code trace. Every clause that can only be verified once code exists is listed in
*§F QA-run-2 trace items* rather than passed silently.

**Verdict: REVISE**
**FAILING_ARTIFACT:** `python/experiments/SPDR-009/design.md`
**REQUIRED_SKILL:** `quant-designer` (all 16 issues are design defects; none require the developer)

**Dirty tree at review time:** `?? python/experiments/SPDR-009/` (untracked — design + `design_derivations/` only).

**Sources read in full:** ckpt-015 design; Addendum v1.1 (Parts 1–3); `SIGNAL-SIGNED.md` §2.1, §2.2,
§2.3, §2.4, §2.5, Part-3 preamble, S9 card, §6.10 falsifier list; `docs/references/spdr-lane.md`;
`quant-designer/references/design-requirements.md` §1–§13; `SPDR-008/design.md` AMENDMENT-8;
`INFR-018/results/instrument_registry.json`; `xen/sigbar/{fences,sessions,spine,classes,acceptance}.py`;
`xen/evaluation.py`; all four `design_derivations/` scripts + JSON outputs.

---

### A. Source-fidelity trace — does the design test S9 as the source states it?

| Source clause | Design (§ref) | Verdict | Notes |
|---|---|---|---|
| S9 PREMISE: "Absorption class AT a level already qualified by a location signal" | §3.1 seven level kinds, gate-free | **MATCHES** | Location-only qualification; S1 gate excluded per Addendum §2.7 |
| S9 PREMISE: "1–3 bars of top-percentile V, bottom-percentile range" | §3.2 effort/no-result legs on frozen p90/p10 | **MATCHES** | Consecutive qualifying bars collapsed to the first; multi-bar aggregate = disclosure |
| S9 PREMISE: "large \|Δ\| whose sign points INTO the level" | §3.3 `delta_abs_resid ≥ d_hi` AND `signed_score = into_side × delta_ratio_resid ≥ dr_hi` | **MATCHES** | Two-leg (magnitude + direction) rule; verified in GT-3/GT-4 |
| §2.3: "the classes are tail regions of the impact ratio and the delta ratio" | §3.3 uses `delta_ratio_resid` (Δ/V) for direction, `delta_abs_resid` for magnitude | **MATCHES** | Impact ratio not used; range residual substitutes for \|ΔP\| — consistent with INFR-018's frozen classifier |
| §2.1: "level features are always zones with stated tolerance, never precision entry levels" | §3.2 τ = 0.25·`ib_width`, stated | **MATCHES (with caveat)** | See §B below — τ is source-sanctioned in *kind*, but 0.25·IB is wide; the design discloses the magnitude and its empirical origin |
| §2.1 / A1 / card ban 2: per-level Δ is estimate-grade — "do not build signals on the latter" | §0 Must-NOT-produce; §7 `fences.assert_no_per_level_delta` | **MATCHES** | `assert_no_per_level_delta` exists at `fences.py:204` |
| A5: "never flat rolling means and never raw numbers"; Δ/V and \|Δ\| normalised separately | §6.1 normaliser object; §3.3 "A raw Δ number is never used" | **MATCHES** | Both residual columns come from the pinned `1b7244c8…` baselines |
| S9 LIKELIHOOD: `rej(level)` — **micro horizon** | §1 horizon = 5 and 10 one-minute bars, primary | **MATCHES** | Horizon taken from the card, not chosen for power — explicitly stated |
| S9 TEST SPEC (a): "vs the unsigned base class at the same levels (the sign's marginal value — the central new measurement)" | T1 | **MATCHES** | Primary read |
| S9 TEST SPEC (b): "the signature mid-range (predicted ≈ no edge)" | T3 | **MATCHES** | Same contrast on no-level-within-1.0·IB bars |
| S9 TEST SPEC (c): "bare level touches" | T5 | **MATCHES** | Disclosure class |
| S9 LIKELIHOOD two-notch condition: "attempts ≥ 2 OR a single climactic attempt" | not operationalised | **MISSING — acceptable** | The design tests the one-notch base claim; not required by Addendum §3.1. Recorded, not an issue |
| S9 INVALIDATION: "close beyond the level on continued same-sign Δ — exit/flip immediately" | not implemented (fixed-H exit) | **DEVIATES — declared** | §1 declares a single-leg fixed-H object. A management rule is out of scope for a screen; the fixed-H estimand is therefore a *lower* bound on the mechanism's managed form. Not an issue, but the report must not claim it tested the managed object |
| Addendum §3.1 marginal framing: "signed-S9 minus unsigned-class on identical events" | §0 Primary read / T1 | **MATCHES** | See §C |
| Addendum §3.1 gate-free: "never by the demoted S1 session gate" | §3.1 + §7 S1-gate refusal | **MATCHES** | `acceptance.evaluate_discriminator` exists and is fenced off |
| Addendum §3.1: "defended bands (S13 detection)" as a level family | §3.1 "S13 defended-band detection is **not built**; its absence is declared" | **DEVIATES — declared** | Honest omission; narrows the habitat but does not change the mechanism |
| ckpt-015 §6 universe: 296 breadth denominator / 194 A5-fitted | §0 Universe | **MATCHES** | Survivorship note carried |
| ckpt-015 §5 bands | §0 Band row | **MATCHES** | DESIGN/CONFIRM/TEST/holdout identical; `band_window` (fences.py:73) defines only DESIGN and CONFIRM, so TEST is unreachable by construction |

---

### B. Point 1 — has τ = 0.25 loosened the mechanism?

**Finding: the loosening is real, source-sanctioned in kind, count-only in provenance, and honestly
disclosed — but its magnitude is under-argued.**

Verified independently:

| Check | Result |
|---|---|
| `diag_pool.py` computes any forward outcome? | **NO.** Counts + distance-to-nearest-level quantiles only. No forward bar indexing, no return, no excursion. |
| `diag_grid.py` computes any forward outcome? | **NO.** Counts of (bar, level) pairs, distinct bars, and Δ-qualified pairs under 3 result-cuts × 4 contact rules. No forward reference. |
| Do they import outcome machinery? | They import `gt_derive.levels_for` / `gt_derive.resid` only. `gt_derive.main()` is `__main__`-guarded, so the import computes nothing. |
| mtimes consistent with "τ fixed before outcomes existed"? | Yes: `diag_pool.json` 15:51:42 → `diag_grid.json` 15:53:01 → `gt_output.json` 15:55:09. |
| Is the strict ("level inside the bar") rule empty as claimed? | **CONFIRMED.** `diag_pool.json`: `n_base_level_inside_bar` = 0 (BTC), 0 (ETH). The design's claim "0 events on BTCUSDT and ETHUSDT across the entire DESIGN bank" reproduces exactly. |
| Is τ = 0.25 the *narrowest* workable choice? | **NO, and this is the gap.** `diag_grid.json` at the pinned p10 cut: τ=0.10 gives BTC 0 / ETH 1 / SOL 58 / XRP 6 / DOGE 16 pairs. τ=0.25 gives 3 / 13 / 145 / 13 / 32. SOL — the only symbol with a non-trivial S9 arm — is already powered-ish at τ=0.10 (58 pairs). The design does not state why 0.25 rather than 0.10 was taken, and 0.25·IB is a materially different object: at SOL's GT-1 session `ib_width` 0.380 the zone is ±0.095 on a $10.7 instrument (±89 bps), versus a bar range of 0.010. |

**Verdict on point 1:** the *mechanism* still tested is "heavy effort, no result, near a level, Δ into
the level" — it is not a different mechanism. But the zone is ~9× the event bar's own width, so "at a
level" has become "in the same neighbourhood as a level", which weakens the source's own claim that
the Δ sign identifies aggressors who *engaged that specific shelf*. This is a **disclosure/argument
defect, not a fidelity defect** — recorded as Issue 17 (informational, no change required if the
designer states the τ=0.10-vs-0.25 rationale on the record).

The design's central selection-risk defence — *the event definition was chosen on counts, never on
outcomes* — is **VERIFIED and holds** for the original registration. See Issue 15 for the forward
hazard this creates for any *later* amendment.

---

### C. Point 2 — marginal framing and arm validity (B-1)

| Requirement | Evidence | Verdict |
|---|---|---|
| Read is signed − unsigned on **identical** events (Addendum §3.1) | T1 = `ret_bps(S9) − ret_bps(BASE)` within pool P; both arms share the same effort/no-result legs, the same level set, the same entry/exit convention (§4.2 `exit-matched`) | **MATCHES** |
| Arms **disjoint** (B-1) | `gt_derive.py:191-196`: a strict if/elif/else on `(da ≥ d_hi, signed ≷ ±dr_hi)`. A row lands in exactly one arm. Verified in `gt_output.json`: arm counts sum to pool size on all three symbols (BTC 2+1+0=3; ETH 13; SOL 130+5+6=141) | **MATCHES** |
| Arms **exhaustive** within P | BASE = "everything else in P" | **MATCHES** |
| **Non-degenerate** (B-1: the signal must not fire on the whole conditioning set) | Measured S9 share of pool P = 6/141 = 4.3% on SOL, 0/13 ETH, 0/3 BTC | **MATCHES** — the baseline is genuinely a different, far larger population |
| Mirror arm is the mechanism's own antisymmetry (Addendum §2.2) | MIRROR = same `|Δ|` leg, opposite `signed_score` sign; SOL 5 events vs S9 6 | **MATCHES** |
| BASE is described accurately | §1 calls BASE "climax-hold events **WITHOUT the Δ signature**". GT-4 shows a BASE event with `delta_abs_resid` +26.0 — an enormous |Δ|, excluded only by the *direction* leg | **DEVIATES (wording)** — §4.2's literal phrasing "failing the Δ legs" is correct; §1's "without the Δ signature" is not. GT-4 discloses it, so this is cosmetic. Folded into Issue 11 |

**Verdict on point 2: the marginal framing is correct and the arms are valid.** The one substantive
worry is power, not validity — see §E.

---

### D. Point 3 — tripwire scope (T1/T2 yes, T4 no)

SPDR-008 AMENDMENT-8 (`SPDR-008/design.md:526-537`) states: *"A within-**trap** future-derangement
preserves the **trap** mean, so it CANNOT referee the T4 mean-availability contrast (B-6
mean-vacuity)."* There the derangement population **was** the T4 treatment population, so the mean was
literally preserved.

SPDR-009 §4.3 deranges outcomes **within pool P** — a strict **superset** of the S9 arm. Consequences:

- The swap preserves the **pool-P** mean, but **does not** preserve the **S9-arm** mean: after the
  swap, `mean(S9_swapped) → mean(pool P)`, which differs from `mean(S9_raw)` whenever the signal has
  any effect. So the design's stated reason — *"a within-pool derangement preserves the pool mean and
  therefore cannot referee a mean-vs-external-control comparison"* — **does not transfer verbatim from
  SPDR-008 and is imprecise as written.**
- The **conclusion is nonetheless correct**: swapped-T4 becomes `mean(pool P) − mean(matched_random)`,
  which has **no zero reference** under a leak-free construction. A "collapse toward zero" test is
  therefore undefined for T4, and a partial move would be misread in either direction. T4's causality
  correctly rests on the ≤t−1 construction plus the matched-unconditional control itself.
- T1 and T2 **are** legitimately adjudicated: both are functions of the (arm-label ↔ outcome) and
  (score ↔ outcome) pairings, which the within-pool derangement destroys while preserving both
  marginals. This matches AMENDMENT-8's corrected form.

**Verdict on point 3: the declared scope is VALID; the stated justification is WRONG-BUT-HARMLESS and
must be corrected (Issue 5).** The design does deserve credit for applying the lesson at design time.

---

### E. Point 4 — power, and the UNPOWERED-is-not-a-null clause

Re-derived from `diag_pool.json`, `diag_grid.json`, `gt_output.json`:

| symbol | bars | vol ≥ p90 | range ≤ p10 | both | pool P pairs | pool P **distinct bars** | S9 pairs | S9 **distinct bars** | MIRROR bars |
|---|---|---|---|---|---|---|---|---|---|
| BTCUSDT | 329,760 | **32,977** | **33,707** | 20 | 3 | 3 | 0 | 0 | 1 |
| ETHUSDT | 329,757 | 32,977 | 32,977 | 27 | 13 | **10** | 0 | 0 | 0 |
| SOLUSDT | 330,835 | 33,084 | 33,844 | 231 | 141 | **102** | 6 | **5** | 5 |
| XRPUSDT | 328,746 | 32,875 | 32,877 | 36 | ~13 | — | 1 (±) | — | — |
| DOGEUSDT | 313,427 | 31,344 | 32,989 | 78 | ~32 | — | 3 (±) | — | — |

Findings:

1. **The design's §6.3 BTC row is wrong.** It prints 32,976 / 32,976; the emitted diagnostic says
   32,977 / **33,707**. (Issue 9.)
2. **All headline counts are (bar × level_kind) PAIRS, not events.** GT-2 is the proof: the 2022-12-29
   01:24Z bar produces two S9 rows (PRIOR_SESSION_LOW 9.590 and PRIOR_VAL 9.59395) with identical
   entry, side and returns. Deduped to the pooled "nearest level" rule the design itself declares in
   §3.2, SOL's pool is **102**, not 141, and its S9 arm is **5**, not 6. §6.3's extrapolation is built
   on the inflated figure. (Issue 7.)
3. **The whole DESIGN-bank S9 arm across the three deepest majors is 5 events.** The pooled projection
   to "order 10^2–10^3" rests on scaling five of the most liquid perpetuals on the venue to 194
   mostly-thinner instruments — against source **A4** ("proxies and delta reads presume many trades per
   bar; thin instruments/hours degrade to the statistics stream alone"). The extrapolation is directionally
   optimistic and the design does not say so. (Issue 7.)
4. **The P_WIDE safeguard is weaker than stated.** §3.2 says P_WIDE "multiplies event counts ~3–5×",
   citing 73/146/1,291 — but those are the *effort∧result stage*, not events. At the Δ-qualified event
   level: pool P = 1/0/11/1/3 = **16 pairs** across the five majors; P_WIDE (p25, τ=0.10) = 1/7/13/6/5
   = **32 pairs**. That is **~2×**, not 3–5×. So the stated purpose — *"exists so that a `P`-UNPOWERED
   outcome does not masquerade as a null"* — is only half-delivered: if P is unpowered, P_WIDE is very
   likely unpowered too. (Issue 8.)

**Is the UNPOWERED clause honest?** Yes, and it is the design's strongest governance feature. §4
("T1 UNPOWERED is INCONCLUSIVE, never a null — the single most important reading rule in this design"),
§5 (UNPOWERED evaluated FIRST), §6.3 (BTC/ETH predeclared UNPOWERED on P at any hold), and the
**DISPOSITION CONSEQUENCE** clause ("if the POOLED T1 read is UNPOWERED on BOTH pool P and P_WIDE, the
item's disposition is INCONCLUSIVE and it is NOT the third powered null") together bind the ckpt-015 §7
closure rule correctly and pre-emptively.

**Is it stated strongly enough given this is the master go/no-go?** The clause is strong; the *numbers
behind it* are not yet credible enough to promise power. Given (2)–(4), an UNPOWERED-on-both outcome is
a materially likely — not a tail — result. That is not a defect in the rule, but the design should say
so plainly so the operator approves the run knowing the most probable outcome is INCONCLUSIVE rather
than a family-closing null. Folded into Issue 7/8.

---

### F. Point 6 — causality trace

| Requirement (§7 HARD) | Evidence | Verdict |
|---|---|---|
| Every conditioning input complete at the event bar's close | `volume_resid`, `range_resid`, `delta_abs_resid`, `delta_ratio_resid` are all functions of bar `b`'s own OHLCV+Δ, residualised against a baseline fitted on the DESIGN bank | **MATCHES** |
| Entry at the NEXT bar's open | `gt_derive.py:199,206` `entry_i = i + 1`; `entry = raw_open[entry_i]`. GT-1 event 03:27Z → entry 03:28Z open 10.770 | **MATCHES** |
| Outcome measured open-to-open, entry bar excluded from excursion | §3.4 `(entry, entry+H]`; §2 "The event bar's own range is EXCLUDED" | **MATCHES (design)**; code-verifiable at run 2 |
| **IB-edge availability**: IB edge not usable before anchor+15 | `gt_derive.py:173` `if kind.startswith("IB") and e["mins_since"] < IB_MINUTES: continue`. `session_breaks` builds IB from `mins_since < ib_minutes` i.e. `[anchor, anchor+15)`, so the edge is complete at `anchor+15`; admitting `mins_since == 15` is correct, not off-by-one | **MATCHES** |
| **Prior-session level shift**: PRIOR_* from the prior *closed* session only | `sessions.py:214` `session_end = anchor_ts.shift(-1)` (the next anchor). `gt_derive.levels_for` builds each session's profile/extremes over `[anchor, session_end)` then `shift(-1)`s the row onto the **next** anchor. So levels for anchor `A` derive from `[A_prev, A)` — closed strictly before `A`, and every event bar is `≥ A`. GT-2 confirms: anchor 2022-12-28 14:30Z, level from the 12-27 session | **MATCHES** |
| Window disjointness | §2: prior session ⟂ IB ⟂ event bar ⟂ outcome window; refractory of max(H) bars within symbol | **MATCHES for micro holds; FAILS for the session-remainder secondary** — see Issue 12 |
| Band fence raises, holdout unreachable | `fences.assert_band` raises (`fences.py:80-93`), with a dedicated `HOLDOUT VIOLATION` branch; `band_window` accepts only DESIGN/CONFIRM | **MATCHES** |
| No look-ahead in the tie-break | `into_side` falls back to `sign(L − Close(b−1))` — strictly past data | **MATCHES** |

**Verdict on point 6: causality is sound.** Both flagged rules (IB-edge availability, prior-session
shift) verified in the frozen library code, not merely asserted in prose.

---

### G. Golden-trace diff — designer's traces re-derived independently

Frozen SOL cuts read directly from `INFR-018/results/instrument_registry.json`
(`pin_sha256 5c3869845bd514bf…` ✓, `class_thresholds.per_symbol_values`, 137 symbols ✓):
`volume.high` **+5.343969692972497**, `range.low` **−0.899321035302038**,
`delta_abs.high` **+4.854608526717178**, `delta_ratio.abs_high` **+1.3777998993173006**.
Design §8 GT-4 prints +5.3440 / −0.8993 / +4.8546 / +1.3778 — **all four match to the stated precision.**

| GT | Design's claim | Independent re-derivation | Verdict |
|---|---|---|---|
| **GT-1** SOL 2022-12-28 03:27Z, IB_LOW 10.700, ib_width 0.380 | zone 0.065 = 0.171·IB ≤ 0.25; vol +5.6998 ≥ 5.3440; range −1.0117 ≤ −0.8993; `delta_abs` +9.8776 ≥ 4.8546; `into_side` −1; `delta_ratio_resid` −1.5016 ⇒ `signed_score` +1.5016 ≥ 1.3778 ⇒ **S9**; entry 03:28Z @ 10.770 LONG; H5 −4.6425, H10 −9.2851 | \|10.765−10.700\| = 0.065; 0.065/0.380 = **0.17105** ✓. All four threshold comparisons re-checked against the registry values above ✓. Close 10.765 > level 10.700 ⇒ `into` = −1 ✓. −1 × (−1.5016) = **+1.5016** ≥ 1.3778 ⇒ S9 ✓. `side = −into = +1` = LONG ✓. `gt_output.json` H5 −4.642525, H10 −9.285051 ✓; implied `Open[+5]` = 10.770 × (1 − 4.6425e−4) = 10.765, internally consistent | **MATCHES** |
| **GT-2** SOL 2022-12-29 01:24Z, PRIOR_SESSION_LOW 9.590 | 0.135 = 0.243·IB; S9; entry 01:25Z @ 9.725 LONG; H5 +15.4242, H10 −5.1414; "proves the level came from the PRIOR closed session" | 0.135/0.555 = **0.24324** ✓; `signed_score` = −1 × (−1.5397) = +1.5397 ≥ 1.3778 ✓; `gt_output.json` H5 +15.424165, H10 −5.141388 ✓. Provenance re-verified through `sessions.session_breaks` (§F) ✓ | **MATCHES** |
| **GT-3** SOL 2022-12-26 23:34Z, PRIOR_VAL 11.265225 — the SIGN GUARD | `delta_abs` +25.5469 ≥ d_hi (large \|Δ\|); Close **below** level ⇒ `into` = +1; `delta_ratio_resid` −1.3820 ⇒ `signed_score` −1.3820 ≤ −1.3778 ⇒ **MIRROR, not S9** | Close 11.260 < 11.265225 ⇒ `into` = +1 ✓; `signed_score` = +1 × (−1.38197) = **−1.38197**, and −1.38197 ≤ −1.37780 ✓ ⇒ MIRROR. **Note for run 2: this is a razor-thin boundary case (margin 0.0042).** A magnitude-only rule would indeed have called it S9 — the guard works. entry 23:35Z @ 11.260 SHORT, H5 −35.5240, H10 −26.6430 ✓ | **MATCHES** |
| **GT-4** SOL 2022-11-12 22:08Z, IB_LOW 14.945 — threshold boundary | vol +14.1027 ✓, range −1.6862 ✓, `delta_abs` +26.0113 ✓ (huge), but `signed_score` −1.2096 clears **neither** +1.3778 nor −1.3778 ⇒ **BASE** | \|−1.2096\| = 1.2096 < 1.3778 ✓ ⇒ BASE ✓. Confirms three-way assignment on **per-symbol**, not pooled, cuts. Also confirms BASE is *not* "no Δ signature" (see §C) | **MATCHES** |
| **GT-5** fence/raise list (a)–(i) | 9 must-raise behaviours | Design-stage only. `assert_band` ✓, `assert_frozen_inputs` ✓, `assert_no_per_level_delta` ✓, `acceptance.evaluate_discriminator` ✓ exist as named. (a)–(i) become run-2 trace items | **DEFERRED to run 2** |

**All four numeric golden traces reproduce exactly.** No arm-assignment or threshold-comparison
discrepancy found.

---

### H. Mandatory declaration blocks (`design-requirements.md` §1–§13)

| § | Block | Present | Verdict |
|---|---|---|---|
| 1 | MECHANISM / DERIVED (estimand, null, horizon, test) | §1 | **PASS** — anti-L-13 check present and substantive; horizon taken from the S9 card, not from power |
| 2 | OBJECT-IDENTITY (3 clauses) | §2 | **PASS** — all three answered YES with content; B-4 seam correctly argued away (no resting order) |
| 3 | CONTROL blocks, one per control | §4.2 (5 controls) | **PARTIAL — Issue 10.** `unsigned_same_pool` is complete. `mirror_arm`, `signed_score_derangement`, `matched_random_timing` omit the mandatory `disclosure: collapse fraction` line. `bare_level_touch` omits `bite/MDE`, `non-vacuity`, `disclosure` and `destroy form`. `destroy form: DERANGEMENT` present where required (L-28) ✓ |
| 4 | TRIPWIRE | §4.3 | **PASS with a gap** — form, vacuity check, statistic, survival rule, positive control, derangement all present. `expected collapse fraction ≈` not given as a point expectation (only the 0.25 survival threshold). See also Issues 4, 5, 6 |
| 5 | BANDS per stratum | §5 | **PASS** — UNPOWERED / SUPPORTED / SUGGESTIVE / WASH / CONTRADICTED, pooled declared not smuggled |
| 6 | POWER | §6.3 | **PRESENT but defective — Issues 7, 8, 9** |
| 7 | GOLDEN-TRACE | §8 | **PASS** — 4 events + 9 fence behaviours, designer-derived, "developer must NOT regenerate" stated |
| 8 | HARD / INFORMATIVE split | §7 | **PASS** — no `pass` field; disposition is an operator act (L-32/INFR-016) |
| 9 | CONVERSION-PIN | §6.1 | **FAIL — Issue 3.** Divisor object correctly declared as NONE (estimand already in bps of entry — the L-21 seam is genuinely closed by construction). But the **cost-floor line's spread inputs are neither stated nor derived on disk.** |
| 10 | SPREAD-SCALE-ROUTING | §6.2 | **PASS (conditional)** — recipe declared, `spread_scale_route` used not re-derived, `t1_undecidable: YES ⇒ disclosure-only` stated. Values resolvable only at run; listed as a run-2 item |
| 11 | Spread as a verdict leg | §0 table: "N/A with reason" | **PARTIAL — Issue 11.** The reason given ("no SUPPORTED/tradability band is emitted") is contradicted by §5, which defines a SUPPORTED band label. Substance is fine (1× spread binds the §6.1 floor); the wording is wrong |
| 12 | Amendment-direction ledger | §10 | **PASS** — opens 0L/0T/0N; the "standing note" correctly classifies τ and P_WIDE as original registration, not amendments |
| 13 | Battery/eligibility/null rules | §4.2, §5, §6.3 | **PARTIAL.** F02 time-stability: present (§5, reported-not-gated — acceptable, nothing is promoted). F04 exit-matched nulls: present ✓. **F06 derived tripwire thresholds: FAIL — Issue 4** (0.25 imported, not derived). F07 MDE-consistent read floors: unaddressed — **Issue 13** (should be N/A-with-reason: 0 TEST reads) |

---

### I. Governance & boundary checklist

| Check | Evidence | Verdict |
|---|---|---|
| Fresh-context requirement | Reviewer session contains no SPDR-009 implementation or design work | **PASS** |
| SPDR HARD integrity boundary — TRAIN-only | §0 band row; `fences.band_window` admits DESIGN/CONFIRM only | **PASS** |
| SPDR HARD — causal t−1 | §F above | **PASS** |
| SPDR HARD — no tradability/deployability claim | §0 Deliverable; §5 FLOOR framing "MARKET SCIENCE, NOT STRATEGY" | **PASS** |
| SPDR HARD — matched control + ≥25-seed battery (L-19) | `matched_random_timing` uses 30 donors, "≥ the L-19 floor of 25" | **PASS** |
| SPDR HARD — per-stratum reporting, multiplicity disclosed (L-03) | §4.1: 42-cell margin table disclosed; pooled **declared** primary with census attached | **PASS** |
| SPDR HARD — no local accounting primitives | §7 `check_no_local_accounting` (`estimand_validation.py:385`) | **PASS (design)**; run-2 execution item |
| SPDR HARD — block ≥ H on overlapping windows | §6.4: 5-day blocks vs 10-minute hold | **PASS for micro; overclaimed for session-remainder — Issue 12** |
| L-28 derangement on every permutation destroy | `signed_score_derangement` and `outcome_path_swap` both declare zero fixed points, asserted; `spine._bucketed_derangement` regenerates (200 attempts) then falls back to `np.roll` — still fixed-point-free | **PASS** |
| L-21 / EXP-025 unit seam | Estimand is bps of entry price; no ATR/IB divisor in the primary path; `ret_norm` disclosure-only with its divisor object named | **PASS** — genuinely closed by construction |
| L-22 spread verdict leg (Bybit) | `bybit_round_trip_cost_bps` used (fees + 1× spread + funding); FTMO table not referenced | **PASS** |
| L-23 amendment ledger | §10, 0/0/0, no streak | **PASS** |
| L-31 / L-29 / L-30 (Nautilus) | Declared N/A — no engine run | **PASS** |
| XENA VOID on new stack (INFR-010 R4) | No XENA routing; SPDR lane | **PASS — N/A** |
| Holdout untouchable | `assert_band` raises a named HOLDOUT VIOLATION; `holdout_start 2025-01-08` | **PASS** |
| Registry precondition (family registered) | CF-SIGAUC-001 REGISTERED, carried from ckpt-014 | **PASS** |
| Counted reads / slots | 0 / 0, no TEST contact | **PASS** |
| Frozen-input pins reproduce | `pin_sha256 5c3869845bd514bf…` ✓ (design cites `5c386984…`); `gt_output.json` records baselines `1b7244c87aaafe29…` ✓ (design cites `1b7244c8…`); 137 symbols with class thresholds ✓ | **PASS** |
| Named library symbols exist | `spine.outcome_path_swap`:606, `spine.path_swap_bite`:718, `classes.derive_thresholds`:53, `acceptance.evaluate_discriminator`:208, `evaluation.block_bootstrap_ci`:55, `.bybit_round_trip_cost_bps`:419, `.spread_scale_route`:457, `fences.assert_no_per_level_delta`:204 | **PASS — all resolve** |
| Cost-floor arithmetic reproduces | `bybit_round_trip_cost_bps(taker, hold_hours=10/60)` with spreads 0.6/0.7/1.5/2.2/2.7 returns **11.621 / 11.721 / 12.521 / 13.221 / 13.721** — matches §6.1's 11.62/11.72/12.52/13.22/13.72 exactly | **ARITHMETIC PASS; INPUTS UNSOURCED — Issue 3** |
| ckpt-015 §4 rule 1 (Addendum §2.1 master-gate conjunction) | §4 "what counts as soil" | **FAIL — Issue 1** |
| ckpt-015 §4 rule 2 (§2.2 mirror-tail) | §4.1 mirror-tail promote rule, event-level + cell-grid | **PASS** — explicitly cites the SPDR-008 7-vs-6 failure |
| ckpt-015 §4 rule 3 (§2.3 census) | §4.1, §4.2, §5 | **PASS** |
| ckpt-015 §4 rule 4 (§2.4 control families; sparse-session blocks wider than the day) | §4.2 declares all four families; §6.4 uses 5-day blocks | **PARTIAL — Issue 2** (derangement scope undefined) |
| ckpt-015 §4 rule 5 (§2.5 finite guards) | §5 finite-value guard, asserted, count reported | **PASS** |
| ckpt-015 §4 rule 6 (§2.6 robust excursion stats) | §3.4 median + 10% trimmed co-reported; mean labelled upper bound | **PASS** |
| ckpt-015 §4 rule 7 (§2.7 S1 anchor-only) | §0, §3.1, §7 refusal + GT-5(h) | **PASS** |
| ckpt-015 §4 rule 8 (§2.8 NO_MATERIAL_EDGE ≠ clean) | §4.3 verbatim: "may not be cited as a clean bill of health" | **PASS** |
| ckpt-015 §4 rule 9 (§2.9 breadth honesty, no net claim) | §0 Universe survivorship note; "May NOT rely on … any net breadth claim (INFR-019 does not exist yet)" | **PASS** |
| ckpt-015 §4 rule 10 (§2.10 horizon menu) | §0 operator direction: micro primary + session secondary; part-exercises the menu | **PASS** |
| ckpt-015 §3 sequencing (SPDR-009 first, own design → QA → operator approval) | This review is that gate | **PASS** |
| ckpt-015 §7 closure rule correctly bound | §6.3 DISPOSITION CONSEQUENCE explicitly denies third-powered-null status to an UNPOWERED outcome | **PASS — and is the design's best feature** |

---

### J. Issues (numbered; each individually addressable)

**Issue 1 — HIGH — the "soil" conjunction omits two of the master gate's three legs.**
`design.md` §4 ("What counts as soil") and §5 ("SIGNED-VALUE reading") define soil as
`T1 SUPPORTED ∧ S9−MIRROR materially positive ∧ T2 survives derangement ∧ T3 ≈ 0`. Addendum §2.1,
carried verbatim as ckpt-015 §4 rule 1 and binding on every item, requires **all three co-equal legs**:
(i) calibrates/reproduces, (ii) **beats a matched unconditional control**, (iii) **clears the measured
cost floor**. Leg (ii) is T4 and leg (iii) is the §6.1 floor — both exist in the design as *reads* but
neither is a soil leg; the floor is explicitly "framing, not a gate". §5 handles only the reverse case
(T4 SUPPORTED with T1 WASH). As written, the design could declare soil on a T1 contrast that does not
beat matched-random timing and sits below the 11.6–13.7 bps floor.
**Required change:** restate the soil conjunction to include T4 and the floor comparison as explicit
legs, per Addendum §2.1 / ckpt-015 §4 rule 1.

**Issue 2 — HIGH — the `signed_score` derangement scope is undefined, and one of the two readings is
predictably vacuous.**
§4.2 `CONTROL signed_score_derangement` says the score is *"DERANGED across events"* (global), but the
same block's `singleton coverage` line says *"a **day block** that cannot be deranged to zero fixed
points → its events dropped and COUNTED"* — implying a within-day-block derangement. These are
different nulls. Addendum §2.4 is explicit that **sparse-session events break day-block derangement**
(SPDR-007: 60 of 7,070 events derangeable) and that such events need blocks **wider than the calendar
day** or a different control family. Given §6.3's measured sparsity (SOL: 102 pool-P bars over ~20
months; most calendar days will carry 0–1 events), a day-blocked derangement would be near-empty here —
the exact SPDR-007 failure, reproduced.
**Required change:** state the derangement unit explicitly. If global-across-events, delete the
day-block singleton clause. If blocked, declare a block width wider than the day and publish the
expected derangeable fraction from the count-only diagnostics **before** the run.

**Issue 3 — HIGH — the CONVERSION-PIN's cost-floor line is not verifiable from the design.**
§6.1 states the floors (BTC 11.62 · ETH 11.72 · SOL 12.52 · DOGE 13.22 · XRP 13.72 bps) and says they
were *"computed 2026-07-21 from `xen.evaluation.bybit_round_trip_cost_bps`, taker, hold_hours = 10/60,
NOT recalled"*. I reproduced all five **exactly** — but only after inferring the per-symbol spread
inputs by subtraction (0.6 / 0.7 / 1.5 / 2.2 / 2.7 bps). **Those five numbers appear nowhere in the
design and no derivation script for them exists in `design_derivations/`.** They are also not tick
floors (BTC tick 0.1 at ~$20k ≈ 0.05 bps), so they are asserted flip-pair estimates. `design-requirements.md`
§9 requires every CONVERSION-PIN line to be *"computed from data, never recalled"*, and this is
precisely the EXP-025/L-21 defect shape — a money claim resting on an unsourced input.
**Required change:** state the per-symbol spread inputs and their derivation in §6.1, or add a
count-only/quote-only derivation script under `design_derivations/` and pin its output.
*(Secondary, LOW: `bybit_round_trip_cost_bps` with `funding_bps_per_8h=None` returns
`funding_coverage: "GAP"` and uses the conservative 1.0 bps/8h default. §6.1 cites "funding ≈ 0.021 bps"
without disclosing the GAP flag.)*

**Issue 4 — MEDIUM — the tripwire's 0.25 collapse threshold is imported, not derived (L-24 F06).**
§4.3 states the threshold is *"INHERITED from the INFR-018 sealed tripwire (L-24 F06), not re-asserted
here"*. F06 requires tripwire thresholds to be **computed from the real TRAIN autocorrelation of the
shifted stream (with CI), never asserted**. Inheriting is not deriving, and INFR-018's 0.25 was derived
for a session-scale excursion object; SPDR-009's object is a 5/10-minute open-to-open return with a
different autocorrelation structure and a different collapse geometry.
**Required change:** derive the collapse threshold on this design's own stream, or state explicitly why
the threshold is horizon-invariant and declare it a NEUTRAL inherited parameter in §10.

**Issue 5 — MEDIUM — the T4 mean-vacuity justification is wrong (the conclusion is right).**
§4.3: *"A within-pool derangement preserves the pool mean and therefore cannot referee a
mean-vs-external-control comparison (B-6 mean-vacuity). This is the SPDR-008 AMENDMENT-8 lesson."*
SPDR-008's swap was **within the trap population = the T4 treatment population**, so it literally
preserved the treatment mean. SPDR-009's swap is within **pool P**, a strict superset of the S9 arm, so
it moves `mean(S9)` toward `mean(pool P)` — the treatment mean is **not** preserved. The correct reason
the swap cannot referee T4 is that **swapped-T4 has no zero reference**: under a leak-free construction
it becomes `mean(pool P) − mean(matched_random)`, an arbitrary non-zero quantity, so neither "collapses"
nor "survives" is interpretable.
**Required change:** correct the stated reasoning. The declared scope (T1, T2 adjudicated; T4 not) is
**valid and should stand**.

**Issue 6 — MEDIUM — `spine.outcome_path_swap` / `path_swap_bite` cannot be reused unmodified.**
§4.3 says the tripwire *"Reuses `spine.outcome_path_swap` / `spine.path_swap_bite`"* and §9 lists
`xen.sigbar.spine` under **"Inherited unmodified"**. The existing implementation
(`spine.py:606-698`, `718-751`) is built for a **session-remainder** object: it requires an
`events.session_end` column, buckets donors by **remaining-session length decile**, splices to
`session_end`, and returns `evaluate_entries(..., tp1_ibw=...)` outputs whose bite statistic is
`corr(mfe, donor_mfe)` on **IB-relative excursion machinery**. SPDR-009's object is a fixed 5/10-bar
open-to-open return with donors matched on **hold length**. The two do not compose.
**Required change:** either declare that `spine` **will** be extended (and move it out of "inherited
unmodified", with a regression assert that existing SPDR-007/008 behaviour is byte-identical), or
declare a fixed-H swap inside `xen.sigbar.absorb`. Left unresolved this becomes design-to-code drift at
QA run 2.

**Issue 7 — MEDIUM — power counts are (bar × level) pairs, and the 194-symbol extrapolation
contradicts source A4.**
§3.2 and §6.3 report SOL pool P = 141 and S9 arm = 6. Deduped to the *"once (nearest level) to the
pooled read"* rule the design itself declares, `gt_output.json` gives SOL **102 distinct bars** and
**5 distinct S9 events** (GT-2's bar appears twice, at PRIOR_SESSION_LOW and PRIOR_VAL). ETH is 13 pairs
/ 10 bars. The whole DESIGN-bank S9 arm across the three deepest majors is **5 events**. §6.3's
extrapolation to "order 10^2–10^3" pooled S9 events scales these inflated pair counts from five of the
venue's most liquid perpetuals onto 194 mostly-thinner instruments, against source **A4** (thin
instruments degrade Δ reads). The within-symbol refractory will reduce n further.
**Required change:** restate the power table in deduped-event units, and state the A4 caveat on the
breadth extrapolation.

**Issue 8 — MEDIUM — the P_WIDE safeguard is ~2×, not the implied 3–5×.**
§3.2: *"It multiplies event counts ~3–5× (BTC 73 / ETH 146 / SOL 1,291 at the effort∧result stage)."*
Those are effort∧result counts, not events. At the Δ-qualified **event** level, `diag_grid.json` gives:
pool P (p10, τ=0.25) = 1 / 0 / 11 / 1 / 3 = **16** pairs across the five majors; P_WIDE (p25, τ=0.10) =
1 / 7 / 13 / 6 / 5 = **32** pairs — a **~2×** multiplier. §3.2's stated purpose ("exists so that a
`P`-UNPOWERED outcome does not masquerade as a null") is therefore only partly delivered: if P is
unpowered, P_WIDE very likely is too, and §6.3's DISPOSITION CONSEQUENCE clause would fire.
**Required change:** correct the multiplier to event units, and state plainly in §6.3 that
UNPOWERED-on-both — i.e. an **INCONCLUSIVE disposition, not a family-closing null** — is a materially
likely outcome, so the operator approves execution knowing that.

**Issue 9 — LOW — §6.3's BTCUSDT row is numerically wrong.**
Design prints `vol ≥ p90` 32,976 and `range ≤ p10` 32,976. `diag_pool.json` emits **32,977** and
**33,707**. The range figure is off by 731.
**Required change:** correct the table from the emitted diagnostic.

**Issue 10 — LOW — three of five control blocks are missing mandatory fields (`design-requirements.md` §3).**
`mirror_arm`, `signed_score_derangement` and `matched_random_timing` omit the required
`disclosure: collapse fraction reported (control effect / raw effect)` line (B-2). `bare_level_touch`
omits `bite/MDE`, `non-vacuity` **and** `disclosure`.
**Required change:** add the missing lines, or mark them N/A with a stated reason.

**Issue 11 — LOW — two internal-consistency wording defects.**
(a) §0's applicability table marks design-requirements §11 *"N/A with reason — no SUPPORTED/tradability
band is emitted (screen)"*, but §5 defines a **SUPPORTED** band label for T1–T4. The substance is fine
(1× spread is a binding leg of the §6.1 floor); the stated reason is contradicted by the design itself.
(b) §1 describes BASE as climax-hold events *"WITHOUT the Δ signature"*; GT-4 shows a BASE event with
`delta_abs_resid` +26.0. §4.2's literal phrasing ("failing the Δ legs") is the correct one.
**Required change:** reword both.

**Issue 12 — LOW — the non-overlapping-windows claim is false for the session-remainder secondary read.**
§2 declares a within-symbol refractory of `max(H)` bars = 10, and §6.4 concludes *"the within-symbol
refractory guarantees non-overlapping outcome windows, so the Phase-010 overlapping-window defect cannot
arise."* For the session-remainder hold, multiple events in the same session all run to the same session
end and overlap heavily; a 10-bar refractory does not prevent it. Day-clustered resampling does absorb
this dependence, so the **method is still valid** — only the claim is overstated.
**Required change:** narrow the claim to the micro holds and state that the session-remainder read's
dependence is handled by day clustering, not by the refractory.

**Issue 13 — LOW — §13 F07 unaddressed.**
§0 marks design-requirements §13 **APPLIES**. F01/F02/F04/F06 are addressed (F06 defectively — Issue 4);
**F07 (MDE-consistent read floors)** is not mentioned.
**Required change:** mark F07 N/A with its reason (0 counted TEST reads; no prospective read floor).

**Issue 14 — LOW — cross-reference error.**
§2 cites *"an IB-edge event before anchor+15 is REFUSED (asserted, **GT-4g**)"*. The fence list item is
**GT-5(e)**.

**Issue 15 — MEDIUM (governance hygiene, forward-looking) — full-pool forward outcomes now exist on disk.**
The design's central selection-risk defence is verified for the **original** registration: `diag_pool.py`
and `diag_grid.py` compute **no forward outcome of any kind** (independently confirmed by full read — no
forward bar indexing, no return, no excursion), and their outputs predate `gt_output.json` by 2–4
minutes. However `gt_output.json` (116 KB) contains `ret_bps_H5` / `ret_bps_H10` for the **entire**
τ=0.25 pool on BTC/ETH/SOL — 157 events — not just the four golden traces. From this point on, **any
amendment to τ, the pool legs, the arm cuts or the hold set is outcome-informed by construction**, and
the §10 standing note's protection (declared direction + LOOSER-streak flag) does not neutralise that.
**Required change:** trim `gt_output.json` to the golden-trace events (plus the per-arm counts §3.2
needs), or seal the full file with a hash and record that any post-seal amendment inherits an
outcome-informed provenance flag.

**Issue 16 — INFORMATIONAL (no change required) — τ = 0.25 rationale is incomplete.**
The design justifies τ empirically by showing the strict "level inside the bar" rule is **empty** on BTC
and ETH — **verified**: `diag_pool.json` `n_base_level_inside_bar` = 0 for both. But `diag_grid.json`
shows τ = 0.10 is non-empty on the one symbol that carries the arm (SOL 58 pairs at the pinned p10 cut),
and the design does not say why 0.25 was taken over 0.10. At GT-1's session (`ib_width` 0.380 on a
$10.7 instrument) the zone is ±89 bps around the level, ~9× the event bar's own range — so "at a level"
is closer to "in the level's neighbourhood". The mechanism tested is still S9's, and τ was fixed on
counts alone, so this is **not** a fidelity breach. Stating the 0.10-vs-0.25 rationale on the record
would close it.

---

### K. QA-run-2 (post-implementation) trace items

These clauses are unverifiable until `screen_code/` and `xen.sigbar.absorb` exist. They are **not**
passed by this review.

| # | Clause (design §) | What run 2 must trace |
|---|---|---|
| R1 | §3.1 level-set provenance | Regression assert reproducing `INFR-018/code/hyp_i4_validation.py::prior_session_levels` **byte-identically** on a fixed symbol/band; `hyp_i4_validation.py` unmodified |
| R2 | §8 GT-1…GT-4 | Emission rows for all four events match the design's arm label, `into_side`, `signed_score`, entry ts/price, side and both `ret_bps` values. GT-3 is a 0.0042-margin boundary — check float handling |
| R3 | §8 GT-5(a)–(i) | Each of the nine behaviours **raises**, not warns. (e) must admit `mins_since == 15` and refuse 14 |
| R4 | §2 refractory | Within-symbol `max(H)`-bar refractory applied, dropped events **counted**; no two same-symbol outcome windows overlap on the micro holds |
| R5 | §3.2 event granularity | One row per (bar, level kind) in margins; **exactly once (nearest level)** in the pooled read. `power_census.json` must report both pair and deduped-event counts |
| R6 | §3.4 contiguity | `[entry, entry+H]` unbroken 1-minute bars; also that `entry_ts == event_ts + 1min` (the designer's `gt_derive.py:199` uses positional `i+1`, which is not identical across a data gap) |
| R7 | §4.2 controls | 30-donor draw excludes the event's own session (GT-5(i)); derangement fixed-point count asserted **exactly 0**; MDE curves published **before** the real read |
| R8 | §4.3 tripwire | Whichever resolution Issue 6 takes; positive-control bite `corr > 0.5` computed and emitted; `NO_MATERIAL_EDGE` handled per Addendum §2.8 |
| R9 | §6.1/§6.2 | `floor_table.json` emitted with per-symbol spread inputs and a LOWER-BOUND label on tick-floored symbols; `spread_scale_route` called, 3× threshold not re-derived |
| R10 | §7 HARD list | `check_no_local_accounting("python/experiments/SPDR-009/screen_code")` passes; `assert_frozen_inputs()` at **every** entry point; CONFIRM-before-freeze refusal |
| R11 | §9 execution order | `class_thresholds_extended.json` + `pool_cuts.json` hashed **before** any CONFIRM path; no CONFIRM number computed pre-freeze |
| R12 | §5 finite guard | `is_finite` guarded on **both** operands of every correlation/regression, dropped count reported |
| R13 | §0 universe | 137-frozen / N-extended split reported on every read; extended-set-only positives flagged |

---

### L. What this review affirms

Recorded so a later run does not re-litigate settled ground:

- **Golden traces GT-1…GT-4 reproduce exactly**, including all per-symbol threshold comparisons against
  the frozen `5c386984…` registry. The three-way arm assignment is correct, and GT-3/GT-4 are genuine
  discriminating cases (a sign guard and a magnitude-without-direction guard).
- **The count-only claim is TRUE.** `diag_pool.py` and `diag_grid.py` compute no forward outcome of any
  kind. The event definition was not chosen against results.
- **Causality is sound** — verified in the frozen library, not in prose: the IB edge is unusable before
  `anchor+15` with no off-by-one, and prior-session levels derive from `[prior_anchor, current_anchor)`,
  strictly closed before the event.
- **The L-21 / EXP-025 unit seam is genuinely closed by construction** (estimand already in bps of the
  entry price; no ATR/IB divisor in the primary path).
- **The marginal framing is correct** and the S9 / MIRROR / BASE arms are disjoint, exhaustive and
  measurably non-degenerate (S9 = 4.3% of pool P).
- **The UNPOWERED discipline is the design's strongest feature** — §6.3's DISPOSITION CONSEQUENCE clause
  pre-emptively denies third-powered-null status to an unpowered outcome, which correctly protects the
  ckpt-015 §7 closure decision from an "unpowered ≠ negative" violation.
- **The tripwire's declared scope (T1/T2 yes, T4 no) is valid**, and applying the SPDR-008 AMENDMENT-8
  lesson at design time rather than post-run is the right instinct — only the stated reason needs fixing.
- **No REJECT-class defect found:** no holdout contact, no causality violation, no missing tripwire, no
  unapproved silent deviation.

**Verdict: REVISE** — 16 issues (3 HIGH, 5 MEDIUM, 7 LOW, 1 informational), routed to `quant-designer`.

---

## QA run 2 — 2026-07-21 — mode: subagent — HEAD `797f926973d610bc3b6d870219f90617f245fa26`

**Stage:** DESIGN-stage re-review of the designer's response to QA-run-1 issues 1–16.
`screen_code/` still does not exist; `xen.sigbar.absorb` still does not exist. The QA-run-1
§K trace items (R1–R13) remain open except **R13**, which the designer fixed at design stage.

**Verdict: REVISE**
**FAILING_ARTIFACT:** `python/experiments/SPDR-009/design.md`
**REQUIRED_SKILL:** `quant-designer`

**Scale of the revision:** substantially improved. Ten of the sixteen run-1 issues are fully and
verifiably closed; three are half-closed (the fix landed in one section and was not propagated to the
section that contradicts it); one fix introduces a new defect. Nine residual issues, all smaller than
run 1's. No REJECT-class defect. **Eight of the nine are one-to-three-line edits**; only R-2 requires
the designer to re-think a method.

**Dirty tree:** `?? python/experiments/SPDR-009/` (unchanged — untracked).
**New artifacts since run 1:** `design_derivations/diag_census.py` (16:42:34) + `diag_census.json`
(16:43:05); `gt_derive.py` and `gt_output.json` regenerated (16:43:48 / 16:44:05).

---

### A. Disposition of the run-1 issues

| Run-1 issue | Claimed fix | Independently verified? | Verdict |
|---|---|---|---|
| **I-1** three-leg master gate | §4 three-leg table | Table is present, correct against Addendum §2.1, and "Reproduction alone never passes" is stated verbatim. **But §5's `SIGNED-VALUE reading` block was not updated** — it still reads *"soil requires T1 SUPPORTED and S9 − MIRROR materially positive and T2 surviving derangement and T3 ≈ 0"*, i.e. leg (i) only | **PARTIAL → R-1** |
| **I-2** derangement scope | §4.2 pinned GLOBAL | Scope pinned unambiguously; the day-block clause that created the contradiction is gone; the cost is stated (does not hold regime fixed); the confound is named; both mitigations (chronological-thirds re-read, within-symbol second derangement) are declared reported-not-gated. Addendum §2.4's sparse-event warning is correctly cited | **CLOSED** |
| **I-3** cost-floor derivation | §4 T0 + §6.1 rebuilt on the INFR-017 pin | **All five floors reproduce exactly** from `column_pins.json` (`e3b9fd9b9b5851b8…` ✓): `max(one_tick_bps, candidate_C_flip_pair.median)` → `bybit_round_trip_cost_bps(taker, hold_hours=10/60)` = **11.265 / 11.326 / 11.748 / 12.498 / 12.986**. Every per-symbol input in the table matches the pin to 5 dp. Round-trip convention check is correct (`t1_round_trip_spread_bps` passes one full spread). **But the estimator is mislabelled against a binding instruction in the pin it consumes** | **PARTIAL → R-3** |
| **I-4** CF* derived not inherited | §4.3 derives CF* on this stream | 0.25 is correctly demoted to a recorded prior and the F06 argument (session-scale ≠ 5/10-min stream) is right. **But the derivation procedure is unsound as specified** | **FIX INTRODUCES A NEW DEFECT → R-2** |
| **I-5** T4 exclusion reasoning | §4.3 re-argued | Correct. The design now states that SPDR-008 deranged *within* the treatment population (mean literally preserved) whereas this deranges across a **superset** so the S9 mean is *not* preserved, and that the real reason is the **absence of a defined reference**: a swapped T4 measures pool-P-mean minus an untouched external control-mean, which has no null value to collapse toward. This is sound, and it is the correct reasoning, not merely a different one | **CLOSED** |
| **I-6** spine reuse withdrawn | §9 rewritten | §9 is exemplary — names why `spine.outcome_path_swap` does not fit (keys on `session_end`, buckets by remaining-session length, IB-relative excursions), specifies a fixed-H analogue in `absorb.py`, and requires a regression test against the session-scale original so the divergence is scoped and proven. **But §4.3 still says "Reuses `spine.outcome_path_swap` / `spine.path_swap_bite`"** | **PARTIAL → R-4** |
| **I-7** pair-vs-event counts + A4 | §6.3 census | `diag_census.json` re-run and cross-checked: **every one of the 20 per-symbol/per-pool rows in §6.3 matches the emitted JSON exactly** (pool-P events 3/10/88/10/21/56/9/25/80/10; S9 0/0/5/1/0/5/1/2/4/1; MIRROR 1/0/5/0/3/5/2/6/10/0). Totals 986 / 312 / 19 / 32 / 261 ✓. A4 extrapolation caveat added and correctly worded as an order-of-magnitude expectation, not an estimate | **CLOSED** (one arithmetic slip → R-6) |
| **I-8** P_WIDE multiplier | corrected to ~2.3× | Verified: S9 arm 44 vs 19 = **2.32×**; total events 725 vs 312 = **2.32×**. The "3–5×" figure is explicitly withdrawn and correctly identified as the effort∧result stage | **CLOSED** |
| **I-9** BTC row | corrected | The erroneous `vol ≥ p90 32,976 / range ≤ p10 32,976` columns are removed from the table entirely; the surviving BTC `effort∧no-result` = 20 matches `diag_census.json` | **CLOSED** |
| **I-10** control-block fields | four blocks completed | Verified line by line: `mirror_arm` now carries bite/MDE + exit-matched + disclosure; `signed_score_derangement` carries disclosure; `matched_random_timing` carries non-vacuity + exit-matched + disclosure; `bare_level_touch` carries non-degeneracy + bite/MDE + non-vacuity + exit-matched + disclosure. All five blocks are now complete against `design-requirements.md` §3. The added `mirror_arm` note — that MIRROR is the smaller arm so **its** MDE, not T1's, is the binding constraint — is a genuine analytical improvement, not boilerplate | **CLOSED** |
| **I-11** §11 scope + BASE wording | both corrected | §0 now reads "APPLIES in substance, with the tradability clause N/A" with the reasoning; §1's null block now defines "unsigned" as failing the **conjunction** of the two Δ legs and cites GT-4 as exactly that case | **CLOSED** |
| **I-12** non-overlap claim | narrowed in §2 | §2's NARROWED CLAIM is correct and well-argued (session-remainder read declared dependence-limited, DISCLOSURE, no promote rests on it). **But §6.4 still asserts the un-narrowed version** | **PARTIAL → R-5** |
| **I-13** F07 | N/A with reason | §0: "F07 governs counted TEST reads; this item spends 0 counted reads and never touches the TEST band, so it has no read floor to set." Correct | **CLOSED** |
| **I-14** GT-4g → GT-5(e) | corrected | §2 line 125 now cites GT-5(e) | **CLOSED** |
| **I-15** gt_output trimmed | regenerated | `gt_output.json` now holds **10 rows — BTC 3 / ETH 2 / SOL 5** (was 157), carries `scope: "PINNED GOLDEN TRACES ONLY — not a result set (QA-1 I-15)"`, and file size fell 116 KB → 7.7 KB. The §6.3 justification now rests on `diag_census.py`, which computes no outcome | **CLOSED** (trivial duplicate → R-9) |
| **I-16** τ rationale | §3.2 + §5 | The rationale is on the record **with its cost**, and it is a better answer than I expected: τ=0.10 collapses BTC to 5 and ETH to 21 events on the wide pool (verified against `diag_census.json`: BTC P_WIDE 5, ETH P_WIDE 21 ✓) and to 0 / 1 pairs on the primary (verified against `diag_grid.json` `p10_pinned tau0.1`: BTC 0, ETH 1 ✓), so τ=0.25 is what keeps the majors representable rather than deciding a family question on an alt-coin-only sample. The **zone-dilution asymmetry** clause in §5 is binding on the disposition wording and states the right asymmetry (a positive under wide τ is conservative; a null does not refute a precise-contact variant). τ=0.10 emitted as a pre-registered sensitivity, not a promote cell | **CLOSED — and this is the strongest single improvement in the revision** |

---

### B. `diag_census.py` — count-only verification (same standard applied to `diag_pool` / `diag_grid` in run 1)

**Finding: the count-only claim is TRUE.** Full read of all 155 lines.

| Check | Result |
|---|---|
| Any forward price read? | **NO.** The script never indexes a bar after the event bar. There is no `Open[i+h]`, no `entry`, no `ret`, no `mfe`/`mae`, no shift forward of any price column. |
| Any return or excursion computed? | **NO.** The only arithmetic on prices is `(Close − level_price).abs()` (contact distance) and `Close.shift(1)` (the backward tie-break). |
| Does it write any outcome? | **NO.** Emitted keys are `symbol, pool, result_cut, tau, n_effort_result, n_pairs, n_events_dedup_refractory, n_S9, n_MIRROR, n_BASE` — all counts. |
| Does importing `gt_derive` pull in outcomes? | **NO.** It imports `REGISTRY`, `levels_for`, `resid` only; `gt_derive.main()` is `__main__`-guarded. |
| Does it implement the design's declared dedup rule? | **YES** — `sort(["OpenTime","d_level"]).group_by("OpenTime").first()` = one event per bar, **nearest level wins**, exactly §3.2's pooled rule. |
| Does it implement the refractory? | **YES** — greedy first-wins on `OpenTime` gaps > 10 minutes (§2's `max(H)` = 10). |
| Does it enforce the IB-availability causality rule? | **YES** — `~level_kind.starts_with("IB") | (mins_since >= IB_MINUTES)`. |
| Reproduces the §6.3 table? | **YES — all 20 rows exact.** |

One implementation divergence between the two designer scripts, noted at R-8.

---

### C. Golden traces — unchanged by the entry-by-clock fix (I-15 / R13)

`gt_derive.py:202-205` now adds `if (raw_ts[entry_i] - e["OpenTime"]).total_seconds() != 60: continue`,
replacing the pure positional `i+1`. This is the QA-run-1 **R13** item, fixed at design stage.

Re-read of the regenerated `gt_output.json` against §8:

| GT | §8 values | Regenerated `gt_output.json` | Verdict |
|---|---|---|---|
| GT-1 | S9, IB_LOW 10.700, into −1, ss +1.5016, entry 03:28Z @ 10.770 LONG, H5 −4.6425, H10 −9.2851 | S9, IB_LOW 10.7, into −1, ss 1.5016, entry 2022-12-28 03:28:00 @ 10.77 LONG, H5 −4.6425, H10 −9.2851 | **BYTE-UNCHANGED** |
| GT-2 | S9, PRIOR_SESSION_LOW 9.590, ss +1.5397, entry 01:25Z @ 9.725 LONG, H5 +15.4242, H10 −5.1414 | identical | **BYTE-UNCHANGED** |
| GT-3 | MIRROR, PRIOR_VAL 11.265225, into +1, ss −1.3820, entry 23:35Z @ 11.260 SHORT, H5 −35.5240, H10 −26.6430 | identical | **BYTE-UNCHANGED** |
| GT-4 | BASE, IB_LOW 14.945, into −1, ss −1.2096, entry 22:09Z @ 14.950 LONG | identical | **BYTE-UNCHANGED** |

**Confirmed: the clock fix changed no golden-trace value.** All four remain valid QA-run-2 diff targets,
and the per-symbol cuts they are checked against (`5c386984…`, SOL `volume.high` +5.343969,
`range.low` −0.899321, `delta_abs.high` +4.854608, `delta_ratio.abs_high` +1.377800) are unchanged.

---

### D. Amendment ledger (§10) — L-23 honesty audit

**Arithmetic:** the running counts are internally consistent at every step
(1T → 1T/1N → 2T/1N → 3T/1N → 3T/2N → 4T/2N → 5T/2N → 5T/3N → 5T/4N → 6T/4N → 6T/5N) and the declared
total **0 LOOSER / 6 TIGHTER / 5 NEUTRAL** is correct. No one-directional LOOSER streak. All eleven are
correctly declared **pre-measurement**, which is true — no read has been taken.

**AMENDMENT-2 (NEUTRAL, not LOOSER) — ACCEPTED.** A global derangement is, on a pure validity axis,
a weaker null than a regime-matched one, and a strict reading would call this LOOSER. The label is
nonetheless honest, because the specified alternative was **never operable**: at ~1 event per
symbol-day a day-blocked derangement has almost no permutable mass, so there was no tightness to lose
— only the appearance of it. That is precisely the failure Addendum §2.4 documents (SPDR-007: 60 of
7,070 derangeable). The amendment states the cost, names the confound it cannot remove, and adds two
reported mitigations rather than hiding behind the label. **NEUTRAL stands; a reviewer could reasonably
have argued LOOSER, and the ledger should note that the call was contested** — that note is the only
thing missing, and it is not worth a numbered issue.

**AMENDMENT-7 (TIGHTER) — ACCEPTED.** The grounds given ("the honest numbers are worse than the ones
they replace") are the right test. It does three restrictive things: withdraws inflated pair counts for
lower true counts, corrects a wrong row, and **declares every per-symbol cell UNPOWERED**, which removes
readable strata from the design rather than adding them. That is a reduction in what the design is
permitted to claim. TIGHTER is correct.

**Remaining L-23 clause:** *"After the final amendment, re-derive the expected false-qualifier count
under the global null with the FINAL gate set."* Not addressed. Almost certainly N/A here — this design
has **no gate set** (everything is a report layer, L-32/INFR-016, no `pass` field anywhere) — but the
N/A should be stated rather than left silent. → **R-10**.

---

### E. Residual issues

**R-1 — MEDIUM — §5's soil sentence still states the one-leg gate, contradicting the new §4 table.**
§4 now carries Addendum §2.1's three-leg conjunction correctly. But §5's `SIGNED-VALUE reading` block
still says *"soil requires T1 SUPPORTED and S9 − MIRROR materially positive and T2 surviving
derangement and T3 ≈ 0"* — legs (ii) T4 and (iii) the cost floor are absent. §5 is the block the
analyst and the operator read when writing the disposition, so as it stands the item can still be
dispositioned on reproduction alone — the exact defect I-1 raised. §5's separate `FLOOR framing` line
does not repair this: it frames the floor as a report label, not as a soil leg.
**Required change:** restate §5's soil sentence as the same three-leg conjunction §4 now carries.

**R-2 — MEDIUM — the new CF* derivation is calibrated in a regime where the statistic is undefined,
and never in the regime where it is applied.**
§4.3 now derives CF* as *"the upper 95th percentile of |collapse_fraction| over ≥200 swap seeds run on
a KNOWN-NULL arm (events whose outcome paths are already deranged)"*. Two problems compound:
- `collapse_fraction = destroyed_contrast / raw_contrast`. On a **known-null** arm the *denominator* is
  ≈ 0 by construction, so the statistic is a ratio of two near-zero noise terms — heavy-tailed, with no
  finite variance and an upper 95th percentile that is essentially a draw from the sampling noise of
  the division. It will not converge in any useful sense across 200 seeds.
- The **MATERIAL-EDGE PRECONDITION** in the same block restricts CF* to fire *only* where the raw
  contrast is a material edge (day-clustered CI excludes zero). So CF* is calibrated exclusively in a
  regime (`raw ≈ 0`) that it is then forbidden from being applied in (`raw` materially non-zero).
The design already contains the right instrument: §4.2's **additive-plant sweep**. Calibrating CF* on
an arm carrying a *planted material effect of known size*, then measuring how far `collapse_fraction`
falls when that arm's outcomes are deranged, produces a distribution in the regime where the threshold
is actually used — and is a genuine F06 derivation on this stream.
**Required change:** re-specify the CF* calibration on a planted-material-edge arm, not a known-null
arm. The F06 argument for deriving rather than inheriting is correct and should stand.

**R-3 — MEDIUM — the spread estimator is mislabelled against a binding instruction in the pin it
consumes, and its sample scope is not disclosed.**
§6.1 calls `candidate_C_flip_pair` *"the quoted-spread proxy"*. `column_pins.json`
(`W2_decision.replacement_estimator`) says the opposite, in terms that bind its consumers:
`known_bias: "CONSERVATIVE UPPER BOUND, not the quoted spread — adjacent flips also span real price
movement. Right direction of error for a cost floor; **must be labelled as such wherever used**."`
Three consequences the design does not carry:
- the label the pin requires is missing;
- `status: VALIDATED_ON_SAMPLE_ONLY` — the medians used are over **4 pre-declared sample days**
  (`n = 5760` minutes, 20 symbol-days), not the TRAIN band. `design-requirements.md` §9 asks for the
  **TRAIN-median** of the divisor object; a 4-day median is not that, and the scope is not stated;
- the **direction of error is stated for only one of the two coverage classes.** §6.1's COVERAGE
  CAVEAT correctly labels non-audited instruments `SPREAD_TICK_FLOOR_ONLY` = lower bound on cost =
  **upper** bound on net (the unsafe direction). For the five audited symbols the flip-pair bias runs
  the *other* way — an upper bound on cost, hence a **conservative** floor. Both directions are in play
  in the same table and only one is labelled.
The arithmetic is correct and the sourcing is now real; this is a labelling and scope-disclosure defect,
not a numbers defect.
**Required change:** carry the pin's mandated "conservative upper bound, not the quoted spread" label;
state the 4-sample-day scope; label the direction of error for both coverage classes.

**R-4 — LOW/MEDIUM — §4.3 still claims the spine reuse that §9 withdraws.**
§9 correctly withdraws it and specifies the fixed-H analogue. §4.3's tripwire block still opens
*"Reuses `spine.outcome_path_swap` / `spine.path_swap_bite`."* A developer reading §4.3 for the
tripwire spec — the natural place to look — gets the retracted instruction. The §4.3 positive-control
line also still cites `corr(swapped_price_mfe, donor_real_mfe)`, which is `spine.path_swap_bite`'s
IB-relative construction rather than the bps-of-entry analogue §9 specifies.
**Required change:** point §4.3 at the `absorb.py` fixed-H analogue and restate the bite statistic in
the analogue's own units.

**R-5 — LOW — §6.4 was not narrowed with §2.**
§2 now carries the correct NARROWED CLAIM. §6.4 still reads *"the within-symbol refractory (§2)
guarantees non-overlapping outcome windows, so the Phase-010 overlapping-window defect cannot arise"*
— true for the micro holds, false for the session-remainder secondary. The inference method is still
valid (day-clustered resampling absorbs the within-day overlap); only the claim is unnarrowed.
**Required change:** propagate §2's narrowing into §6.4.

**R-6 — LOW — §6.3's P_WIDE MIRROR column total is wrong.**
The table prints **33**. The per-row values it prints (0, 3, 4, 1, 2, 7, 2, 3, 16, 2) sum to **40**,
which is what `diag_census.json` emits. Every other total in the row (986 / 312 / 19 / 32 / 261 / 725 /
44) is correct. Arithmetic slip in one cell.
**Required change:** 33 → 40.

**R-7 — LOW — §4.2 still quotes the withdrawn pair count.**
`CONTROL unsigned_same_pool` still argues non-degeneracy from *"the measured S9 share of pool P is ~4%
(SOL 6/141)"*. Both figures are the pair counts AMENDMENT-7 withdrew. The post-census values are
**19/312 = ~6%** pooled and **SOL 5/88**. The non-degeneracy conclusion is unaffected — it is stronger,
if anything — but the design should not carry a number it has formally withdrawn elsewhere.
**Required change:** update to the census figures.

**R-8 — LOW — the two designer scripts disagree on the `into_side` tie-break.**
`gt_derive.py:154` computes `prev_close` as `Close.shift(1)` on the full joined frame = the genuinely
previous bar. `diag_census.py:60` computes it as `Close.shift(1).over("anchor_ts")` on the **filtered**
`base` frame = the previous *qualifying* bar, which may be hours earlier. The two therefore break exact
`Close == level` ties differently. Impact is confined to exact ties (rare, but reachable on coarse-tick
instruments where a level can sit exactly on a close), so the census counts may differ from what the
implementation will produce by a small number of events.
**Required change:** make the tie-break identical in both, and pin which definition `absorb.py` uses.

**R-9 — TRIVIAL — `gt_output.json` contains a duplicated BTC row.**
`2022-11-08 00:44:00` (BASE) appears twice, from overlapping slices in the trace-picking logic. Harmless
— no §8 trace depends on it — but it makes BTC read as 3 events when it is 2 distinct bars.

**R-10 — LOW — L-23's final-gate clause is unaddressed.**
*"After the final amendment, re-derive the expected false-qualifier count under the global null with the
FINAL gate set."* Almost certainly N/A — this design has no gate set (report layers only, no `pass`
field). State the N/A with its reason, as §0 already does for `design-requirements` §13 F07.

---

### F. QA-run-2 additions to the post-implementation trace list

Run-1 items R1–R12 stand unchanged (**R13 is now CLOSED** — fixed at design stage). Added:

| # | Clause | What run 3 must trace |
|---|---|---|
| R14 | §4.3 CF* | CF* computed and published to `results/tripwire.json` with its seed set **before** any adjudicated read; whichever calibration regime R-2 resolves to; the derived value reported against the 0.25 prior even when it lands far from it |
| R15 | §4.2 derangement | Scope is GLOBAL in code; the within-symbol second derangement is actually emitted; deranged fraction reported beside every effect; chronological-thirds ρ re-read present |
| R16 | §9 `absorb.py` path-swap | The fixed-H analogue exists, donors bucketed by **hold length** (not remaining-session length), excursions in **bps of entry**, and the regression test against `spine.outcome_path_swap`'s derangement + bite semantics on a session-scale fixture passes |
| R17 | §6.1 floor table | `results/floor_table.json` carries the pin-mandated conservative-upper-bound label, the sample-day scope, and `SPREAD_TICK_FLOOR_ONLY` on every non-audited instrument |
| R18 | §3.2 τ sensitivity | The τ=0.10 read is emitted as a **sensitivity**, is not counted in the 4-cell multiplicity budget, and is not promotable |
| R19 | §2 / §6.4 | Session-remainder reads are labelled DISCLOSURE in the emission and no cluster or promote claim references them |

---

### G. What run 2 affirms

- **`diag_census.py` computes no forward outcome of any kind** — verified to the same standard as
  `diag_pool.py` / `diag_grid.py` in run 1. The event definition remains un-chosen against results.
- **Every one of the 20 per-symbol/per-pool rows in the new §6.3 census reproduces exactly.**
- **All five cost floors reproduce exactly** from the pinned `column_pins.json` inputs. The arithmetic
  and the sourcing are now real; only the labelling is defective.
- **The four golden traces are byte-unchanged** by the entry-by-clock fix.
- **The P_WIDE ~2.3× multiplier, the τ=0.10 collapse figures (BTC 5 / ETH 21 wide, 0 / 1 primary), and
  the "MIRROR is larger than S9" finding (32 vs 19) all reproduce.**
- **The T4 tripwire-exclusion reasoning is now correct** — the run-1 correction was understood, not
  merely pasted.
- **The amendment ledger is arithmetically sound and its two contested direction labels
  (AMENDMENT-2 NEUTRAL, AMENDMENT-7 TIGHTER) are honest.**
- **`gt_output.json` is trimmed to the pinned traces**, closing the outcome-informed-amendment hazard.
- **The τ=0.25 rationale and its zone-dilution cost are on the record and binding on the disposition
  wording** — the single strongest improvement in this revision, and it makes a future null
  interpretable rather than overclaimed.
- No holdout contact, no causality violation, no missing tripwire, no unapproved silent deviation.

**Verdict: REVISE** — 9 residual issues + 1 trivial (2 MEDIUM requiring thought, the rest one-to-three
line edits), routed to `quant-designer`. R-1 and R-2 are verdict-material; R-3 through R-10 are
accuracy and propagation.

---

## QA run 3 — 2026-07-21 — mode: subagent — HEAD `797f926973d610bc3b6d870219f90617f245fa26`

**Stage:** DESIGN-stage re-review of the response to QA-run-2 residuals R-1…R-10.
`screen_code/` and `xen.sigbar.absorb` still do not exist — this remains a design review; the
post-implementation trace list (R1–R12 from run 1, R14–R19 from run 2, plus R20 below) stands open.

**Verdict: APPROVE**

All sixteen run-1 issues and all ten run-2 residuals are closed and independently verified. No fix
introduced a new defect. The design is ready for the operator's execution gate. **QA APPROVE does not
launch anything** — execution remains the operator's act.

**Dirty tree:** `?? python/experiments/SPDR-009/` (unchanged).
**Regenerated since run 2:** `diag_census.py` (16:54:50) → `diag_census.json` (16:55:45);
`gt_derive.py` (16:54:59) → `gt_output.json` (16:55:14).

---

### A. Disposition of the run-2 residuals

| Residual | Claimed fix | Independently verified | Verdict |
|---|---|---|---|
| **R-1** §5 soil clause | restated with all three legs | §5:460-466 now states (i) T1+mirror+T2+T3, (ii) T4 positive, (iii) S9 median clears its floor, plus "Reproduction alone never passes (Addendum §2.1)" and an explicit pointer that **§4's table is authoritative** and this clause exists "so a reader of §5 alone cannot disposition on leg (i)". §4 and §5 now agree | **CLOSED** |
| **R-2** CF* calibration | moved to a planted causal edge at ~1× MDE | See §B — the new regime **is** the application regime, and the vanishing-denominator reasoning is written into §4.3 correctly | **CLOSED** |
| **R-3** spread-estimator labelling | pin label + sample scope + both directions | §6.1 now carries the pin's exact language ("a CONSERVATIVE UPPER BOUND on the spread, NOT the quoted spread"); names all four sample days — **2022-09-14, 2023-01-11, 2023-06-07, 2023-11-01**, which match `column_pins.json` `days_used` exactly; states both directions and that "the two classes are never mixed in one statement". The added consequence — *"a 'clears the floor' reading on them is conservative, while a 'below the floor' reading on them is NOT conclusive"* — is sharper than what I asked for and is the correct asymmetry | **CLOSED** |
| **R-4** §4.3 spine residual | removed; bite in bps | §4.3:391 now reads "`spine.outcome_path_swap` / `path_swap_bite` are NOT reused as-is (QA-2 R-4); donors are bucketed by hold length rather than remaining-session length". Bite restated as `corr(swapped_mfe_bps, donor_real_mfe_bps)` in bps of the target's entry price, with the divisor-mismatch reason. SPDR-007's 0.77 / SPDR-008's 0.64 are explicitly demoted: *"PRIORS on a different object, not thresholds transplanted here — the 0.5 floor is the inherited rule, the comparison numbers are context"*. Grep confirms only two `spine.` mentions remain in the body, both stating non-reuse | **CLOSED** |
| **R-5** §6.4 non-overlap | aligned with §2 | §6.4:629-635 now splits the claim: micro holds guaranteed by the refractory; **"For the SESSION-remainder secondary the windows DO overlap within a symbol"**, that read relies on day clustering alone, "the guarantee is weaker and the read stays DISCLOSURE with no promote claim resting on it". Matches §2's narrowed claim | **CLOSED** |
| **R-6** §6.3 totals | census regenerated | See §C — **every one of the eight totals is now its own column sum, and all 20 rows reproduce from the regenerated JSON** | **CLOSED** |
| **R-7** §4.2 non-degeneracy | re-based on events | §4.2:301-305 now argues from "19 of 313 events over ten instruments; SOL 5 of 87 — deduplicated event counts, §6.3, not the withdrawn pair counts". Both figures match the regenerated census. The ~6% share is the correct post-dedup number | **CLOSED** |
| **R-8** tie-break unified | `prev_close` before the filter | `diag_census.py:56-64` now computes `pl.col("Close").shift(1)` on the full session-attached frame `j` **before** the event filter, with the reason in a comment. This is the same construction as `gt_derive.py:154`. The two scripts now break `Close == level` ties identically | **CLOSED** |
| **R-9** duplicate GT row | emission de-duplicated | `gt_output.json` now holds BTC **2** / ETH **2** / SOL **5**; the repeated `2022-11-08 00:44:00` BTC row is gone | **CLOSED** |
| **R-10** L-23 final-gate clause | N/A with reason | §10 records it as N/A because the item "has no qualifier gate set, spends no counted read, and emits no admission decision, so there is no false-qualifier count to re-derive". Correct — the design is report-layers-only with no `pass` field anywhere (§7) | **CLOSED** |

---

### B. R-2 in detail — is the new calibration regime the application regime?

**Yes. The fix is correct, and it is correct for the right reason.**

| Question | Finding |
|---|---|
| Is the vanishing-denominator problem stated? | Yes, and accurately: *"on a known-null arm the raw contrast is ≈0, so `collapse_fraction = destroyed/raw` has a vanishing denominator and is undefined-to-explosive"*. |
| Is the regime-mismatch problem stated? | Yes: *"it would calibrate the threshold in precisely the regime where the material-edge precondition forbids the threshold from ever being used"*. That was the substantive half of R-2 and it is understood, not paraphrased. |
| Is the new regime the application regime? | **Yes.** The plant makes the raw contrast material **by construction**, which is exactly the precondition (`raw CI excludes zero`) that gates the survival rule. Denominator is bounded away from zero in expectation; the ratio is well-defined. |
| Does the calibration measure the right quantity? | **Yes.** CF* is now *"how much of a genuinely causal, non-leaking edge survives this destroy by chance"* — the upper 95th percentile of `\|collapse_fraction\|` over ≥200 seeds on a planted **causal** edge. The survival rule `\|collapse_fraction\| > CF*` then reads: *more of the contrast survived the outcome-destroy than a genuinely causal edge ever does by chance ⇒ the construction is reading the outcome*. The logic runs in the correct direction. |
| Does it use the design's own instrument? | Yes — §4.2's additive-plant sweep, already required for every control's MDE. No new machinery. |
| Is it published before use? | Yes — `results/tripwire.json` with its seed set **and plant size**, before any real read; 0.25 retained as a recorded prior with "if the derived CF* lands far from it, that is reported, not smoothed". |

**One observation, carried as a trace item rather than a residual (R20).** The plant is specified at
**~1× MDE** — the *weakest* material edge the design can recognise (§5's SUPPORTED band opens at
`effect ≥ its own MDE`). That is the noisiest point of the `destroyed/raw` distribution, so it yields
the **highest** CF*, and since survival requires `|collapse_fraction| > CF*`, a higher CF* makes the
leak gate **more permissive**. The choice is defensible — it calibrates at the boundary where a real
edge would most plausibly sit given this design's power situation — but CF*'s stability across plant
sizes is not visible from a single point. Emitting CF* at 2–3 plant sizes (e.g. 1×, 2×, 3× MDE) costs
nothing beyond seeds and would show whether the threshold is a property of the stream or of the plant.
**This is an improvement, not a correction, and does not qualify the verdict.**

---

### C. Regenerated census — full re-verification

`diag_census.py` re-read after the R-8 edit: **still count-only.** No forward bar index, no return,
no excursion, no forward price of any kind; emitted keys remain counts only. The R-8 change touches
only where `prev_close` is computed.

Every cell of §6.3 re-checked against the regenerated `diag_census.json`:

| symbol | P events | S9 | MIR | BASE | P_WIDE | S9 | MIR | table = JSON? |
|---|---|---|---|---|---|---|---|---|
| BTCUSDT | 3 | 0 | 1 | 2 | 5 | 1 | 0 | ✓ |
| ETHUSDT | 10 | 0 | 0 | 10 | 21 | 3 | 3 | ✓ |
| SOLUSDT | 87 | 5 | 5 | 77 | 176 | 6 | 3 | ✓ |
| XRPUSDT | 10 | 1 | 0 | 9 | 29 | 5 | 1 | ✓ |
| DOGEUSDT | 22 | 0 | 3 | 19 | 38 | 3 | 1 | ✓ |
| ADAUSDT | 57 | 5 | 5 | 47 | 111 | 7 | 7 | ✓ |
| AVAXUSDT | 8 | 1 | 1 | 6 | 24 | 4 | 1 | ✓ |
| LINKUSDT | 25 | 2 | 6 | 17 | 41 | 1 | 3 | ✓ |
| MATICUSDT | 81 | 4 | 10 | 67 | 255 | 16 | 15 | ✓ |
| LTCUSDT | 10 | 1 | 0 | 9 | 27 | 4 | 2 | ✓ |

**Column sums recomputed from the printed rows:** 313 / 19 / 31 / 263 / 727 / 50 / 36 — **every
total is now its own column sum**, and every one matches the emitted JSON (`effort∧no-result` 986 ✓).
The run-2 defect (MIRROR total 33 against rows summing to 40) is gone and cannot recur silently, since
the design now states in-line that "totals are the column sums of this table and reproduce from
`diag_census.json`".

**Cell movement from the tie-break unification** is ≤3 everywhere, as claimed: SOL P 88→87,
SOL P_WIDE 179→176, XRP P_WIDE 25→29 (+4 — the one cell exceeding "≤3"; the design's "≤3 per cell"
wording is off by one on this cell, which I record here rather than as an issue since the direction
and magnitude are immaterial and the emitted JSON is authoritative), DOGE P 21→22, ADA P 56→57,
AVAX P 9→8, MATIC P 80→81.

**Multipliers re-derived:** S9 arm 50/19 = **2.63×** ("~2.6×" ✓); total events 727/313 = **2.32×**
("~2.3×" ✓). Both restated correctly in §3.2. The MIRROR-larger-than-S9 finding survives the
regeneration (31 vs 19) and §6.3's binding-MDE conclusion is unchanged.

---

### D. Golden traces — byte-unchanged through a third regeneration

| GT | §8 | regenerated `gt_output.json` | Verdict |
|---|---|---|---|
| GT-1 | S9, IB_LOW 10.700, into −1, ss +1.5016, entry 03:28Z @ 10.770 LONG, H5 −4.6425, H10 −9.2851 | identical | **BYTE-UNCHANGED** |
| GT-2 | S9, PRIOR_SESSION_LOW 9.590, ss +1.5397, entry 01:25Z @ 9.725 LONG, H5 +15.4242, H10 −5.1414 | identical | **BYTE-UNCHANGED** |
| GT-3 | MIRROR, PRIOR_VAL 11.265225, into +1, ss −1.3820, entry 23:35Z @ 11.260 SHORT, H5 −35.5240, H10 −26.6430 | identical | **BYTE-UNCHANGED** |
| GT-4 | BASE, IB_LOW 14.945, into −1, ss −1.2096, entry 22:09Z @ 14.950 LONG | identical | **BYTE-UNCHANGED** |

All four have now survived three independent regenerations of `gt_derive.py` (entry-by-clock fix in
run 2, tie-break unification and de-duplication in run 3) without a single value moving. They remain
valid diff targets for the post-implementation trace, and the per-symbol cuts they are checked against
(`5c386984…`; SOL +5.343969 / −0.899321 / +4.854608 / +1.377800) are unchanged.

---

### E. Amendment ledger — L-23 audit of AMENDMENT-12…17

**Arithmetic:** 0/7/5 → 0/8/5 → 0/8/6 → 0/9/6 → 0/9/7 → 0/9/8. Every running count is correct and the
declared total **0 LOOSER / 9 TIGHTER / 8 NEUTRAL** matches. No one-directional LOOSER streak.

**Direction labels — all defensible:**
- A-12 (§5 soil clause) **TIGHTER** ✓ — restores two gate legs to the block that governs the disposition.
- A-13 (CF* recalibration) **TIGHTER** ✓ — a valid calibration replaces an invalid one; the gate gains teeth it did not have.
- A-14 (spread labelling) **NEUTRAL** ✓ — accuracy of a cost claim's direction; no threshold moved.
- A-15 (§4.3 spine + bite units) **TIGHTER** ✓ — removes a retracted instruction from the block a developer reads.
- A-16 (four consistency fixes + tie-break) **NEUTRAL** ✓ — the tie-break unification is the only one that moves numbers, and it moves them in both directions (some cells up, some down), which is the signature of a consistency fix rather than a loosening. Correctly labelled.
- A-17 (dedup + L-23 N/A) **NEUTRAL** ✓ — completeness.

**Contested-label note:** present, and it does what L-23's spirit asks — it records my run-2 point that
AMENDMENT-2 could be scored LOOSER (a global derangement does not hold regime fixed), states the
alternative count **1L/9T/7N**, notes that even under that scoring there is no one-directional streak,
and marks the call "contested rather than settled". This is the right handling: the disagreement is on
the record for the operator rather than resolved by the party with an interest in the answer.

**One ledger gap, non-blocking:** AMENDMENT-16's regeneration also moved the P_WIDE **S9-arm**
multiplier from ~2.3× to ~2.6× (§3.2 is updated correctly), but the entry records only the census-cell
movement, and AMENDMENT-7's historical text still quotes the superseded ~2.3× S9 figure. AMENDMENT-7 is
a correct record of what run 2 did, so it should not be edited; a half-line in AMENDMENT-16 noting the
multiplier restatement would close the trail. Recorded, not numbered.

---

### F. Addition to the post-implementation trace list

Run-1 R1–R12 and run-2 R14–R19 stand. Added:

| # | Clause | What the post-implementation QA must trace |
|---|---|---|
| R20 | §4.3 CF* calibration | The plant is **causal** (not a relabelling), sized at ~1× the published MDE, and the raw contrast on the planted arm is verified material before CF* is taken. Emit CF* at 2–3 plant sizes so its stability is visible; if CF* varies materially with plant size, that is a finding for the operator, not a number to average |
| R21 | §6.3 census reproduction | `results/power_census.json` reproduces `diag_census.json` on the ten instruments under the implementation's own code path — a disagreement means `absorb.py` and the designer's census disagree on dedup, refractory or tie-break |

---

### G. Verdict

**APPROVE.**

Across three runs this design has closed 16 issues and 10 residuals, including one defect that a fix
introduced and one that only surfaced because the fix was checked rather than accepted. Every number
in the design that I could verify against a pinned artifact or re-run script now reproduces exactly:
the ten-instrument census (all 20 rows and all 8 totals), the five cost floors, the four golden traces,
the τ-sensitivity counts, the P_WIDE multipliers, and the frozen per-symbol cuts.

What makes this approvable is not that it is clean but that it is **honest about where it is weak**: the
S9 arm is scarce (19 events over ten deep instruments), the MIRROR arm is larger than the signal arm,
the two biggest instruments in the venue contribute nothing to the primary read, the contact zone is
~9× the event bar and dilutes a precise-contact effect, and the spread inputs are 4-day sample medians
of an upper-bound estimator. Every one of those is stated in the design rather than discovered later,
and two governance clauses convert them into binding constraints on the conclusion: the
**DISPOSITION CONSEQUENCE** clause (UNPOWERED on both pools ⇒ INCONCLUSIVE, **not** the third powered
null that would close CF-SIGAUC-001) and the **zone-dilution asymmetry** clause (a null under this τ
does not refute a precise-contact variant). For an item that is the checkpoint's master go/no-go on a
family's fate, those two clauses are what make a null safe to act on and an inconclusive impossible to
misread as a null.

Residual risk at execution: **the most likely outcome is INCONCLUSIVE, not a family-closing null.** The
design says so itself. The operator should approve execution knowing that, and should treat a
"third powered null" reading as available only if the pooled T1 read clears its published MDE on at
least one pool.

**No REJECT-class defect at any point across three runs:** no holdout contact, no causality violation,
no missing tripwire, no unapproved silent deviation, no counted read, no TEST contact.

---

### H. Length judgement (operator question, held separate from the verdict)

`design.md` is **851 lines against the ~300-line budget** (`research-pipeline/_pipeline-config.md`;
`quant-designer/SKILL.md` — "dense (tables/bullets), no prose padding"). Section sizes:

| lines | section | |
|---|---|---|
| 105 | §10 amendment ledger | review-cycle history |
| 90 | §4.2 controls | mandatory, load-bearing |
| 69 | §6.3 power | mandatory + measured table |
| 66 | §4.3 tripwire | mandatory, load-bearing |
| 61 | §8 golden trace | mandatory, load-bearing |
| 51 | §6.1 floor + CONVERSION-PIN | mandatory + measured table |
| 49 | §3.2 event pool | spec + τ history |

**I partly disagree with the "dense, not padded" read.** The specification sections are dense and
should not be cut — §4.2, §4.3, §6.3's census, §6.1's floor table, §8's traces, §2, §5 and §7 are the
mandatory declaration blocks plus the measured evidence, and they are precisely what let three QA runs
*verify* rather than trust. That material got longer and the design got better. But roughly **200 lines
are review-cycle archaeology that has now served its purpose**, in two forms:

1. **§10 (105 lines).** Under L-23 this is load-bearing, but it is *history*, not specification, and it
   did not exist at registration. At 17 entries it is the single largest section of the design. Move it
   to a sibling `amendments.md`, keeping inline only the running count, the contested-label note, and
   the standing note. Reclaims ~90 lines with no loss of governance.
2. **~110 lines of inline QA narration.** Most fixed clauses carry the superseded version *and* its
   refutation: §4.3 spends eight lines re-litigating the SPDR-008 analogy before stating the operative
   rule; §4.3's CALIBRATION REGIME block and AMENDMENT-13 state the same vanishing-denominator argument
   twice at length; §6.3 explains why its totals changed; §3.2 carries the τ history. The
   *conclusions* are load-bearing; the *refutations of drafts no one will ever read* belong in the
   ledger entry that already records them. One clause plus a pointer would do.

That lands ~600 lines — still 2× budget, which I would accept and would not push further: five
controls, a HARD tripwire with a derived threshold, a ten-instrument census, a five-symbol floor table
and four golden traces do not compress into 300 lines without deleting the evidence that makes the
design checkable.

**This is a recommendation for the next design, not a condition of approval.** Nothing above changes
the verdict, and I would not delay execution to reformat the document — the archaeology is harmless
where it sits, merely misplaced.

---

## QA run 4 — 2026-07-21T23:30Z — mode: subagent — HEAD `797f926973d610bc3b6d870219f90617f245fa26`

**Stage:** DESIGN-ONLY re-review after **D6 four-pair rewrite + operator option A** (AMENDMENT-18…20).
`screen_code/` still absent; `xen.sigbar.absorb` still absent. Scope = **design-fidelity + governance**
against ckpt-015 §D6, INFR-020 (QA-APPROVED run 5), SPDR integrity boundary, and design-requirements.
**Not** a design-to-code trace.

**Verdict: REVISE**
**FAILING_ARTIFACT:** `python/experiments/SPDR-009/design.md`
**REQUIRED_SKILL:** `quant-designer` (incomplete D6 propagation into claimed pair-invariant integrity /
report clauses)

**Dirty tree at review time (same frame as prior runs):** committed HEAD `797f926…`; working changes
under review are `python/experiments/SPDR-009/` (design + `design_derivations/` + this file) and peer
INFR-020 design apparatus. No live `git status` in this tooling.

**Sources re-read for this run:** live `SPDR-009/design.md` (full); ckpt-015 §D6; INFR-020 `design.md`
§0–§1.1, W2a COMPLETE withdrawal, §5 universe retention table + activity conditioning; INFR-020
QA run 5 APPROVE; `diag_census.json` (all 20 rows); `diag_census.py` / `diag_pool.py` / `diag_grid.py`
headers + outcome-path greps; SPDR lane integrity boundary; design-requirements §1–§13 checklist;
prior SPDR-009 QA runs 1–3 (history only — every critical claim re-derived).

---

### A. Critical-check matrix (re-derived; prose not trusted)

| # | Check | Evidence | Verdict |
|---|---|---|---|
| 1 | D6.2 four pairs present; D6.3 1m invariant restated + code-asserted | §0 Domain pairs D1–D4; §0 D6.3 quote; §3.1 `assert_levels_from_1m`; §3.4 1m-path `ret_bps`/MFE/MAE; GT-5(j) | **PASS** |
| 2 | §6.3 ~194 event projection withdrawn; usable ~72/47/31; D1 19/313 | Withdrawn block present; table matches INFR-020 §5 (0.387/0.202/0.089 → 72/47/31); census totals re-summed from printed rows **and** `diag_census.json` → P=313 S9=19 MIRROR=31 BASE=263 P_WIDE=727/50/36 | **PASS** |
| 3 | Option A activity conditioning not a silent filter | §0 ACTIVITY CONDITIONING; §6.3 disposition consequence "Every D2/D3/D4 disposition states activity conditioning" | **PASS** |
| 4 | Zone = prior HTF session range; τ count-only/pair; D1 ib_width sensitivity | §3.2 primary scale + τ freeze + `zone_scale_census_d1_ibwidth` sensitivity | **PASS** (see I-4 on §5 τ=0.10 orphan) |
| 5 | Multiplicity 4×2×2=16; pair leading; no pair-pooled headline | §3.2, §4.1 | **PASS** |
| 6 | Null at D1 alone cannot close family | §6.3 DISPOSITION CONSEQUENCE; AMENDMENT-20; aligns D6.5 | **PASS** |
| 7 | Entry next LTF; outcomes 1m path; holds scale with LTF | §2, §3.4 wall-clock table D1–D4 | **PASS** |
| 8 | Cost floor: fee hold-invariant; per-pair `hold_hours` | §6.1 fee 11.0; D1–D4 hold_hours 10/60…10.0; funding scales | **PASS** |
| 9 | COMPLETE-window shared predicate; import INFR-020; no zero-fill | §3.2 `absorb_candidate_predicate()` COMPLETE-window; §9 "no reimplementation"; GT-5(l); zero-fill withdrawn language | **PASS** |
| 10 | GT-1…4 D1-valid; GT-5 (j)(k)(l) | §8 last paragraph + GT-5 (j)(k)(l) present | **PASS** |
| 11 | Mandatory design-requirement blocks; L-23 count | MECHANISM, OBJECT-IDENTITY, 5× CONTROL, TRIPWIRE+DERANGEMENT, bands, POWER, GT, HARD/INFORMATIVE, CONVERSION-PIN, SPREAD-SCALE, §10 ledger; running **1L/10T/9N** arithmetic checks (A-18 L → A-19 N → A-20 T) | **PASS** (substance); incomplete D6 lines in §7 listed as issues |
| 12 | No outcome in count-only derivations | `diag_census.py` header + body: counts only; `diag_pool`/`diag_grid` count-only; `gt_derive` outcomes only for pinned GTs (AMENDMENT-10 discipline) | **PASS** |

---

### B. Design-fidelity trace (D6 rewrite clauses)

| Design clause (§ref) | Expected (from D6 / option A / INFR-020) | Design text | Verdict | Notes |
|---|---|---|---|---|
| D6.2 four pairs | 1d/1m, 1h/5m, 4h/15m, 1d/1h one frozen design | §0 | **MATCHES** | |
| D6.3 1m path + levels | outcomes + profiles on 1m | §0, §3.1, §3.4, GT-5(j) | **MATCHES** | |
| D6.4 IB rule | 15m wall-clock; D4 min 1×1h DEVIATES | §3.1 table | **MATCHES** | §2 matches; **§7 does not** — I-1 |
| D6.4 zone scale | prior HTF session range; τ count-only; D1 0.25×ib_width sensitivity | §3.2 | **MATCHES** | |
| D6.5 / family close | null at D1 alone insufficient | §6.3 + AMENDMENT-20 | **MATCHES** | |
| Option A universe | keep 4 pairs; ~194/72/47/31; activity condition dispositions | §0, §6.3 | **MATCHES** | numbers = INFR-020 measured table |
| Shared predicate | import COMPLETE-window predicate; zero-fill withdrawn | §3.2, §9, GT-5(l) | **MATCHES** | |
| Entry / holds | next LTF open; H in LTF bars; wall-clock H×LTF | §2, §3.4 | **MATCHES** | |
| Multiplicity / strata | 16 cells; pair leading; no pair headline pool | §3.2, §4.1 | **MATCHES** | |
| Fee / floor | fee invariant; hold_hours per pair | §6.1 | **MATCHES** | |
| T3 mid-range scale | should be coherent with D6 zone scale | T3 still `1.0 × ib_width` only | **DEVIATES** | I-3 |
| ret_norm unit pin | single divisor object | §3.4 prior-session-range vs §6.1 IB A-USOPEN | **DEVIATES** | I-2 |
| §7 IB causal fence | refuse before IB complete **per pair** | still `before anchor+15` | **DEVIATES** | I-1 **MAJOR** |
| Pair-invariant carry claim | header lists §2 as carried unchanged | AMENDMENT-19 rewrote §2; content shows D2–D4 | **WORDING** | I-5 |

Mechanism / arms / controls / tripwire / bands / D1 GTs (pair-invariant body): no new integrity
defect found beyond the incomplete-propagation items above. Prior runs 1–3 APPROVE content on those
blocks still holds.

---

### C. Golden-trace diff (design-stage)

| Event | Expected from design rules | Design §8 / notes | Verdict |
|---|---|---|---|
| GT-1…GT-4 | D1-only; entry next 1m; arm labels S9/MIRROR/BASE; prior-session levels | Stated D1-only; D2–D4 GT deferred to INFR-020 fixtures | **PASS (D1)** |
| GT-5(a–i) | prior HARD fences | retained | **PASS** |
| GT-5(j)(k)(l) | D6.3 LTF-path ban; A-H1/A-H4 non-edge; COMPLETE only | present | **PASS** |
| Implementation GT for D2–D4 | not designer-pinned (baselines absent until INFR-020 runs) | declared | **ACCEPTABLE** for design-only |

---

### D. Governance & boundary checklist

| Item | Evidence | Verdict |
|---|---|---|
| SPDR TRAIN-only / 0 reads / no tradability | §0 band + counted reads 0/0; disposition-only language | **OK** |
| Causal t−1 / entry next bar | §2, §3.4; **D4 IB fence broken in §7** | **DEFECT I-1** |
| Matched controls + derangement L-28 | §4.2 destroy form DERANGEMENT; path-swap derangement | **OK** |
| Per-stratum + multiplicity disclosed | 16 cells; pair leading | **OK** |
| No local accounting / SPDR N/A Nautilus | §0 applicability | **OK** |
| Block ≥ H | §6.4 5-day blocks ≫ D4 10h | **OK** |
| CONVERSION-PIN (L-21) | §6.1; estimand already bps; floor from pin | **OK** (ret_norm disclosure dual-defined — I-2) |
| SPREAD-SCALE-ROUTING | §6.2 | **OK** |
| L-23 amendment ledger | 1L/10T/9N; A-18 single LOOSER (D6 widen); no LOOSER streak ≥3; A-19 NEUTRAL / A-20 TIGHTER defensible | **OK** |
| L-24 F02/F04/F06; F07 N/A | §0 + controls + CF* derivation | **OK** |
| XENA VOID / no counted TEST | no XENA route; TEST never | **OK** |
| INFR-020 prerequisite gate | header + §9 execution order step 1 | **OK** |
| design-requirements blocks | all mandatory present | **OK** |
| Outcome ban on freeze-path census | diag_* count-only | **OK** |

---

### E. Issues

**I-1 — MAJOR — §7 HARD still refuses IB-edge events only before `anchor+15`, which is false for D4.**

- **§:** §7 HARD causal line vs §2 / §3.1 / GT-5(e) / D6.4
- **Defect:** §2 correctly states IB complete at +15 (D1–D3) and **+60 (D4)**. GT-5(e) correctly says
  "before IB wall-clock completes **for that pair**". §7 HARD still says `IB-edge events before
  anchor+15 REFUSED`. On D4, IB is not knowable until anchor+60; a developer implementing the HARD
  list literally would **admit IB_HIGH/IB_LOW events in (anchor+15, anchor+60)** — a causality leak
  (levels not yet fixed).
- **Required change:** rewrite the §7 HARD causal IB fence to the same per-pair rule as §2/GT-5(e)
  (`before IB wall-clock completes for that pair` / D4 = anchor+60). Do not leave HARD text at D1-only
  wall-clock.

**I-2 — MEDIUM — `ret_norm` has two contradictory divisor objects.**

- **§:** §3.4 vs §6.1 CONVERSION-PIN
- **Defect:** §3.4 defines `ret_norm = ret_bps / prior_htf_session_range_bps`. §6.1 still pins the
  disclosure divisor as *"this session's IB high − IB low … frozen anchor A-USOPEN L=15"*. Under D6
  those are different objects (and A-USOPEN L=15 is D1-only).
- **Required change:** one authoritative divisor. Prefer §3.4 (prior HTF session range, pair-native)
  and rewrite §6.1's disclosure pin to match; or explicitly demote `ret_norm` to D1-only continuity
  with the IB pin and drop the §3.4 range formula.

**I-3 — MEDIUM — T3 mid-range distance still hard-coded to `1.0 × ib_width` with no D6 statement.**

- **§:** §4 T3 (claimed pair-invariant carry) vs D6.4 zone scale
- **Defect:** Contact zone is now `τ_pair × prior_htf_session_range`. Soil leg (i) still requires
  T3 ≈ 0 on "no level within `1.0 × ib_width`". At D2 IB is 25% of the hour; at D3/D4 IB is a single
  LTF bar. That mid-range neighborhood is no longer a fixed multiple of the contact zone and is not
  declared as intentional.
- **Required change:** define mid-range per pair (e.g. `1.0 × prior_htf_session_range`, or
  `k × zone_scale`, or retain ib_width **with an explicit reason and pair caveats**). State that T3 is
  pair-stratum and not cross-pair comparable if scales differ.

**I-4 — MEDIUM — §5 still mandates a `τ = 0.10` sensitivity that D6 no longer registers cleanly.**

- **§:** §5 zone-dilution paragraph vs §3.2 / AMENDMENT-11 / AMENDMENT-18(d)
- **Defect:** Pre-D6: primary `0.25×ib_width`, sensitivity `τ=0.10`. D6: primary = prior-session-range
  × τ_pair (count-frozen); D1 sensitivity = **retain `0.25×ib_width`** (former primary). §5 still says
  "the τ = 0.10 sensitivity read is reported beside" every null. P_WIDE is "tighter τ (count-frozen)"
  without equating it to 0.10 on which scale.
- **Required change:** rewrite §5 zone-dilution to name the D6 sensitivities exactly (per-pair
  count-frozen tighter τ / P_WIDE; D1 `0.25×ib_width` census). Drop or re-pin `τ=0.10` with scale.

**I-5 — LOW — header "pair-invariant" inventory is wrong about §2 (and partially §4.1).**

- **§:** design header Revision line vs AMENDMENT-19
- **Defect:** Header claims §2 object identity carried unchanged; AMENDMENT-19 lists §2 entry/IB/
  refractory as rewritten (correct — content has D2–D4). §4.1 also rewritten while §4 is listed as
  invariant. Misleads the next reviewer about what must be re-checked.
- **Required change:** correct the carry-over list (pair-dependent: §0, §2 IB/entry, §3.1–3.2, §3.4,
  §4.1, §6.1 floors, §6.3, §9; pair-invariant: mechanism core, §3.3 arms, T1–T5 *structure*, controls,
  tripwire, bands, §7 *after I-1 fix*, D1 GTs).

**I-6 — LOW — §7 HARD omits COMPLETE-window and D6.3 1m-path lines that GT-5 already requires.**

- **§:** §7 vs GT-5(j)(l) / §0 Must-NOT
- **Defect:** Not a contradiction if GT-5 is treated as authoritative, but HARD is what implementers
  and tripwire reviews cite first. Missing: non-COMPLETE candidate ban; outcome/level path must be 1m.
- **Required change:** add both as HARD bullets (mirror GT-5(j)(l)).

**I-7 — LOW — residual D1-only wording in §6.3 UNPOWERED list.**

- **§:** §6.3 "every per-symbol … cell on pool P (either pair)"
- **Required change:** "any pair" (four pairs).

---

### F. What this run affirms (not issues)

- Operator option A is implemented honestly: all four pairs kept; usable floors ~194/72/47/31 from
  INFR-020 measurement; activity conditioning required on D2–D4 dispositions; instruments below floor
  liquidity-limited, never signed-negative.
- Old ~194-everywhere event-power projection is explicitly **withdrawn**; D2–D4 event counts not
  invented; `power_census` at run before contrasts.
- D1 census 19/313 and all table cells still reproduce from `diag_census.json`; count-only discipline
  intact.
- Family-close rule correctly tightened (AMENDMENT-20): D1 null alone cannot close CF-SIGAUC-001.
- COMPLETE-window / zero-fill withdrawal correctly imported from INFR-020 (design-level).
- L-23: single LOOSER (A-18 D6 widen); no LOOSER streak; A-19 NEUTRAL / A-20 TIGHTER acceptable.
- No REJECT-class defect: no holdout/TEST contact, no missing tripwire, no unapproved silent deviation,
  no outcome-informed τ freeze path in cited census scripts.

---

### G. Post-implementation trace additions (when code exists; not blocking this design revise)

| # | Clause | Trace |
|---|---|---|
| R22 | §7 / GT-5(e) after I-1 | IB-edge refuse uses **pair IB wall-clock** (D4=60m); no D1-only +15 constant in production path |
| R23 | §3.2 / INFR-020 | `absorb_candidate_predicate` **imported**; candidates with `window_class ≠ COMPLETE` raise; no local zero-fill |
| R24 | §3.4 / D6.3 | `ret_bps` / MFE/MAE from **1m opens/prices** on all four pairs; LTF used only for detection + entry schedule |
| R25 | §4.1 | no headline contrast pools across pairs; 16 primary cells emitted |
| R26 | §6.3 option A | `universe_membership` + disposition text carry activity-conditioning ratios from coverage_report |
| R27 | §6.1 | `floor_table.json` per pair with fee invariant + hold_hours-scaled funding |

Run-1 R1–R12 and run-2/3 R14–R21 still stand for the pair-invariant implementation body.

---

### H. Verdict

**REVISE** — route to **quant-designer**.

D6 + option A are largely correct and honest on the pair-dependent spine (§0, §3.1–3.2, §3.4, §4.1,
§6.1, §6.3, §9, AMENDMENT-18…20). The rewrite is **not yet frozen-safe** because the HARD integrity
block (§7) still encodes the **D1-only IB clock**, which is a causality defect on D4 if followed, and
because two report-layer unit definitions (ret_norm, T3 mid-range, §5 τ sensitivity) were left on the
old scale while the event geometry moved.

**Close for APPROVE when:** I-1 fixed in §7; I-2 and I-3 resolved with one scale each; I-4 §5
sensitivity text aligned to §3.2. I-5…I-7 may ship with those fixes.

**Still blocked on execution until:** INFR-020 implements (design already QA-APPROVED run 5) **and**
this design re-QA APPROVE **and** operator execution gate. This run does not restore the suspended
1d/1m execution approval.

---

## QA run 5 — 2026-07-21T24:00Z — mode: subagent — HEAD `797f926973d610bc3b6d870219f90617f245fa26`

**Stage:** DESIGN-ONLY re-review after **AMENDMENT-21** (QA-4 residual fixes I-1…I-7).
`screen_code/` still absent; `xen.sigbar.absorb` still absent. Scope = verify each QA-4 residual is
closed in live `design.md`, plus no regression on D6 option A spine. **Not** a design-to-code trace.

**Verdict: APPROVE**

All seven QA-4 residuals are independently closed. No fix introduced a new defect. D6 option A spine
(four pairs, usable floors, activity conditioning, family-close rule) is intact. Design is ready for
the operator's execution gate **after** INFR-020 implements. **QA APPROVE does not launch anything.**

**Dirty tree:** same frame as prior runs — committed HEAD `797f926…`; working changes under review
are `python/experiments/SPDR-009/` (design + `design_derivations/` + this file). No live `git status`
in this tooling.

**Sources re-read:** live `SPDR-009/design.md` (full; focus §0 header, §2, §3.4, §4 T3, §5 zone text,
§6.1, §6.3 UNPOWERED, §7 HARD, §8 GT-5, §10 A-21); QA run 4 issue text (I-1…I-7) as checklist only —
every claim re-derived from design text.

---

### A. Disposition of QA-4 residuals (I-1…I-7)

| Residual | Required change | Evidence in live design | Verdict |
|---|---|---|---|
| **I-1 MAJOR** §7 HARD IB fence D1-only +15 | Per-pair wall-clock; D4 = anchor+60 | §7 HARD: *"IB-edge events before IB wall-clock completes **for that pair** REFUSED (D1–D3: anchor+15 min; **D4: anchor+60 min** — not a universal +15)"*. Aligns §2 (D1–D3 +15m / D4 +60m), §3.1 IB table, GT-5(e). Grep: no residual HARD-only `before anchor+15` without per-pair scope | **CLOSED** |
| **I-2 MEDIUM** ret_norm dual divisor | One authoritative divisor | §3.4: `ret_bps / prior_htf_session_range_bps` (not IB width; §6.1 pin matches). §6.1: disclosure divisor = **prior HTF session range in bps of entry**; IB-width **not** used for `ret_norm` under D6; optional D1-only continuity column `ret_norm_ib_d1_only` never mixed with `ret_norm`. No A-USOPEN L=15 IB pin on `ret_norm` remains | **CLOSED** |
| **I-3 MEDIUM** T3 still `1.0 × ib_width` | Mid-range on D6 scale family | §4 T3: no level within **`1.0 × prior_htf_session_range`** (same scale family as contact zone, not ib_width); per-pair stratum; not cross-pair comparable. Soil leg (i) still requires T3 ≈ 0 — now on coherent scale | **CLOSED** |
| **I-4 MEDIUM** §5 τ=0.10 orphan | Sensitivities = P_WIDE + D1 ib_width; withdraw 0.10 as named | §5 zone-dilution: (1) **P_WIDE** p25 + tighter τ_pair on prior-session-range scale; (2) **D1 only** `0.25 × ib_width` census. *"Pre-D6 `τ = 0.10 × ib_width` is **withdrawn as a named sensitivity**"*. Historical AMENDMENT-11 ledger text still mentions 0.10 (history only — not binding) | **CLOSED** |
| **I-5 LOW** header pair-invariant list wrong | Correct carry / rewrite inventory | Header Revision: **Pair-invariant:** §1 mechanism core, §3.3 arms, T1–T5 *structure*, §4.2 controls, §4.3 tripwire, §5 band *labels*, §8 D1 GTs. **Pair-dependent:** §0, §1 DERIVED horizon, §2, §3.1–3.2, §3.4, §4.1, §4 T3 mid-range scale, §5 zone-sensitivity text, §6.1, §6.3, §7 HARD IB/COMPLETE/1m fences, §9. Matches AMENDMENT-19/21 content | **CLOSED** |
| **I-6 LOW** §7 HARD missing COMPLETE + D6.3 | Add HARD bullets mirroring GT-5(j)(l) | §7 HARD: *"D6.3: any outcome path … or level/profile construction that consumes LTF bars instead of 1-minute bars raises"*; *"COMPLETE-window only: candidate / event with `window_class ≠ COMPLETE` raises"*. Also A-H1/A-H4 non-edge HARD (GT-5(k) companion). GT-5(j)(k)(l) remain | **CLOSED** |
| **I-7 LOW** "either pair" | "any of the four pairs" | §6.3 UNPOWERED: *"every per-symbol … cell on pool P (**any** of the four pairs)"*. Grep: no residual "either pair" outside A-21 ledger history | **CLOSED** |

---

### B. Spot-check — D6 option A spine (no regression)

| Check | Evidence | Verdict |
|---|---|---|
| Four pairs D1–D4 one frozen design | §0 Domain pairs; multiplicity 4×2×2=16 | **PASS** |
| Usable floors ~194 / 72 / 47 / 31 | §0 universe; §6.3 table; option A 0.50 retention | **PASS** |
| Activity conditioning on D2–D4 dispositions | §0 ACTIVITY CONDITIONING; §6.3 disposition consequence | **PASS** |
| ~194-everywhere projection withdrawn; D2–D4 counts not invented | §6.3 withdrawn block; power_census at run | **PASS** |
| Family close needs all four pairs (or operator scope) | §6.3 DISPOSITION CONSEQUENCE; AMENDMENT-20 | **PASS** |
| D6.3 1m path for outcomes + levels | §0, §3.1, §3.4, §7 HARD, GT-5(j) | **PASS** |
| Zone = prior HTF session range; τ count-only; D1 ib_width sensitivity | §3.2; §5 aligned (I-4) | **PASS** |
| Fee hold-invariant; per-pair hold_hours / funding | §6.1 | **PASS** |
| Pair leading stratum; no pair-pooled headline | §4.1 | **PASS** |
| INFR-020 prerequisite; execution suspended until pins | header + §9 step 1 | **PASS** |

---

### C. Design-fidelity trace (AMENDMENT-21 clauses only)

| Design clause (§ref) | Code (file:line) | Verdict | Notes |
|---|---|---|---|
| §7 HARD IB per-pair wall-clock | design-stage only | **MATCHES** | D4 +60 explicit; not universal +15 |
| §3.4 + §6.1 ret_norm unified | design-stage only | **MATCHES** | prior HTF session range; D1 IB diagnostic demoted |
| §4 T3 mid-range scale | design-stage only | **MATCHES** | `1.0 × prior_htf_session_range` |
| §5 zone sensitivities | design-stage only | **MATCHES** | P_WIDE + D1 ib_width; 0.10 withdrawn |
| Header pair inventory | design-stage only | **MATCHES** | §2/§4.1/T3/§7 correctly pair-dependent |
| §7 HARD COMPLETE + D6.3 | design-stage only | **MATCHES** | both bullets present |
| §6.3 "any of the four pairs" | design-stage only | **MATCHES** | |

---

### D. Golden-trace diff

| Event | Expected | Design | Verdict |
|---|---|---|---|
| GT-1…GT-4 | D1-only; unchanged by A-21 | Still D1-only; A-21 does not touch §8 numeric traces | **PASS (unchanged)** |
| GT-5(e) | IB wall-clock for that pair | present | **PASS** |
| GT-5(j)(k)(l) | D6.3 / A-H non-edge / COMPLETE | present; now mirrored in §7 HARD | **PASS** |

---

### E. Governance & boundary

| Item | Evidence | Verdict |
|---|---|---|
| SPDR TRAIN-only / 0 reads / no tradability | §0 | **OK** |
| Causal t−1 / IB complete per pair | §2 + §7 HARD (I-1 closed) | **OK** |
| L-28 derangement | §4.2 / §4.3 | **OK** |
| CONVERSION-PIN / ret_norm single disclosure object | §6.1 (I-2 closed) | **OK** |
| SPREAD-SCALE-ROUTING | §6.2 | **OK** |
| L-23 amendment ledger | A-21 TIGHTER; running **1L/11T/9N**; single LOOSER still A-18; no LOOSER streak ≥3 | **OK** — arithmetic 1L/10T/9N → 1L/11T/9N correct; A-21 TIGHTER defensible (I-1 causality fence) |
| L-24 F02/F04/F06; F07 N/A | unchanged from run 3/4 | **OK** |
| XENA VOID / no TEST/holdout | §0 | **OK** |
| design-requirements blocks | all present | **OK** |
| No REJECT-class defect | no holdout/TEST contact; no missing tripwire; no silent LOOSER | **OK** |

---

### F. Issues

**None open from QA-4 I-1…I-7.**

No new residual issues found on re-read of the amended clauses. Non-blocking notes (not numbered issues):

- **Execution still blocked** until INFR-020 implements (pins hashed) **and** operator execution gate. This APPROVE restores design readiness after D6 suspension; it does not implement or launch.
- Post-implementation trace items R1–R27 from runs 1–4 still stand when code exists (especially R22 IB pair wall-clock; R23 COMPLETE predicate; R24 1m path).
- AMENDMENT-11 historical text still describes pre-D6 τ=0.10 sensitivity; binding text is §3.2 / §5 / A-18(d) / A-21. Ledger history should not be rewritten.

---

### G. Verdict

**APPROVE.**

QA-4's blocking set is closed: the HARD IB fence is per-pair (D4 = +60), report-layer scales (ret_norm, T3, §5 sensitivities) sit on the D6 prior-session-range family, header inventory matches the rewrite, and COMPLETE/D6.3 integrity lines are in HARD. Option A four-pair spine and family-close tightening are unchanged.

**Still required before any run:** INFR-020 implementation + pins; then developer implementation of `xen.sigbar.absorb` + screen runner; post-implementation QA (design-to-code); operator execution gate.

---

## QA run 6 — 2026-07-22 — mode: subagent — HEAD `99f1a5537f9f37ca459d07f7f0a0bdf8a89e9807`

**Stage:** post-implementation design-to-code QA (pre-execution). Real SPDR-009 screen **not** executed (`--execute` not run). Fresh-context subagent; did not author the implementation.

**Verdict: REVISE**
**FAILING_ARTIFACT:** `python/src/xen/sigbar/absorb.py` + `python/experiments/SPDR-009/screen_code/absorb_screen.py`
**REQUIRED_SKILL:** `experiment-developer`

**Dirty tree (implementation under review; git status not re-run in this tooling):**
- `python/src/xen/sigbar/absorb.py` (NEW shared module)
- `python/experiments/SPDR-009/screen_code/absorb_screen.py` (NEW runner)
- `python/tests/test_sigbar_absorb.py` (NEW tests)
- prior design / `design_derivations/` / this append-only file

**Sources read:** live `design.md` §§0,1–9 + A-22/23/24; `gt_output.json`; `absorb.py` full; `absorb_screen.py` full; `test_sigbar_absorb.py` full; shared `ltf.py` helpers (import surface + COMPLETE/`formed_ts`); `fences.py` band/load; INFR-020 `pins.json` + report freeze line; INFR-018 registry `pin_sha256`; INFR-017 `column_pins.json` pin; SOL cuts in `class_thresholds_1m.json`; governance-constraints + skill protocol. QA runs 1–5 used as history only.

**Developer claims checked independently (not trusted):**
- Shared LTF imports, no local redefinition — **PASS** (source scan + import surface).
- Frozen re-hash at entry — **PASS** (contract constants + on-disk pin fields align; runtime path present).
- COMPLETE / causal next-LTF entry / 1m outcomes / DESIGN·CONFIRM only — **PASS** on core event/outcome path.
- Fixed-H path-swap (not raw spine) + bite in bps of entry — **PASS** as primitives; runner tripwire incomplete (see Issues).
- No local accounting / no real screen execution in this QA — **PASS**.
- Tests: 23 functions; GT parametrize ×4 ⇒ **26** absorb cases as claimed — structure verified; suite not re-executed here (no shell). Full-suite 256 claim **not re-run**.
- DEVIATIONS block: **none recorded** — matches (none found as approved silent deviation file).

---

### A. Independent pin re-hash (contract consistency)

| Pin | Contracted | Evidence this run | Verdict |
|---|---|---|---|
| INFR-020 `pins.json` | `5f170b717e350fb7c0cf1647cd1b78fb88a1fa212ed50dce83ec1049af44f6c5` | `absorb.INFR020_PINS_SHA256`; INFR-020 report operator freeze line | **MATCH** (constant↔report; runtime re-hashes file) |
| `seasonal_baselines_mtf.parquet` | `86c81937cbee…38a12c1` | design §0 = `pins.json.artifacts` = absorb dict; file **present** under INFR-020/results | **MATCH** (contract; full byte re-hash delegated to `assert_spdr009_frozen_inputs` / test) |
| `class_thresholds_1m.json` | `dee853ad…e9fc` | same three-way agreement | **MATCH** |
| `class_thresholds_mtf.json` | `745fb435…3ae7` | same | **MATCH** |
| `sessions_mtf.json` | `c55cd880…62df` | same | **MATCH** |
| `zone_scale_census.json` | `f64e0d22…7f1e` | same | **MATCH** |
| `zone_scale_census_d1_ibwidth.json` | `76c3d4b5…5f0c` | same | **MATCH** |
| `coverage_report.json` | `68dac757…3a424` | same | **MATCH** |
| INFR-017 baselines | `1b7244c8…` | `fences.BASELINES_SHA256`; pins.json frozen_inputs; file present | **MATCH** |
| INFR-017 column_pins | `e3b9fd9b…` | `column_pins.json` field `pin_sha256` exact | **MATCH** |
| Catalog fence | `35d3375e…` | fences constant + pins.json frozen_inputs | **MATCH** (constant; not re-streamed as a file here) |
| INFR-018 registry | `5c386984…` | registry `pin_sha256` exact at EOF | **MATCH** |

Nine INFR-020 artifact rows in `pins.json` (battery + gap + seven consumers) agree with the INFR-020 report table. SPDR consumer re-verifies the seven design-§0 consumers + the pins.json envelope (not battery/gap) — acceptable for this item’s consumption surface.

---

### B. Golden-trace re-derivation (from design §8 / `gt_output.json`, not impl fixtures)

SOLUSDT cuts from frozen `class_thresholds_1m.json` (independent read):  
`volume.high=5.34397`, `range.low=−0.899321`, `delta_abs.high=4.85461`, `delta_ratio.abs_high=1.37780` — matches design GT-4 pin text.

| Event | Design / gt_output | Arm rule re-check | ret H5 / H10 | Verdict |
|---|---|---|---|---|
| **GT-1** 2022-12-28 03:27 IB_LOW | into=−1; dr=−1.5016 ⇒ signed=+1.5016; da=9.88 ≥ d_hi; signed ≥ dr_hi | **S9** · side LONG · entry 03:28 / 10.770 | −4.6425 / −9.2851 | **PASS** (design ≡ gt_output) |
| **GT-2** 2022-12-29 01:24 PRIOR_SESSION_LOW | into=−1; signed=+1.5397; da huge | **S9** · LONG · entry 01:25 / 9.725 | +15.4242 / −5.1414 | **PASS** |
| **GT-3** 2022-12-26 23:34 PRIOR_VAL | into=+1; dr=−1.382 ⇒ signed=−1.382 ≤ −dr_hi; da huge | **MIRROR** (not S9) · SHORT | −35.5240 / −26.6430 | **PASS** (sign guard) |
| **GT-4** 2022-11-12 22:08 IB_LOW | into=−1; dr=+1.2096 ⇒ signed=−1.2096; \|signed\| < 1.3778; da=26.0 ≥ d_hi | **BASE** (magnitude without extreme direction) | −43.4783 / −40.1338 | **PASS** |
| **GT-5** raise set | band / freeze / hash / per-level Δ / IB wall-clock / derange FP / S1 / D6.3 / A-H non-edge / COMPLETE | Unit tests cover most; **e,f,i** not dedicated (see Issues) | — | **PARTIAL** |

Implementation arm primitive `_arm_label` and into_side match §3.3 / §3.2. Tests assert GT rows against designer-pinned `gt_output.json` under D1 `ib_width` τ=0.25 (continuity zone) — correct source of expectation.

---

### C. Design-fidelity trace

| Design clause (§ref) | Code (file:line) | Verdict | Notes |
|---|---|---|---|
| §0 frozen re-hash every entry | `absorb.py:177–242` | **MATCHES** | INFR-017 + registry + pins.json + 7 consumers |
| §0 four pairs D1–D4 | `absorb.py:125–158` | **MATCHES** | D4 IB wall=60 disclosed |
| §0 D6.3 1m outcomes/levels | `absorb.py:282–288, 496, 557–563, 765–858` | **MATCHES** | `assert_no_ltf_outcome_path`; levels via `structural_levels_1m` on 1m |
| §0 DESIGN/CONFIRM only; no TEST | `absorb.py:485–486`; `fences.load_bars` band window | **MATCHES** | TEST/holdout not in `BANDS` |
| §0 no local accounting | screen calls `check_no_local_accounting`; no banned defs | **MATCHES** |
| §0 no S1 qualifier | `refuse_s1_as_qualifier` | **MATCHES** (explicit raise helper) |
| §0 A-H non-edge | `assert_not_edge_bearing_operational`; D2/D3 `edge_bearing_anchor=False` | **MATCHES** (path never sets as_edge=True for A-H*) |
| §3.1 shared level/session/availability | imports `structural_levels_1m`, `assign_candidate_sessions`, `available_levels_for_candidates` | **MATCHES** | not redefined in absorb |
| §3.1 formed_ts mandatory | enforced in shared `available_levels_for_candidates` | **MATCHES** (via import) |
| §3.2 COMPLETE-window candidates | `ltf_complete_bars` + fence on non-COMPLETE rows + `absorb_candidate_predicate(..., require_complete=True)` | **MATCHES** | GT-5(l) raise is partial (filter + traded_fraction raise) |
| §3.2 effort / no-result / zone / into_side | `build_contact_events` | **MATCHES** for pool P | |
| §3.2 consecutive same-level → first | `absorb.py:732–734` | **DEVIATES** | Comment only; sort/return — no collapse (refractory partially substitutes) |
| §3.2 P_WIDE p25 + tighter τ | partial `pool_mode` + threshold override | **MISSING** in runner | No P_WIDE τ freeze; execute path never builds P_WIDE |
| §3.2 τ count-only freeze | `absorb_screen.step_pool_cuts` | **MATCHES** (intent) | Sample-heuristic MIN_POOL_EVENTS=30 on ≤20 symbols — disclose, not integrity fail |
| §3.3 three arms | `_arm_label` | **MATCHES** on located pool | |
| §3.3 MID_RANGE arm (T3 habitat) | `absorb.py:601–656` | **DEVIATES (MAJOR)** | `into = sign(dr)`; `signed = into*dr` ⇒ always \|dr\|; **MIRROR unreachable** |
| §3.4 entry next LTF open; side=−into | `entry_ts = OpenTime + ltf`; `side: -into` | **MATCHES** | |
| §3.4 ret_bps / MFE/MAE 1m path | `evaluate_outcomes_1m` | **MATCHES** | open-to-open; path after entry; contiguity drop |
| §3.4 session-remainder secondary | — | **MISSING** | not emitted |
| §3.4 ret_norm prior-session-range | `evaluate_outcomes_1m:846–851` | **MATCHES** when zone_mode=prior_session_range | ib_width path leaves ret_norm null |
| §2 refractory 10 LTF | `apply_refractory` | **MATCHES** | |
| §4 T1 S9−BASE + mirror companion | `contrast_day_clustered` + screen layers | **PARTIAL** | Primitive OK; **day contrast uses global base mean**, not same-day arm contrast |
| §4 T2 Spearman + ≥2000 derange | `spearman_finite` + `derange_scores_global`; screen seeds 2000 | **MATCHES** structure | within-symbol second null not in runner |
| §4 T3 mid-range | pool_mode MID_RANGE exists; **not in runner** | **MISSING / DEVIATES** | broken arm math if used |
| §4 T4 matched random | `matched_random_timing` primitive | **MISSING** in runner | GT-5(i) raise present in primitive |
| §4 T5 bare level touch | — | **MISSING** | no primitive |
| §4.2 MDE plant curves before read | — | **MISSING** | no plant / `mde_curves` artifact |
| §4.3 fixed-H path-swap + bite bps | `outcome_path_swap_fixed_h` + `path_swap_bite_bps` | **MATCHES** primitives | L-28 zero FP asserted |
| §4.3 CF* plant calibration + collapse survival | — | **MISSING** | runner only bite; no CF*, no collapse_fraction, no survival rule |
| §4.3 material-edge precondition | — | **MISSING** | not coded on tripwire path |
| §5 UNPOWERED-first labels | partial UNPOWERED flags on thin contrast | **PARTIAL** | no full band-label emission |
| §6.1 cost floor pin | `cost_floor_bps` + `bybit_round_trip_cost_bps` | **MATCHES** | SOL ~11.748 at H=10min in unit test design |
| §6.2 SPREAD-SCALE-ROUTING | — | **MISSING** in runner | |
| §6.3 usable universe option A | `usable_universe` from coverage_report | **MATCHES** | tests expect 194/72/31 |
| §6.3 power_census before contrast | screen order on `--execute` | **MATCHES** order | missing MDE curves step |
| §6.4 day-clustered block bootstrap | `block_bootstrap_ci` DAY_BLOCK=5 | **PARTIAL** | see T1 day-contrast note |
| §7 CONFIRM-before-freeze | `assert_confirm_freeze_ready` | **MATCHES** helper | CONFIRM band never run in runner |
| §7 IB per-pair wall-clock | `ib_minutes_for_pair` + raise in contact | **MATCHES** | D4=60 |
| §9 import boundary / no spine path-swap reuse | fixed-H in absorb; no `spine.outcome_path_swap` | **MATCHES** | |
| §9 execution order | prep freezes without outcomes; execute needs flag | **PARTIAL** | prep OK; execute incomplete vs T1–T5+tripwire+CONFIRM |

---

### D. Golden-trace diff (implementation logic vs design)

| Item | Expected (design) | Implemented | Verdict |
|---|---|---|---|
| GT-1…4 arms + signed_score construction | §8 + cuts | `_arm_label` / `_into_side` + residual path | **MATCHES** (logic); emission tested against pinned JSON |
| GT-1…4 returns open-to-open 1m | ret formula §3.4 | `evaluate_outcomes_1m` | **MATCHES** |
| GT-5a TEST/holdout | raise | `load_bars("TEST")` raises | **MATCHES** |
| GT-5b CONFIRM before freeze | raise | `assert_confirm_freeze_ready` | **MATCHES** |
| GT-5c hash mismatch | raise | monkeypatch registry pin | **MATCHES** |
| GT-5d per-level Δ | raise | fences helper | **MATCHES** |
| GT-5e IB before complete | raise | contact path raises | **MATCHES** logic; no dedicated test |
| GT-5f PRIOR_* current session | raise | shared `formed_ts` / availability | **MATCHES** via ltf; no absorb-level test |
| GT-5g derange FP | raise | trap.derange n=1 | **MATCHES** |
| GT-5h S1 | raise | `refuse_s1_as_qualifier` | **MATCHES** |
| GT-5i matched_random own session | raise | primitive raises | **MATCHES** logic; no unit test |
| GT-5j D6.3 LTF outcome | raise | `assert_no_ltf_outcome_path` | **MATCHES** |
| GT-5k A-H edge | raise | helper | **MATCHES** |
| GT-5l non-COMPLETE | raise | filter + traded_fraction raise; series fence | **PARTIAL** |

---

### E. Governance & boundary checklist

| Check | Evidence | Verdict |
|---|---|---|
| Holdout sealed; no final 30% | `HOLDOUT_START=2025-01-08`; bands only DESIGN/CONFIRM; `assert_band` | **OK** |
| Causal t−1 entry | next LTF open after detection close; IB availability via shared mins + fence | **OK** |
| COMPLETE-window only | complete_only aggregate + predicate + fence | **OK** |
| D6.3 1m path | outcomes and levels on 1m | **OK** |
| L-28 derangement (T2 + path-swap) | zero fixed points asserted | **OK** on primitives |
| No local accounting | `check_no_local_accounting(screen_code)`; no accounting defs in absorb | **OK** |
| SPDR TRAIN-only; 0 counted reads; no TEST | design + band fence; no registry TEST path | **OK** |
| No estimand-gated P&L / no BacktestNode | vectorised Python only | **OK** |
| Tripwire HARD future_destroy present as **complete adjudicator** | path-swap exists; **CF*/collapse/survival missing** | **REVISE** |
| CONVERSION-PIN L-21 | estimand already bps of entry | **OK** |
| SPREAD-SCALE-ROUTING declared in design; code | design yes; runner no | **REVISE** (report layer, not integrity) |
| Amendment ledger L-23 | 2L/13T/9N; no LOOSER streak ≥3 | **OK** (design) |
| XENA VOID N/A | SPDR screen | **OK** |
| Shared-code boundary | LTF helpers imported not reimplemented | **OK** |
| DEVIATIONS | none | **OK** |

---

### F. Issues

1. **MAJOR — MID_RANGE / T3 arm math broken**  
   **Design §:** §3.3 + §4 T3  
   **Where:** `absorb.py:624–627`  
   **Problem:** synthetic `into = sign(delta_ratio_resid)` makes `signed_score = |dr|` always ≥ 0, so MIRROR is impossible and S9 is not “aggression into a level.”  
   **Required:** define mid-range score without fabricating into_side from |dr| (e.g. use raw `delta_ratio_resid` as the continuous score with the same ±dr_hi split), and add a regression that MIRROR can fire.

2. **MAJOR — Screen execute path incomplete vs design battery**  
   **Design §:** §4 T1–T5, §4.2 controls, §5, §9 step 5–6  
   **Where:** `absorb_screen.py:step_design_reads` (~254–341)  
   **Problem:** only T1 / T1-mirror / T2 (+ thin tripwire). Missing T3, T4, T5, bare-level control wiring, matched-random wiring, within-symbol derangement disclosure, session-remainder secondary, CONFIRM once, floor-vs-arm absolute framing, spread-scale routing. Disposition cannot be formed from current layers alone.  
   **Required:** implement remaining report layers per pair (or explicitly scope a staged runner in design with operator approval — currently design requires full battery).

3. **MAJOR — Tripwire not design-complete**  
   **Design §:** §4.3 HARD  
   **Where:** `absorb_screen.py:313–337`; no CF* code in absorb  
   **Problem:** no additive-plant CF* calibration (1×/2×/3× MDE), no `collapse_fraction`, no material-edge precondition, no survival rule, no `results/tripwire.json` with seed set **before** real read. Bite alone is not the tripwire.  
   **Required:** implement fixed-H path-swap adjudication for T1/T2 exactly as §4.3.

4. **MAJOR — MDE plant curves not emitted before contrasts**  
   **Design §:** §4.2 bite/MDE; §6.3; §9 step 5  
   **Where:** runner has no `mde_curves` step  
   **Problem:** MDE must be published from plants at realised n before real T1/T2.  
   **Required:** plant grid → `results/mde_curves.json` after `power_census`, before DESIGN contrasts.

5. **MAJOR — P_WIDE stratum not frozen or read**  
   **Design §:** §3.2 secondary pool; multiplicity 4×2×2=16  
   **Where:** `step_pool_cuts` / `step_design_reads`  
   **Problem:** only pool P; P_WIDE p25 + tighter τ not count-frozen or executed.  
   **Required:** freeze P_WIDE cuts on counts only; emit separate stratum (never pool with P).

6. **MEDIUM — Day-clustered contrast uses global BASE mean**  
   **Design §:** §6.4 per-day arm contrast  
   **Where:** `absorb.py:1196–1200`  
   **Problem:** `day_contrast = treat_day_mean − overall_base_mean` is not a same-day arm contrast.  
   **Required:** form per-day (or day-clustered) S9−BASE contrast with the design’s stated resampling unit.

7. **MEDIUM — Consecutive same-level first-bar rule not implemented**  
   **Design §:** §3.2  
   **Where:** `absorb.py:732–734`  
   **Problem:** comment claims collapse; code only sorts. Refractory of 10 LTF bars partially overlaps but is not the same rule.  
   **Required:** implement first-bar-at-(symbol,pair,level_kind) collapse before refractory, or design amendment if refractory is accepted as substitute.

8. **LOW — GT-5(e)(f)(i) lack dedicated tests; GT-5(l) is filter-first**  
   **Design §:** §8 GT-5  
   **Required:** add raise-path tests for IB-before-complete, current-session PRIOR_*, matched-random own session; align COMPLETE “raises” wording with filter+fence behavior or raise on non-COMPLETE rows in the candidate series.

9. **LOW — D1 ib_width sensitivity / CONFIRM path not scheduled**  
   **Design §:** §3.2 / §5 / §9  
   **Required:** emit D1 `0.25×ib_width` census path; wire CONFIRM after freeze with one verify pass.

**Non-issues / verified good:** shared LTF boundary; frozen pin contracts; core pool-P event construction; arm three-way on located events; 1m outcomes; refractory primitive; fixed-H path-swap primitive + bps bite; cost floor pin; option-A universe sizes in unit tests; no local accounting; no TEST/holdout; prep path freezes without outcomes.

---

### G. Verdict

**REVISE.**

Core event object, pins, D1 golden-trace arm/return logic, shared LTF imports, and several integrity fences look sound. The screen is **not ready for the operator execution gate**: T3–T5 and controls are unfinished, the HARD tripwire is incomplete, MDE curves are absent, P_WIDE is absent, and MID_RANGE arm assignment is wrong if T3 is turned on.

After developer fix: re-run this skill (fresh context), then operator `--execute` gate. **QA does not launch the screen.**

---

## QA run 7 — 2026-07-22T12:00Z — mode: subagent — HEAD `99f1a5537f9f37ca459d07f7f0a0bdf8a89e9807`

**Stage:** post-REVISE re-review (QA run 6 residuals). Fresh-context subagent; did not author the implementation. `--execute` **not** run.

**Verdict: REVISE**
**FAILING_ARTIFACT:** `python/src/xen/sigbar/absorb.py` + `python/experiments/SPDR-009/screen_code/absorb_screen.py`
**REQUIRED_SKILL:** `experiment-developer`

**Dirty tree (implementation under review; full `git status` not available in this tooling):**
- HEAD matches run 6: `99f1a5537f9f37ca459d07f7f0a0bdf8a89e9807` (`.git/refs/heads/main`)
- Files re-read for this pass: `absorb.py`, `absorb_screen.py`, `test_sigbar_absorb.py`, live `design.md` §§0,3–9, `gt_output.json`, INFR-020 `pins.json` + `class_thresholds_1m.json` (SOL + structure), INFR-018 registry pin, QA run 6 issues as checklist only

**Developer fix claims (independent disposition):**

| # | Claim | Verdict | Evidence |
|---|---|---|---|
| 1 | MID_RANGE uses raw `delta_ratio_resid` as signed_score (MIRROR reachable) | **FIXED** | `absorb.py:624–629`: `signed = float(dr)`; no `into=sign(dr)` projection. `_arm_label` + unit test `test_mid_range_score_allows_mirror_arm` |
| 2 | Screen complete battery T1–T5 + P_WIDE freeze + mid-range T3 + matched random T4 + bare T5 + within-symbol derange disclosure + CONFIRM + spread-scale proxy + D1 ib_width | **PARTIAL** | Runner wires all named layers; residual defects below (P_WIDE p25, T4 CI, §5 labels, session secondary, bare match quality) |
| 3 | Tripwire CF* + collapse + material-edge + survival + bite bps + `tripwire.json` | **PARTIAL** | Structure present in `_run_tripwire` / `calibrate_cf_star`; T2 not adjudicated; CF* seeds/order/artifact incomplete |
| 4 | MDE plant curves before DESIGN contrasts | **FIXED** | `step_mde_curves` → `results/mde_curves.json` then `step_design_reads` (`absorb_screen.py:712–715`) |
| 5 | P_WIDE count-only freeze + separate stratum | **PARTIAL / FAIL on p25 leg** | τ freeze + separate layer present; **no-result cut is still p10** (see Issues) |
| 6 | Day-clustered shared-day arm contrast when available | **FIXED** | `contrast_day_clustered`: shared days ≥3 → `mt[d]−mb[d]`; else global base fallback + `paired_days` flag (`absorb.py:1226–1232`) |
| 7 | Consecutive same-level first-bar collapse | **FIXED** | Implemented before return (`absorb.py:735–755`); consecutive LTF gap + same `level_kind`/symbol/pair |

---

### A. Independent pin re-hash (contract consistency)

| Pin | Contracted (design §0 / absorb) | On-disk / code | Verdict |
|---|---|---|---|
| INFR-020 `pins.json` envelope | `5f170b717e350fb7c0cf1647cd1b78fb88a1fa212ed50dce83ec1049af44f6c5` | `absorb.INFR020_PINS_SHA256` | **MATCH** (constant; runtime re-hashes) |
| `seasonal_baselines_mtf.parquet` | `86c81937…38a12c1` | `pins.json.artifacts` = absorb dict | **MATCH** |
| `class_thresholds_1m.json` | `dee853ad…e9fc` | three-way | **MATCH** |
| `class_thresholds_mtf.json` | `745fb435…3ae7` | three-way | **MATCH** |
| `sessions_mtf.json` | `c55cd880…62df` | three-way | **MATCH** |
| `zone_scale_census.json` | `f64e0d22…7f1e` | three-way | **MATCH** |
| `zone_scale_census_d1_ibwidth.json` | `76c3d4b5…5f0c` | three-way | **MATCH** |
| `coverage_report.json` | `68dac757…3a424` | three-way | **MATCH** |
| INFR-017 baselines | `1b7244c8…` | `pins.json.frozen_inputs` | **MATCH** |
| INFR-017 column_pins | `e3b9fd9b…` | `pins.json.frozen_inputs` | **MATCH** |
| Catalog fence | `35d3375e…` | `pins.json.frozen_inputs` | **MATCH** |
| INFR-018 registry | `5c386984…` | registry EOF `pin_sha256` exact | **MATCH** |

SOL frozen cuts (independent read of `class_thresholds_1m.json`):  
`volume.high=5.34397`, `range.low=−0.899321`, `delta_abs.high=4.85461`, `delta_ratio.abs_high=1.37780` — match design GT-4 / run-6.  
**Note:** range blocks carry only p90/p10 (`high`/`low`); **no `range.p25` field** exists in the frozen threshold JSON.

---

### B. Golden-trace re-derivation (design §8 / `gt_output.json` — not impl fixtures)

Arm rule from design §3.3: `signed_score = into_side × delta_ratio_resid`; S9 if `da≥d_hi` and `signed≥dr_hi`; MIRROR if `da≥d_hi` and `signed≤−dr_hi`; else BASE.

| Event | into · dr → signed | da vs d_hi | signed vs ±dr_hi | Arm | Verdict |
|---|---|---|---|---|---|
| **GT-1** IB_LOW 03:27 | (−1)×(−1.5016)=+1.5016 | 9.88 ≥ 4.85 | +1.50 ≥ +1.38 | **S9** | **PASS** |
| **GT-2** PRIOR_SESSION_LOW | (−1)×(−1.5397)=+1.5397 | huge | ≥ +dr_hi | **S9** | **PASS** |
| **GT-3** PRIOR_VAL | (+1)×(−1.382)=−1.382 | huge | ≤ −dr_hi | **MIRROR** | **PASS** |
| **GT-4** IB_LOW | (−1)×(+1.2096)=−1.2096 | 26 ≥ d_hi | \|signed\| < 1.3778 | **BASE** | **PASS** |

Implementation `_into_side` / `_arm_label` / located-pool `signed = into * dr` match. Tests bind to designer-pinned `gt_output.json` under D1 `ib_width` τ=0.25. Suite structure: 24 test functions + 4 GT params ≈ **27** cases as claimed (not re-executed here).

---

### C. Design-fidelity trace (post-fix residual focus)

| Design clause (§ref) | Code (file:line) | Verdict | Notes |
|---|---|---|---|
| §0 frozen re-hash | `absorb.py:177–242` | **MATCHES** | |
| §0 four pairs + D4 IB=60 | `PAIR_SPECS` / `ib_minutes_for_pair` | **MATCHES** | |
| §0 D6.3 1m path | outcomes + levels | **MATCHES** | |
| §0 DESIGN/CONFIRM only | band fence | **MATCHES** | |
| §3.2 consecutive same-level → first | `absorb.py:735–755` | **MATCHES** | by level_kind+adjacency; not level_price (LOW residual) |
| §3.2 P_WIDE = **p25 range** + tighter τ | `absorb.py:517–526` + screen freeze | **DEVIATES (MAJOR)** | no p25 in thresholds → silent p10; only τ differs from P |
| §3.2 τ count-only freeze | `step_pool_cuts` | **MATCHES** (intent) | sample-heuristic disclose |
| §3.3 three arms (located) | `_arm_label` + into×dr | **MATCHES** | |
| §3.3 MID_RANGE continuous score | raw `dr` | **MATCHES** (QA-6 I-1 closed) | habitat score ≠ into-level by construction; disclosed |
| §3.4 entry next LTF; side=−into | contact builder | **MATCHES** | mid-range uses fade of measured aggression |
| §3.4 session-remainder secondary | — | **MISSING** | still not emitted |
| §3.4 ret_norm prior-session-range | outcomes | **MATCHES** when zone_mode primary | |
| §4 T1 + mirror companion | `_layers_for_events` + day-clustered | **MATCHES** structure | shared-day when available |
| §4 T2 Spearman + ≥2000 derange | `_t2_dose` | **MATCHES** global seeds | within-symbol disclosure @ 200 seeds |
| §4 T3 mid-range | MID_RANGE path + layers | **MATCHES** structure | |
| §4 T4 matched random + day-clustered CI | `matched_random_timing` + screen | **PARTIAL** | primitive OK; runner emits means only — **no day-clustered CI** |
| §4 T5 bare touch (30 matched / event) | `bare_level_touch_events` | **PARTIAL** | complement near level; not phase/side matched 30-per-event as §4.2 |
| §4.2 MDE before read | `step_mde_curves` | **MATCHES** | sample ≤30 symbols |
| §4.3 path-swap fixed-H + bite bps | primitives + runner | **MATCHES** primitives | |
| §4.3 CF* plant 1×/2×/3× MDE, ≥200 seeds, **before** real read | `calibrate_cf_star` + `_run_tripwire` | **DEVIATES** | seeds=50; calibration after T1 in same step; T2 not adjudicated |
| §4.3 collapse + material-edge + survival | `_run_tripwire` | **MATCHES** for T1 | T2 absent |
| §4.3 `results/tripwire.json` full | `_emit(tripwire.json)` | **DEVIATES** | per-pair overwrite; last pair wins |
| §5 UNPOWERED-first labels | thin UNPOWERED flags only | **PARTIAL** | no SUPPORTED/WASH/… emission |
| §6.1 cost floor | `cost_floor_bps` | **MATCHES** | |
| §6.2 SPREAD-SCALE-ROUTING | SOL proxy in layers | **PARTIAL** | not per-symbol at screen time |
| §6.3 usable universe option A | `usable_universe` | **MATCHES** | tests 194/72/31 |
| §6.4 day-clustered unit | shared-day contrast | **MATCHES** | |
| §7 CONFIRM-before-freeze + CONFIRM once | helper + `step_confirm` | **MATCHES** | CONFIRM samples ≤40 symbols |
| §9 execution order prep/execute | main() | **PARTIAL** | MDE before contrasts OK; CF* order not |

---

### D. Golden-trace diff (implementation logic vs design)

| Item | Expected | Implemented | Verdict |
|---|---|---|---|
| GT-1…4 arms + returns | §8 / gt_output | `_arm_label` + 1m path | **MATCHES** (logic; suite pins JSON) |
| GT-5a–d,g–h,j–k | raise | dedicated tests | **MATCHES** |
| GT-5e IB before complete | raise | contact path raise | **MATCHES** logic; no dedicated test |
| GT-5f PRIOR_* current session | raise | shared `formed_ts` | **MATCHES** via ltf; no absorb test |
| GT-5i matched_random own session | raise | primitive | **MATCHES** logic; no unit test |
| GT-5l non-COMPLETE | raise | filter + traded_fraction raise | **PARTIAL** |

---

### E. Governance & boundary checklist

| Check | Evidence | Verdict |
|---|---|---|
| Holdout sealed; no TEST | bands + HOLDOUT_START | **OK** |
| Causal t−1 entry | next LTF open | **OK** |
| COMPLETE-window | aggregate + predicate + fence | **OK** |
| D6.3 1m path | outcomes/levels | **OK** |
| L-28 derangement | path-swap + score derange assert FP=0 | **OK** on primitives |
| No local accounting | screen + check | **OK** |
| SPDR TRAIN-only; 0 counted reads | design + band fence | **OK** |
| No estimand P&L / no BacktestNode | vectorised only | **OK** |
| Tripwire HARD complete adjudicator | T1 path yes; **T2 missing**; CF* short/order | **REVISE** |
| CONVERSION-PIN L-21 | estimand already bps | **OK** |
| SPREAD-SCALE-ROUTING | SOL proxy only | **PARTIAL** |
| L-23 amendment ledger | design 2L/13T/9N (no LOOSER streak) | **OK** (design) |
| Shared LTF boundary | imports not redefined | **OK** |
| DEVIATIONS | none | **OK** — silent P_WIDE p10 fallback is **not** an approved deviation |

---

### F. Issues (open after this re-review)

1. **MAJOR — P_WIDE no-result cut is not p25**  
   **Design §:** §3.2 secondary pool; multiplicity 4×2×2=16; §5 zone sensitivity  
   **Where:** `absorb.py:517–526`; frozen `class_thresholds_*.json` have only `range.low` (p10)  
   **Problem:** Without `range.p25`, code keeps p10 and relies on tighter τ. That is a **different object** than “p25 range residual + tighter τ”. Count freeze and layers still run, but the secondary stratum is mis-defined. Design census scripts compute p25 from residual quantiles at freeze time — production path does not.  
   **Required:** compute/freeze per-(symbol,tf) range p25 on DESIGN residuals (count-only, before outcomes), write into `pool_cuts.json` (or equivalent), and set `range.low` from that for `pool_mode=="P_WIDE"`. Refuse or hard-fail if P_WIDE would silently equal P’s result cut.

2. **MAJOR — Tripwire does not adjudicate T2**  
   **Design §:** §4.3 HARD — “ADJUDICATES: T1 … and T2 (ρ)”  
   **Where:** `absorb_screen.py:_run_tripwire`  
   **Problem:** collapse/survival only for T1 H10. T2 ρ under fixed-H path-swap is not computed.  
   **Required:** after path-swap, recompute Spearman(signed_score, swapped ret) vs raw ρ; apply material-edge precondition + CF* survival to T2, or document operator-approved scope cut (none present).

3. **MEDIUM — CF* calibration undersized and ordered after real T1**  
   **Design §:** §4.3 — ≥200 seeds; publish CF* + three plant sizes **before** any real read  
   **Where:** `_run_tripwire` `n_seeds=50`; called after `_layers_for_events` builds T1  
   **Required:** default/run ≥200 seeds; emit full CF* block (1×/2×/3×, seed set, prior 0.25) to `tripwire.json` **before** DESIGN contrasts (after MDE curves); then apply to T1/T2.

4. **MEDIUM — `results/tripwire.json` overwritten per pair**  
   **Where:** `absorb_screen.py:646`  
   **Problem:** each pair `_emit`s a single-key object with `_partial: True`; only the last pair remains on disk. Per-pair detail lives in `layers.json` only.  
   **Required:** accumulate all pairs into one `tripwire.json` (and include CF* calibration block).

5. **MEDIUM — T4 emits means, not day-clustered CI**  
   **Design §:** §4 T4 “day-clustered CI”  
   **Where:** `step_design_reads` T4 block (~480–486)  
   **Required:** resolve donor outcomes with day keys and use `contrast_day_clustered` (or equivalent) for the S9−control contrast.

6. **MEDIUM — bare_level_touch not matched as §4.2 specifies**  
   **Design §:** §4.2 — same level kind, phase band, side; 30 matched draws **per event**  
   **Where:** `bare_level_touch_events`  
   **Problem:** global complement of climax-hold near any level; global subsample; no per-event 30-draw matching; `into_side` drops ties (`prev_close=None`).  
   **Required:** implement matched draws per pool-P event (or design amendment if global control is accepted).

7. **MEDIUM — §5 band labels not emitted**  
   **Design §:** §5 UNPOWERED-first labels  
   **Where:** layers emission  
   **Problem:** thin UNPOWERED flags only; no SUPPORTED/SUGGESTIVE/WASH/CONTRADICTED vs MDE.  
   **Required:** label each primary contrast using published MDE + CI before disposition.

8. **LOW — session-remainder secondary hold still missing**  
   **Design §:** §0 / §3.4 disclosure hold  
   **Required:** emit session-remainder ret (disclosure only) or explicit design-scoped deferral with operator note.

9. **LOW — GT-5(e)(f)(i) still lack dedicated tests; spread-scale is SOL proxy only**  
   **Required:** raise-path tests; per-symbol `spread_scale_route` on audited set when practical.

**Closed from QA-6 (verified this run):** I-1 MID_RANGE arm math; I-6 day-clustered shared-day contrast; I-7 consecutive first-bar collapse; MDE curves step; core tripwire *primitives* (path-swap, bite bps, CF* plant function, collapse/survival *for T1*); T1–T5 *wiring presence*; P_WIDE *stratum + τ freeze presence* (definition still broken — Issue 1).

**Non-issues / still good:** shared LTF imports; frozen pin contracts; GT-1…4 arm/return logic; 1m outcomes; refractory; no local accounting; no TEST/holdout; prep freezes without outcomes; option-A universe sizes in tests.

---

### G. Verdict

**REVISE.**

The seven claimed fixes land partially: mid-range arm math, day-cluster contrast, consecutive collapse, MDE-before-contrast, and most battery *wiring* are real. The screen is **still not ready for the operator execution gate** because:

1. **P_WIDE is not the designed secondary pool** (p10 silently, not p25).  
2. **HARD tripwire is incomplete** (T2 not adjudicated; CF* seeds/order/artifact incomplete).  
3. Report-layer gaps remain (T4 CI, bare matching, §5 labels).

Route to **experiment-developer**. After fix: fresh-context QA again, then operator `--execute` gate. **QA does not launch the screen.**

---

## QA run 8 — 2026-07-22T18:00Z — mode: subagent — HEAD `99f1a5537f9f37ca459d07f7f0a0bdf8a89e9807`

**Stage:** post-REVISE re-review after second developer fix pass (QA run 7 residuals). Fresh-context subagent; did not author the implementation. `--execute` **not** run. Smoke counts (SOL D1 P=203 / P_WIDE@τ0.10=920) **not** re-executed here — logic of p25 vs p10 checked in code only.

**Verdict: APPROVE**

All **MAJOR** run-7 residuals are independently closed. Primary battery (T1–T4, tripwire HARD on T1+T2, P_WIDE p25, MDE-before-contrast, §5 labels on primary contrasts) is design-faithful enough for the operator execution gate. Residual notes below are **non-blocking** (disclosure / report polish).

**Dirty tree (implementation under review; full `git status` not available in this tooling):**
- HEAD matches runs 6–7: `99f1a5537f9f37ca459d07f7f0a0bdf8a89e9807` (`.git/refs/heads/main`)
- Files re-read: `absorb.py` (P_WIDE cut, CF*, labels, bare, contrast), `absorb_screen.py` (order, tripwire merge, T4/T5), `test_sigbar_absorb.py` (structure), design §§3.2, 4.2–4.3, 5; pin constants + registry EOF; QA run 7 issue list as checklist only

**Developer fix claims (independent disposition):**

| # | Claim | Verdict | Evidence |
|---|---|---|---|
| 1 | P_WIDE p25 of `range_resid` on COMPLETE series; raise if unavailable; no silent p10 | **FIXED** | `absorb.py:518–543`: derive `quantile(0.25)` on COMPLETE residuals (`vals.len() >= 20`); override via `range_resid_p25`; else `RuntimeError`. Sets `r["low"]=p25`, `wide_cut_source="p25_range_resid"`. Default `range_resid_cut_key="low"` does **not** fall through to p10 as p25 |
| 2 | Tripwire CF* n_seeds=200 before real layers; T1 **and** T2 collapse; merge `tripwire.json`; survival both | **FIXED** | `absorb_screen.py:466–486` CF* before `_layers_for_events`; `n_seeds=200`; `_run_tripwire` collapse_t1/t2 + survives_t1/t2; merge at `796–809`. Fallback prior 0.25 only when calibration thin (disclosed) |
| 3 | T4 day-clustered block-bootstrap CI + label | **FIXED** | T4 block `~526–560`: per-day S9 means − global control mean → `block_bootstrap_ci` (DAY_BLOCK); `label_band` |
| 4 | T5 bare + n_per_event=30; contrast + label | **PARTIAL** | Contrast + label present; `n_per_event=30` is a **global cap factor** (`×50`), not true 30-per-event matched draws (see residual N-1) |
| 5 | §5 `label_band` on T1/T1_mirror/T4/T5; T2 SUPPORTED/WASH/CONTRADICTED | **FIXED** | `_layers_for_events` labels T1/T1m/T2; T4/T5 labelled in runner |
| 6 | Pins / GT-1…4 still green (27 absorb cases) | **STRUCTURE OK** | 24 test fns + GT parametrize ×4 = **27** cases; pin constants still match design §0 / registry EOF. Suite not re-executed this run |

---

### A. Independent pin re-hash (contract consistency)

| Pin | Contracted | Evidence this run | Verdict |
|---|---|---|---|
| INFR-020 `pins.json` envelope | `5f170b717e350fb7c0cf1647cd1b78fb88a1fa212ed50dce83ec1049af44f6c5` | `absorb.INFR020_PINS_SHA256` | **MATCH** |
| `seasonal_baselines_mtf.parquet` | `86c81937…38a12c1` | absorb dict | **MATCH** |
| `class_thresholds_1m.json` | `dee853ad…e9fc` | absorb dict | **MATCH** |
| INFR-018 registry | `5c386984…` | registry EOF `pin_sha256` exact | **MATCH** |

(Other INFR-020 consumer rows unchanged from runs 6–7; runtime still re-hashes at entry.)

---

### B. Golden-trace re-derivation (design §8 — not impl fixtures)

Arm rule unchanged. Implementation `_into_side` / `_arm_label` / located `signed = into × dr` unchanged from run 7 **PASS** on GT-1…4 logic. Tests still bind to designer-pinned `gt_output.json` under D1 ib_width τ=0.25.

| Event | Arm | Verdict |
|---|---|---|
| GT-1 | S9 | **PASS** (logic) |
| GT-2 | S9 | **PASS** |
| GT-3 | MIRROR | **PASS** |
| GT-4 | BASE | **PASS** |

---

### C. Design-fidelity trace (run-7 residual focus)

| Design clause (§ref) | Code (file:line) | Verdict | Notes |
|---|---|---|---|
| §3.2 P_WIDE = **p25 range** + tighter τ | `absorb.py:518–543` + screen freeze | **MATCHES** | Hard-fail if p25 unavailable; no silent p10 |
| §3.2 τ count-only freeze | `step_pool_cuts` | **MATCHES** (intent) | p25 re-derived per build (deterministic on frozen residuals); not written into `pool_cuts.json` (disclosure only) |
| §4 T4 day-clustered CI | `absorb_screen.py:526–560` | **MATCHES** | Cross-session control ⇒ global ctrl mean under day units (disclosed by construction) |
| §4 T5 bare + contrast | bare + `contrast_day_clustered` | **PARTIAL** | Population not fully §4.2-matched (N-1) |
| §4.2 30 matched draws / event (kind×phase×side) | `bare_level_touch_events` | **DEVIATES** | Global near-level complement + cap; residual N-1 |
| §4.3 CF* ≥200 seeds, 1×/2×/3× MDE, before real read | `calibrate_cf_star` + screen order | **MATCHES** | Per-pair CF before that pair’s layers; side-file `tripwire_cf_{pair}.json` then merge |
| §4.3 adjudicates T1 **and** T2 | `_run_tripwire` | **MATCHES** | T2 dest “excludes zero” ≈ `abs(ρ_sw)>0` (weak proxy; conservative HARD) |
| §4.3 survival both + material-edge | `_survives` | **MATCHES** | |
| §4.3 `tripwire.json` all pairs | merge `existing[pair_id]` | **MATCHES** | Reset at step start |
| §5 labels T1/T1m/T2/T4/T5 | layers + runner | **MATCHES** | T4/T5 often `mde=None` → SUPPORTED unreachable (N-2) |
| §4.2 MDE before contrasts | `step_mde_curves` then layers | **MATCHES** | |
| §3.4 session-remainder secondary | outcomes H∈{5,10} only | **MISSING** | residual N-3 (disclosure) |
| §0 frozen re-hash / D6.3 / COMPLETE / no TEST | unchanged paths | **MATCHES** | |
| Shared LTF / no local accounting | imports + check | **MATCHES** | |

---

### D. Golden-trace diff (implementation vs design)

| Item | Expected | Implemented | Verdict |
|---|---|---|---|
| GT-1…4 arms + 1m returns | §8 / gt_output | `_arm_label` + `evaluate_outcomes_1m` | **MATCHES** (logic; suite pins JSON) |
| GT-5a–d,g–h,j–k | raise | dedicated tests | **MATCHES** |
| GT-5e,f,i | raise | contact / ltf / primitive paths | **MATCHES** logic; still no dedicated tests (N-4) |
| GT-5l non-COMPLETE | raise | filter + fence | **PARTIAL** (unchanged) |

---

### E. Governance & boundary checklist

| Check | Evidence | Verdict |
|---|---|---|
| Holdout sealed; no TEST | bands + HOLDOUT_START | **OK** |
| Causal t−1 entry; COMPLETE; D6.3 1m | contact + outcomes | **OK** |
| L-28 derangement | path-swap + score derange FP=0 | **OK** on primitives |
| No local accounting | screen + check | **OK** |
| SPDR TRAIN-only; 0 counted reads | design + band fence | **OK** |
| Tripwire HARD complete adjudicator | T1+T2; CF* 200; survival; merge artifact | **OK** |
| CONVERSION-PIN L-21 | estimand bps of entry | **OK** |
| SPREAD-SCALE-ROUTING | SOL proxy in layers | **PARTIAL** (unchanged; report) |
| Shared LTF boundary | imports not redefined | **OK** |
| DEVIATIONS | none | **OK** — silent p10 P_WIDE **removed** |

---

### F. Disposition of QA-7 issues

| QA-7 # | Severity | Status | Notes |
|---|---|---|---|
| 1 P_WIDE not p25 | MAJOR | **CLOSED** | Derive + raise; no silent p10 |
| 2 Tripwire no T2 | MAJOR | **CLOSED** | collapse + survival T2 |
| 3 CF* seeds/order | MEDIUM | **CLOSED** | 200 seeds; before layers per pair |
| 4 tripwire.json overwrite | MEDIUM | **CLOSED** | merge per pair |
| 5 T4 no day-clustered CI | MEDIUM | **CLOSED** | block bootstrap + label |
| 6 bare not §4.2 matched | MEDIUM | **OPEN (non-blocking)** | residual N-1 |
| 7 §5 band labels | MEDIUM | **CLOSED** | T1/T1m/T2/T4/T5 |
| 8 session-remainder | LOW | **OPEN (non-blocking)** | residual N-3 |
| 9 GT-5 tests / spread proxy | LOW | **OPEN (non-blocking)** | residual N-4 |

**Closed earlier (runs 6–7, still hold):** MID_RANGE arm math; day-clustered shared-day T1; consecutive first-bar collapse; MDE curves step; battery wiring; pin contracts; GT-1…4 arm/return logic.

---

### G. Residual notes (non-blocking — not REVISE conditions)

**N-1 — MEDIUM (disclosure control) — bare_level_touch still not 30 matched draws per event.**  
`bare_level_touch_events` builds a global near-level complement of climax-hold, then caps at `n_per_event * 50`. Docstring claims per-event matching; code does not match by level kind × phase × side per pool-P event. T5 is **disclosure** (soil legs use T1–T4 + floor). Operator must not promote T5 without re-matching, or accept global control as a design amendment.

**N-2 — LOW — T4/T5 `label_band(..., mde=None)`.**  
MDE curves plant T1 only. Positive T4/T5 CI can at best be SUGGESTIVE, never SUPPORTED. Soil leg (ii) needs T4 *positive* (`excludes_zero`), not the SUPPORTED label.

**N-3 — LOW — session-remainder secondary hold not emitted.**  
Design §0/§3.4 disclosure hold; primary H∈{5,10} only.

**N-4 — LOW — GT-5(e)(f)(i) still lack dedicated tests; spread-scale SOL proxy only.**

---

### H. Verdict

**APPROVE.**

Run-7 blockers are closed: P_WIDE is p25 (hard-fail, no silent p10); HARD tripwire calibrates CF* at 200 seeds before real layers, adjudicates T1 and T2, merges `tripwire.json`, and applies survival on both; T4 has day-clustered CI + label; §5 labels land on primary contrasts. Remaining N-1…N-4 do not block the operator execution gate for the primary soil battery.

**Next:** operator `--execute` gate only (QA does not launch). If T5 is material to disposition narrative, fix N-1 first or record an accepted global-control scope note. **QA APPROVE does not launch the screen.**

---

## QA run 9 — 2026-07-22T00:56Z — mode: operator-session (fresh context) — HEAD `99f1a5537f9f37ca459d07f7f0a0bdf8a89e9807`

**Stage:** post-APPROVE residual-fix re-review (QA run 8 residuals N-1…N-4). Fresh context — this session did **not** author the implementation. `--execute` **not** run. No commit.

**Verdict: REVISE**
**FAILING_ARTIFACT:** `python/src/xen/sigbar/absorb.py` + `python/experiments/SPDR-009/screen_code/absorb_screen.py`
**REQUIRED_SKILL:** `experiment-developer`

Both blockers are **new defects introduced by the post-run-8 residual-fix pass**, not carry-overs. Run-8's approved primary battery is otherwise intact and independently re-verified below. Both fixes are small.

**Dirty tree at review (`git status --porcelain`):**
```
 M docs/experiments-docs/INDEX.md
 M docs/experiments-docs/checkpoints/2026-07-21-015-signed-value-absorption-screen/design.md
 M docs/signal-registry/candidate-families/cf-sigauc-001.md
 M python/experiments/SPDR-009/design.md
 M python/experiments/SPDR-009/qa-review.md
?? python/experiments/SPDR-009/screen_code/
?? python/src/xen/sigbar/absorb.py
?? python/tests/test_sigbar_absorb.py
```

**Sources read this run:** `_pipeline-config.md`; `qa-compliance/SKILL.md`; live `design.md` §§0–10 incl. AMENDMENT-22/23/24; `qa-review.md` runs 6–8; `absorb.py` (full, 1772 lines); `absorb_screen.py` (full, 936 lines); `test_sigbar_absorb.py` (full); `ltf.py` import surface; INFR-020 `results/pins.json`; `xen.evaluation.{bybit_round_trip_cost_bps,spread_scale_route}`.

**Executed this run (read-only):** `pytest python/tests/test_sigbar_absorb.py` → **32 passed** (29 test fns, GT parametrize ×4). `shasum -a 256` on INFR-020 `pins.json`. Three targeted reproduction probes (below). **No screen execution.**

---

### A. Independent pin re-hash

| Pin | Contracted | Evidence this run | Verdict |
|---|---|---|---|
| INFR-020 `pins.json` | `5f170b717e350fb7c0cf1647cd1b78fb88a1fa212ed50dce83ec1049af44f6c5` | `shasum -a 256` on disk = **exact byte match**; `absorb.INFR020_PINS_SHA256` identical | **MATCH** (re-hashed, not asserted) |
| 7 INFR-020 consumers (`seasonal_baselines_mtf`, `class_thresholds_1m`, `class_thresholds_mtf`, `sessions_mtf`, `zone_scale_census`, `zone_scale_census_d1_ibwidth`, `coverage_report`) | design §0 table | `test_assert_spdr009_frozen_inputs_matches_contracted_hashes` re-hashes all 7 on disk against `absorb.INFR020_ARTIFACT_SHA256` and against `pins.json.artifacts` — **passed** | **MATCH** |
| INFR-017 baselines `1b7244c8…`, column_pins `e3b9fd9b…`, fence `35d3375e…` | design §0 | `assert_frozen_inputs` inside the same passing test | **MATCH** |
| INFR-018 registry `5c386984…` + kernel K-UNIFORM | design §0 | `absorb.py:188–204`; passing test | **MATCH** |
| Mismatch behaviour | raise | `test_gt5c_frozen_hash_mismatch_raises` — passed | **MATCH** |

---

### B. Golden traces GT-1…GT-4 (re-run, not asserted)

`test_golden_trace_arm_and_returns` executed and **passed for all four**, binding to designer-pinned `design_derivations/gt_output.json` (arm, `into_side`, `signed_score` ±1e-4, `ret_bps_H5`/`H10` ±1e-3, `entry_ts` exact).

| Event | Arm | Verdict |
|---|---|---|
| GT-1 2022-12-28 03:27 IB_LOW | S9 | **PASS (executed)** |
| GT-2 2022-12-29 01:24 PRIOR_SESSION_LOW | S9 | **PASS (executed)** |
| GT-3 2022-12-26 23:34 PRIOR_VAL | MIRROR (sign guard) | **PASS (executed)** |
| GT-4 2022-11-12 22:08 IB_LOW | BASE (large \|Δ\|, sub-threshold direction) | **PASS (executed)** |

Arm rule `signed = into × dr`, three-way split at `±dr_hi` under `da ≥ d_hi` — `absorb.py:421–432`, `712–713` — matches §3.3.

---

### C. Disposition of run-8 residuals N-1…N-4

| # | Claimed fix | Verdict | Independent evidence |
|---|---|---|---|
| **N-1** | `bare_level_touch`: per-event match, `level_kind × side × phase±30m`, `n_per_event=30` | **CLOSED** | `absorb.py:1578–1633` — donors indexed by `(level_kind, side)`; per pool event `abs(donor.mins_since_close − phase) ≤ 30` **and** `donor.anchor_ts != own_anchor`; `rng.choice(..., size=min(30, len(elig)), replace=False)`; `src_event_ts` stamped. Disjointness from pool P enforced twice (`~(effort ∧ no-result)` at `1494–1496`; `OpenTime ∈ event_times` skip at `1542`). Test `test_bare_level_matches_per_event_not_global_sample` passes. Global `×50` cap is **gone**. |
| **N-2** | Session-remainder secondary hold + `T1_session_remainder` disclosure | **CLOSED IN INTENT — NEW DEFECT (Issue 1)** | Columns emitted `absorb.py:905–922`; disclosure layer `absorb_screen.py:441–457` with the "no promote claim" note. But the emission introduces a schema-inference crash — reproduced, see Issue 1. |
| **N-3** | GT-5(e)(f)(i) dedicated tests | **PARTIAL — 2 of 3 real** | (e) `test_gt5e_ib_edge_before_complete_is_unavailable` — real, asserts `level_available=False` + `excluded_not_yet_formed`. (f) `test_gt5f_prior_levels_formed_before_consumer_session` — real, asserts non-null `formed_ts` strictly `< cur`. (i) `test_gt5i_matched_random_own_session_raises` — **vacuous**, see Issue 3. |
| **N-4** | Per-symbol `spread_scale_route` | **CLOSED (capped)** | `absorb_screen.py:426–440` — loops `s9["symbol"].unique()[:20]`, per-symbol `cost_floor_bps → spread_rt_bps → spread_scale_route`, stamps `spread_label`. Gross = pooled stratum contrast, which is what §6.2 specifies. 20-symbol cap is undisclosed in the artifact (residual R-4). |
| — | "32 absorb tests pass" | **VERIFIED** | Executed: `32 passed in 8.44s`. |

---

### D. Standing checklist re-verified (runs 6–8 items)

| Check | Evidence this run | Verdict |
|---|---|---|
| Shared LTF import boundary | `absorb.py:55–64` imports `absorb_candidate_predicate`, `structural_levels_1m`, `assign_candidate_sessions`, `available_levels_for_candidates`, `aggregate_signed`, `prior_htf_session_ranges`, `design_gap_days`; `test_absorb_imports_shared_ltf_helpers_not_redefined` asserts no `def <name>` in absorb — passed | **OK** |
| P_WIDE = p25 range residual, no silent p10 | `absorb.py:526–544` — derives `quantile(0.25)` on COMPLETE residuals (`len ≥ 20`), or explicit `range_resid_p25`; default `range_resid_cut_key="low"` makes the p10 branch **unreachable**; else `RuntimeError`. Confirmed no fall-through | **OK** |
| HARD tripwire complete | `_run_tripwire` (`absorb_screen.py:692–843`): CF* pre-computed at `466–507` **before** `_layers_for_events`, `n_seeds=200`, plants 1×/2×/3× MDE (`absorb.py:1367–1440`); collapse + survival on **both** T1 and T2; material-edge precondition; per-pair merge into one `tripwire.json` with reset at step start (`464`); bite in bps of entry (`path_swap_bite_bps`, `> 0.5`) | **OK** |
| L-28 derangement, zero fixed points | `derange_scores_global` (index-FP assert `970–971`), `derange_scores_within_symbol` (`1000–1001`), `outcome_path_swap_fixed_h` (`1146–1154`). `test_derange_scores_global_zero_fixed_points`, `test_gt5g_derangement_fixed_point_raises` — passed | **OK** |
| DESIGN/CONFIRM only; TEST/holdout unreachable | `build_contact_events:487–488` raises on any other band; `test_gt5a` (`load_bars("…","TEST")` raises) and `test_holdout_constant_is_sealed` — passed. No TEST/holdout literal anywhere in either file except docstrings | **OK** |
| Causal ≤ t−1 | Entry = `event OpenTime + ltf` (`714`, `649`); contiguity `event→entry` re-checked on the 1m grid (`846–850`); IB availability via shared helper + fence (`695–700`); prior-session levels via `structural_levels_1m` `formed_ts` | **OK** |
| D6.3 1-minute path | `assert_no_ltf_outcome_path(1, …)` at `498`, `823`, `1108`; levels built from `bars_1m`; `assert_levels_from_1m` at `577–581`; `test_gt5j` passed | **OK** |
| COMPLETE-window only | `ltf_complete_bars` (`complete_only=True`) + explicit non-COMPLETE fence `509–515` + `absorb_candidate_predicate(require_complete=True)`; `test_gt5l` passed | **OK** |
| No local accounting | `check_no_local_accounting(screen_code)` at runner entry (`61`) and in `test_no_local_accounting_in_spdr009_screen_dir` — passed | **OK** |
| Card ban 2 / S1 refusal / A-H non-edge | `assert_no_per_level_delta` (`583`), `refuse_s1_as_qualifier` (`270–280`), `assert_not_edge_bearing_operational` (`261–267`, called `492`); `test_gt5d/h/k` passed | **OK** |
| CONVERSION-PIN L-21 | Estimand already bps of entry price (`872`); `ret_norm` divisor = prior HTF session range only (`895–903`) — matches §3.4 = §6.1 | **OK** |
| Cost floor §6.1 | `cost_floor_bps` reads INFR-017 `column_pins` per symbol, `max(tick, flip)`, labels `MAX_TICK_FLIP_UPPER_BOUND` / `SPREAD_TICK_FLOOR_ONLY`, `validated_on_sample_only`; `test_cost_floor_audited_symbols_near_design_table` reproduces SOL **11.748** @ H=10min, fee leg 11.0 — passed | **OK** |
| Option-A universe | `usable_universe` from frozen `coverage_report`; `test_usable_universe_option_a_floors` asserts **194 / 72 / 31** — passed | **OK** |
| MDE before contrasts | `main()`: `step_power_census → step_mde_curves → step_design_reads` (`908–911`) | **OK** |
| SPDR lane: 0 counted reads, no TEST, no BacktestNode, no P&L booked | vectorised Python; no registry/TEST path; disposition is an operator act | **OK** |
| L-23 amendment ledger | design 2L/13T/9N; LOOSERs A-18, A-24; no LOOSER streak ≥ 3 (A-22 T → A-23 T → A-24 L) | **OK** (design) |

---

### E. Issues

1. **MAJOR — session-remainder emission crashes `evaluate_outcomes_1m`, and every caller swallows it → silent loss of instruments from the PRIMARY pooled read**
   **Design §:** §3.4 secondary hold; §4.1 (pooled per pair is the PRIMARY stratum); §6.3 (`power_census` is the declared census); Code Standards *safe optimization must not change sample membership*.
   **Where:** `absorb.py:927` `out = pl.DataFrame(out_rows)` — default `infer_schema_length=100`.
   **Problem:** `rec["ret_bps_session"]` is initialised `None` (`906`) and only overwritten when the session remainder clears its contiguity guard (`910–922`). If the first ≥100 events of a batch have no remainder and a later one does, Polars infers `Null` for the column and then raises
   `ComputeError: could not append value: … of type: f64 to the builder`.
   **Reproduced this run** on real SOL DESIGN bars: 120 events with `session_end == entry_ts` followed by one 2-hour remainder → `ComputeError`. This is exactly the regime expected on D2–D4, where COMPLETE-window retention is 0.387 / 0.202 / 0.089 and long remainder spans routinely fail contiguity.
   **Why it is not merely a crash:** every caller catches `Exception` and continues —
   `absorb_screen.py:484–485` (DESIGN reads), `293–294` (MDE curves), `859–860` (CONFIRM), `541–543` (T4), `625–626` (T5). The affected symbol vanishes from `layers.json`, `mde_curves.json` and `events_DESIGN_*.parquet`, while `step_power_census` — which never calls `evaluate_outcomes_1m` — still counts it. `layers` and `power_census` would disagree with **no emitted drop count**, on a screen whose disposition turns on powered-null vs UNPOWERED.
   **Required:** construct with `pl.DataFrame(out_rows, infer_schema_length=None)` (or an explicit schema); add a regression covering the all-None-then-float ordering; and either narrow the runner's `except Exception` or emit a per-pair `n_symbols_failed` count into `layers.json`.
   **Also fixed by the same change:** `rec["session_exit_ts"]` (`922`) is set only on success and is **silently dropped** when it first appears after row 100 (verified: extra keys past the inference window are discarded without error). Column is unused downstream, so this is cosmetic only.

2. **MEDIUM — T2 `CONTRADICTED` is unreachable; anti-monotone dose-response would be reported as `WASH`**
   **Design §:** §5 — *"CONTRADICTED … (for T2: return ANTI-monotone in aggression-into-level — genuine evidence against the mechanism, and a result in its own right)"*.
   **Where:** `absorb_screen.py:405–417`, using `one_sided_p` from `_t2_dose:346–350` (`p = mean(null ≥ ρ)`, right-tailed).
   **Problem:** the `CONTRADICTED` branch requires `ρ < 0` **and** `one_sided_p ≤ 0.05`. With a right-tailed p, a strongly negative ρ against a null centred near zero gives `p ≈ 1`, so the branch can never fire; every anti-monotone T2 falls through to `WASH`. This suppresses the one T2 outcome the design names as evidence **against** the mechanism — material on a screen whose role is falsification.
   **Required:** compute the left-tail fraction (`mean(null ≤ ρ)`) for the negative branch and label on that; report both tails in the T2 block.

3. **LOW — GT-5(i) has no effective test (N-3 only 2/3 closed)**
   **Design §:** §8 GT-5(i).
   **Where:** `test_sigbar_absorb.py:316–366`.
   **Problem:** the body is wrapped in `try/except RuntimeError`; the non-raise path guards on `if out.height:` and its only assertion is `assert bad.height == 0 or True`, which is vacuous. Executed in isolation this run: the call **does not raise** and returns `height == 0`, so the test asserts nothing at all. The primitive's guard itself is correct (`absorb.py:1061–1065`, raises when a donor entry lands in `[event.anchor_ts, event.session_end)`), but it is unexercised.
   **Required:** construct an event whose `session_end` provably spans a donor anchor + phase and assert `pytest.raises(RuntimeError, match="MATCHED_RANDOM")`.

---

### F. Residual notes (non-blocking; carry forward)

- **R-1 — CF\* calibrated on one symbol, applied to a pooled contrast.** `absorb_screen.py:493–504` picks the first symbol with ≥4 events; `_run_tripwire` then applies that CF\* to the cross-symbol pooled T1/T2. Design §4.3 calibrates on *this design's own stream*, which is the pooled arm. Direction of the bias is not obvious; the value is disclosed in `tripwire_cf_<pair>.json`, so it is auditable. Unchanged from run 8.
- **R-2 — `calibrate_cf_star` degenerate branch.** `absorb.py:1407–1409`: if `base.columns` is not a superset of `s9p.columns`, `pool` falls back to the S9 arm alone and `sw_base` then falls back to the **unswapped** `base` (`1419`, `1422`), mixing a swapped treat arm with a raw control. Unreachable when both arms come from one frame (the normal path), but it should raise rather than degrade silently.
- **R-3 — T5 coverage caps and fallback.** `absorb_screen.py:606` iterates only `list(bars_by)[:30]`; `607–610` falls back to matching donors against **all** pool-P events when a symbol has no BASE events, while the contrast remains BASE − bare. Both are undisclosed in `layers.json`.
- **R-4 — Undisclosed caps.** `spread_scale_route` first 20 symbols (`431`); MDE curves first 30 symbols (`288`); CONFIRM first 40 symbols (`854`). All reasonable for cost, none emitted as a coverage line.
- **R-5 — bare-touch tie-break asymmetry.** Bare donors call `_into_side(..., prev_close=None)` (`1553`), so exact `Close == level` touches are dropped; pool P uses the prior-close tie-break (`701–705`). Small population difference between treated and control.
- **R-6 — P_WIDE p25 not written to `pool_cuts.json`.** Re-derived deterministically per build from frozen residuals (`absorb.py:529–533`); §3.2/§9 read as if the cut were frozen into the artifact. Unchanged from run 8.
- **R-7 — T4/T5 label with `mde=None`** (run-8 N-2): positive CI can at best read `SUGGESTIVE`. Soil leg (ii) needs T4 *positive* (`excludes_zero`), not the `SUPPORTED` label — the analyst must read it that way.
- **R-8 — T2 runtime.** `_t2_dose` runs 2000 global derangements + 200 within-symbol per (hold × pool × pair) — 16 primary cells. Not a correctness issue; flagged so the operator is not surprised by wall-clock at `--execute`.
- **R-9 — GT-5(e) semantics.** Design says an IB-edge event before IB wall-clock "raises"; the implementation makes it *unavailable* via the shared helper, so the `absorb.py:695–700` raise is defensive and normally unreachable. Integrity effect is identical (the event never enters the pool); wording differs. Unchanged from runs 6–8.

---

### G. Verdict

**REVISE.**

Run-8's approved battery re-verifies clean: pins re-hashed byte-exact including the INFR-020 envelope `5f170b71…`, GT-1…GT-4 executed and passing, shared LTF boundary intact, HARD tripwire complete (CF\* 200 seeds before layers, T1+T2 collapse+survival, merged artifact, bite in bps), P_WIDE genuinely p25 with a hard failure and no p10 fall-through, no local accounting, DESIGN/CONFIRM only, holdout sealed. Residuals **N-1 and N-4 are closed**; **N-3 is 2/3 closed**.

The residual-fix pass introduced two defects that must be fixed before the operator execution gate:

1. The session-remainder emission (N-2) makes `evaluate_outcomes_1m` raise on a plausible batch ordering, and every caller swallows the exception — instruments would silently drop out of the primary pooled read with no count emitted. Reproduced on real bars this run.
2. T2 can never be labelled `CONTRADICTED`, suppressing the one dose-response outcome the design names as evidence against the mechanism.

Both are small, local fixes. Route to **experiment-developer**; then fresh-context QA run 10; then the operator `--execute` gate. **QA does not launch the screen. Nothing committed.**

---

## QA run 10 — 2026-07-22T01:11Z — mode: subagent (fresh context) — HEAD `99f1a5537f9f37ca459d07f7f0a0bdf8a89e9807`

**Stage:** post-REVISE re-review after the developer's QA-9 fix pass (I-1, I-2, I-3), applied without an intervening QA run. Fresh-context subagent; did **not** author the implementation. `--execute` **not** run. Nothing committed. No implementation or design file edited.

**Verdict: REVISE**
**FAILING_ARTIFACT:** `python/src/xen/sigbar/absorb.py` (`matched_random_timing`) + `python/tests/test_sigbar_absorb.py`
**REQUIRED_SKILL:** `experiment-developer`

**All three QA-9 issues are independently confirmed CLOSED.** The blocker is a *pre-existing* defect that runs 6–9 did not catch and that this pass's new companion test structurally masks: the **T4 matched-random control emits zero rows on real data**, so soil leg (ii) can never be read.

**Dirty tree at review (`git status --porcelain`):**
```
 M docs/experiments-docs/INDEX.md
 M docs/experiments-docs/checkpoints/2026-07-21-015-signed-value-absorption-screen/design.md
 M docs/signal-registry/candidate-families/cf-sigauc-001.md
 M python/experiments/SPDR-009/design.md
 M python/experiments/SPDR-009/qa-review.md
?? python/experiments/SPDR-009/screen_code/
?? python/src/xen/sigbar/absorb.py
?? python/tests/test_sigbar_absorb.py
```

**Sources read:** `qa-compliance/SKILL.md`; `research-pipeline/_pipeline-config.md`; live `design.md` §§0–10 incl. AMENDMENT-22/23/24; `qa-review.md` runs 8–9 in full (1–7 as context); `absorb.py` (all 1775 lines); `absorb_screen.py` (all 959 lines); `test_sigbar_absorb.py` (all 621 lines); `ltf.py` import surface; INFR-020 `results/pins.json`.

**Executed (read-only):** `pytest python/tests/test_sigbar_absorb.py` → **34 passed**; full suite (minus the two pre-existing collection errors) → **264 passed / 4 skipped**; `shasum -a 256` on INFR-020 `pins.json`; four targeted reproduction probes (I-1 old-vs-new, dtype/concat, T2 label reachability, GT-5(i) raise, T4 control census). **The screen was not launched.**

---

### A. Independent pin re-hash

| Pin | Contracted | Evidence this run | Verdict |
|---|---|---|---|
| INFR-020 `pins.json` | `5f170b717e350fb7c0cf1647cd1b78fb88a1fa212ed50dce83ec1049af44f6c5` | `shasum -a 256` on disk = **byte-exact**; `absorb.INFR020_PINS_SHA256` identical | **MATCH** (re-hashed) |
| 7 INFR-020 consumer artifacts | design §0 table | `test_assert_spdr009_frozen_inputs_matches_contracted_hashes` re-hashes all 7 on disk vs `INFR020_ARTIFACT_SHA256` **and** vs `pins.json.artifacts` — passed | **MATCH** |
| INFR-017 `1b7244c8…` / `e3b9fd9b…` / fence `35d3375e…` | design §0 | `assert_frozen_inputs` inside the same passing test | **MATCH** |
| INFR-018 registry `5c386984…` + K-UNIFORM | design §0 | `absorb.py:188–204`; passing test | **MATCH** |
| Mismatch ⇒ raise | GT-5(c) | `test_gt5c_frozen_hash_mismatch_raises` — passed | **MATCH** |

---

### B. Golden traces GT-1…GT-4 (executed, not asserted)

`test_golden_trace_arm_and_returns` ran and passed for all four against designer-pinned `design_derivations/gt_output.json` (arm, `into_side`, `signed_score` ±1e-4, `ret_bps_H5`/`H10` ±1e-3, exact `entry_ts`). Arm rule `signed = into × dr`, three-way split at `±dr_hi` under `da ≥ d_hi` — `absorb.py:421–432`, `701–713` — matches §3.3.

| Event | Expected arm (design §8) | Verdict |
|---|---|---|
| GT-1 2022-12-28 03:27 IB_LOW | S9 | **PASS (executed)** |
| GT-2 2022-12-29 01:24 PRIOR_SESSION_LOW | S9 | **PASS (executed)** |
| GT-3 2022-12-26 23:34 PRIOR_VAL | MIRROR (sign guard) | **PASS (executed)** |
| GT-4 2022-11-12 22:08 IB_LOW | BASE (large \|Δ\|, sub-threshold direction) | **PASS (executed)** |

---

### C. Disposition of QA-9 issues 1–3 (independently reproduced, not accepted)

| QA-9 # | Severity | Claimed fix | Verdict | Independent evidence |
|---|---|---|---|---|
| **I-1** | MAJOR | `infer_schema_length=None` on the five list-of-dicts frames; regression test; per-pair `coverage` counts | **CLOSED — reproduced both ways** | Built QA-9's exact batch (120 events with `session_end == entry_ts`, then one 2-hour remainder) on real SOL DESIGN bars. **Current code:** 121 rows, `ret_bps_session` **Float64**, 1 non-null, `session_remainder_ok` sum 1. **Same batch with `pl.DataFrame` shimmed back to the old default:** `ComputeError: could not append value: -43.093129 of type: f64 to the builder` — the original failure reproduces exactly and is removed by the fix. All five constructions carry the flag (`absorb.py:747, 930, 1094, 1219, 1639`); `1742` is an explicit-schema empty frame. The `session_exit_ts` side-issue is also gone (column now present, Datetime, 1 non-null). |
| **I-2** | MEDIUM | `_t2_dose` emits `one_sided_p_neg` + `mde_rho_p05`; label branch uses the left tail | **CLOSED — all three labels reachable** | Drove the real `_t2_dose` (`absorb_screen.py:321–367`) and the real label branch (`405–425`) on three synthetic pools: monotone-positive ρ=+0.987, p_pos=0.000 → **SUPPORTED**; monotone-negative ρ=−0.981, p_neg=0.000, p05=−0.163 → **CONTRADICTED**; pure noise ρ=+0.000 → **WASH**. Under the run-9 code the negative case gave p=1.000 and fell through to WASH. |
| **I-3** | LOW | GT-5(i) rewritten with a 30-day event session so donors provably land inside; `pytest.raises` | **CLOSED for the raise** | With `anchor = entry − 100 min` and `session_end = anchor + 30 d` over 233 DESIGN anchors, **1–6 of the 30 drawn donors land inside the declared session on every seed 1–10**; `matched_random_timing` raises `MATCHED_RANDOM DISJOINT FAIL` on seeds 1–5. The raise is genuinely exercised, not merely reachable. **But the companion test added alongside it is vacuous — see Issue 1.** |
| — | — | "34 absorb tests; 264 passed / 4 skipped" | **VERIFIED** | `34 passed in 9.08s`; `264 passed, 4 skipped`. The two collection errors (`test_xena_certify.py`, `test_xena_final_gate.py`) are `ModuleNotFoundError: No module named 'tests'` import-mode failures in files untouched by this work — pre-existing and unrelated. |

**New-defect sweep on the I-1/I-2/I-3 changes (the specific risks named at hand-off):**

| Risk | Check | Result |
|---|---|---|
| `infer_schema_length=None` changes a dtype | Symbol with **no** remainders → `ret_bps_session` dtype **Null**; symbol **with** remainders → **Float64** | Expected and harmless: every cross-symbol combine is `pl.concat(..., how="diagonal_relaxed")` (`absorb_screen.py:302, 505, 538, 652, 673, 694, 727, 767, 888`). Probed the mixed Null/Float64 concat directly → **OK, resolves to Float64**, height preserved. A plain `how="diagonal"` would have raised; none is used. |
| `infer_schema_length=None` changes sample membership | Row count and drop counters compared old vs new on the reproduction batch | **No change** — the flag only widens type inference; `n_dropped_gap` logic untouched. |
| Added `coverage` key breaks a `layers.json` consumer | `_layers_for_events(..., mde_info=...)` reads only `T1_H{h}` / `T1_mirror_H{h}`; `census.json` reads only `P.n` / `P.n_S9` | **No break.** The extra `n_symbols_read` / `n_symbols_failed` keys inside `mde_curves["pairs"][pair]` pass through `mde_info.get(...)` harmlessly and are echoed into `layers["…"]["mde"]`. The `UNPOWERED` early-return branch (`step_mde_curves:300`) still yields `mde_h = None`, and `_run_tripwire`'s `mde.get("mde_bps") or 5.0` still falls back cleanly. |

---

### D. Standing checklist re-verified

| Check | Evidence this run | Verdict |
|---|---|---|
| INFR-020 pins re-hashed (not asserted) | §A above; runtime re-hash at every entry point | **OK** |
| GT-1…GT-4 executed | §B | **OK** |
| GT-5(a)–(l) raise set | dedicated tests a,b,c,d,e,f,g,h,i,j,k,l present and passing; (e) semantics = "unavailable" not "raise" (R-9) | **OK** |
| Shared LTF import boundary | `absorb.py:55–64`; `test_absorb_imports_shared_ltf_helpers_not_redefined` asserts no `def <name>` in absorb — passed | **OK** |
| HARD leak tripwire | CF\* computed at `absorb_screen.py:500–520` **before** `_layers_for_events` (`541`); `n_seeds=200`; plants 1×/2×/3× MDE (`absorb.py:1370–1443`); collapse **and** survival on **both** T1 and T2 (`716–852`); material-edge precondition; per-pair merge into one `tripwire.json` with reset at `472`; bite = `corr(mfe_bps, donor_mfe_bps) > 0.5` in **bps of entry** (`absorb.py:1222–1235`) | **OK** |
| P_WIDE p25, no p10 fall-through | `absorb.py:526–544` — `quantile(0.25)` on COMPLETE residuals (`len ≥ 20`) or explicit `range_resid_p25`; the `range_resid_cut_key` branch is unreachable at the default `"low"`; otherwise `RuntimeError` | **OK** |
| No local accounting | `check_no_local_accounting` at runner entry (`61`) + passing test | **OK** |
| DESIGN/CONFIRM only; TEST/holdout unreachable | `build_contact_events:487–488` raises on any other band; `test_gt5a`, `test_holdout_constant_is_sealed` passed | **OK** |
| Causal ≤ t−1 entry | entry = event LTF OpenTime + `ltf` (`649`, `714`); contiguity re-checked on the 1m grid (`846–850`); IB availability via shared helper + fence (`695–700`); prior-session levels via `formed_ts` | **OK** (but see Issue 1 — this same guard is what kills T4) |
| D6.3 1-minute path | `assert_no_ltf_outcome_path(1, …)` at `498`, `823`, `1111`; levels from `bars_1m`; `assert_levels_from_1m` at `577–581`; `test_gt5j` passed | **OK** |
| COMPLETE-window only | `ltf_complete_bars(complete_only=True)` + explicit fence `509–515` + `absorb_candidate_predicate(require_complete=True)`; `test_gt5l` passed | **OK** |
| L-28 derangements (zero fixed points) | `derange_scores_global` (`971–974`), `derange_scores_within_symbol` (`1003–1004`), `outcome_path_swap_fixed_h` (`1149–1157`); tests passed | **OK** |
| CONVERSION-PIN L-21 | estimand already bps of entry (`872`); `ret_norm` divisor = prior HTF session range only (`895–903`) | **OK** |
| Cost floor §6.1 | `cost_floor_bps` per symbol from INFR-017 `column_pins`, `max(tick, flip)`, labels + `validated_on_sample_only`; SOL **11.748** @ H=10 min with fee leg 11.0 reproduced by passing test | **OK** |
| Option-A universe | `usable_universe` from frozen `coverage_report`; test asserts **194 / 72 / 31** | **OK** |
| MDE before contrasts | `main()`: `step_power_census → step_mde_curves → step_design_reads` | **OK** |
| SPDR lane: 0 counted reads, no TEST, no BacktestNode, no P&L | vectorised Python; disposition is an operator act | **OK** |
| L-23 amendment ledger | design §10: **2 LOOSER / 13 TIGHTER / 9 NEUTRAL**; LOOSERs A-18, A-24; no LOOSER streak ≥ 3 (A-22 T → A-23 T → A-24 L) | **OK** |
| **T4 availability control (§4.2 `matched_random_timing`, soil leg ii)** | **Probed on real data: 150 donor rows built, 0 survive** | **FAILS — Issue 1** |

---

### E. Issues

1. **MAJOR — the T4 matched-random control returns ZERO rows on real data, so soil leg (ii) can never be read; the new companion test hides it**
   **Design §:** §4 T4 (*"Does the S9 arm beat a matched random-timing entry at all"*); §4.2 `CONTROL matched_random_timing`; §4/§5 three-leg conjunction — *"(ii) T4 positive — the S9 arm must beat matched random-timing entries, not merely beat the BASE arm"*; §5 *"Reproduction alone never passes"*.
   **Where:** `absorb.py:1075` (`matched_random_timing` stamps `"event_ts": e["event_ts"]` — the **original** event's timestamp — on every donor row while `entry_ts` is the **donor's**) colliding with `absorb.py:846–850` in `evaluate_outcomes_1m` (`if event_ts in idx: if (entry_ts − event_ts).total_seconds() != ltf*60 → drop`). `matched_random_timing` ends by calling `evaluate_outcomes_1m` (`1095`).
   **Problem:** for a genuine cross-session donor the gap between the event's bar and the donor's entry is never one LTF bar, and the original `event_ts` is always a real 1-minute grid timestamp, so the guard fires on **every** donor row. The control is structurally empty for all four pairs.
   **Reproduced this run** on real SOLUSDT D1 DESIGN bars: 88 pool-P events, 5 in the S9 arm → `matched_random_timing` built **150 donor rows** and returned **0**. Re-running the identical donor frame with a donor-consistent `event_ts` returns **145 of 150**, isolating the guard as the sole cause.
   **Consequence:** `absorb_screen.py:568` (`if ctrl.height and …`) is never true, so `absorb_screen.py:622–623` writes `T4 = {"UNPOWERED": True}` for every pair and both pools, with no drop count and no error — the same silent-loss shape as QA-9 I-1, on a control the design calls REQUIRED. A screen whose master gate is a three-leg conjunction would report leg (ii) as permanently unpowered while looking healthy.
   **Also:** the test added in this pass, `test_matched_random_cross_session_donors_do_not_raise` (`test_sigbar_absorb.py:360–400`), wraps its only assertion in `if out.height:` — and `out.height` is **0**, so it asserts nothing. It is vacuous in exactly the way QA-9 I-3 objected to, and it masks this defect.
   **Required:** stamp each donor row with its own `event_ts` (donor `entry_ts − ltf` minutes), or exempt `pool == "MATCHED_RANDOM"` rows from the event→entry contiguity guard; then make the companion test assert a **non-zero** control row count (e.g. `assert out.height > 0` before the disjointness check) so the control can never silently empty again.
   **Not introduced by this pass** — the guard and the `event_ts` stamp both predate QA run 9 (cited there at the same line numbers); runs 6–9 did not test the control's yield. Recorded as pre-existing, but blocking: it is verdict-material for the §4 conjunction.

2. **LOW — the new per-pair `coverage` block over-counts reads and mis-describes failures**
   **Design §:** §6.3 (`power_census` reconciliation); this is the QA-9 I-1 remediation.
   **Where:** `absorb_screen.py:481–497` and `522–533`.
   **Problem:** `bars_by[sym]` is populated (`484`) *before* the P / P_WIDE / MID_RANGE builds, and a failure in any one of the three lands the symbol in `skipped` as well — so the same symbol counts in both `n_symbols_read` and `n_symbols_failed`, and `n_symbols_read + n_symbols_failed` can exceed `n_usable`. The emitted note claims *"n_symbols_failed are absent from these layers"*, which is false when only the P_WIDE or MID_RANGE build failed (the P part is already appended at `492`).
   **Required:** count a symbol as read only if at least one pool build succeeded, record which pool failed, and soften the note to match. Non-blocking on its own; listed because the block exists specifically to make layers reconcilable with `power_census`.

---

### F. Disposition of QA run 9 residual notes R-1…R-9 (non-blocking; not re-escalated)

| # | Status this run | Evidence |
|---|---|---|
| **R-1** CF\* calibrated on one symbol, applied pooled | **STANDS** | `absorb_screen.py:506–517` still picks the first symbol with ≥4 events; value disclosed in `tripwire_cf_<pair>.json`, so it stays auditable |
| **R-2** `calibrate_cf_star` degenerate branch degrades silently | **STANDS** | `absorb.py:1410–1412` / `1421–1425` unchanged; unreachable on the normal single-frame path |
| **R-3** T5 symbol cap + BASE-less fallback | **STANDS** | `absorb_screen.py:630` `list(bars_by)[:30]`; `631–634` still falls back to all pool-P events while the contrast stays BASE − bare; neither emitted |
| **R-4** undisclosed caps | **PARTLY IMPROVED, STANDS** | MDE coverage now emits `n_symbols_read` / `n_symbols_failed` (`313–314`); the spread-route 20-symbol cap (`439`) and CONFIRM 40-symbol cap (`878`) are still unemitted |
| **R-5** bare-touch tie-break asymmetry | **STANDS** | `absorb.py:1556` still `_into_side(..., None)` vs pool P's prior-close tie-break (`701–705`) |
| **R-6** P_WIDE p25 not written to `pool_cuts.json` | **STANDS** | still re-derived deterministically per build (`526–533`) |
| **R-7** T4/T5 labelled with `mde=None` | **STANDS**, and now moot for T4 | `absorb_screen.py:602–604`, `657–659`; T4 cannot produce a contrast at all until Issue 1 is fixed |
| **R-8** T2 runtime | **STANDS, slightly worse** | `_t2_dose` runs 2000 global + 200 within-symbol derangements per hold; now also invoked for the MID_RANGE (T3) and D1 ib_width sensitivity layers, i.e. more than the 16 primary cells. Wall-clock warning only |
| **R-9** GT-5(e) "unavailable" vs "raises" | **STANDS** | integrity effect identical (the event never enters the pool); wording differs |

No R-item has new evidence warranting escalation.

---

### G. Verdict

**REVISE.**

The three QA-9 issues are independently confirmed closed, each by direct reproduction rather than by reading the fix: the schema crash reproduces under the old default and is gone under the new one; all three T2 labels now fire on constructed data; the GT-5(i) raise fires on 1–6 donors per seed. The fixes introduced no dtype, sample-membership, or downstream-consumer regression — the Null/Float64 `ret_bps_session` split is absorbed by `diagonal_relaxed`, and the new `coverage` / `n_symbols_*` keys pass through every reader untouched. The standing battery re-verifies clean: pins re-hashed byte-exact, GT-1…GT-4 executed, shared LTF boundary intact, HARD tripwire complete, P_WIDE genuinely p25, holdout sealed, DESIGN/CONFIRM only, causal t−1, 1-minute paths, COMPLETE-window, L-28 derangements, ledger 2L/13T/9N with no LOOSER streak.

What blocks the execution gate is a defect this fix pass did not cause but its new test conceals: **the matched-random availability control produces no rows at all**, so T4 — one of the three co-equal legs the design says the screen cannot pass without — would report UNPOWERED on every pair for a mechanical reason, not an evidentiary one. Measured on real bars: 150 donors built, 0 survive.

Route to **experiment-developer** for the `event_ts` stamp (Issue 1) and the coverage-count wording (Issue 2); then a fresh-context QA run 11; then the operator `--execute` gate. **QA does not launch the screen. Nothing committed.**

---

## QA run 11 — 2026-07-22T01:18Z — mode: subagent (fresh context) — HEAD `99f1a5537f9f37ca459d07f7f0a0bdf8a89e9807`

**Stage:** post-REVISE re-review after the operator's QA-10 fix pass (Issue 1 empty T4 arm; Issue 2 coverage double-count). Fresh-context subagent; did **not** author the implementation. `--prep` and `--execute` **not** run. Nothing committed. No implementation or design file edited.

**Verdict: APPROVE**

Both QA-10 issues are independently confirmed closed by direct measurement on real bars, not by reading the diff. The fix is provably *field-local*: the matched-random control's donor set, entry prices, sides, phases, holds and exit convention are bit-identical to the pre-fix construction — the only column that changed is the one that was breaking it. No new defect found in the fourth-pass sweep.

**Dirty tree at review (`git status --porcelain`):**
```
 M docs/experiments-docs/INDEX.md
 M docs/experiments-docs/checkpoints/2026-07-21-015-signed-value-absorption-screen/design.md
 M docs/signal-registry/candidate-families/cf-sigauc-001.md
 M python/experiments/SPDR-009/design.md
 M python/experiments/SPDR-009/qa-review.md
?? python/experiments/SPDR-009/screen_code/
?? python/src/xen/sigbar/absorb.py
?? python/tests/test_sigbar_absorb.py
```

**Executed (read-only):** `pytest python/tests/test_sigbar_absorb.py` → **34 passed**; full suite minus the two pre-existing xena collection errors → **264 passed / 4 skipped**; `shasum -a 256` on INFR-020 `pins.json`; a seven-part reproduction probe on real SOLUSDT D1 DESIGN bars (donor census, revert simulation, field-invariance diff, phase/price/hold checks, `event_ts` collision census, concat safety, disjointness census); a runner-equivalent T4 block replay. **The screen was not launched.**

---

### A. Pin re-hash (unchanged, re-verified)

| Pin | Contracted | Evidence this run | Verdict |
|---|---|---|---|
| INFR-020 `pins.json` | `5f170b717e350fb7c0cf1647cd1b78fb88a1fa212ed50dce83ec1049af44f6c5` | `shasum -a 256` on disk = **byte-exact**; `absorb.INFR020_PINS_SHA256` identical | **MATCH** (re-hashed) |
| 7 INFR-020 consumers + INFR-017 trio + INFR-018 registry | design §0 | `test_assert_spdr009_frozen_inputs_matches_contracted_hashes` re-hashes each on disk and cross-checks `pins.json.artifacts` — passed | **MATCH** |
| Mismatch ⇒ raise | GT-5(c) | `test_gt5c_frozen_hash_mismatch_raises` — passed | **MATCH** |

---

### B. Golden traces GT-1…GT-4

All four executed and passed against designer-pinned `gt_output.json` (arm, `into_side`, `signed_score` ±1e-4, `ret_bps_H5`/`H10` ±1e-3, exact `entry_ts`). Arm rule and thresholds untouched by this pass — the fix does not reach `build_contact_events`.

---

### C. Disposition of QA-10 issues

| QA-10 # | Severity | Claimed fix | Verdict | Independent evidence |
|---|---|---|---|---|
| **1** | MAJOR | donor rows stamp `event_ts = entry_ts − ltf_minutes`; source linkage on `src_event_ts`; test asserts non-empty | **CLOSED — measured** | On real SOLUSDT D1 (88 pool-P events, 5 in the S9 arm): `matched_random_timing` now returns **145 of 150** requested donor rows (was **0**), `ret_bps_H10` and `ret_bps_H5` non-null on all 145, `arm`/`pool` = `MATCHED_RANDOM`. `absorb.py:1079` is the changed line; the guard at `846–850` now sees exactly `ltf × 60` s by construction and no longer fires. |
| **2** | LOW | `n_symbols_read = len(set(bars_by) − failed_syms)`; `n_symbols_failed` deduplicated; note reworded | **CLOSED** | `absorb_screen.py:521–535`: `failed_syms` is a set built from `skipped`; read and failed are now **disjoint** and sum to ≤ `n_usable`. The note now reads *"a failed symbol is missing from at least one pool (P / P_WIDE / MID_RANGE) of these layers while power_census.json still counts it"* — which is true both when `load_bars` fails (missing from all three) and when only the P_WIDE build fails (missing from one). Matches behaviour. |

---

### D. Did the fix change WHAT the control measures? (the load-bearing question)

Rebuilt the donor set twice under identical seeding — once with the old stamp, once with the new — and diffed every field.

| Property | Check | Result |
|---|---|---|
| Donor session draw | `entry_ts`, `anchor_ts` frames compared | **identical** |
| Side | `side` column compared | **identical** |
| Phase (`mins_since_anchor`) | `phase` column compared; control phases vs source-event phases | **identical** — control `[128, 655, 747, 778, 1040]` == source `[128, 655, 747, 778, 1040]` |
| Hold / exit convention | `ltf_minutes` compared; `evaluate_outcomes_1m` resolves `i0 + h × ltf` open-to-open, unchanged | **identical** |
| Entry price | spot-checked 3 emitted rows: `entry` == `bars.Open` at `entry_ts` (42.73 / 35.76 / 36.63) | **correct** |
| **Only differing column** | full column diff old vs new | **`event_ts` alone** |
| Revert simulation | recompiled `matched_random_timing` from its own source with the old stamp restored, ran it on the same input | **0 rows** — so `assert out.height > 0` in `test_matched_random_cross_session_donors_do_not_raise` genuinely fails on revert; the test is no longer vacuous |
| GT-5(i) disjointness | raise sits at `absorb.py:1064–1068`, **before** the row append — untouched; `test_gt5i_matched_random_own_session_raises` passes; census over the 145 emitted rows | **0 donor entries inside their source event's session** |

---

### E. New-defect sweep (fourth-pass risk, weighted heavily)

| Risk | Check | Result |
|---|---|---|
| Derived `event_ts` collides with a real pool-P event | census of all 145 donor `event_ts` against the 88 pool-P `event_ts` on the same symbol | **0 collisions.** Materially it cannot matter either: the control frame is never written to an artifact, never passed to `apply_refractory`, never to `outcome_path_swap_fixed_h` (which runs on `parts_p` only), and never to `contrast_day_clustered` — the runner consumes it as a raw numpy array (`absorb_screen.py:569`) |
| `src_event_ts` breaks a concat / schema path | dtype check + `diagonal_relaxed` concat of a pool frame (no such column) with the control frame | **OK** — `Datetime('us')`, concat succeeds, missing side filled with nulls. Same column name and dtype as `bare_level_touch_events` emits (`absorb.py:1639`), and the two frames are never combined |
| Downstream keyed on old donor `event_ts` semantics | `step_design_reads` T4 block, `outcome_path_swap_fixed_h`, `contrast_day_clustered` day keys | **No behavioural change beyond the intended one.** T4 clusters on `day`, derived from `entry_ts` (`absorb.py:868`) — untouched by the stamp. The path-swap never sees the control. `contrast_day_clustered` is not called on the control in the T4 lane |
| Contiguity guard silently weakened for donors | `event_ts = entry_ts − ltf` makes the `846–850` check pass by construction | **Acceptable, not a hole.** The guard exists to enforce detection-bar→entry adjacency for *real* events; a donor has no detection bar. Forward-window contiguity is still enforced independently at `851–860` and did its job — 5 of 150 donors were dropped for gap/end-of-data |
| T4 now emits a degenerate contrast | replayed the runner's T4 block on SOL | S9 n=5 across **5 distinct days** (≥3 ⇒ the day-clustered block-bootstrap branch is reachable, not the UNPOWERED fallback); control n=145, mean −3.979 bps; S9 mean −3.360 bps; raw T4 contrast +0.619 bps. **A real, clusterable number where run 10 measured a structural blank** |
| Coverage counts now under- or over-state | arithmetic re-derivation | Read and failed are disjoint; a symbol failing only its P_WIDE build is now excluded from `n_symbols_read` even though its P rows are in the layers — **conservative direction**, recorded as residual N-2 below |

---

### F. Standing checklist re-confirmed

| Check | Evidence this run | Verdict |
|---|---|---|
| INFR-020 pins re-hashed | §A | **OK** |
| GT-1…GT-4 executed | §B | **OK** |
| GT-5(a)–(l) raise set | all twelve tests present and passing; (e) semantics per R-9 | **OK** |
| Shared LTF import boundary | `absorb.py:55–64`; `test_absorb_imports_shared_ltf_helpers_not_redefined` passed | **OK** |
| HARD leak tripwire | CF\* before layers, `n_seeds=200`, 1×/2×/3× MDE plants, T1 **and** T2 collapse + survival, merged `tripwire.json`, bite in bps of entry | **OK** (untouched this pass) |
| P_WIDE p25, no p10 fall-through | `absorb.py:533` `quantile(0.25)`; `538` `RuntimeError` when underivable | **OK** |
| No local accounting | `check_no_local_accounting` at `absorb_screen.py:61` + passing test | **OK** |
| DESIGN/CONFIRM only; TEST/holdout unreachable | `absorb.py:487`; `test_gt5a`, `test_holdout_constant_is_sealed` passed | **OK** |
| Causal ≤ t−1 | entry = event LTF OpenTime + `ltf`; forward-span contiguity on the 1m grid; IB fence | **OK** |
| D6.3 1-minute path | `assert_no_ltf_outcome_path(1, …)` at `498`, `823`, `1116`; `test_gt5j` passed | **OK** |
| COMPLETE-window only | `absorb.py:513` fence + `require_complete=True`; `test_gt5l` passed | **OK** |
| L-28 derangements | `absorb.py:972`, `974`, plus within-symbol and path-swap asserts; tests passed | **OK** |
| L-23 amendment ledger | design §10 **2 LOOSER / 13 TIGHTER / 9 NEUTRAL**; no LOOSER streak ≥ 3 | **OK** |
| Five list-of-dicts frames carry `infer_schema_length=None` | `747, 930, 1099, 1224, 1644` | **OK** (QA-9 I-1 fix intact) |
| **T4 availability control (soil leg ii)** | 145 usable donor rows on real bars; day-clustered branch reachable | **OK — was the run-10 blocker** |

---

### G. Residual notes (non-blocking)

QA-9 residuals **R-1 … R-9 all still stand exactly as recorded in run 10** — none was touched by this pass and none has new evidence:
R-1 CF\* calibrated on one symbol, applied pooled · R-2 `calibrate_cf_star` degenerate branch degrades silently · R-3 T5 symbol cap + BASE-less fallback · R-4 undisclosed caps (spread-route 20, CONFIRM 40; MDE coverage now emitted) · R-5 bare-touch tie-break asymmetry · R-6 P_WIDE p25 not written to `pool_cuts.json` · R-7 T4/T5 labelled with `mde=None` (T4 can now at best read SUGGESTIVE — leg (ii) needs *positive*, i.e. `excludes_zero`, not the SUPPORTED label) · R-8 T2 runtime · R-9 GT-5(e) "unavailable" vs "raises".

Run-10 residuals:
- **QA-10 Issue 2 (coverage double-count)** — **CLOSED** (§C).
- **N-1 (new, LOW) — T4 donor drop count not surfaced.** `matched_random_timing` returns the frame with `_batch_dropped_gap` set (5 of 150 on the SOL probe), but `absorb_screen.py:592–605` emits only `n_control`. The realised donor count is therefore visible; the dropped count is not. Disclosure only.
- **N-2 (new, LOW) — `n_symbols_read` under-counts when a symbol fails only one pool.** Its P rows are in the layers while the symbol counts as failed. Conservative direction; the `failed` list names the symbol and the error, so it is reconcilable.
- **N-3 (carried, LOW) — T4 control weighting.** Each S9 event contributes up to 30 donor rows to a single global control mean, so symbols with more S9 events dominate the control side. Pre-existing design shape (noted at run 8); disclosed by `n_control`.

---

### H. Verdict

**APPROVE.**

The run-10 blocker is closed by measurement, not assertion: the matched-random control resolves **145 of 150** donors on real bars where it previously resolved none, and the runner's T4 block now produces a day-clusterable contrast (+0.619 bps on the SOL probe, 5 clustering days) instead of a structural `UNPOWERED`. Critically, the fix changed **only** the `event_ts` field — donor sessions, sides, phases, holds, entry prices and exit convention are bit-identical to the pre-fix construction, so the control still measures what §4.2 says it measures. Reverting the stamp reproduces the empty arm, which means the rewritten test is genuinely load-bearing. Cross-session disjointness (GT-5(i)) still raises and still measures zero violations. The coverage counts are now disjoint and the note matches behaviour.

The fourth-pass new-defect sweep found nothing: no `event_ts` collisions with real pool events, no concat or schema breakage from `src_event_ts`, and no downstream consumer keyed on the old donor semantics. The full standing battery re-confirms — pins byte-exact, GT-1…GT-4 executed, GT-5 set complete, shared LTF boundary intact, HARD tripwire complete, P_WIDE genuinely p25, holdout sealed, causal t−1, 1-minute paths, COMPLETE-window, L-28 derangements, ledger 2L/13T/9N with no LOOSER streak. 34 absorb tests and 264 passed / 4 skipped overall.

Ready for the **operator's `--execute` gate**. The residuals above are disclosure items for the analyst, not conditions on execution. **QA APPROVE does not launch the screen. Nothing committed.**

---

## QA run 12 — 2026-07-22T02:34Z — mode: subagent (fresh context) — HEAD `99f1a5537f9f37ca459d07f7f0a0bdf8a89e9807`

**Stage:** post-execution precondition review. Run 1 of the screen executed under operator approval after the run-11 APPROVE, three design preconditions were found unmet, the `results/` tree was **hard-deleted**, and four **post-measurement** amendments (A-25…A-28) were appended to design §10. This run reviews the fixes and the governance handling before a re-run. Fresh-context subagent; did **not** author any of it. `--prep` / `--execute` **not** run; nothing written to `results/` (which is correctly absent).

**Verdict: REVISE**
**FAILING_ARTIFACT:** `python/src/xen/sigbar/absorb.py` (`plant_mde_curve` / `label_band` / `calibrate_cf_star` interaction)
**REQUIRED_SKILL:** `experiment-developer`

All four fixes are real and I verified each by measurement. The blocker is a **new coupling created by AMENDMENT-25**: now that the MDE is computed on the same arm as the contrast, `mde_bps = 0.0` becomes logically equivalent to "the raw T1 contrast is positively material" — and both downstream consumers mishandle a zero MDE, in exactly the branch the screen exists to detect.

**Dirty tree:** unchanged from run 11 (`design.md`, `qa-review.md` modified; `screen_code/`, `absorb.py`, `test_sigbar_absorb.py` untracked). `results/` absent — intentional.

**Executed (read-only):** `pytest python/tests/test_sigbar_absorb.py` → **34 passed**; full suite minus the two pre-existing xena collection errors → **264 passed / 4 skipped**; `shasum -a 256` on INFR-020 `pins.json`; a six-symbol D1 probe exercising `_build_scored`, `mde_for_arm`, `calibrate_cf_star`, `_swap_pooled`, `path_swap_bite_bps`; a reachability probe on the zero-MDE branch; a replay of the P_WIDE selection logic. **The screen was not run.**

---

### A. Pin re-hash

| Pin | Contracted | This run | Verdict |
|---|---|---|---|
| INFR-020 `pins.json` | `5f170b717e350fb7c0cf1647cd1b78fb88a1fa212ed50dce83ec1049af44f6c5` | `shasum -a 256` = **byte-exact** | **MATCH** |
| 7 INFR-020 consumers + INFR-017 trio + INFR-018 registry + K-UNIFORM | design §0 | `test_assert_spdr009_frozen_inputs_matches_contracted_hashes` re-hashes each on disk — passed | **MATCH** |

---

### B. The four precondition fixes — independently measured

| # | Amendment | Claim | Verdict | Measured evidence (6-symbol D1 arm, τ=0.05, DESIGN) |
|---|---|---|---|---|
| 1 | **A-25 MDE/CF\* arm** | MDE per pool on the arm the contrast uses; CF\* on the pooled arm; never defaults to 0.25 | **REAL — but see Issues 1–2** | `mde_for_arm` reports `n_events 338 / n_S9 18 / n_BASE 291 / n_symbols 6`, `T1_H10 = 10.5 bps`; the same computation on a 2-symbol subsample gives **14.5 bps** — the A-25 defect shape reproduced, and the fix removes it. `calibrate_cf_star(bars_by, ev_p, …)` returns **status DERIVED, cf\* = 1.588, 10/10 usable seeds at every plant**, falling 1.588 → 0.691 → 0.442 across 1×/2×/3× with `cf_star_spread_across_plants = 1.147` emitted. Both underivable paths return `cf_star = None`: `mde=None` → `"no MDE at realised n"`, thin arm → `"thin arms"`. `prior_cf: 0.25` is recorded with `prior_is_never_a_fallback: True` and is never substituted. |
| 2 | **A-26 P_WIDE zone** | grid extended below the P floor; selection restricted to τ strictly < τ_P; raises if none | **REAL** | `TAU_GRID` unchanged (floor still 0.05); `P_WIDE_TAU_GRID = (0.005, 0.01, 0.02, 0.03, 0.05, 0.10, 0.15, 0.20)` — the four new values all sit **below** the old floor. `absorb_screen.py:162–179` filters to `t < chosen` *before* counting, defaults to the loosest strictly-tighter value, and closes with `assert wide_chosen < chosen`. Replayed across every possible τ_P: at τ_P = 0.05 the candidate set is `[0.005, 0.01, 0.02, 0.03]`, default 0.03 — the two pools can no longer coincide. Selection is **count-only**: `_count_pool` calls `build_contact_events` + `apply_refractory` and returns `.height`, touching no outcome. |
| 3 | **A-27 tripwire bite** | per-symbol correlation; floor on the per-symbol median; pooled retained as artifact | **REAL** | `path_swap_bite_bps` now returns `per_symbol_median_corr`, `per_symbol_min_corr`, `n_symbols`, `frac_symbols_above_floor`, `floor: 0.5`, `applied_to: "per_symbol_median_corr"`, and `bite_ok` keyed on the **median**, with the pooled figure carrying an explicit divisor-dispersion note. On the probe arm: pooled 0.967, per-symbol median **0.9793**, min 0.9558, 6/6 above floor. (This subset spans only 0.075 → 12.1 in price, so the pooled/per-symbol divergence is small here; the 0.00067 → 20551 span that produced the 0.33 pooled reading is a full-universe property I cannot re-measure with `results/` deleted — the *mechanism* is verified, the D1 numbers in A-27 are not independently reproduced.) |
| 4 | **A-28 contiguity drops** | located / with-outcome / dropped accumulated per pool into `coverage`; `census.json` reconciles | **REAL** | `_build_scored` returns `(frame, n_located)`; the caller accumulates `located` / `kept` per pool and emits `n_events_located`, `n_events_with_outcome`, `n_events_dropped_no_1m_path`. Probe: 394 located → 338 with outcomes → **56 dropped (14.2%)**, and `kept` reconciles exactly with the pooled arm height (338). `census.json` now carries `census_P` from `power_census` alongside `n` and the whole `coverage` block. |

---

### C. §9 execution order — MDE and CF\* before any contrast, on the identical population

Traced statement by statement through `step_design_reads` (`absorb_screen.py:474–753`):

| Order | Line | Action | Contrast run? |
|---|---|---|---|
| 1 | `495–514` | build every symbol's P / P_WIDE / MID_RANGE events, accumulate located/kept | no |
| 2 | `516–517` | `ev_p`, `ev_w` — each pair's arm built **once** | no |
| 3 | `522–528` | `mde_for_arm(ev_p)` and `mde_for_arm(ev_w)` → `mde_curves["pairs"][pair_id]` → **`_emit(mde_curves.json)`** | plants only |
| 4 | `532–548` | `calibrate_cf_star(bars_by, ev_p, mde_bps=…)` → **`_emit(tripwire_cf_<pair>.json)`** | plants only |
| 5 | `574–583` | `_layers_for_events(…, mde_info=mde_by_pool[name])` — **first real contrast** | yes |
| 6 | `740–746` | `_run_tripwire(…, cf_precomputed=cf_pre)` — CF\* is now a **required** kwarg, no internal fallback calibration | yes |

**Order holds.** Both artifacts are on disk before the first real contrast, and steps 3, 4 and 5 all consume the identical `ev_p` / `ev_w` objects — the population identity A-25 demanded. `step_mde_curves` is fully removed with no dangling references; all three `_build_scored` call sites (`504`, `726`, `915`) unpack the new tuple; `_run_tripwire`'s dropped `mde_curves` arg matches its call site; `main()` no longer deletes `power`, which `census.json` now consumes. Cross-pair note, not a defect: D1's contrasts run before D2's MDE is computed, but each pair's MDE is a deterministic function of that pair's own arm, so no ordering contamination is possible.

---

### D. Governance — post-measurement amendment handling

| Question | Finding |
|---|---|
| Hard-delete + full re-run the right response? | **Yes.** This is the programme's amend-in-place rule for a frozen-design confound (dated amendment + hard delete + full rerun, never a follow-up read). `results/` is genuinely absent; nothing from run 1 is reachable by the re-run. |
| A-25…28 correctly dated and directed? | **Yes.** All four carry the 2026-07-22 date, an explicit POST-MEASUREMENT banner, and a direction. A-25 TIGHTER (derived threshold replaces inherited; inapplicable gate labelled) — correct. A-26 TIGHTER (strictly tighter zone) — correct. A-27 **LOOSER** — correctly booked without hedging, since it converts a failing required control into a passing one even though the failure was in the statistic rather than the swap. A-28 NEUTRAL (disclosure of an existing quantity) — correct. |
| Run-1 outcomes disclosed? | **Yes**, and prominently: D1 T1 WASH (+1.8 / −3.2 bps, CI spanning zero, S9 n=310, 168 days), D2–D4 UNPOWERED, D4 zero signed events, S9 median −0.0 bps against an ~11.3–13 bps floor. A reader can weigh every amendment against what was already seen. |
| A-26 outcome-informed risk acceptable? | **Acceptable, with a disclosure requirement.** A-26 does not add a degree of freedom — it *implements* §3.2's pre-registered "tighter τ" leg, which run 1 failed to honour. The three stated mitigations all hold in code (count-only selection; new values appended below the old floor; P's own τ untouched at 0.05). The residual is real but bounded: §3.2 counts P_WIDE among the **16 primary cells**, so the τ for a primary cell was picked after outcomes were seen. Required, non-blocking: the disposition must state that P_WIDE's τ grid was extended post-measurement and that the P_WIDE stratum is therefore outcome-informed, while P is not. |
| Ledger arithmetic | **Correct.** 2L/13T/9N → A-25 T (2L/14T/9N) → A-26 T (2L/15T/9N) → A-27 L (3L/15T/9N) → A-28 N (3L/15T/10N). Header total **3 LOOSER / 15 TIGHTER / 10 NEUTRAL** matches. |
| LOOSER streak ≥ 3? | **No.** Sequence is T → T → L → N. The three LOOSERs (A-18, A-24, A-27) are non-adjacent. Correctly stated in the design footer. |

---

### E. New defects from the restructure

1. **MAJOR — CF\* is calibrated on a ZERO plant whenever T1 is positively material, i.e. in the only regime where CF\* is ever applied.**
   **Design §:** §4.3 CALIBRATION REGIME + AMENDMENT-13 (*"plant a known CAUSAL effect of ~1× the published MDE on the S9 arm so the raw contrast is material by construction"*) + AMENDMENT-4 (CF\* derived, never inherited) + §4.3 MATERIAL-EDGE PRECONDITION.
   **Where:** `absorb.py:1374` (`grid = np.arange(0.0, 30.01, 0.5)` — the plant sweep starts at **0.0**) → `absorb_screen.py:532` (`mde_bps = pair_mde["T1_H10"]["mde_bps"]`) → `absorb.py:1488` (`calibrate_cf_star` guards only `mde_bps is None`).
   **Problem:** `plant_mde_curve` returns the smallest grid value whose CI excludes zero, so it returns **0.0** exactly when the unplanted contrast is already positively material. Before A-25 the MDE came from a decoupled 30-symbol subsample and was ~9.5 bps; now that it is computed on the same arm, `mde_bps == 0.0` is *logically equivalent* to `raw T1 is positively material` — which is precisely the tripwire's material-edge precondition. So in every case where the survival rule actually fires, CF\* is derived with `plant_bps = 0.0`, i.e. on the **observed, unplanted** edge rather than a known-causal one. The threshold that decides "is this edge leaking?" would then be calibrated on the possibly-leaking edge itself.
   **Reproduced this run:** planting a real +40 bps edge into the observed S9 arm gives `mde_for_arm → T1_H10 mde_bps = 0.0`, raw contrast 37.59 bps with CI [30.00, 43.82] excluding zero, and `calibrate_cf_star(mde_bps=0.0)` returns **`status: DERIVED`, `cf_star = 0.317`, `by_multiple["1.0"] = {plant_bps: 0.0, n_usable_seeds: 5}`** — a silently self-referential calibration reported as a clean derivation.
   **Required:** treat a zero MDE as "this instrument cannot size a plant here". Either start the plant grid at the first strictly positive step and return `raw_already_material: True` separately, or guard `if not mde_bps` (None **or** 0) in `calibrate_cf_star` → `UNDERIVABLE`. Preferably plant a strictly positive known-causal effect so CF\* stays derivable in the material branch — otherwise the tripwire becomes inapplicable exactly when it is needed.

2. **MAJOR — §5 `SUPPORTED` is unreachable whenever the MDE lands at 0.0, which is the same positively-material branch.**
   **Design §:** §5 (*"SUPPORTED: effect ≥ its own MDE and ci_low > 0"*) and §4/§5 soil leg (i), which requires **T1 SUPPORTED**.
   **Where:** `absorb.py:1367–1368` — `if mde is not None and (not np.isfinite(mde) or mde <= 0): mde = None`, then `ci[0] > 0` with `mde is None` returns `SUGGESTIVE`.
   **Problem:** by §5's own arithmetic, MDE = 0 and `ci_low > 0` gives `effect ≥ MDE` and should read **SUPPORTED**. The implementation nulls a zero MDE and downgrades to SUGGESTIVE. **Reproduced:** contrast 37.59 bps, CI [30.00, 43.82], MDE 0.0 → `label_band` returns **`SUGGESTIVE`**. Combined with Issue 1's coupling, the screen's strongest possible positive result is systematically demoted, and soil leg (i) — which names SUPPORTED explicitly — can never be satisfied. This is a design-fidelity **DEVIATES**, not a judgement call.
   **Required:** make `label_band` honour a genuine zero MDE as SUPPORTED (keeping the `NaN` / negative guard), or fix the MDE instrument per Issue 1 so 0.0 is never emitted — but the two consumers must agree, because today `label_band` treats 0.0 as "no MDE" while `calibrate_cf_star` treats it as a valid plant size.

3. **LOW — `tripwire.survives: false` is emitted when the gate is inapplicable.** `absorb_screen.py:858` computes `survives = bool(None) or bool(None) = False` while `survives_T1`/`survives_T2` are correctly `None`. The `status` string (`CF_STAR_UNDERIVABLE_GATE_INAPPLICABLE`), `cf_star_derived` and `adjudicable` all disambiguate, but a reader keying on `survives` alone would read a clean bill of health where Addendum §2.8 forbids one. Prefer `survives: None`.

4. **LOW — two amendment citations in code comments point at the wrong amendment.** `absorb_screen.py:244` credits the drop-count fix to "AMENDMENT-27" (it is A-28); `absorb.py:1248` credits the per-symbol bite to "AMENDMENT-25" (it is A-27). Cosmetic, but the ledger is a governance artifact and the code is its main cross-reference.

---

### F. Standing battery re-confirmed

| Check | Evidence | Verdict |
|---|---|---|
| INFR-020 pins re-hashed | §A | **OK** |
| GT-1…GT-4 | `test_golden_trace_arm_and_returns` executed, all four pass against designer-pinned `gt_output.json` | **OK** |
| GT-5(a)–(l) raise set | all twelve tests present and passing | **OK** |
| Shared LTF import boundary | `absorb.py:55–64`; no-redefinition test passed | **OK** |
| P_WIDE p25 no-result leg | `absorb.py:526–544` unchanged — `quantile(0.25)` or explicit override, else `RuntimeError`; now paired with a strictly tighter τ | **OK** |
| Holdout sealed; DESIGN/CONFIRM only | `absorb.py:487`; `test_gt5a`, `test_holdout_constant_is_sealed` passed | **OK** |
| Causal ≤ t−1 | entry = event LTF OpenTime + `ltf`; forward-span contiguity; IB fence | **OK** |
| D6.3 1-minute path | `assert_no_ltf_outcome_path(1, …)` at three sites; `test_gt5j` passed | **OK** |
| COMPLETE-window only | fence + `require_complete=True`; `test_gt5l` passed | **OK** |
| L-28 derangements | global / within-symbol / path-swap asserts; tests passed | **OK** |
| No local accounting | `check_no_local_accounting` at runner entry + passing test | **OK** |
| T4 matched-random (run-11 fix) | `matched_random_timing` unchanged this pass; `_swap_pooled` does not touch it | **OK** |
| Restructure integrity | `step_mde_curves` removed with no dangling refs; all `_build_scored` call sites unpack the tuple; `_run_tripwire` signature matches its call site; `census.json` shape valid | **OK** |
| L-23 ledger | 3L/15T/10N, arithmetic checked, no LOOSER streak | **OK** |

---

### G. Residuals

R-1 is **superseded** — CF\* is no longer calibrated on one symbol; it now plants on the pooled arm via `_swap_pooled`, which is what §4.3 asks for. R-2 is **superseded** — the degenerate `calibrate_cf_star` fallback branch is gone; the function now returns `UNDERIVABLE` instead of degrading. R-3, R-4 (spread-route 20 / CONFIRM 40 caps), R-5, R-6, R-7, R-8, R-9 all **stand** unchanged. Run-11 residuals N-1 (T4 donor drop count not surfaced), N-2 (`n_symbols_read` conservative), N-3 (T4 control weighting) all **stand**. New: the bite remains a report layer with no enforcement even though §7 lists it as HARD — unchanged from earlier runs, and A-27's "blocks a disposition outright" is an operator act, not a code gate.

---

### H. Verdict

**REVISE.**

The governance handling is sound: run 1 is genuinely hard-deleted, the four amendments are dated, directed, justified and disclose what was seen before they were written, the ledger arithmetic is right (3L/15T/10N) and there is no LOOSER streak. All four fixes are real and I measured each — the MDE now moves with the arm (10.5 vs 14.5 on a subsample), CF\* derives on the pooled arm with every seed usable and never falls back to the 0.25 prior, the bite floor is applied to a per-symbol median, and the drop counts reconcile exactly (394 located → 338 kept → 56 dropped). §9's order holds: MDE and CF\* are both on disk before the first real contrast and all three read the identical event population. A-26's outcome-informed risk is acceptable because it implements a pre-registered clause rather than adding a new degree of freedom, subject to the P_WIDE stratum being labelled outcome-informed in the disposition.

What blocks the re-run is a coupling the fix itself created. With the MDE now computed on the contrast's own arm, `mde_bps = 0.0` means exactly "T1 is positively material" — and both consumers get that case wrong: `calibrate_cf_star` accepts it as a valid 1× plant and reports a self-referential CF\* as `DERIVED` (reproduced: `plant_bps 0.0`, `cf_star 0.317`, status DERIVED), while `label_band` nulls it and demotes a 37.6 bps contrast with CI [30.0, 43.8] to `SUGGESTIVE` when §5's own rule says SUPPORTED. Together they disable the leak gate and the soil-leg-(i) label in precisely the branch the screen exists to detect. Both are small, local fixes in `absorb.py`, and the two consumers must be made to agree on what a zero MDE means.

Route to **experiment-developer**; then a fresh-context QA run 13; then the operator re-run gate. **QA does not launch the screen. Nothing committed.**

---

## QA run 13 — 2026-07-22T02:45Z — mode: subagent (fresh context) — HEAD `99f1a5537f9f37ca459d07f7f0a0bdf8a89e9807`

**Stage:** re-review of the QA-12 fixes (AMENDMENT-29: centred MDE, CF\* non-positive-plant refusal, `label_band` zero handling, `survives: None`, citation corrections). Fresh-context subagent; did **not** author the fixes. Screen **not** run.

**Verdict: REVISE**
**FAILING_ARTIFACT:** `python/src/xen/sigbar/absorb.py` `label_band` fall-through + design.md §5 (undefined label region)
**REQUIRED_SKILL:** `quant-designer` (define the label), then `experiment-developer` (one branch)

**Both QA-12 blockers are genuinely closed — verified by measurement on a real D1 arm.** The centring decision is, in my judgement, not merely acceptable but *required* by the design's own text. The remaining blocker is a consequence the fix widens rather than causes: centring systematically lowers every MDE, which pushes cells into a region §5 does not define, and the implementation resolves that region to `UNPOWERED` — the one label with the heaviest governance weight in this design.

**Executed (read-only):** `pytest python/tests/test_sigbar_absorb.py` → **37 passed**; full suite minus the two pre-existing xena collection errors → **267 passed / 4 skipped**; `shasum -a 256` on INFR-020 `pins.json`; a real 6-symbol D1 arm rebuilt from the catalog (n=338, S9=18, BASE=291) exercising `plant_mde_curve`, `calibrate_cf_star`, `label_band`; an uncentred-vs-centred comparison; a full label-branch sweep. **The screen was not run.**

---

### A. Pin re-hash

`shasum -a 256` on `python/experiments/INFR-020/results/pins.json` = `5f170b717e350fb7c0cf1647cd1b78fb88a1fa212ed50dce83ec1049af44f6c5` — **byte-exact**. All seven INFR-020 consumers plus the INFR-017 trio, the INFR-018 registry and K-UNIFORM re-hashed on disk by the passing frozen-inputs test. **MATCH.**

---

### B. QA-12 blockers — closed, measured

| QA-12 # | Claim | Verdict | Measured evidence |
|---|---|---|---|
| **1** CF\* on a zero plant | `plant_mde_curve` centres the arm; `calibrate_cf_star` refuses non-positive plants | **CLOSED** | On the QA-12 fixture (real arm + a planted 40 bps S9 edge; raw contrast 37.59, CI excludes zero) the MDE is now **8.0, was 0.0**. `calibrate_cf_star` with that MDE returns **DERIVED, `plant_bps = 8.0`** — a genuinely positive known-causal plant. It returns **UNDERIVABLE with `cf_star = None`** for `mde_bps` of `0.0`, `None` and `-1.0`, and `prior_cf: 0.25` is recorded with `prior_is_never_a_fallback: True`, never substituted. |
| **2** SUPPORTED unreachable | `label_band` nulls only non-finite or **negative** MDE | **CLOSED** | Same fixture: `label_band(37.59, ci, 8.0)` → **SUPPORTED** (was SUGGESTIVE). Full branch sweep: SUPPORTED (mde 2.0 **and** mde 0.0), SUGGESTIVE, CONTRADICTED, WASH, UNPOWERED all reachable. The two consumers now disagree deliberately and explicitly about zero — `label_band` accepts it as a resolution statement, `calibrate_cf_star` refuses it as a plant size — and each says so in place. |
| — | LOW items | **CLOSED** | `survives` is `None` (not `false`) when `cf_derived` is False, with the "did not survive / was never applied" distinction commented at `absorb_screen.py:858–862`. Both miscited amendments corrected: `absorb.py:1248` → A-27 (per-symbol bite), `absorb_screen.py:244` → A-28 (drop counts); `:306` → A-25 and `:53` → A-26 were already right. |

**Centring verified as effect-independent (the property the fix claims).** Adding a constant +40 bps to the S9 arm leaves the centred MDE **unchanged at 8.0**, while the *uncentred* sweep on the same two arms collapses from **10.5 → 0.0**. That is the defining test of the change and it passes.

---

### C. Scrutiny of the centring decision itself

**Is an effect-independent MDE the right reading of §4.2/§5? Yes — and I would go further: the design's text requires it.**

- §5 defines `SUPPORTED: effect ≥ its own MDE`. If the MDE is the smallest plant that makes the *observed* contrast significant, the test is a tautology — every material contrast passes with MDE 0, every immaterial one fails. A comparison is only meaningful against a quantity that does not embed its own operand.
- §4.2 asks for "MDE read off the curve **at the realised n** per stratum". "At the realised n" is a statement about the arm's sample size and noise, not about what the arm happened to show.
- §6.3 and §9 both require the MDE "published **BEFORE** the real read". An MDE computed by sweeping the uncentred arm cannot honour that literally — it is a function of the read. Centring is what makes the ordering constraint satisfiable rather than nominal.

**Caveat, correctly disclosed:** the centring constant is itself estimated from the same data, so the MDE is independent of the effect's *location* but still uses the data to locate it. That is unavoidable for an MDE at realised n and is disclosed by the new `centred_on_observed` / `observed_contrast` keys.

**Is LOOSER the right direction label? Yes, and conservatively so.** A-29 bundles a genuine loosening (lower MDE ⇒ SUPPORTED easier) with a genuine tightening (`calibrate_cf_star` now refuses plants it previously accepted, so the leak gate is strictly harder to satisfy). Splitting them would have been marginally more precise, but booking the bundle at its most permissive component is the conservative choice L-23 exists to enforce. Ledger arithmetic is right: 3L/15T/10N + A-29 L = **4L/15T/10N**; sequence T→T→L→N→L; the four LOOSERs (A-18, A-24, A-27, A-29) are non-adjacent, so **no streak ≥ 3**.

**One directional consequence A-29 does not book, and should state.** Lowering the MDE also moves the WASH/UNPOWERED boundary — and it moves it *against* closure, not for it. WASH requires `|effect| < MDE`; a smaller MDE means fewer zero-spanning cells qualify as WASH and more fall through to UNPOWERED. Under AMENDMENT-24 a pair reading UNPOWERED is "horizon-covered but inconclusive — neither blocking nor contributing to the close", while a powered WASH is what a family-closing null looks like. So centring makes CF-SIGAUC-001 **harder to close**, which is the opposite direction from the SUPPORTED effect A-29 does book. Required disclosure, not a direction error: A-29's LOOSER label stands, but its rationale should name both consequences so the operator is not surprised if pairs come back UNPOWERED that would previously have read WASH. This is also the mechanism behind Issue 1 below.

**Is post-measurement introduction legitimate? Yes.** A-29 repairs a defect *introduced by A-25* and caught at QA *before any re-run*, so no outcome produced by the fixed code exists. Decisively: the change **cannot** alter run 1's reading (§D), so it cannot have been selected to rescue or bury that result. It touches an instrument (the power yardstick), not the estimand, arms, cuts, τ, holds, bands or nulls.

---

### D. Point 3 — does run 1's D1 reading change label under the new MDE? **No. Plainly: no.**

Run 1 D1 read T1 effect **+1.8 / −3.2 bps with a CI spanning zero**, against an MDE of 13.0. Centring lowers the D1 MDE to roughly 10.

`SUPPORTED` and `SUGGESTIVE` **both require `ci[0] > 0`** — they are unreachable for any MDE whatever when the interval spans zero. I swept the actual `label_band` across MDEs of 13.0, 10.0, 5.0, 1.0, 0.5 and 0.0 at both run-1 effect sizes:

| effect | CI | MDE 13.0 | 10.0 | 5.0 | 1.0 | 0.5 | 0.0 |
|---|---|---|---|---|---|---|---|
| +1.8 | spans zero | WASH | WASH | WASH | UNPOWERED | UNPOWERED | UNPOWERED |
| −3.2 | spans zero | WASH | WASH | WASH | UNPOWERED | UNPOWERED | UNPOWERED |

**At the centred MDE (~10) the label is still WASH** — `|1.8| < 10` and `|−3.2| < 10`. A WASH could only become UNPOWERED if the MDE fell below the effect size (~2–3 bps), roughly four times lower than centring achieves. **So run 1's D1 conclusion is unchanged, and no run-1 reading can be upgraded to SUGGESTIVE or SUPPORTED by this change.** The operator can start the re-run without expecting the previous null to be resurrected by the amendment.

What *does* change for the re-run is the direction shown in the table's right-hand columns — and that is Issue 1.

---

### E. Issues

1. **MEDIUM, verdict-material — `label_band` returns `UNPOWERED` when the effect EXCEEDS its MDE but the CI spans zero, and centring makes that region systematically more reachable.**
   **Design §:** §5 — `UNPOWERED: MDE > |plausible effect| at the realised n`; `WASH: |effect| < MDE → "cannot distinguish", never a refutation (L-11)`; §6.3 `T1 UNPOWERED is INCONCLUSIVE, never a null (B-5)`; AMENDMENT-24 closure rule.
   **Where:** `absorb.py` `label_band` — the terminal `return "UNPOWERED"` after the `|effect| < MDE → WASH` test.
   **Problem:** when the CI spans zero and `|effect| ≥ MDE`, neither §5 label applies — WASH is excluded by its own inequality, and UNPOWERED asserts `MDE > |plausible effect|`, which is the *opposite* of what holds. §5 has a genuine gap here, and the code resolves it to UNPOWERED, i.e. to the assertion that is false. **Reproduced:** `label_band(12.0, [-4.0, 20.0], 1.0)` → `UNPOWERED`. Correct behaviour is retained when the MDE is `None` (an arm that genuinely does not resolve) — the defect is confined to a finite MDE below the observed effect.
   **Why this pass matters:** centring lowers every MDE (measured: 10.5 → 8.0 on the real arm), and WASH requires `|effect| < MDE`, so the change *systematically* shifts zero-spanning cells out of WASH and into this undefined region. Under A-24 an UNPOWERED pair "neither blocks nor contributes to the close" while a powered WASH is exactly what a family-closing null looks like — so the mislabel silently converts "we measured it and cannot distinguish it from zero" into "we did not test it", on the checkpoint's master go/no-go. D1 is safe (effects 1.8–3.2 vs MDE ~10), but thinner pairs and the P_WIDE strata, where double-digit effects with zero-spanning intervals are ordinary, are not.
   **Required:** a designer decision on the label for `|effect| ≥ MDE` with a zero-spanning CI — WASH is the closest fit to §5's intent and to L-11 ("cannot distinguish", never a refutation) — recorded as a §5 clause, then the corresponding one-branch change. Route `quant-designer` → `experiment-developer`.

2. **LOW — importing the runner module recreates `results/`.** `absorb_screen.py:47` runs `OUT.mkdir(parents=True, exist_ok=True)` at import time, so any probe that imports the module resurrects the directory that the A-25…28 governance response hard-deleted. `results/` is present but **empty** at this review (almost certainly created by my own QA-12 probe import; no artifact of any kind is in it, and `git status` shows nothing). Not a breach — `assert_confirm_freeze_ready` keys on `pool_cuts.json`, not on the directory — but "hard-deleted" is not an import-safe state, which is worth knowing before the next deletion is relied upon. Prefer creating the directory inside `main()`.

---

### F. New-defect sweep on the four edits

| Risk | Check | Result |
|---|---|---|
| Centring breaks the `u = 0` guarantee | swept the real and edged arms | **OK** — MDE strictly positive (8.0) in both; `u = 0` never qualifies once centred |
| Centring interacts with the unpaired-days fallback | `plant_mde_curve` centres with `contrast_day_clustered`'s own estimator and sweeps with the same function | **OK** — same estimator on both sides, so the centring is exact by construction |
| `calibrate_cf_star` new early return | `if "arm" not in events.columns or ret_col not in events.columns` returns UNDERIVABLE with the prior recorded but unused | **OK** — replaces a raise; `prior_is_never_a_fallback` still emitted |
| CF\* refusal too aggressive | `if not mde_bps or float(mde_bps) <= 0` | **OK** — refuses `0.0`, `None`, negatives; accepts the centred 8.0 and derives |
| `label_band` zero handling regressed another branch | full branch sweep incl. `mde=None` with a live CI | **OK** — `(5.0, [1.0, 9.0], None)` → SUGGESTIVE; `None/None/None` → UNPOWERED |
| `survives: None` breaks a consumer | grepped; nothing keys on `survives` programmatically; `status`, `cf_star_derived`, `adjudicable` all present | **OK** |
| Mirror MDE also centred | `mde_for_arm` calls `plant_mde_curve(s9, mirror, …)` | **OK** — same treatment, so T1 and T1_mirror label against comparable denominators |
| Cost of the extra contrast call | one additional `contrast_day_clustered` per curve | **OK** — negligible against the 61-point sweep |

---

### G. §9 execution order and standing battery

**Order holds, unchanged from run 12 and re-traced:** `mde_for_arm` (`522`, `525`) → `_emit(mde_curves.json)` (`528`) → `calibrate_cf_star` (`540`) → `_emit(tripwire_cf_<pair>.json)` (`548`) → **first real contrast** `_layers_for_events` (`581`) → `_run_tripwire` (`740`). Both artifacts are on disk before any contrast, and all three stages consume the identical `ev_p` / `ev_w`. Centring strengthens this rather than weakening it: the published MDE no longer depends on the read it precedes.

**Standing battery — all OK:** INFR-020 pins byte-exact; GT-1…GT-4 executed and passing against designer-pinned `gt_output.json`; GT-5(a)–(l) raise set complete; shared LTF import boundary intact (no redefinition); P_WIDE p25 no-result leg plus a strictly tighter τ; holdout sealed and DESIGN/CONFIRM only; causal ≤ t−1 entry; D6.3 1-minute paths; COMPLETE-window fence; L-28 derangements zero fixed points; no local accounting; T4 matched-random (run-11 fix) untouched; A-25…28 fixes (per-pool MDE, strictly tighter P_WIDE, per-symbol bite, drop-count reconciliation) all still in place. L-23 ledger 4L/15T/10N with no LOOSER streak. Three new regression tests pinned and passing (`test_mde_strictly_positive_when_raw_edge_already_material`, `test_cf_star_refuses_zero_or_absent_mde`, `test_label_band_all_branches_reachable`); 37 absorb tests, 267 passed / 4 skipped overall.

**Residuals:** R-1 and R-2 remain superseded. R-3, R-4, R-5, R-6, R-8, R-9 stand. R-7 is **closed** — T4/T5 still label with `mde=None`, but SUPPORTED is no longer structurally unreachable elsewhere, and the soil-leg-(ii) reading rule is unchanged. Run-11 N-1/N-2/N-3 stand. The bite remains a report layer with no code-level enforcement despite §7 listing it as HARD — unchanged and an operator act.

---

### H. Verdict

**REVISE** — one branch and one design sentence away from a re-run.

The two QA-12 blockers are closed and I confirmed each by measurement, not by reading: the MDE on an already-material arm is 8.0 where it was 0.0, CF\* plants a real 8.0 bps known-causal effect and refuses 0.0/None/negatives with `UNDERIVABLE`, SUPPORTED is reachable again, and the defining property of the change — effect-independence — holds exactly (a +40 bps shift moves the uncentred MDE 10.5 → 0.0 and leaves the centred MDE at 8.0). Centring is the right call and I would defend it as required by §4.2/§5 rather than merely permitted; the LOOSER booking is correct and conservative; the post-measurement introduction is legitimate because the change provably cannot move run 1's label.

**On the operator's question: run 1's D1 WASH cannot become SUGGESTIVE or SUPPORTED.** Both labels require the CI to exclude zero, and run 1's spans it — the MDE is irrelevant to that test. At the centred MDE (~10) against effects of +1.8 / −3.2 the label remains WASH.

What blocks the re-run is the far side of that same table. Because centring lowers every MDE, more zero-spanning cells now satisfy `|effect| ≥ MDE`, and §5 defines no label for that combination; the code resolves it to `UNPOWERED`, the one reading §6.3 and AMENDMENT-24 treat as "not tested" and exclude from family closure. On a screen whose entire purpose is a powered null, silently relabelling "measured, cannot distinguish" as "inconclusive" is not a cosmetic error — and this change is what widens the region. Define the label in §5 (WASH is the natural fit), make the one-branch change, then a fresh-context QA run 14 and the operator's re-run gate.

**QA does not launch the screen. Nothing committed.**

---


## QA run 14 — 2026-07-22T02:54Z — mode: subagent (fresh context) — HEAD `99f1a5537f9f37ca459d07f7f0a0bdf8a89e9807`

**Stage:** re-review of the QA-13 fixes — AMENDMENT-30 (new `IMPRECISE` band, §5 rewritten as an exhaustive decision table, `label_band` restructured) and the import-side-effect removal. Fresh-context subagent; did **not** author the changes. Screen **not** run.

**Verdict: REVISE**
**FAILING_ARTIFACT:** `python/experiments/SPDR-009/screen_code/absorb_screen.py` (`mde_for_arm` coverage) + design §5 UNPOWERED row
**REQUIRED_SKILL:** `experiment-developer` (compute the missing MDE curves §4.2 already mandates), with a `quant-designer` confirmation on the §5 ordering

**The IMPRECISE call is sound and I accept the rejection of my WASH suggestion — the designer is right and I was wrong.** The import fix is complete. The blocker is a second-order consequence of A-30's new *first* rule, which I verified by measurement: making "no MDE ⇒ UNPOWERED" the pre-emptive test pins five of the design's reads — T3, T4, T5, the D1 ib_width sensitivity and the **entire CONFIRM pass** — to `UNPOWERED` regardless of their data, because the implementation only ever computes an MDE for T1 and T1_mirror.

**Executed (read-only):** `pytest python/tests/test_sigbar_absorb.py` → **38 passed** (coordinator reported 39 — see LOW-3); full suite minus the two pre-existing xena collection errors → **268 passed / 4 skipped**; `shasum -a 256` on INFR-020 `pins.json`; a 1,296-combination exhaustive sweep of `label_band`; a consumer trace of every `label_band` / `mde_info` call site; an import-side-effect test. **The screen was not run.**

---

### A. Pin re-hash

`shasum -a 256` on `python/experiments/INFR-020/results/pins.json` = `5f170b717e350fb7c0cf1647cd1b78fb88a1fa212ed50dce83ec1049af44f6c5` — **byte-exact**; all seven INFR-020 consumers, the INFR-017 trio, the INFR-018 registry and K-UNIFORM re-hashed by the passing frozen-inputs test. **MATCH.**

---

### B. Challenging the designer call — IMPRECISE

**Is IMPRECISE the right resolution? Yes. My WASH suggestion was wrong and the rejection reasoning is correct.**

I proposed WASH in run 13 on the strength of "CI spans zero ⇒ cannot distinguish". That reasoning ignored what WASH *does* in this design. WASH is not a neutral descriptor — §5 names it "the design's POWERED NULL cell", and under AMENDMENT-24 a powered null is exactly what contributes to closing CF-SIGAUC-001. Labelling a cell whose point estimate **exceeds its own resolution** as a powered null would let a large, unstable estimate argue "nothing is there". That is the B-5 overclaim the design forbids in terms ("T1 UNPOWERED is INCONCLUSIVE, never a null"), and it would have been a LOOSER change smuggled in under a NEUTRAL-looking label. The designer caught a real error in my recommendation.

**The stated mechanism is also correct, and it is the part that makes IMPRECISE a distinct state rather than a fudge.** `plant_mde_curve` adds a *constant* to every treated event, so the planted contrast has the arm's own dispersion and nothing more; a real effect concentrated in a few calendar days carries extra between-day variance that the day-clustered bootstrap sees but the plant never simulated. So `|effect| ≥ MDE` with a zero-spanning CI is a genuine physical state — "bigger than what a uniform effect of this size would need to be detectable, yet too lumpy to resolve" — not an arithmetic leftover. Giving it its own band, reading it as inconclusive in both directions, and pinning it to UNPOWERED's closure semantics is the correct treatment.

**Is NEUTRAL the correct direction? Yes.** The affected cells already resolved to UNPOWERED before the amendment, and UNPOWERED and IMPRECISE are identical under A-24 (neither blocks nor contributes). Nothing became easier or harder to claim; what changed is that the reading is now honest about *why* the cell is inconclusive. The counterfactual — my WASH proposal — would have been LOOSER, and A-30 forecloses it. Ledger checks out: 4L/15T/10N + N = **4L/15T/11N**; sequence …A-27 L → A-28 N → A-29 L → A-30 N; **no LOOSER streak ≥ 3**.

**Does adding a band exceed what a post-measurement amendment may do? No, on three grounds.** (i) It defines a region that was previously *undefined* — it does not redraw a boundary between two existing bands, so no cell moves from a claim to a non-claim or back. (ii) It is non-contributing in both directions, so it cannot manufacture either a positive or a family close. (iii) It provably cannot touch run 1: D1's readings sit at WASH for every MDE down to ~2, far below the centred value, so no previously-seen result changes label. That last point is the decisive legitimacy test for a post-measurement change and it holds.

**Downstream consumers of the band string: none break.** I grepped the repository — no `.py` or `.md` outside `absorb.py` and this review file consumes `SUPPORTED`/`SUGGESTIVE`/`WASH`/`CONTRADICTED`/`UNPOWERED` as literals; `screen.md` and the analyst artifacts do not exist yet, so they will be written against the six-value table. The closure logic in §6.3 / A-24 is operator-executed prose, and A-30 states the IMPRECISE ⇒ non-contributing rule inside §5 where that reader will find it. The one thing to carry forward: whoever writes `screen.md` and the analyst prompt must enumerate **six** bands, not five.

---

### C. Blocker — the new first rule pins five reads to UNPOWERED

**Issue 1 (MAJOR).** §5's rewritten table opens with `UNPOWERED: MDE unavailable at the realised n, or no CI (tested FIRST)`, and `label_band` implements it faithfully as a pre-emptive early return. But `mde_for_arm` (`absorb_screen.py:300–323`) computes `plant_mde_curve` for **T1 and T1_mirror only**. Every other labelled contrast is called with `mde=None`:

| Read | Call site | MDE supplied? | Label under A-30 |
|---|---|---|---|
| T4 matched-random (**soil leg ii**) | `absorb_screen.py:646` `label_band(stat, ci, None)` | no | **always UNPOWERED** |
| T5 bare-level touch | `:701` `label_band(…, None)` | no | **always UNPOWERED** |
| T3 mid-range (**leg (i)'s "T3 ≈ 0"**) | `:720` `mde_info=None` | no | **always UNPOWERED** |
| D1 ib_width sensitivity | `:740` `mde_info=None` | no | **always UNPOWERED** |
| **CONFIRM T1 / T1_mirror** (the design's one verification pass) | `:934` `mde_info=None` | no | **always UNPOWERED** |

**Measured on the real `label_band`:**

| Input | Pre-A-30 (run-13 code) | Now |
|---|---|---|
| T4 clearly positive, effect +6.0, CI [3.0, 9.0], mde None | SUGGESTIVE | **UNPOWERED** |
| T4 clearly negative, effect −6.0, CI [−9.0, −3.0], mde None | CONTRADICTED | **UNPOWERED** |
| CONFIRM T1 positive, effect +8.0, CI [2.0, 14.0], mde None | SUGGESTIVE | **UNPOWERED** |
| the same three triples with `mde = 5.0` | — | SUPPORTED / CONTRADICTED / SUPPORTED |

**Why this blocks.** Three separate things break. (a) §5 now contains clauses its own table makes unreachable: "T4 SUPPORTED with T1 WASH ⇒ …" and "T5 SUPPORTED with T1 WASH ⇒ …" describe outcomes that cannot occur. (b) `CONTRADICTED: ci_high < 0` carries no MDE term anywhere in §5, yet a T4 or CONFIRM contrast whose interval lies wholly below zero is now reported as "not tested" — an affirmatively false statement about a measured cell, and the same error class as the run-13 blocker, reappearing at a different input. (c) The CONFIRM pass exists to verify DESIGN once (§0, §5 time-stability, §9 step 6); it now emits no usable band on any pair. This is the pre-existing R-7 residual escalated from "reads SUGGESTIVE at best" (a LOW) to "reads UNPOWERED always" (structural), because UNPOWERED is the label with governance weight under §6.3 and A-24.

**The design already requires the missing piece.** §4.2 mandates a `bite/MDE` line for every control, explicitly including `matched_random_timing` — *"MDE in CONTRAST UNITS (bps), published before the real read"* (design line 402) — and `bare_level_touch` (line 416). So the gap is an implementation gap, not a design one: T4 and T5 were always supposed to carry their own MDE curves.

**Required:** extend `mde_for_arm` (or add the equivalent) to publish MDE curves for the T4 and T5 contrasts before their reads, per §4.2, and supply an MDE to the CONFIRM and T3 layer calls — or, if the designer prefers, add an explicit §5 clause defining the label for a contrast that legitimately has no MDE, so that `CONTRADICTED` and `SUGGESTIVE` remain reachable there. The first route is the one §4.2 already asks for.

---

### D. Exhaustiveness of `label_band` — 1,296-combination sweep

Swept 12 effect values × 12 CI shapes × 9 MDE values (including `None`, `NaN`, `±inf`, `0`, negatives, `1e-9`, `1e9`, malformed and inverted intervals).

- **Every label returned is one of the six defined bands** — `{UNPOWERED 891, IMPRECISE 145, WASH 80, SUPPORTED 58, CONTRADICTED 45, SUGGESTIVE 32}`. No `None`, no empty string, no undefined value.
- **Boundary semantics correct and symmetric:** `|effect| = MDE` with a zero-spanning CI → IMPRECISE; `|effect|` a hair below → WASH; `ci_low = 0` exactly is treated as spanning zero (consistent with `excludes_zero = ci[0] > 0 or ci[1] < 0` used elsewhere); `mde = 0.0` with a zero-spanning CI → IMPRECISE, which is right (an arm that resolves any positive effect, showing one, that still cannot exclude zero).
- **One exhaustiveness gap (LOW-2):** 45 of 1,296 combinations **raise `TypeError`** rather than returning a band — all of them `ci = [None, None]` with a finite MDE (`'<' not supported between instances of 'NoneType' and 'int'`). Not reachable from `contrast_day_clustered`, which builds `ci` from `block_bootstrap_ci` as floats, and `NaN` bounds are handled without raising. But the "no input yields an undefined label" claim in `test_label_band_imprecise_cell_is_not_a_null` is not literally true, and its own sweep does not cover `None`-valued interval bounds.

---

### E. Import side effect — closed

`OUT.mkdir` is gone from module scope. Directory creation now happens in `_emit` (`absorb_screen.py:62`, on write) and once directly in `step_design_reads` (`:487`) immediately before the `tripwire.json` reset `write_text`. **Verified by execution:** importing `absorb_screen` in a fresh interpreter leaves `results/` absent. No `mkdir`, `write_text` or `write_parquet` remains at module scope in either `absorb_screen.py` or `absorb.py`. The tree is currently clean — `results/` does not exist. Complete.

---

### F. New-defect sweep on these edits (seventh pass)

| Risk | Check | Result |
|---|---|---|
| Restructured `label_band` changes an existing label | diffed all six branches against the run-13 behaviour across the sweep | **One change, and it is Issue 1** — every `mde=None` input moved from SUGGESTIVE/CONTRADICTED to UNPOWERED. All `mde`-present labels are unchanged. |
| IMPRECISE leaks into a positive claim | soil legs read `SUPPORTED` (leg i) and `excludes_zero` (leg ii) | **OK** — IMPRECISE satisfies neither |
| IMPRECISE contributes to a close | §5 pins it to UNPOWERED's A-24 semantics | **OK** — stated in the design, operator-executed |
| Duplicated `mde is None` guard | two consecutive guards at the top of `label_band`, the first now subsumed by the second | **Dead code, harmless** — LOW-1 |
| Band string breaks a consumer | repo-wide grep for the five old literals | **OK** — no consumer outside `absorb.py` |
| A-29's centring regressed | `plant_mde_curve` untouched this pass | **OK** |
| §9 order | `mde_for_arm` (`522`, `525`) → `_emit(mde_curves.json)` (`528`) → `calibrate_cf_star` (`540`) → `_emit(tripwire_cf_<pair>.json)` (`548`) → first contrast `_layers_for_events` (`586`) → `_run_tripwire` (`745`) | **OK — holds** |

---

### G. Standing battery

All **OK**: INFR-020 pins byte-exact; GT-1…GT-4 executed and passing against designer-pinned `gt_output.json`; GT-5(a)–(l) complete; shared LTF import boundary intact; P_WIDE p25 leg plus strictly-tighter τ (A-26); holdout sealed and DESIGN/CONFIRM only; causal ≤ t−1; D6.3 1-minute paths; COMPLETE-window fence; L-28 derangements; no local accounting; T4 matched-random donor resolution (run-11 fix) intact; A-25/27/28 fixes in place; CF\* refuses non-positive plants and never substitutes the 0.25 prior; `survives: None` when the gate is inapplicable; L-23 ledger 4L/15T/11N with no streak.

**Residuals:** R-1, R-2 superseded. R-3, R-4, R-5, R-6, R-8, R-9 stand. **R-7 is superseded by Issue 1** — the "T4/T5 label with `mde=None`" residual is no longer a disclosure nit but a structural mislabel, and closing Issue 1 closes R-7 outright. Run-11 N-1/N-2/N-3 stand. The bite remains a report layer with no code-level enforcement despite §7 listing it as HARD.

**LOW-1** — dead guard: `if mde is None and (ci is None or len(ci) < 2): return "UNPOWERED"` is fully subsumed by the next line. Harmless, but it is the kind of leftover that makes the next reader mis-trace the table.
**LOW-2** — `label_band` raises on `ci = [None, None]` (§D). Unreachable today; the exhaustiveness test should cover it.
**LOW-3** — test count: the suite collects **38** absorb tests, not the 39 reported. Overall 268 passed / 4 skipped matches.

---

### H. Verdict

**REVISE** — the band work is right; one implementation gap it exposed must be closed first.

I asked for a label for the undefined cell and suggested WASH; the designer rejected that and was correct to. WASH is the powered-null cell, so my suggestion would have let a point estimate that exceeds its own resolution argue for closing CF-SIGAUC-001 — the B-5 overclaim, and a LOOSER change wearing a neutral label. `IMPRECISE` is the right resolution, its constant-shift-plant mechanism is a real physical state rather than an arithmetic patch, NEUTRAL is the right direction, the ledger is correct at 4L/15T/11N with no streak, and introducing it post-measurement is legitimate because it defines a previously undefined region, contributes in neither direction, and provably cannot move run 1's readings. The import side effect is fully closed — verified by importing the runner and finding `results/` still absent. `label_band` returns one of the six defined bands across all 1,296 swept combinations, with correct and symmetric boundary behaviour.

What blocks the re-run is the new *first* rule. "MDE unavailable ⇒ UNPOWERED, tested first" is sound in isolation, but the implementation supplies an MDE only to T1 and T1_mirror, so T3, T4, T5, the D1 sensitivity and every CONFIRM contrast are now pinned to UNPOWERED whatever the data says. Measured: a T4 with CI [3.0, 9.0] reads UNPOWERED, and one with CI [−9.0, −3.0] reads UNPOWERED rather than CONTRADICTED — which §5 defines with no MDE term at all. That makes soil leg (ii) unlabelable, renders §5's own "T4 SUPPORTED with T1 WASH" clause unreachable, and voids the verification pass the design runs CONFIRM for. §4.2 already mandates an MDE for `matched_random_timing` and `bare_level_touch`, so the fix is to publish the curves the design has always asked for rather than to weaken the new rule.

Route to **experiment-developer** (MDE curves for T4/T5, and an MDE for the CONFIRM and T3 layer calls), with a **quant-designer** confirmation if the alternative route — an explicit §5 clause for legitimately MDE-less contrasts — is preferred instead. Then a fresh-context QA run 15 and the operator's re-run gate.

**QA does not launch the screen. Nothing committed.**

---

## QA run 15 — 2026-07-22T03:19:37Z — mode: subagent (fresh context) — HEAD `99f1a5537f9f37ca459d07f7f0a0bdf8a89e9807`

**Stage:** re-review after operator option A: AMENDMENT-31 ordering correction, T4/T5 and
missing-arm MDE publication, constant-shift MDE optimization, immutable bar/control reuse, and
isolated `--smoke`. Fresh-context subagent; did **not** author the changes. Full `--execute` was
not approved and was **not run**.

**Verdict: REVISE**
**FAILING_ARTIFACT:** `python/experiments/SPDR-009/screen_code/absorb_screen.py`
**REQUIRED_SKILL:** `experiment-developer` (time-stability/CONFIRM/T2 plant fidelity), with
`quant-designer` only if §9 is intentionally meant to permit per-pair rather than global MDE
publication.

**Reviewed git state (`git status --porcelain`):**
```
 M docs/experiments-docs/INDEX.md
 M docs/experiments-docs/checkpoints/2026-07-21-015-signed-value-absorption-screen/design.md
 M docs/signal-registry/candidate-families/cf-sigauc-001.md
 M python/experiments/SPDR-009/design.md
 M python/experiments/SPDR-009/qa-review.md
?? python/experiments/SPDR-009/screen_code/
?? python/src/xen/sigbar/absorb.py
?? python/tests/test_sigbar_absorb.py
```

**Executed:** focused suite `pytest python/tests/test_sigbar_absorb.py -q` -> **40 passed**;
INFR-020 pin re-hash -> exact `5f170b717e350fb7c0cf1647cd1b78fb88a1fa212ed50dce83ec1049af44f6c5`;
inspection of the completed isolated smoke at `/private/tmp/spdr009-smoke-nm4_g9tu`.
`python/experiments/SPDR-009/results` is **absent**. No production screen execution.

### Design-fidelity trace

| Design clause (§ref) | Code (file:line) | Verdict | Notes |
|---|---|---|---|
| §5 / A-31 band order | `absorb.py:1433-1475` | **MATCHES** | Invalid CI first; negative CI -> CONTRADICTED before MDE; positive CI + missing MDE -> SUGGESTIVE; zero-spanning + missing MDE -> UNPOWERED. Malformed/None bounds return UNPOWERED. |
| §4.2 T4 matched-random MDE | `absorb_screen.py:355-418,462-493,714-787,857-867` | **MATCHES** | Donor arm built once; exact rows reused by MDE and read. T4 uses the registered global control mean on treated days for both computations. Smoke emits H5/H10 MDE 5.5/4.5 bps. |
| §4.2 T5 bare-level MDE | `absorb_screen.py:420-459,778-780,869-894` | **MATCHES** | Bare arm built once; exact rows reused. Smoke emits H5/H10 MDE 4.0/8.5 bps. |
| §4.2/§5 T3 and D1 sensitivity MDE | `absorb_screen.py:787-793,896-919` | **MATCHES** | T3 and D1 sensitivity receive their own same-arm T1/T1-mirror curves. Smoke T3 is explicitly underivable at n=24; D1 sensitivity has finite H5/H10 curves. |
| §5/§9 CONFIRM MDE | `absorb_screen.py:1091-1132` | **MATCHES for implemented reads** | CONFIRM T1/T1-mirror curves are written before `_layers_for_events`; smoke has finite H5/H10 MDE and WASH labels. See Issue 2: the verification pass itself is incomplete. |
| §4.2 MDE is arm resolution, not observed edge | `absorb.py:1364-1430` | **MATCHES** | Arm is centred once on its observed contrast; fixed-seed mean bootstrap is translation-equivariant, so adding `u` to the centred lower bound is mathematically identical to rerunning each constant plant. Regression compares against explicit grid sweep and asserts two bootstrap calls. |
| §4.2/§9 immutable population identity | `absorb_screen.py:677-780,841-894` | **MATCHES** | Polars frames in `bars_by`, event arms, and control frames are immutable; controls are constructed before MDE and reused without rebuild for the read. |
| §9 MDE publication before contrast | `absorb_screen.py:672-935` | **DEVIATES (literal global order)** | Each pair's curves/CF* are published before that pair's first read, but D1 real contrasts run before D2-D4 curves exist. Earlier QA accepted this as contamination-safe; literal §9 step 5 says all “MDE curves before any contrast.” See Issue 4. |
| §5 time stability / L-24 F02 | no implementation (`rg` finds no `third`/`chronological` path) | **MISSING** | No T1-T5 read is repeated on the three DESIGN thirds; no per-third n/sign output exists. See Issue 1. |
| §5/§9 “every read” on CONFIRM | `absorb_screen.py:1091-1132` | **MISSING** | CONFIRM emits T1, mirror, T2 and floor only; T3/T4/T5 controls are absent and population is capped at first 40 symbols without a design declaration. See Issue 2. |
| §4.2 signed-score control plant/MDE | `absorb_screen.py:496-547` | **DEVIATES** | `mde_rho_p95/p05` are quantiles of the derangement null, not the predeclared synthetic monotone score->return plant curve. See Issue 3. |
| §7 hard fences | `absorb.py` fences + focused tests | **MATCHES** | DESIGN/CONFIRM only; TEST/holdout unreachable; causal next-open; 1-minute path; COMPLETE windows; derangements; no local accounting all pass. |
| §10 A-25...A-31 ledger | `design.md:1054-1183` | **MATCHES** | A-31 correctly booked LOOSER because MDE-less positive CI moves UNPOWERED -> SUGGESTIVE. Count 5L/15T/11N; post-measurement sequence T,T,L,N,L,N,L has no LOOSER streak >=3. |

### Golden-trace diff

Focused tests executed GT-1...GT-4 against designer-pinned `design_derivations/gt_output.json`:

| Event | Design expectation | Implemented result | Verdict |
|---|---|---|---|
| GT-1 SOL 2022-12-28 03:27 | S9, pinned entry/side/H5/H10 | exact arm/timestamp; returns within pinned tolerance | **MATCHES** |
| GT-2 SOL 2022-12-29 01:24 | S9 from prior-session level | exact arm/prior-session provenance/returns | **MATCHES** |
| GT-3 SOL 2022-12-26 23:34 | MIRROR sign guard | MIRROR, not magnitude-only S9 | **MATCHES** |
| GT-4 SOL 2022-11-12 22:08 | BASE at signed-score boundary | BASE | **MATCHES** |
| GT-5(a)-(l) | each forbidden path raises/refuses | dedicated focused tests pass | **MATCHES** |

### Governance & boundary

| Check | Evidence | Verdict |
|---|---|---|
| Frozen inputs | INFR-020 pins and seven consumers re-hashed by focused tests; manifest hash independently exact | **PASS** |
| No local accounting | focused `check_no_local_accounting` test | **PASS** |
| Holdout / TEST | only DESIGN and CONFIRM accepted; holdout constant sealed | **PASS** |
| Causality / real-price / 1-minute path | next-LTF-open entry; 1-minute outcome and level construction; focused fence tests | **PASS** |
| L-28 derangement | global, within-symbol and path-swap zero-fixed-point assertions/tests | **PASS** |
| Isolated smoke semantics | `--smoke` forces a new `/private/tmp/spdr009-smoke-*`, refuses combination with `--execute`, then returns before production completion | **PASS** |
| Isolated smoke evidence | `smoke_integrity.json: passed=true`; P/P_WIDE/T3/CONFIRM nonempty; T4/T5 donors, T2 derangement, CF* status and path-swap donors present; census reconciles | **PASS** |
| No result contamination | `python/experiments/SPDR-009/results` absent after tests and smoke inspection | **PASS** |
| Smoke regression strength | integrity assertion checks donors/nonempty paths but does not assert T4/T5/T3/sensitivity/CONFIRM MDE artifact keys or publication order | **RESIDUAL** |
| Full execution gate | operator did not approve `--execute`; it was not run | **PASS** |

### Issues

1. **MAJOR — the mandatory time-stability read is absent.**
   **Design:** §5 lines 549-550; L-24 F02; §4.2 derangement mitigation. **Code:** no
   chronological-third split or output anywhere in `absorb_screen.py`/`absorb.py`.
   **Impact:** a concentrated effect can receive the pooled label without the three-third n/sign
   evidence the design requires, and the declared mitigation for the global derangement is not
   delivered. **Required:** emit T1-T5 (including T2) by all three DESIGN thirds with per-third n
   and sign/interval; retain pooled as declared.

2. **MAJOR — CONFIRM is not the registered “every read once” verification and changes the population.**
   **Design:** §5 lines 549-550; §9 lines 870-872. **Code:** `step_confirm` lines 1105-1129.
   It takes `u["usable"][:40]` and runs only `_layers_for_events` (T1, mirror, T2, floor), omitting
   T3, T4 and T5 plus their controls. The first-40 cap is not declared and is not guaranteed to
   represent the DESIGN pooled cross-section. **Required:** run the complete registered CONFIRM
   battery on the declared population, or amend the design before execution to name the reduced
   verification estimands and population with direction/count.

3. **MAJOR — T2's required planted bite/MDE is not implemented.**
   **Design:** §4.2 lines 387-388 requires a known synthetic monotone score->return plant and an
   MDE published before the read. **Code:** `_t2_dose` lines 507-545 only deranges observed scores
   and calls the null p95/p05 `mde_rho_*`; no known effect is planted and nothing is prepublished.
   **Required:** implement/publish the registered monotone plant curve before T2, or amend §4.2 to
   define the null critical values as the intended power instrument.

4. **MEDIUM — §9's global publication sentence and the runner's per-pair schedule disagree.**
   The current order is scientifically contamination-safe: every pair uses deterministic curves
   written before its own first real contrast, and exact frame identity holds. But literal §9 step
   5 says all MDE curves precede *any* contrast. **Required:** either split `step_design_reads` into
   all-pair build/control/MDE publication then all-pair reads, or amend §9 explicitly to say
   “per pair, before that pair's first contrast.”

### Residuals

- The smoke is genuinely isolated and its retained artifacts directly show the new MDE wiring,
  but `assert_smoke_integrity` would still pass if those MDE keys disappeared while donors stayed
  nonempty. Add assertions for T4/T5 curve keys, T3/sensitivity explicit derived-or-underivable
  state, CONFIRM curve keys, and label presence.
- Prior disclosed items remain: T5 first-30 and spread-route first-20 caps; conservative
  `n_symbols_read`; T4 donor drop count/weighting; bare-touch tie-break; P_WIDE p25 not serialized;
  GT-5(e) wording; bite hard status remains operator-enforced rather than code-enforced.

### Verdict

**REVISE.** The option-A fixes themselves are correct: band ordering is exhaustive and safe,
T4/T5/T3/D1-sensitivity/CONFIRM MDE wiring is present, the one-bootstrap constant-shift result is
exact for this fixed-seed mean bootstrap, the same immutable frames feed MDE and read, the focused
suite passes 40 tests, and the isolated smoke leaves the real results tree absent. The re-run is
still blocked by three previously missed design-fidelity gaps: no chronological-third reads,
an incomplete/capped CONFIRM pass, and no planted T2 MDE. Resolve those plus the §9 wording/order
before returning to the operator execution gate.

**QA does not launch the screen. Nothing committed.**

---

## QA run 16 — 2026-07-22T03:43:28Z — mode: subagent (fresh context) — HEAD `99f1a5537f9f37ca459d07f7f0a0bdf8a89e9807`

**Stage:** re-review after QA run 15 fixes: chronological-third reporting, uncapped complete
T1–T5 CONFIRM controls, the registered T2 monotone plant, A-33 per-pair MDE publication wording,
and strengthened isolated-smoke assertions. Fresh-context subagent; did **not** author the changes.
Full `--execute` was not approved and was **not run**.

**Verdict: REVISE**
**FAILING_ARTIFACT:** `python/experiments/SPDR-009/screen_code/absorb_screen.py`
**REQUIRED_SKILL:** `experiment-developer` (complete the registered time-stability strata and
CONFIRM sensitivity), with `quant-designer` only if the intended scope is narrower than the live
§4.1/§5 registration.

**Reviewed git state (`git status --porcelain`):**
```
 M docs/experiments-docs/INDEX.md
 M docs/experiments-docs/checkpoints/2026-07-21-015-signed-value-absorption-screen/design.md
 M docs/signal-registry/candidate-families/cf-sigauc-001.md
 M python/experiments/SPDR-009/design.md
 M python/experiments/SPDR-009/qa-review.md
?? python/experiments/SPDR-009/screen_code/
?? python/src/xen/sigbar/absorb.py
?? python/tests/test_sigbar_absorb.py
```

**Evidence:** independently reran the focused suite -> **41 passed**; inspected the completed
isolated smoke at `/private/tmp/spdr009-smoke-tv3h50qc` -> `smoke_integrity.json` reports **56/56
checks true** and `passed=true`; coordinator supplied the isolated full-suite result **271 passed /
4 skipped**. `python/experiments/SPDR-009/results` remains **absent**. No production screen execution.

### QA-15 closure trace

| QA-15 requirement | Code / artifact | Verdict | Notes |
|---|---|---|---|
| T1–T5 on chronological thirds with n/sign/interval | `absorb_screen.py:729-854,1112-1117`; smoke `layers.json` | **PARTIAL / BLOCKING** | P emits three ordered equal-count slices and all T1–T5 reads. P_WIDE emits none, despite being a registered primary pool/stratum (§4.1). See Issue 1. |
| Complete uncapped CONFIRM battery/population | `absorb_screen.py:1283-1417`; smoke `layers_CONFIRM.json` | **PARTIAL / BLOCKING** | The prior first-40 cap is gone and all usable symbols feed P/P_WIDE/T3 plus T4/T5 controls. The registered D1 ib-width sensitivity read is still omitted. See Issue 2. |
| Genuine planted T2 MDE before read | `absorb.py:1303-1452`; `absorb_screen.py:312-344,647-686,1362-1382` | **MATCHES** | Deterministic Spearman centring; 0–30 bps/score-SD in 0.5-bps steps; 200 zero-fixed-point derangements; first plant clearing p95 and p<=0.05; both bps and rho published before the pair's read. Real T2 remains a separate derangement battery. |
| Per-pair §9 publication order | `design.md:869-878,1193-1198`; runner module/step docstrings and pair loop | **MATCHES** | A-33 now states the implemented contamination-safe rule: every pair's immutable curves precede that pair's first contrast; earlier pairs cannot adapt later inputs. |

### Adversarial review

| Check | Result |
|---|---|
| A-31 label order and complete MDE wiring | **PASS** — negative intervals remain CONTRADICTED before the MDE gate; positive missing-MDE intervals are only SUGGESTIVE; zero-spanning cells need an MDE. T1/mirror/T2/T3/T4/T5 and D1 DESIGN sensitivity have explicit curve state. |
| A-32 plant fidelity | **PASS** — the published T2 quantity is now a planted resolution, not a renamed null quantile. Finite guards and exact zero-fixed-point assertions remain in the real and planted paths. |
| A-33 wording/code consistency | **PASS** — live §9 and runner both say per pair. |
| A-31–A-33 ledger | **PASS** — directions L/L/N; running count **6L/15T/12N**; sequence A-27 L, A-28 N, A-29 L, A-30 N, A-31 L, A-32 L, A-33 N has no LOOSER streak >=3. |
| Constant-shift MDE optimization / frame reuse | **PASS** — translation-equivalent lower-bound transform is regression-tested against the explicit grid; immutable event/control frames feed both curve and read. |
| Smoke strength | **IMPROVED, BUT MISSES THE BLOCKERS** — labels, T2/T4/T5 MDEs, T3/sensitivity state, CONFIRM labels/T2 MDE, CF*, donors and path swap are asserted. `DESIGN_thirds_present` checks only that one P object has length three, and no assertion requires P_WIDE thirds or D1 sensitivity on CONFIRM. |
| Output schemas | **PASS except Issues 1–2** — P/P_WIDE/T3/T4/T5 MDE/label objects and CONFIRM event files are explicit; the absent strata are not represented as explicit underivable states. |
| Hard fences | **PASS** — DESIGN/CONFIRM only; TEST/holdout inaccessible; causal next-LTF-open entries; 1-minute level/outcome paths; COMPLETE-window fence; L-28 derangements; shared LTF construction; no local accounting. |

### Issues

1. **MAJOR — time stability omits an entire registered primary pool and does not publish one
   common third definition.** §4.1 declares `pool {P, P_WIDE} × chronological third` and §5 says
   every read is repeated on the three DESIGN thirds. `_time_stability_thirds` accepts only `ev_p`
   and P controls (`absorb_screen.py:765-771`), and its only caller supplies `controls["P"]`
   (`:1112-1117`). The smoke makes the omission concrete: `pairs.D1.time_stability_thirds` contains
   only `n_P`, while `pairs.D1.P_WIDE` has no thirds object. The implementation also cuts P and T3
   independently by event rank (`:780-790`), so “third 1” is not serialized as one reusable DESIGN
   time interval. A regime-instability read can therefore be reported for P while the equally
   primary P_WIDE cell has no mitigation, and consumers cannot prove that P/T3 slices refer to the
   same chronological band. **Required:** freeze and publish three disjoint chronological DESIGN
   boundaries once per pair; apply them to P, P_WIDE, T3 and their source-matched controls; emit
   T1–T5 for both registered pools with per-third n, sign and available interval (explicit
   UNPOWERED state where an interval cannot be derived); assert both pools and shared boundaries in
   smoke/tests.

2. **MAJOR — CONFIRM still omits the registered D1 ib-width sensitivity read.** §3.2 says the D1
   `0.25 × ib_width` sensitivity is emitted alongside; §5 names it beside every null and then says
   **every read** is repeated once on CONFIRM. DESIGN constructs and reads it at
   `absorb_screen.py:1101-1110`, but `step_confirm` builds only P, P_WIDE and MID_RANGE
   (`:1307-1321`) and emits only those blocks (`:1362-1410`). The uncapped T1–T5 P/P_WIDE core is
   now complete, so this is no longer QA-15's population/control defect; it is the remaining
   registered sensitivity stratum. **Required:** build the count-frozen D1 ib-width event arm on
   CONFIRM, publish its MDE state before its read, emit its registered layers, and require it in
   smoke; or amend §3.2/§5 before execution with direction/count if the sensitivity was intentionally
   DESIGN-only.

### Verdict

**REVISE.** QA-15's most serious implementation defects are closed: CONFIRM is uncapped and runs
T1–T5 for P/P_WIDE plus T3; T2 now has a genuine pre-read monotone plant; A-33 makes the per-pair
schedule literal; 41 focused tests and the 56-check isolated smoke pass; hard fences remain intact;
and the official results tree is absent. Execution is still blocked because the time-stability
report omits all P_WIDE primary cells and does not serialize shared DESIGN-third boundaries, while
CONFIRM omits the registered D1 ib-width sensitivity. Close those two fidelity gaps, strengthen the
smoke assertions accordingly, then return for fresh-context QA before any production run.

**QA does not launch the screen. Nothing committed.**

---

## QA run 17 — 2026-07-22T03:57:03Z — mode: subagent (fresh context) — HEAD `99f1a5537f9f37ca459d07f7f0a0bdf8a89e9807`

**Stage:** re-review after QA run 16 fixes: one serialized equal-duration DESIGN-boundary set
per pair applied to P, P_WIDE, T3 and source-linked controls; complete T1–T5 third reporting for
both pools; and uncapped D1 ib-width sensitivity on CONFIRM. Fresh-context subagent; did **not**
author the changes. Full `--execute` was not approved and was **not run**.

**Verdict: APPROVE**

**Reviewed git state (`git status --porcelain`):**
```
 M docs/experiments-docs/INDEX.md
 M docs/experiments-docs/checkpoints/2026-07-21-015-signed-value-absorption-screen/design.md
 M docs/signal-registry/candidate-families/cf-sigauc-001.md
 M python/experiments/SPDR-009/design.md
 M python/experiments/SPDR-009/qa-review.md
?? python/experiments/SPDR-009/screen_code/
?? python/src/xen/sigbar/absorb.py
?? python/tests/test_sigbar_absorb.py
```

**Evidence:** focused suite `pytest ... test_sigbar_absorb.py -q` -> **41 passed**; broader suite
excluding the two pre-existing xena import-collection failures -> **271 passed / 4 skipped**;
inspected isolated smoke `/private/tmp/spdr009-smoke-dl0fgizs` -> `smoke_integrity.json`
**62/62 checks true**, `passed=true`. Official `python/experiments/SPDR-009/results` is absent.
No production screen execution.

### QA-16 closure trace

| QA-16 requirement | Code / artifact | Verdict | Notes |
|---|---|---|---|
| One immutable, serialized equal-duration DESIGN-boundary set per pair | `absorb_screen.py:729-746,1120-1129`; smoke `layers.json` | **MATCHES** | `_design_third_boundaries` derives three disjoint `[start,end)` intervals once from the frozen DESIGN fence. The same tuple list is serialized once under each pair and passed unchanged to both pool reads. Smoke emits exact thirds ending `2022-01-18 12:35:20`, `2022-08-09 18:17:40`, `2023-03-01 00:00:00`. |
| Same boundaries on P, P_WIDE and T3 | `absorb_screen.py:738-746,773-849,1131-1144` | **MATCHES** | P and P_WIDE are sliced by the shared `entry_ts` intervals. The same `ev_mid` T3 population is sliced by those same boundaries inside both pool reports; no independent event-rank thirds remain. |
| Source-matched T4/T5 controls use the same thirds | `absorb_screen.py:749-758,799-837`; `absorb.py:1040-1100,1782-1973` | **MATCHES** | Matched-random and bare-touch rows retain `src_event_ts`; every third filters donors to source events in that exact pool/time slice before T4/T5. Controls are built once and reused. |
| T1–T5 with n, sign and available interval for both pools | `absorb_screen.py:761-865`; smoke `layers.json` | **MATCHES** | Each pool has exactly three records and 12 keys (`T1`, mirror, `T2`, `T3`, `T4`, `T5` × H5/H10). Every record carries pool/T3 n; each read carries its arm n, explicit sign, and CI/derangement interval when derivable or an explicit `UNPOWERED` state otherwise. Smoke: P and P_WIDE each have all three thirds and all 12 reads. |
| Uncapped D1 ib-width sensitivity on CONFIRM | `absorb_screen.py:1322-1370,1386-1437,1466-1478`; smoke `layers_CONFIRM.json` | **MATCHES** | The loop uses all `u["usable"]`; no first-N cap. D1 `0.25 × ib_width` events are built on CONFIRM, their realised-n MDE is emitted before the read, and labelled T1/T1-mirror/T2 layers are written. Smoke: **n=388**, S9=52, H5/H10 labels WASH, MDE 5/7 bps. |
| Smoke regression covers both blockers | `absorb_screen.py:1517-1613`; smoke `smoke_integrity.json` | **MATCHES** | Requires the shared serialized boundaries, complete P and P_WIDE thirds with exact T1–T5 schemas, plus nonempty and explicit-MDE D1 CONFIRM sensitivity. All checks pass. |

### Standing fidelity and governance recheck

| Check | Evidence | Verdict |
|---|---|---|
| T2 planted MDE | `absorb.py:1303-1452`; focused tests | **PASS** — deterministic Spearman centring; registered 0–30 bps/score-SD grid; zero-fixed-point plant derangements; real read remains separate. |
| A-31 band order | `absorb.py:1585-1627`; exhaustive focused test | **PASS** — invalid CI first, CONTRADICTED before MDE, positive missing-MDE SUGGESTIVE, zero-spanning missing-MDE UNPOWERED, WASH/IMPRECISE exhaustive. |
| A-31–A-33 ledger | `design.md` §10 | **PASS** — directions L/L/N; total **6L/15T/12N**; no LOOSER streak >=3. |
| Per-pair publication order / immutable arms | `design.md` §9/A-33; `absorb_screen.py:947-1045,1412-1437` | **PASS** — all curves for a pair precede that pair's first contrast; exact event/control frames are reused and earlier pairs cannot adapt later inputs. |
| Band / holdout / causal fences | `fences.py:37-140`; `ltf.py:297-460,645+`; focused tests | **PASS** — DESIGN/CONFIRM only; TEST/holdout inaccessible; next-LTF-open entry; COMPLETE windows; 1-minute levels/outcomes; formed-time and IB availability guards. |
| Derangement / tripwire / accounting | `absorb.py` controls and fixed-H path swap; focused tests | **PASS** — zero fixed points asserted; bite and CF* states explicit; `check_no_local_accounting` passes. |
| Output schema / smoke assertions | isolated smoke, 62 checks | **PASS** — P/P_WIDE/T3/control/CONFIRM paths, MDE states, labels, census reconciliation and tripwire donors are explicit. |
| Performance safety | runner + shared helpers | **PASS** — each symbol's 1-minute bars are loaded once per band and reused across pools/controls; immutable Polars frames are sliced, not rebuilt; constant-shift MDE uses one bootstrap; T2 seed matrices and per-third loops are bounded. No sample, timing or denominator shortcut. |
| Official result isolation | filesystem check | **PASS** — `python/experiments/SPDR-009/results` absent; retained evidence is only under `/private/tmp/spdr009-smoke-dl0fgizs`. |

### Golden trace

Focused tests still execute GT-1…GT-4 against the designer-pinned output and all GT-5(a)–(l)
refusal paths. All pass. The run-17 edits are orchestration/reporting only and do not alter event,
arm, entry, outcome or fence logic.

### Residuals

- The nested P_WIDE third records retain the generic count key `n_P`; its enclosing `P_WIDE`
  object, `n_total`, and per-read arm counts make the population unambiguous. This is cosmetic and
  does not affect the registered n/sign/interval evidence.
- Prior disclosed, non-blocking implementation residuals remain as recorded in runs 15–16
  (T5/spread disclosure caps, conservative symbol-count wording, donor weighting/tie-break notes,
  and operator enforcement of the bite status). None is changed or made verdict-material here.

### Verdict

**APPROVE.** Both QA-16 blockers are closed. Each pair now publishes one reusable equal-duration
DESIGN time partition and applies it identically to P, P_WIDE, T3 and source-linked controls;
both registered pools emit complete T1–T5 n/sign/interval evidence. CONFIRM now runs the D1
ib-width sensitivity over the full usable population, publishes its MDE before the read, and emits
labelled layers. The focused 41-test suite, broader 271-test suite and 62-check isolated smoke all
pass; hard fences, A-31–A-33 governance, output schemas and performance safeguards remain intact;
the official results tree is absent.

Approval returns the item to the **operator execution gate** only. QA does not launch the screen.
Nothing committed.
