# EXP-022 — QA / Compliance Review (append-only)

## QA run 1 — 2026-07-06T10:14:26Z — mode: subagent — HEAD 50af382
Reviewed state: `50af382` + dirty tree (untracked `python/experiments/EXP-022/`, `EXP-021/`,
`VAL-007/`, `docs/.../cf-csrr-001*`, `checkpoints/…-009-…`). Only artifact under review:
`python/experiments/EXP-022/design.md` (22,674 bytes). No `code/` / `analysis_code/` present —
this is a **design pre-execution review** of an execution-agnostic availability screen (no C#
stage, no engine run; precedent EXP-008/009/021). Fresh-context self-check: this conversation did
NOT produce the design.

**Verdict: APPROVE.** No REVISE-level or REJECT-level defect. Ready for the operator's execution
gate. (QA APPROVE does not launch anything.) Two non-blocking disclosures noted below.

EXP-022 is the Indices mirror of EXP-021, which was APPROVED at its own run-2 after three REVISE
fixes. All three EXP-021 fixes are already present here by construction (see Regression-vs-EXP-021).

---

### Mandatory declaration blocks (design-requirements.md) — all 8 present

| # | Block | Location | Status |
|---|---|---|---|
| 1 | Mechanism (MECHANISM+DERIVED) | §1 | PRESENT, filled |
| 2 | Object-identity (3 sub-fields) | §2 | PRESENT, filled |
| 3 | Control validity proofs (per control) | §5 (3 blocks) | PRESENT, filled |
| 4 | Leak tripwire | §5 TRIPWIRE | PRESENT, filled |
| 5 | Interpretation bands (per stratum) | §7 | PRESENT, filled |
| 6 | Power statement | §8 | PRESENT, filled |
| 7 | Golden trace | §10 | PRESENT, filled |
| 8 | Integrity vs informative split | §9 | PRESENT, filled |

---

### Design-fidelity trace (design-internal coherence; no code yet)

| Design clause (§ref) | Cross-check | Verdict | Notes |
|---|---|---|---|
| Execution-agnostic carve-out (no engine/fills/P&L/estimand gate) | §1/§4/§9/§11 | MATCHES (honest) | No P&L/accounting object → nothing for `xen.estimand_validation` to reconcile; no edge-generating strategy → cTrader-primary rule doesn't bind. Precedent EXP-008/009/021, family card §Implementation path. Integrity carried by ≤t-1 provenance + tripwire + golden trace + holdout fence. Correctly framed, not an evasion. |
| Native single-factor, σ_i=+1 all (no sign-alignment) | top block + §3 | MATCHES | Equity indices all load positively on global equity risk; median/mean of log-moves from anchor is factor-coherent by construction. Removes EXP-021's USD-strength sign problem entirely → no JPY-cross deviation to reconcile (Issue 2 of EXP-021 cannot recur). Residual s_i=u_i−m still measures relative over/under-performance; MR of s_i is the substrate test. Defensible. |
| Open-to-open estimand (L-01) | §3 return row L103, §1 DERIVED L49-50, §10 (d) | MATCHES | `g_i(t,h)=ln(Open_i(t+1+h)/Open_i(t+1))` — entry next-bar OPEN, exit h bars later at OPEN; signal u/m/s/k/HL from confirmed RealClose ≤ t. Signal-basis and return-basis cleanly separated (EXP-021 Issue 1 already fixed here). Golden trace deterministic + bit-reproducible. |
| Native vehicle L-13: estimand/null/horizon from THIS mechanism | §1 DERIVED + §3 | MATCHES | Consensus-hedged forward reversion of a cross-sectional residual; within-bar cross-sectional identity permutation; horizon = residual's own AR(1) half-life. Explicitly not copy-pasteable onto another mechanism (§1 tail). All three specific to cross-sectional consensus reversion. |
| Permuted-axis PRIMARY null non-vacuity (B-6/EXP-012) | §5 PRIMARY | MATCHES | Re-pairs s_i(t) ↔ a different present member's forward idio → moves E[·]; median/mean consensus is label-invariant so |s| magnitudes preserved (dislocation-MATCHED), only i→i linkage destroyed. Not a mean-invariant single-series permutation. |
| Random-index twin disjointness (B-1) | §5 | MATCHES | Random member j≠argmax typically near-consensus (small |s|), forward idio ≈0 → different population than max-|s| tail. |
| Random-timing twin battery + L-13/L-19 | §5 | MATCHES | ≥25 seeds, percentile/rank read, battery-mean vs MDE; correctly demoted to SECONDARY (spurious-negative near consensus). |
| Tripwire collapses edge, L-07/EXP-012-clean | §5 TRIPWIRE | MATCHES | Temporal block-permute (block≥h) of the s→forward pairing → rho→0; block-permutes returns (not price-path rotation, L-07); moves the conditional mean (not mean-invariant, EXP-012). |
| Multiplicity: PRIMARY N×P max-stat over 16 cells; others robustness/secondary | §3.1 | MATCHES | Significance claimed ONLY at build N × anchor P (max-stat over 16 A×B×C×D cells per instrument, family-wise). Overlays (A, anchor S) recomputed as sign/band stability, NOT new significance. Build R has its OWN internal max-stat per bloc. Net rule is a CONJUNCTION (clears primary max-stat ∧ sign-stable both anchors ∧ survives ≥2/3 builds) — a strictly HIGHER bar, not 96 bites. Overlays can only downgrade a lead, never manufacture one. FWER genuinely controlled. |
| Object-identity for availability screen (L-16) | §2 | MATCHES | Per-event forward idio return, NOT the multi-leg episode P&L object (EXP-023/V5). Kill criterion substrate-level (is s_i MR); family disposition checkpoint-only → L-16 respected (per-event null cannot retire a structure-borne P&L family here). |
| Per-stratum bands; UNPOWERED≠negative; collapse-fraction | §7 | MATCHES | Per instrument×cell; UNPOWERED (n<100 / MDE>1bp / null band>effect) excluded from negatives (B-5); collapse fraction for every control + tripwire (L-15); pooled disclosure-only unless homogeneity shown (L-03). |
| Build-A activity gate causality | §3 | MATCHES | Member dropped when its 4h bar range < 10th-pct of own trailing 4h true-range OR outside liquid session. Tested range is bar t's own (confirmed at bar-t close, acted t+1 open) — part of the ≤t confirmed-close signal, consistent with §3 causality footnote; session-calendar is static. No leak. |
| Test selection L-20-hardened | §6 | MATCHES | Circular block≥h, ≥10k×5-seed battery, block_sensitivity ½/1/2×, trimmed_mean; "CI excludes zero" not a bootstrap p; permuted-axis max-stat multiplicity at PRIMARY. |
| Causal ≤t-1 across anchor/consensus/residual/threshold/HL | §3/§9/§10 | MATCHES | All signal inputs from confirmed RealClose ≤ t; anchor = last rollover close ≤ t; act next open. Trace asserted in analysis_code, diffed by QA. |
| Complexity budget / single hypothesis | §4 | MATCHES (operator-mandated scope) | 3 stat families, 1 module, ≤6 plots. One falsifiable question (HYP-002); 16 cells read MARGINALLY per axis. The 6 plots (vs comparative ≤5 guideline) and the 3-builds×2-anchors expansion are operator-mandated (top block), single hypothesis — informative, not a budget violation. |
| Anchor axis S (per-index session) as robustness only | §3 | MATCHES | Mixed per-member session anchors make members incomparable at a common bar; correctly kept SECONDARY, common 00:00-UTC (P) is PRIMARY. |

---

### Golden-trace diff (hand-evaluation of §10 vs the frozen PRIMARY construction)

Frozen cell: build N × anchor P (00:00-UTC), A=median, B=raw, C=single-worst, D=hedged,
k=trailing-median, h=HL. Rule: first 3 single-worst fade events post-warmup (not hand-picked) —
deterministic. ✓ Developer-independent (frozen first-3 rule, no hand-pick).

- (a) present-member set at t (≥4), m=median of present u (label-invariant): hand-checkable. ✓
- (b) s_i, k, HL from confirmed RealClose ≤ t; anchor = last 00:00-UTC close ≤ t: hand-checkable. ✓
  (σ_i=+1 for all members — even simpler than EXP-021's signed basis; no sign to verify.)
- (c) selected = argmax|s|, dir = −sign(s): hand-checkable. ✓
- (d) inputs ≤t-1, forward return uses RealOpen: entry Open(t+1), exit Open(t+1+h) — open-to-open,
  no close leakage. Formula matches §3; hand-verifiable. ✓
- (e) rho recomputed matches emission bit-for-bit: reproducible given the open-to-open basis. ✓

Minor (non-blocking, carried from EXP-021 run-1): h_i (AR(1) half-life) and k (trailing-median) are
series-fitted quantities, not literally hand-computable. QA takes them as emitted inputs (HL/k
tables) and verifies downstream by hand. In-sample HL/k fit over TRAIN applied to TRAIN events is
acceptable for a characterisation screen and involves no holdout/TEST contact. §10 does not state
this explicitly — recommend the analyst note it in the emitted golden_trace (disclosure, not a
blocker; EXP-021 shipped identically and was APPROVED).

---

### Governance & boundary

- **Holdout:** TRAIN = first 49% (0.7×0.7); TEST band not emitted; final-30% never loaded (§4/§9).
  VAL-007 PASS independently verified — `holdout_rows_read=0`, 6.1M analysis rows validated,
  2.62M holdout rows sealed at first touch. Indices basket 10/10 admitted. PASS.
- **`check_no_local_accounting`:** N/A (no P&L/accounting object) and honored — canonical `xen`
  helpers only (§11). PASS.
- **No Python strategy backtest:** correct — execution-agnostic screen, no fills/P&L. PASS.
- **Registry preconditions:** CF-CSRR-001 REGISTERED; multiplicity-registry row `HYP-002 = EXP-022`
  is **REGISTERED — READY** (VAL-007 PASS); test-read-ledger records VAL-007 unblocks EXP-022 with
  0 counted reads / 0 slots. Verified. PASS.
- **No auto-verdict thresholds:** §7/§9 informative bands only; no auto-RETIRE; substrate kill is
  reported-to-operator, family disposition checkpoint-009-only. PASS.
- **Deviation provenance:** no unapproved deviation. Native single-factor build removes EXP-021's
  JPY-cross deviation; the all-three-builds + both-anchors expansion is operator-mandated (top block,
  2026-07-06) with §3.1 multiplicity honesty. PASS.
- **Elicitation hygiene:** no open plain-language questions embedded. N/A.

---

### Regression-vs-EXP-021 (the three run-1 REVISE issues)

| EXP-021 issue | Status in EXP-022 |
|---|---|
| 1 [HIGH] close-to-close vs open-to-open estimand | Pre-fixed — §3/§1/§10 are open-to-open throughout. |
| 2 [MED] JPY-cross exclusion vs family card | Cannot recur — native single-factor equity basket, σ_i=+1 all, no sign-alignment / no crosses. |
| 3 [LOW] vacuous momentum-contrast control | Pre-fixed — §5 has the "DRIFT-CARRY CHECK deferred to EXP-023" note (ρ_mom≡−ρ_rev), no vacuous control; the 3 remaining controls are all non-vacuous. |

---

### Issues
None (blocking). Two non-blocking disclosures:
- **N1 (disclosure):** §10 should state that HL and k are taken as emitted series-fitted inputs
  (verified downstream, not literally hand-computed). Carried from EXP-021 run-1; not a blocker.
- **N2 (predeclared-UNPOWERED, already disclosed):** build R Asia bloc (n=3) yields a coarse
  within-bar identity permutation null (few distinct pairings) and thin counts. §3/§8 already
  predeclare this UNPOWERED and route it through B-5 (never read as a negative). Correctly handled;
  noted so the analyst reports the permutation granularity, not a spurious p_perm, on small blocs.

---

### Verdict
**APPROVE.** All 8 mandatory blocks present and validly filled; estimand/null/horizon are
mechanism-native and not copy-pasteable (L-13); the PRIMARY permuted-axis null is dislocation-matched
and non-vacuous for the mean statistic (B-6/EXP-012); the tripwire is L-07/EXP-012-clean; §3.1
multiplicity accounting genuinely controls family-wise error (significance only at N×P max-stat over
16 cells; overlays/secondary can only downgrade, net rule is a strict conjunction — not 96 bites);
object-identity (L-16) and the no-estimand-gate carve-out are honest and correct for an availability
screen; golden trace is deterministic and developer-independent; holdout fence + VAL-007 gate + 0
reads independently verified. Ready for the operator's execution gate.
