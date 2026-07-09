using System;
using System.Collections.Generic;
using cAlgo.API;
using Xen.StrategyHost;

namespace cAlgo.Robots;

// =======================================================================
// EXP-020 (CF-VOLHARV-001 HYP-002) — structure-borne oscillation harvest,
// two arms (design §3), Mode=NativeOrders, 4h decision grid, m1 fills.
//
// ARM R  "rebalance_harvest": banded 50/50 constant-mix rebalance on a
//   virtual portfolio (real position + virtual cash leg). Trigger: weight
//   w(t−1 close) outside [0.5−b, 0.5+b] → market trade at open t back to
//   w*=0.5. Twin (ShTwin=true): identical init, NEVER rebalanced.
//   Estimand = per-bar path (PortWeight/PortUnits/PortCash emitted per bar
//   + every fill in trade_blotter); cis_trades intentionally EMPTY (the
//   rebalanced path is not a round-trip-leg object).
//
// ARM G  "grid_harvest": symmetric fixed grid, anchor A = previous
//   calendar-month close, levels A±k·g (k=1..4/side), 1 unit (min volume)
//   each, native pending orders. MR grid: buy LIMITs below / sell LIMITs
//   above; unwind = TP one level TOWARD A (buy at A−k·g → sell at
//   A−(k−1)·g; k=1 unwinds at A). Inverted twin (ShTwin=true): buy STOPs
//   above / sell STOPs below; unwind = TP one level AWAY from A (buy at
//   A+k·g → sell at A+(k+1)·g) — design §3 twin clarification 2026-07-05.
//   Monthly reset cancels ENTRY orders only; open inventory + its TPs are
//   carried, never force-closed. Cap 8 open legs: a level order is NOT
//   placed at cap (cap_skip logged, T3). Round trips → cis_trades rows;
//   fence-open legs → censored open_at_end rows.
//
// Tripwire 1 (both arms): ShDelayBars=1 delays every decision input by one
//   completed bar (identical code path at 0).
//
// DEVIATIONS: none in strategy semantics. Clarifications folded into the
//   design pre-implementation (dated, §3): grid unwind arithmetic (T2) and
//   inverted-twin unwind direction + stop-order entry (the only
//   non-degenerate mirror satisfying control B-6). Conf packaging follows
//   the EXP-019 D6 precedent: one multi-symbol conf per arm (6 confs = 68
//   cells) instead of 68 single-symbol confs — single family root per arm
//   for xen.estimand_validation.
// =======================================================================
public partial class Xen
{
    // ---------------- shared ----------------
    private const string RebStrategyName = "rebalance_harvest";
    private const string GridStrategyName = "grid_harvest";
    private const int GridLevelsPerSide = 4;      // design §3: k = 1..4
    private const int GridMaxOpenLegs = 8;        // design §3: hard cap

    private bool _rebReady;
    private bool _gridReady;
    private bool _shStopping;
    private Bars _shH4 = null!;
    private int _shIndex = -1;                     // last processed completed 4h bar
    private string _shLabel = "";
    private long _shTradeSeq;
    private List<SignalEventRecord> _shPeriodEvents = new();
    private List<StrategyTradeRecord> _shPeriodTrades = new();

    private void ShAssertDomainAndFence(string arm)
    {
        if (DomainMinutes != 240)
            throw new InvalidOperationException($"{arm} (EXP-020) is 4h-only; DomainMinutes must be 240, got {DomainMinutes}.");
        if (!TryParseAnalysisEndUtc(AnalysisEndUtc, out var analysisEndUtc))
            throw new InvalidOperationException("Analysis End UTC must be explicit, e.g. 2026-01-01T00:00:00Z.");
        if (ShDelayBars < 0 || ShDelayBars > 1)
            throw new InvalidOperationException($"SH Delay Bars must be 0 (live) or 1 (tripwire), got {ShDelayBars}.");
        _shH4 = MarketData.GetBars(TimeFrame.Hour4, SymbolName);
        _strategyFence = new HoldoutFence(analysisEndUtc);
    }

    private void ShEmitEvent(DateTime t, string strategy, string type, double value)
    {
        _shPeriodEvents.Add(new SignalEventRecord(t, "4h", strategy, type, 0, 0, value));
    }

    // ================= ARM R — rebalance_harvest =================
    private bool _rebInitialized;
    private bool _rebInitStaged;
    private double _rebUnits;                      // real asset units held
    private double _rebCash;                       // virtual cash leg (account ccy)
    private double _rebV0 = double.NaN;            // portfolio value at init fill
    private long _rebMinVolSkips;

    private void StartRebalanceHarvest()
    {
        ShAssertDomainAndFence("RebalanceHarvest");
        if (!(ShBandW > 0.0))
            throw new InvalidOperationException("SH Band W (weight-band b_w, A1 table) must be > 0 for ARM R.");
        _strategyWriter = new StrategyRunParquetWriter(
            StrategyOutputDirectory, RebStrategyName, SymbolName, "4h",
            _strategyFence!, BuildStrategyParameters(null));
        _shLabel = $"reb_{SanitizeLabel(SymbolName)}";
        _rebReady = true;
        Print("Xen EXP-020 ARM R for {0}: twin={1}; b_w={2}; delay={3}; AnalysisEndUtc={4:o}; out={5}",
            SymbolName, ShTwin, ShBandW, ShDelayBars, _strategyFence!.AnalysisEndUtc, _strategyWriter.RunDirectory);
    }

    private void RunRebalanceHarvestOnBar()
    {
        if (_shStopping)
            return;
        var latest = _shH4.Count - 2;
        for (var i = _shIndex + 1; i <= latest; i++)
            if (!ProcessRebBar(i, armOrders: i == latest))
                return;
    }

    // Sized so the smallest band-triggered trade (≈ 2·b_w·u0 units) is ≥ ~20 volume steps —
    // granularity error < ~5% of any rebalance trade. Virtual sizing scale cancels in the
    // per-bar log-return estimand.
    private double RebInitialUnits()
    {
        var step = Symbol.VolumeInUnitsStep > 0 ? Symbol.VolumeInUnitsStep : Symbol.VolumeInUnitsMin;
        var target = 10.0 * step / ShBandW;
        var vol = Symbol.NormalizeVolumeInUnits(target, RoundingMode.ToNearest);
        return Math.Max(vol, Symbol.VolumeInUnitsMin);
    }

    private bool ProcessRebBar(int i, bool armOrders)
    {
        var openTime = _shH4.OpenTimes[i];
        var closeTime = openTime.AddMinutes(240);
        if (_strategyFence!.ShouldStopBeforeProcessing(closeTime))
        {
            _shStopping = true;
            Stop();
            return false;
        }

        // Init: buy the asset half at the open of the first armable bar (both arm and twin).
        if (!_rebInitialized && !_rebInitStaged && armOrders)
        {
            _rebInitStaged = true;
            var res = ExecuteMarketOrder(TradeType.Buy, SymbolName, RebInitialUnits(), _shLabel, null, null, "init");
            if (res.IsSuccessful && res.Position != null)
            {
                _rebUnits = res.Position.VolumeInUnits;
                _rebCash = _rebUnits * res.Position.EntryPrice;   // cash leg == asset leg at init fill
                _rebV0 = 2.0 * _rebCash;
                _rebInitialized = true;
                RebBookTrade("buy", res.Position.EntryPrice, _rebUnits, "init");
            }
            else
                throw new InvalidOperationException($"ARM R init order failed: {res.Error}");
        }

        // Rebalance decision on the delayed confirmed close (tripwire 1: effIdx = i − delay).
        if (_rebInitialized && !ShTwin && armOrders)
        {
            var effIdx = i - ShDelayBars;
            var c = effIdx >= 0 ? _shH4.ClosePrices[effIdx] : double.NaN;
            if (c > 0.0)
            {
                var v = _rebUnits * c + _rebCash;
                var w = _rebUnits * c / v;
                if (Math.Abs(w - 0.5) >= ShBandW)
                {
                    var deltaUnits = 0.5 * v / c - _rebUnits;   // restore w*=0.5 at the decision close
                    var vol = Symbol.NormalizeVolumeInUnits(Math.Abs(deltaUnits), RoundingMode.ToNearest);
                    if (vol < Symbol.VolumeInUnitsMin)
                    {
                        _rebMinVolSkips++;
                        ShEmitEvent(closeTime, RebStrategyName, "min_vol_skip", deltaUnits);
                    }
                    else if (deltaUnits > 0)
                    {
                        var res = ExecuteMarketOrder(TradeType.Buy, SymbolName, vol, _shLabel, null, null, "rebalance");
                        if (res.IsSuccessful && res.Position != null)
                        {
                            _rebUnits += res.Position.VolumeInUnits;
                            _rebCash -= res.Position.VolumeInUnits * res.Position.EntryPrice;
                            RebBookTrade("buy", res.Position.EntryPrice, res.Position.VolumeInUnits, "rebalance");
                        }
                    }
                    else
                    {
                        // Sell = partial/full closes across ALL our real positions (buys open
                        // separate positions on a hedging account) until the target volume is
                        // exhausted; every actual fill is booked from History (QA run-1 M2).
                        var remaining = vol;
                        var open = new List<Position>();
                        foreach (var p in Positions)
                            if (p.Label == _shLabel)
                                open.Add(p);
                        foreach (var p in open)
                        {
                            if (remaining < Symbol.VolumeInUnitsMin)
                                break;
                            var closeVol = Math.Min(remaining, p.VolumeInUnits);
                            var res = ClosePosition(p, closeVol);
                            if (!res.IsSuccessful)
                                continue;
                            var fill = ClosingPriceOf(p.Id);
                            _rebUnits -= closeVol;
                            _rebCash += closeVol * fill;
                            RebBookTrade("sell", fill, -closeVol, "rebalance");
                            remaining -= closeVol;
                        }
                    }
                }
            }
        }

        EmitRebBar(i, closeTime);
        _shIndex = i;
        return true;
    }

    private void RebBookTrade(string action, double price, double deltaUnits, string reason)
    {
        _shPeriodTrades.Add(new StrategyTradeRecord(
            Server.Time, "4h", RebStrategyName, action, 0, 0, price, deltaUnits, ++_shTradeSeq));
        ShEmitEvent(Server.Time, RebStrategyName, reason, deltaUnits);
    }

    private void EmitRebBar(int i, DateTime closeTime)
    {
        var c = _shH4.ClosePrices[i];
        double w = double.NaN, mtm = double.NaN;
        if (_rebInitialized && c > 0.0)
        {
            var v = _rebUnits * c + _rebCash;
            w = _rebUnits * c / v;
            mtm = (v / _rebV0 - 1.0) * 1e4;   // portfolio bps vs init value
        }
        var rec = new SignalPositionRecord(
            SourceCloseTime: closeTime, Domain: "4h", Strategy: RebStrategyName,
            Position: _rebInitialized ? 1 : 0, SignalValue: w,
            RealOpen: _shH4.OpenPrices[i], RealHigh: _shH4.HighPrices[i],
            RealLow: _shH4.LowPrices[i], RealClose: c,
            Warmup: !_rebInitialized, IsFlat: !_rebInitialized,
            OpenLegs: _rebInitialized ? 1 : 0, MtmBps: mtm,
            PortWeight: w, PortUnits: _rebInitialized ? _rebUnits : double.NaN,
            PortCash: _rebInitialized ? _rebCash : double.NaN);
        _strategyWriter!.Append(new SignalUpdate(rec, _shPeriodEvents, _shPeriodTrades));
        _shPeriodEvents = new List<SignalEventRecord>();
        _shPeriodTrades = new List<StrategyTradeRecord>();
    }

    // ================= ARM G — grid_harvest =================
    private sealed class GridLeg
    {
        public long PositionId;
        public int Level;                          // k (1..4)
        public int Dir;                            // +1 long / −1 short
        public int GridId;                         // monthly grid sequence the leg belongs to
        public double EntryFill;
        public double UnwindPx;
        public DateTime EntryTime;
        public int EntryH4Index;
        public double MaeBps;
        public double MfeBps;
    }

    private sealed class GridClosed
    {
        public GridLeg Leg = null!;
        public double ExitFill;
        public string Reason = "";
        public DateTime ExitTime;
    }

    private double _gridAnchor = double.NaN;
    private double _gridPx;                        // g in price units (= A · g_bps / 1e4)
    private int _gridId;                           // increments at each monthly reset
    private int _gridResetAtIndex = -1;            // staged reset bar (delay tripwire)
    private int _gridBoundaryIdx = -1;             // last-of-month bar whose close is the anchor
    private readonly List<GridLeg> _gridLegs = new();
    private readonly List<GridClosed> _gridPeriodClosed = new();
    private readonly Dictionary<long, string> _gridPendingReason = new();
    private int _gridFiringIndex = -1;
    private long _gridCapSkips;
    private long _gridBreachSkips;
    private double _gridVolume;

    private void StartGridHarvest()
    {
        ShAssertDomainAndFence("GridHarvest");
        if (!(ShGridBps > 0.0))
            throw new InvalidOperationException("SH Grid Bps (spacing g, A1 table) must be > 0 for ARM G.");
        _strategyWriter = new StrategyRunParquetWriter(
            StrategyOutputDirectory, GridStrategyName, SymbolName, "4h",
            _strategyFence!, BuildStrategyParameters(null));
        _shLabel = $"grd_{SanitizeLabel(SymbolName)}";
        _gridVolume = Symbol.NormalizeVolumeInUnits(Symbol.VolumeInUnitsMin);
        Positions.Opened += OnGridPositionOpened;
        Positions.Closed += OnGridPositionClosed;
        _gridReady = true;
        Print("Xen EXP-020 ARM G for {0}: invert={1}; g_bps={2}; delay={3}; AnalysisEndUtc={4:o}; out={5}",
            SymbolName, ShTwin, ShGridBps, ShDelayBars, _strategyFence!.AnalysisEndUtc, _strategyWriter.RunDirectory);
    }

    private void RunGridHarvestOnBar()
    {
        if (_shStopping)
            return;
        var latest = _shH4.Count - 2;
        for (var i = _shIndex + 1; i <= latest; i++)
            if (!ProcessGridBar(i, armOrders: i == latest))
                return;
    }

    private bool ProcessGridBar(int i, bool armOrders)
    {
        var openTime = _shH4.OpenTimes[i];
        var closeTime = openTime.AddMinutes(240);
        if (_strategyFence!.ShouldStopBeforeProcessing(closeTime))
        {
            _shStopping = true;
            Stop();
            return false;
        }

        var close = _shH4.ClosePrices[i];
        if (close > 0.0)
            foreach (var leg in _gridLegs)
            {
                if (!(leg.EntryFill > 0.0))
                    continue;
                var bps = leg.Dir * (close - leg.EntryFill) / leg.EntryFill * 1e4;
                if (bps < leg.MaeBps) leg.MaeBps = bps;
                if (bps > leg.MfeBps) leg.MfeBps = bps;
            }

        // Month boundary: bar i is the last completed bar of its month iff the FORMING bar
        // (i+1) opens in a different calendar month. Anchor = close of bar i (previous-month
        // close). Reset executes ShDelayBars later (tripwire 1; 0 = at the month's first open).
        if (i + 1 < _shH4.Count)
        {
            var cur = _shH4.OpenTimes[i];
            var next = _shH4.OpenTimes[i + 1];
            if (cur.Year != next.Year || cur.Month != next.Month)
            {
                _gridBoundaryIdx = i;
                _gridResetAtIndex = i + ShDelayBars;
            }
        }
        if (armOrders && _gridResetAtIndex >= 0 && i >= _gridResetAtIndex && _gridBoundaryIdx >= 0)
        {
            _gridAnchor = _shH4.ClosePrices[_gridBoundaryIdx];
            _gridPx = _gridAnchor * ShGridBps / 1e4;
            _gridId++;
            _gridResetAtIndex = -1;
            CancelGridEntryOrders();               // entry orders only; open legs + TPs carried
            ShEmitEvent(closeTime, GridStrategyName, "grid_anchor_reset", _gridAnchor);
        }

        EmitGridBar(i, closeTime);

        // Re-arm sweep every armable bar: place any missing, valid, uncapped level order of the
        // CURRENT grid (a level re-arms after its round trip completes — cadence table, A1).
        if (armOrders && !double.IsNaN(_gridAnchor))
        {
            _gridFiringIndex = i;
            ArmGridLevels(i, closeTime);
        }

        _shIndex = i;
        return true;
    }

    // Level geometry per design §3 (+2026-07-05 twin clarification):
    //   MR    (ShTwin=false): buy LIMIT  at A−k·g, TP A−(k−1)·g;  sell LIMIT at A+k·g, TP A+(k−1)·g.
    //   invert (ShTwin=true): buy STOP   at A+k·g, TP A+(k+1)·g;  sell STOP  at A−k·g, TP A−(k+1)·g.
    private (double entry, double unwind, bool isStop) GridLevel(int k, int dir)
    {
        if (!ShTwin)
        {
            var entry = _gridAnchor - dir * k * _gridPx;
            var unwind = _gridAnchor - dir * (k - 1) * _gridPx;
            return (entry, unwind, false);
        }
        else
        {
            var entry = _gridAnchor + dir * k * _gridPx;
            var unwind = _gridAnchor + dir * (k + 1) * _gridPx;
            return (entry, unwind, true);
        }
    }

    private void ArmGridLevels(int i, DateTime closeTime)
    {
        var decIdx = i - ShDelayBars;
        if (decIdx < 0)
            return;
        var c = _shH4.ClosePrices[decIdx];
        foreach (var dir in new[] { 1, -1 })
            for (var k = 1; k <= GridLevelsPerSide; k++)
            {
                var slot = $"{_gridId};{k};{dir}";
                if (GridSlotOccupied(slot))
                    continue;
                if (_gridLegs.Count + GridPendingEntryCount() >= GridMaxOpenLegs)
                {
                    _gridCapSkips++;
                    ShEmitEvent(closeTime, GridStrategyName, "cap_skip", k * dir);
                    continue;
                }
                var (entry, unwind, isStop) = GridLevel(k, dir);
                var px = Math.Round(entry, Symbol.Digits);
                // Placement validity vs the ≤t−1 confirmed close: a limit must rest on the far
                // side of price; a stop on the trigger side. Invalid → skipped, disclosed.
                var valid = isStop
                    ? (dir > 0 ? px > c : px < c)
                    : (dir > 0 ? px < c : px > c);
                if (!valid)
                {
                    _gridBreachSkips++;
                    ShEmitEvent(closeTime, GridStrategyName, "arm_skip_breach", k * dir);
                    continue;
                }
                var comment = $"{slot};{Math.Round(unwind, Symbol.Digits)}";
                var side = dir > 0 ? TradeType.Buy : TradeType.Sell;
                if (isStop)
                    PlaceStopOrder(side, SymbolName, _gridVolume, px, _shLabel, null, null, null, comment);
                else
                    PlaceLimitOrder(side, SymbolName, _gridVolume, px, _shLabel, null, null, null, comment);
            }
    }

    private bool GridSlotOccupied(string slot)
    {
        foreach (var leg in _gridLegs)
            if ($"{leg.GridId};{leg.Level};{leg.Dir}" == slot)
                return true;
        foreach (var o in PendingOrders)
            if (o.Label == _shLabel && (o.Comment ?? "").StartsWith(slot + ";", StringComparison.Ordinal))
                return true;
        return false;
    }

    private int GridPendingEntryCount()
    {
        var n = 0;
        foreach (var o in PendingOrders)
            if (o.Label == _shLabel)
                n++;
        return n;
    }

    private void CancelGridEntryOrders()
    {
        var toCancel = new List<PendingOrder>();
        foreach (var o in PendingOrders)
            if (o.Label == _shLabel)
                toCancel.Add(o);
        foreach (var o in toCancel)
            CancelPendingOrder(o);
    }

    private void OnGridPositionOpened(PositionOpenedEventArgs args)
    {
        var pos = args.Position;
        if (pos.Label != _shLabel)
            return;
        var parts = (pos.Comment ?? "").Split(';');
        if (parts.Length < 4)
            throw new InvalidOperationException($"Grid fill without slot provenance (comment='{pos.Comment}').");
        var gid = int.Parse(parts[0]);
        var k = int.Parse(parts[1]);
        var dir = int.Parse(parts[2]);
        var unwind = double.Parse(parts[3], System.Globalization.CultureInfo.InvariantCulture);
        _gridLegs.Add(new GridLeg
        {
            PositionId = pos.Id, Level = k, Dir = dir, GridId = gid,
            EntryFill = pos.EntryPrice, UnwindPx = unwind,
            EntryTime = Server.Time, EntryH4Index = _gridFiringIndex
        });
        pos.ModifyTakeProfitPrice(unwind);         // the unwind order (native TP, m1-touch fill)
        _shPeriodTrades.Add(new StrategyTradeRecord(
            Server.Time, "4h", GridStrategyName, dir > 0 ? "buy" : "sell",
            0, dir, pos.EntryPrice, 1, ++_shTradeSeq));
        ShEmitEvent(Server.Time, GridStrategyName, "grid_level_fill", k * dir);
    }

    private void OnGridPositionClosed(PositionClosedEventArgs args)
    {
        var pos = args.Position;
        if (pos.Label != _shLabel)
            return;
        GridLeg? leg = null;
        foreach (var l in _gridLegs)
            if (l.PositionId == pos.Id) { leg = l; break; }
        var fill = ClosingPriceOf(pos.Id);
        var reason = _gridPendingReason.TryGetValue(pos.Id, out var r) ? r : "grid_unwind";
        _gridPendingReason.Remove(pos.Id);
        if (leg != null)
        {
            _gridPeriodClosed.Add(new GridClosed
            {
                Leg = leg, ExitFill = fill, Reason = reason, ExitTime = Server.Time
            });
            _gridLegs.Remove(leg);
        }
        _shPeriodTrades.Add(new StrategyTradeRecord(
            Server.Time, "4h", GridStrategyName, (leg?.Dir ?? 1) > 0 ? "sell" : "buy",
            leg?.Dir ?? 0, 0, fill, 1, ++_shTradeSeq));
        ShEmitEvent(Server.Time, GridStrategyName, reason, leg?.Level ?? 0);
    }

    private void EmitGridBar(int i, DateTime closeTime)
    {
        var closeI = _shH4.ClosePrices[i];
        double mtm = double.NaN;
        if (_gridLegs.Count > 0 && closeI > 0.0)
        {
            var acc = 0.0;
            foreach (var leg in _gridLegs)
                if (leg.EntryFill > 0.0)
                    acc += leg.Dir * (closeI - leg.EntryFill) / leg.EntryFill * 1e4;
            mtm = acc;
        }
        var net = 0;
        foreach (var leg in _gridLegs)
            net += leg.Dir;
        var rec = new SignalPositionRecord(
            SourceCloseTime: closeTime, Domain: "4h", Strategy: GridStrategyName,
            Position: Math.Sign(net), SignalValue: _gridAnchor,
            RealOpen: _shH4.OpenPrices[i], RealHigh: _shH4.HighPrices[i],
            RealLow: _shH4.LowPrices[i], RealClose: closeI,
            Warmup: double.IsNaN(_gridAnchor), IsFlat: _gridLegs.Count == 0,
            OpenLegs: _gridLegs.Count, MtmBps: mtm);
        _strategyWriter!.Append(new SignalUpdate(rec, _shPeriodEvents, _shPeriodTrades));
        _shPeriodEvents = new List<SignalEventRecord>();
        _shPeriodTrades = new List<StrategyTradeRecord>();

        foreach (var ct in _gridPeriodClosed)
            _strategyWriter!.AppendCisTrade(GridTradeRecord(ct.Leg, closeTime, ct.ExitTime,
                ct.ExitFill, ct.Reason, censored: 0, barsHeld: Math.Max(0, i - ct.Leg.EntryH4Index)));
        _gridPeriodClosed.Clear();
    }

    private CisTradeRecord GridTradeRecord(GridLeg leg, DateTime closeTime, DateTime exitTime,
        double exitFill, string reason, int censored, int barsHeld)
    {
        var bps = leg.EntryFill > 0.0 && censored == 0
            ? leg.Dir * (exitFill - leg.EntryFill) / leg.EntryFill * 1e4
            : double.NaN;
        return new CisTradeRecord(
            SourceCloseTime: closeTime, Domain: "4h", Strategy: GridStrategyName,
            Series: ShTwin ? "GRID_INVERTED" : "GRID_MR",
            EntryTime: leg.EntryTime, ExitTime: exitTime, Direction: leg.Dir, LadderLevel: leg.Level,
            EntryFillPrice: leg.EntryFill, ExitFillPrice: exitFill, ExitReason: reason,
            BarsHeld: barsHeld, RealizedBps: bps,
            EntryZ: double.NaN, EntrySpread: double.NaN, EntryAnchorPrice: _gridAnchor,
            EntrySigma: double.NaN, ExitAnchorPrice: double.NaN, ExitSpread: double.NaN,
            EntryTrendZ: double.NaN, EntryTrendDir: 0, EntryVolRegime: -1,
            FixedExitPrice: leg.UnwindPx, MaeBps: leg.MaeBps, MfeBps: leg.MfeBps, Censored: censored,
            SlPrice: double.NaN, HorizonBars: 0);
    }

    // Fence/stop: open grid inventory → censored open_at_end rows (disclosed, never dropped —
    // the VAL-006 e1-survivorship lesson; month-episode MTM is analysis-side from these rows).
    private void FlushGridCensored()
    {
        if (_strategyWriter == null || _shH4 == null)
            return;
        Print("EXP-020 ARM G fence flush for {0}: {1} censored open legs; cap_skips={2}; breach_skips={3}",
            SymbolName, _gridLegs.Count, _gridCapSkips, _gridBreachSkips);
        if (_gridLegs.Count == 0)
            return;
        var idx = _shIndex >= 0 && _shIndex < _shH4.Count ? _shIndex : _shH4.Count - 1;
        if (idx < 0)
            return;
        var mark = _shH4.ClosePrices[idx];
        var closeTime = _shH4.OpenTimes[idx].AddMinutes(240);
        foreach (var leg in _gridLegs)
            _strategyWriter.AppendCisTrade(GridTradeRecord(leg, closeTime, closeTime, mark,
                "open_at_end", censored: 1, barsHeld: Math.Max(0, _shIndex - leg.EntryH4Index)));
    }

    private void FlushRebalanceSummary()
    {
        if (_rebReady)
            Print("EXP-020 ARM R done for {0}: units={1}; cash={2}; min_vol_skips={3}",
                SymbolName, _rebUnits, _rebCash, _rebMinVolSkips);
    }
}
