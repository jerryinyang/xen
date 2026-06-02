# Experiment Index

| ID | Title | Status | Key Finding | Date |
|----|-------|--------|-------------|------|
| EXP-001 | Synthetic Substrate Validation | SUPPORTED | Substrate gate PASS: P0 56/56, both nulls ≈0, positives recover planted m to machine precision; 5 sub-material 4h cells under-powered (INCONCLUSIVE, immaterial). | 2026-06-02 |
| EXP-002 | Referee Golden-Fixture Correctness | SUPPORTED | Both referees correct: 10/10 verdicts and 25/25 gate-leg states reproduce hand-computed expectations; gate stack emits all 5 legs with no short-circuit. | 2026-06-02 |
| EXP-003 | Referee Operating-Characteristic Calibration (keystone) | SUPPORTED | Measured stringency↔sensitivity trade-off: gate-stack FPR=0 at all domains/α vs minimal FPR≈α, bought with 2–8× MDE inflation (net 1/4/12 bps on 5m/1h/4h); L5 materiality is the binding, α-invariant leg. 18/18 MDE cells PASS. | 2026-06-02 |
| EXP-004 | Real Dogfood Consistency Anchor | SUPPORTED | H-dogfood SUPPORTED: all 48 cells REJECT and consistent with the EXP-003 MDE map (matched_reject); untuned Donchian/MA carry no positive edge even gross (≈[−2.2,+1.3] bps, CIs include 0). Keystone anchor is a null/lower anchor — simple edges sit below every gate MDE, so structural blindness is bounded, not resolved. | 2026-06-02 |
| VAL-001 | Data Architecture Temporal Integrity Validation | SUPPORTED (rev. 3) | Base data, timeframe aggregation, and chart generators passed all temporal-integrity checks (416/416 PASS); 23/23 negative controls detected across every data-integrity and alignment check; outputs reproduced rev. 2 byte-for-byte. | 2026-06-01 |
