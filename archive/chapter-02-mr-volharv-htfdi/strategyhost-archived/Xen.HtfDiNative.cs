using System;
using System.Collections.Generic;
using System.Linq;
using cAlgo.API;
using Xen.StrategyHost;

namespace cAlgo.Robots;

// =======================================================================
// EXP-025 (CF-HTFDI-001/HYP-A) — native-order arm for the capping exits:
//   E1 triple-barrier: TP 3.0x / SL 1.5x entry-frozen 1h ATR(14) + 96-bar
//      time backstop (market close);
//   E4 adverse-excursion stop only: SL 1.5x + 96-bar backstop, no TP.
// REAL cTrader stop/limit protections with m1 fill resolution — a
// StrategyHost model must never self-fill an intrabar barrier on
// aggregated-bar OHLC (L-14 / EXP-013 NativeOrders).
//
// SIGNAL PARITY: decisions replicate the StrategyHost arm exactly — the
// robot aggregates its own m1 feed into clock-aligned UTC 5min bars
// (BarAggregator, same StrictCoverage/MinCoverage params) and the same
// WilderHtfState 1h context, so T2's E1/E4 cells condition on the identical
// signal stream as T1 (never broker-server-aligned MarketData hour bars).
// Only execution differs: market entry at the next m1 tick after the signal
// close (≈ next 5min open), TP/SL owned by the engine.
//
// Gate is the di vehicle only (E1/E4 exist only in T2 on T1 survivors).
// =======================================================================
public partial class Xen
{
    private bool _hdReady;
    private bool _hdStopping;
    private bool _hdTakeProfit;                          // true = E1 (TP+SL), false = E4 (SL only)
    private const int HdBackstopBars = 96;               // design §3 E1/E4 time backstop (5min bars)
    private const double HdTpAtrMult = 3.0;
    private const double HdSlAtrMult = 1.5;

    // Boundary-triggered 5min bucketer (NOT BarAggregator): BarAggregator emits bucket t only
    // when the first m1 of bucket t+1 ARRIVES, which would lag every market action ~1 minute
    // past the 5min open. Here the bucket finalizes the instant its last m1 bar closes (m1
    // CloseTime on the 5min boundary), so ExecuteMarketOrder fires at the current tick = the
    // next 5min bar's open — the design's entry/exit fill point. StrictCoverage semantics match
    // the StrategyHost arm: an incomplete bucket (missing m1 minutes) is dropped.
    private readonly List<TimeBar> _hdBucket = new();
    private readonly WilderHtfState _hdHtf = new(60);
    private readonly Queue<double> _hdPriorHighs = new();
    private readonly Queue<double> _hdPriorLows = new();
    private string _hdLabel = "";
    private string _hdStrategyName = "";
    private double _hdVolume;
    private long _hdBarIndex = -1;
    private long _hdTradeSeq;
    private DateTime? _hdLastM1CloseTime;

    private sealed class HdLeg
    {
        public long PositionId;
        public int Dir;
        public double EntryFill;
        public long EntryBarIndex;
        public DateTime EntryTime;
        public HtfSnapshot Snapshot = null!;
        public double BreakoutRef;
        public double TpPrice = double.NaN;
        public double SlPrice = double.NaN;
        public double MaeBps;
        public double MfeBps;
    }

    private HdLeg? _hdLeg;                               // one position at a time (design §3)
    private string _hdPendingReason = "";
    private HtfSnapshot? _hdArmSnapshot;
    private double _hdArmBreakoutRef;
    private int _hdArmDir;
    private double _hdPendingEntryFill = double.NaN;
    private double _hdPendingExitFill = double.NaN;
    private List<SignalEventRecord> _hdPeriodEvents = new();
    private List<StrategyTradeRecord> _hdPeriodTrades = new();
    private readonly List<CisTradeRecord> _hdPeriodClosed = new();

    private void StartHtfDiNative()
    {
        if (DomainMinutes != 5)
            throw new InvalidOperationException(
                $"HtfDiBreakout native arm (EXP-025 E1/E4) is 1h/5min only; DomainMinutes must be 5, got {DomainMinutes}.");
        var exit = HtfExit.Trim().ToLowerInvariant();
        _hdTakeProfit = exit switch
        {
            "e1" => true,
            "e4" => false,
            _ => throw new InvalidOperationException(
                $"HTFDI Exit '{HtfExit}' does not run in Mode=NativeOrders (only e1|e4; others are StrategyHost).")
        };
        if (!string.Equals(HtfGate.Trim(), "di", StringComparison.OrdinalIgnoreCase))
            throw new InvalidOperationException("HtfDiBreakout native arm supports Gate=di only (T2 survivors).");
        if (!TryParseAnalysisEndUtc(AnalysisEndUtc, out var analysisEndUtc))
            throw new InvalidOperationException("Analysis End UTC must be explicit, e.g. 2026-01-01T00:00:00Z.");

        if (!StrictCoverage)
            throw new InvalidOperationException(
                "HtfDiBreakout native arm requires StrictCoverage=true (signal parity with the StrategyHost arm).");
        var minCoverage = (double?)null;
        _strategyFence = new HoldoutFence(analysisEndUtc);
        _hdStrategyName = $"htfdi_x{HtfX}_{exit}_di" + (HtfShiftBars > 0 ? $"_shift{HtfShiftBars}" : "");
        _strategyWriter = new StrategyRunParquetWriter(
            StrategyOutputDirectory, _hdStrategyName, SymbolName, "5m",
            _strategyFence, BuildStrategyParameters(minCoverage));
        _hdLabel = $"hd_{SanitizeLabel(SymbolName)}";
        _hdVolume = Symbol.NormalizeVolumeInUnits(Symbol.VolumeInUnitsMin);

        Positions.Opened += OnHdPositionOpened;
        Positions.Closed += OnHdPositionClosed;
        _hdReady = true;

        Print("Xen EXP-025 HtfDiNative for {0}: exit={1}; X={2}; shift={3}; AnalysisEndUtc={4:o}; out={5}",
            SymbolName, exit, HtfX, HtfShiftBars, _strategyFence.AnalysisEndUtc, _strategyWriter.RunDirectory);
    }

    private void RunHtfDiNativeOnBar()
    {
        if (_hdStopping)
            return;
        var index = Bars.Count - 2;                      // last completed m1 bar
        if (index < 0)
            return;
        var openTime = Bars.OpenTimes[index];
        var closeTime = openTime.AddMinutes(1);
        if (_hdLastM1CloseTime.HasValue && closeTime <= _hdLastM1CloseTime.Value)
            return;                                      // duplicate OnBar tick for the same bar
        _hdLastM1CloseTime = closeTime;

        if (_strategyFence!.ShouldStopBeforeProcessing(closeTime))
        {
            _hdStopping = true;          // partial trailing bucket is dropped (strict semantics)
            Stop();
            return;
        }

        var m1 = new TimeBar(SymbolName, openTime, closeTime,
            Bars.OpenPrices[index], Bars.HighPrices[index], Bars.LowPrices[index],
            Bars.ClosePrices[index], Convert.ToInt64(Bars.TickVolumes[index]));

        // stale bucket left open across a gap (its boundary m1 never arrived) → drop it
        if (_hdBucket.Count > 0 && BucketKeyOf(m1.CloseTime) != BucketKeyOf(_hdBucket[0].CloseTime))
            _hdBucket.Clear();
        _hdBucket.Add(m1);

        // finalize the instant the bucket's boundary minute closes (CloseTime on the 5min grid)
        var secs = (long)(DateTime.SpecifyKind(closeTime, DateTimeKind.Utc)
                          - new DateTime(1970, 1, 1, 0, 0, 0, DateTimeKind.Utc)).TotalSeconds;
        if (secs % (DomainMinutes * 60L) != 0)
            return;
        var complete = _hdBucket.Count == DomainMinutes;   // strict: drop incomplete buckets
        if (complete)
        {
            var first = _hdBucket[0];
            var domainBar = new TimeBar(SymbolName, first.OpenTime, closeTime,
                first.Open,
                _hdBucket.Max(b => b.High), _hdBucket.Min(b => b.Low),
                m1.Close, _hdBucket.Sum(b => b.TickVolume), _hdBucket.Count);
            _hdBucket.Clear();
            ProcessHdDomainBar(domainBar);
        }
        else
        {
            _hdBucket.Clear();
        }
    }

    private long BucketKeyOf(DateTime closeTime)
    {
        var secs = (long)(DateTime.SpecifyKind(closeTime, DateTimeKind.Utc)
                          - new DateTime(1970, 1, 1, 0, 0, 0, DateTimeKind.Utc)).TotalSeconds;
        return (secs - 1) / (DomainMinutes * 60L);
    }

    // One completed 5min bar: execute the staged entry (market, fills at the current m1 tick
    // ≈ this bar's successor open — the engine already staged it last bar), evaluate the
    // backstop, emit the per-bar record, then decide the next entry from this closed bar.
    private bool ProcessHdDomainBar(TimeBar bar)
    {
        if (_strategyFence!.ShouldStopBeforeProcessing(bar.CloseTime))
        {
            _hdStopping = true;
            Stop();
            return false;
        }
        _hdBarIndex++;

        // ---- fold this closed bar into decision state ----
        _hdHtf.Update(bar);
        var snapNow = _hdHtf.Snapshot(HtfShiftBars);

        if (_hdLeg is not null && _hdLeg.EntryFill > 0.0)
        {
            var bps = _hdLeg.Dir * (bar.Close - _hdLeg.EntryFill) / _hdLeg.EntryFill * 1e4;
            if (bps < _hdLeg.MaeBps) _hdLeg.MaeBps = bps;
            if (bps > _hdLeg.MfeBps) _hdLeg.MfeBps = bps;

            // 96-bar time backstop → market close at the next open (design §3 E1/E4)
            if (_hdBarIndex - _hdLeg.EntryBarIndex + 1 >= HdBackstopBars)
            {
                _hdPendingReason = "time_backstop";
                foreach (var p in Positions)
                    if (p.Label == _hdLabel && p.Id == _hdLeg.PositionId) { ClosePosition(p); break; }
            }
        }

        var channelReady = _hdPriorHighs.Count >= HtfX;
        double upper = double.NaN, lower = double.NaN;
        if (channelReady)
        {
            upper = double.NegativeInfinity; lower = double.PositiveInfinity;
            foreach (var h in _hdPriorHighs) upper = Math.Max(upper, h);
            foreach (var l in _hdPriorLows) lower = Math.Min(lower, l);
        }

        // ---- entry decision on this closed bar; the market order goes out NOW ----
        // We are at the first tick past bar.CloseTime, i.e. the next 5min bar's open — the
        // design's fill point. The engine (m1 backtester) owns the fill.
        var warmup = !channelReady || snapNow is null || double.IsNaN(snapNow.PlusDi) || double.IsNaN(snapNow.Atr);
        if (!warmup && _hdLeg is null && !_hdStopping)
        {
            var candidate = 0;
            double breakoutRef = double.NaN;
            if (bar.Close > upper) { candidate = 1; breakoutRef = upper; }
            else if (bar.Close < lower) { candidate = -1; breakoutRef = lower; }
            if (candidate != 0 && Math.Sign(snapNow!.PlusDi - snapNow.MinusDi) == candidate)
            {
                // LEAK GUARD (hard): the HTF bar conditioning this entry must be closed at or
                // before the signal bar's close (< the entry fill time, which is now, later).
                if (snapNow.CloseTime > bar.CloseTime)
                    throw new InvalidOperationException(
                        $"HTF leak guard (native): snapshot CloseTime {snapNow.CloseTime:o} > signal close {bar.CloseTime:o}");
                _hdArmDir = candidate;
                _hdArmBreakoutRef = breakoutRef;
                _hdArmSnapshot = snapNow;
                _hdPeriodEvents.Add(new SignalEventRecord(bar.CloseTime, "5m", _hdStrategyName,
                    "breakout_signal", candidate, 0,
                    candidate > 0 ? bar.Close - upper : bar.Close - lower));
                double? slPips = HdSlAtrMult * snapNow.Atr / Symbol.PipSize;
                double? tpPips = _hdTakeProfit ? HdTpAtrMult * snapNow.Atr / Symbol.PipSize : null;
                ExecuteMarketOrder(candidate > 0 ? TradeType.Buy : TradeType.Sell, SymbolName,
                    _hdVolume, _hdLabel, slPips, tpPips);
            }
        }

        _hdPriorHighs.Enqueue(bar.High);
        _hdPriorLows.Enqueue(bar.Low);
        if (_hdPriorHighs.Count > HtfX) { _hdPriorHighs.Dequeue(); _hdPriorLows.Dequeue(); }

        // ---- per-bar emission (same field mapping as the StrategyHost arm) ----
        var plusMinus = snapNow is not null ? snapNow.PlusDi - snapNow.MinusDi : double.NaN;
        var held = _hdLeg?.Dir ?? 0;
        _strategyWriter!.Append(new SignalUpdate(
            new SignalPositionRecord(
                bar.CloseTime, "5m", _hdStrategyName,
                held,
                snapNow?.Adx ?? double.NaN,
                bar.Open, bar.High, bar.Low, bar.Close,
                warmup, held == 0,
                EntryFillPrice: _hdPendingEntryFill,
                ExitFillPrice: _hdPendingExitFill,
                TrendZ: plusMinus,
                TrendDir: double.IsNaN(plusMinus) ? 0 : Math.Sign(plusMinus),
                VolRegime: snapNow?.AtrRegime ?? -1,
                OpenLegs: _hdLeg is null ? 0 : 1,
                MtmBps: _hdLeg is not null && _hdLeg.EntryFill > 0.0
                    ? _hdLeg.Dir * (bar.Close - _hdLeg.EntryFill) / _hdLeg.EntryFill * 1e4
                    : double.NaN),
            _hdPeriodEvents, _hdPeriodTrades));
        foreach (var row in _hdPeriodClosed)
            _strategyWriter.AppendCisTrade(row with { SourceCloseTime = bar.CloseTime });
        _hdPeriodClosed.Clear();
        _hdPeriodEvents = new List<SignalEventRecord>();
        _hdPeriodTrades = new List<StrategyTradeRecord>();
        _hdPendingEntryFill = double.NaN;
        _hdPendingExitFill = double.NaN;
        return true;
    }

    private void OnHdPositionOpened(PositionOpenedEventArgs args)
    {
        var pos = args.Position;
        if (pos.Label != _hdLabel)
            return;
        var dir = pos.TradeType == TradeType.Sell ? -1 : 1;
        _hdLeg = new HdLeg
        {
            PositionId = pos.Id,
            Dir = dir,
            EntryFill = pos.EntryPrice,
            EntryBarIndex = _hdBarIndex + 1,             // fill lands in the bar after the decision bar
            EntryTime = Server.Time,
            Snapshot = _hdArmSnapshot!,
            BreakoutRef = _hdArmBreakoutRef,
            TpPrice = pos.TakeProfit ?? double.NaN,
            SlPrice = pos.StopLoss ?? double.NaN
        };
        _hdPendingEntryFill = pos.EntryPrice;
        _hdPeriodTrades.Add(new StrategyTradeRecord(Server.Time, "5m", _hdStrategyName,
            dir > 0 ? "enter_long" : "enter_short", 0, dir, pos.EntryPrice, 1, ++_hdTradeSeq));
    }

    private void OnHdPositionClosed(PositionClosedEventArgs args)
    {
        var pos = args.Position;
        if (pos.Label != _hdLabel || _hdLeg is null || pos.Id != _hdLeg.PositionId)
            return;
        var leg = _hdLeg;
        _hdLeg = null;
        var fill = ClosingPriceOf(pos.Id);
        _hdPendingExitFill = fill;
        var reason = args.Reason switch
        {
            PositionCloseReason.StopLoss => "sl_barrier",
            PositionCloseReason.TakeProfit => "tp_barrier",
            _ => string.IsNullOrEmpty(_hdPendingReason) ? "unstaged_close" : _hdPendingReason
        };
        _hdPendingReason = "";
        var bps = leg.EntryFill > 0.0 ? leg.Dir * (fill - leg.EntryFill) / leg.EntryFill * 1e4 : double.NaN;
        _hdPeriodTrades.Add(new StrategyTradeRecord(Server.Time, "5m", _hdStrategyName,
            leg.Dir > 0 ? "exit_long" : "exit_short", leg.Dir, 0, fill, 1, ++_hdTradeSeq));
        _hdPeriodEvents.Add(new SignalEventRecord(Server.Time, "5m", _hdStrategyName, reason, 0, leg.Dir, bps));
        _hdPeriodClosed.Add(HdTradeRow(leg, Server.Time, fill, reason, bps, censored: 0,
            barsHeld: (int)Math.Max(0, _hdBarIndex - leg.EntryBarIndex + 1)));
    }

    private CisTradeRecord HdTradeRow(HdLeg leg, DateTime exitTime, double exitFill, string reason,
                                      double bps, int censored, int barsHeld)
    {
        return new CisTradeRecord(
            SourceCloseTime: exitTime, Domain: "5m", Strategy: _hdStrategyName,
            Series: HtfDiBreakoutModel.SeriesLabel,
            EntryTime: leg.EntryTime, ExitTime: exitTime, Direction: leg.Dir, LadderLevel: 0,
            EntryFillPrice: leg.EntryFill, ExitFillPrice: exitFill, ExitReason: reason,
            BarsHeld: barsHeld, RealizedBps: bps,
            EntryZ: double.NaN, EntrySpread: double.NaN, EntryAnchorPrice: double.NaN,
            EntrySigma: double.NaN, ExitAnchorPrice: double.NaN, ExitSpread: double.NaN,
            EntryTrendZ: leg.Snapshot.PlusDi - leg.Snapshot.MinusDi,
            EntryTrendDir: Math.Sign(leg.Snapshot.PlusDi - leg.Snapshot.MinusDi),
            EntryVolRegime: leg.Snapshot.AtrRegime,
            FixedExitPrice: leg.TpPrice, MaeBps: leg.MaeBps, MfeBps: leg.MfeBps, Censored: censored,
            SlPrice: leg.SlPrice, HorizonBars: HdBackstopBars,
            BreakoutRef: leg.BreakoutRef, SignalX: HtfX,
            HtfPlusDi: leg.Snapshot.PlusDi, HtfMinusDi: leg.Snapshot.MinusDi,
            HtfAdx: leg.Snapshot.Adx, HtfAtr: leg.Snapshot.Atr,
            HtfBarCloseTime: leg.Snapshot.CloseTime);
    }

    // Fence-open leg → censored open_at_end row (excluded from realized reads, disclosed).
    private void FlushHtfDiNativeCensored()
    {
        if (_strategyWriter is null || _hdLeg is null)
            return;
        var leg = _hdLeg;
        _hdLeg = null;
        _strategyWriter.AppendCisTrade(HdTradeRow(leg, leg.EntryTime, double.NaN, "open_at_end",
            double.NaN, censored: 1, barsHeld: (int)Math.Max(0, _hdBarIndex - leg.EntryBarIndex + 1)));
    }
}
