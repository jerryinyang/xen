# xen

Core, thesis-agnostic Python infrastructure for intraday-trading research.

The `xen` package is the **data layer**: deterministic, streaming-compatible
chart-type generators (Line Break, Renko, Heiken Ashi) and OHLC resampling built
on a 1-minute time-bar base. These primitives are shared by every experiment and
are not tied to any single research thesis.

## Layout

```
python/
├── pyproject.toml
├── README.md
├── src/
│   └── xen/
│       ├── bar_aggregator.py        # N-minute OHLC resampling
│       ├── heiken_ashi_generator.py # Heiken Ashi candles
│       ├── linebreak_generator.py   # Line Break bars
│       ├── renko_generator.py       # ATR-based Renko bricks
│       └── indicators/              # optional reusable indicator ports
├── tests/
└── experiments/                     # per-experiment analysis lives here
```

## Install (editable)

```bash
cd python
uv pip install -e .
```

## Usage

```python
import polars as pl
from xen import generate_linebreak, generate_renko, generate_heiken_ashi

bars = pl.read_parquet("data/timebars/timebars_eurusd_*.parquet").sort("CloseTime")
lb = generate_linebreak(bars, level=3)
renko = generate_renko(bars, atr_period=14)
ha = generate_heiken_ashi(bars)
```

## Tests

```bash
cd python
uv run pytest
```
