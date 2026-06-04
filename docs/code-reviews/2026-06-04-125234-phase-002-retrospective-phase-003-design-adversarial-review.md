Using `bmad-review-adversarial-general` with the `research-pipeline` references. Content type: research programme retrospective + next-phase design. Active lenses: research governance, statistical validity, predeclaration discipline, phase alignment.

```json
[
  {
    "id": "F01",
    "severity": "Major",
    "title": "Phase success criteria conflict with framework-conclusion claim",
    "evidence": "Phase 003 design says the suite is built/frozen for Phase 004 (design.md:24-26,47,156-158), but success also permits 'incremental unit not buildable this phase' (design.md:130) and failure only if both Track A fully fails and Track B substrate fails (design.md:132).",
    "impact": "A partial result could be treated as phase success while the defined qualification suite is not actually available, letting Phase 004 start without the validated fitness unit.",
    "fix": "Split outcomes into FULL_FRAMEWORK_CONCLUDED, PARTIAL_SUCCESS, and BLOCKED/DEFERRED. Only allow Phase 004 signal exploration after EXP-013-015 pass and D-adopt is satisfied."
  },
  {
    "id": "F02",
    "severity": "Major",
    "title": "4h loose-referee adoption gate is ambiguous",
    "evidence": "D-ratify-point requires 4h to pass D-ratify-4h (design.md:40), while D-ratify-4h says non-agreement may become 'adopt-with-split-caveat' or fallback, deferred to EXP-012 scope (design.md:41).",
    "impact": "The adoption decision can become outcome-aware at EXP-012 scope time, weakening the predeclaration freeze.",
    "fix": "Define the exact edge grid, protocol-agreement tolerance, and allowed 4h verdicts now. Either remove 'adopt-with-split-caveat' or give it a precise predeclared trigger."
  },
  {
    "id": "F03",
    "severity": "Major",
    "title": "Fresh-draw ratification overclaims independence",
    "evidence": "The design defines fresh as new seeds, not new real data, with all draws on the same first-70% analysis slice (design.md:42,101), but also calls ratification out-of-sample confirmation (design.md:57,158).",
    "impact": "This confirms seed-level robustness against synthetic draw selection, not independence across market regimes, real samples, or harness assumptions.",
    "fix": "Rename it 'fresh-seed synthetic ratification' and explicitly state the limitation. Do not describe the result as broadly out-of-sample-confirmed."
  },
  {
    "id": "F04",
    "severity": "Major",
    "title": "Loose-referee adoption ignores sub-material pass stability",
    "evidence": "Phase 002 warns that low tau can buy MDE with sub-material passes, especially 5m at 0.398 for recommended tau (retrospective.md:82,112-116). Phase 003 adoption checks only FPR and MDE (design.md:40,68).",
    "impact": "A domain could adopt the loose referee even if fresh draws reproduce MDE/FPR while materially worsening economic usefulness.",
    "fix": "Add a fresh-draw sub-material pass-rate ceiling or tolerance per domain, especially for 5m, and report adoption with an explicit materiality verdict."
  },
  {
    "id": "F05",
    "severity": "Major",
    "title": "Incremental-edge estimator is under-specified at checkpoint level",
    "evidence": "D-incr-form only gives a default orthogonalization concept and defers residualization method, cost attribution, and denominator to EXP-013 scope (design.md:43).",
    "impact": "The highest-leverage definition in Track B can still move during experiment scoping, creating room for ambiguity before measurement.",
    "fix": "Add a dated design amendment before EXP-013 defining the estimator, denominator, cost attribution, reference construction, and simpler alternative considered."
  },
  {
    "id": "F06",
    "severity": "Major",
    "title": "Residualization method may create false incremental edge under dependence",
    "evidence": "The proposed default uses residualization against the reference signal (design.md:43), while governance rejects unjustified stationarity/i.i.d./model assumptions (governance-constraints.md:21-31).",
    "impact": "Linear residualization can mis-handle nonlinear dependence, shared latent state, heteroskedasticity, and active-overlap costs, producing phantom incremental edge.",
    "fix": "Prefer marginal portfolio P&L difference as the primary economic estimator, or explicitly validate residualization against nonlinear/shared-structure nulls with blocked/permutation controls."
  },
  {
    "id": "F07",
    "severity": "Major",
    "title": "Dependence stress is required but not parameterized",
    "evidence": "The design requires reference/candidate dependence handling (design.md:46,71), but does not define dependence regimes, active overlap, lag structure, or reference strength.",
    "impact": "EXP-015 could pass on an easy dependence case while missing the false-positive mode the track is meant to control.",
    "fix": "Predeclare a dependence grid: shared latent state strength, candidate/reference correlation, active overlap, lag/lead cases, and reference edge strength."
  },
  {
    "id": "F08",
    "severity": "Major",
    "title": "EXP-016 only validates the negative integration path",
    "evidence": "EXP-016 uses the real EXP-009 dogfood set and expects standalone REJECT/no incremental edge because those strategies are net losers (design.md:73,119; retrospective.md:100).",
    "impact": "The assembled suite may compose correctly on null/negative cases while pass-path wiring, adoption-path behavior, or positive incremental verdicts remain untested end to end.",
    "fix": "Keep real dogfood as a negative integration check, but add a synthetic positive suite-level fixture or require an EXP-015 positive end-to-end composition check."
  },
  {
    "id": "F09",
    "severity": "Major",
    "title": "Multiplicity governance is deferred past framework freeze",
    "evidence": "Programme-level multiplicity/file-drawer registry is deferred (retrospective.md:183; design.md:142), while Phase 004 will screen operator-defined candidate families (design.md:150-152).",
    "impact": "The suite may control per-candidate error but still allow inflated programme-level false discoveries during exploration.",
    "fix": "Make a Phase 004 registry/multiplicity plan mandatory before any candidate run, or explicitly scope the concluded framework to single-candidate qualification only."
  },
  {
    "id": "F10",
    "severity": "Minor",
    "title": "Strict-referee conclusion is phrased broader than EXP-005 supports",
    "evidence": "The retrospective says the strict gate is not structurally blind (retrospective.md:48-62), based on one synthetic imperfect-candidate construction with fixed active/match parameters (retrospective.md:50).",
    "impact": "Readers may infer universal non-blindness across real candidate structures, when the evidence supports the specific EXP-005 candidate family and grid.",
    "fix": "Phrase the claim as conditional: not blind for the EXP-005 candidate construction and tested domains; reserve broader claims for future candidate/noise-regime tests."
  }
]
```

Highest-priority fixes are F01, F02, F04, and F05. The retrospective is mostly disciplined about Phase 002’s “recommend, not adopt” boundary; the next design is directionally coherent, but its conclusion/freeze language is stronger than several gates currently justify.
