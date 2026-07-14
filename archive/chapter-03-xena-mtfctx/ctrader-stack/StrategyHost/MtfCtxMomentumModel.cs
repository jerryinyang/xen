using System.Text.Json;
using Parquet;
using Parquet.Data;
using Parquet.Schema;

namespace Xen.StrategyHost;

// ===========================================================================
// XENA-002 MTFCTX-C2 — CTRL-02 NAIVE MOMENTUM multi-candidate host.
//
// Design: python/experiments/XENA-002/design.md (QA APPROVE run 1, design
// stage, 2026-07-11). One model instance runs ONE (symbol, LTF domain) feed
// and evaluates ALL 76 candidates (19 filter variants x 4 hold multipliers).
// All candidates of a feed share the same deterministic breakout signal
// stream and differ only by filter masking + hold length.
//
// From-scratch clause (design §3 / Amendment 1): no code reuse from
// MtfCtxRandomModel; the HTF feature logic below (Wilder ADX/DI(14),
// median-TR ATR(14), hysteresis vol regime, 250-bar percentile rank) is
// implemented directly from the family spec
// (docs/signal-registry/candidate-families/cf-mtfctx-001.md) and the design
// pins; QA verifies spec equivalence in a fresh context.
//
// DEVIATIONS: none. Interpretations (recorded per the silent-deviation rule):
//   * hold exit is processed before the same bar's entry decision, so a
//     candidate whose hold ends at bar t may re-enter at bar t if a breakout
//     signal is live (the family/XENA-001 convention);
//   * HTF minutes derive from the registered domain-pair map
//     (60->1440, 15->240, 5->60) — the three registered pairs only;
//   * entry additionally requires the median-TR ATR to be ready (SlPrice is
//     mandatory on every leg) and >= 4 confirmed LTF bars (breakout window).
//
// Causality: the decision at bar t's open uses (a) the breakout comparison
// Close[t-1] vs High/Low[t-4..t-2] over CONFIRMED LTF bars only (bar t's own
// OHLC is never read before the fill at bar t's Open), (b) HTF features from
// HTF buckets completed strictly before bar t's bucket, (c) the candidate's
// own past state. Strict inequalities; ties = no signal.
//
// Emission: per candidate, data/strategy_runs/XENA-002/<candidate-id>/ with
// run_metadata.json + positions.parquet (shared real-OHLC grid +
// per-candidate Position/IsFlat/OpenLegs) + cis_trades.parquet (per-leg
// fills, finite SlPrice on every leg — XENA fills contract). The feed-level
// writer keeps its own run dir (sentinel Position=0 rows) purely for the
// harness's run-completion gating; it is not a candidate.
// ===========================================================================
public sealed class MtfCtxMomentumModel : ISignalModel, IDisposable
{
    private const int BreakoutLookback = 3;    // prior-range window (family pin, CTRL-02)
    private const int AtrPeriod = 14;          // median-TR ATR window (family pin)
    private const int AdxPeriod = 14;          // Wilder ADX/DI period
    private const double AdxThreshold = 25.0;  // trend-strength split
    private const int VolRankWindow = 250;     // percentile window (design pin, 200-300)
    private const double SlAtrMultiple = 2.0;  // sizing stop k (design pin)
    private const int VariantCount = 19;
    private static readonly string[] HoldLabels = { "H05X", "H1X", "H2X", "H4X" };

    private readonly string _symbol;
    private readonly string _domainPair;       // "1D1H" | "4H15M" | "1H5M"
    private readonly int[] _holdBars;
    private readonly string _outputRoot;
    private readonly DateTime _analysisEndUtc;
    private readonly int _htfMinutes;

    // Confirmed-LTF-bar window for the breakout read: [t-4, t-3, t-2, t-1]
    // relative to the current decision bar t (front = oldest).
    private readonly Queue<TimeBar> _ltfWindow = new();

    // HTF bucketing (same causal bucket-roll convention the harness uses for
    // aggregated views: bucket key from (closeSeconds-1)/(period*60); an HTF
    // bar is emitted when the bucket rolls, from whatever LTF bars the session
    // provided — completed buckets only).
    private readonly List<TimeBar> _htfBucket = new();
    private long? _htfBucketKey;

    // --- HTF feature state (completed HTF bars only) ---
    private TimeBar? _prevHtfBar;
    private readonly Queue<double> _trWindow = new();
    private double _medAtr = double.NaN;
    private bool _medAtrReady;
    private readonly Queue<double> _medAtrHistory = new();
    private int _volLabel = -1;                 // 0 LOW / 1 MID / 2 HIGH
    private bool _volReady;
    private int _dmCount;
    private double _smTr, _smPlusDm, _smMinusDm;
    private double _plusDi = double.NaN, _minusDi = double.NaN;
    private int _dxCount;
    private double _dxSum, _adx = double.NaN;
    private bool _adxReady;
    private DateTime _lastHtfCloseTime = DateTime.MinValue;

    // --- shared per-bar grid (one copy per feed; written into every candidate dir) ---
    private readonly List<DateTime> _gridCloseTime = new();
    private readonly List<double> _gridOpen = new();
    private readonly List<double> _gridHigh = new();
    private readonly List<double> _gridLow = new();
    private readonly List<double> _gridClose = new();
    private readonly List<bool> _gridWarmup = new();

    private sealed class Candidate
    {
        public string Id = "";
        public int Variant;
        public int HoldBars;
        public List<sbyte> Positions = new();
        public List<CisTradeRecord> Trades = new();
        public int Direction;                  // 0 = flat
        public int EntryBarIndex = -1;
        public DateTime EntryTime;
        public double EntryFill = double.NaN;
        public double SlPrice = double.NaN;
        public double EntryAdx = double.NaN, EntryPlusDi = double.NaN,
                      EntryMinusDi = double.NaN, EntryAtr = double.NaN;
        public DateTime EntryHtfClose = DateTime.MinValue;
    }

    private readonly Candidate[] _candidates;
    private int _barIndex = -1;
    private bool _disposed;

    public MtfCtxMomentumModel(string symbol, int ltfDomainMinutes, string outputRoot,
                               DateTime analysisEndUtc)
    {
        _symbol = symbol.ToUpperInvariant();
        var (htfMinutes, pairLabel) = ltfDomainMinutes switch
        {
            60 => (1440, "1D1H"),
            15 => (240, "4H15M"),
            5 => (60, "1H5M"),
            _ => throw new InvalidOperationException(
                $"MtfCtxMomentum supports LTF domains 60/15/5 minutes only; got {ltfDomainMinutes}.")
        };
        _domainPair = pairLabel;
        var baseSpan = htfMinutes / ltfDomainMinutes;
        _holdBars = new[] { baseSpan / 2, baseSpan, 2 * baseSpan, 4 * baseSpan };
        _outputRoot = outputRoot;
        _analysisEndUtc = analysisEndUtc;
        _htfMinutes = htfMinutes;

        _candidates = new Candidate[VariantCount * 4];
        for (var v = 0; v < VariantCount; v++)
            for (var h = 0; h < 4; h++)
                _candidates[v * 4 + h] = new Candidate
                {
                    Id = $"C2-{_symbol}-{_domainPair}-{HoldLabels[h]}-V{v:00}",
                    Variant = v,
                    HoldBars = _holdBars[h]
                };
        StrategyName = "mtfctx_c2";
    }

    public string StrategyName { get; }

    public SignalUpdate OnBar(TimeBar bar, string domain)
    {
        _barIndex++;

        // (a) HTF features first: a completed HTF bucket closed <= this bar's open.
        var htfKey = (SecondsSinceEpoch(bar.CloseTime) - 1) / (_htfMinutes * 60L);
        if (_htfBucketKey.HasValue && htfKey != _htfBucketKey.Value && _htfBucket.Count > 0)
        {
            UpdateHtfFeatures(BuildHtfBar());
            _htfBucket.Clear();
        }
        _htfBucketKey = htfKey;
        _htfBucket.Add(bar);

        // (b) breakout signal from confirmed LTF bars only (design §3):
        //     LONG  if Close[t-1] > max(High[t-4..t-2]);
        //     SHORT if Close[t-1] < min(Low[t-4..t-2]). Strict; ties = no signal.
        var signalSide = 0;
        if (_ltfWindow.Count == BreakoutLookback + 1)
        {
            var window = _ltfWindow.ToArray();          // [t-4, t-3, t-2, t-1]
            var prevClose = window[BreakoutLookback].Close;
            var rangeHigh = double.NegativeInfinity;
            var rangeLow = double.PositiveInfinity;
            for (var i = 0; i < BreakoutLookback; i++)
            {
                rangeHigh = Math.Max(rangeHigh, window[i].High);
                rangeLow = Math.Min(rangeLow, window[i].Low);
            }
            if (prevClose > rangeHigh)
                signalSide = 1;
            else if (prevClose < rangeLow)
                signalSide = -1;
        }

        // (c) per-candidate hold exits, then entry decisions, at THIS bar's open.
        foreach (var cand in _candidates)
        {
            if (cand.Direction != 0 && _barIndex - cand.EntryBarIndex == cand.HoldBars)
                CloseLeg(cand, bar, exitFill: bar.Open, censored: false);

            if (cand.Direction == 0 && signalSide != 0 && _medAtrReady
                && VariantAllows(cand.Variant, signalSide))
            {
                cand.Direction = signalSide;
                cand.EntryBarIndex = _barIndex;
                cand.EntryTime = bar.CloseTime;
                cand.EntryFill = bar.Open;
                cand.SlPrice = bar.Open - signalSide * SlAtrMultiple * _medAtr;
                cand.EntryAdx = _adx;
                cand.EntryPlusDi = _plusDi;
                cand.EntryMinusDi = _minusDi;
                cand.EntryAtr = _medAtr;
                cand.EntryHtfClose = _lastHtfCloseTime;
            }
            cand.Positions.Add((sbyte)cand.Direction);
        }

        // (d) shared grid row; then this bar becomes a confirmed bar for t+1.
        _gridCloseTime.Add(bar.CloseTime);
        _gridOpen.Add(bar.Open);
        _gridHigh.Add(bar.High);
        _gridLow.Add(bar.Low);
        _gridClose.Add(bar.Close);
        _gridWarmup.Add(!_medAtrReady);

        _ltfWindow.Enqueue(bar);
        if (_ltfWindow.Count > BreakoutLookback + 1)
            _ltfWindow.Dequeue();

        // Feed-level sentinel row (harness completion gating only; not a candidate).
        return SignalUpdate.PositionOnly(new SignalPositionRecord(
            bar.CloseTime, domain, StrategyName, 0, signalSide,
            bar.Open, bar.High, bar.Low, bar.Close, !_medAtrReady, true));
    }

    // ------------------------------------------------------------------ filters
    // Variant map (design §3): V00 baseline; V01 ADX<25; V02 ADX>=25; V03 DI
    // direction; V04/05/06 vol LOW/MID/HIGH; V07-V12 vol x ADX; V13-V18
    // vol x ADX + DI. Combo order: (LOW,<25)(LOW,>=25)(MID,<25)(MID,>=25)
    // (HIGH,<25)(HIGH,>=25).
    private bool VariantAllows(int variant, int side)
    {
        switch (variant)
        {
            case 0: return true;
            case 1: return _adxReady && _adx < AdxThreshold;
            case 2: return _adxReady && _adx >= AdxThreshold;
            case 3: return _adxReady && DiAllows(side);
            case 4: case 5: case 6:
                return _volReady && _volLabel == variant - 4;   // LOW=0, MID=1, HIGH=2
            default:
            {
                var k = variant >= 13 ? variant - 13 : variant - 7;
                var volTarget = k / 2;
                var wantHighAdx = (k % 2) == 1;
                if (!_volReady || !_adxReady)
                    return false;
                if (_volLabel != volTarget)
                    return false;
                if (wantHighAdx ? _adx < AdxThreshold : _adx >= AdxThreshold)
                    return false;
                return variant < 13 || DiAllows(side);
            }
        }
    }

    private bool DiAllows(int side) => side > 0 ? _plusDi > _minusDi : _plusDi < _minusDi;

    // ------------------------------------------------------------------ HTF features
    private static readonly DateTime Epoch = new(1970, 1, 1, 0, 0, 0, DateTimeKind.Utc);

    private static long SecondsSinceEpoch(DateTime closeTime)
    {
        var utc = closeTime.Kind switch
        {
            DateTimeKind.Utc => closeTime,
            DateTimeKind.Local => closeTime.ToUniversalTime(),
            _ => DateTime.SpecifyKind(closeTime, DateTimeKind.Utc)
        };
        return (long)(utc - Epoch).TotalSeconds;
    }

    private TimeBar BuildHtfBar()
    {
        var first = _htfBucket[0];
        var last = _htfBucket[^1];
        var high = double.NegativeInfinity;
        var low = double.PositiveInfinity;
        long volume = 0;
        foreach (var b in _htfBucket)
        {
            high = Math.Max(high, b.High);
            low = Math.Min(low, b.Low);
            volume += b.TickVolume;
        }
        return new TimeBar(first.Symbol, first.OpenTime, last.CloseTime,
            first.Open, high, low, last.Close, volume, _htfBucket.Count);
    }

    private void UpdateHtfFeatures(TimeBar htfBar)
    {
        _lastHtfCloseTime = htfBar.CloseTime;
        if (_prevHtfBar is null)
        {
            _prevHtfBar = htfBar;
            return;
        }

        var prevClose = _prevHtfBar.Close;
        var tr = Math.Max(htfBar.High - htfBar.Low,
                 Math.Max(Math.Abs(htfBar.High - prevClose), Math.Abs(htfBar.Low - prevClose)));

        // median-TR ATR(14): rolling median of the last 14 true ranges
        // (even window -> mean of the two middle order statistics).
        _trWindow.Enqueue(tr);
        if (_trWindow.Count > AtrPeriod)
            _trWindow.Dequeue();
        if (_trWindow.Count == AtrPeriod)
        {
            var sorted = _trWindow.ToArray();
            Array.Sort(sorted);
            _medAtr = (sorted[AtrPeriod / 2 - 1] + sorted[AtrPeriod / 2]) / 2.0;
            _medAtrReady = true;
            UpdateVolRegime(_medAtr);
        }

        // Wilder DM smoothing -> +DI/-DI -> DX -> ADX(14).
        var upMove = htfBar.High - _prevHtfBar.High;
        var downMove = _prevHtfBar.Low - htfBar.Low;
        var plusDm = upMove > downMove && upMove > 0 ? upMove : 0.0;
        var minusDm = downMove > upMove && downMove > 0 ? downMove : 0.0;
        if (_dmCount < AdxPeriod)
        {
            _smTr += tr;
            _smPlusDm += plusDm;
            _smMinusDm += minusDm;
            _dmCount++;
        }
        else
        {
            _smTr = _smTr - _smTr / AdxPeriod + tr;
            _smPlusDm = _smPlusDm - _smPlusDm / AdxPeriod + plusDm;
            _smMinusDm = _smMinusDm - _smMinusDm / AdxPeriod + minusDm;
        }
        if (_dmCount >= AdxPeriod && _smTr > 0)
        {
            _plusDi = 100.0 * _smPlusDm / _smTr;
            _minusDi = 100.0 * _smMinusDm / _smTr;
            var diSum = _plusDi + _minusDi;
            var dx = diSum > 0 ? 100.0 * Math.Abs(_plusDi - _minusDi) / diSum : 0.0;
            if (_dxCount < AdxPeriod)
            {
                _dxSum += dx;
                _dxCount++;
                if (_dxCount == AdxPeriod)
                {
                    _adx = _dxSum / AdxPeriod;
                    _adxReady = true;
                }
            }
            else
            {
                _adx = (_adx * (AdxPeriod - 1) + dx) / AdxPeriod;
            }
        }

        _prevHtfBar = htfBar;
    }

    // Percentile rank of the current medATR against the trailing 250 PRIOR
    // values; hysteresis: HIGH entered > P80 / exited < P65; LOW entered
    // < P20 / exited > P35; MID otherwise (family appendix pin).
    private void UpdateVolRegime(double currentMedAtr)
    {
        if (_medAtrHistory.Count >= VolRankWindow)
        {
            var below = 0;
            foreach (var v in _medAtrHistory)
                if (v < currentMedAtr)
                    below++;
            var pct = (double)below / _medAtrHistory.Count;

            if (!_volReady)
            {
                _volLabel = pct > 0.80 ? 2 : (pct < 0.20 ? 0 : 1);
                _volReady = true;
            }
            else
            {
                switch (_volLabel)
                {
                    case 2 when pct < 0.65:
                        _volLabel = pct < 0.20 ? 0 : 1;
                        break;
                    case 0 when pct > 0.35:
                        _volLabel = pct > 0.80 ? 2 : 1;
                        break;
                    case 1:
                        if (pct > 0.80) _volLabel = 2;
                        else if (pct < 0.20) _volLabel = 0;
                        break;
                }
            }
        }
        _medAtrHistory.Enqueue(currentMedAtr);
        if (_medAtrHistory.Count > VolRankWindow)
            _medAtrHistory.Dequeue();
    }

    // ------------------------------------------------------------------ legs
    private void CloseLeg(Candidate cand, TimeBar bar, double exitFill, bool censored)
    {
        var realized = censored
            ? double.NaN
            : cand.Direction * (exitFill - cand.EntryFill) / cand.EntryFill * 1e4;
        cand.Trades.Add(new CisTradeRecord(
            bar.CloseTime, _domainPair, StrategyName, cand.Id,
            cand.EntryTime, bar.CloseTime, cand.Direction, 0,
            cand.EntryFill, exitFill,
            censored ? "censored_end" : "hold_period",
            _barIndex - cand.EntryBarIndex, realized,
            double.NaN, double.NaN, double.NaN, double.NaN, double.NaN, double.NaN,
            double.NaN, 0, -1,
            double.NaN, double.NaN, double.NaN,
            censored ? 1 : 0,
            "", 0,
            cand.SlPrice, cand.HoldBars,
            double.NaN, 0,
            cand.EntryPlusDi, cand.EntryMinusDi, cand.EntryAdx, cand.EntryAtr,
            cand.EntryHtfClose));
        cand.Direction = 0;
        cand.EntryBarIndex = -1;
    }

    // ------------------------------------------------------------------ emission
    public void Dispose()
    {
        if (_disposed)
            return;
        _disposed = true;
        if (_gridCloseTime.Count == 0)
            return;

        var lastBarOpen = _gridOpen[^1];
        var lastBarTime = _gridCloseTime[^1];
        foreach (var cand in _candidates)
        {
            // Censor any leg still open at the fence (last mark = final emitted bar's open).
            if (cand.Direction != 0)
                cand.Trades.Add(new CisTradeRecord(
                    lastBarTime, _domainPair, StrategyName, cand.Id,
                    cand.EntryTime, lastBarTime, cand.Direction, 0,
                    cand.EntryFill, lastBarOpen, "censored_end",
                    _barIndex - cand.EntryBarIndex, double.NaN,
                    double.NaN, double.NaN, double.NaN, double.NaN, double.NaN, double.NaN,
                    double.NaN, 0, -1,
                    double.NaN, double.NaN, double.NaN, 1, "", 0,
                    cand.SlPrice, cand.HoldBars, double.NaN, 0,
                    cand.EntryPlusDi, cand.EntryMinusDi, cand.EntryAdx, cand.EntryAtr,
                    cand.EntryHtfClose));
            WriteCandidate(cand);
        }
    }

    private void WriteCandidate(Candidate cand)
    {
        var dir = Path.Combine(_outputRoot, cand.Id.ToLowerInvariant());
        Directory.CreateDirectory(dir);

        var metadata = new
        {
            candidate_id = cand.Id,
            strategy = StrategyName,
            symbol = _symbol,
            domain_pair = _domainPair,
            variant = cand.Variant,
            hold_bars = cand.HoldBars,
            analysis_end_utc = _analysisEndUtc.ToString("o"),
            breakout_lookback = BreakoutLookback,
            sl_atr_multiple = SlAtrMultiple,
            vol_rank_window = VolRankWindow,
            generated_utc = DateTime.UtcNow.ToString("o")
        };
        File.WriteAllText(Path.Combine(dir, "run_metadata.json"),
            JsonSerializer.Serialize(metadata, new JsonSerializerOptions { WriteIndented = true }));

        WritePositions(Path.Combine(dir, "positions.parquet"), cand);
        WriteCisTrades(Path.Combine(dir, "cis_trades.parquet"), cand.Trades);
    }

    private void WritePositions(string path, Candidate cand)
    {
        var n = _gridCloseTime.Count;
        var fields = new DataField[]
        {
            new DataField<DateTime>("SourceCloseTime"),
            new DataField<string>("Domain"),
            new DataField<string>("Strategy"),
            new DataField<int>("Position"),
            new DataField<double>("RealOpen"),
            new DataField<double>("RealHigh"),
            new DataField<double>("RealLow"),
            new DataField<double>("RealClose"),
            new DataField<bool>("Warmup"),
            new DataField<bool>("IsFlat"),
            new DataField<int>("OpenLegs")
        };
        var positions = new int[n];
        var isFlat = new bool[n];
        var openLegs = new int[n];
        for (var i = 0; i < n; i++)
        {
            positions[i] = cand.Positions[i];
            isFlat[i] = cand.Positions[i] == 0;
            openLegs[i] = cand.Positions[i] == 0 ? 0 : 1;
        }
        var domainCol = new string[n];
        var strategyCol = new string[n];
        Array.Fill(domainCol, _domainPair);
        Array.Fill(strategyCol, cand.Id);

        using var stream = new FileStream(path, FileMode.Create, FileAccess.Write);
        using var writer = ParquetWriter.CreateAsync(new ParquetSchema(fields), stream)
            .GetAwaiter().GetResult();
        writer.CompressionMethod = CompressionMethod.Zstd;
        using var group = writer.CreateRowGroup();
        group.WriteColumnAsync(new DataColumn(fields[0], _gridCloseTime.ToArray())).GetAwaiter().GetResult();
        group.WriteColumnAsync(new DataColumn(fields[1], domainCol)).GetAwaiter().GetResult();
        group.WriteColumnAsync(new DataColumn(fields[2], strategyCol)).GetAwaiter().GetResult();
        group.WriteColumnAsync(new DataColumn(fields[3], positions)).GetAwaiter().GetResult();
        group.WriteColumnAsync(new DataColumn(fields[4], _gridOpen.ToArray())).GetAwaiter().GetResult();
        group.WriteColumnAsync(new DataColumn(fields[5], _gridHigh.ToArray())).GetAwaiter().GetResult();
        group.WriteColumnAsync(new DataColumn(fields[6], _gridLow.ToArray())).GetAwaiter().GetResult();
        group.WriteColumnAsync(new DataColumn(fields[7], _gridClose.ToArray())).GetAwaiter().GetResult();
        group.WriteColumnAsync(new DataColumn(fields[8], _gridWarmup.ToArray())).GetAwaiter().GetResult();
        group.WriteColumnAsync(new DataColumn(fields[9], isFlat)).GetAwaiter().GetResult();
        group.WriteColumnAsync(new DataColumn(fields[10], openLegs)).GetAwaiter().GetResult();
    }

    private static void WriteCisTrades(string path, IReadOnlyList<CisTradeRecord> rows)
    {
        var fields = new DataField[]
        {
            new DataField<DateTime>("SourceCloseTime"),
            new DataField<string>("Domain"),
            new DataField<string>("Strategy"),
            new DataField<string>("Series"),
            new DataField<DateTime>("EntryTime"),
            new DataField<DateTime>("ExitTime"),
            new DataField<int>("Direction"),
            new DataField<double>("EntryFillPrice"),
            new DataField<double>("ExitFillPrice"),
            new DataField<string>("ExitReason"),
            new DataField<int>("BarsHeld"),
            new DataField<double>("RealizedBps"),
            new DataField<int>("Censored"),
            new DataField<double>("SlPrice"),
            new DataField<int>("HorizonBars"),
            new DataField<double>("HtfPlusDi"),
            new DataField<double>("HtfMinusDi"),
            new DataField<double>("HtfAdx"),
            new DataField<double>("HtfAtr"),
            new DataField<DateTime>("HtfBarCloseTime")
        };
        using var stream = new FileStream(path, FileMode.Create, FileAccess.Write);
        using var writer = ParquetWriter.CreateAsync(new ParquetSchema(fields), stream)
            .GetAwaiter().GetResult();
        writer.CompressionMethod = CompressionMethod.Zstd;
        using var group = writer.CreateRowGroup();
        group.WriteColumnAsync(new DataColumn(fields[0], rows.Select(r => r.SourceCloseTime).ToArray())).GetAwaiter().GetResult();
        group.WriteColumnAsync(new DataColumn(fields[1], rows.Select(r => r.Domain).ToArray())).GetAwaiter().GetResult();
        group.WriteColumnAsync(new DataColumn(fields[2], rows.Select(r => r.Strategy).ToArray())).GetAwaiter().GetResult();
        group.WriteColumnAsync(new DataColumn(fields[3], rows.Select(r => r.Series).ToArray())).GetAwaiter().GetResult();
        group.WriteColumnAsync(new DataColumn(fields[4], rows.Select(r => r.EntryTime).ToArray())).GetAwaiter().GetResult();
        group.WriteColumnAsync(new DataColumn(fields[5], rows.Select(r => r.ExitTime).ToArray())).GetAwaiter().GetResult();
        group.WriteColumnAsync(new DataColumn(fields[6], rows.Select(r => r.Direction).ToArray())).GetAwaiter().GetResult();
        group.WriteColumnAsync(new DataColumn(fields[7], rows.Select(r => r.EntryFillPrice).ToArray())).GetAwaiter().GetResult();
        group.WriteColumnAsync(new DataColumn(fields[8], rows.Select(r => r.ExitFillPrice).ToArray())).GetAwaiter().GetResult();
        group.WriteColumnAsync(new DataColumn(fields[9], rows.Select(r => r.ExitReason).ToArray())).GetAwaiter().GetResult();
        group.WriteColumnAsync(new DataColumn(fields[10], rows.Select(r => r.BarsHeld).ToArray())).GetAwaiter().GetResult();
        group.WriteColumnAsync(new DataColumn(fields[11], rows.Select(r => r.RealizedBps).ToArray())).GetAwaiter().GetResult();
        group.WriteColumnAsync(new DataColumn(fields[12], rows.Select(r => r.Censored).ToArray())).GetAwaiter().GetResult();
        group.WriteColumnAsync(new DataColumn(fields[13], rows.Select(r => r.SlPrice).ToArray())).GetAwaiter().GetResult();
        group.WriteColumnAsync(new DataColumn(fields[14], rows.Select(r => r.HorizonBars).ToArray())).GetAwaiter().GetResult();
        group.WriteColumnAsync(new DataColumn(fields[15], rows.Select(r => r.HtfPlusDi).ToArray())).GetAwaiter().GetResult();
        group.WriteColumnAsync(new DataColumn(fields[16], rows.Select(r => r.HtfMinusDi).ToArray())).GetAwaiter().GetResult();
        group.WriteColumnAsync(new DataColumn(fields[17], rows.Select(r => r.HtfAdx).ToArray())).GetAwaiter().GetResult();
        group.WriteColumnAsync(new DataColumn(fields[18], rows.Select(r => r.HtfAtr).ToArray())).GetAwaiter().GetResult();
        group.WriteColumnAsync(new DataColumn(fields[19], rows.Select(r => r.HtfBarCloseTime).ToArray())).GetAwaiter().GetResult();
    }
}
