# Chapter 05–06 Experiment Index

## Chapter 06 — active

Checkpoint-017 open. Family `CF-VOLDIR-001` registered. SPDR-012 **run complete, awaiting operator gate A**; SPDR-013 **run complete, awaiting operator gate B / Reflection C**.

| ID | Family | Status | Purpose |
|---|---|---|---|
| SPDR-012 **(SPDR)** | CF-VOLDIR-001 | **RUN COMPLETE — AWAITING OPERATOR GATE A** — 0 counted reads, 0 slots, TRAIN-only. Integrity self-check all-PASS; universe pin exact; fresh-context QA (REVISE → findings fixed) and fresh-context analysis both complete. **No PASS/STOP call made** (AMENDMENT-T2 — §6.4 unsatisfiable as frozen; three bases reported side by side). Vol magnitude reliably forecastable on H1/H4 across all 15 forecastable symbols (CONFIRM median rank IC 0.338 / 0.301, homogeneous I²=0); D1 weaker and one symbol contradicted. Two binding qualifications: the IC is span-dependent, and 26–75% of it is between-month level structure — **no within-day skill**. Ships with **no hard leak gate** (AMENDMENT-T1); causality rests on construction asserts + two independent code re-derivations | Volatility characterisation — reliability of prediction/modelling |
| SPDR-013 **(SPDR)** | CF-VOLDIR-001 | **RUN COMPLETE — AWAITING OPERATOR GATE B / REFLECTION C** — 0 reads, 0 slots, TRAIN-only. 25 sym × (6 SMA + ZZ) × 5 exit modes × 2 clocks × 2 bands = 2940 cells, 1.64M episodes. Integrity self-check all-PASS; universe pin exact; engine parity 0.0; `--jobs` parallel bit-identical to sequential. QA (REVISE → all 10 fixed). Amendments operator-signed 2026-07-23: DEV-1/T1 (future-destroy tripwire → informative — outcome-side destroy can't separate causal timing from a leak on a mean-P&L object), A3 (exit-mode decomposition + ZZ structural leg), E1 (medians). **Signed direction NOT adequate:** 0/2940 SUPPORTED; net cost-fatal (≈ 13.5 cost floor); no net sign-timing edge (derangement pctile ≈0.5 H1, <0.5 M15); ZigZag ≈ SMA benchmark (Δ≈0). **MFE:** geometry gives back reached favourable (60–280 bps) but it is **ambient, not signal-granted** (signal horizon-MFE ÷ random ≈ 1.0) → direction-agnostic harvest question, not a signed-direction fix. **One powered positive:** ZZ next-swing **magnitude** forecast IC 0.34–0.46 (vol/path-noise null). Analysis recommends direction-agnostic branch for Reflection C; operator decides | Direction expectancy bps (SMA + ZigZag; not win-rate) |
| SPDR-014 | CF-VOLDIR-001 | **REGISTERED / BLOCKED ON REFLECTION C** | Combination / extraction after mid-checkpoint freeze |
| XENA-VOLDIR-001 | CF-VOLDIR-001 | **RESERVED** — requires SPDR-014 graduation + separate design/QA/approval | Portfolio/search on graduated bases only |

See checkpoint-017 and `docs/references/chapter-06-governance.md`.

## Chapter 05 — closed path (no further authorised work)

| ID | Family | Status | Purpose |
|---|---|---|---|
| SPDR-011 | CF-VOLCONV-001 | **CLOSED** — operator 2026-07-23: L1 **NOT SUPPORTED** (also UNPOWERED for ~10 bps); L2–L5 not opened; see `report.md` | One frozen DESIGN event table; L1 partial-cost characterisation only |
| EXP-099 | CF-VOLCONV-001 | **RESERVED / NOT AUTHORISED** — Run-1 evidence not accepted for graduation | Frozen-rule Nautilus reproduction and physicality only |

Checkpoint-016 retrospective (family disposition for CF-VOLCONV-001) still pending and independent of Chapter 06.
