# Results: EXP-094 — 4h Readiness + Falsification Re-Screen (RSI-2 fade / EXIT-RCT)

**Phase 021 · CF-MR-001/HYP-002 · `D0-amendment-004`+`005` · TRAIN-only · 0 slots · 0 counted TEST reads ·
holdout sealed · determinism PASS · audit PASS (re-audit after the corrected-bite-check rerun).** Experiment
verdict: **`ADMIT_4H`** — the 4h domain is admitted as a domain expansion of the bare RSI-2 fade + EXIT-RCT
lever (0 new candidate slots).

## Summary

On the **6 powered 4h cells** (AUDJPY, EURJPY, EURUSD, GBPJPY, USDCHF, XAUUSD), the bare RSI-2 fade's
net-of-cost EXIT-RCT edge **survives the matched-distance oscillation falsification 6/6** — real EXIT-RCT beats
a same-distance favourable limit fired at random times on every powered cell (`delta_lo` 0.19–0.27 ATR), and it
**also** beats the nearer realized-capture-distance null 6/6 (sensitivity, `delta_lo_realized` 0.17–0.30). The
mechanism is a **completion-rate lift**: entering at a genuine RSI extreme raises the reversion-completion hit
rate from ~65% (random timing) to ~99% (real), turning a net-negative oscillation baseline into a net-positive
edge. **So the 4h edge is signal-driven, not generic oscillation harvesting** — EXP-089's 4h dead-by-absence
(1/14) is, on these cells, a metric-specific false negative of the ~3-bar MFE_med availability statistic. The
binding falsification statistic is FPR-controlled and powered (bite-check GREEN; 1h positive control 5/5).

**Two load-bearing qualifications:** (1) the powered breadth is **6 cells, not the 12 TEMP-091 implied** — the
readiness gate excluded 7/13 (incl. the indices USTEC-4h/US2000-4h); (2) `ADMIT_4H` opens the 4h domain for the
EXP-092/093 sequence but is **not** a tradability confirmation — that remains a counted-TEST question.

## Detailed findings

### Finding 1 — Readiness corrects TEMP-091's over-claim (6 powered, not 12)
6 MEMBER / 7 COVERAGE_EXCLUDED (`readiness_4h.csv`). Excluded "no finite RCT MDE": AUDUSD, GBPUSD, NZDUSD,
US2000, USDJPY, USTEC-4h; JP225-4h fails to build. TEMP-091's "RCT net-clears 12/12" included six cells that
**cannot bound a confirmation** — the mandated readiness leg caught a naive-screen over-claim. The powered set is
JPY-cross / EUR-GBP-CHF major / gold; the **indices TEMP-091 highlighted are unpowered**.

### Finding 2 — Real beats the oscillation null 6/6, homogeneous, robust to distance choice
`falsification_quorum.csv`: binding 6/6 cells / 6 instruments; `delta_lo` 0.193–0.272. Real RCT net +0.07…+0.16;
matched-distance null net −0.09…−0.18. Not carried by one cell (drop any → still ≥5/5). The **realized-capture
sensitivity** (audit §5) is **also 6/6** (`beats_realized` ∀; null still nets −0.07…−0.20 at the nearer ~0.36-ATR
distance) → the verdict is robust to whether the null target matches the entry-bar target or the realized capture.

### Finding 3 — Mechanism: a 65%→99% completion-rate lift
Real RCT `terminal_fav` ~0.98–0.99; the same-distance limit at random times is reached only ~64–67%, so the
~1/3 misses run to the 2×ATR stop/cap → the null nets negative while real nets positive, with identical exit
geometry. The edge is the **entry signal's timing**, not the target geometry.

### Finding 4 — Robustness: all 6 members are mean-AND-median net-positive
net_median +0.016…+0.132 on every powered cell — unlike the 1h EXP-091 pass (3/5 median-negative). The powered
4h set is a **defensible robust core**, not tail-carried; the whole set (not just 2 cells) is a credible EXP-092
carry.

### Finding 5 — The bite-check (gate calibration) is GREEN after correction
First run HALTed on a RED bite-check; diagnosed (audit §4) as a power-leg miscalibration (planted the
sub-threshold single-arm MDE). Corrected to per-cell detection at a fixed 0.10-ATR reference: FPR per-cell 0.052
/ quorum 0.000; per-cell power at ref 0.857 ≥ 0.80; two-sample MDE 0.10 ≪ observed median Δ 0.276 → **GREEN**.
The gate neither over-fires nor is blind to the real effect.

## Interpretation-guide resolution (pre-registered)

- Bite-check GREEN ∧ leg (b) RCT quorum (6/6) ∧ leg (c) real-beats-null quorum (6/6) ∧ 1h control (5/5) ⇒
  **`ADMIT_4H`** ✓. 4h is admitted (domain expansion, 0 new slots); the 6 powered cells are eligible for the
  EXP-092 cost-bearing sequence.

## Hypothesis verdict

**SUPPORTED (H₁).** On the 6 powered 4h cells, the fade entry is load-bearing — it beats both the entry-bar-target
and realized-capture oscillation nulls 6/6 via a 65%→99% completion-rate mechanism, FPR-controlled and powered.
4h is admitted. CF-MR-001 stays `ADMITTED (BINDING)`; **no new candidate slot, 0 counted TEST reads** (4h strata
stay 0/2).

## Limitations

- **Powered breadth 6 cells** (not the TEMP-091 12); the result does **not** extend to the unpowered cells (incl.
  USTEC/US2000 indices). Any 4h EXP-092/093 carry is at most these 6.
- **Availability, in the tradability direction — not a TEST confirmation.** `ADMIT_4H` is a TRAIN-only screen
  outcome; net-of-cost tradability on a counted TEST read is EXP-093's question.
- Bite-check per-cell power at the 0.10-ATR reference (0.857) is above but not far above the 0.80 floor;
  non-limiting because the gate's MDE (0.10) is ≪ the ~0.27 real effect.

## Alternative explanations (considered & addressed)

- *"Well-formed target, not timing."* The matched-distance null holds the target distance fixed; it still loses,
  and both the entry-bar and realized-capture distance variants give the same verdict → it is the timing.
- *"A few lucky cells."* 6/6 homogeneous, drop-one-robust, mean-and-median positive.

## Recommended next steps (new scopes)

1. **EXP-092 (per-instrument cost-bearing sequence)** — extend the planned 1h sequence to include the **6 powered
   4h cells**, smallest-defensible, 0 new slots; produce the hash-pinned candidate set + phase Holm rule.
2. **EXP-093 (one-shot TEST)** — carry the smallest-defensible cell set (1h ∪ 4h) under the 2/stratum cap.
3. Other deferred levers (15m capture, vol-regime, contrarian, 25/75) remain behind their own `D0-amendment-*`.
