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
