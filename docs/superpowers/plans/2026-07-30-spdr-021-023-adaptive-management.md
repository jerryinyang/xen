# SPDR-021–023 Adaptive Management Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development
> (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use
> checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build three independent, TRAIN-only Nautilus characterisation experiments that measure
how confirmed volatility components change breakout, MOMO and MR native geometry and external
trade management.

**Architecture:** Put shared, strategy-neutral contracts, features, policies, Nautilus execution and
analysis in `xen.adaptive_management`. Keep each SPDR directory as a thin experiment wrapper with its
own entry configuration, emissions and analysis. Generate a common signal/zone-origin population,
materialise fixed plus direct/reverse native-parameter schedules, then execute orders and competing
exits on native one-minute bars. Compare native arms over all common origins and management arms by
paired episode ID.

**Tech Stack:** Python 3.13+, NautilusTrader 1.230.0, Polars, NumPy, SciPy, PyArrow, pytest.

## Global Constraints

- Binding design:
  `docs/experiments-docs/checkpoints/2026-07-25-018-trade-opportunity-capture-geometry/adaptive-management-design.md`.
- SPDR-021, SPDR-022 and SPDR-023 are independent; no runner may gate another.
- TRAIN only. Use `xen.nautilus.catalog_fence`; reject TEST and holdout paths in code.
- Crypto and cTrader run and emit separately; never pool them.
- All decisions use information complete by `t-1`.
- Use Nautilus order/fill/position records for accounting; do not infer competing-exit order from
  H1 OHLC.
- Emit the fixed-native comparator, both native orientations, every bounded native-native
  combination, the fixed-management baseline and every fixed-device/adaptive row.
- Keep every common origin, including no-signal, no-event and unfilled outcomes.
- Do not cross strategy-native parameters with the external management grid.
- Report all strata. No winner-only pruning and no supported/refuted labels.
- Event count, CI and block MDE are informative metadata only.
- Keep sizing separate from exit combinations and never describe sizing as improving expectancy.
- No new dependencies.
- Do not touch the deleted experiment families or their recoverable Git history.

---

## File map

| Path | Responsibility |
|---|---|
| `python/src/xen/adaptive_management/contracts.py` | frozen enums, dataclasses, row keys and schemas |
| `python/src/xen/adaptive_management/features.py` | causal volatility components and calibration |
| `python/src/xen/adaptive_management/entries.py` | common origins plus breakout and breach episodes |
| `python/src/xen/adaptive_management/native_parameters.py` | direct/reverse threshold, expiry, z and H schedules |
| `python/src/xen/adaptive_management/policies.py` | fixed/adaptive device parameters and bounded grid |
| `python/src/xen/adaptive_management/strategy.py` | Nautilus orders, pending expiry and competing exits |
| `python/src/xen/adaptive_management/runner.py` | fenced catalog runs and canonical emissions |
| `python/src/xen/adaptive_management/analysis.py` | common-origin and paired estimates, native/device measures, controls, CIs/MDE |
| `python/src/xen/adaptive_management/integrity.py` | fences, parity, tripwires, determinism and row accounting |
| `python/experiments/SPDR-021/screen_code/run_screen.py` | breakout experiment wrapper |
| `python/experiments/SPDR-022/screen_code/run_screen.py` | MOMO experiment wrapper |
| `python/experiments/SPDR-023/screen_code/run_screen.py` | MR experiment wrapper |
| `python/experiments/SPDR-02{1,2,3}/analysis_code/analyse.py` | experiment-local analysis entrypoints |
| `python/tests/test_adaptive_management_*.py` | unit, integration, fence and golden-trace tests |

---

### Task 1: Freeze contracts and the exact arm lattice

**Files:**
- Create: `python/src/xen/adaptive_management/__init__.py`
- Create: `python/src/xen/adaptive_management/contracts.py`
- Create: `python/tests/test_adaptive_management_contracts.py`

**Interfaces:**
- Produces: `ExperimentSpec`, `Origin`, `Episode`, `Component`, `NativeParameter`, `Orientation`,
  `Device`, `NativeArmSpec`, `PolicySpec`, `ResultKey`;
  `build_native_lattice(experiment_id: str) -> tuple[NativeArmSpec, ...]`;
  `native_combination_pairs(experiment_id, component) -> set[tuple[str, str]]`;
  `build_management_lattice(experiment_id: str) -> tuple[PolicySpec, ...]`.
- Consumes: no experiment runtime code.

- [ ] **Step 1: Write the failing schema and lattice tests**

```python
def test_lattice_keeps_sizing_out_of_exit_combinations():
    arms = build_management_lattice("SPDR-021")
    assert not any(a.device == Device.SIZE and a.combination_id for a in arms)


def test_all_adaptive_arms_name_a_fixed_comparator():
    for experiment_id in ("SPDR-021", "SPDR-022", "SPDR-023"):
        for arm in (*build_native_lattice(experiment_id), *build_management_lattice(experiment_id)):
            if arm.is_adaptive:
                assert arm.comparator_id.startswith("FIXED_")


def test_native_lattice_is_broad_but_bounded():
    breakout = build_native_lattice("SPDR-021")
    assert {a.parameter for a in breakout if a.combination_id is None} == {
        NativeParameter.BREAKOUT_THRESHOLD, NativeParameter.PENDING_EXPIRY
    }
    breach = build_native_lattice("SPDR-022")
    assert {a.parameter for a in breach if a.combination_id is None} == {
        NativeParameter.BAND_Z, NativeParameter.BAND_H
    }
    singles = [a for a in breakout + breach if a.combination_id is None]
    assert all(a.orientation in {Orientation.DIRECT, Orientation.REVERSE} for a in singles)


def test_native_combinations_are_only_four_orientation_pairs_per_component():
    pairs = native_combination_pairs("SPDR-021", Component.RANGE_SCALE)
    assert pairs == {
        ("DIRECT", "DIRECT"), ("DIRECT", "REVERSE"),
        ("REVERSE", "DIRECT"), ("REVERSE", "REVERSE"),
    }


def test_native_and_management_grids_never_cross():
    assert not any(a.native_arm_id for a in build_management_lattice("SPDR-021"))


def test_native_adaptive_configuration_counts():
    assert len([a for a in build_native_lattice("SPDR-021") if a.is_adaptive]) == 64
    assert len([a for a in build_native_lattice("SPDR-022") if a.is_adaptive]) == 128
    assert len([a for a in build_native_lattice("SPDR-023") if a.is_adaptive]) == 128
```

- [ ] **Step 2: Run the tests and confirm the missing-module failure**

Run:
`PYTHONPATH=python python/.venv/bin/pytest python/tests/test_adaptive_management_contracts.py -q`

Expected: collection fails because `xen.adaptive_management.contracts` does not exist.

- [ ] **Step 3: Implement immutable contracts and the predeclared matrix**

```python
class Component(StrEnum):
    RANGE_SCALE = "RANGE_SCALE"
    SWING_SCALE = "SWING_SCALE"
    LEVEL_NOW = "LEVEL_NOW"
    LEVEL_FORECAST_K4 = "LEVEL_FORECAST_K4"
    LEVEL_FORECAST_K12 = "LEVEL_FORECAST_K12"
    SHOCK = "SHOCK"
    SWING_GT_CUR = "SWING_GT_CUR"
    TAIL_RISK = "TAIL_RISK"


class Device(StrEnum):
    TARGET = "TARGET"
    STOP = "STOP"
    TRAIL = "TRAIL"
    HOLD = "HOLD"
    SIZE = "SIZE"


class NativeParameter(StrEnum):
    BREAKOUT_THRESHOLD = "BREAKOUT_THRESHOLD"
    PENDING_EXPIRY = "PENDING_EXPIRY"
    BAND_Z = "BAND_Z"
    BAND_H = "BAND_H"


class Orientation(StrEnum):
    DIRECT = "DIRECT"
    REVERSE = "REVERSE"


@dataclass(frozen=True)
class PolicySpec:
    policy_id: str
    component: Component | None
    device: Device
    setting: str
    comparator_id: str
    combination_id: str | None = None
    native_arm_id: str | None = None
    is_adaptive: bool = True


@dataclass(frozen=True)
class NativeArmSpec:
    native_arm_id: str
    component: Component
    parameter: NativeParameter | None
    orientation: Orientation | None
    comparator_id: str
    entry_variant: str
    parameters: tuple[NativeParameter, ...] = ()
    combination_id: str | None = None
    orientation_pair: tuple[Orientation, Orientation] | None = None
    is_adaptive: bool = True
```

Encode all seven components against each applicable native parameter, both orientations, exactly
four native orientation-pair combinations per component, and only the four component plus three
multi-device combinations named in the design. Reject unknown experiment IDs and any
native×management cross.

- [ ] **Step 4: Run the contract tests**

Run:
`PYTHONPATH=python python/.venv/bin/pytest python/tests/test_adaptive_management_contracts.py -q`

Expected: all pass.

- [ ] **Step 5: Commit the contract unit**

```bash
git add python/src/xen/adaptive_management/__init__.py \
  python/src/xen/adaptive_management/contracts.py \
  python/tests/test_adaptive_management_contracts.py
git commit -m "feat: freeze adaptive management arm contracts"
```

---

### Task 2: Build causal volatility features

**Files:**
- Create: `python/src/xen/adaptive_management/features.py`
- Create: `python/tests/test_adaptive_management_features.py`

**Interfaces:**
- Consumes: H1 `pl.DataFrame` with `symbol`, `ts`, `open`, `high`, `low`, `close`.
- Produces:
  `fit_calibration(bars, calibration_end) -> Calibration`;
  `build_feature_panel(bars, calibration) -> pl.DataFrame`.

- [ ] **Step 1: Write failing tests for lag, calibration and frozen definitions**

```python
def test_feature_at_t_does_not_change_when_bar_t_outcome_changes(h1_bars):
    left = build_feature_panel(h1_bars, fit_calibration(h1_bars, CAL_END))
    changed = h1_bars.with_columns(
        pl.when(pl.col("ts") == DECISION_TS).then(pl.col("close") * 9).otherwise(pl.col("close"))
        .alias("close")
    )
    right = build_feature_panel(changed, fit_calibration(changed, CAL_END))
    cols = ["range_scale", "level_now", "shock", "tail_risk"]
    assert left.filter(pl.col("ts") == DECISION_TS).select(cols).equals(
        right.filter(pl.col("ts") == DECISION_TS).select(cols)
    )


def test_reference_values_use_only_first_twenty_percent_of_train(h1_bars):
    calibration = fit_calibration(h1_bars, CAL_END)
    assert calibration.end_ts == CAL_END
    assert calibration.distance_median > 0
```

Add separate fixtures for R-MARKOV `k=4/k=12`, two-bar shock life, `T-GT-CUR` logit-ridge and
the expanding P90 exceedance probability.

- [ ] **Step 2: Run the feature tests and confirm failure**

Run:
`PYTHONPATH=python python/.venv/bin/pytest python/tests/test_adaptive_management_features.py -q`

Expected: import or missing-function failure.

- [ ] **Step 3: Implement the minimum causal feature pipeline**

Implement:

```python
@dataclass(frozen=True)
class Calibration:
    end_ts: datetime
    distance_median_by_symbol: dict[str, float]
    p90_move_by_symbol: dict[str, float]
    range_conversion_by_symbol: dict[str, float]


def build_feature_panel(bars: pl.DataFrame, calibration: Calibration) -> pl.DataFrame:
    """One row per H1 decision; every value uses completed rows strictly before that decision."""
```

Reuse the SPDR-012/013/015 formulas exactly. Port the formulas; do not import experiment scripts at
runtime. Record formula-source names in output columns for parity checks.

- [ ] **Step 4: Add parity fixtures against frozen parent rows**

Store a small hand-selected input/output fixture in
`python/tests/fixtures/adaptive_management/parent_feature_rows.parquet`. Assert exact state labels
and tolerance `1e-10` for continuous values.

- [ ] **Step 5: Run feature and existing foundation tests**

Run:
`PYTHONPATH=python python/.venv/bin/pytest python/tests/test_adaptive_management_features.py python/tests/test_nautilus_foundation.py -q`

Expected: all pass.

- [ ] **Step 6: Commit the feature unit**

```bash
git add python/src/xen/adaptive_management/features.py \
  python/tests/test_adaptive_management_features.py \
  python/tests/fixtures/adaptive_management/parent_feature_rows.parquet
git commit -m "feat: add causal volatility feature panel"
```

---

### Task 3: Generate common origins and fixed entry populations

**Files:**
- Create: `python/src/xen/adaptive_management/entries.py`
- Create: `python/tests/test_adaptive_management_entries.py`

**Interfaces:**
- Produces:
  `breakout_origins(h1, features) -> pl.DataFrame`;
  `breach_origins(h1, features) -> pl.DataFrame`;
  `breakout_episodes(origins, threshold, expiry) -> pl.DataFrame`;
  `breach_episodes(origins, event, direction, z, horizon) -> pl.DataFrame`.
- Origin keys: `origin_id`, `symbol`, `decision_ts`, component states.
- Episode keys: `origin_id`, `episode_id`, `event_ts`, `entry_ts`, `side`, `entry_variant`.

- [ ] **Step 1: Encode the design’s golden traces as failing tests**

```python
def test_breakout_long_and_unfilled_short_match_design_golden_traces():
    episodes = breakout_episodes(breakout_golden_h1(), breakout_golden_features())
    assert episodes.row(0, named=True)["stop_price"] == 102.0
    assert episodes.row(1, named=True)["stop_price"] == 97.0


@pytest.mark.parametrize(
    ("direction", "event", "expected_side"),
    [("MOMO", "E_TOUCH", 1), ("MR", "E_TOUCH", -1),
     ("MOMO", "E_CLOSE", -1), ("MR", "E_CLOSE", 1)],
)
def test_breach_side_mapping(direction, event, expected_side):
    row = breach_episodes(breach_golden_h1(), breach_golden_features(), event, direction).row(
        0, named=True
    )
    assert row["side"] == expected_side
```

- [ ] **Step 2: Run and confirm failure**

Run:
`PYTHONPATH=python python/.venv/bin/pytest python/tests/test_adaptive_management_entries.py -q`

- [ ] **Step 3: Implement common origins and fixed comparators**

Create the common origin clock before applying a threshold, expiry, z or H: every warm H1 decision
bar for breach strategies and every warm bar passing the threshold-free candlestick shape for
breakout. Materialise the fixed comparator with breakout `0.50 × ATR(20)` and two-bar expiry, or
Z-VOL `z=1.5`, `H=12`. Generate stable origin IDs independently of the parameter arm; derive
episode IDs from origin plus arm and event time. Record arm-specific `BLOCKED_ACTIVE` when its prior
order, zone or position prevents action. Do not accept parameter values from CLI.

- [ ] **Step 4: Add SPDR-014 event parity**

On the same parent fixture, assert E-TOUCH/E-CLOSE timestamp and side equality. Require zero
differences before proceeding.

- [ ] **Step 5: Run tests**

Run:
`PYTHONPATH=python python/.venv/bin/pytest python/tests/test_adaptive_management_entries.py -q`

Expected: all pass.

- [ ] **Step 6: Commit**

```bash
git add python/src/xen/adaptive_management/entries.py \
  python/tests/test_adaptive_management_entries.py
git commit -m "feat: add common origins and fixed entries"
```

---

### Task 4: Materialise native-parameter and external-management schedules

**Files:**
- Create: `python/src/xen/adaptive_management/native_parameters.py`
- Create: `python/src/xen/adaptive_management/policies.py`
- Create: `python/tests/test_adaptive_management_policies.py`

**Interfaces:**
- Consumes: origins, episodes, feature panel, calibration, `NativeArmSpec` or `PolicySpec`.
- Produces:
  `materialise_native_arm(origins, features, calibration, spec) -> pl.DataFrame`;
  `materialise_policy(episodes, features, calibration, spec) -> pl.DataFrame`;
  native columns include threshold, expiry, z and H; management columns include target, stop,
  trail, activation, hold bars and risk size.

- [ ] **Step 1: Write failing formula tests**

```python
def test_scale_distance_and_fixed_comparator():
    adaptive = policy_row(component_value=80.0, median_value=50.0, multiplier=1.5)
    assert adaptive.target_distance_bps == 120.0
    assert adaptive.fixed_target_distance_bps == 75.0


def test_risk_size_is_clipped_and_tail_halved():
    assert scale_size(median_scale=50, event_scale=10, tail_high=False, shock=False) == 2.0
    assert scale_size(median_scale=50, event_scale=100, tail_high=True, shock=False) == 0.25


def test_state_schedule_emits_both_states():
    assert state_distance(100, "LOW") == 75
    assert state_distance(100, "HIGH") == 150


def test_continuous_native_parameters_run_both_directions():
    assert breakout_threshold(0.5, q=2.0, orientation="DIRECT") == 0.25
    assert breakout_threshold(0.5, q=2.0, orientation="REVERSE") == 1.0
    assert band_z(1.5, q=2.0, orientation="DIRECT") == 1.0
    assert band_z(1.5, q=2.0, orientation="REVERSE") == 2.0


def test_categorical_native_parameters_are_balanced():
    assert expiry_bars("HIGH", "DIRECT") == 4
    assert expiry_bars("HIGH", "REVERSE") == 1
    assert band_h("HIGH", "DIRECT") == 24
    assert band_h("HIGH", "REVERSE") == 4


def test_no_native_arm_is_crossed_with_management():
    with pytest.raises(ValueError, match="native.*management"):
        materialise_crossed_arm(native_spec(), target_spec())
```

- [ ] **Step 2: Run and confirm failure**

Run:
`PYTHONPATH=python python/.venv/bin/pytest python/tests/test_adaptive_management_policies.py -q`

- [ ] **Step 3: Implement native and device formulas with separate bounded combinations**

Keep pure functions separate from Nautilus. Native arms use the exact continuous and categorical
direct/reverse formulas in the design. Emit all four threshold+expiry or z+H orientation pairs for
each component. Refuse specs outside their respective lattices, any native×management cross, and
position size attached to a multi-exit combination.

- [ ] **Step 4: Test complete row accounting**

For a two-origin fixture, assert every native arm retains both origin IDs when one produces no event
or is `BLOCKED_ACTIVE`. For filled episodes, assert each adaptive management row has one
fixed-device and one plain baseline row with the same `episode_id`.

- [ ] **Step 5: Run and commit**

Run:
`PYTHONPATH=python python/.venv/bin/pytest python/tests/test_adaptive_management_policies.py -q`

```bash
git add python/src/xen/adaptive_management/native_parameters.py \
  python/src/xen/adaptive_management/policies.py \
  python/tests/test_adaptive_management_policies.py
git commit -m "feat: materialise adaptive management policies"
```

---

### Task 5: Execute native orders and competing exits in Nautilus

**Files:**
- Create: `python/src/xen/adaptive_management/strategy.py`
- Create: `python/tests/test_adaptive_management_strategy.py`

**Interfaces:**
- Produces: `AdaptiveManagementConfig(StrategyConfig)` and
  `AdaptiveManagementStrategy(Strategy)`.
- Consumes: one symbol’s immutable policy schedule parquet.

- [ ] **Step 1: Write failing synthetic-catalog tests**

Test the three design golden paths:

```python
def test_target_before_later_stop_is_not_rewritten(run_synthetic_policy):
    trade = run_synthetic_policy(side=1, entry=100, target=102, stop=98)
    assert trade["exit_reason"] == "TARGET"
    assert trade["exit_price"] == 102


def test_pending_order_expires_after_two_complete_h1_bars(run_synthetic_breakout):
    result = run_synthetic_breakout(stop_price=97, minimum_low=97.2)
    assert result["status"] == "EXPIRED"
    assert result["fills"] == 0
```

Also test one- and four-bar adaptive expiries, z/H-dependent event creation, trail activation, hold
exit, reduce-only exit and one-position-per-variant.

- [ ] **Step 2: Run and confirm failure**

Run:
`PYTHONPATH=python python/.venv/bin/pytest python/tests/test_adaptive_management_strategy.py -q`

- [ ] **Step 3: Implement the Nautilus strategy**

Use native stop-market/limit/market orders and engine timers. Tag every order with `origin_id`,
`episode_id`, `native_arm_id`, `policy_id`, `device`, `entry_variant` and `exit_reason`. Keep
no-event/no-order/blocked origins in the origin ledger. Cancel sibling exits after the first closing
fill. Reject schedules containing overlapping episodes or decision times outside the supplied fence.

- [ ] **Step 4: Reconcile orders and fills in tests**

Assert exactly one entry outcome and at most one closing fill per episode-policy pair. Assert
unfilled expiries have no P&L row.

- [ ] **Step 5: Run and commit**

Run:
`PYTHONPATH=python python/.venv/bin/pytest python/tests/test_adaptive_management_strategy.py -q`

```bash
git add python/src/xen/adaptive_management/strategy.py \
  python/tests/test_adaptive_management_strategy.py
git commit -m "feat: execute adaptive policies in Nautilus"
```

---

### Task 6: Add fenced runners and canonical emissions

**Files:**
- Create: `python/src/xen/adaptive_management/runner.py`
- Create: `python/tests/test_adaptive_management_runner.py`
- Create: `python/experiments/SPDR-021/screen_code/run_screen.py`
- Create: `python/experiments/SPDR-022/screen_code/run_screen.py`
- Create: `python/experiments/SPDR-023/screen_code/run_screen.py`

**Interfaces:**
- Produces:
  `run_experiment(spec: ExperimentSpec, universe: Literal["crypto", "ctrader"], output: Path)`.
- Wrappers accept only `--universe`, `--output`, `--jobs` and `--dry-run`; no research parameter CLI.

- [ ] **Step 1: Write failing fence and independence tests**

```python
def test_runner_refuses_non_train_band(tmp_path):
    with pytest.raises(FenceViolation):
        run_experiment(SPDR021, "crypto", tmp_path, band="TEST")


def test_wrapper_never_invokes_companion_experiment(monkeypatch, tmp_path):
    seen = []
    monkeypatch.setattr(runner, "run_experiment", lambda spec, **kw: seen.append(spec.experiment_id))
    run_spdr022.main(["--universe", "crypto", "--output", str(tmp_path), "--dry-run"])
    assert seen == ["SPDR-022"]
```

- [ ] **Step 2: Run and confirm failure**

Run:
`PYTHONPATH=python python/.venv/bin/pytest python/tests/test_adaptive_management_runner.py -q`

- [ ] **Step 3: Implement fenced catalog orchestration**

Reuse `xen.nautilus.catalog_fence` and `xen.nautilus.emission`. Add an explicit INFR-021 manifest
adapter for cTrader rather than passing cTrader dates through the Bybit manifest. Write emissions
atomically to a new output directory; refuse overwrite.

Required raw artifacts:

```text
config.json
fence_attestation.json
calibration.parquet
features.parquet
origins.parquet
native_parameter_schedule.parquet
episodes.parquet
policy_schedule.parquet
orders.parquet
fills.parquet
positions.parquet
episode_results.parquet
run_summary.json
```

- [ ] **Step 4: Test dry-run row plans and universe separation**

Dry-run must load only metadata, print the expected arm/episode plan, and create no result files.
Assert crypto paths never mention the cTrader catalog and vice versa.

- [ ] **Step 5: Run and commit**

Run:
`PYTHONPATH=python python/.venv/bin/pytest python/tests/test_adaptive_management_runner.py -q`

```bash
git add python/src/xen/adaptive_management/runner.py \
  python/tests/test_adaptive_management_runner.py \
  python/experiments/SPDR-021/screen_code/run_screen.py \
  python/experiments/SPDR-022/screen_code/run_screen.py \
  python/experiments/SPDR-023/screen_code/run_screen.py
git commit -m "feat: add independent SPDR adaptive runners"
```

---

### Task 7: Compute origin-native and device-native analysis

**Files:**
- Create: `python/src/xen/adaptive_management/analysis.py`
- Create: `python/tests/test_adaptive_management_analysis.py`
- Create: `python/experiments/SPDR-021/analysis_code/analyse.py`
- Create: `python/experiments/SPDR-022/analysis_code/analyse.py`
- Create: `python/experiments/SPDR-023/analysis_code/analyse.py`

**Interfaces:**
- Produces:
  `analyse_run(run_dir: Path, output_dir: Path) -> None`;
  `origin_estimates(origins, episodes, block_bars=24) -> pl.DataFrame`;
  `paired_estimates(results, block_bars=24) -> pl.DataFrame`.

- [ ] **Step 1: Write failing device-measure tests**

```python
def test_target_metrics_are_not_replaced_by_common_score(target_fixture):
    row = target_metrics(target_fixture)
    assert {"reach_rate", "realised_capture_bps", "missed_excess_bps", "time_to_target"}.issubset(row)


def test_size_metrics_exclude_expectancy_improvement(size_fixture):
    row = size_metrics(size_fixture)
    assert {"risk_dispersion", "drawdown_bps", "tail_loss_bps", "concentration"}.issubset(row)
    assert "expectancy_improvement" not in row


def test_every_adaptive_row_has_paired_fixed_device_delta(result_fixture):
    table = paired_estimates(result_fixture, block_bars=24)
    assert table["paired_n"].min() > 0
    assert table["comparator_id"].str.starts_with("FIXED_").all()


def test_native_analysis_retains_no_event_and_unfilled_origins(origin_fixture):
    table = origin_estimates(origin_fixture.origins, origin_fixture.episodes, block_bars=24)
    assert table["eligible_origins"].unique().to_list() == [origin_fixture.origin_count]
    assert {"signal_rate", "event_rate", "fill_rate", "exposure_per_origin"}.issubset(table.columns)


def test_native_analysis_emits_both_orientations_and_all_four_pairs(native_fixture):
    rows = origin_estimates(native_fixture.origins, native_fixture.episodes, block_bars=24)
    assert set(rows["orientation"]) >= {"FIXED", "DIRECT", "REVERSE"}
    assert set(rows.filter(pl.col("arm_class") == "NATIVE_COMBINATION")["orientation_pair"]) == {
        "DIRECT_DIRECT", "DIRECT_REVERSE", "REVERSE_DIRECT", "REVERSE_REVERSE"
    }


def test_no_native_management_cross_appears(result_fixture):
    assert result_fixture.filter(
        pl.col("native_arm_id").is_not_null() & pl.col("policy_id").is_not_null()
    ).is_empty()
```

- [ ] **Step 2: Run and confirm failure**

Run:
`PYTHONPATH=python python/.venv/bin/pytest python/tests/test_adaptive_management_analysis.py -q`

- [ ] **Step 3: Implement metrics, paired blocks and informative MDE**

Use calendar-block bootstrap with block length at least 24 H1 bars; sample dates first and retain
the instrument cluster inside each sampled block. Native arms compare fixed, direct and reverse on
the complete common-origin ledger, with shared-trade pairing as a diagnostic. Management arms
remain paired by episode. Emit direct estimate, CI, origin/event/trade counts, effective count and
MDE without a result label.

Emit:

```text
per_stratum_estimates.parquet
native_parameter_origins.parquet
native_parameter_shared_trades.parquet
native_parameter_selected_excluded.parquet
device_target.parquet
device_stop.parquet
device_trail.parquet
device_hold.parquet
device_size.parquet
state_sections.parquet
selection_checks.parquet
controls.parquet
analysis_summary.json
```

- [ ] **Step 4: Enforce full reporting**

Compare the emitted row key set with both expected lattices × observed states. Fail analysis on
missing/duplicate keys, dropped origins or any native×management row. “Best” helper tables must
retain `metric_name` and the source row key.

- [ ] **Step 5: Run and commit**

Run:
`PYTHONPATH=python python/.venv/bin/pytest python/tests/test_adaptive_management_analysis.py -q`

```bash
git add python/src/xen/adaptive_management/analysis.py \
  python/tests/test_adaptive_management_analysis.py \
  python/experiments/SPDR-021/analysis_code/analyse.py \
  python/experiments/SPDR-022/analysis_code/analyse.py \
  python/experiments/SPDR-023/analysis_code/analyse.py
git commit -m "feat: add origin and device native analysis"
```

---

### Task 8: Add integrity, controls and deterministic replay

**Files:**
- Create: `python/src/xen/adaptive_management/integrity.py`
- Create: `python/tests/test_adaptive_management_integrity.py`

**Interfaces:**
- Produces:
  `run_integrity_checks(run_dir: Path) -> dict`;
  `derange_component_times(features, seed)`;
  `magnitude_matched_controls(episodes, features)`.

- [ ] **Step 1: Write failing hard-check tests**

```python
def test_derangement_has_zero_fixed_points(feature_fixture):
    shuffled = derange_component_times(feature_fixture, seed=240730)
    assert (shuffled["source_ts"] == shuffled["ts"]).sum() == 0


def test_future_shift_tripwire_changes_every_decision_mapping(feature_fixture):
    result = future_shift_tripwire(feature_fixture)
    assert result["unchanged_fraction"] < 1.0


def test_deterministic_replay_hashes_match(two_identical_runs):
    assert replay_hashes(two_identical_runs[0]) == replay_hashes(two_identical_runs[1])
```

- [ ] **Step 2: Run and confirm failure**

Run:
`PYTHONPATH=python python/.venv/bin/pytest python/tests/test_adaptive_management_integrity.py -q`

- [ ] **Step 3: Implement hard and informative checks**

Hard: fences, causal provenance, entry parity, order/fill/position reconciliation, row accounting,
golden traces, common-origin completeness, native-lattice completeness, cross-grid prohibition and
deterministic replay. Informative: derangement change, magnitude-matched state contrast, CI/MDE and
partial-cost sensitivity.

Write `integrity_selfcheck.json`, `golden_traces.json`, `determinism.json`,
`row_accounting.json` and `controls.json`.

- [ ] **Step 4: Run all adaptive tests**

Run:
`PYTHONPATH=python python/.venv/bin/pytest python/tests/test_adaptive_management_*.py -q`

Expected: all pass.

- [ ] **Step 5: Commit**

```bash
git add python/src/xen/adaptive_management/integrity.py \
  python/tests/test_adaptive_management_integrity.py
git commit -m "test: enforce adaptive experiment integrity"
```

---

### Task 9: Final implementation verification without research execution

**Files:**
- Modify only if verification finds a defect in files created by Tasks 1–8.

- [ ] **Step 1: Run the complete Python suite**

Run:
`PYTHONPATH=python python/.venv/bin/pytest python/tests -q`

Expected: all tests pass; existing skip count may remain.

- [ ] **Step 2: Run lint and diff checks**

Run:
`python/.venv/bin/ruff check python/src/xen/adaptive_management python/tests/test_adaptive_management_*.py python/experiments/SPDR-02{1,2,3}`

Run: `git diff --check`

Expected: both clean.

- [ ] **Step 3: Dry-run each experiment and universe**

Run each wrapper with `--dry-run` for `crypto` and `ctrader`. Expected: six successful plans, no
catalog data beyond TRAIN loaded, no results emitted, and no companion experiment invoked.

- [ ] **Step 4: Audit the implementation against the approved design**

Check:

```text
all 3 experiments independent
all 7 components present where applicable
breakout threshold and expiry each have fixed/direct/reverse arms
breach z and H each have fixed/direct/reverse arms
all 4 native orientation pairs present per component
all common origins retained, including no-event/no-fill
all 5 external management devices present
all individual rows precede combinations
only 4 component and 3 device combinations present
only threshold+expiry and z+H native combinations present
no native parameter crossed with external management
all states and both E-TOUCH/E-CLOSE variants visible
no verdict labels
size not crossed with exits
crypto/cTrader separate
```

- [ ] **Step 5: Stop at the execution gate**

Report implementation readiness and test evidence. Do not run a full TRAIN experiment until the
operator separately authorises execution.
