# D0 — Disclosure-Synthesis Memo (Phase 008, Tier 0)

**Date:** 2026-06-10.
**Type:** Desk artifact. No new computation; every number below is read from
existing EXP-030/EXP-031 result artifacts (paths cited). This memo (1) fixes the
EXP-034 declared cell family and its testing order, (2) records the verified
pyramid-policy table, (3) summarizes the exit-substitution profile that scopes
EXP-033/B2, and (4) lists every data-dependent design choice in Phase 008.

---

## 1. Per-instrument break-even map (EXP-030 `results/net_by_instrument.csv`)

Net = CONSERVATIVE costs, **before financing**. CI = 95% regime-cluster bootstrap.

| Cell | n | Gross abs (bps) | Net cons (bps) | 95% CI | RT_cons | Break-even RT |
| --- | --- | --- | --- | --- | --- | --- |
| **EURUSD-4h** | 39 | +15.38 | **+12.38** | [+2.67, +21.46] | 3.0 | 15.4 |
| **USTEC-4h** | 36 | +15.38 | **+10.38** | [−19.43, +36.28] | 5.0 | 15.4 |
| **XAUUSD-1h** | 207 | +6.00 | **+0.001** | [−4.86, +4.90] | 6.0 | 6.0 |
| XAUUSD-4h | 42 | +5.31 | −0.69 | [−22.53, +25.63] | 6.0 | 5.3 |
| EURUSD-1h | 243 | −0.06 | −3.06 | [−5.59, −0.70] | 3.0 | −0.1 |
| USTEC-1h | 188 | +0.77 | −4.23 | [−11.10, +3.03] | 5.0 | 0.8 |
| XAUUSD-5m | 2956 | +0.75 | −5.25 | [−5.60, −4.89] | 6.0 | 0.7 |
| EURUSD-5m | 2886 | +0.42 | −2.58 | [−2.81, −2.36] | 3.0 | 0.4 |
| USTEC-5m | 2828 | +0.58 | −4.42 | [−5.05, −3.76] | 5.0 | 0.6 |
| BTCUSD-5m | 4125 | +1.30 | −14.70 | [−15.74, −13.61] | 16.0 | 1.3 |
| BTCUSD-1h | 286 | −0.88 | −16.88 | [−35.71, +0.24] | 16.0 | −0.9 |
| BTCUSD-4h | 70 | +4.33 | −11.67 | [−72.89, +42.14] | 16.0 | 4.3 |

### 1.1 Declared cell family for EXP-034 (FIXED here; supersedes the design §5/A1 default)

**Mechanical declaration rule (predeclared):** declare exactly the cells whose
EXP-030 disclosure `net_cons` point estimate is > 0.

**Declared family (3 cells, in fixed testing order):**

1. **EURUSD-4h** (primary; +12.38, CI_low already > 0 pre-financing)
2. **USTEC-4h** (+10.38; n=36, half-width ≈ 27.9 bps — declared by rule, expected
   INCONCLUSIVE on power; stated honestly per the design's power-statement mandate)
3. **XAUUSD-1h** (+0.001; point ≈ 0, financing will push it negative — declared by
   rule, expected to fail)

**Deviation from the design default (recorded):** the design's default 6-cell
family included EURUSD-1h, USTEC-1h, and XAUUSD-4h. The verified map shows
EURUSD-1h is already EVIDENCE_AGAINST descriptively (CI entirely below 0, gross
negative before costs) and USTEC-1h / XAUUSD-4h have negative net points.
Declaring known-negative cells inflates the multiplicity family and costs power on
the live cells while adding no information — all 12 cells receive disclosed
descriptive CIs in EXP-034 regardless, so nothing is hidden or closed. Amended
within the design's "until Stage-1 scope freeze" window.

### 1.2 Testing procedure for EXP-034 (FIXED here; amends design §8.4 wording for A1)

**Fixed-sequence (hierarchical) testing replaces Holm for the A1 family:** test
EURUSD-4h at one-sided α = 0.05; only if it passes (net CI_low > 0), test
USTEC-4h; only then XAUUSD-1h. Stop at the first failure. Fixed-sequence testing
controls FWER at exactly 0.05 — the strict-gate spirit of §8.4 is preserved with
no leniency added. Rationale: the hierarchy is justified a priori by the headroom
ordering above, and Holm-3 (smallest-p threshold 0.0167) would risk failing the
primary cell on multiplicity alone: EURUSD-4h's pre-financing CI_low is +2.67 bps,
and the predeclared financing layer (≈1–2 bps on multi-day 4h holds) plausibly
moves its one-sided p into the 0.02–0.04 range — passing α = 0.05, failing 0.0167.
Choosing the test that protects the primary cell is admissible **only because it is
fixed before measurement**; it is recorded here, pre-results, as data-dependent
design. G2 (holdout admissibility) reads "passes the fixed-sequence at α = 0.05"
wherever design §8.4 says "Holm across the declared family" for A1.

## 2. Pyramid-policy table (EXP-030 `results/run_metadata.json` → `pyramid_net_split`)

Net = CONSERVATIVE, equal-weight aggregate per domain, before financing.

| Domain | n pyr / non-pyr | Net pyramid | Net non-pyramid | Gross abs pyr / non-pyr | Read |
| --- | --- | --- | --- | --- | --- |
| 5m | 6258 / 6537 | −7.51 | −7.50 | +0.77 / +0.86 | Tie — both cost-drowned |
| 1h | 443 / 481 | **−4.88** | −8.74 | **+3.31** / −0.72 | Pyramids carry the edge |
| 4h | 84 / 103 | **+15.44** | −12.49 | **+24.71** / −3.85 | Pyramids carry the edge |

**Implication (already encoded in design §5/B2):** a blanket "no-pyramid" variant
is contradicted on 1h/4h — pyramid legs are the *stronger* legs there. Pyramid
policy ∈ {all-legs, first-leg-only, pyramid-legs-only} is therefore a TRAIN-frozen
per-domain composition element of B2, selected mechanically (one-SE rule, simplicity
preference order: all-legs → first-leg-only → pyramid-legs-only), computed in
EXP-033 after H\*_d is fixed.

## 3. Exit-substitution profile (EXP-031 report/results)

| Domain | H=1: BTC exit vs FH(1), events / controls | H=6: BTC exit vs FH(6), events / controls | X_exit at H=6 (matched-control) |
| --- | --- | --- | --- |
| 5m | +0.42 / −4.19 bps | −0.60 / +2.47 bps | −3.06 [−3.45, −2.69] |
| 1h | +2.97 / −20.48 bps | −0.84 / +2.26 bps | −3.15 [−8.63, +2.57]† |
| 4h | — | — | **−27.14 [−46.47, −7.44]** |

† not leg-significant.

**Implication:** the FH-exit prize on 5m/1h events is ≈ +0.6–0.8 bps absolute —
small against a 3–7.5 bps cost gap. The realistic B2 case is **4h**, where the BTC
exit's matched-control drag is −27 bps and leg-significant. The design's B2
expectation set (5m/1h null expected) follows from this table.

## 4. EXP-033 H\*-selection objective — instrument set (FIXED here)

The TRAIN FH(H) net curve used for H\*_d selection is the **equal-weight mean over
EURUSD, USTEC, XAUUSD (BTCUSD excluded)**. Rationale: BTCUSD is excluded from every
declared tradability family by the break-even map (§1 — its 16 bps RT exceeds every
gross figure), so letting its cost structure shape H\* would optimize the exit for
an instrument no Tier-B confirmation will bind on. All four per-instrument curves
are disclosed. Data-dependent choice, recorded.

## 5. Register of data-dependent design choices (guardrail §7.4)

| # | Choice | Derived from | Where it binds |
| --- | --- | --- | --- |
| 1 | A1 declared family = {EURUSD-4h, USTEC-4h, XAUUSD-1h}, by mechanical net-point>0 rule | EXP-030 `net_by_instrument.csv` | EXP-034 scope |
| 2 | A1 fixed-sequence testing order EURUSD-4h → USTEC-4h → XAUUSD-1h | Same | EXP-034 scope; G2 reading for A1 |
| 3 | 5m and BTCUSD cells excluded from any declared tradability family | Same (break-even map) | EXP-034; Tier-B TEST families |
| 4 | Pyramid-policy menu {all, first-leg-only, pyramid-legs-only} as B2 composition element | EXP-030 `pyramid_net_split` | EXP-033 outputs; EXP-037 scope |
| 5 | B2 expectation set: realistic case is 4h; 5m/1h null expected | EXP-031 exit-substitution | EXP-037 scope |
| 6 | H\*-selection objective excludes BTCUSD | EXP-030 break-even map | EXP-033 scope |
| 7 | A3 dimensions themselves (chosen knowing the edge is cost-dominated and relative) | Phase 007 synthesis | EXP-035 scope |

All seven are fixed **before** any Phase 008 measurement. None may be revised after
any Tier-A result is read; changes after that point require a governance amendment.

## 6. Freeze note

The financing rates (EURUSD 0.6 / USTEC 1.2 / XAUUSD 1.2 / BTCUSD 10.0 bps per
calendar day, adverse-side) remain operator-amendable until the EXP-034 Stage-1
scope freezes. Items §1.1, §1.2, §4 freeze with this memo, subject only to operator
veto before the corresponding scope is approved.
