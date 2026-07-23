# SPDR-011 — Report

**Family:** `CF-VOLCONV-001`  
**Checkpoint:** `2026-07-22-016-volatility-direction-conversion`  
**Status:** **CLOSED** — operator final verdict 2026-07-23  
**Band:** TRAIN DESIGN only; 0 counted TEST reads; holdout sealed  

## Question

Does a causally known **HIGH** daily-volatility state, after a completed four-hour break of the prior
UTC-day range, leave **positive signed residue** over one fixed four-hour episode after taker fees,
discrete funding, and a 2 bps execution allowance (spread unavailable / not charged)?

## Mechanism (registered)

Daily vol predicts magnitude, not sign. Completed range-break supplies sign. Edge exists only if
enough signed movement remains after the breakout under partial costs.

## Method summary

- Nautilus DESIGN emission, five symbols, A13 path; artifact
  `data/nautilus_runs/SPDR-011/artifact-bundle/design.parquet` (1,390 events; 394 HIGH with 4h path).
- Ordered layers L1–L5 predeclared; **only L1 opened** (operator scope).
- Analyst own code under `analysis_code/`; canonical costs via `xen.evaluation`.
- Integrity: fence PINNED, holdout untouched, causal provenance, fill anchors, no local accounting;
  future-destroy sentinel + collapse recorded; real-edge survival `NOT_APPLICABLE` (raw L3 not SUPPORTED).

## L1 key evidence

**Estimand:** HIGH-state mean `partial_net_2bps` (gross signed 4h − fees − funding − 2 bps).

| Stratum | n | mean | median | trim20 | CI (date-block) | MDE | Label |
|---|---:|---:|---:|---:|---|---:|---|
| BTCUSDT | 54 | −21.1 | −15.3 | −22.5 | [−54.6, +6.6] | 39 | UNPOWERED |
| ETHUSDT | 54 | −4.4 | +5.9 | −8.7 | [−40.7, +21.6] | 40 | UNPOWERED |
| SOLUSDT | 115 | +58.8 | −30.6 | −23.6 | [−24.7, +143.4] | 93 | UNPOWERED |
| DOGEUSDT | 71 | +47.5 | −26.2 | −20.5 | [−50.7, +139.2] | 96 | UNPOWERED |
| XRPUSDT | 100 | −50.6 | −35.5 | −44.5 | **[−94.2, −18.2]** | 47 | UNPOWERED (CI excludes 0, negative) |
| POOLED (disclosure) | 394 | +9.4 | −23.5 | −27.4 | [−30.2, +53.4] | 37 | UNPOWERED / not homogeneous |

**For (thin):** pooled mean positive at 0/2/5 bps allowance before concentration checks; gross mean
+22.8 bps before costs; occupancy part-time as designed.

**Against (decisive):**
1. One date (2022-10-29, DOGE-only) supplies ~99% of pooled total; without it mean ≈ +0.1 bps.
2. Design independence unit (UTC date): date-weighted mean **−15.3 bps** (sign flip).
3. Median / trimmed / body (|x|≤500) all negative; win-rate 0.44.
4. Drop top 5 legs → mean −17.8; top-decile concentration extreme.
5. Cross-symbol span ~109 bps; pooling not legitimate for a common claim.
6. Leave-one-symbol / leave-one-third / chronological halves unstable.
7. Every stratum UNPOWERED for a ~10 bps target (realised σ ~401 bps vs design σ 100 assumption).
8. Spread not charged → every net figure **overstated**.

**Informal adjuncts (not formal L2/L3; not disposition-bearing alone):**
- MID/LOW on same emission also lack reliable post-cost remnant; all medians negative.
- Absolute moves still larger in HIGH than MID/LOW (magnitude story).
- TEMP-SPDR-011B (deleted after use): 4h vol clock + top-25 liquid names → HIGH partial mean **−13.4**,
  all terciles negative after partial costs; abs still ranks with vol. Does not rescue L1.

## Integrity

| Check | Result |
|---|---|
| Estimand gate (per-cell expect + family manifest) | PASS (all five cells) |
| Provenance / holdout / non-STUB fence | PASS |
| Fill open-to-open anchors | PASS |
| Cost rebuild vs `xen.evaluation` | PASS (0 mismatches) |
| Future-destroy sentinel | PASS; real-edge rule NOT_APPLICABLE |

Note: pipeline CLI `validate_family(... --expect all five)` false-fails per-symbol cells; regenerated
via `analysis_code/gate_estimand.py` with correct scoping.

## Verdicts

| Role | Verdict |
|---|---|
| **Analyst recommendation** | **NOT SUPPORTED at L1**, and **UNPOWERED** for a small (~10 bps) true effect. Apparent pooled positive is concentration/regime artifact. |
| **Operator final (2026-07-23)** | **Accept analyst recommendation.** L1 **NOT SUPPORTED**. L2–L5 not advanced. EXP-099 not authorised. |

**Claim boundary:** not fully-net, not cost-complete, not tradable, not deployable.

## Route consequences

- **L2–L5:** not opened; STOP after L1 economics.
- **CONFIRM:** not opened.
- **EXP-099:** remains RESERVED; start gate (“Run-1 rule/evidence accepted”) **not met**.
- **Family `CF-VOLCONV-001`:** status unchanged here (`REGISTERED`). Family open/retire only at
  operator-signed checkpoint retrospective. Evidence row appended to family card.

## Artifacts

- `design.md`, `qa-review.md`, `analysis.md` (L1)
- `code/`, `analysis_code/`, `results/` (`estimand_validation.json`, `l1_estimand.json`, …)
- Emission: `data/nautilus_runs/SPDR-011/`

## Follow-ups (optional; not auto-authorised)

- Checkpoint retrospective: family RETIRE vs formal shadow park.
- Not licensed by this result: new vol indicator, new breakout definition, new horizon/exit grid, or
  signed-flow pattern family (source brief + family card exclusions).
