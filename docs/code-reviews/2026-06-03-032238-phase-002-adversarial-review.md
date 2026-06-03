Used `research-pipeline` references: pipeline config, dataset reference, architecture reference, experiment indexes, last completed retrospective, and active checkpoint design. No separate rationale file exists for Phase 002; I treated the provenance/objective sections in [design.md](/Users/jerryinyang/cAlgo/Sources/Robots/Xen/Xen/docs/experiments-docs/checkpoints/2026-06-03-002-referee-refinement-and-stringency/design.md:7) as the rationale.

Active lenses: empirical validity, predeclaration/governance integrity, reproducibility, and scope control.

```json
[
  {
    "id": "F01",
    "severity": "Major",
    "title": "Confirmable defaults weaken the predeclaration freeze",
    "evidence": "Phase 002 says decisions are frozen before measurement and changes require a new design, but also says D-lenientL5, D-nearMDE, and D-loss are 'frozen-but-confirmable' until each experiment executes: design.md lines 26-41.",
    "impact": "Operator confirmation after earlier Phase 002 results could make later definitions outcome-aware, especially the EXP-011 loss function and EXP-007 lenient variant.",
    "fix": "Freeze D-lenientL5, D-nearMDE, and D-loss in the checkpoint design before EXP-005 starts, or require a new dated design amendment before any related measurement is read."
  },
  {
    "id": "F02",
    "severity": "Major",
    "title": "EXP-005 may not close the real-edge blind-spot question",
    "evidence": "Retrospective requires a 'substrate-validated candidate carrying a small real edge' near MDE; Phase 002 says to 'plant' an edge carried by a realistic candidate, but does not specify construction: retrospective.md lines 109-113; design.md lines 37 and 49-50.",
    "impact": "If the edge is synthetically planted or too oracle-adjacent, EXP-005 may only test a noisy synthetic fixture, not whether the referee detects naturally plausible weak real market edges.",
    "fix": "Before EXP-005, define the candidate-generation mechanism, noise/SNR model, active-bar denominator, cost treatment, and why it is a valid proxy for a realistic weak real edge."
  },
  {
    "id": "F03",
    "severity": "Major",
    "title": "Pooled MDE may overstate keystone closure",
    "evidence": "Phase 001 notes MDEs pool four instruments with heterogeneous cost and dispersion; Phase 002 EXP-005 uses the pooled domain gate MDE grid, while EXP-008 depools only later: retrospective.md lines 121-123; design.md lines 37 and 111.",
    "impact": "A domain-level EXP-005 pass could mask instrument-level blindness, especially where cost or dispersion differs materially.",
    "fix": "Either run EXP-008 before final EXP-005 interpretation, or make EXP-005 report both pooled-domain and per-instrument detection where sample size permits."
  },
  {
    "id": "F04",
    "severity": "Major",
    "title": "Lenient L5 may remove economic materiality rather than characterize it",
    "evidence": "D-lenientL5 replaces the strict requirement that point estimate exceed cost plus materiality buffer with CI lower bound greater than zero: design.md line 36.",
    "impact": "The variant may pass statistically positive but economically negligible effects, undermining the stated purpose of a referee for scarce validation resources.",
    "fix": "Define the economic interpretation of lenient L5 explicitly, compare it against a threshold sweep including zero/materiality-buffer variants, and require EXP-007 to report economically sub-material pass rates."
  },
  {
    "id": "F05",
    "severity": "Major",
    "title": "Phase success criteria conflict with optional scope trimming",
    "evidence": "EXP-009 and EXP-010 may be dropped if the phase is too heavy, but phase success still requires broadened effect-size distribution and split-protocol robustness: design.md lines 117 and 123-127.",
    "impact": "The phase can become ambiguous: dropping work may be operationally allowed while making the declared success criteria impossible to satisfy.",
    "fix": "Separate core success criteria from optional refinements. For example: core = EXP-005, EXP-006, EXP-007, EXP-011; optional/context = EXP-008-010 with explicit deferral rules."
  },
  {
    "id": "F06",
    "severity": "Minor",
    "title": "Material difference margins are deferred but referenced as predeclared",
    "evidence": "H-pool says per-instrument MDEs differ materially by a predeclared margin, but the checkpoint design does not state that margin: design.md line 61.",
    "impact": "EXP-008 could later choose a margin that fits observed scale unless the experiment scope freezes it before results.",
    "fix": "Add the material-difference threshold to the checkpoint design or require EXP-008 scope to freeze it before any per-instrument MDE artifact is loaded."
  },
  {
    "id": "F07",
    "severity": "Minor",
    "title": "Retrospective slightly overstates dogfood rejections as true negatives",
    "evidence": "The retrospective says dogfood rejections are true negatives because no positive real edge was present near the MDE boundary, while effects mostly have CIs bracketing zero: retrospective.md lines 92-102.",
    "impact": "Non-detection does not prove no small edge exists; it proves no material detectable edge under the tested design.",
    "fix": "Rephrase as 'consistent with true negatives for qualification purposes' or 'no material positive edge detected,' preserving the bounded-not-closed conclusion."
  }
]
```

The core handoff is coherent: Phase 001 correctly identifies the unresolved keystone, and Phase 002 targets it directly. The main risks are not in the broad direction; they are in predeclaration discipline and whether EXP-005’s engineered near-MDE candidate will actually answer the “weak real edge” question it is meant to close.
