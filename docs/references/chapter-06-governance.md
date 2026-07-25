# Chapter 06 Governance — Structural Volatility + Direction Programme

**State:** `CHECKPOINT-017 OPEN / SPDR-012+013 COMPLETE / REFLECTION-C SIGNED (O3+A) / SPDR-014+015+016+017 DESIGNS COMPLETE`

**Governing RAW brief:** `.ignore/what-next/alts/vol-direction-structural-programme-raw.md`

**Family:** `CF-VOLDIR-001` — `REGISTERED` 2026-07-23

**Checkpoint:** `docs/experiments-docs/checkpoints/2026-07-23-017-structural-vol-direction-programme/design.md`

This file records the approved route and enforcement boundary for the structural
vol → direction expectancy → combination programme. It is **not** a reopening of
`CF-VOLCONV-001` / SPDR-011 late range-break conversion.

## 1. Fixed route

1. `SPDR-012` — volatility characterisation (reliability). **COMPLETE.**  
2. `SPDR-013` — direction expectancy (SMA + ZigZag; not win-rate). **COMPLETE.**  
3. Mid-checkpoint reflection — **SIGNED:** O3 direction-agnostic only; Decision A.  
4. O3 sequence (designs complete; runs per operator gate):  
   - `SPDR-014` — Group 1: zone / mispricing event / post-event MOMO vs MR (**first**).  
   - `SPDR-015` — Group 2: level-regime transitions + ordinal ZZ magnitude (order flexible).  
   - `SPDR-016` — Group 3a: refine named 014 residual (**start-gated** on 014 pin).  
   - `SPDR-017` — Group 3b: independent predicted-price mispricing (operator original #3);
     **not** gated on 014 residual success; same characterisation method as 014.  
5. `XENA-VOLDIR-001` — **only if** a graduated cost-surviving base emerges + separate authority.

Sequence brief: `.ignore/what-next/alts/cf-voldir-o3-zone-event-sequence.md`

All SPDR stages are TRAIN-only, disposition/characterisation screens under
`docs/references/spdr-lane.md`. Historical analysis-TEST and the global holdout are never loaded.

**AMENDMENT-S1 (2026-07-23):** cross-instrument stability is **not** required for SUPPORTED labels
on SPDR-014/015/016; multi-symbol agreement is credibility only. DIRECTION: NEUTRAL.

**Universe (AMENDMENT-U1):** top **25** instruments by 30-day total USD traded volume
(`sum(close×volume)` on fenced 1m bars), ranked on TRAIN only with
`asof = train_end_utc` (window `[train_end−30d, train_end)`). Pin:
`docs/signal-registry/candidate-families/cf-voldir-001-universe.json`. Applies to SPDR-012/013/014
and any later XENA universe definition unless the operator freezes a subset at reflection C.

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
- Design registration for SPDR-014/015/016/017 does **not** authorise execution.  
- Each SPDR requires its own `design.md` before run; SPDR lane self-check replaces full QA subagent
  unless operator demands more.  
- Operator gates: execution per SPDR; D graduate after 014 (+ optional 015/016); XENA separate.

## 5. Relation to checkpoint-016

- `CF-VOLCONV-001` / SPDR-011 L1 closed NOT SUPPORTED remains evidence-only until that
  checkpoint’s retrospective.  
- Chapter 06 proceeds independently under this governance file.
