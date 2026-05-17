# Experiment Index

| ID | Title | Status | Key Finding | Date |
|----|-------|--------|-------------|------|
| EXP-001 | Information Density & Ghost Bar Comparison | REFUTED | only EURUSD meets all thresholds; ghost reduction universal but entropy gains instrument-specific | 2026-05-16 |
| EXP-002 | Volatility & Trend Regime Representation | REFUTED | LineBreak3 and Renko exceed hybrid-rate bound (0.05) on all 4 instruments; median lag 0.0 but 17-34% transitions missed | 2026-05-16 |
| EXP-003 | Noise Filtering & Statistical Robustness | SUPPORTED | Renko direction stability superior to time bars on 4/4 instruments; HA reduces variance drift 80-93% (distortion diagnostic) | 2026-05-16 |
| EXP-004 | Market Structure Capture Speed & Fidelity | REFUTED | Event charts 50-55x slower than time bars; precision-recall trade-off, not speed advantage | 2026-05-16 |
| EXP-005 | Cross-Chart-Type Alignment & Regime Correspondence | REFUTED | LB↔Renko raw agreement ~90% but paired bootstrap refutes hypothesis; LB and Renko each agree more with time bars than with each other on paired subset | 2026-05-16 |
| EXP-006 | Heiken Ashi Synthetic Price Distortion Quantification | REFUTED | HA compresses vol ~25-26% and median abs return ~20-27%; hypothesis (≥30% vol) REFUTED | 2026-05-16 |
| EXP-001-TF | Timeframe Replication: Information Density & Ghost Bar Comparison | REFUTED | Ghost reduction replicates (70-100%) but entropy gains uniformly negative; 0/4 instruments meet all thresholds | 2026-05-17 |
| EXP-002-TF | Timeframe Replication: Volatility & Trend Regime Representation | REFUTED | Hybrid rates 9-22% exceed 0.05 bound on all instruments; median lag ≤2 bars but boundary cost structural | 2026-05-17 |
| EXP-003-TF | Timeframe Replication: Noise Filtering & Statistical Robustness | REFUTED | Max 2 instruments meet 25% lower drift threshold (need ≥3); complexity drift 10-30x worse for event charts | 2026-05-17 |
| EXP-004-TF | Timeframe Replication: Market Structure Capture Speed & Fidelity | REFUTED | Event charts faster (0-15 min vs 30 min) AND more precise (0.51-1.02 vs 0.15-0.25); speed-recall-precision trade-off | 2026-05-17 |
| EXP-005-TF | Timeframe Replication: Cross-Chart-Type Alignment & Regime Correspondence | REFUTED | LB<->Renko agreement 100% on matched events but only 50% overlap; improvement over Time bars only 1-2pp (need ≥10pp) | 2026-05-17 |
| EXP-006-TF | Timeframe Replication: Heiken Ashi Synthetic Price Distortion Quantification | REFUTED | Volatility compression 23-27% (need ≥30%); return compression 23-29% meets ≥20% but both thresholds required | 2026-05-17 |
| EXP-007 | Multi-State Signal-Quality Baseline | SUPPORTED | Measurement gate passed via 15m Renko FE/AE and LineBreak AE differentiation; FE/AE carry forward, precision/run-continuation do not | 2026-05-17 |
| EXP-008 | Renko as a Precision Gate Over Time-Bar Signals | PLANNED | Scope and analysis plan created; tests 1-minute and 15-minute Renko-confirmed time-bar signals | 2026-05-17 |
| EXP-009 | Heiken Ashi Direction as a Signal Generator, Evaluated on Real Prices | PLANNED | Scope and analysis plan created; tests HA direction changes as real-price signal candidates | 2026-05-17 |
| EXP-010 | Line Break as a Confirmation Layer Over Renko Signals | PLANNED | Scope and analysis plan created; tests Line Break-confirmed Renko quality and coverage cost | 2026-05-17 |
| EXP-011 | Event-Native Volatility Regime Detection | PLANNED | Scope and analysis plan created; tests fixed Renko-native regime features without parameter search | 2026-05-17 |

<!-- 
New experiments are added as they are completed.
Format: | EXP-NNN | Title | INCONCLUSIVE/FAILED/PARTIALLY_SUPPORTED/REFUTED/PLANNED | One-line finding | YYYY-MM-DD |
-->
