namespace Xen.StrategyHost;

// ===========================================================================
// EXP-025 (CF-HTFDI-001/HYP-A) — higher-timeframe (1h) Wilder DMI/ATR state
// machine shared by the StrategyHost model (HtfDiBreakoutModel, exits E0/E2/
// E3/E5/E6) and the native-order arm (Xen.HtfDiNative.cs, exits E1/E4), so
// both arms condition on IDENTICAL clock-aligned UTC 1h context (design §3).
//
// Feed it the experiment's 5min domain bars in order; it buckets them into
// clock-aligned 1h bars (same (closeSeconds-1)/3600 keying convention as
// BarAggregator, i.e. grouping by the hour of OpenTime; resample semantics —
// no coverage floor, matching the design §13 golden-trace derivation), and on
// each COMPLETED 1h bar appends one immutable snapshot:
//   CloseTime (the 1h bar's last source-bar CloseTime — its true info time),
//   Wilder ±DI(14)/ADX(14)/ATR(14), the ATR tercile regime vs the trailing
//   2,016 closed-1h ATR values (-1 = UNSET until the window is full, design
//   §3), and the ADX>trailing-2,016-median sentinel gate (operator-resolved
//   window, 2026-07-08).
//
// CAUSAL CONTRACT: a snapshot exists only for a CLOSED 1h bar (its last 5min
// bar has closed before any decision that reads it — the forming 1h bar is
// never represented). Callers read via Snapshot(shiftBars): shiftBars=0 is
// the last closed bar; shiftBars=60 is the +60-closed-bar HTF phase-shift
// tripwire (design §6 — rolls the whole DI/ATR/regime stream, cadence
// preserved). Warmup: null until >= MinClosedBars (28) closed 1h bars.
// ===========================================================================
public sealed record HtfSnapshot(
    DateTime CloseTime,
    double PlusDi,
    double MinusDi,
    double Adx,
    double Atr,
    int AtrRegime,        // 0 low / 1 mid / 2 high tercile; -1 UNSET (window not full)
    bool AdxGateReady,    // trailing-median window full
    bool AdxAboveMedian); // sentinel gate: ADX > trailing 2016-value median

public sealed class WilderHtfState
{
    public const int DmiPeriod = 14;
    public const int MinClosedBars = 28;          // design §3: no signal until >= 28 closed 1h bars
    public const int RegimeWindow = 2016;         // trailing closed-1h bars (~12 wk) for terciles/median

    private readonly int _htfMinutes;
    private static readonly DateTime Epoch = new(1970, 1, 1, 0, 0, 0, DateTimeKind.Utc);

    // forming-HTF-bar accumulator
    private long? _bucketKey;
    private DateTime _bucketOpenTime;
    private DateTime _bucketCloseTime;
    private double _bucketOpen, _bucketHigh, _bucketLow, _bucketClose;
    private bool _bucketHasBars;

    // Wilder DMI/ATR incremental state (classic construction: 14-sum seed, then
    // smoothed S = S - S/14 + x; ADX = mean of first 14 DX then Wilder-smoothed).
    private int _closedBars;
    private double _prevHigh, _prevLow, _prevClose;
    private double _sumTr, _sumPlusDm, _sumMinusDm;   // seed accumulators (first 14)
    private double _smTr, _smPlusDm, _smMinusDm;      // Wilder-smoothed sums
    private double _plusDi, _minusDi;
    private int _dxCount;
    private double _dxSum, _adx;
    private double _atr;                               // Wilder ATR(14)

    // trailing windows for the regime tercile + sentinel median (ring buffers)
    private readonly Queue<double> _atrWindow = new();
    private readonly Queue<double> _adxWindow = new();

    private readonly List<HtfSnapshot> _snapshots = new();

    public WilderHtfState(int htfMinutes = 60)
    {
        if (htfMinutes < 10)
            throw new ArgumentOutOfRangeException(nameof(htfMinutes));
        _htfMinutes = htfMinutes;
    }

    public int ClosedBars => _closedBars;

    /// <summary>Feed one completed DOMAIN (5min) bar; returns true if a 1h bar closed.</summary>
    public bool Update(TimeBar bar)
    {
        var key = BucketKey(bar.CloseTime);
        var closed = false;
        if (_bucketKey.HasValue && key != _bucketKey.Value && _bucketHasBars)
        {
            CloseHtfBar();
            closed = true;
        }
        if (!_bucketKey.HasValue || key != _bucketKey.Value)
        {
            _bucketKey = key;
            _bucketOpenTime = bar.OpenTime;
            _bucketOpen = bar.Open;
            _bucketHigh = bar.High;
            _bucketLow = bar.Low;
            _bucketHasBars = true;
        }
        else
        {
            _bucketHigh = Math.Max(_bucketHigh, bar.High);
            _bucketLow = Math.Min(_bucketLow, bar.Low);
        }
        _bucketClose = bar.Close;
        _bucketCloseTime = bar.CloseTime;
        return closed;
    }

    /// <summary>
    /// HTF snapshot rolled back by <paramref name="shiftBars"/> CLOSED 1h bars (0 = last
    /// closed). Null during warmup (fewer than MinClosedBars + shiftBars closed bars).
    /// </summary>
    public HtfSnapshot? Snapshot(int shiftBars = 0)
    {
        var idx = _snapshots.Count - 1 - shiftBars;
        if (idx < 0)
            return null;
        // warmup counted on the SHIFTED stream: the snapshot itself must sit at or past
        // the 28-closed-bar warmup point of its own history.
        if (idx + 1 < MinClosedBars)
            return null;
        return _snapshots[idx];
    }

    private void CloseHtfBar()
    {
        var high = _bucketHigh;
        var low = _bucketLow;
        var close = _bucketClose;
        _closedBars++;

        if (_closedBars == 1)
        {
            _prevHigh = high; _prevLow = low; _prevClose = close;
            AppendSnapshot();
            return;
        }

        var tr = Math.Max(high - low, Math.Max(Math.Abs(high - _prevClose), Math.Abs(low - _prevClose)));
        var upMove = high - _prevHigh;
        var downMove = _prevLow - low;
        var plusDm = upMove > downMove && upMove > 0.0 ? upMove : 0.0;
        var minusDm = downMove > upMove && downMove > 0.0 ? downMove : 0.0;

        var trBars = _closedBars - 1;   // TR/DM defined from the 2nd closed bar on
        if (trBars <= DmiPeriod)
        {
            _sumTr += tr; _sumPlusDm += plusDm; _sumMinusDm += minusDm;
            if (trBars == DmiPeriod)
            {
                _smTr = _sumTr; _smPlusDm = _sumPlusDm; _smMinusDm = _sumMinusDm;
                _atr = _sumTr / DmiPeriod;
                ComputeDiDx();
            }
        }
        else
        {
            _smTr = _smTr - _smTr / DmiPeriod + tr;
            _smPlusDm = _smPlusDm - _smPlusDm / DmiPeriod + plusDm;
            _smMinusDm = _smMinusDm - _smMinusDm / DmiPeriod + minusDm;
            _atr = (_atr * (DmiPeriod - 1) + tr) / DmiPeriod;
            ComputeDiDx();
        }

        _prevHigh = high; _prevLow = low; _prevClose = close;
        AppendSnapshot();
    }

    private void ComputeDiDx()
    {
        _plusDi = _smTr > 0.0 ? 100.0 * _smPlusDm / _smTr : 0.0;
        _minusDi = _smTr > 0.0 ? 100.0 * _smMinusDm / _smTr : 0.0;
        var diSum = _plusDi + _minusDi;
        var dx = diSum > 0.0 ? 100.0 * Math.Abs(_plusDi - _minusDi) / diSum : 0.0;
        _dxCount++;
        if (_dxCount <= DmiPeriod)
        {
            _dxSum += dx;
            if (_dxCount == DmiPeriod)
                _adx = _dxSum / DmiPeriod;
        }
        else
        {
            _adx = (_adx * (DmiPeriod - 1) + dx) / DmiPeriod;
        }
    }

    private void AppendSnapshot()
    {
        var haveDmi = _closedBars - 1 >= DmiPeriod;   // DI/ATR defined
        var atrRegime = -1;
        var adxReady = false;
        var adxAbove = false;

        if (haveDmi)
        {
            _atrWindow.Enqueue(_atr);
            if (_atrWindow.Count > RegimeWindow) _atrWindow.Dequeue();
            if (_atrWindow.Count == RegimeWindow)
                atrRegime = TercileOf(_atr, _atrWindow);

            if (_dxCount >= DmiPeriod)
            {
                _adxWindow.Enqueue(_adx);
                if (_adxWindow.Count > RegimeWindow) _adxWindow.Dequeue();
                if (_adxWindow.Count == RegimeWindow)
                {
                    adxReady = true;
                    adxAbove = _adx > MedianOf(_adxWindow);
                }
            }
        }

        _snapshots.Add(new HtfSnapshot(
            _bucketCloseTime,
            haveDmi ? _plusDi : double.NaN,
            haveDmi ? _minusDi : double.NaN,
            _dxCount >= DmiPeriod ? _adx : double.NaN,
            haveDmi ? _atr : double.NaN,
            atrRegime,
            adxReady,
            adxAbove));
    }

    private static int TercileOf(double value, IReadOnlyCollection<double> window)
    {
        var sorted = window.ToArray();
        Array.Sort(sorted);
        var lo = sorted[(int)Math.Floor(sorted.Length / 3.0)];
        var hi = sorted[(int)Math.Floor(2.0 * sorted.Length / 3.0)];
        if (value <= lo) return 0;
        if (value <= hi) return 1;
        return 2;
    }

    private static double MedianOf(IReadOnlyCollection<double> window)
    {
        var sorted = window.ToArray();
        Array.Sort(sorted);
        var n = sorted.Length;
        return n % 2 == 1 ? sorted[n / 2] : 0.5 * (sorted[n / 2 - 1] + sorted[n / 2]);
    }

    private long BucketKey(DateTime closeTime)
    {
        var utc = closeTime.Kind switch
        {
            DateTimeKind.Utc => closeTime,
            DateTimeKind.Local => closeTime.ToUniversalTime(),
            _ => DateTime.SpecifyKind(closeTime, DateTimeKind.Utc)
        };
        var seconds = (long)(utc - Epoch).TotalSeconds;
        return (seconds - 1) / (_htfMinutes * 60L);
    }
}
