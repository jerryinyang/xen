# SPDR-008 — QA review (append-only)

## QA run 1 — 2026-07-21T11:19:48Z — mode: subagent — HEAD 53c9c3def03d91d64fcd21db476c5a1c1f9248aa
Verdict: **REVISE**

Reviewed git state: HEAD `53c9c3d` (clean); only untracked path `python/experiments/SPDR-008/`.
Stage: **DESIGN-STAGE QA** — no implementation code exists (only `design.md`); precedent SPDR-007
QA run 1 was a design-level REVISE before any code. The fidelity trace below is therefore
design → intent / source (`SIGNAL-SIGNED.md`) / governance, not design → code. Shared-code claims
in the design were verified against the actual modules.

### Design-fidelity trace

| Design clause (§ref) | Verified against | Verdict | Notes |
|---|---|---|---|
| Frozen pins: registry `5c386984`, baselines `1b7244c8`, column_pins `e3b9fd9b`, fence `35d3375e` (§0, §Frozen inputs) | `INFR-018/results/instrument_registry.json` `pin_sha256`; `fences.py` `BASELINES_SHA256`/`COLUMN_PINS_SHA256`/`FENCE_MANIFEST_SHA256`; `column_pins.json` | MATCHES | All four pins verified byte-prefix-exact. |
| Anchor A-USOPEN, IB L=15, δ=0, A6=D4-t50-w30 W=30, kernel K-UNIFORM (§0, §3.1) | registry `anchor.anchor_id`=A-USOPEN, `ib_minutes`=15; `a6_rule`=D4-t50-w30 τ=0.5 w=30 δ=0 q=30; `kernel.winner`=K-UNIFORM | MATCHES | Frozen params reproduced from the pin. |
| SpreadBps UNUSABLE; §2.5 regime UNAVAILABLE (§0, §6.1) | `column_pins.json` `W2_decision.stored_column_status`=UNUSABLE; `assert_frozen_inputs` raises if it changes | MATCHES | Spread handling routes to tick/flip-pair + SPREAD-SCALE-ROUTING. |
| PVA edges from `profile.poc_and_value_area(build_profile(prior_session_bars,"K-UNIFORM"),share=0.685)` (§3.1) | `profile.build_profile(bars,kernel,*,edges,weight_col="Volume")` and `profile.poc_and_value_area(edges,prof,share=0.685)` exist; default share 0.685 | MATCHES (with shorthand) | Functions exist and return `(poc, VAL_edge, VAH_edge)`. Design's inline call passes `build_profile`'s 2-tuple as one arg — designer shorthand; real call is `poc_and_value_area(edges, prof, share=0.685)`. Harmless at design stage. |
| `fences.assert_no_per_level_delta` guards card ban 2 (§7, GT-4d) | `fences.py:204`; `build_profile` calls it on `weight_col` (Volume) | MATCHES | Guard raises on any name containing delta/signed/buyvolume/sellvolume. |
| `check_no_local_accounting` (§7) | `xen/estimand_validation.py:385` | MATCHES | Primitive exists. |
| Uncertainty via `xen.evaluation.block_bootstrap_ci`; routing via `spread_scale_route`; floor via `bybit_round_trip_cost_bps` (§6) | `evaluation.py:55 / :457 / :419 / :398` | MATCHES | All cited helpers exist. |
| **Trap detection "reusing acceptance … exactly" AND "generalised `acceptance.find_pokes`" on PVA/PRIOR levels (§3.1, §9)** | `acceptance.find_pokes` / `evaluate_discriminator` are HARD-WIRED to `ib_high`/`ib_low` (poke thresholds and `close_beyond` both read the IB edge) | **DEVIATES** | See Issue 2. Shared apparatus is not level-agnostic as written; "exactly" and "generalised" conflict; generalisation mechanism + pin-preservation guard unspecified. |
| **`trap_load = side_sign × Σ delta_abs_resid` = "same-direction taker Δ" (§1, §3.2, §6.1)** | `delta_abs_resid` is the residual of **\|Δ\|** (magnitude); `acceptance.py:346-356` states it is "direction-free, so it cannot invert between sides"; measured direction lives in `delta_ratio_resid` (used by SPDR-007 signed by side) | **DEVIATES** | See Issue 1. The load's sign comes from price geometry (poke side), not measured flow. |
| CONVERSION-PIN block (§6.1) | design-requirements §9 mandates divisor object + **measured value** + resulting effect + cost floor | PARTIAL | See Issue 4 — the "measured value" (TRAIN-median `ib_width_bps`) line is absent. |
| Golden trace GT-1..GT-4 (§8) | design-requirements §7; SPDR-007 §8 precedent (every GT session concretely pinned) | PARTIAL | GT-1 + GT-4 concrete/cross-checkable; GT-2/GT-3 sessions unpinned. See Issue 3. |
| Mechanism / object-identity / bands / power / integrity-split blocks (§1,§2,§5,§6.3,§7) | design-requirements §1,2,5,6,8 | MATCHES | All present and filled. |
| Controls: trap_load_derangement, matched_unconditional, ordinary_touch + path-swap tripwire (§4.2,§4.3) | design-requirements §3,4; L-28 | MATCHES | Each carries DISJOINT/bite-MDE/non-vacuity/expected/disclosure/destroy-form; derangements asserted zero-fixed-point; B-6 symmetry stated where permutation-based. |
| Independence of boundary types (no cross-type pooling) (§0,§4,§4.1,§4.2) | operator direction 2026-07-21 | MATCHES | Strongly enforced: promote rule "within a single boundary type", controls drawn within-type, cross-type pooling barred as a headline. |
| P-01 discipline: T3 price-only = control only, S1 not re-run (§0,§4,§5) | card §5 P-01; pitfalls-ledger P-01 | MATCHES (but see Issue 1) | T3 non-promotable; signed-value verdict requires T1∧T2. Integrity of the *signed* facet depends on Issue 1. |

### Golden-trace diff

No implementation exists, so no numeric diff is possible this run. Assessing the **spec's**
readiness for a later diff:

- **GT-1** (BTCUSDT 2023-01-11 14:30Z) — concrete inputs, reused from SPDR-007 GT-3 (IB 17419.0/
  17372.0/47.0; poke 14:48 extreme 17426.0; closes-beyond 0.3667 < 0.50 ⇒ REJECT). Cross-checkable.
  Caveat: its status as a **TRAP** (i.e. that it reclaims inside within the window) is *asserted*,
  not shown — SPDR-007 only certified it as a REJECT. If it does not reclaim, GT-1 is not a trap
  and must be swapped.
- **GT-2** (DOWN branch) — session not pinned ("a DESIGN SOLUSDT session with a failed downside
  poke that reclaims"). Not independently derivable until `gt_derive.py` chooses one.
- **GT-3** (PVA + HIGH/LOW load pair; PRIOR alongside) — the **widening's core**, and the least
  concrete: neither symbol, current session, nor prior session is pinned. This is exactly the new
  code path (profile → value-area → prior-level poke → reclaim → tercile) that most needs an
  independent hand-derivation.
- **GT-4** (fence/hash/order raises) — concrete and complete; correctly requires raises (not warns)
  incl. (g) PVA/PRIOR computed from the current session ⇒ raise (causality).

Routing: see Issue 3.

### Governance & boundary

- **TRAIN-only fence** — `fences.assert_band` knows only DESIGN/CONFIRM; TEST (≥2023-12-18) and
  holdout (≥2025-01-08) raise. §0 band table + §7 HARD "raise not warn". PASS (by construction).
- **Causal ≤ t−1** — §2 + §7: trap load from poke bars ≤ reclaim_ts; PVA/PRIOR levels from the
  prior closed session; tercile cuts DESIGN-only; entry at OpenTime==reclaim_ts bar open. GT-4(e)/(g)
  raise on violation. PASS.
- **Future-destroy tripwire** — §4.3 reversal_path_swap: derangement (zero fixed points asserted),
  must-collapse on every material adjudicated read, material-edge precondition (inherited SPDR-007
  D-2), pooled positive-control bite corr>0.5. PASS.
- **No-per-level-Δ / no-local-accounting** — both HARD in §7; guards exist. PASS.
- **L-28 derangement** — trap_load_derangement and path-swap both DERANGEMENT, regenerated to
  exactly 0 fixed points, asserted; coverage drop+count. PASS.
- **L-03 per-stratum** — §4.1; boundary types leading dimension, pooled disclosure-only,
  cross-type pooling barred. PASS.
- **B-5 UNPOWERED-first** — §5 evaluates UNPOWERED first; §6.3 predeclares UNPOWERED strata with n+MDE.
  PASS.
- **L-19 seed floors** — matched_unconditional 30 donors (≥25); trap_load_derangement ≥2000;
  T4 ≥25-seed. PASS.
- **INFR-016 report-layers-not-gates** — §4/§7: "report layers", "no `pass` field anywhere",
  bands are labels; disposition is an operator act. PASS.
- **L-21 unit pin** — divisor (IB width) and normaliser (`delta_abs_resid`) objects named exactly;
  but CONVERSION-PIN omits the measured-value line (Issue 4). PARTIAL.
- **SPREAD-SCALE-ROUTING** — §6.2 present, uses `spread_scale_route` 3× threshold, not re-derived.
  PASS.
- **Amendment ledger** — §10 opens 0L/0T/0N; pre-measurement amendments append at QA. PASS.
- **Scope** — TRAIN-only, 0/0 reads, no TEST/holdout, no tradability/deployability claim, registers
  nothing; three boundary types are faceting (4 stat reads, ≤5 plot types, 1 module), at the top of
  the screen budget but not over it. PASS.
- **Universe** — 296 breadth / 197 DESIGN draw / 194 A5-fitted matches ckpt-014 AMENDMENT-1;
  survivorship caveat carried. PASS.
- **Operator-facing** — chat summary is plain and short (below). PASS.

### Issues (all routed to quant-designer — design defects)

1. **[SUBSTANTIVE] `trap_load` derives its sign from price geometry, not measured flow — the signed
   warrant is not actually tested.** §1 / §3.2 / §6.1.
   The design defines `trap_load = side_sign × Σ over poke-and-fail bars of delta_abs_resid` and
   calls it "the cumulative same-direction taker Δ … expressed as a residual against the A5 \|Δ\|
   baseline." But `delta_abs_resid` is the residual of **\|Δ\|** — a magnitude, direction-free. The
   frozen apparatus states this in its own code: `acceptance.py:355` — *"This leg is direction-free,
   so it cannot invert between sides."* SPDR-007 gets measured direction from a different column,
   `delta_ratio_resid` (Δ/V), signed by side. So SPDR-008's load = (aggression **magnitude**) ×
   (poke **price direction**); the *measured* sign of the poke bars' flow never enters.
   Why it matters: SPDR-008's entire reason to exist (over the price-only SPDR-007, which came back
   P-01) is that *measured* signed flow carries information price geometry does not. As written, a
   poke that ticked beyond the boundary on net **opposite** flow (absorption — a phenomenon the
   family explicitly prizes, card §1) is scored as **high** trap load, which is the opposite of the
   mechanism. The "signed" primary read (T1/T2) then reduces to aggression-magnitude × price-geometry
   — a quantity T3 (the P-01 control) already partly carries — so a T1/T2 "signed-supported" result
   would not distinguish measured flow from a magnitude×geometry confound.
   Required change: make the load's **sign** come from measured flow. Either use the signed-flow
   residual (e.g. `side_sign` applied to a Δ/V-based `delta_ratio_resid` load, or a signed-Δ residual)
   so direction is measured not assumed; or, if magnitude-only load is deliberately intended, drop
   the "same-direction taker Δ" language, justify magnitude-as-trap-load against the source, and add a
   binding disclosure that decomposes measured direction from magnitude and shows the derangement null
   + T3/P-01 flag can separate them. This gate should be resolved before the module is built.

2. **[SUBSTANTIVE] Boundary generalisation vs "reuses acceptance exactly" — mechanism unspecified,
   frozen-pin regression guard missing.** §3.1 / §9.
   §3.1 says event construction is done "reusing `xen.sigbar.{sessions,acceptance,profile}` **exactly**
   as INFR-018/SPDR-007", then describes poke/A6 via "**generalised** `acceptance.find_pokes`" applied
   to PVA/PRIOR levels. The shared code is not level-agnostic: `acceptance.find_pokes` computes poke
   thresholds from `ib_high`/`ib_low` (`acceptance.py:149-161`) and `evaluate_discriminator` reads
   `close_beyond` against `ib_high`/`ib_low` (`:246-249`). Reusing them "exactly" on a non-IB level
   is impossible without generalisation, and the two words conflict.
   Why it matters: (a) if the developer parameterises the shared `acceptance.py`, that edits frozen
   apparatus INFR-018/SPDR-007 depend on — a silent change to the IB path would break pin `5c386984`
   reproduction (this is the "reference that moves when the design says fixed" failure shape QA exists
   to catch); (b) if the developer re-implements poke/A6 in `trap.py`, the frozen D4-t50-w30 close-count
   form (half-open `[poke_ts, qualify_end)` window, `w`-sub-window filter, `close_beyond.mean() ≥ τ`)
   could subtly diverge on the IB level.
   Required change: state explicitly which path is taken, and pin the corresponding guard — if
   `acceptance.py` is parameterised, require a byte-identical regression assertion that the IB-edge
   path reproduces INFR-018/SPDR-007 exactly; if re-implemented in `trap.py`, require an asserted
   equivalence to the frozen D4-t50-w30 form on the IB level. Remove "exactly" where generalisation is
   meant.

3. **[MODERATE] Golden trace under-specifies the new paths.** §8.
   GT-2 (DOWN branch) and GT-3 (PVA/PRIOR — the widening's core) do not pin concrete sessions, so the
   highest-risk new code (prior-session profile → value-area edge → prior-level poke → reclaim →
   tercile) is not independently hand-derivable; the derivation script is free to choose the session.
   SPDR-007's precedent pinned every GT session concretely. Also GT-1's TRAP membership (that it
   reclaims) is asserted, not shown.
   Required change: pin GT-2 and GT-3 to named sessions — symbol + current session date **and the
   prior session date** for PVA/PRIOR — with the hand-derivable input state (prior VAH/VAL or prior
   extreme, poke_ts, poke_extreme, reclaim bar) stated as in GT-1, and confirm GT-1 actually reclaims
   (or name a fallback). The computed outputs (load, MFE_rev, race) may still be filled by
   `gt_derive.py`, but the events themselves must be fixed in the design.

4. **[MINOR] CONVERSION-PIN omits the mandated measured-value line.** §6.1.
   design-requirements §9 requires the CONVERSION-PIN to state the **measured TRAIN-median value** of
   the divisor object in bps, "computed from data, never recalled"; SPDR-007 §6.3 stated it for the 5
   majors. §6.1 here jumps from divisor object to "resulting effect" with no measured `ib_width_bps`.
   For a 296-instrument breadth screen the full table is legitimately emitted at run (`floor_table`),
   but the design should still state the reference/anchor-symbol measured medians plus one worked floor
   row so the conversion arithmetic is QA-traceable at design time.
   Required change: add the measured-value line (reference symbols' DESIGN-median `ib_width_bps`) and a
   single worked `reversal_bps` vs floor example.

5. **[LOW] Control-label legend missing.** §4 / §4.2.
   The read table (§4) references CONTROL-A/B/C but §4.2 names the controls without an A/B/C mapping.
   Inferable (A=`ordinary_touch`, B=`trap_load_derangement`, C=`matched_unconditional`) but should be
   stated. Add a one-line legend.

6. **[LOW] Uniform IB-width divisor wording for PVA/PRIOR.** §3.2 / §6.1.
   The rationale "one frozen divisor object keeps types comparable" sits in mild tension with the
   independence mandate (types are explicitly *not* compared), and "reversal_bps ≈ ib_width_bps … on a
   full rotation" holds only for IB — PVA/PRIOR targets are ~1 VA-width / prior-range, not ~1 IB width.
   The money-bps read (divisor cancels: `mfe_rev_norm × ib_width_bps` = true excursion bps), the
   derangement null, and the same-unit MDE are all unaffected, so this is wording, not a numeric
   defect. Correct the "comparability"/"≈ ib_width_bps" phrasing for the widened types.

**Verdict rationale.** REVISE on Issues 1 and 2 (both substantive: Issue 1 goes to whether the primary
signed read measures signed flow at all versus a magnitude×geometry P-01 confound; Issue 2 risks silently
altering the frozen pin or diverging from the frozen A6 form on the shared apparatus). Issues 3–6 are
design-completeness/clarity fixes. No integrity firewall breach found (fences, causality, derangements,
no-per-level-Δ, no-local-accounting, report-layers, holdout untouched all sound), so this is REVISE, not
REJECT. All findings route to the quant-designer; re-QA after revision.

---

## QA run 2 — 2026-07-21T11:39:44Z — mode: subagent — HEAD 53c9c3def03d91d64fcd21db476c5a1c1f9248aa
Verdict: **APPROVE**

Reviewed git state: HEAD `53c9c3d` (clean); untracked `python/experiments/SPDR-008/` (design.md +
qa-review.md + design_derivations/). Re-read the revised `design.md` (changed §1, §3.1, §3.2, §4.2,
§6.1, §8, §9, §10). Still design-stage — no runner/module code yet; the run-1 findings were all
design-level and are checked here against the revised text, the frozen apparatus, and the newly
supplied `design_derivations/gt_derive.py`.

### Fix-verification trace (run-1 issue → revised location → verdict)

| Run-1 issue | Revised location | Verdict | Evidence |
|---|---|---|---|
| **1 (blocking) — load signed by geometry not flow** | §3.2 `trap_load` row; §1; §6.1 normaliser object | **RESOLVED** | `trap_load = poke_side × Σ delta_ratio_resid` (the A5 **signed** Δ/V column). Confirmed `delta_ratio_resid × side` is the frozen direction leg (`acceptance.py:381`), and `delta_abs_resid` is the direction-free magnitude (`acceptance.py:353-355`). Sign now comes from measured flow; `>0` = flow agreed (genuine trap), `≤0` = absorption. Source-inventory disclosure variant (`poke_side × Σ [sign(Δ_bar) × delta_abs_resid]`) added as a sensitivity — and it too is measured-flow-signed, not geometry-signed. |
| **2 (blocking) — "exactly"/"generalised" conflict, pin risk** | §3.1 reuse-boundary block; §9 code-modules | **RESOLVED** | IB reuses `find_pokes`/`evaluate_discriminator`/`label_outcomes` **unmodified**, with `assert_ib_matches_frozen` (byte-identical to SPDR-007's reject set). PVA/PRIOR use NEW `trap.py` `find_pokes_at_level` + a re-implemented D4-t50-w30 close-count **regression-guarded to reproduce `evaluate_discriminator` byte-identically on the IB level**. `acceptance.py`/`profile.py` explicitly NOT modified (pin preserved). Conflict removed; both guards specified. |
| **3 — GT-2/GT-3 sessions unpinned; GT-1 trap membership asserted** | §8; `design_derivations/gt_derive.py` + `gt_output.txt` | **RESOLVED** | Ran `gt_derive.py`: it exists, runs clean, and reproduces every pinned §8 value exactly — GT-1 BTC 2022-07-15 IB-down (load **+151.7**), GT-2 SOL 2022-07-14 IB-up (load **−83.3**, the absorption guard), GT-3(a) BTC PVA 2022-07-17/prior-16 (VAL 21147.4→VAH 21468.4, +87.23), GT-3(b) BTC PRIOR 2022-07-16/prior-15 (prior-High 21195.5→prior-Low 20469.5, +573.4). Prior sessions named; all events in DESIGN band (2022-07). GT-1 reclaim confirmed (13:46, entry 20833.5 back inside). Internal cross-consistency: GT-1's MFE reaches 21195.5 = the prior-High used by GT-3(b) — real geometry on real bars. |
| **4 — CONVERSION-PIN missing measured value** | §6.1 | **RESOLVED** | Measured-value line present: BTC 48.745 · ETH 69.958 · SOL 96.217 · DOGE 86.969 · XRP 60.753 bps (matches SPDR-007 §6.3 on the identical divisor). Worked row added (SOL mfe_rev_norm 1.0 ⇒ 96.217 bps vs floor 14.73 ⇒ ABOVE_FLOOR). Reference floors listed (BTC 14.24 … XRP 15.93) — cross-checked against SPDR-007 §6.3, exact. Full per-symbol table deferred to `results/floor_table.json` (legitimate for a 296-symbol breadth screen). |
| **5 — control-label legend** | §4.2 | **RESOLVED** | Legend added: A=`ordinary_touch`, B=`trap_load_derangement`, C=`matched_unconditional` — matches the §4 T-table usage (T1/T2→B, T3→A, T4→C). |
| **6 — uniform IB-width divisor wording for PVA/PRIOR** | §3.2 `ib_width` row; §6.1 resulting-effect | **RESOLVED** | Reworded: single frozen L-21 divisor, "it cancels (`mfe_rev_norm × ib_width_bps` = true excursion bps), NOT a claim that a PVA/PRIOR reversal spans one IB width; types read independently, never compared on the normalised scale." No "≈ ib_width_bps" off-IB claim remains. |

### Amendment ledger & regression check

- §10 logs the five pre-measurement amendments as **0L / 2T / 3N** (AMENDMENT-1 trap-load-sign TIGHTER,
  AMENDMENT-2 reuse-guards TIGHTER, 3/4/5 NEUTRAL). Directions are correct: neither blocking fix
  loosened an acceptance bar or event definition — both made the signed read stricter/validity-guarded.
  No LOOSER amendment; the three-NEUTRAL tail is not a directional streak (NEUTRAL moves no goalpost).
- No new integrity regression: §7 HARD block, §4.2/§4.3 controls+tripwire, §5 bands, §6.2/§6.4 routing
  and uncertainty, and all four frozen pins are unchanged from run 1; the edits are tightenings and
  concretisations only. Fences/causality/derangements/no-per-level-Δ/no-local-accounting/report-layers/
  holdout-untouched all remain sound.

### Residual observations (non-blocking — designer's discretion, do NOT hold execution)

- **O-1 (§0 frozen-inputs, line 55):** still reads "the trap-load reads `delta_abs_resid` (|Δ| baseline)
  and `delta_ratio_resid`", listing the magnitude column first. After AMENDMENT-1 the PRIMARY column is
  `delta_ratio_resid`; `delta_abs_resid` is now disclosure-only. Not wrong (both are read), but the
  emphasis is inverted vs the corrected §3.2. Optional one-line tidy.
- **O-2 (§8 note):** the golden trace pins the **raw** `poke_side × ΣΔ` sign and asserts the screen's
  seasonally-normalised `delta_ratio_resid` load "carries the same sign", checked at diff. Raw-ΣΔ sign
  and residual-vs-seasonal sign are not a general identity (a same-direction poke *below* its seasonal
  norm could flip the residual). It holds for the chosen strong-trap/clear-absorption GT events, and the
  design already treats sign agreement as a required diff check — so at code-QA a GT sign disagreement
  must be a finding to investigate, not silently accepted. Recorded so the later diff pass applies it.

### Verdict

**APPROVE.** All six run-1 findings resolved; both blocking issues (signed-flow load, frozen-apparatus
reuse boundary) are fixed correctly and verified against the frozen code and the reproducible golden
trace. No integrity firewall breach; amendment ledger clean (0L/2T/3N). Two non-blocking wording
observations recorded for the designer and for the later code-QA diff. Ready for the operator's
execution gate. (Execution remains the operator's act — APPROVE launches nothing.)

---

## QA run 3 — 2026-07-21T12:28:04Z — mode: subagent — HEAD 53c9c3def03d91d64fcd21db476c5a1c1f9248aa
Verdict: **REVISE**

**CODE-STAGE fidelity trace** — the implementation now exists (`xen.sigbar.trap` + runner + smoke);
I did not write it, so fresh context holds. Reviewed working tree: untracked `python/src/xen/sigbar/
trap.py` and `python/experiments/SPDR-008/`; frozen apparatus (`acceptance.py`, `profile.py`, `spine.py`)
**byte-unchanged** (`git diff --stat HEAD` empty — verified). Ran `_smoke_trap.py` and `gt_derive.py`
under `uv run --with nautilus_trader==1.230.0 …`.

**Headline:** the CORE is sound — golden trace reproduces exactly, trap_load is signed by measured
flow, the frozen apparatus is untouched and the IB regression assert passes, and every integrity
FIREWALL holds. The pooled PRIMARY read is genuinely NULL and is not corrupted by any gap. **But the
code omits or deviates from several design-mandated adjudication components** — the HARD-required
tripwire *bite*, the tripwire's collapse-on-contrast statistic, the per-cell derangement that the K=3
deliverable needs, T4's CI, the MDE curves, and the T3 disclosure — none logged as ratified deviations
(§10). For the observed null these do not corrupt the disposition, but as a design→code fidelity matter
the emission does not implement the designed disposition machinery, and it ships an **un-null-adjusted
per-cell allocation map** that is a P-01/L-03 multiplicity landmine if read as-is. Hence REVISE, not
APPROVE — with a proportionate path for the operator (below).

### Golden-trace diff (the core check) — PASS, exact

Ran `_smoke_trap.py` (trap.py) and `gt_derive.py` (independent oracle). trap.py reproduces every §8 GT
value exactly, geometry AND residual load:

| GT | boundary | expected trap_load | smoke (trap.py) | oracle (gt_derive) | geometry |
|---|---|---|---|---|---|
| GT-1 | IB BTC 2022-07-15 down | +0.8821 | **+0.882126** | matches | mfe_rev_norm 1.9307, mae 1.9413, STOP ✓ |
| GT-2 | IB SOL 2022-07-14 up (absorption) | −0.1229 | **−0.122858** | matches | mfe 0.4333, mae 15.75, STOP ✓ |
| GT-3(a) | PVA BTC 2022-07-17 | +0.2736 | **+0.273623** | matches | VAL 21147.4→VAH 21468.4, mfe 13.9745 ✓ |
| GT-3(b) | PRIOR BTC 2022-07-16 | −0.7273 | **−0.727272** | matches | High 21195.5→Low 20469.5, mfe 5.3053 ✓ |

`assert_ib_matches_frozen` passed for both IB symbols. Non-circularity: the risky new geometry
(poke/reclaim/MFE/MAE/level) is computed by fully separate code in `trap.find_pokes_at_level`+`find_traps`
vs `gt_derive._find_trap` and they agree exactly; the residual load shares only the intended frozen
`baselines.residualise` primitive. GT-2's negative load confirms the Issue-1 fix works in code — an
up-poke on net selling scores NEGATIVE (absorption), where the retired magnitude×geometry form would
have scored it high-positive.

### Design-fidelity trace (design clause → code → verdict)

| Design clause (§ref) | Code | Verdict | Notes |
|---|---|---|---|
| trap_load signed by measured flow (§3.2) | `trap.py:264-265` `side*Σ delta_ratio_resid` | MATCHES | Uses the signed Δ/V residual, not `delta_abs_resid`. Confirmed against `acceptance.py:381`. |
| Frozen reuse: IB unmodified + regression assert (§3.1) | `trap_screen.py:83,94-96`; `trap.assert_ib_matches_frozen`; git diff empty | MATCHES | IB reject via frozen `evaluate_discriminator`; assert runs on DESIGN and passes; `acceptance.py`/`profile.py` byte-unchanged. |
| PVA/PRIOR levels from PRIOR closed session (§2, §3.1) | `trap.boundary_levels:90-105` (uses `prev` anchor) | MATCHES | Prior VAH/VAL via `build_profile(prior,"K-UNIFORM")`; prior extreme from prior session. Causal. |
| Entry = bar at reclaim_ts+1min; excursion strictly after (§2, §3.2) | `trap.py:267-268,276-284` | MATCHES | Entry-bar range excluded from MFE/MAE. |
| Same-bar pessimistic → STOP (§3.2) | `trap._race_outcome:311-312` | MATCHES | |
| Tercile cuts DESIGN-only, frozen+hashed before CONFIRM tiering (§3.3, §7) | `trap_screen.py:295-303,305-313` | PARTIAL | Cuts computed from DESIGN only (no leak) and hashed; **but** CONFIRM *events* are assembled before the cuts file is written and there is no code-asserted freeze-before-CONFIRM refusal (design §7 HARD). Substantively safe (cut is DESIGN-only), guard not enforced. |
| T1 monotonicity vs ≥2000-seed derangement (§4, §5) | `trap_screen.py:122-144` | MATCHES (pooled) | 2000 seeds, one-sided p, CI. Pooled per boundary only. |
| T2 tier marginal, day-clustered CI (§4) | `t2_tier_marginal:159-181` | MATCHES | Paired-day block bootstrap. |
| **T4 availability with dependence-honest CI (§4, §4.2)** | `t4_availability:184-209` | **DEVIATES** | Emits contrast of means, **no bootstrap CI**. Cannot be read as SUPPORTED. |
| **T3 ordinary_touch disclosure (§4, §4.2)** | `t3_unsigned_base:212-218` (stub, uncalled) | **MISSING** | Not computed, not in layers.json. Stub asserts "P-01 carried by T1 derangement". |
| **reversal_path_swap: collapse on each effect-CONTRAST (§4.3)** | `tripwire_path_swap:221-243` | **DEVIATES** | Computes swapped-vs-raw **means**, not `destroyed_contrast/raw_contrast` on T1 ρ / T2 / T4. Non-adjudicating (NO_MATERIAL_EDGE) — design-sanctioned here since the pooled edge is ~0. |
| **Tripwire positive-control BITE, REQUIRED (§4.3)** | `tripwire_path_swap` (`bites=[]` unused) | **MISSING** | `corr(mfe_swapped_price, mfe_donor_price)>0.5` not computed. Design: "no disposition emits without it." |
| **Per-cell derangement null → K=3 deliverable (§0, §4, §4.1)** | `allocation_map` build `trap_screen.py:341-353` | **MISSING** | allocation_map ships raw per-symbol ρ + high_low_diff + median; **no per-cell null-adjusted p**. K=3 (survives-derangement) not computable from the emission. |
| **MDE curves published before the read (§4.2, §6.3)** | — | **MISSING** | No `mde_curves` artifact; no co-designed plants. UNPOWERED is a crude `n<20` (T1) / `n<3` proxy, not MDE-based; §5 SUPPORTED (effect ≥ MDE) cannot be evaluated. |
| Universe honesty: 194 signed / 296 breadth (§0) | `layers.json` `a5_fitted_run:194`, `breadth_denominator_design_note:296`, `n_symbols_with_events:189` | MATCHES (minor) | Stated. 5 symbol skips (BUSD/CKB/NKN/PAXG DESIGN; BUSD/DENT/PAXG/SUN CONFIRM — ColumnNotFound/Schema) are **logged** in run_log (not silent) but **not structurally tallied** in the emission (design's "counted, never silently dropped"). |
| No `pass`/auto-verdict (INFR-016) | `layers.json` | MATCHES | 0 `pass`/SUPPORTED/verdict fields; raw stats only; UNPOWERED/excludes_zero are report flags. |

### Governance & integrity firewall — all HOLD

- Frozen apparatus byte-unchanged (git diff empty). PASS.
- TRAIN fence: `fences.load_bars(band)` loads only DESIGN/CONFIRM; `assert_band` raises on holdout/TEST. PASS.
- Causal ≤t−1: trap load from poke bars ≤ reclaim; PVA/PRIOR from prior closed session; entry reclaim_ts+1. PASS.
- No-per-level-Δ: profile weights Volume only; `assert_no_per_level_delta` guards; trap reads per-BAR `delta_ratio_resid`. PASS.
- `check_no_local_accounting`: called in `main` on screen_code + analysis_code. PASS.
- Derangement zero-fixed-point: `trap.derange` regenerates until no fixed points (L-28). PASS.
- `assert_frozen_inputs` at entry (re-hashes baselines/pins). PASS.
- Freeze cut is provably DESIGN-only (no CONFIRM leak into the cut) despite the un-asserted ordering. PASS (substance).
- **No integrity firewall breached; no corrupt positive validated.** The pooled primary is null and self-evidently so.

### Per-item calls on the self-disclosed gaps (as requested)

- **(a) T4 no bootstrap CI** — ACCEPTABLE-AS-DISCLOSURE for this null screen (T4 is report-class; the pooled contrasts are small and flip sign DESIGN↔CONFIRM on IB, so nothing is SUPPORTED). Must be recorded: T4 cannot be read as SUPPORTED without a CI.
- **(b) Tripwire compares means, non-adjudicating, material-edge-gated** — the NO_MATERIAL_EDGE state is design-sanctioned (SPDR-007 D-2) because the pooled edge is ~0, so nothing false is validated. BUT the collapse-on-contrast statistic is not what §4.3 specifies, and the HARD-required **bite is absent** (SPDR-007 computed it at 0.77 even at NO_MATERIAL_EDGE). This is a genuine deviation from the HARD tripwire spec — it corrupts no null result, but it means the tripwire cannot vouch for ANY edge a future re-run might surface.
- **(c) No per-cell derangement null; raw per-cell ρ shipped** — the most consequential. The allocation_map's 241 powered cells show **58 with ρ>0.10 and 56 with ρ<−0.10** — a symmetric-around-zero distribution that is itself dispositive of null. So the honest NOT_WORTH-shaped disposition IS reachable, but ONLY if read two-sided as un-null-adjusted. As shipped (raw ρ, no null column), the map is a multiplicity landmine if the 58 positives are read as "signal pays here." The design's K=3 (survives-derangement) deliverable is not computable from this emission.
- **(d) T3 ordinary_touch stubbed** — ACCEPTABLE-AS-DISCLOSURE. T3 is disclosure-class and the SIGNED read's P-01 isolation is genuinely carried by T1's derangement (which IS computed and null). Record the scope reduction.

### Issues (numbered; route in each)

1. **[HARD-spec, must fix or ratify] Tripwire bite absent + wrong statistic.** §4.3 → `trap_screen.py:221-243`. Design requires `corr(mfe_swapped_price, mfe_donor_price)>0.5` ("no disposition emits without it") and collapse computed on each effect-CONTRAST (T1 ρ, T2, T4). Code computes raw-vs-swapped means and never computes the bite (`bites=[]` unused). Required: implement the bite + contrast-collapse, OR the operator ratifies the tripwire as NO_MATERIAL_EDGE/bite-not-computed with a binding "no cell promotable without re-running bite+contrast-collapse." Route: experiment-developer (+ operator ratify in §10).
2. **[Deliverable-required] Per-cell derangement null missing; allocation map un-null-adjusted.** §0/§4/§4.1 → `trap_screen.py:341-353`. K=3 needs per-cell survives-derangement; allocation_map has raw ρ only. Required: add a per-cell (or pooled-cluster) derangement-adjusted p to the allocation map, OR ship it with an explicit "raw ρ, un-null-adjusted; read two-sided (58 ρ>0.10 vs 56 ρ<−0.10 of 241 = symmetric null)" label and a binding analyst instruction. Route: experiment-developer (+ analyst handoff).
3. **[Bands can't be applied] MDE curves not emitted.** §4.2/§6.3/§5 → runner (no `mde_curves`). UNPOWERED is `n<20`/`n<3`, not MDE-based; SUPPORTED (effect ≥ MDE) is unevaluable. Required: emit the co-designed MDE plants before the read, OR ratify n-floor UNPOWERED as a declared simplification (§10). Route: experiment-developer (+ quant-designer).
4. **[Disclosure] T4 CI missing (§4.2) and T3 stubbed (§4).** Add T4's day-clustered CI; either compute T3 ordinary_touch or record it as a ratified disclosure-scope reduction. Route: experiment-developer.
5. **[Minor] Freeze-before-CONFIRM not code-asserted; 5 skips not tallied.** §7 → `trap_screen.py`. Add the code-asserted refusal (cuts file must exist before any CONFIRM tiering) and a structured skip count/reasons in layers.json ("counted, never silently dropped"). Substantively safe today (cut is DESIGN-only; skips are logged). Route: experiment-developer.
6. **[Governance] None of the above logged as deviations.** §10 still reads 0L/2T/3N — the adjudication reductions (bite, per-cell derangement, MDE, T4 CI, T3) are not in the amendment ledger and were not operator-approved. Every intentional reduction must append to §10 with a DIRECTION (L-23) and be operator-ratified. Route: quant-designer/operator.

### Verdict rationale + proportionate path

REVISE. The core is sound and no validity firewall failed — golden trace exact, signed-flow load
correct, frozen apparatus untouched, IB regression assert passing, fences/causality/no-per-level-Δ/
no-accounting/derangement all intact, and the pooled primary read is uncorrupted and NULL (with the
2000-seed derangement that IS implemented, plus a symmetric-null per-cell ρ distribution). This is not
a REJECT: nothing corrupt is being validated and the null disposition is honest and reachable.

It is not an APPROVE because the emission does not implement the design's disposition machinery: the
HARD-required tripwire bite is absent and the tripwire statistic deviates; the per-cell derangement
behind the K=3 deliverable is missing; MDE curves are absent so §5 bands can't be applied; T4 has no CI
and T3 is stubbed — none ratified in §10. Because the primary is null, the fix is **bounded and the
operator has a light path**: either (A) the developer adds the missing adjudication (bite +
contrast-collapse, per-cell derangement, T4 CI, MDE, T3) and re-runs — near-certain to reconfirm the
null — or (B) the operator formally ratifies these as scope reductions in §10 (L-23) and the emission
is dispositioned strictly as a **pooled-null screen** with binding analyst-handoff notes: read per-cell
ρ two-sided as un-null-adjusted (symmetric noise, not an allocation signal); the tripwire is
NO_MATERIAL_EDGE with the bite uncomputed; and **no cell may be promoted without re-running the full
bite + per-cell derangement machinery**. Route: experiment-developer (implementation) + quant-designer/
operator (deviation ratification + analyst handoff).
