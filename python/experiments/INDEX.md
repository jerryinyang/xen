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
| EXP-008 | Renko as a Precision Gate Over Time-Bar Signals | REFUTED | Renko confirmation lowers AE on 4/4 instruments but also lowers FE; primary log FE/AE improves on only USTEC | 2026-05-17 |
| EXP-009 | Heiken Ashi Direction as a Signal Generator, Evaluated on Real Prices | REFUTED | HA cuts 15m direction changes to 48-49% of time-bar count but log FE/AE improves on 0/4 instruments | 2026-05-17 |
| EXP-010 | Line Break as a Confirmation Layer Over Renko Signals | REFUTED | LB confirms 53-63% of 15m Renko signals; primary log FE/AE improves on only BTCUSD, not 3/4 instruments | 2026-05-17 |
| EXP-011 | Event-Native Volatility Regime Detection | REFUTED | Fixed Renko-native features show high hybrid rates (0.56-0.79 at 15m); no feature supports regime replacement | 2026-05-17 |
| EXP-012 | ICT Data Readiness and Feasibility | SUPPORTED | All 4 instruments clear macro-family coverage thresholds; NY-time assumptions and cost proxies are documented | 2026-05-23 |
| EXP-014 | PDH PDL ONH ONL Liquidity Level Reproducibility | SUPPORTED | All 4 instruments pass deterministic PDH/PDL and ONH/ONL readiness thresholds | 2026-05-24 |
| EXP-013 | NY Macro Window Characterization | REFUTED | Fixed macro windows support 0/4 instruments versus adjacent and random controls | 2026-05-24 |
| EXP-015 | Prior High Low Sweep Reversal Behavior | REFUTED | Sweep-only failed-breakout behavior supports only EURUSD Test; 1/4 instruments meet the primary criterion | 2026-05-25 |
| EXP-016 | Macro Window Interaction With Sweep Outcomes | PLANNED | Scope and analysis plan created for H2 macro-context interaction | 2026-05-23 |
| EXP-017 | Premium Discount Filter Impact on Sweep Quality | PLANNED | Scope and analysis plan created for premium/discount filter test | 2026-05-23 |
| EXP-018 | Displacement Confirmation Added to Sweeps | PLANNED | Scope and analysis plan created for H3 displacement confirmation | 2026-05-23 |
| EXP-019 | Micro Swing Break Confirmation After Sweep | PLANNED | Scope and analysis plan created for H3 swing-break variant | 2026-05-23 |
| EXP-020 | FVG IFVG Detection Reproducibility | PLANNED | Scope and analysis plan created for H4 FVG/IFVG prerequisite | 2026-05-23 |
| EXP-021 | IFVG Confirmation Entry Quality | PLANNED | Scope and analysis plan created for H4 IFVG entry-quality test | 2026-05-23 |
| EXP-022 | Objective Breaker Candidate Reproducibility | PLANNED | Scope and analysis plan created for H5 breaker prerequisite | 2026-05-23 |
| EXP-023 | Breaker Confirmation Trade Quality | PLANNED | Scope and analysis plan created for H5 breaker confirmation test | 2026-05-23 |
| EXP-024 | Second Candle Open Execution Timing | PLANNED | Scope and analysis plan created for execution-timing rule test | 2026-05-23 |
| EXP-025 | Fixed 1 to 2 Risk Reward Justification | PLANNED | Scope and analysis plan created for H6 risk/reward validation | 2026-05-23 |
| EXP-026 | Incremental ICT Component Ablation | PLANNED | Scope and analysis plan created for component contribution table | 2026-05-23 |
| EXP-027 | Predeclared Full ICT Model Analysis-Set Test | PLANNED | Scope and analysis plan created for gated full-model test | 2026-05-23 |
| EXP-028 | ICT Candidate Robustness and Falsification | PLANNED | Scope and analysis plan created for robustness/falsification checks | 2026-05-23 |

<!-- 
New experiments are added as they are completed.
Planned Phase 003 rows are ordered by execution dependency; EXP IDs remain stable.
Format: | EXP-NNN | Title | INCONCLUSIVE/FAILED/PARTIALLY_SUPPORTED/REFUTED/PLANNED | One-line finding | YYYY-MM-DD |
-->
