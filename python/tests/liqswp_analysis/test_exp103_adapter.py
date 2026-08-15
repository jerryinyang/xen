from __future__ import annotations

from types import ModuleType
from typing import Callable

import polars as pl


def test_profile_integrity_rejects_bad_mask_conservation_and_boundary(
    load_exp_module: Callable[[str], ModuleType],
) -> None:
    module = load_exp_module("EXP-103")
    valid = module.golden_profile_frame()
    status, evidence = module.validate_profile_frame(valid)
    assert status.blocking_pass
    assert evidence["defined"] == 2

    malformed = valid.with_columns(
        pl.lit('{"outer_low_bin_index":103,"outer_high_bin_index":101}').alias("gap_mask")
    )
    assert not module.validate_profile_frame(malformed)[0].blocking_pass

    bad_conservation = valid.with_columns(pl.lit(False).alias("tpo_conservation_ok"))
    assert not module.validate_profile_frame(bad_conservation)[0].blocking_pass

    strict_boundary = valid.head(1).with_columns(
        pl.lit(4.0).alias("va_width"),
        pl.lit(104.0).alias("vah"),
        pl.lit(2.0).alias("gap_span"),
        pl.lit(0.2).alias("gap_span_atr"),
        pl.lit(0.5).alias("gap_span_va"),
        pl.lit(False).alias("tight_gap"),
    )
    assert module.validate_profile_frame(strict_boundary)[0].blocking_pass


def test_exp103_emits_all_defined_and_tight_contrast_without_false_arm(
    load_exp_module: Callable[[str], ModuleType],
) -> None:
    module = load_exp_module("EXP-103")
    adapter = module.Adapter(n_boot=40, n_destroy=20, seeds=(0, 1))
    frame = adapter.fixture_frame()
    assert adapter.integrity(frame).blocking_pass
    rows = adapter.analyze(frame)
    assert {(row["arm"], row["comparator"]) for row in rows} == {(True, False)}
    extra = adapter.extra(frame)
    assert set(extra["profile_census"]) >= {"all", "defined", "tight", "non_tight"}
    assert extra["golden_trace"]["blocking_pass"] is True
