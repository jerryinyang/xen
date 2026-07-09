# Phase 004 — Cross-Domain MR Renewal (CF-MR-004) — Retrospective

**Phase number:** 004 (Chapter 02)
**Design ratified:** 2026-07-01 (G0)
**Retrospective written:** 2026-07-03
**Status:** COMPLETE — **CF-MR-004 RETIRED (operator D1, 2026-07-03): EXP-014c CREDIBLE_NEGATIVE_RETIRE.** The fixed-parameter cross-instrument spread MR fade has a real but narrow availability (4h JP225 ≫ EURUSD) that does **not** convert to a net edge even when the traded object exactly matches the measured two-barrier race — because the traded **entry** (limit fill at the band touch) is a different conditioning event than the measured one (open after confirmed close-breach). Fourth consecutive MR family closed at the capture/attribution seam. Spin-out: the extend-arm own-price ladder field → **CF-MR-005 REGISTERED** (operator D2).
**Slots/reads:** 0 candidate slots; 0 counted TEST reads; global holdout sealed throughout; frozen referee untuned (L-12).

**Design reference:** [design.md](design.md) · amendments [001](amendment-001-faithful-full-strategy-redo.md) / [002](amendment-002-exit-set-faithfulness-redo.md) / [003](amendment-003-streamlined-s8-symmetry-control.md) / [004](amendment-004-lean-bracket-redesign.md)
**Experiments:** EXP-013 (HYP-001, CONFOUNDED), EXP-014 (HYP-002, NOT-TRADABLE), EXP-014b (HYP-003, REJECT_LEAK), EXP-014c (HYP-004, CREDIBLE_NEGATIVE_RETIRE) — see `python/experiments/<ID>/report.md`.
**Operator decision record:** `.ignore/temp/d1/exp-014c-findings-and-decisions.md` (D1–D6, binding).

---

## 1. Phase objective recap

O1 (design): does the complete precalc limit-order strategy on 4 fixed-parameter cross-instrument anchor series (S5 redo, S6, S7, S8) produce (a) reversion-to-anchor beyond a dislocation-matched control (availability) AND (b) net-positive P&L under the frozen referee (tradability), per stratum, on TRAIN? Full-strategy-first (operator mandate), price-primary in-engine, from-scratch family code (L-13), MR screen informative-not-gating (L-12). Honest prior: LOW (all prior price-derived MR families closed).

## 2. The arc — four experiments, two amendments-in-place

| Step | Verdict | What it established |
|---|---|---|
| **EXP-013** (HYP-001, 4 series × 32 cells, native orders) | **CONFOUNDED** (downgraded from NOT_TRADABLE, amendment-001) | The strategy that ran was not the strategy proposed: form-1 event-reversion exit absent, form-2 TP frozen at entry → peer-side reversion never exits; the "~30% favorable-hit" was a static-TP hit rate. Not a family reading. Lesson **L-14** (exit-set diff at the pre-exec gate). Record retained. |
| **EXP-014** (HYP-002, faithful redo, 152 cells / 38 binding strata) | **NOT-TRADABLE (faithful)** | Both proposal-named exits fire (form-1 281 / refreshing form-2 1898 / horizon 1266) → L-14 discharged. Frozen 4h referee: **0/38 net- AND gross-admit, homogeneous (no masking)**; availability does not separate at 4h vs matched control. Mechanism = capture-vs-dispersion wash (per-trade −57…+29 bps). Power caveat: 19/38 cells bite-fail (per-bar mean referee vs discrete bracket, L-12 mode-2). RETIRE recommended; operator instead directed the amendment-003/004 exploratory track. |
| **EXP-014b** (HYP-003, S8 only, symmetry two-barrier availability, 1h+4h, 220 strata) | **REJECT_LEAK, 0 TRADABLE** (audited; C1 label logic + C2 both-leg weighting fixed analysis-only) | Every 1h availability raw-pass **survives the peer-feed phase-shift** → own-price auto-reversion, the S8 basket *dilutes* it (EURUSD live 0.508 vs shift 0.688) → S8-at-1h retired. Collapse-verified availability narrowed to **4h JP225 (p_inward 0.696, ci_low 0.638; replicated z1.5) + weakly 4h EURUSD (0.589/0.520)**. Moving-mean exit = small form-2 wins vs large form-1 anchor-drift losses ≈ 0 gross (the moving-target loss engine). Extend-arm own-price harvest first flagged here. |
| **EXP-014c** (HYP-004, lean bracket — trade the measured object; 198 native runs + 33 shift twins, 262 cells) | **CREDIBLE_NEGATIVE_RETIRE** (audit PASS, 0 Critical; W1 relabel of the verdict.json headline) | Both prespecified primaries (e3/none/z20 JP225, EURUSD) **powered + bite-valid + net-fail** (JP225 +0.26 bps/bar, ci_low −1.84; EURUSD +0.28, −0.46); 0 Holm admits in the binding family. Census: NULL 218 / UNPOWERED 22 / NOT_TRADABLE 14 / NET_ADMIT 4 / REJECT_LEAK 4. Family retires on it (D1). |

## 3. Mechanism — why the confirmed availability did not convert

**The loss is at the entry seam, not the exits** (EXP-014c audit §5.2, raw-data traced). The 014b measurement conditions on a **confirmed close-breach** (depth ≥ band, read at the next open); the strategy fills a **resting limit at the band touch** — a shallower, earlier, adversely-selected conditioning event (D = z\*σ exactly, the marginal dislocation). JP225 realized TP-share **0.52** (CI 0.39–0.66) vs measured p_inward **0.696**; a symmetric ±D race at ~52% pays the spread. Decoupling is direct: 20/32 JP225 TP fills occurred **without** spread reversion; 15/24 time-stopped legs saw the spread revert while the frozen price TP never filled; EURUSD 0/20 stop-outs coincided with a spread reversion (the SL fires exactly when the basket signal is jointly wrong).

**The E0→E3 exit decomposition worked as an instrument:** freezing the TP removes most of E0's moving-target loss engine (JP225 −0.58 → +0.26 net/bar); the symmetric SL subtracts value; the time-stop is benign. **No exit rule unlocks the entry** — re-opening CF-MR-004 requires a confirmed-breach entry object under a new D0, not another exit design.

## 4. Discovery — the extend-arm field → CF-MR-005

Deweighting the leak test and ranking all 262 EXP-014c cells by net ci_low: **61 cells > 0, of which 53 never Holm-admitted — every one an extend/allow arm; no `none` arm is positive.** Spans both z\*, all four exit sets, 10/11 instruments on the powered read (the raw ci_low>0 set touches all 11; USDJPY's cells are unpowered); the three strongest cells positive every year 2021–2024 (US2000 e3/extend/z15 +10.7/+17.5/+5.3/+9.2 bps/active-bar). Per-leg P&L fattens with ladder depth (US2000 L0 +2.8 / L1 +10.5 / L2 +26.3 bps/leg). Cost stress: NZDUSD survives 3×, AUDUSD 2×, US2000 1× only. Under the 60h phase-shift the edge retains 50–85% → the basket supplies a trigger, not the harvest ⇒ **inadmissible as CF-MR-004 evidence (attribution), robust on its own terms**. One mechanism: **ladder scale-in on 4h dislocations harvesting short-horizon own-price mean reversion.**

Disposition (operator D2/D3): **CF-MR-005 REGISTERED** (basket-free trigger; mechanism characterisation before any tradability claim; cost realism binding early; native ladder availability per L-13; no exit-stack rescues per P-02). Phase-shift-control semantics on mixed P&L deferred behind the characterisation (D3). EXP-015 (CF-MR-005/HYP-001, analysis-only mechanism characterisation) designed and pre-exec-gated post-phase.

## 5. Outcomes vs objectives

| Objective | Outcome | Evidence |
|---|---|---|
| O1(a) availability | **Real but narrow** — only 4h JP225 (0.696) + weakly EURUSD (0.589) survive the phase-shift collapse test; all 1h raw passes were own-price leaks. | EXP-014 (no 4h separation, faithful vehicle), EXP-014b (collapse-verified narrowing). |
| O1(b) tradability | **NO — credible negative.** Primaries powered + bite-non-vacuous + net-fail; the measurement-matched bracket was the family's declared last shot. | EXP-014c (audit PASS, 0 Critical; all key numbers re-derived from raw emissions). |
| Family disposition | **RETIRED (D1)**; all per-cell statuses stand (D4); prior statuses retained, nothing deleted. | `candidate-families/cf-mr-004.md`, multiplicity registry family close-out. |
| Unplanned yield | Extend-arm field → **CF-MR-005 registered** (D2); W3 collapse-fraction rule → KB lesson (D5). | EXP-014c report §6 / audit §5.4. |

## 6. Lessons (for chapter-rollover Extract)

1. **Entry-seam / conditioning-event matching.** Measure→trade translation must match the **conditioning event at the fill**, not just the barrier object: a resting-limit touch (marginal dislocation, adverse selection) is a different event than a confirmed close-breach, and the availability measured on the latter does not transfer. Exit-side fidelity (the whole E0→E3 axis) cannot repair an entry-side mismatch. (EXP-014c; lesson-candidate for the KB.)
2. **W3 — attribution controls must report the collapse fraction, not only a binary admit.** US2000 extend/z15's shift twins stayed CI-positive at every exit and flipped only on the 3.0-bps L5 materiality leg (2.3–2.6 bps), while the same cell at e0/z15 passed the full stack under shift — a binary read binarizes noise at the admit bar. Filed as **L-15** (`docs/knowledge-base/lessons-and-amendments.md`).
3. **L-14 (originated + discharged in-phase).** A silently-dropped proposal-named exit ships a confounded verdict; the pre-exec gate now diffs implemented exits against the proposal's named exits. The faithful redo confirmed the confound was real but not verdict-flipping.
4. **The amendment-in-place discipline paid.** Two frozen-design confounds (exit set, EXP-013; label logic + both-leg weighting, EXP-014b) were handled by dated amendments + reruns/analysis-fixes, keeping every record on the books and the arc auditable.
5. **A structurally vacuous arm is a design smell, not data.** e1/none (no SL/time-stop + reentry-none) blocks re-arming for years (EURUSD: 1 trade in 5y) — exclude such arms from attribution narratives at design time (EXP-014c I1).

## 7. Governance ledger

- **Slots:** 0 consumed across the phase (all four experiments were TRAIN-only family probes).
- **Counted TEST reads:** 0. **Holdout:** sealed throughout (per-symbol first-49% TRAIN fence, byte-identical EXP-013 → 014c, audit-verified).
- **Referee (L-12):** frozen 4h referee untuned by any candidate.
- **Audits:** EXP-013 audit superseded by amendment-001 review (downgrade); EXP-014 PASS 0 Critical; EXP-014b 2 Critical found + fixed analysis-only (family outcome unchanged); EXP-014c PASS 0 Critical / 3 Warnings (W1 headline relabel, W2 session-flag normalisation, W3 collapse-fraction rule).
- **Registry:** `cf-mr-004.md` RETIRED with full status history retained; `cf-mr-005.md` REGISTERED (0 slots at registration); multiplicity registry HYP-001…HYP-004 rows + family close-out + CF-MR-005 registration block entered.

## 8. Status: CLOSED

Phase 004 is concluded. CF-MR-004 is retired at the entry-seam: availability real-but-narrow, tradability credibly negative on the measurement-matched object. The programme's next step is CF-MR-005 mechanism characterisation (EXP-015, designed and gated), with the phase-shift-semantics study deferred behind it (D3).
