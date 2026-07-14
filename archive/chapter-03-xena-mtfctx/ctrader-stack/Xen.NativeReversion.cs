using System;
using System.Collections.Generic;
using cAlgo.API;
using Xen.StrategyHost;

namespace cAlgo.Robots;

// ===========================================================================
// XENA-003 NativeOrders mode — CTRL-03 NAIVE REVERSION execution partial.
//
// The EXP-013 carve-out, rebuilt for XENA-003 (the chapter-02 NativeOrders
// wiring was archived at rollover): limit strategies must be filled by the
// cTrader engine against m1 backtest data, never self-adjudicated on
// aggregated-bar OHLC. This partial owns ALL broker interaction; the
// MtfCtxReversionModel owns all signal/exit logic and emission. Interface:
// INativeQuoteExecutor (place/amend/cancel + market close), plus fill events
// routed back (Positions.Opened/Closed).
//
// One robot instance = one (symbol, LTF domain) feed hosting 76 candidates:
// <= 152 resting limit orders + <= 76 open positions concurrently, each at
// the symbol's minimum volume (candidates never size — XENA carve-out; the
// Python oracle does all sizing). Label = candidate id (order & position).
// ===========================================================================
public partial class Xen
{
    private MtfCtxReversionModel? _nativeModel;
    private BarAggregator? _nativeAggregator;
    private HoldoutFence? _nativeFence;
    private StrategyRunParquetWriter? _nativeWriter;
    private DateTime? _nativeLastCloseTime;
    private long _nativeSourceBars;
    private long _nativeDomainBars;
    private bool _nativeReady;
    private bool _nativeStopping;

    private sealed class NativeQuoteExecutor : INativeQuoteExecutor
    {
        private readonly Xen _robot;
        // (candidateId, side) -> resting order id
        private readonly Dictionary<(string, int), int> _orders = new();

        public NativeQuoteExecutor(Xen robot) => _robot = robot;

        public void SyncQuote(string candidateId, int side, double? limitPrice)
        {
            var key = (candidateId, side);
            var have = _orders.TryGetValue(key, out var orderId);
            PendingOrder? order = null;
            if (have)
            {
                foreach (var o in _robot.PendingOrders)
                    if (o.Id == orderId)
                    {
                        order = o;
                        break;
                    }
                if (order is null)
                    _orders.Remove(key); // filled or externally gone
            }

            if (!limitPrice.HasValue)
            {
                if (order is not null)
                {
                    order.Cancel();
                    _orders.Remove(key);
                }
                return;
            }

            var price = Math.Round(limitPrice.Value, _robot.Symbol.Digits);
            if (order is not null)
            {
                if (Math.Abs(order.TargetPrice - price) > _robot.Symbol.TickSize / 2)
                    order.ModifyTargetPrice(price);
                return;
            }

            var result = _robot.PlaceLimitOrder(
                side > 0 ? TradeType.Buy : TradeType.Sell,
                _robot.SymbolName,
                _robot.Symbol.VolumeInUnitsMin,
                price,
                candidateId);
            if (result.IsSuccessful && result.PendingOrder is not null)
                _orders[key] = result.PendingOrder.Id;
            // A rejected quote (e.g. crossed by the time the engine sees it) is
            // simply absent this bar — the passive-only rule re-quotes next bar.
        }

        public void CloseCandidate(string candidateId, string exitReason)
        {
            foreach (var p in _robot.Positions)
                if (p.Label == candidateId && p.SymbolName == _robot.SymbolName)
                {
                    _robot.ClosePosition(p);
                    return;
                }
        }

        public void CancelSide(string candidateId, int side)
        {
            var key = (candidateId, side);
            if (!_orders.TryGetValue(key, out var orderId))
                return;
            foreach (var o in _robot.PendingOrders)
                if (o.Id == orderId)
                {
                    o.Cancel();
                    break;
                }
            _orders.Remove(key);
        }

        public void Forget(string candidateId, int side) => _orders.Remove((candidateId, side));

        public void CancelAll()
        {
            foreach (var o in _robot.PendingOrders)
                if (o.SymbolName == _robot.SymbolName)
                    o.Cancel();
            _orders.Clear();
        }
    }

    private NativeQuoteExecutor? _nativeExecutor;

    private bool IsNativeOrdersMode() => Mode == XenMode.NativeOrders;

    private void StartNativeOrders()
    {
        if (Strategy != XenStrategy.MtfCtxReversion)
            throw new InvalidOperationException(
                "NativeOrders mode currently hosts MtfCtxReversion (XENA-003) only.");
        if (!TryParseAnalysisEndUtc(AnalysisEndUtc, out var analysisEndUtc))
            throw new InvalidOperationException("Analysis End UTC must be explicit, e.g. 2026-01-01T00:00:00Z.");

        var domain = DomainLabel(DomainMinutes);
        _nativeFence = new HoldoutFence(analysisEndUtc);
        _nativeAggregator = new BarAggregator(DomainMinutes, StrictCoverage ? (double?)null : MinCoverage);
        _nativeModel = new MtfCtxReversionModel(
            SymbolName, DomainMinutes, StrategyOutputDirectory, _nativeFence.AnalysisEndUtc);
        _nativeExecutor = new NativeQuoteExecutor(this);
        _nativeModel.AttachExecutor(_nativeExecutor);
        _nativeWriter = new StrategyRunParquetWriter(
            StrategyOutputDirectory,
            _nativeModel.StrategyName,
            SymbolName,
            domain,
            _nativeFence,
            new Dictionary<string, object?>
            {
                ["strategy"] = Strategy.ToString(),
                ["mode"] = "NativeOrders",
                ["run"] = "XENA-003",
                ["domain_minutes"] = DomainMinutes,
                ["extreme_lookback"] = 3,
                ["candidates_per_feed"] = 76
            });

        Positions.Opened += OnNativePositionOpened;
        Positions.Closed += OnNativePositionClosed;
        _nativeReady = true;

        Print("Xen NativeOrders host started for {0} {1}; AnalysisEndUtc={2:o}; output={3}",
            SymbolName, domain, _nativeFence.AnalysisEndUtc, _nativeWriter.RunDirectory);
    }

    private void OnNativeBar()
    {
        if (!_nativeReady || _nativeStopping)
            return;
        if (_nativeAggregator is null || _nativeFence is null || _nativeModel is null
            || _nativeWriter is null || _nativeExecutor is null)
            throw new InvalidOperationException("Xen NativeOrders host was not initialised.");

        var index = Bars.Count - 2;
        if (index < 0)
            return;

        var openTime = Bars.OpenTimes[index];
        var closeTime = openTime.AddMinutes(1);
        if (_nativeLastCloseTime.HasValue && closeTime <= _nativeLastCloseTime.Value)
            throw new InvalidOperationException("Bar CloseTime is not strictly increasing.");
        _nativeLastCloseTime = closeTime;

        if (_nativeFence.ShouldStopBeforeProcessing(closeTime))
        {
            FinalizeNativeRun();
            Stop();
            return;
        }

        var bar = new TimeBar(
            SymbolName, openTime, closeTime,
            Bars.OpenPrices[index], Bars.HighPrices[index],
            Bars.LowPrices[index], Bars.ClosePrices[index],
            Convert.ToInt64(Bars.TickVolumes[index]));
        if (bar.High < Math.Max(bar.Open, bar.Close) || bar.Low > Math.Min(bar.Open, bar.Close))
            throw new InvalidOperationException("Bar OHLC integrity check failed.");

        _nativeSourceBars++;
        var domain = DomainLabel(DomainMinutes);
        foreach (var ltfBar in _nativeAggregator.Update(bar))
        {
            if (_nativeFence.ShouldStopBeforeProcessing(ltfBar.CloseTime))
            {
                FinalizeNativeRun();
                Stop();
                return;
            }
            var update = _nativeModel.OnLtfBarCompleted(ltfBar, domain, Symbol.Bid, Symbol.Ask);
            _nativeWriter.Append(update);
            _nativeDomainBars++;
        }
    }

    private void OnNativePositionOpened(PositionOpenedEventArgs args)
    {
        if (_nativeStopping || _nativeModel is null || _nativeExecutor is null)
            return;
        var pos = args.Position;
        if (pos.SymbolName != SymbolName || string.IsNullOrEmpty(pos.Label)
            || !pos.Label.StartsWith("C3-", StringComparison.Ordinal))
            return;
        var side = pos.TradeType == TradeType.Buy ? +1 : -1;
        _nativeExecutor.Forget(pos.Label, side);          // this order just filled
        _nativeExecutor.CancelSide(pos.Label, -side);     // one position at a time
        _nativeModel.OnEntryFilled(pos.Label, pos.EntryTime, pos.EntryPrice, side);
    }

    private void OnNativePositionClosed(PositionClosedEventArgs args)
    {
        if (_nativeStopping || _nativeModel is null)
            return;
        var pos = args.Position;
        if (pos.SymbolName != SymbolName || string.IsNullOrEmpty(pos.Label)
            || !pos.Label.StartsWith("C3-", StringComparison.Ordinal))
            return;

        // Engine-realized closing price from the deal history (synchronous in backtest).
        var closingPrice = double.NaN;
        for (var i = History.Count - 1; i >= 0; i--)
        {
            if (History[i].PositionId == pos.Id)
            {
                closingPrice = History[i].ClosingPrice;
                break;
            }
        }
        if (double.IsNaN(closingPrice))
            closingPrice = pos.CurrentPrice;
        _nativeModel.OnExitFilled(pos.Label, Server.Time, closingPrice);
    }

    private void FinalizeNativeRun()
    {
        if (_nativeStopping)
            return;
        _nativeStopping = true; // suppress event booking during the flatten

        // Book censored legs FIRST (family convention: last mark = final emitted
        // bar's open; NaN P&L), then flatten the engine account for cleanliness.
        _nativeModel?.CensorOpenLegs();
        _nativeExecutor?.CancelAll();
        foreach (var p in Positions)
            if (p.SymbolName == SymbolName && !string.IsNullOrEmpty(p.Label)
                && p.Label.StartsWith("C3-", StringComparison.Ordinal))
                ClosePosition(p);

        // Candidate dirs before the feed-level writer (harness run_complete gate
        // keys on the feed writer's artifacts — XENA-001 truncation lesson).
        _nativeModel?.Dispose();
        _nativeWriter?.Dispose();
        Print("Xen NativeOrders host stopped for {0}. Source bars={1}, domain bars={2}.",
            SymbolName, _nativeSourceBars, _nativeDomainBars);
    }
}
