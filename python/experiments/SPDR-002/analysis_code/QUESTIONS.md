# SPDR-002 interrogation question list (posed before compute)

Q1  Integrity: TRAIN fence, HTF-boundary causality, LTF-breakout causality, seed regenerability — all pass?
Q2  Baseline anatomy: what is the unfiltered-momentum forward-return distribution per stratum (mean/std/hit/skew/tails)? Is naive momentum itself available (CI vs 0) or a wash?
Q3  HTF-filter LIFT: does any HTF gating/confirmation arm move the mean off the unfiltered baseline with CI clear of 0? magnitude + sign, per stratum.
Q4  Degeneracy: how many "lift CI>0" cells are just admit_frac≈1 (filter ≈ baseline trivially)? strip them.
Q5  DI confirmation: does requiring HTF-direction agreement change the momentum outcome? magnitude.
Q6  Control C: for DI arms with lift CI>0, does the HTF phase-shift collapse the lift (collapse_frac)? An HTF-alignment claim MUST collapse.
Q7  Control B: does momentum timing beat the 25-seed matched-random-timing battery? percentile. Does HTF filtering widen/shrink the gap?
Q8  Dose-response ADX: is the momentum mean / dispersion monotone in continuous ADX? rank rho + CI.
Q9  Dose-response ATR-pct: same for HTF ATR percentile.
Q10 Dispersion normaliser guard: does the ATR[t-1]-normalised dispersion read survive under raw-bps and fixed-long-window-ATR normalisers, or is it a normaliser artifact?
Q11 Horizon: how does the momentum mean/hit evolve across hold multiples 1-4?
Q12 Heterogeneity (L-03): do instruments/domains agree, or does one carry/veto? no pooling.
Q13 Interaction ADX x ATR x DI: do triple-combo arms show structure beyond marginals?
Q14 Power map (B-5): which strata are UNPOWERED (n<block floor / MDE>plausible)? never a negative.
Q15 Falsification: what would make the headline lift wrong? block-fragility, seed-range straddle, admit-frac degeneracy.
