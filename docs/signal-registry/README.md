# Signal Registry

The signal registry is the programme-level file-drawer control for real signal
exploration. A candidate family must be registered here before any candidate
screening, cTrader run, result interpretation, or suite qualification.

## Directory Layout

```text
docs/signal-registry/
├── README.md
├── multiplicity-registry.md
├── candidate-families/
│   └── avwap.md
└── components/
    └── global-techniques.md
```

## Registry Objects

| Object | Meaning | Required before |
| --- | --- | --- |
| Candidate family | A related signal thesis with fixed first-branch definitions and explicit variants. | Any experiment scope. |
| Hypothesis | One falsifiable question inside a candidate family. | Any EXP using that question. |
| Component | Reusable entry, exit, risk, or position-management idea. | Any strategy that uses it. |
| Experiment | A pipeline EXP-ID that tests exactly one hypothesis or readiness question. | Any implementation. |

## Status Values

| Status | Meaning |
| --- | --- |
| `DRAFT` | Notes exist, but the item is not eligible for experiments. |
| `REGISTERED` | Definitions are fixed enough to create a scope. |
| `SCOPED` | A pipeline scope exists, but no result exists. |
| `SCREENED` | The frozen suite or scoped experiment has produced results. |
| `RETIRED` | The item is closed and cannot be silently reused as a fresh candidate. |

## Candidate-Family Document Requirements

Each file in `candidate-families/` must define:

- candidate-family ID and status;
- thesis summary;
- brainstorming provenance when the family is promoted from prior notes;
- fixed first-branch definitions;
- explicit parameters and allowed domains;
- hypotheses, with the EXP-ID that will test each one;
- exclusions, registered non-baseline branches, and any deferred variants;
- implementation path: Python characterization first when needed, cTrader
  strategy-host screening only after the component is defined;
- real-price outcome discipline and holdout exclusion.

## Multiplicity Rules

1. A candidate family, variant, detector choice, parameter branch, or follow-up
   candidate is countable once it is considered for screening.
2. Countable items must be listed in `multiplicity-registry.md` before any
   result-producing code or cTrader run.
3. Failed, refuted, blocked, and inconclusive items remain in the ledger. They
   are not deleted or renamed away.
4. A parameter change after seeing results is a new registered branch, not a
   revision of the old branch.
5. The frozen qualification suite is not tuned during Phase 004. It remains:
   strict gate stack, EXP-012 ratified-loose referee, and EXP-018 revised
   portfolio-fitness unit.

## Current Registered Batch

Phase 004 Batch A registers one candidate family:

- `CF-AVWAP-001` - Anchored VWAP on regime pivots.

The active batch is documented in `multiplicity-registry.md`.
