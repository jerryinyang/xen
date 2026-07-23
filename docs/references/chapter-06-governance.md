# Chapter 06 Governance — Structural Volatility + Direction Programme

**State:** `CHECKPOINT-017 OPEN / FAMILY REGISTERED / SPDR DESIGNS PENDING`

**Governing RAW brief:** `.ignore/what-next/alts/vol-direction-structural-programme-raw.md`

**Family:** `CF-VOLDIR-001` — `REGISTERED` 2026-07-23

**Checkpoint:** `docs/experiments-docs/checkpoints/2026-07-23-017-structural-vol-direction-programme/design.md`

This file records the approved route and enforcement boundary for the structural
vol → direction expectancy → combination programme. It is **not** a reopening of
`CF-VOLCONV-001` / SPDR-011 late range-break conversion.

## 1. Fixed route

1. `SPDR-012` — volatility characterisation (reliability).  
2. `SPDR-013` — direction expectancy (SMA + ZigZag; not win-rate).  
3. Mid-checkpoint reflection — freeze combination or stop/branch.  
4. `SPDR-014` — combination / extraction (or authorised direction-agnostic branch).  
5. `XENA-VOLDIR-001` — **only if** SPDR-014 graduates a cost-surviving base.

All SPDR stages are TRAIN-only, disposition/characterisation screens under
`docs/references/spdr-lane.md`. Historical analysis-TEST and the global holdout are never loaded.

## 2. Cost boundary (inherits Chapter-05 no-spread amendment)

- Spread cost unavailable and not charged (`spread_rt_bps=null`,
  `PARTIAL_FEES_FUNDING_ONLY`).
- Reported cost understates total cost; reported net is overstated.
- Every money-bearing report must disclose that caveat.
- No deployability claim from SPDR outputs.

## 3. Hard refusals

- Primary direction device = SPDR-011 confirmed daily-range breakout without new evidence.  
- Win-rate as primary direction metric.  
- Combination or XENA before A and B quantified.  
- Unbounded indicator/ML zoo without frozen arms.  
- TEST / holdout contact.  
- Automatic family open/retire from experiment code (retrospective only).

## 4. Enforcement

- `docs/experiments-docs/INDEX.md` is the live status record.  
- Registration authorises design work for SPDR-012 next; it does **not** authorise execution.  
- Each SPDR requires its own `design.md` before run; SPDR lane self-check replaces full QA subagent
  unless operator demands more.  
- Operator gates after A, B, C, D before the next stage.

## 5. Relation to checkpoint-016

- `CF-VOLCONV-001` / SPDR-011 L1 closed NOT SUPPORTED remains evidence-only until that
  checkpoint’s retrospective.  
- Chapter 06 proceeds independently under this governance file.
