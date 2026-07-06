# EXP-021 — QA / Compliance Review (append-only)

## QA run 1 — 2026-07-06T00:27:20Z — mode: subagent — HEAD 50af382
Reviewed state: `50af382` + dirty tree (untracked `python/experiments/EXP-021/`,
`docs/.../cf-csrr-001*`, `checkpoints/...-009-...`). Only artifact under review:
`python/experiments/EXP-021/design.md` (19,183 bytes). `code/` and `analysis_code/` empty —
this is a **design pre-execution review** (availability screen; no C# stage, no engine run,
precedent EXP-008/009). Fresh-context self-check: this conversation did NOT produce the design.

**Verdict: REVISE** (3 issues: 1 high, 1 medium, 1 low). No REJECT-level defect (no holdout
contact, tripwire present, causal intent stated). Route: `quant-designer` (design defects).

---

### Mandatory declaration blocks (design-requirements.md) — all 8 present

| # | Block | Location | Status |
|---|---|---|---|
| 1 | Mechanism (MECHANISM+DERIVED) | §1 | PRESENT, filled |
| 2 | Object-identity (3 sub-fields) | §2 | PRESENT, filled |
| 3 | Control validity proofs (per control) | §5 (4 blocks) | PRESENT, filled |
| 4 | Leak tripwire | §5 TRIPWIRE | PRESENT, filled |
| 5 | Interpretation bands (per stratum) | §7 | PRESENT, filled |
| 6 | Power statement | §8 | PRESENT, filled |
| 7 | Golden trace | §10 | PRESENT, filled |
| 8 | Integrity vs informative split | §9 | PRESENT, filled |

No block missing → not an auto-reject on completeness.

---

### Design-fidelity trace (design-internal coherence; no code yet)

| Design clause (§ref) | Cross-check | Verdict | Notes |
|---|---|---|---|
| Native vehicle L-13: estimand/null/horizon from THIS mechanism | §1 DERIVED + §3 | MATCHES | Consensus-hedged forward reversion of a cross-sectional residual; within-bar cross-sectional identity permutation; horizon = residual's own AR(1) half-life. Explicitly contrasted vs CF-MR own-price. Not copy-pasteable. |
| Permuted-axis null non-vacuity for a mean stat (B-6/EXP-012) | §5 PRIMARY | MATCHES | Re-pairs s_i(t)↔a different member's forward idio; for single-worst the argmax member's ±1 sign is applied to an unrelated member's forward return → moves E[·], permutation dist centres ≈0. Not a mean-invariant outcome-multiset permutation. |
| Null dislocation-matched (L-13) | §5 PRIMARY | MATCHES | Symmetric consensus (median/mean) is label-invariant, so each s_i magnitude is preserved; only the i→i linkage is destroyed. Correct. |
| Random-index twin disjointness (B-1) | §5 | MATCHES | Random member j≠argmax is typically near-consensus (small |s|) → different population than the max-|s| tail. |
| Random-timing twin battery + L-13/L-19 caveat | §5 | MATCHES | ≥25 seeds, percentile/rank read, battery-mean vs MDE; correctly demoted to SECONDARY (spurious-negative near consensus). |
| Tripwire collapses edge, L-07/EXP-012-clean | §5 TRIPWIRE | MATCHES | Temporal block-permute (block≥h) of forward returns → s(t) pairs with unrelated-time return, mean→0. Block-permutes returns (not a price-path rotation, L-07); moves the mean (not mean-invariant, EXP-012). |
| Per-stratum bands; UNPOWERED≠negative; collapse-fraction | §7 | MATCHES | Per instrument×cell; UNPOWERED (n<100 / MDE>1bp / null band > effect) excluded from negatives (B-5); collapse fraction for every control + tripwire (L-15); pooled disclosure-only (L-03). |
| Object-identity for availability screen (L-16) | §2 | MATCHES | Per-event forward idio return, NOT the multi-leg episode P&L object (EXP-023/V5). Kill criterion is substrate-level (is s_i MR); family disposition checkpoint-only → L-16's "per-event null cannot retire a structure-borne P&L family" is respected. |
| Governance: TRAIN-only, holdout sealed, 0 reads, no auto-verdict | §4/§7/§9 | MATCHES | TRAIN=first 49% (0.7×0.7); TEST band not emitted; final-30% never loaded; 0 counted reads/slots; no auto-RETIRE, family disposition checkpoint-only. |
| No evaded gate: no estimand-validation / cTrader stage | §1/§4/§9 | MATCHES (honest) | No P&L/accounting object → nothing for `xen.estimand_validation` to reconcile; no edge-generating strategy → cTrader-primary rule (edge experiments) doesn't bind. Integrity carried by ≤t-1 provenance + tripwire + golden trace. Correctly framed, not an evasion. |
| Test selection L-20-hardened | §6 | MATCHES | Circular block≥h, 5-seed battery, block_sensitivity ½/1/2×, trimmed_mean; "CI excludes zero" not a bootstrap p; permuted-axis max-stat for multiplicity. |
| Causal ≤t-1 across anchor/consensus/residual/threshold/HL | §3/§9/§10 | **DEVIATES** | Intent stated (all inputs ≤t-1, act next open) BUT the forward-return **formula contradicts it** — see Issue 1. |
| Consensus population = 7 USD pairs, JPY crosses excluded | top block + §3 | **DEVIATES** | Family card says "decompose JPY crosses to USD legs **where possible**"; design **excludes** them. Presented as operator decision but diverges from the cited card — see Issue 2. |
| Momentum-contrast control informativeness | §5 | **DEVIATES** | ρ_mom ≡ −ρ_rev identically (algebraic negation) → zero independent attribution info — see Issue 3. |
| Anchor causal-reset (operator G0 fix) | top block + §3 | MATCHES | Rolling daily/session rollover anchor with causal reset, accumulating intraday, HL-keyed; matches family-card §Fixed-first-branch G0 (2026-07-06 operator fix) and checkpoint-009. The terse "prior-4h-close" 1-bar line is correctly superseded. |
| Complexity budget / single hypothesis | §4/§1 | MATCHES | 3 stat families, ≤5 plots, 1 module (within comparative budget); 16 cells read MARGINALLY per axis under max-stat, one falsifiable question (HYP-001) — not 16 hypotheses. |

---

### Golden-trace diff (hand-evaluation of §10 vs the frozen construction)

Frozen cell: A=median, B=raw, C=single-worst, D=hedged, daily-reset anchor, k=trailing-median,
h=HL. Rule: first 3 single-worst fade events post-warmup (not hand-picked) — deterministic. ✓

Hand-verifiable items (a)–(e) check out **conditional on the return-basis fix**:
- (a) σ_i signs (USD-quote −1, USD-base +1): hand-checkable. ✓
- (b) m = median of 7 u_i (label-invariant): hand-checkable. ✓
- (c) selected = argmax|s|, dir = −sign(s): hand-checkable. ✓
- (d) inputs ≤t-1, forward return starts next OPEN: **cannot be verified bit-for-bit** because
  §3's `g_i(t,h)=σ_i·ln(P_i(t+h)/P_i(t))` with `P=RealClose` is close-to-close, contradicting
  "next OPEN" (Issue 1). Determinism of item (e) depends on resolving this.
- (e) rho recomputed matches emission bit-for-bit: **blocked by Issue 1** — the estimand formula
  is ambiguous (close-to-close per §3 table vs open-to-open per §3 note/§9/§10).

Minor (non-blocking): h_i (AR(1) half-life) and k (trailing-median) are series-fitted quantities,
not literally hand-computable; QA takes them as emitted inputs (HL table / k column) and verifies
downstream by hand. §10 should state this explicitly. HL fit in-sample over full TRAIN then applied
to TRAIN events is acceptable for a characterisation screen and is disclosed — not a leak (no
holdout/TEST contact).

---

### Governance & boundary

- **Holdout:** TRAIN-only, first 49%; TEST band not emitted; final-30% never loaded (§4/§9). PASS.
- **`check_no_local_accounting`:** N/A (no P&L/accounting object) and honored — no accounting
  primitives introduced; §11 states canonical `xen` helpers only. PASS.
- **No Python strategy backtest:** correct — execution-agnostic screen, no fills/P&L (§1/§4). PASS.
- **Registry preconditions:** CF-CSRR-001 REGISTERED (family card), checkpoint-009 scoped,
  HYP-001 = EXP-021; 0 counted reads / 0 slots stated. PASS.
- **No auto-verdict thresholds:** §7/§9 informative bands only; no auto-RETIRE; disposition
  checkpoint-only. PASS.
- **Deviation provenance:** anchor causal-reset deviation from terse G0 line = operator-approved
  (family card + checkpoint, 2026-07-06). PASS. JPY-cross exclusion = **NOT cleanly evidenced**
  against the card (Issue 2). REVISE.
- **Elicitation hygiene:** no open plain-language questions to operator embedded. N/A.

---

### Issues

**Issue 1 — HIGH — Forward-return estimand is close-to-close in the formula but open-to-open in
the prose; golden trace is therefore non-deterministic and the measurement is non-tradable/
look-ahead-adjacent.**
- FAILING_ARTIFACT: `design.md` §3 construction table (rows "Forward USD-signed return"
  `g_i(t,h)=σ_i·ln(P_i(t+h)/P_i(t)), P=4h RealClose` and "Consensus forward" `G(t,h)`), §1 DERIVED,
  §10 golden-trace items (d)/(e).
- Problem: `g_i` uses `RealClose(t)`→`RealClose(t+h)` (close-to-close, entered at the SAME close
  that defines the signal `s_i(t)` — a zero-latency same-price entry). This contradicts §3's own
  note "return measured from next open forward (open-to-open)", §9 "return from next open", and §10
  (d) "forward return starts at next OPEN". The programme mandates open-to-open (binding, `_pipeline-
  config` Programme Principles). Because L-01 shipped a false positive through exactly a Python
  close-referenced acausal outcome, and this run's integrity rests on the ≤t-1 lag + golden trace,
  the ambiguity is verdict-material: item (e) "rho matches bit-for-bit" cannot be hand-verified.
- REQUIRED CHANGE: redefine `g_i(t,h)` (and `G(t,h)`, the estimand, and the §10 golden trace)
  consistently open-to-open — entry at Open(t+1), exit at Open(t+1+h) (or the design's intended
  causal open basis) — so the formula matches the stated next-open action, and re-state the golden
  trace so `rho` is hand-recomputable and deterministic.

**Issue 2 — MEDIUM — JPY-cross EXCLUSION deviates from the family card's "decompose to USD legs
where possible" and is asserted (not evidenced) as an operator decision; it changes the consensus
population.**
- FAILING_ARTIFACT: `design.md` top "Operator construction decisions" block + §3 Members line
  (`JPY crosses EURJPY/GBPJPY/AUDJPY excluded`).
- Problem: the family card (`cf-csrr-001.md` §Currencies consensus) and checkpoint-009 both direct
  "handle JPY crosses explicitly by **decomposing to their USD legs where possible**." The design
  instead **excludes** all three (disclosure-only naive-median contrast). Excluding vs decomposing
  changes the consensus/residual population (7 vs up to 10 legs) — a verdict-material population/
  anchor choice. The mechanism rationale (a scalar-USD consensus cannot define a JPY-cross residual)
  is scientifically defensible, but it is presented as an operator decision without citing where the
  operator approved the *exclusion* specifically, and it diverges from the canonical card text QA
  can see.
- REQUIRED CHANGE: either (a) cite the explicit operator approval for the exclusion (record it as an
  approved deviation, with the decompose-where-possible default explicitly overridden), or
  (b) reconcile with the card (decompose the crosses to USD legs as the card directs). Do not carry
  an operator-attributed population change that the cited source contradicts.

**Issue 3 — LOW — The momentum-contrast control is the algebraic negation of the estimand, so it
carries no independent attribution information and its stated pre-check can never fire.**
- FAILING_ARTIFACT: `design.md` §5 CONTROL momentum-contrast.
- Problem: `ρ_mom = +sign(s_i)·idio_i` and the estimand `ρ_rev = −sign(s_i)·idio_i` → `ρ_mom ≡
  −ρ_rev` event-by-event. The stated pre-check "reversion-specific ⇒ ρ_rev>0 AND ρ_mom<0" is one
  condition written twice, and the failure case "ρ_rev>0 AND ρ_mom≥0" is impossible — the control
  discloses nothing and cannot separate reversion from drift/carry. (The genuine drift-carry check
  is the momentum-signed *inverted* twin / carry-matched benchmark, correctly deferred to EXP-023.)
- REQUIRED CHANGE: either define a genuine drift/carry benchmark here (e.g. unconditional idio drift
  in the fade direction, or a direction/exposure-matched carry twin) or drop the momentum-contrast
  block and its reversion-specificity claim (fold the drift-carry attribution into the random-timing
  twin + the EXP-023 inverted twin, which already address it).

---

### Summary
Strong, mechanism-native design: all 8 mandatory blocks present and validly filled; the primary
permuted-axis null is genuinely dislocation-matched and non-vacuous for the mean statistic; the
tripwire is L-07/EXP-012-clean and will collapse a causal edge; per-stratum + UNPOWERED + collapse-
fraction discipline is correct; object-identity (L-16) and the no-estimand-gate framing are honest
and correct for an availability screen. Held at **REVISE** on: (1) a close-to-close vs open-to-open
estimand contradiction that breaks golden-trace determinism and the tradability discipline [HIGH];
(2) a JPY-cross exclusion that deviates from the family card and is asserted rather than evidenced
as operator-approved [MEDIUM]; (3) a vacuous momentum-contrast control [LOW]. Fix and re-run QA.

---

## QA run 2 (re-review) — 2026-07-06T00:33:49Z — mode: subagent — HEAD 50af382
Reviewed state: `50af382` + dirty tree; `design.md` re-read after run-1 REVISE. `code/` and
`analysis_code/` still empty (design-stage availability screen). Verifying only the three run-1
issues were fixed and introduced no regression.

**Verdict: APPROVE.**

### Fix verification (each run-1 issue re-checked against the design text)

| Issue (run 1) | Fix location | Verdict | Evidence |
|---|---|---|---|
| 1 [HIGH] close-to-close vs open-to-open contradiction | §3 return row (L103), §1 DERIVED (L51-52), §10 golden trace (L265, L268-272) | **RESOLVED** | §3 now `g_i(t,h)=σ_i·ln(Open_i(t+1+h)/Open_i(t+1))` — entry next-bar OPEN, exit h bars later at OPEN; explicit "signal u/m/s/k/HL use confirmed RealClose ≤ t; TRADED forward return uses RealOpen (open-to-open, L-01)". §1 DERIVED carries the same open-to-open clause. §10 writes the open formula and adds item (d) "the forward return uses RealOpen: entry Open(t+1), exit Open(t+1+h) — open-to-open, no close leakage". The RealClose(t)→RealClose(t+h) formula is gone; signal-basis (RealClose ≤ t) and return-basis (RealOpen from t+1) are now cleanly separated → golden trace is deterministic and item (e) bit-for-bit reproducible. |
| 2 [MED] JPY-cross exclusion asserted, not evidenced | top block L12-17 | **RESOLVED** | Now labelled "**APPROVED DEVIATION from family card §Currencies consensus**"; states the operator chose "7 USD pairs, drop crosses" over the all-10 currency-vector build in this design turn's 2026-07-06 elicitation, and books the currency-strength-vector build (which would service the crosses) as a deferred registered branch. Provenance is explicit and the card default is named as the overridden option. |
| 3 [LOW] vacuous momentum-contrast control | §5 L174-178 | **RESOLVED** | The momentum-contrast CONTROL block is removed; replaced by "DRIFT-CARRY CHECK — deferred to EXP-023 (not run here)" note that states ρ_mom=+sign(s)·idio ≡ −ρ_rev is an exact algebraic negation carrying no independent attribution, and books the genuine momentum-signed INVERTED twin at the validatory tier (EXP-023). No vacuous control remains in §5; the remaining three controls (random-index, random-timing battery, permuted-axis PRIMARY null) are all non-vacuous and were APPROVED in run 1. |

### Regression check
- No new estimand/null/horizon drift: §1 DERIVED, §5 PRIMARY null, and §5 TRIPWIRE unchanged in
  substance and still L-13/L-07/EXP-012-compliant; the open-to-open edit is confined to the return
  basis and does not alter the permutation or tripwire logic.
- Mandatory blocks: still all 8 present and filled.
- Governance unchanged: TRAIN-only (first 49%), holdout sealed, 0 reads, no auto-verdict, family
  disposition checkpoint-only — all intact.
- §3 causality footnote (L113-114) still says "decision at bar close, return measured from next open
  forward (open-to-open)" — now consistent with the corrected formula (no residual contradiction).

### Verdict
All three run-1 issues resolved with no regression. **APPROVE** — ready for the operator's
execution gate. (QA APPROVE does not launch anything; execution remains the operator's gate.)
