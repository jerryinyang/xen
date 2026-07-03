using System;
using System.Collections.Generic;
using System.Linq;
using cAlgo.API;
using cAlgo.API.Internals;
using Xen.StrategyHost;

namespace cAlgo.Robots;

// ===========================================================================
// CF-MR-004 (EXP-014b / HYP-003) — BOTH-LEG grouped-spread native execution
// (amendment-003 A4/A10; Increment B). Self-contained: the single-leg netting
// engine in Xen.cs is untouched. On an S8 spread extreme the robot opens ONE
// joint spread position over N+1 real cTrader legs — the traded instrument A
// plus each equal-weight basket mate — so reversion is captured whichever side
// moves (audit M1 structural fix). Held as a unit, exited jointly on form-1
// (spread reverts through the mean). reentry is forced none (≤1 open group).
//
// Entry sub-axes (CisBothLegEntry):
//   "market" — the ≤t-1 confirmed-close spread breaches ±z*·σ → market-fill all
//              N+1 legs at the next domain-bar open (clean group, no desync).
//   "limit"  — ATOMIC: A rests band-limits at exp(anchorLog±z*·σ); on the A fill
//              (which fixes the spread side) each mate rests a limit at its ≤t-1
//              close on the correct side; if the full N+1 group is not filled by
//              the next domain bar, market-unwind any filled legs (flat) and
//              cancel remaining pendings — only a full-group fill survives.
//
// SpreadDir: +1 = LONG spread  (A cheap → long A, short mates); the fade of a
//            below-mean dislocation. −1 = SHORT spread (A rich → short A, long
//            mates). A-leg dir = SpreadDir; each mate-leg dir = −SpreadDir.
//
// Cost/analysis: this block emits ONE cis_trades row per leg (shared
// SpreadPositionId + LegSymbol + per-leg engine-realized fills → gross bps). The
// Python referee sums the frozen per-instrument per-domain cost over all N+1
// legs (L-02) and re-weights the joint-spread return (A weight 1, each mate 1/n).
// Per-bar MtmBps is emitted already spread-weighted (A + mean(mate)).
//
// CAUSAL CONTRACT: every decision reads only ≤ t-1 completed bars (the same
// bracket the single-leg path Observes); orders fill at the next domain-bar open
// (engine m1); the forming bar's own OHLC is never read; every emitted
// SourceCloseTime passes the same HoldoutFence gate as the single-leg path.
// ===========================================================================
public partial class Xen
{
    private const string GroupArming = "arming";
    private const string GroupHeld = "held";
    private const string GroupClosing = "closing";

    private bool _bothLeg;
    private string _bothLegEntry = "market";       // market | limit (A10)
    private string _bothLegLabel = "";
    private double _blZStar = 2.0;                  // both-leg base band multiple (no reentry ladder)
    private int _blExpectedLegs;                    // 1 (A) + resolved mate count
    private long _spreadGroupSeq;
    private readonly List<string> _blMateNames = new();
    private readonly List<Bars> _blMateBars = new();
    private readonly Dictionary<string, Bars> _blMateBarsBySymbol = new();
    private BothLegGroup? _group;                   // the single arming/held/closing group (reentry none)
    private readonly List<BothLegGroup> _blStagedClosed = new();  // fully-closed groups awaiting fence-consistent emit

    private sealed class BothLegLeg
    {
        public long PositionId;
        public string Symbol = "";
        public int Dir;                             // +1 long / −1 short (this leg)
        public double EntryFill;
        public double Volume;
        public DateTime EntryTime;
        public double ExitFill = double.NaN;
        public DateTime ExitTime;
        public bool IsAnchor;                       // the traded instrument A
    }

    private sealed class BothLegGroup
    {
        public long GroupId;
        public int SpreadDir;                       // +1 long-spread / −1 short-spread (0 until a limit A fills)
        public int ExpectedLegs;
        public int EntryBarIndex;
        public int ExitBarIndex;
        public DateTime EntryTime;
        public DateTime ArmBarOpenTime;             // OpenTime of the ≤t-1 arm bar (mate ≤t-1-close alignment)
        public double ArmAnchorClosePrice;          // exp(logClose) at the arm bar (mate volume sizing)
        public string State = GroupArming;
        public string EntryMode = "market";
        public string CloseReason = "";
        public double EntryZ, EntrySpread, EntryAnchorPrice, EntrySigma;
        public double EntryTrendZ;
        public int EntryTrendDir;
        public int EntryVolRegime;
        public readonly List<BothLegLeg> Legs = new();
        public readonly HashSet<long> ClosingIds = new();
    }

    // --- Init (from StartNativeOrders) -----------------------------------------------------
    private void InitBothLeg(IReadOnlyList<string> mates, TimeFrame timeFrame)
    {
        _bothLegEntry = (CisBothLegEntry ?? "market").Trim().ToLowerInvariant();
        if (_bothLegEntry != "market" && _bothLegEntry != "limit")
            throw new InvalidOperationException(
                $"CIS Both Leg Entry must be market|limit, got '{CisBothLegEntry}'.");
        _bothLegLabel = $"cisbl_{SanitizeLabel(SymbolName)}_{CisSeries}";
        _blZStar = CisZStar > 0.0 ? CisZStar : CrossInstrumentSpreadPlanner.ZStar;
        foreach (var mate in mates)
        {
            Bars? bars = null;
            try
            {
                if (Symbols.GetSymbol(mate) != null)
                    bars = MarketData.GetBars(timeFrame, mate);
            }
            catch (Exception ex)
            {
                Print("CF-MR-004 both-leg: mate '{0}' unresolved ({1}) — skipped.", mate, ex.Message);
                bars = null;
            }
            if (bars != null)
            {
                _blMateNames.Add(mate);
                _blMateBars.Add(bars);
                _blMateBarsBySymbol[mate] = bars;
            }
        }
        _blExpectedLegs = 1 + _blMateNames.Count;
        Print("Xen CF-MR-004 BOTH-LEG {0} for {1}: entry={2}; legs=1+{3}; z*={4}; label={5}",
            CisSeries, SymbolName, _bothLegEntry, _blMateNames.Count, _blZStar, _bothLegLabel);
    }

    // --- Per-bar driver (from ProcessCompletedH4Bar) ---------------------------------------
    private void ProcessBothLegBar(int i, bool armOrders, double logClose, double close,
                                   int mateCount, bool mateGap, DateTime closeTime)
    {
        // Joint form-1 exit on the held group: sc = logClose − anchorLog = spread − mean. A short
        // spread reverts when sc ≤ 0, a long spread when sc ≥ 0 → close ALL legs at the next open.
        var form1 = false;
        if (armOrders && _group != null && _group.State == GroupHeld
            && double.IsFinite(_lastBracket.AnchorLog) && double.IsFinite(logClose))
        {
            var sc = logClose - _lastBracket.AnchorLog;
            var reverted = (_group.SpreadDir < 0 && sc <= 0.0) || (_group.SpreadDir > 0 && sc >= 0.0);
            if (reverted)
            {
                form1 = true;
                CloseBothLegGroup(i, "form1_reversion");
            }
        }

        // Atomic partial unwind (limit sub-axis): an arming group not completed by its next bar.
        if (_group != null && _group.State == GroupArming && i > _group.EntryBarIndex)
            UnwindArmingGroup(i);

        EmitBothLegBar(i, closeTime, mateCount, mateGap, form1);

        // Arm a new group only when flat (reentry none) and the ≤t-1 inputs are valid.
        if (armOrders && _group == null && !_lastBracket.Warmup && !mateGap
            && _lastBracket.Sigma > 0.0 && double.IsFinite(_lastBracket.AnchorLog) && double.IsFinite(logClose))
        {
            if (_bothLegEntry == "market")
                TryOpenMarketGroup(i, logClose);
            else
                TryArmLimitGroup(i, logClose);
        }
    }

    // --- Entry: market sub-axis ------------------------------------------------------------
    private void TryOpenMarketGroup(int i, double logClose)
    {
        var band = _blZStar * _lastBracket.Sigma;
        var sc = logClose - _lastBracket.AnchorLog;   // spread − mean (≤ t-1)
        int spreadDir;
        if (sc >= band) spreadDir = -1;               // spread rich → short A + long mates
        else if (sc <= -band) spreadDir = 1;          // spread cheap → long A + short mates
        else return;                                  // no ≤t-1 breach → no entry

        // Pre-size every leg; SKIP the whole group if any leg cannot meet its symbol min-volume
        // (never place a partial-by-sizing group — directive/A4).
        var aPrice = Math.Exp(logClose);
        var mateVols = new double[_blMateNames.Count];
        for (var m = 0; m < _blMateNames.Count; m++)
        {
            var v = ComputeMateVolume(Symbols.GetSymbol(_blMateNames[m]), aPrice);
            if (!(v > 0.0))
            {
                Print("both-leg market group skipped ({0}): mate '{1}' below min-volume at sizing.",
                    SymbolName, _blMateNames[m]);
                return;
            }
            mateVols[m] = v;
        }

        var group = NewGroup(i, spreadDir, "market", logClose);
        _group = group;
        var comment = group.GroupId.ToString();
        ExecuteMarketOrder(spreadDir > 0 ? TradeType.Buy : TradeType.Sell, SymbolName, _orderVolume,
            _bothLegLabel, null, null, comment);
        var mateDir = -spreadDir;
        for (var m = 0; m < _blMateNames.Count; m++)
            ExecuteMarketOrder(mateDir > 0 ? TradeType.Buy : TradeType.Sell, _blMateNames[m], mateVols[m],
                _bothLegLabel, null, null, comment);
        // Backtest fills are synchronous → OnBothLegOpened moves the group to Held once all N+1 in.
    }

    // --- Entry: limit sub-axis (atomic) ----------------------------------------------------
    private void TryArmLimitGroup(int i, double logClose)
    {
        var band = _blZStar * _lastBracket.Sigma;
        var closeI = Math.Exp(logClose);
        var sell = RoundPrice(Math.Exp(_lastBracket.AnchorLog + band));
        var buy = RoundPrice(Math.Exp(_lastBracket.AnchorLog - band));

        var group = NewGroup(i, 0, "limit", logClose);   // SpreadDir unknown until the A band fills
        var comment = group.GroupId.ToString();
        var placed = false;
        if (sell > closeI && sell > Symbol.Bid)          // not through ≤t-1 close nor the live market
        {
            PlaceLimitOrder(TradeType.Sell, SymbolName, _orderVolume, sell, _bothLegLabel, null, null, null, comment);
            placed = true;
        }
        if (buy < closeI && buy < Symbol.Ask)
        {
            PlaceLimitOrder(TradeType.Buy, SymbolName, _orderVolume, buy, _bothLegLabel, null, null, null, comment);
            placed = true;
        }
        if (placed)
            _group = group;                              // else nothing armed this bar (group discarded)
    }

    // On the A-band fill, rest each mate limit at its ≤t-1 close on the −SpreadDir side.
    private void PlaceLimitMates(BothLegGroup group)
    {
        var mateDir = -group.SpreadDir;
        for (var m = 0; m < _blMateNames.Count; m++)
        {
            var name = _blMateNames[m];
            var msym = Symbols.GetSymbol(name);
            var px = MateCloseAt(_blMateBars[m], group.ArmBarOpenTime);   // mate ≤ t-1 close
            if (!(px > 0.0))
                px = mateDir > 0 ? msym.Ask : msym.Bid;                  // fallback: live market
            var vol = ComputeMateVolume(msym, group.ArmAnchorClosePrice);
            if (!(vol > 0.0))
                continue;   // unsizable mate never fills → the atomic unwind aborts the group next bar
            PlaceLimitOrder(mateDir > 0 ? TradeType.Buy : TradeType.Sell, name, vol,
                Math.Round(px, msym.Digits), _bothLegLabel, null, null, null, group.GroupId.ToString());
        }
    }

    // --- Fill / close events (routed from OnNativePositionOpened/Closed) --------------------
    private void OnBothLegOpened(Position pos)
    {
        if (_group == null || pos.Comment != _group.GroupId.ToString())
            return;
        var isAnchor = pos.SymbolName == SymbolName;
        var dir = pos.TradeType == TradeType.Buy ? 1 : -1;
        if (_group.EntryMode == "limit" && isAnchor && _group.SpreadDir == 0)
        {
            _group.SpreadDir = dir;                                  // A fill fixes the spread side
            CancelBothLegAnchorSide(pos.TradeType == TradeType.Buy ? TradeType.Sell : TradeType.Buy);
            PlaceLimitMates(_group);
        }
        _group.Legs.Add(new BothLegLeg
        {
            PositionId = pos.Id, Symbol = pos.SymbolName, Dir = dir, EntryFill = pos.EntryPrice,
            Volume = pos.VolumeInUnits, EntryTime = Server.Time, IsAnchor = isAnchor
        });
        if (_group.Legs.Count >= _group.ExpectedLegs)
            _group.State = GroupHeld;
    }

    private void OnBothLegClosed(Position pos)
    {
        if (_group == null)
            return;
        var leg = _group.Legs.FirstOrDefault(l => l.PositionId == pos.Id);
        if (leg == null)
            return;
        leg.ExitFill = ClosingPriceOf(pos.Id);
        leg.ExitTime = Server.Time;
        _group.ClosingIds.Remove(pos.Id);
        if (_group.State == GroupClosing && _group.ClosingIds.Count == 0)
        {
            _blStagedClosed.Add(_group);   // flushed to cis_trades at the next EmitBothLegBar (fence-consistent)
            _group = null;
        }
    }

    // Close a held group jointly (form-1) — market-close every leg at the next domain-bar open.
    private void CloseBothLegGroup(int i, string reason)
    {
        if (_group == null)
            return;
        _group.State = GroupClosing;
        _group.CloseReason = reason;
        _group.ExitBarIndex = i;
        _group.ClosingIds.Clear();
        foreach (var leg in _group.Legs)
            _group.ClosingIds.Add(leg.PositionId);
        foreach (var id in _group.Legs.Select(l => l.PositionId).ToList())
            CloseBothLegPosition(id);
    }

    // Atomic partial unwind — cancel remaining pendings and market-close any legs that filled.
    private void UnwindArmingGroup(int i)
    {
        CancelBothLegPendings();
        if (_group == null)
            return;
        if (_group.Legs.Count == 0)
        {
            _group = null;                 // nothing filled → drop the armed group
            return;
        }
        _group.State = GroupClosing;
        _group.CloseReason = "partial_abort";
        _group.ExitBarIndex = i;
        _group.ClosingIds.Clear();
        foreach (var leg in _group.Legs)
            _group.ClosingIds.Add(leg.PositionId);
        foreach (var id in _group.Legs.Select(l => l.PositionId).ToList())
            CloseBothLegPosition(id);
    }

    private void CloseBothLegPosition(long id)
    {
        foreach (var p in Positions)
            if (p.Label == _bothLegLabel && p.Id == id)
            {
                ClosePosition(p);
                break;
            }
    }

    private void CancelBothLegAnchorSide(TradeType oppType)
    {
        var toCancel = new List<PendingOrder>();
        foreach (var o in PendingOrders)
            if (o.Label == _bothLegLabel && o.SymbolName == SymbolName && o.TradeType == oppType)
                toCancel.Add(o);
        foreach (var o in toCancel)
            CancelPendingOrder(o);
    }

    private void CancelBothLegPendings()
    {
        var toCancel = new List<PendingOrder>();
        foreach (var o in PendingOrders)
            if (o.Label == _bothLegLabel)
                toCancel.Add(o);
        foreach (var o in toCancel)
            CancelPendingOrder(o);
    }

    // --- Emission --------------------------------------------------------------------------
    private void EmitBothLegBar(int i, DateTime closeTime, int mateCount, bool mateGap, bool form1)
    {
        var b = _lastBracket;
        var held = _group != null && _group.State == GroupHeld;
        var heldPosition = held ? _group!.SpreadDir : 0;
        var closeI = _h4.ClosePrices[i];

        double armSell = double.NaN, armBuy = double.NaN;
        bool breachSell = false, breachBuy = false, liveBreachSell = false, liveBreachBuy = false;
        if (!b.Warmup && double.IsFinite(b.AnchorLog) && b.Sigma > 0.0)
        {
            var band = _blZStar * b.Sigma;
            armSell = Math.Exp(b.AnchorLog + band);
            armBuy = Math.Exp(b.AnchorLog - band);
            breachSell = armSell <= closeI;
            breachBuy = armBuy >= closeI;
            liveBreachSell = armSell <= Symbol.Bid;
            liveBreachBuy = armBuy >= Symbol.Ask;
        }

        // Spread-weighted intra-position MTM (L-09): A weight 1 + equal-weight mate mean (= Σ 1/n · mate).
        var mtm = double.NaN;
        if (held)
        {
            var acc = 0.0;
            var anchorLeg = _group!.Legs.FirstOrDefault(l => l.IsAnchor);
            if (anchorLeg != null && anchorLeg.EntryFill > 0.0)
                acc += anchorLeg.Dir * (closeI - anchorLeg.EntryFill) / anchorLeg.EntryFill * 1e4;
            var mSum = 0.0; var mN = 0;
            var openTime = _h4.OpenTimes[i];
            foreach (var leg in _group.Legs)
            {
                if (leg.IsAnchor || !(leg.EntryFill > 0.0))
                    continue;
                var mp = _blMateBarsBySymbol.TryGetValue(leg.Symbol, out var bars)
                    ? MateCloseAt(bars, openTime) : double.NaN;
                if (double.IsFinite(mp))
                {
                    mSum += leg.Dir * (mp - leg.EntryFill) / leg.EntryFill * 1e4;
                    mN++;
                }
            }
            if (mN > 0) acc += mSum / mN;
            mtm = acc;
        }

        var rec = new SignalPositionRecord(
            SourceCloseTime: closeTime, Domain: _nativeDomain, Strategy: NativeStrategyName,
            Position: heldPosition, SignalValue: b.Z,
            RealOpen: _h4.OpenPrices[i], RealHigh: _h4.HighPrices[i],
            RealLow: _h4.LowPrices[i], RealClose: closeI,
            Warmup: b.Warmup, IsFlat: heldPosition == 0,
            ExitFillPrice: double.NaN, EntryFillPrice: double.NaN,   // per-leg fills live in cis_trades (both-leg)
            Anchor: b.Warmup ? double.NaN : Math.Exp(b.AnchorLog),
            Dev: b.Spread, Z: b.Z, Vr: b.Vr, Hl: b.Hl, Beta: b.Beta,
            ArmSellPrice: armSell, ArmBuyPrice: armBuy, Sigma: b.Sigma, SpreadMean: b.Mean,
            MateCount: mateCount, MateExpected: _cisFeed.ExpectedMates, MateGap: mateGap,
            TrendZ: _trendZ, TrendDir: _trendDir, VolRegime: _volRegime,
            BreachSkipSell: breachSell, BreachSkipBuy: breachBuy,
            LiveBreachSkipSell: liveBreachSell, LiveBreachSkipBuy: liveBreachBuy,
            OpenLegs: held ? _group!.Legs.Count : 0, MtmBps: mtm, RefreshedTp: double.NaN, Form1Any: form1);
        _strategyWriter!.Append(new SignalUpdate(rec, _periodEvents, _periodTrades));
        _periodEvents = new List<SignalEventRecord>();
        _periodTrades = new List<StrategyTradeRecord>();

        // Flush groups closed within the period ending at closeTime (fence-consistent).
        var anchorPx = b.Warmup ? double.NaN : Math.Exp(b.AnchorLog);
        foreach (var grp in _blStagedClosed)
            EmitClosedGroupRows(grp, closeTime, anchorPx, b.Spread, censored: 0);
        _blStagedClosed.Clear();
    }

    private void EmitClosedGroupRows(BothLegGroup grp, DateTime closeTime, double exitAnchor,
                                     double exitSpread, int censored)
    {
        var barsHeld = Math.Max(0, grp.ExitBarIndex - grp.EntryBarIndex);
        foreach (var leg in grp.Legs)
        {
            var bps = censored == 0 && leg.EntryFill > 0.0 && double.IsFinite(leg.ExitFill)
                ? leg.Dir * (leg.ExitFill - leg.EntryFill) / leg.EntryFill * 1e4
                : double.NaN;
            _strategyWriter!.AppendCisTrade(new CisTradeRecord(
                SourceCloseTime: closeTime, Domain: _nativeDomain, Strategy: NativeStrategyName, Series: CisSeries,
                EntryTime: leg.EntryTime, ExitTime: leg.ExitTime, Direction: leg.Dir, LadderLevel: 0,
                EntryFillPrice: leg.EntryFill, ExitFillPrice: leg.ExitFill, ExitReason: grp.CloseReason,
                BarsHeld: barsHeld, RealizedBps: bps,
                EntryZ: grp.EntryZ, EntrySpread: grp.EntrySpread, EntryAnchorPrice: grp.EntryAnchorPrice,
                EntrySigma: grp.EntrySigma, ExitAnchorPrice: exitAnchor, ExitSpread: exitSpread,
                EntryTrendZ: grp.EntryTrendZ, EntryTrendDir: grp.EntryTrendDir, EntryVolRegime: grp.EntryVolRegime,
                FixedExitPrice: double.NaN, MaeBps: double.NaN, MfeBps: double.NaN, Censored: censored,
                LegSymbol: leg.Symbol, SpreadPositionId: grp.GroupId));
        }
    }

    // At the fence/stop: flush staged closed groups, then emit any still-open group as censored
    // open_at_end legs (RealizedBps NaN, excluded from the realized referee; disclosed for survival).
    private void FlushBothLegCensored()
    {
        if (_strategyWriter == null || _h4 == null)
            return;
        var idx = _h4Index >= 0 && _h4Index < _h4.Count ? _h4Index : _h4.Count - 1;
        if (idx < 0)
            return;
        var closeTime = _h4.OpenTimes[idx].AddMinutes(_nativeDomainMinutes);
        var anchorPx = _lastBracket.Warmup ? double.NaN : Math.Exp(_lastBracket.AnchorLog);

        foreach (var grp in _blStagedClosed)
            EmitClosedGroupRows(grp, closeTime, anchorPx, _lastBracket.Spread, censored: 0);
        _blStagedClosed.Clear();

        if (_group != null && _group.Legs.Count > 0)
        {
            var mark = _h4.ClosePrices[idx];
            var openTime = _h4.OpenTimes[idx];
            foreach (var leg in _group.Legs)
            {
                var px = mark;
                if (!leg.IsAnchor && _blMateBarsBySymbol.TryGetValue(leg.Symbol, out var bars))
                {
                    var mp = MateCloseAt(bars, openTime);
                    if (double.IsFinite(mp)) px = mp;
                }
                leg.ExitFill = px;
                leg.ExitTime = closeTime;
            }
            _group.CloseReason = "open_at_end";
            _group.ExitBarIndex = idx;
            EmitClosedGroupRows(_group, closeTime, anchorPx, _lastBracket.Spread, censored: 1);
        }
    }

    // --- Helpers ---------------------------------------------------------------------------
    private BothLegGroup NewGroup(int i, int spreadDir, string mode, double logClose)
    {
        return new BothLegGroup
        {
            GroupId = ++_spreadGroupSeq, SpreadDir = spreadDir, ExpectedLegs = _blExpectedLegs,
            EntryBarIndex = i, EntryTime = Server.Time, ArmBarOpenTime = _h4.OpenTimes[i],
            ArmAnchorClosePrice = Math.Exp(logClose), State = GroupArming, EntryMode = mode,
            EntryZ = _lastBracket.Z, EntrySpread = _lastBracket.Spread,
            EntryAnchorPrice = _lastBracket.Warmup ? double.NaN : Math.Exp(_lastBracket.AnchorLog),
            EntrySigma = _lastBracket.Sigma, EntryTrendZ = _trendZ, EntryTrendDir = _trendDir,
            EntryVolRegime = _volRegime
        };
    }

    private double ComputeMateVolume(Symbol msym, double aPrice)
    {
        var n = _blMateNames.Count;
        if (n <= 0 || msym == null || !(aPrice > 0.0))
            return 0.0;
        var aNotional = _orderVolume * aPrice;      // A units · price (equal-spread-weight base N)
        var target = aNotional / n;                 // each mate carries 1/n of the A notional
        var mp = msym.Bid;
        if (!(mp > 0.0))
            return 0.0;
        var vol = msym.NormalizeVolumeInUnits(target / mp);
        if (vol < msym.VolumeInUnitsMin || !(vol > 0.0))
            return 0.0;
        return vol;
    }

    // Mate ≤ t-1 close at EXACTLY OpenTime == openTime (bounded backward scan). NaN if unaligned.
    private static double MateCloseAt(Bars bars, DateTime openTime)
    {
        var lo = Math.Max(0, bars.Count - 500);
        for (var k = bars.Count - 1; k >= lo; k--)
            if (bars.OpenTimes[k] == openTime)
                return bars.ClosePrices[k];
        return double.NaN;
    }
}
