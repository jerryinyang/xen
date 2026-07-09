# QA Review — EXP-024 (CF-CSRR-001 / HYP-002b)

## QA run 1 — 2026-07-06T14:49:06Z — mode: subagent — HEAD 50af382
Verdict: **APPROVE** (design-stage; with one BLOCKING carry-forward to implementation QA, R1)

Reviewed artifact: `python/experiments/EXP-024/design.md` (execution-agnostic Python availability
screen; no C# model, no `.conf`, no `analysis_code/` yet — pre-execution design review). Vehicle
to be reused: `python/experiments/EXP-022/analysis_code/screen.py` (verified present + capabilities).
Fresh-context check: PASS — this context did not produce the design or any implementation.

### Design-fidelity trace (design § → intent → checkable substrate)

| Design clause (§ref) | Substrate / evidence | Verdict | Notes |
|---|---|---|---|
| §0 controlled thesis-shopping guards | construction FROZEN (§3 one value/axis), family=4 members Holm (§3), binding bar = hardened block-boot CI USTEC FAILED (§0/§6/§7), TRAIN-only in-sample-honest, "pass only graduates to EXP-023, not confirmatory" | MATCHES | Guards real + sufficient; a TRAIN pass is explicitly NOT read as OOS confirmation. |
| Registration precondition (§ header, §11) | `multiplicity-registry.md:1227` HYP-002b REGISTERED, checkpoint-009, "new construction branch, multiplicity rule 4"; family card `cf-csrr-001.md:116` row present | MATCHES | Precondition met before screening. |
| P-06 re-open standard (pitfalls) | reversion endpoint + consensus anchor + permuted-axis null (not directional RS); family card §Distinctness | MATCHES | Not a P-01/P-02/P-06 dead-end re-run; new mechanism/target satisfied. |
| §3 single frozen family (no sweep) | A=median, B=raw, D=hedged, anchor=S, C=all>k — each ONE value; multiplicity = 4 members only; "no 16-cell max-stat, no cross-construction overlays" | MATCHES | single-worst continuity + 1/2/3·HL are disclosed sign-checks, NOT scored cells — not a hidden sweep. |
| §1/§6 binding bar = hardened CI | §6 "Effect (rho) — BINDING: mean rho + block_bootstrap_ci circular block≥h, ≥10k×5-seed battery, block_sensitivity ½/1/2×, trimmed_mean"; §7 SUPPORTED requires hardened ci_low>0 | MATCHES (intent) | Correct estimand & referee. **Implementation hazard R1** — see Issues. |
| §5 permuted-axis null (primary, B-6) | `screen.py:319` within-bar identity permutation re-pairs s_i↔idio owner; median label-invariant; moves conditional mean (not mean-invariant) | MATCHES | EXP-012/B-6 non-vacuity satisfied; Holm over 4 members. |
| §5 twins (random-index, random-timing) | `screen.py:334/372`; N_SEEDS=25 (L-19 battery); percentile/rank read declared | MATCHES | L-19 seed-battery + percentile binding read; single-draw disease avoided. |
| §5 tripwire future-destroyer (must collapse) | `screen.py:356` temporal block-permute of owner idio; BLOCK_TRIP=12 ≥ h clamp max 12 | MATCHES | block≥h holds at the clamp ceiling; vacuity check moves E[idio|s_i], not a path rotation. |
| §2 object identity (L-16) | PARTIAL-BY-DESIGN availability object; cannot retire multi-leg P&L family; conditioning event == V5 active-entry event | MATCHES | L-16 does not bind (no multi-leg retirement); no B-4 passive-limit seam. |
| §1 native vehicle (L-13) | estimand consensus-hedged, null cross-sectional identity, horizon = residual AR(1) HL | MATCHES | Not copy-pasteable to single-instrument/directional. |
| §9 causal ≤t-1 / open-to-open | `screen.py`: u/m/s/k/HL from confirmed close ≤t, `reset_anchor` causal, forward g from Open(t+1) | MATCHES | Evaluate-on-open + lagged-reference honored. |
| §4/§9 holdout | `screen.py:78` TRAIN_FRAC=0.49, `:145` "only ever touch first 49%"; TEST band unemitted; final-30% never loaded | MATCHES | Holdout fence sound + checkable. |
| §5 drift-carry deferred | ρ_mom ≡ −ρ_rev algebraic negation → vacuous here; booked as EXP-023 requirement | MATCHES | Correct (USDCAD lesson deferred to P&L tier). |
| §8 power realism / B-5 | all>k dilution trade-off pre-declared (effect may fall below EXP-022 +4.7 as n rises); US500 predeclared UNPOWERED, never a negative | MATCHES | Honest; the experiment's own question (ci_low>0 vs dilute-to-MDE) is stated. |
| §10 golden trace | first-3 all>k post-warmup, frozen rule "no hand-picking", hand-computable (present set, median, s_i, k, HL, fade, g/G/idio/rho) | MATCHES | Developer-independent + bit-verifiable; mirrors EXP-022 QA-verified pattern. |
| Execution-agnostic carve-out | no engine / no fills / no P&L / no `xen.adjudication` estimand gate; precedent EXP-008/009/021/022 | MATCHES | Legitimate; estimand-reconciliation gate N/A (no accounting object); `check_no_local_accounting` honored (no P&L). |

### Golden-trace diff (design-derived expectations)
No emission exists yet (design stage). The §10 rule is deterministic and hand-computable from the
frozen R_US / anchor-S / median / raw / all>k / hedged construction; the reused `screen.py` primitives
(`reset_anchor` offset = SESSION_HOUR, `consensus_resid` median/raw, `trailing_threshold` k,
`ar1_halflife` → h clamp[1,12], forward from Open(t+1)) reproduce every trace quantity. Expected values
must be hand-derived from the DESIGN at the code-QA pass, never read back from a run. No discrepancy at
design level.

### Governance & boundary
- Mandatory declaration blocks present: mechanism (§1), object-identity (§2), control-validity proofs
  (§5, incl. B-1 non-degeneracy + B-6 non-vacuity), tripwire (§5), bands (§7), power (§8), golden trace
  (§10), hard/informative split (§9). PASS.
- `check_no_local_accounting`: N/A (no P&L object) but honored — no accounting primitives; canonical
  `xen.evaluation` only. PASS.
- No Python strategy backtest (availability screen; execution-agnostic). PASS.
- Registry preconditions: family REGISTERED; HYP-002b row present; 0 counted TEST reads / 0 slots stated.
  PASS.
- Holdout: TRAIN_FRAC=0.49 fence in the vehicle; TEST unemitted; final-30% never loaded. PASS.
- Deviations block: none claimed. N/A.
- Elicitation hygiene: no open operator questions embedded. PASS.

### Issues

1. **[BLOCKING — carry to implementation + code-QA; route: experiment-developer / data-analyst]**
   The binding bar is the **hardened** block-boot CI on the **R_US / anchor-S / all>k / hedged** cell,
   but the reused vehicle hardwires the hardened battery to a different cell: `screen.py:422`
   `full_ci = (tag_build == "N" and anchor == "P")` routes build R + anchor S to the LIGHT path
   (`N_BOOT_ROBUST=2000`, and `block_sensitivity` / `trimmed_mean` / `ci_low_seed_range` are emitted
   only under `full_ci`, lines 512–517); the extra hardened disclosures at line 464 are further gated to
   the **single-worst** cell, not `all>k`. A verbatim "reuse screen.py with US-bloc/all>k/anchor-S args"
   (as §11 Deliverables phrases it) would silently under-deliver the ≥10k-boot + block-sensitivity-sweep
   + trimmed-mean disclosures the design commits to in §6/§7 — on exactly the binding construction.
   Required change: the EXP-024 `analysis_code` must apply the FULL hardened CI battery
   (n_boot ≥ 10k, 5-seed `ci_low_seed_range`, `block_sensitivity` ½/1/2×, `trimmed_mean`) to the
   R_US/anchor-S/all>k/hedged binding cell — i.e. do NOT inherit the `full_ci = N×P` gate. Verify this at
   the code-QA pass before the operator's execution gate. (The design's statistical INTENT is correct and
   complete; this is a reuse-instruction hazard, not a methodological defect — hence APPROVE-with-condition,
   not REVISE. Recommend §11 be reworded from "reuse screen.py" to "adapt screen.py so the hardened CI
   applies to the binding construction" to remove the ambiguity.)

2. **[MINOR — design clarity; route: quant-designer, non-blocking]** Holm denominator ambiguity when a
   member is UNPOWERED. §3/§7 set the multiplicity family = 4 members (Holm), while §7/§8 predeclare US500
   likely UNPOWERED (n<100) and "never a negative" (B-5). State explicitly whether Holm corrects over all 4
   or over the powered members only (a member with no valid p_perm should not consume Holm alpha). Either
   rule is conservative for the graduation read; naming it removes a post-hoc DOF. Not verdict-material
   (Holm-over-4 is the stricter bar for USTEC either way).

3. **[ADVISORY]** Tripwire block (BLOCK_TRIP=12) satisfies block ≥ h only because h is clamped to [1,12];
   confirm at code-QA that no realized h_i exceeds the tripwire block after the session-anchor HL re-fit
   (clamp guarantees ≤12, so BLOCK_TRIP=12 is exactly sufficient — verify equality is intended).

### Summary
Design is mechanism-first, internally consistent, and honest on the controlled-thesis-shopping axis:
single frozen construction, 4-member Holm family (no disguised sweep), binding bar = the hardened CI USTEC
previously FAILED (not the permutation-only read that lit it up), TRAIN-only and explicitly non-confirmatory,
US500 predeclared UNPOWERED (B-5), native estimand/null/horizon (L-13), L-19/L-20 hardened-CI + seed-battery
discipline, sound integrity gates (tripwire collapse, holdout fence, causal ≤t-1, open-to-open), and a
developer-independent golden trace. APPROVE for the operator execution gate, conditioned on Issue 1 being
resolved and verified in the `analysis_code` before execution (a fresh code-QA pass is the natural place to
close it). Issues 2–3 are non-blocking.

---

## QA run 2 — 2026-07-06T17:15:00Z — mode: subagent — HEAD 631863a
Verdict: **APPROVE** (pre-execution CODE-QA; R1 RESOLVED; integrity sound)

Reviewed artifact: `python/experiments/EXP-024/analysis_code/screen.py` (549 lines; sole file in
`analysis_code/`). Design: `python/experiments/EXP-024/design.md` (frozen). Prior QA: run 1
(APPROVE with one BLOCKING carry-forward, Issue 1 / R1). Vehicle for comparison:
`python/experiments/EXP-022/analysis_code/screen.py`. Canonical API: `python/src/xen/evaluation.py`.
Fresh-context check: PASS — this context did not produce the design, the prior QA, or the code.
No execution performed (static review only).

### 1. R1 RESOLUTION — the blocking carry-forward (VERIFIED RESOLVED)

R1 required: the R_US/anchor-S/all>k/hedged binding cell must receive the FULL hardened CI battery
(N_BOOT_FULL=10_000, n_seeds=5, block_sensitivity ½/1/2×, trimmed_mean, ci_low_seed_range) WITHOUT
the `full_ci = (tag_build == "N" and anchor == "P")` gate that EXP-022 `screen.py:422` used (which
routed R_US/S to the 2k-boot LIGHT path and gated hardened disclosures to the N×P cell).

Evidence that R1 is resolved in EXP-024 `screen.py`:

| R1 requirement | EXP-024 code line | Verification |
|---|---|---|
| No `full_ci = N×P` gate | `grep` confirms ZERO occurrences of `full_ci` in `analysis_code/` | RESOLVED — gate removed entirely |
| N_BOOT_FULL = 10_000 on binding cell | `:73` `N_BOOT_FULL = 10_000`; `:402` `n_boot=N_BOOT_FULL` | RESOLVED — 10k boots, unconditional |
| 5-seed battery | `:402` `n_seeds=5`; `:404` `n_seeds=5`; `:405` `n_seeds=5` | RESOLVED |
| ci_low_seed_range emitted | `:419-420` `ci_low_seed_range_bps`, `ci_high_seed_range_bps` | RESOLVED |
| block_sensitivity ½/1/2× | `:404` `ev.block_sensitivity(rho, [max(1,blk//2), blk, blk*2], …)`; `:422` emits `block_sens_ci_low_bps` | RESOLVED |
| trimmed_mean | `:405` `ev.block_bootstrap_ci(rho, ev.trimmed_mean, …)`; `:421` emits `trimmed_mean_bps`, `tmean_ci_low_bps` | RESOLVED |
| MDE | `:423` `ev.mde(rho, block=blk, n_boot=N_BOOT_FULL)`; emits `mde_bps` | RESOLVED |
| Battery on all>k/hedged (NOT single-worst) | `:388` `rows_allk = build_rows(..., "allk", ..., True, ...)`; loop `:390-429` | RESOLVED — binding cell |
| Single-worst gets LIGHTER CI | `:466-484` uses `N_BOOT_ROBUST=2000` (`:74`), no hardened disclosures | MATCHES design §3 |

**R1 verdict: RESOLVED.** The `full_ci` gate is completely absent; the binding cell receives the
full hardened battery unconditionally. The docstring at `:26-31` explicitly documents the R1 fix.

### 2. block ≥ h on the binding CI (design §6 "circular block ≥h")

- `:373` `hvec[li] = int(np.clip(round(2 * h_), 1, 12))` — h_i = clamp(round(2·HL_i), [1,12]).
- `:401` `blk = max(1, int(hvec[li]))` — binding CI block = h_i per member. `:402` passes `block=blk`.
- `evaluation.py:78` caps block to `[1, n-1]` (F1 hardening) — block stays ≥ 1 and < n.
- block_sensitivity sweep `:404`: `[max(1, blk//2), blk, blk*2]` = [≈½h, h, 2h].
- **MATCHES.** Circular block = h_i per member; block_sensitivity brackets h_i at ½/1/2×.

### 3. Frozen construction — single cell, no sweep (design §3)

| Axis | Design frozen value | Code line | Status |
|---|---|---|---|
| Basket R_US | {USTEC, US500, US2000, US30} | `:57` `MEMBERS = [...]` | MATCHES |
| Anchor S | session-open reset | `:60` `SESSION_HOUR={…12…}`; `:312` `reset_anchor`; `:356` `U = uS` | MATCHES |
| A = median | single value | `:363` `consensus_resid(U, present, "median", "raw")` | MATCHES |
| B = raw | single value | `:363` (same call) | MATCHES |
| C = all>k (PRIMARY) | powered selection | `:388` `build_rows(..., "allk", ...)` | MATCHES |
| D = hedged | idio = g_i − G | `:388` `hedged=True`; `:189-190` `G=median(gp); idio=g-G` | MATCHES |
| No A/B/C/D/anchor sweep | — | no loop over construction axes; only member loop `:390` | MATCHES |
| Single-worst = continuity | lighter CI, not scored | `:466-484` N_BOOT_ROBUST=2000 | MATCHES |
| Horizon 1/2/3·HL = sign-stability | not scored | `:456-464` emits `sign` only | MATCHES |
| Both-halves = sign-stability | not scored | `:445-455` emits `sign` + light CI | MATCHES |

**MATCHES.** One frozen construction; robustness overlays are disclosed, not a hidden sweep.

### 4. Holm over 4 members — UNPOWERED excluded (QA issue 2)

- `:389` `pvals = [np.nan] * len(MEMBERS)` — initialized to NaN.
- `:397-399` if `ne < 1`: `continue`, pvals[li] stays NaN (UNPOWERED).
- `:408-409` `if perm_null.size: pvals[li] = p_perm` — only set for valid permutation nulls.
- `:431-436` `holm_adjust(pvals)` → `:335` `valid = [(i,p) ... if np.isfinite(p)]`; `:336` `m = len(valid)`
  — denominator = valid count only. `:343` `(m - rank) * p` uses m = valid count.
- `:433` `n_valid_holm` emitted in summary + holm rows.
- **MATCHES.** UNPOWERED members do not consume Holm alpha. QA issue 2 resolved in code.

### 5. Controls present (design §5)

| Control | Function | Call site | Seeds/reps | Status |
|---|---|---|---|---|
| Permuted-axis null | `permuted_axis_null` `:218-230` | `:406` | N_PERM=1000 (`:70`) | MATCHES |
| Random-index twin | `random_index_twin` `:233-251` | `:410` | N_SEEDS=25 (`:69`) | MATCHES |
| Random-timing twin | `random_timing_twin` `:270-299` | `:411` | N_SEEDS=25 | MATCHES |
| Tripwire block-permute | `tripwire_block_permute` `:254-267` | `:412` | N_TRIP=300, BLOCK_TRIP=12 | MATCHES |

All controls emit collapse_fraction via `ev.collapse_fraction` (`:425,427,428`). **MATCHES.**

### 6. Holdout fence (design §4/§9)

- `:66` `TRAIN_FRAC = 0.49`.
- `:306` `cut = int(df.height * TRAIN_FRAC)` — only first 49% computed.
- `:307` `df = df.head(cut)` — only first 49% loaded into memory.
- `:309` `bars = bars.head(bars.height - 1)` — drops trailing partial window.
- No TEST split, no TEST emission anywhere. Summary `:535` records `train_frac` only.
- Final-30% (beyond 70%) never loaded: first 49% ⊂ first 70%; tail never read from disk.
- **MATCHES.** Holdout fence sound: first 49% only, TEST unemitted, final-30% never loaded.

### 7. Causality / provenance (design §9)

| Signal | Source | Code line | ≤ t? |
|---|---|---|---|
| u_i(t) | ln(Close_i(t) / anchor_i(t)); confirmed close | `:311-314` `c=Close; aS=reset_anchor; uS=log(c/aS)` | ≤ t |
| anchor_i(t) | close of prior reset-period's last bar (causal) | `:80-95` `anchor[k]=close[prev_last]`, prev_last < k | < t |
| m(t) | median of present u_j at t | `:131` `np.nanmedian(Um, axis=1)` | ≤ t |
| s_i(t) | u_i − m | `:132` | ≤ t |
| k(t) | trailing-median of max\|s\|, window strictly < t | `:144-145` `win = maxabs[max(0,t-w):t]` | < t |
| HL_i | AR(1) half-life (member-level constant) | `:98-111,371-373` fitted once per member | population parameter |
| h_i | clamp(round(2·HL_i), [1,12]) | `:373` | fixed per member |
| Forward g | ln(Open(t+1+h)/Open(t+1)) — open-to-open, L-01 | `:178-182` `k1=t+1; g=log(O[k1+hi]/O[k1])` | entry t+1, exit t+1+h |
| Decision bar | confirmed close at t; fade acted next open | `:163,193` `fade=-sign(s[t,i])` | signal ≤ t |

**MATCHES.** Signal inputs ≤ t-1; forward open-to-open; confirmed-bar decisions. `reset_anchor`
causal. HL is a member-level parameter (same as EXP-022; approved in QA run 1).

### 8. Tripwire / leak check (design §5/§9)

- `:254-267` `tripwire_block_permute`: shuffles owner idio in temporal blocks; re-pairs fade[t]
  with idio from unrelated time. `:266` `out[p] = np.mean(fade * idio_own[idx])`.
- `:412` BLOCK_TRIP=12, N_TRIP=300. block ≥ h: h_i clamped [1,12] (`:373`); 12 ≥ all h_i.
- QA run 1 advisory 3: confirm no h_i exceeds BLOCK_TRIP. Clamp guarantees h_i ≤ 12. **RESOLVED.**
- Collapse: `:428` `tripwire_collapse = ev.collapse_fraction(obs, trip_mean)` — expects ≈1.0.
- **MATCHES.** Future-destroyer; surviving edge ⇒ leak ⇒ REJECT. Block ≥ h at clamp ceiling.
### 9. Golden-trace code check (design §10)

Design §10 requires: first 3 all>k fade events after warmup, with timestamp, present members +
u_j, m=median, s_i, |s_i|>k test, fade, h_i, g_i, G, idio, rho.

- `:491-516` golden trace loop. `:494` iterates `rows_allk` (binding cell events).
- `:495` `if r[0] < K_TRAIL_W: continue` — warmup skip (K_TRAIL_W=120, `:67`). Session warmup
  implicit (u NaN before first reset → s NaN → won't pass |s|>k).
- `:515-516` `if len(golden) >= 3: break` — first-3-post-warmup, no hand-picking.

| §10 field | Code line | Key | Present |
|---|---|---|---|
| timestamp t | `:507` `"CloseTime": str(times[t])` | ✓ | |
| present members (≥3) | `:508` `"present": ",".join(...)` | ✓ | |
| u_j(t) | `:509` `"u_j": …` | ✓ | |
| m(t) = median | `:510` `"m_median": float(np.nanmedian(...))` | ✓ | |
| s_i(t) | `:511` `"s_i": r[2]` | ✓ | |
| k threshold | `:511` `"k_thr": float(k_thr[t])` | ✓ | |
| \|s_i\| > k test | `:512` `"abs_s_gt_k": bool(abs(r[2]) >= k_thr[t])` | ✓ | |
| fade side | `:513` `"fade": r[5]` | ✓ | |
| h_i | `:513` `"h": hi` | ✓ | |
| g_i | `:513` `"g_i": float(g[li_local])`; `:500` recompute | ✓ | |
| G = median(g_j) | `:513` `"G": G_t`; `:503` | ✓ | |
| idio = g_i − G | `:513` `"idio": float(r[7][li_local])` | ✓ | |
| rho_i | `:513-514` `"rho": r[4]`, `"rho_bps": r[4]*BPS` | ✓ | |

- g_i recomputation `:500` = `ln(O[k1+hi]/O[k1])` identical to build_rows `:182`. idio from stored
  row `r[7][li_local]` = g[li_local] − G (build_rows `:190`). Consistent with binding-cell emission.
- Written to `golden_trace{sx}.parquet` `:531`.
- **MATCHES.** All §10 fields present; first-3-post-warmup enforced; g/idio/rho consistent.

### 10. No local accounting; canonical xen only

- Imports: `:45` `from xen.bar_aggregator import aggregate_ohlc`; `:46` `from xen import evaluation
  as ev`. No experiment-local imports. `sys.path` → `python/src` only (`:44`).
- `grep` for banned primitives (assemble_realized_bps, assemble_multileg_bps, per_leg_net,
  build_episodes, fill, position, pnl, adjudication): ZERO hits in executable code (only docstring
  declaration at `:6`).
- Estimands from canonical `ev.*`; resampling controls (permuted_axis_null, twins, tripwire) are
  pure-stat functions, not accounting primitives. No P&L, no fills, no positions.
- **MATCHES.** Canonical xen only; no local accounting; no strategy backtest.
### 11. §7 SUPPORTED band — emitted fields check

All inputs for the SUPPORTED band (design `:189-190`) are emitted in `cell_rows`:

| Band clause | Emitted field(s) | Line |
|---|---|---|
| mean rho ≥ +1 bp | `mean_rho_bps` | `:417` |
| hardened ci_low > 0 | `ci_low_bps` | `:418` |
| 5-seed (block-stable) | `ci_low_seed_range_bps`, `block_sens_ci_low_bps` | `:419,422` |
| both halves sign-stable | `rob_rows` type=`both_halves`, `sign` | `:451-455` |
| beats both twins (Δ>0) | `ri_twin_bps`, `rt_twin_bps` | `:425,426` |
| p_perm Holm-significant | `p_perm`, `holm_p` | `:424,434` |
| tripwire collapses | `tripwire_collapse` | `:428` |

**MATCHES.** All band inputs present for operator judgment.

### Issues

1. **[R1 / BLOCKING carry-forward — RESOLVED]**
   The `full_ci = (tag_build == "N" and anchor == "P")` gate from EXP-022 `screen.py:422` is
   completely absent from EXP-024 `analysis_code/screen.py` (grep confirms zero occurrences). The
   binding all>k/hedged cell (`:388-429`) receives the full hardened battery unconditionally:
   N_BOOT_FULL=10_000 (`:73,:402`), 5-seed (`:402,:404,:405`), block_sensitivity ½/1/2× (`:404`),
   trimmed_mean (`:405`), ci_low_seed_range (`:419-420`), MDE (`:423`). Single-worst continuity
   uses the lighter N_BOOT_ROBUST=2000 path (`:479`), as designed. **No further action required.**

2. **[MINOR — strict vs non-strict threshold; non-blocking]**
   Design §3/§10 specify `|s_i(t)| > k` (strictly greater). Code uses `>=` at `build_rows:170,173`
   and golden trace `:512`. Since k is a trailing-median of continuous |s|, exact equality is
   measure-zero — `>=` and `>` are operationally identical. Noted for bit-for-bit fidelity.

3. **[MINOR — random-timing twin horizon; non-blocking]**
   `random_timing_twin:274` uses `h = int(np.median(hvec))` (median across all 4 members) rather
   than per-member `hvec[i_local]`. Inherited verbatim from EXP-022. The twin is a control
   (timing-informativeness), not the binding read; horizon mismatch is secondary to the
   random-timing treatment. Does not affect binding CI or any integrity gate.

4. **[MINOR — block_sensitivity half-block rounding; non-blocking]**
   `:404` `[max(1, blk // 2), blk, blk * 2]` uses integer floor-division for ½× block. For even h
   exact (h=4 → [2,4,8]); for odd h under-rounds (h=5 → [2,5,10] = 0.4×). Design says "½/1/2×";
   floor(h/2) is the standard integer approximation. Intent preserved. Not verdict-material.

5. **[ADVISORY — hash()-based RNG seeding reproducibility; non-blocking]**
   `:400,477` seed via `RNG_GLOBAL + hash(("EXP-024", …, int(gi))) % 100_000`. Python 3 randomizes
   string hashes (PYTHONHASHSEED), so exact CI bounds / p_perm / twin percentiles are not
   byte-reproducible across re-runs unless PYTHONHASHSEED is pinned. Inherited from EXP-022 (`:488`);
   not flagged in prior QA. Does NOT affect structural integrity gates (holdout, causal, tripwire
   logic are seed-independent). 5-seed median aggregation partially stabilizes bounds.
   Recommendation: pin PYTHONHASHSEED at execution, or use a deterministic digest. Not a gate.

6. **[ADVISORY — QA run 1 issue 3 (tripwire block vs h): RESOLVED]**
   `:373` clamps h_i to [1,12]; BLOCK_TRIP=12 (`:72`) ≥ all h_i by construction. Clamp guarantees
   equality at ceiling. No further action.
### Integrity-gate summary

| Gate | Status | Evidence |
|---|---|---|
| Holdout fence (first 49%, TEST unemitted, final-30% never loaded) | PASS | `:66,306-309`; no TEST emission |
| Causal provenance (u/m/s/k/HL ≤ t-1, open-to-open, confirmed-bar decisions) | PASS | `:80-95,131-132,140-149,178-182,193` |
| Tripwire (block-permute block ≥ h, must collapse) | PASS | `:254-267,412`; BLOCK_TRIP=12 ≥ h_i ≤ 12 |
| No local accounting (canonical xen only) | PASS | `:45-46`; grep confirms no banned primitives |
| No Python strategy backtest (availability screen, no fills/P&L) | PASS | emits rho/CI only; no fills/positions/P&L |
| Estimand reconciliation gate | N/A | no P&L/accounting object (design §9) |
| R1 carry-forward (hardened CI on binding cell, no N×P gate) | RESOLVED | `:388-429` unconditional; `full_ci` absent |
| Golden trace (first-3-post-warmup, all §10 fields) | PASS | `:491-516`; all fields present |
| Deviations block | none | — |

### Summary

R1 — the sole BLOCKING carry-forward from QA run 1 — is RESOLVED in code. The `full_ci = N×P` gate
is completely absent; the binding R_US/anchor-S/all>k/hedged cell receives the full hardened CI
battery (10k boots, 5-seed, block_sensitivity ½/1/2×, trimmed_mean, ci_low_seed_range, MDE)
unconditionally. The frozen construction is a single cell (median/raw/all>k/hedged/session-S) with
no sweep; single-worst/horizon/halves are disclosed continuity checks with lighter CI. Holm
corrects over valid pvals only (UNPOWERED excluded — QA issue 2 resolved). All four controls
(permuted-axis null, random-index twin, random-timing twin, tripwire) are present with ≥25 seeds /
≥1000 reps / block ≥ h. Holdout fence (first 49%, TEST unemitted, final-30% never loaded) is
sound. Causal provenance (signal ≤ t-1, open-to-open forward, confirmed-bar decisions) is sound.
The golden trace emits the first-3-post-warmup all>k events with all §10 fields. No local
accounting; canonical xen only; no fills/P&L (execution-agnostic availability screen).

Issues 2–4 are MINOR (non-blocking fidelity/rounding notes inherited from the vehicle). Issue 5 is
ADVISORY (hash()-based seeding reproducibility, inherited, non-gate). Issue 6 (QA run 1 advisory 3)
is RESOLVED by the h-clamp guarantee.

**Verdict: APPROVE** for the operator's execution gate. R1 is resolved; all integrity gates pass.
The operator may proceed to execution.