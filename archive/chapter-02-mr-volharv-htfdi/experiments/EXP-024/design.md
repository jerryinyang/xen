# EXP-024 — Design (CF-CSRR-001 — US-bloc session-anchor availability primary)

**Title:** Pre-registered US-regional-bloc consensus-residual reversion — powered, single-family
availability primary chasing the EXP-022 USTEC lead (R_US bloc, session-open anchor, hedged, all>k,
4h, TRAIN-only, execution-agnostic).
**Family:** CF-CSRR-001 (checkpoint-009). **Tier:** exploratory (decide-before-retire). **Reads:** 0.
**Status:** DESIGN → QA (fresh context). **Vehicle:** Python availability screen — no engine, no fills,
no P&L, no `xen.adjudication` estimand gate (same tier as EXP-021/022; precedent EXP-008/009).
**New registered branch (multiplicity rule 4):** must be registered before screening — new row
`CF-CSRR-001/HYP-002b` (US-bloc session-anchor availability primary), checkpoint-009-scoped,
operator-directed. Registration is the honest guard on controlled thesis-shopping (see §0).

## 0. Provenance & honest framing (controlled thesis-shopping — read first)

EXP-022 selected USTEC **post-hoc** as the best of 10 instruments × 6 constructions on TRAIN. Re-testing
USTEC on the **same TRAIN** is in-sample and cannot prove out-of-sample. This experiment is legitimate ONLY
as a **controlled** follow-up (KB `controlled_thesis_shopping_allowed`): the construction is **frozen and
pre-registered** (no sweep — one A/B/C/D choice), the multiplicity family is the **4 US-bloc members**
(Holm-controlled), and the **binding bar is the hardened block-bootstrap CI USTEC previously FAILED**
(EXP-022 ci_low −0.58, effect ≈ MDE 5.28) — not the permutation-only read that lit it up. A clean pass here
does **not** license deployment; it only decides whether USTEC is worth an EXP-023 tradability read (and,
later, the gated HYP-004 TEST read). This is stated so QA can reject any framing that reads a TRAIN pass as
confirmation.

---

## 1. Falsifiable question + mechanism

**Q.** On the 4-member US equity bloc at 4h TRAIN, with the session-open-anchored **hedged** residual and an
`all>k` (powered) selection frozen in advance: does fading a member's consensus residual earn a positive
consensus-hedged forward return that clears the **hardened block-bootstrap CI at the ≥1 bp band**, both
temporal halves, and both twins — for USTEC (power question) AND for ≥1 sibling (mechanism-vs-artifact
question)?

```
MECHANISM: The 4 US index CFDs (USTEC, US500, US2000, US30) are tightly cointegrated intraday around one
common US-equity factor. When one member's move (accumulated from its NY-session open) deviates from the
4-member consensus, that idiosyncratic residual is transient local flow (one index's thin extended-hours
tape, lagged propagation of a sector shock) and reverts toward the consensus within ~its residual half-life.
The exploited regularity = the negative predictive relation between a member's current cross-sectional
residual s_i(t) and its forward IDIOSYNCRATIC (consensus-hedged) return. Cadence = per confirmed 4h bar,
each member with |s_i|>k (all>k). P&L object at the tradability tier = single-position episode (EXP-023);
HERE, execution-agnostic, the object is the per-event forward idiosyncratic return over horizon h.

DERIVED:
  estimand = rho_i(t,h) = -sign(s_i)*idio_i, idio = g_i - G  (consensus-hedged forward, open-to-open)
  null     = within-bar cross-sectional identity permutation (dislocation-matched) + Holm over 4 members
  horizon  = h_i = clamp(round(2*HL_i),[1,12]); HL_i = AR(1) half-life of s_i under the session anchor
  test     = mean rho with HARDENED block-boot CI (L-20) at the >=1 bp band + both-halves + twin deltas
```

Native to a cross-sectional bloc-reversion mechanism (consensus-hedged residual, cross-sectional permutation
null, residual's own half-life) — not copy-pasteable to a single-instrument or directional mechanism (L-13).

---

## 2. Object identity declarations

```
OBJECT-IDENTITY:
  measurement object == trading object: PARTIAL-BY-DESIGN. Measures the per-event forward idiosyncratic
    return (availability), NOT the EXP-023 single-position episode P&L. Correct object for an availability
    screen; the kill/graduate read is per-event/substrate-level (L-16 binds only for multi-leg P&L retirement,
    which this tier cannot do).
  measured conditioning event == traded entry event: YES. Conditions on confirmed |s_i(t)|>=k at bar close
    (data <= t-1), fade acted next bar OPEN. EXP-023 vehicle V5 = ACTIVE confirmed-breach entry at next open
    = the SAME event. No passive-limit seam (B-4) imported.
  effect-splitting windows non-overlapping: forward horizons OVERLAP across events (rolling); handled by
    circular block-bootstrap CI (block >= h, L-07/L-20) — never iid CIs on overlapping windows.
```

---

## 3. Construction (FROZEN — pre-registered, no sweep)

**Members (4):** USTEC, US500, US2000, US30 (σ_i=+1 all; near-24h US CFDs → 90%-coverage 4h filter drops
only ~20%, so no EU/Asia-style thinning). Consensus over the members present at t (≥3 of 4 required).

| Element | Frozen value |
|---|---|
| Basket | R_US bloc {USTEC, US500, US2000, US30}; consensus over present members (≥3) |
| Anchor | **session-open reset (S)** — the SAME per-index NY-session-open anchor rule as EXP-022 `screen.py` (frozen; reused verbatim, not re-derived) |
| Accumulated move | `u_i(t) = ln(P_i(t)/anchor_i(t))`, P = 4h RealClose, accumulates from the session reset |
| Consensus A | **median** of {u_i(t)} (pre-declared single value) |
| Residual | `s_i(t) = u_i(t) − m(t)` |
| Normalization B | **raw** (pre-declared) |
| Selection C (PRIMARY) | **all>k** — every present member with `|s_i(t)|>k`; `k` = trailing-median of per-bar `max_i|s_i|` (causal, `<t`). Powered (more events than single-worst) |
| Hedge D | **hedged** — `idio_i = g_i − G` (mechanism-faithful idiosyncratic) |
| Fade | `−sign(s_i(t))` |
| Forward (open-to-open) | `g_i(t,h) = ln(Open_i(t+1+h)/Open_i(t+1))`; `G(t,h)=median({g_j})`; signal from RealClose ≤ t |
| Estimand | `rho_i(t,h) = −sign(s_i(t))·idio_i(t,h)` |
| Horizon | `h_i = clamp(round(2·HL_i),[1,12])`; HL_i = AR(1) half-life of s_i under the session anchor |

**Robustness (disclosed, NOT a second primary):** the **single-worst hedged** read (the exact EXP-022 lead
form) on the same 4 members — continuity check that the all>k powering did not change the sign. Horizon
1·/2·/3·HL sign-stability disclosed (as EXP-021/022). **No other axis is swept** — A, B, D, anchor are frozen.

**Multiplicity family = the 4 US-bloc members** (all>k primary). Significance = permutation identity null per
member + **Holm over the 4 members**. This is the entire family — no 16-cell max-stat, no cross-construction
overlays (that was EXP-022's job). Causality: anchor/u/m/s/k/HL all ≤ t−1; return from next open.

---

## 4. Scope

| Item | Value |
|---|---|
| Instruments | 4 US-bloc indices (above) |
| Domain | 4h only (`xen.bar_aggregator`, `min_coverage=0.90` — US indices lose ~20%, no EU/Asia thinning) |
| Data | latest-glob 5-year files (VAL-005/VAL-007); US bloc all reach 2021-06-02 |
| Split | **TRAIN = first 49%**. TEST band NOT emitted. Final-30% holdout NEVER loaded |
| Alignment | shared 4h `CloseTime`; member enters m(t) if present; ≥3-of-4 required for a valid consensus bar |
| Complexity budget | 2 stat families (reversion-Δ hardened bootstrap CI + permuted-axis Holm null); ≤4 plots; reuse EXP-022 `screen.py` (frozen construction, US-bloc/all>k args) |
| Engine | N/A — execution-agnostic screen; no fills/P&L; no accounting object |
| Reads / slots | 0 counted TEST reads, 0 slots (TRAIN-only) |

---

## 5. Controls (validity proofs)

```
CONTROL random-index-twin:
  question: does fading the residual beat fading a random present bloc member? (is |s| informative)
  population: same bars/timing, fade assigned to a uniformly random present member j (≥25 seeds). DISJOINT:
             a random member is typically nearer consensus → different forward idio than the fired member.
  bite/MDE: seed battery → null band; signal−twin vs MDE (§6). Co-designed, not a fixed plant.
  non-vacuity: re-pairs the fade with a different member's forward idio → moves the conditional mean.
  expected if H true: signal >> twin (Δ>0). If H false: Δ≈0.
  disclosure: collapse fraction (twin/signal) per member (L-15).

CONTROL random-timing-twin (BATTERY ≥25 seeds, L-19):
  question: does dislocation-conditioning (|s|>k) beat firing at random times? (timing)
  population: random bars, matched count/member, direction −sign(s_i) at that bar. DISJOINT: random bars
             mostly non-extreme.
  bite/MDE: per-member seed SD → MDE; binding read = signal PERCENTILE in the 25-seed distribution + battery
            mean vs MDE (rank read, L-19).
  non-vacuity: changes which s_i and forward idio enter the mean.
  L-13 caveat: random-timing reads spuriously negative near consensus → SECONDARY twin; PRIMARY null = the
            dislocation-matched permutation below.
  disclosure: collapse fraction + percentile per member.

CONTROL permuted-axis-null (PRIMARY significance null; dislocation-matched, L-13/L-08):
  question: does member i's residual predict i's OWN forward reversion beyond an equally-dislocated random
            pairing? (the cross-sectional linkage, dislocation held fixed)
  population: within each bar, permute {s_i} ↔ {forward-idio owner} across present members (≥1000 perms).
             Preserves each member's marginal |s| + market state; destroys only the i→i linkage. Median
             consensus is label-invariant → m,s magnitudes untouched.
  bite/MDE: permutation width per member → effective MDE; multiplicity via HOLM over the 4 members.
  non-vacuity: re-pairs s_i with a different member's forward idio → moves the conditional mean (not a
            mean-invariant permutation; EXP-012/B-6 compliant).
  expected if H true: observed rho beyond the permutation tail (p_perm small, Holm-significant). If H false:
            inside the band.
  disclosure: p_perm (Holm-adjusted) + observed-vs-null band per member.
```

DRIFT-CARRY (momentum-signed inverted twin) — DEFERRED to EXP-023 (vacuous here: ρ_mom = +sign(s)·idio ≡
−ρ_rev, exact algebraic negation, no independent attribution). Booked as an EXP-023 requirement (USDCAD lesson).

```
TRIPWIRE future-destroyer (MUST collapse):
  temporal block-permutation (block ≥ h, L-07) of the (s_i(t) → forward-return) pairing: s_i(t) pairs with a
  forward return from an unrelated time. A causal reversion edge MUST collapse to rho≈0.
  expected collapse fraction ≈ 1.0.
  vacuity check: moves the conditional mean E[idio|s_i] (not a price-path rotation, not a mean-invariant P&L
  permutation). Surviving rho ⇒ leak ⇒ REJECT.
```

---

## 6. Test selection (candidate-aware)

| Purpose | Method | Why matched |
|---|---|---|
| Half-life | AR(1) on s_i under session anchor → HL_i | sets horizon from mechanism scale (L-13) |
| Effect (rho) — **BINDING** | mean rho + `xen.evaluation.block_bootstrap_ci` (circular block ≥h, ≥10k×**5-seed** battery; `block_sensitivity` ½/1/2×; `trimmed_mean` disclosure) | the hardened CI USTEC FAILED in EXP-022 — the honest bar (L-20) |
| Significance | permuted-axis p_perm + **Holm over 4 members** | dislocation-matched, small honest family (L-08/L-13) |
| Twin separation | signal−twin Δ + percentile (random-index, random-timing battery) | extremeness vs timing (L-19 rank read) |
| Robustness | single-worst continuity + both-temporal-halves + horizon 1/2/3·HL sign | powering/period/horizon stability |

Non-parametric/bootstrap only; no fixed referee stack (retired from service). Report "CI excludes zero", never
a bootstrap p-value (L-20).

---

## 7. Interpretation bands (per member — no binaries)

```
BANDS (per US-bloc member, on rho, bps of idiosyncratic forward return):
  SUPPORTED:    mean rho ≥ +1 bp AND HARDENED block-boot ci_low > 0 (5-seed, block-stable) AND both temporal
                halves sign-stable AND beats BOTH twins (Δ>0) AND p_perm Holm-significant AND tripwire collapses
  WASH:         |mean rho| < max(1 bp, seed-SD) — reverts≈random, not a refutation (L-11)
  CONTRADICTED: mean rho ≤ −1 bp with ci_high < 0 (residual continues)
  UNPOWERED:    n_events < 100 OR MDE > effect OR permutation band wider than effect — never a negative (B-5).
                US500 flagged likely-UNPOWERED (thin under both selections).
POOLED: any cross-member aggregate is disclosure-only (L-03). Collapse fraction disclosed for every control + tripwire.
```

**Operator read (informative, no auto-verdict):**
- **USTEC SUPPORTED + ≥1 sibling SUPPORTED** → real bloc mechanism → graduates to EXP-023 tradability.
- **USTEC SUPPORTED, siblings null/UNPOWERED** → single-instrument idiosyncrasy (thin base; operator judges
  whether one instrument warrants a tradability read).
- **USTEC still fails the hardened ci_low even powered** → effect-at-MDE confirmed → retire evidence.

---

## 8. Power statement

```
POWER: US bloc, 4h TRAIN ≈ 3,000–3,200 valid bars/member (US CFDs, ~20% coverage loss, no session thinning).
  all>k (k=trailing-median max|s|): each member fires on the bars where its |s|>k ≈ upper fraction of its own
    |s| distribution → expect ~800–1,500 events/member for USTEC/US2000/US30; US500 fewer (it was rarely even
    the single-worst — likely 300–700, possibly < floor).
  MDE at n≈1,000, hardened block-boot 4h: ≈ 1.5–3.5 bps. KEY TRADE-OFF (pre-declared): all>k admits moderate
    dislocations, so the per-event effect may FALL below EXP-022's single-worst +4.7 bps even as n rises — the
    experiment resolves whether ci_low clears zero at the powered n or the effect dilutes to the MDE.
  Predeclared UNPOWERED risk: US500 (thin under both selections) — disclose, never a negative (B-5).
```

---

## 9. Integrity vs informative split

```
HARD (block): TRIPWIRE collapse (rho→0 under temporal block-permute; surviving edge ⇒ REJECT); HOLDOUT
  (TRAIN first 49%; TEST band unemitted; final-30% never loaded; any touch ⇒ REJECT); CAUSAL PROVENANCE
  (u/m/s/k/HL ≤ t−1; return from next open; asserted in analysis_code, QA-diffed). Estimand-reconciliation
  gate N/A (no P&L/accounting object).
INFORMATIVE (operator judges): all rho magnitudes, hardened CIs, p_perm/Holm, twin Δ/percentiles, collapse
  fractions, half-lives, both-halves/horizon stability. No materiality thresholds, no readiness floors, no
  gate conjunctions beyond the pre-declared SUPPORTED band, no auto-RETIRE.
```

---

## 10. Golden trace (QA diffs before sign-off)

```
GOLDEN-TRACE: the FIRST 3 all>k fade events after warmup (session + HL/threshold window) in TRAIN, on the
  frozen construction (R_US, session anchor S, median/raw/hedged). For each event (member i, bar t):
  timestamp t (4h CloseTime); present members (≥3) and their u_j(t); m(t)=median; s_i(t)=u_i−m and the test
  |s_i|>k; fade side −sign(s_i); h_i from HL_i; g_i=ln(Open_i(t+1+h)/Open_i(t+1)), G=median(g_j), idio=g_i−G,
  rho_i. QA hand-verifies: (a) present set + median label-invariance; (b) s_i,k,HL from RealClose ≤ t, session
  anchor = last NY-session-open close ≤ t; (c) |s_i|>k fired; direction −sign(s); (d) inputs ≤ t−1, forward
  open-to-open entry Open(t+1)/exit Open(t+1+h); (e) rho matches emission bit-for-bit. First-3-post-warmup is
  the frozen rule — no hand-picking.
```

---

## 11. Deliverables

- `analysis_code/` — reuse EXP-022 `screen.py` (frozen construction; US-bloc / all>k / anchor-S / hedged
  args), single-family driver; hardened `xen.evaluation` CI; permuted-axis Holm null; twins + tripwire.
  Canonical `xen` only; no local accounting.
- `results/` — per-member rho + hardened CI (+ seed range + block sweep + trimmed_mean) + p_perm(Holm) + twin
  Δ/percentile + collapse fractions; HL table; single-worst continuity + both-halves + horizon tables;
  `golden_trace.parquet`.
- `plots/` — ≤4: rho + hardened CI per member (band annotated); signal-vs-twins; permutation null bands;
  both-halves/horizon stability.
- `analysis.md` (data-analyst) — evidence for+against per member + recommended (non-final) verdict.

**Registration precondition:** register `CF-CSRR-001/HYP-002b` (US-bloc session-anchor availability primary)
in `multiplicity-registry.md` + family card before screening (operator-directed, checkpoint-009).

**Next stage:** QA-compliance (FRESH context) → operator execution gate → data-analyst → operator verdict.
Availability screen: no engine, no estimand-validation gate; integrity gates are §9.
