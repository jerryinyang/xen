using System;
using System.Collections.Generic;
using cAlgo.API;
using Xen.StrategyHost;

namespace cAlgo.Robots;

// =======================================================================
// EXP-019 (CF-VOLHARV-001 HYP-001) — RandomHold: seeded random-timing,
// random-direction, fixed-hold market legs (design §4). Native cTrader
// market orders, m1 fills, 4h decision grid. NO conditioning of any kind:
// entries fire unconditionally at pre-scheduled bar opens from a CSV fixed
// before the run; the ONLY override is the deterministic inventory cap
// (scheduled entry at cap → SKIPPED, logged cap_skip, never deferred).
// Exits: market at the open of entry-bar + H. No TP, no SL, no refresh.
// Reuses the EXP-018 schedule-consumption machinery (LoadSchedule /
// scheduled fire / matched-hold market exits); all CIS trigger/basket/z
// code paths are absent by construction.
//
// DEVIATIONS (raised 2026-07-04, operator-resolved pre-implementation):
//   D1. Schedule calendar source: the engine's 4h grid is broker-server-
//       aligned (UTC+2/+3, DST-switching), so a UTC clock calendar cannot
//       be used. The generator consumes the engine's own emitted per-bar
//       timestamps (timestamps ONLY, never prices). This requires one
//       cheap calendar-emission run per instrument (RH Schedule Path=""
//       → no orders, per-bar records only) before schedule generation.
//   D2. TRAIN fence = the EXP-013/018 per-instrument 49% cutoffs
//       (2023-vintage base files) — operator-selected for band identity
//       with the EXP-018 anomaly.
//   D3. Generator drops entries whose hold would cross the fence
//       (operator-selected: zero censored legs, balanced hold strata).
//   D4. Warmup = first 50 calendar 4h bars excluded (operator-selected).
//   D5. Design §6 swap table replaced by operator directive 2026-07-04:
//       cost table = FTMO published commissions/spread; swap disregarded.
//       Analysis-layer concern only; the engine emission stays gross.
//   D6. Conf packaging: one multi-symbol conf per arm (EXP-019.conf /
//       EXP-019-delay1.conf / EXP-019-cal.conf) with the seed selected via
//       EXP019_SEED, instead of the design's 16 per-symbol confs — same
//       cells, but a SINGLE family root per arm so xen.estimand_validation
//       validate_family covers the whole emission in one gate call.
// =======================================================================
public partial class Xen
{
    private const string RhStrategyName = "random_hold";

    private bool _rhReady;
    private bool _rhStopping;
    private bool _rhScheduleMode;                       // false = calendar-emission run (no orders)
    private Bars _rhH4 = null!;
    private int _rhIndex = -1;                          // last processed completed 4h bar
    private string _rhLabel = "";
    private double _rhVolume;
    private long _rhTradeSeq;
    private List<ScheduledEntry> _rhSchedule = new();
    private int _rhScheduleCursor;
    private int _rhFiringIndex = -1;                    // decision-bar index staged before ExecuteMarketOrder
    private int _rhClosingIndex = -1;                   // decision-bar index staged before ClosePosition
    private long _rhCapSkips;
    private long _rhStaleSkips;

    private sealed class RhLeg
    {
        public long PositionId;
        public int Dir;                                 // +1 long / −1 short
        public double EntryFill;
        public int EntryH4Index;                        // decision-bar index (fill = open of index+1)
        public DateTime EntryTime;
        public int HoldBars;
        public double MaeBps;
        public double MfeBps;
    }

    private readonly List<RhLeg> _rhLegs = new();
    private readonly Dictionary<long, string> _rhPendingReason = new();

    private sealed class RhClosed
    {
        public RhLeg Leg = null!;
        public double ExitFill;
        public string Reason = "";
        public DateTime ExitTime;
        public int BarsHeld;
    }

    private readonly List<RhClosed> _rhPeriodClosed = new();
    private List<SignalEventRecord> _rhPeriodEvents = new();
    private List<StrategyTradeRecord> _rhPeriodTrades = new();
    private int _rhPeriodStartSign;
    private int _rhPeriodEntryDir;
    private double _rhPendingEntryFill = double.NaN;
    private double _rhPendingExitFill = double.NaN;

    private void StartRandomHold()
    {
        if (DomainMinutes != 240)
            throw new InvalidOperationException(
                $"RandomHold (EXP-019) is 4h-only; DomainMinutes must be 240, got {DomainMinutes}.");
        if (!TryParseAnalysisEndUtc(AnalysisEndUtc, out var analysisEndUtc))
            throw new InvalidOperationException("Analysis End UTC must be explicit, e.g. 2026-01-01T00:00:00Z.");
        if (RhMaxOpenLegs < 1)
            throw new InvalidOperationException("RH Max Open Legs must be >= 1.");

        if (!string.IsNullOrWhiteSpace(RhSchedulePath))
        {
            _rhSchedule = LoadSchedule(RhSchedulePath.Trim());
            _rhScheduleMode = true;
        }

        _rhH4 = MarketData.GetBars(TimeFrame.Hour4, SymbolName);
        _strategyFence = new HoldoutFence(analysisEndUtc);
        _strategyWriter = new StrategyRunParquetWriter(
            StrategyOutputDirectory, RhStrategyName, SymbolName, "4h",
            _strategyFence, BuildStrategyParameters(null));
        _rhLabel = $"rh_{SanitizeLabel(SymbolName)}";
        _rhVolume = Symbol.NormalizeVolumeInUnits(Symbol.VolumeInUnitsMin);

        Positions.Opened += OnRhPositionOpened;
        Positions.Closed += OnRhPositionClosed;
        _rhReady = true;

        Print(
            "Xen EXP-019 RandomHold for {0}: mode={1}; schedule_rows={2}; seed={3}; cap={4}; AnalysisEndUtc={5:o}; out={6}",
            SymbolName, _rhScheduleMode ? "scheduled" : "calendar_emission", _rhSchedule.Count,
            RhSeed, RhMaxOpenLegs, _strategyFence.AnalysisEndUtc, _strategyWriter.RunDirectory);
    }

    private void RunRandomHoldOnBar()
    {
        if (_rhStopping)
            return;
        var latest = _rhH4.Count - 2;   // last fully-completed 4h bar
        if (latest <= _rhIndex)
            return;
        for (var i = _rhIndex + 1; i <= latest; i++)
            if (!ProcessRhBar(i, armOrders: i == latest))
                return;   // hit fence
    }

    // Process one completed 4h bar i: fence check, matched-hold exits (decision on the completed
    // bar, market fill at the open of i+1), emit the per-bar record, then fire schedule rows whose
    // open_time_utc == the forming bar's open (fill timestamp == scheduled bar open — tripwire 2).
    private bool ProcessRhBar(int i, bool armOrders)
    {
        var openTime = _rhH4.OpenTimes[i];
        var closeTime = openTime.AddMinutes(240);
        if (_strategyFence!.ShouldStopBeforeProcessing(closeTime))
        {
            _rhStopping = true;
            Stop();
            return false;
        }

        var close = _rhH4.ClosePrices[i];
        if (close > 0.0)
            foreach (var leg in _rhLegs)
            {
                if (!(leg.EntryFill > 0.0))
                    continue;
                var bps = leg.Dir * (close - leg.EntryFill) / leg.EntryFill * 1e4;
                if (bps < leg.MaeBps) leg.MaeBps = bps;
                if (bps > leg.MfeBps) leg.MfeBps = bps;
            }

        // Matched-hold exits: close every leg held >= its scheduled hold. EntryH4Index is the
        // DECISION bar (fill at open of EntryH4Index+1), so closing at completed bar
        // i = EntryH4Index + H fills at open(i+1) = open(fill-bar + H): held exactly H bars.
        if (armOrders && _rhLegs.Count > 0)
        {
            var toClose = new List<long>();
            foreach (var leg in _rhLegs)
                if (i - leg.EntryH4Index >= leg.HoldBars)
                    toClose.Add(leg.PositionId);
            _rhClosingIndex = i;
            foreach (var id in toClose)
            {
                _rhPendingReason[id] = "matched_hold";
                foreach (var p in Positions)
                    if (p.Label == _rhLabel && p.Id == id) { ClosePosition(p); break; }
            }
        }

        EmitRhPosition(i, closeTime);
        _rhPendingEntryFill = double.NaN;
        _rhPendingExitFill = double.NaN;

        if (armOrders && _rhScheduleMode)
            FireRhScheduledEntries(i);

        _rhIndex = i;
        return true;
    }

    // Fire schedule rows whose open_time_utc == the FORMING bar's open (available: the engine has
    // opened bar i+1 when bar i completes). The market order fills at the first m1 tick of that
    // bar ≈ its open — the scheduled bar open. Rows older than the forming bar are stale-skipped
    // (start-of-run backlog only; disclosed). A row landing at the inventory cap is SKIPPED and
    // logged cap_skip — deterministic, never deferred (design §4).
    private void FireRhScheduledEntries(int i)
    {
        if (i + 1 >= _rhH4.Count)
            return;
        var nextOpen = _rhH4.OpenTimes[i + 1];
        while (_rhScheduleCursor < _rhSchedule.Count && _rhSchedule[_rhScheduleCursor].OpenTimeUtc < nextOpen)
        {
            _rhStaleSkips++;
            Print("EXP-019 stale schedule row skipped: {0:o}", _rhSchedule[_rhScheduleCursor].OpenTimeUtc);
            _rhScheduleCursor++;
        }
        while (_rhScheduleCursor < _rhSchedule.Count && _rhSchedule[_rhScheduleCursor].OpenTimeUtc == nextOpen)
        {
            var e = _rhSchedule[_rhScheduleCursor++];
            if (_rhLegs.Count >= RhMaxOpenLegs)
            {
                _rhCapSkips++;
                _rhPeriodEvents.Add(new SignalEventRecord(
                    nextOpen, "4h", RhStrategyName, "cap_skip", 0, 0, e.HoldBars));
                Print("EXP-019 cap_skip at {0:o} (open legs={1})", nextOpen, _rhLegs.Count);
                continue;
            }
            _rhFiringIndex = i;
            ExecuteMarketOrder(e.Dir > 0 ? TradeType.Buy : TradeType.Sell, SymbolName, _rhVolume,
                _rhLabel, null, null, $"{e.Level};{e.HoldBars}");
        }
    }

    private void OnRhPositionOpened(PositionOpenedEventArgs args)
    {
        var pos = args.Position;
        if (pos.Label != _rhLabel)
            return;
        var dir = pos.TradeType == TradeType.Sell ? -1 : 1;
        var hold = 0;
        var parts = (pos.Comment ?? "").Split(';');
        if (parts.Length >= 2) int.TryParse(parts[1], out hold);
        if (hold < 1)
            throw new InvalidOperationException($"RandomHold fill without a scheduled hold (comment='{pos.Comment}').");
        _rhLegs.Add(new RhLeg
        {
            PositionId = pos.Id, Dir = dir, EntryFill = pos.EntryPrice,
            EntryH4Index = _rhFiringIndex, EntryTime = Server.Time, HoldBars = hold
        });
        _rhPeriodEntryDir = dir;
        _rhPendingEntryFill = pos.EntryPrice;
        _rhPeriodTrades.Add(new StrategyTradeRecord(
            Server.Time, "4h", RhStrategyName, dir > 0 ? "buy" : "sell",
            0, dir, pos.EntryPrice, 1, ++_rhTradeSeq));
        _rhPeriodEvents.Add(new SignalEventRecord(
            Server.Time, "4h", RhStrategyName, "scheduled_market_entry", dir, 0, hold));
    }

    private void OnRhPositionClosed(PositionClosedEventArgs args)
    {
        var pos = args.Position;
        if (pos.Label != _rhLabel)
            return;
        RhLeg? leg = null;
        foreach (var l in _rhLegs)
            if (l.PositionId == pos.Id) { leg = l; break; }
        var fill = ClosingPriceOf(pos.Id);
        _rhPendingExitFill = fill;
        var reason = _rhPendingReason.TryGetValue(pos.Id, out var r) ? r : "unstaged_close";
        _rhPendingReason.Remove(pos.Id);
        var prev = leg?.Dir ?? (pos.TradeType == TradeType.Sell ? -1 : 1);
        if (leg != null)
        {
            _rhPeriodClosed.Add(new RhClosed
            {
                Leg = leg, ExitFill = fill, Reason = reason, ExitTime = Server.Time,
                BarsHeld = Math.Max(0, _rhClosingIndex - leg.EntryH4Index)
            });
            _rhLegs.Remove(leg);
        }
        _rhPeriodTrades.Add(new StrategyTradeRecord(
            Server.Time, "4h", RhStrategyName, prev > 0 ? "sell" : "buy",
            prev, 0, fill, 1, ++_rhTradeSeq));
        _rhPeriodEvents.Add(new SignalEventRecord(
            Server.Time, "4h", RhStrategyName, reason, 0, prev, double.NaN));
    }

    private void EmitRhPosition(int i, DateTime closeTime)
    {
        var closeI = _rhH4.ClosePrices[i];
        var heldPosition = _rhPeriodEntryDir != 0 ? _rhPeriodEntryDir : _rhPeriodStartSign;

        double mtm = double.NaN;
        if (_rhLegs.Count > 0)
        {
            var acc = 0.0; var n = 0;
            foreach (var leg in _rhLegs)
                if (leg.EntryFill > 0.0) { acc += leg.Dir * (closeI - leg.EntryFill) / leg.EntryFill * 1e4; n++; }
            if (n > 0) mtm = acc;
        }

        var rec = new SignalPositionRecord(
            SourceCloseTime: closeTime, Domain: "4h", Strategy: RhStrategyName,
            Position: heldPosition, SignalValue: double.NaN,
            RealOpen: _rhH4.OpenPrices[i], RealHigh: _rhH4.HighPrices[i],
            RealLow: _rhH4.LowPrices[i], RealClose: closeI,
            Warmup: false, IsFlat: heldPosition == 0,
            ExitFillPrice: _rhPendingExitFill, EntryFillPrice: _rhPendingEntryFill,
            OpenLegs: _rhLegs.Count, MtmBps: mtm);
        _strategyWriter!.Append(new SignalUpdate(rec, _rhPeriodEvents, _rhPeriodTrades));
        _rhPeriodEvents = new List<SignalEventRecord>();
        _rhPeriodTrades = new List<StrategyTradeRecord>();

        foreach (var ct in _rhPeriodClosed)
        {
            var bps = ct.Leg.EntryFill > 0.0
                ? ct.Leg.Dir * (ct.ExitFill - ct.Leg.EntryFill) / ct.Leg.EntryFill * 1e4
                : double.NaN;
            _strategyWriter!.AppendCisTrade(new CisTradeRecord(
                SourceCloseTime: closeTime, Domain: "4h", Strategy: RhStrategyName, Series: "RANDOM_HOLD",
                EntryTime: ct.Leg.EntryTime, ExitTime: ct.ExitTime, Direction: ct.Leg.Dir, LadderLevel: 0,
                EntryFillPrice: ct.Leg.EntryFill, ExitFillPrice: ct.ExitFill, ExitReason: ct.Reason,
                BarsHeld: ct.BarsHeld, RealizedBps: bps,
                EntryZ: double.NaN, EntrySpread: double.NaN, EntryAnchorPrice: double.NaN,
                EntrySigma: double.NaN, ExitAnchorPrice: double.NaN, ExitSpread: double.NaN,
                EntryTrendZ: double.NaN, EntryTrendDir: 0, EntryVolRegime: -1,
                FixedExitPrice: double.NaN, MaeBps: ct.Leg.MaeBps, MfeBps: ct.Leg.MfeBps, Censored: 0,
                SlPrice: double.NaN, HorizonBars: ct.Leg.HoldBars));
        }
        _rhPeriodClosed.Clear();

        var s = 0;
        foreach (var leg in _rhLegs)
            s += leg.Dir;
        _rhPeriodStartSign = Math.Sign(s);
        _rhPeriodEntryDir = 0;
    }

    // At the fence/stop, emit any still-open legs as censored open_at_end rows (RealizedBps NaN,
    // excluded from realized reads, disclosed). With the generator's drop-can't-complete rule
    // (D3) this should be empty on a clean run — a non-empty flush is itself a finding.
    private void FlushRandomHoldCensored()
    {
        if (_strategyWriter == null || _rhH4 == null || _rhLegs.Count == 0)
            return;
        var idx = _rhIndex >= 0 && _rhIndex < _rhH4.Count ? _rhIndex : _rhH4.Count - 1;
        if (idx < 0)
            return;
        var mark = _rhH4.ClosePrices[idx];
        var closeTime = _rhH4.OpenTimes[idx].AddMinutes(240);
        foreach (var leg in _rhLegs)
            _strategyWriter.AppendCisTrade(new CisTradeRecord(
                SourceCloseTime: closeTime, Domain: "4h", Strategy: RhStrategyName, Series: "RANDOM_HOLD",
                EntryTime: leg.EntryTime, ExitTime: closeTime, Direction: leg.Dir, LadderLevel: 0,
                EntryFillPrice: leg.EntryFill, ExitFillPrice: mark, ExitReason: "open_at_end",
                BarsHeld: Math.Max(0, _rhIndex - leg.EntryH4Index), RealizedBps: double.NaN,
                EntryZ: double.NaN, EntrySpread: double.NaN, EntryAnchorPrice: double.NaN,
                EntrySigma: double.NaN, ExitAnchorPrice: double.NaN, ExitSpread: double.NaN,
                EntryTrendZ: double.NaN, EntryTrendDir: 0, EntryVolRegime: -1,
                FixedExitPrice: double.NaN, MaeBps: leg.MaeBps, MfeBps: leg.MfeBps, Censored: 1,
                SlPrice: double.NaN, HorizonBars: leg.HoldBars));
        Print("EXP-019 fence flush: {0} censored open legs; cap_skips={1}; stale_skips={2}",
            _rhLegs.Count, _rhCapSkips, _rhStaleSkips);
    }
}
