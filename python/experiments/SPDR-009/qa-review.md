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
