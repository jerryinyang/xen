using System.Text.Json;
using Parquet;
using Parquet.Data;
using Parquet.Schema;

namespace Xen.StrategyHost;

// ===========================================================================
// XENA-003 MTFCTX-C3 — CTRL-03 NAIVE REVERSION multi-candidate host.
//
// Design: python/experiments/XENA-003/design.md (QA APPROVE run 1, design
// stage, 2026-07-11). One model instance runs ONE (symbol, LTF domain) feed
// and evaluates ALL 76 candidates (19 filter variants x 4 hold multipliers).
//
// EXECUTION CONTRACT (EXP-013 carve-out, family binding constraint): entries
// are NATIVE cTrader limit orders filled by the engine against m1 backtest
// data. This model NEVER simulates a fill; it computes desired quotes and
// exit instructions, and the Xen robot (Xen.NativeReversion partial) places /
// amends / cancels the real orders and routes engine fill events back via
// OnEntryFilled / OnExitFilled.
//
// From-scratch clause (family / XENA-002 Amendment 2 scope): entry/model
// logic written from scratch; the HTF feature block (Wilder ADX/DI(14),
// median-TR ATR(14), hysteresis vol regime, 250-bar percentile rank) is
// spec-identical to the family implementation — cross-universe comparability
// (operator decision 2026-07-11, XENA-002 QA run 2); QA verifies spec
// equivalence in a fresh context.
//
// DEVIATIONS: none. Interpretations (recorded per the silent-deviation rule):
//   * decisions pinned to "LTF bar t open" execute when the aggregator emits
//     the completed bar t-1, i.e. at the first m1 tick of bar t — engine
//     market fills land at the first available price of the bar, not the
//     bar's recorded Open field (native-execution reality; the physicality
//     tripwire audits fills against raw m1);
//   * crossed-limit rule (operator 2026-07-11): a side quotes ONLY when
//     passive — buy limit strictly below current Bid, sell limit strictly
//     above current Ask; a crossed side simply does not rest that bar;
//   * hold exit is processed before the same bar's quote refresh, so a
//     candidate whose hold ends at bar t may re-quote at bar t (family
//     convention);
//   * HTF minutes derive from the registered domain-pair map
//     (60->1440, 15->240, 5->60) — the three registered pairs only;
//   * quoting additionally requires the median-TR ATR to be ready (SlPrice
//     is mandatory on every leg) and >= 3 confirmed LTF bars (extreme window).
//
// Causality: quote decisions at bar t's open use (a) the 3-bar extreme over
// CONFIRMED LTF bars t-3..t-1 only, (b) HTF features from HTF buckets
// completed strictly before bar t's bucket, (c) the candidate's own past
// state. The profit exit reads Close[t-1] (confirmed) against the CURRENT
// HTF median-TR ATR (latest confirmed HTF bar) — the distance floats, never
// entry-frozen (L-14 moving-target rule).
//
// Emission: per candidate, data/strategy_runs/XENA-003/<candidate-id>/ with
// run_metadata.json + positions.parquet (shared real-OHLC grid) +
// cis_trades.parquet (engine fills, finite SlPrice on every leg — XENA
// fills contract). Feed-level sentinel rows keep the harness's
// run-completion gating, as in XENA-001/002.
// ===========================================================================

/// <summary>Robot-side order executor the model drives (native orders only).</summary>
public interface INativeQuoteExecutor
{
    /// <summary>Ensure candidate's side quote matches <paramref name="limitPrice"/>;
    /// null cancels any resting order on that side. side: +1 buy, -1 sell.</summary>
    void SyncQuote(string candidateId, int side, double? limitPrice);

    /// <summary>Market-close the candidate's open engine position (exit fill is
    /// reported back via OnExitFilled).</summary>
    void CloseCandidate(string candidateId, string exitReason);
}

public sealed class MtfCtxReversionModel : ISignalModel, IDisposable
{
    private const int ExtremeLookback = 3;     // trailing extreme window (family pin, CTRL-03)
    private const int AtrPeriod = 14;          // median-TR ATR window (family pin)
    private const int AdxPeriod = 14;          // Wilder ADX/DI period
    private const double AdxThreshold = 25.0;  // trend-strength split
    private const int VolRankWindow = 250;     // percentile window (design pin, 200-300)
    private const double SlAtrMultiple = 2.0;  // sizing stop k (design pin)
    private const double ProfitAtrMultiple = 0.5; // floating profit-exit distance (family pin)
    private const int VariantCount = 19;
    private static readonly string[] HoldLabels = { "H05X", "H1X", "H2X", "H4X" };

    private readonly string _symbol;
    private readonly string _domainPair;       // "1D1H" | "4H15M" | "1H5M"
    private readonly int[] _holdBars;
    private readonly string _outputRoot;
    private readonly DateTime _analysisEndUtc;
    private readonly int _htfMinutes;
    private INativeQuoteExecutor? _executor;

    // Confirmed-LTF-bar window for the extreme read: [t-3, t-2, t-1] relative
    // to the current decision bar t (front = oldest).
    private readonly Queue<TimeBar> _ltfWindow = new();

    // HTF bucketing (family causal bucket-roll convention).
    private readonly List<TimeBar> _htfBucket = new();
    private long? _htfBucketKey;

    // --- HTF feature state (completed HTF bars only; spec-identical block) ---
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

        public int Direction;                  // 0 = flat (engine-confirmed)
        public bool ExitPending;               // close requested, engine fill not yet reported
        public string PendingExitReason = "";
        public int EntryBarIndex = -1;         // LTF bar index containing the entry fill
        public DateTime EntryTime;
        public double EntryFill = double.NaN;
        public double SlPrice = double.NaN;
        public double EntryAdx = double.NaN, EntryPlusDi = double.NaN,
                      EntryMinusDi = double.NaN, EntryAtr = double.NaN;
        public DateTime EntryHtfClose = DateTime.MinValue;

        // Context captured at the quote refresh that armed the resting order —
        // the HTF state that authorized the entry (design §3).
        public double ArmedAdx = double.NaN, ArmedPlusDi = double.NaN,
                      ArmedMinusDi = double.NaN, ArmedAtr = double.NaN;
        public DateTime ArmedHtfClose = DateTime.MinValue;
    }

    private readonly Candidate[] _candidates;
    private readonly Dictionary<string, Candidate> _byId;
    private bool _disposed;

    public MtfCtxReversionModel(string symbol, int ltfDomainMinutes, string outputRoot,
                                DateTime analysisEndUtc)
    {
        _symbol = symbol.ToUpperInvariant();
        var (htfMinutes, pairLabel) = ltfDomainMinutes switch
        {
            60 => (1440, "1D1H"),
            15 => (240, "4H15M"),
            5 => (60, "1H5M"),
            _ => throw new InvalidOperationException(
                $"MtfCtxReversion supports LTF domains 60/15/5 minutes only; got {ltfDomainMinutes}.")
        };
        _domainPair = pairLabel;
        var baseSpan = htfMinutes / ltfDomainMinutes;
        _holdBars = new[] { baseSpan / 2, baseSpan, 2 * baseSpan, 4 * baseSpan };
        _outputRoot = outputRoot;
        _analysisEndUtc = analysisEndUtc;
        _htfMinutes = htfMinutes;

        _candidates = new Candidate[VariantCount * 4];
        _byId = new Dictionary<string, Candidate>(_candidates.Length);
        for (var v = 0; v < VariantCount; v++)
            for (var h = 0; h < 4; h++)
            {
                var cand = new Candidate
                {
                    Id = $"C3-{_symbol}-{_domainPair}-{HoldLabels[h]}-V{v:00}",
                    Variant = v,
                    HoldBars = _holdBars[h]
                };
                _candidates[v * 4 + h] = cand;
                _byId[cand.Id] = cand;
            }
        StrategyName = "mtfctx_c3";
    }

    public string StrategyName { get; }

    public void AttachExecutor(INativeQuoteExecutor executor) => _executor = executor;

    // ------------------------------------------------------------------ engine events
    /// <summary>Engine entry fill (robot event). Bar index of the fill = the
    /// currently forming LTF bar = count of completed grid rows.</summary>
    public void OnEntryFilled(string candidateId, DateTime fillTimeUtc, double fillPrice, int side)
    {
        var cand = _byId[candidateId];
        cand.Direction = side;
        cand.EntryBarIndex = _gridCloseTime.Count;
        cand.EntryTime = fillTimeUtc;
        cand.EntryFill = fillPrice;
        cand.SlPrice = fillPrice - side * SlAtrMultiple * cand.ArmedAtr;
        cand.EntryAdx = cand.ArmedAdx;
        cand.EntryPlusDi = cand.ArmedPlusDi;
        cand.EntryMinusDi = cand.ArmedMinusDi;
        cand.EntryAtr = cand.ArmedAtr;
        cand.EntryHtfClose = cand.ArmedHtfClose;
        // One position at a time: the robot cancels the other side on fill.
    }

    /// <summary>Engine exit fill (robot event, market close we requested).</summary>
    public void OnExitFilled(string candidateId, DateTime fillTimeUtc, double fillPrice)
    {
        var cand = _byId[candidateId];
        if (cand.Direction == 0)
            return; // already censored/flat (fence flatten) — never double-book

        var barsHeld = _gridCloseTime.Count - cand.EntryBarIndex;
        var realized = cand.Direction * (fillPrice - cand.EntryFill) / cand.EntryFill * 1e4;
        cand.Trades.Add(BuildTrade(cand, fillTimeUtc, fillPrice,
            string.IsNullOrEmpty(cand.PendingExitReason) ? "hold_period" : cand.PendingExitReason,
            barsHeld, realized, censored: false));
        cand.Direction = 0;
        cand.ExitPending = false;
        cand.PendingExitReason = "";
        cand.EntryBarIndex = -1;
    }

    // ------------------------------------------------------------------ per-LTF-bar decision
    /// <summary>Called by the robot when LTF bar (index = grid count) completes —
    /// i.e. standing at the NEXT bar's open. bid/ask = current market (passivity check).</summary>
    public SignalUpdate OnLtfBarCompleted(TimeBar bar, string domain, double bid, double ask)
    {
        if (_executor is null)
            throw new InvalidOperationException("MtfCtxReversion requires an attached native-order executor.");

        // (a) HTF features first: a completed HTF bucket closed <= this bar's open.
        var htfKey = (SecondsSinceEpoch(bar.CloseTime) - 1) / (_htfMinutes * 60L);
        if (_htfBucketKey.HasValue && htfKey != _htfBucketKey.Value && _htfBucket.Count > 0)
        {
            UpdateHtfFeatures(BuildHtfBar());
            _htfBucket.Clear();
        }
        _htfBucketKey = htfKey;
        _htfBucket.Add(bar);

        // (b) grid row for the completed bar; state below refers to the NEXT
        // (forming) bar's open — index _gridCloseTime.Count after this append.
        _gridCloseTime.Add(bar.CloseTime);
        _gridOpen.Add(bar.Open);
        _gridHigh.Add(bar.High);
        _gridLow.Add(bar.Low);
        _gridClose.Add(bar.Close);
        _gridWarmup.Add(!_medAtrReady);

        _ltfWindow.Enqueue(bar);
        if (_ltfWindow.Count > ExtremeLookback)
            _ltfWindow.Dequeue();

        var formingIndex = _gridCloseTime.Count;   // LTF bar index of the bar now opening

        // (c) trailing extremes over the last 3 CONFIRMED bars.
        var haveWindow = _ltfWindow.Count == ExtremeLookback;
        var rangeLow = double.PositiveInfinity;
        var rangeHigh = double.NegativeInfinity;
        if (haveWindow)
            foreach (var b in _ltfWindow)
            {
                rangeLow = Math.Min(rangeLow, b.Low);
                rangeHigh = Math.Max(rangeHigh, b.High);
            }

        foreach (var cand in _candidates)
        {
            // Exits first (design: whichever first; processed at bar open).
            if (cand.Direction != 0 && !cand.ExitPending)
            {
                var held = formingIndex - cand.EntryBarIndex;
                var profitDist = cand.Direction * (bar.Close - cand.EntryFill); // price units
                if (held >= cand.HoldBars)
                {
                    cand.ExitPending = true;
                    cand.PendingExitReason = "hold_period";
                    _executor.CloseCandidate(cand.Id, "hold_period");
                }
                else if (_medAtrReady && profitDist > 0
                         && profitDist >= ProfitAtrMultiple * _medAtr)
                {
                    cand.ExitPending = true;
                    cand.PendingExitReason = "profit_exit";
                    _executor.CloseCandidate(cand.Id, "profit_exit");
                }
            }

            // Quote refresh: two-sided trailing limits while flat; a side rests
            // only if the variant mask allows it AND the quote is passive.
            var flat = cand.Direction == 0 && !cand.ExitPending;
            double? buyQuote = null, sellQuote = null;
            if (flat && haveWindow && _medAtrReady)
            {
                if (VariantAllows(cand.Variant, +1) && rangeLow < bid)
                    buyQuote = rangeLow;
                if (VariantAllows(cand.Variant, -1) && rangeHigh > ask)
                    sellQuote = rangeHigh;
                if (buyQuote.HasValue || sellQuote.HasValue)
                {
                    cand.ArmedAdx = _adx;
                    cand.ArmedPlusDi = _plusDi;
                    cand.ArmedMinusDi = _minusDi;
                    cand.ArmedAtr = _medAtr;
                    cand.ArmedHtfClose = _lastHtfCloseTime;
                }
            }
            _executor.SyncQuote(cand.Id, +1, flat ? buyQuote : null);
            _executor.SyncQuote(cand.Id, -1, flat ? sellQuote : null);

            cand.Positions.Add((sbyte)cand.Direction);
        }

        // Feed-level sentinel row (harness completion gating only; not a candidate).
        return SignalUpdate.PositionOnly(new SignalPositionRecord(
            bar.CloseTime, domain, StrategyName, 0, 0,
            bar.Open, bar.High, bar.Low, bar.Close, !_medAtrReady, true));
    }

    /// <summary>Fence/end-of-run: mark still-open legs censored (last mark = final
    /// emitted bar's open, family convention). The robot separately flattens the
    /// engine account; those fills are NOT booked (censored legs carry NaN P&L).</summary>
    public void CensorOpenLegs()
    {
        if (_gridCloseTime.Count == 0)
            return;
        var lastBarOpen = _gridOpen[^1];
        var lastBarTime = _gridCloseTime[^1];
        foreach (var cand in _candidates)
        {
            if (cand.Direction == 0)
                continue;
            // A leg whose entry fill landed inside the never-completed final LTF
            // bar (EntryTime > last grid mark; possibly at/after the fence tick)
            // has no grid representation — emitting it violates the fence /
            // entries-in-grid contract (candidate gate). Drop it: censored legs
            // are NaN-P&L and oracle-invisible either way.
            if (cand.EntryTime > lastBarTime)
            {
                cand.Direction = 0;
                cand.ExitPending = false;
                cand.EntryBarIndex = -1;
                continue;
            }
            cand.Trades.Add(BuildTrade(cand, lastBarTime, lastBarOpen, "censored_end",
                _gridCloseTime.Count - 1 - cand.EntryBarIndex, double.NaN, censored: true));
            cand.Direction = 0;
            cand.ExitPending = false;
            cand.EntryBarIndex = -1;
        }
    }

    private CisTradeRecord BuildTrade(Candidate cand, DateTime exitTime, double exitFill,
                                      string reason, int barsHeld, double realized, bool censored)
    {
        return new CisTradeRecord(
            exitTime, _domainPair, StrategyName, cand.Id,
            cand.EntryTime, exitTime, cand.Direction, 0,
            cand.EntryFill, exitFill, reason,
            barsHeld, realized,
            double.NaN, double.NaN, double.NaN, double.NaN, double.NaN, double.NaN,
            double.NaN, 0, -1,
            double.NaN, double.NaN, double.NaN,
            censored ? 1 : 0,
            "", 0,
            cand.SlPrice, cand.HoldBars,
            double.NaN, 0,
            cand.EntryPlusDi, cand.EntryMinusDi, cand.EntryAdx, cand.EntryAtr,
            cand.EntryHtfClose);
    }

    // ISignalModel surface: native-order feeds never route through OnBar.
    public SignalUpdate OnBar(TimeBar bar, string domain)
        => throw new InvalidOperationException(
            "MtfCtxReversion runs only in NativeOrders mode (engine fills); OnBar replay is invalid for limit strategies (EXP-013).");

    // ------------------------------------------------------------------ filters
    // Variant map (family spec): V00 baseline; V01 ADX<25; V02 ADX>=25; V03 DI
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

    // ------------------------------------------------------------------ emission
    public void Dispose()
    {
        if (_disposed)
            return;
        _disposed = true;
        if (_gridCloseTime.Count == 0)
            return;
        CensorOpenLegs();
        foreach (var cand in _candidates)
            WriteCandidate(cand);
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
            extreme_lookback = ExtremeLookback,
            sl_atr_multiple = SlAtrMultiple,
            profit_atr_multiple = ProfitAtrMultiple,
            vol_rank_window = VolRankWindow,
            execution = "native_limit_orders_m1_fills",
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
