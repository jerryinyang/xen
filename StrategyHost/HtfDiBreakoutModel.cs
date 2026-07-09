namespace Xen.StrategyHost;

// ===========================================================================
// EXP-025 (CF-HTFDI-001/HYP-A) — CTRL-02 X-bar breakout on confirmed 5min bars,
// gated by last-CLOSED 1h Wilder ±DI(14) agreement. PRICE-PRIMARY, StrategyHost
// arm (market fills at bar open). Exits E1/E4 (native stop/limit, m1 fills) run
// in Mode=NativeOrders instead — see Xen.HtfDiNative.cs; this model refuses them.
//
// DEVIATIONS (raised pre-implementation, operator-resolved 2026-07-08):
//   D1. Sentinel ADX median window unpinned in design §6 → trailing 2016 closed
//       1h bars (same window as the ATR-tercile regime).
//   D2. TEST family clarified: E0 × 4 holds + exit* as one additional stat
//       (design §8 amended in place).
//   D3. E2 (trailing last-X HH/LL, trail lookback = entry X) and E6 (opposite
//       X-breakout) are FORMALLY IDENTICAL exit rules for this vehicle: for a
//       long, both exit on Close[t] < min(Low[t-X..t-1]) (mirror for shorts).
//       Both are implemented (shared predicate) and emit distinct labels so the
//       equivalence is measurable, but T2 should expect byte-identical streams.
//       Flagged to QA/designer.
//   D4. CTRL-REF-RANDOM (random-entry reference arm) runs as GateMode=StateOnly:
//       the engine emits the full per-bar HTF state + real OHLC and holds no
//       positions; the seed-2001 random entry TIMESTAMPS and the H∈{12,24,36,48}
//       forward returns are drawn/computed analysis-side from this emission
//       (EXP-019 D1 calendar-emission precedent; entries carry no price info,
//       so no engine fill is required — the estimand is dir_gap on forward
//       returns, not a fill-bearing P&L).
//   D5. Battery (GateMode=Battery) preserves the candidate's entry timestamps
//       EXACTLY under E0 (hold length is direction-independent). Under
//       direction-dependent exits (E2/E3/E5/E6) the position-busy windows can
//       drift after the first divergent exit; cadence match is then approximate
//       — analyst must disclose realized-cadence deltas (design §6 disclosure).
//
// CAUSAL CONTRACT (decide-on-closed, act-next-open):
//   OnBar(bar_t) first EXECUTES actions decided at t-1 close (fills at
//   bar_t.Open), then DECIDES from bar_t close + the last-closed (shifted)
//   1h snapshot. The forming bar is never read. LEAK GUARD (hard, code-
//   asserted): the HTF snapshot consumed by an entry decision must have
//   CloseTime <= bar_t.CloseTime <= entry bar Open — any violation throws.
// ===========================================================================
public enum HtfDiGateMode
{
    Di,          // candidate side must match last-closed 1h DI sign (the vehicle)
    AdxSentinel, // CTRL-NULLSENT: direction = breakout side, gate = ADX > trailing median (no DI)
    Battery,     // CTRL-RND-BATTERY: DI-gated event timestamps, direction ~ seeded Bernoulli(0.5)
    StateOnly    // CTRL-REF-RANDOM substrate: no trades, per-bar HTF state emission only (D4)
}

public enum HtfDiExit
{
    E0FixedHold,     // exit at open of entry-bar + H
    E2TrailXChannel, // close-confirmed breach of the trailing X-bar channel (== E6, D3)
    E3HeikenAshi,    // real Close crosses min/max(HAOpen,HAClose) of the last closed HA bar
    E5DiFlip,        // last-closed 1h DI direction flips vs its state at entry
    E6OppositeBreak  // opposite X-breakout fires (== E2, D3)
}

public sealed class HtfDiBreakoutModel : ISignalModel
{
    public const string SeriesLabel = "HTFDI";
    private const int TimeBackstopBars = 0; // E2/E3/E5/E6 are horizon-free (design §3)

    private readonly int _x;
    private readonly int _holdBars;
    private readonly HtfDiExit _exit;
    private readonly HtfDiGateMode _gate;
    private readonly int _phaseShiftBars;
    private readonly Random? _batteryRng;
    private readonly WilderHtfState _htf = new(60);

    // prior-X 5min channel (excludes the current bar; DonchianBreakoutModel convention)
    private readonly Queue<double> _priorHighs = new();
    private readonly Queue<double> _priorLows = new();

    // Heiken-Ashi state of the LAST CLOSED 5min bar (decision only; P&L on real prices)
    private double _haOpen = double.NaN, _haClose = double.NaN;

    // pending actions decided at t-1 close, executed at bar_t open
    private bool _pendingEntry;
    private int _pendingDir;
    private double _pendingBreakoutRef;
    private HtfSnapshot? _pendingSnapshot;
    private bool _pendingExit;
    private string _pendingExitReason = "";

    // open trade state
    private int _position;
    private double _entryFill = double.NaN;
    private DateTime _entryTime;
    private long _entryBarIndex = -1;
    private int _entryHtfDir;
    private HtfSnapshot? _entrySnapshot;
    private double _entryBreakoutRef = double.NaN;
    private double _maeBps, _mfeBps;

    private long _barIndex = -1;
    private long _tradeSequence;
    private readonly List<CisTradeRecord> _pendingTradeRows = new();

    public HtfDiBreakoutModel(int x, int holdBars, HtfDiExit exit, HtfDiGateMode gate,
                              int batterySeed = 0, int phaseShiftBars = 0,
                              string? strategyName = null)
    {
        if (x < 1) throw new ArgumentOutOfRangeException(nameof(x));
        if (exit == HtfDiExit.E0FixedHold && holdBars < 1)
            throw new ArgumentOutOfRangeException(nameof(holdBars), "E0 requires HoldBars >= 1.");
        if (gate == HtfDiGateMode.Battery && batterySeed <= 0)
            throw new ArgumentException("Battery gate requires a pre-registered seed (1001-1025).");
        if (phaseShiftBars < 0) throw new ArgumentOutOfRangeException(nameof(phaseShiftBars));
        _x = x;
        _holdBars = holdBars;
        _exit = exit;
        _gate = gate;
        _phaseShiftBars = phaseShiftBars;
        _batteryRng = gate == HtfDiGateMode.Battery ? new Random(batterySeed) : null;
        StrategyName = strategyName ?? DefaultName(x, holdBars, exit, gate, batterySeed, phaseShiftBars);
    }

    public string StrategyName { get; }

    /// <summary>Per-trade rows completed on this bar; drained by the host after Append.</summary>
    public IReadOnlyList<CisTradeRecord> DrainTradeRows()
    {
        var rows = _pendingTradeRows.ToArray();
        _pendingTradeRows.Clear();
        return rows;
    }

    public SignalUpdate OnBar(TimeBar bar, string domain)
    {
        _barIndex++;
        var events = new List<SignalEventRecord>();
        var trades = new List<StrategyTradeRecord>();
        double entryFillEmit = double.NaN, exitFillEmit = double.NaN;

        // ---- 1. execute actions decided at t-1 close, at THIS bar's open ----
        if (_pendingExit && _position != 0)
        {
            exitFillEmit = bar.Open;
            CloseTrade(bar, bar.Open, _pendingExitReason, censored: false, trades, events, domain);
        }
        _pendingExit = false;
        _pendingExitReason = "";

        if (_pendingEntry && _position == 0)
        {
            // LEAK GUARD (hard): the HTF bar conditioning this entry must be closed
            // strictly before the entry bar's open (design §3, golden-trace pin).
            if (_pendingSnapshot is null || _pendingSnapshot.CloseTime > bar.OpenTime)
                throw new InvalidOperationException(
                    $"HTF leak guard: snapshot CloseTime {_pendingSnapshot?.CloseTime:o} " +
                    $">= entry bar Open {bar.OpenTime:o}");
            _position = _pendingDir;
            _entryFill = bar.Open;
            entryFillEmit = bar.Open;
            _entryTime = bar.OpenTime;
            _entryBarIndex = _barIndex;
            _entrySnapshot = _pendingSnapshot;
            _entryHtfDir = Math.Sign(_pendingSnapshot.PlusDi - _pendingSnapshot.MinusDi);
            _entryBreakoutRef = _pendingBreakoutRef;
            _maeBps = 0.0; _mfeBps = 0.0;
            trades.Add(new StrategyTradeRecord(bar.CloseTime, domain, StrategyName,
                _position > 0 ? "enter_long" : "enter_short", 0, _position, bar.Open, 1, _tradeSequence++));
        }
        _pendingEntry = false;
        _pendingSnapshot = null;

        var heldPosition = _position;   // position accruing this bar's open-to-open return

        // ---- 2. fold bar_t into decision state (bar_t is now a CLOSED bar) ----
        _htf.Update(bar);
        // Tripwire runs shift the WHOLE HTF stream (design §6): decisions, regime,
        // and the emitted per-bar/per-trade HTF state all read the SAME shifted snapshot.
        var snap = _htf.Snapshot(_phaseShiftBars);

        if (_position != 0 && _entryFill > 0.0)
        {
            var bps = _position * (bar.Close - _entryFill) / _entryFill * 1e4;
            if (bps < _maeBps) _maeBps = bps;
            if (bps > _mfeBps) _mfeBps = bps;
        }

        var channelReady = _priorHighs.Count >= _x;
        double upper = double.NaN, lower = double.NaN;
        if (channelReady)
        {
            upper = double.NegativeInfinity; lower = double.PositiveInfinity;
            foreach (var h in _priorHighs) upper = Math.Max(upper, h);
            foreach (var l in _priorLows) lower = Math.Min(lower, l);
        }

        // ---- 3. exit decision on the closed bar (acts at next open) ----
        if (_position != 0)
        {
            var barsHeld = (int)(_barIndex - _entryBarIndex) + 1; // completed bars incl. this one
            switch (_exit)
            {
                case HtfDiExit.E0FixedHold:
                    if (barsHeld >= _holdBars) StageExit("fixed_hold");
                    break;
                case HtfDiExit.E2TrailXChannel:
                    if (channelReady && (_position > 0 ? bar.Close < lower : bar.Close > upper))
                        StageExit("trail_channel_breach");
                    break;
                case HtfDiExit.E6OppositeBreak:
                    // Amended design §3 (2026-07-08, QA Issue 4/D3): opposite breakout must
                    // ALSO pass the HTF-DI gate in the opposite direction (the full §1 event).
                    if (channelReady && snap is not null && !double.IsNaN(snap.PlusDi)
                        && (_position > 0
                            ? bar.Close < lower && snap.PlusDi < snap.MinusDi
                            : bar.Close > upper && snap.PlusDi > snap.MinusDi))
                        StageExit("opposite_breakout");
                    break;
                case HtfDiExit.E3HeikenAshi:
                    if (!double.IsNaN(_haOpen))
                    {
                        var haRef = _position > 0 ? Math.Min(_haOpen, _haClose) : Math.Max(_haOpen, _haClose);
                        if (_position > 0 ? bar.Close < haRef : bar.Close > haRef)
                            StageExit("ha_trail_cross");
                    }
                    break;
                case HtfDiExit.E5DiFlip:
                    if (snap is not null && !double.IsNaN(snap.PlusDi))
                    {
                        var dir = Math.Sign(snap.PlusDi - snap.MinusDi);
                        if (dir != 0 && dir != _entryHtfDir) StageExit("htf_di_flip");
                    }
                    break;
            }
        }

        // ---- 4. entry decision (flat, not exiting this open, confirmed signal) ----
        var warmup = !channelReady || snap is null || double.IsNaN(snap?.PlusDi ?? double.NaN);
        double signalValue = double.NaN;
        if (_gate != HtfDiGateMode.StateOnly && !warmup && _position == 0 && !_pendingExit && !_pendingEntry)
        {
            var candidate = 0;
            double breakoutRef = double.NaN;
            if (bar.Close > upper) { candidate = 1; breakoutRef = upper; }
            else if (bar.Close < lower) { candidate = -1; breakoutRef = lower; }

            if (candidate != 0)
            {
                var htfDir = Math.Sign(snap!.PlusDi - snap.MinusDi);
                var eligible = _gate switch
                {
                    HtfDiGateMode.Di => htfDir == candidate,
                    HtfDiGateMode.Battery => htfDir == candidate,      // same event timestamps as the candidate
                    HtfDiGateMode.AdxSentinel => snap.AdxGateReady && snap.AdxAboveMedian,
                    _ => false
                };
                if (eligible)
                {
                    var dir = _gate == HtfDiGateMode.Battery
                        ? (_batteryRng!.NextDouble() < 0.5 ? 1 : -1)   // seeded coin, drawn once per gated event
                        : candidate;
                    _pendingEntry = true;
                    _pendingDir = dir;
                    _pendingBreakoutRef = breakoutRef;
                    _pendingSnapshot = snap;
                    signalValue = candidate > 0 ? bar.Close - upper : bar.Close - lower;
                    events.Add(new SignalEventRecord(bar.CloseTime, domain, StrategyName,
                        "breakout_signal", dir, 0, signalValue));
                }
            }
        }

        // ---- 5. fold decision windows AFTER use (channel excludes the current bar) ----
        _priorHighs.Enqueue(bar.High);
        _priorLows.Enqueue(bar.Low);
        if (_priorHighs.Count > _x) { _priorHighs.Dequeue(); _priorLows.Dequeue(); }
        var haCloseNew = (bar.Open + bar.High + bar.Low + bar.Close) / 4.0;
        _haOpen = double.IsNaN(_haOpen) ? (bar.Open + bar.Close) / 2.0 : (_haOpen + _haClose) / 2.0;
        _haClose = haCloseNew;

        // ---- 6. per-bar emission: bar OHLC + the (shifted) HTF state decisions saw ----
        // Field mapping (documented for the analyst): TrendZ = (+DI - -DI), TrendDir =
        // sign(TrendZ), VolRegime = ATR tercile (-1 UNSET), SignalValue = ADX.
        var plusMinus = snap is not null ? snap.PlusDi - snap.MinusDi : double.NaN;
        return new SignalUpdate(
            new SignalPositionRecord(
                bar.CloseTime, domain, StrategyName,
                heldPosition,
                snap is not null ? snap.Adx : double.NaN,
                bar.Open, bar.High, bar.Low, bar.Close,
                warmup,
                heldPosition == 0,
                EntryFillPrice: entryFillEmit,
                ExitFillPrice: exitFillEmit,
                TrendZ: plusMinus,
                TrendDir: double.IsNaN(plusMinus) ? 0 : Math.Sign(plusMinus),
                VolRegime: snap?.AtrRegime ?? -1,
                OpenLegs: heldPosition == 0 ? 0 : 1,
                MtmBps: heldPosition != 0 && _entryFill > 0.0
                    ? heldPosition * (bar.Close - _entryFill) / _entryFill * 1e4
                    : double.NaN),
            events,
            trades);
    }

    /// <summary>Censor a fence-open trade at run end (host calls before Dispose).</summary>
    public void FlushOpenAsCensored(string domain)
    {
        if (_position == 0)
            return;
        _pendingTradeRows.Add(BuildTradeRow(
            sourceCloseTime: _entryTime, exitTime: _entryTime, exitFill: double.NaN,
            exitReason: "open_at_end", barsHeld: (int)(_barIndex - _entryBarIndex) + 1,
            realizedBps: double.NaN, censored: 1, domain: domain));
        _position = 0;
    }

    private void StageExit(string reason)
    {
        _pendingExit = true;
        _pendingExitReason = reason;
    }

    private void CloseTrade(TimeBar bar, double fill, string reason, bool censored,
                            List<StrategyTradeRecord> trades, List<SignalEventRecord> events, string domain)
    {
        var barsHeld = (int)(_barIndex - _entryBarIndex);
        var bps = _entryFill > 0.0 ? _position * (fill - _entryFill) / _entryFill * 1e4 : double.NaN;
        trades.Add(new StrategyTradeRecord(bar.CloseTime, domain, StrategyName,
            _position > 0 ? "exit_long" : "exit_short", _position, 0, fill, 1, _tradeSequence++));
        events.Add(new SignalEventRecord(bar.CloseTime, domain, StrategyName, reason, 0, _position, bps));
        _pendingTradeRows.Add(BuildTradeRow(bar.CloseTime, bar.OpenTime, fill, reason, barsHeld,
            bps, censored ? 1 : 0, domain));
        _position = 0;
        _entryFill = double.NaN;
        _entryBarIndex = -1;
    }

    private CisTradeRecord BuildTradeRow(DateTime sourceCloseTime, DateTime exitTime, double exitFill,
                                         string exitReason, int barsHeld, double realizedBps,
                                         int censored, string domain)
    {
        var s = _entrySnapshot;
        return new CisTradeRecord(
            SourceCloseTime: sourceCloseTime, Domain: domain, Strategy: StrategyName, Series: SeriesLabel,
            EntryTime: _entryTime, ExitTime: exitTime, Direction: _position, LadderLevel: 0,
            EntryFillPrice: _entryFill, ExitFillPrice: exitFill, ExitReason: exitReason,
            BarsHeld: barsHeld, RealizedBps: realizedBps,
            EntryZ: double.NaN, EntrySpread: double.NaN, EntryAnchorPrice: double.NaN,
            EntrySigma: double.NaN, ExitAnchorPrice: double.NaN, ExitSpread: double.NaN,
            EntryTrendZ: s is not null ? s.PlusDi - s.MinusDi : double.NaN,
            EntryTrendDir: _entryHtfDir,
            EntryVolRegime: s?.AtrRegime ?? -1,
            FixedExitPrice: double.NaN, MaeBps: _maeBps, MfeBps: _mfeBps, Censored: censored,
            SlPrice: double.NaN,
            HorizonBars: _exit == HtfDiExit.E0FixedHold ? _holdBars : TimeBackstopBars,
            BreakoutRef: _entryBreakoutRef,
            SignalX: _x,
            HtfPlusDi: s?.PlusDi ?? double.NaN,
            HtfMinusDi: s?.MinusDi ?? double.NaN,
            HtfAdx: s?.Adx ?? double.NaN,
            HtfAtr: s?.Atr ?? double.NaN,
            HtfBarCloseTime: s?.CloseTime ?? default);
    }

    private static string DefaultName(int x, int hold, HtfDiExit exit, HtfDiGateMode gate,
                                      int seed, int shift)
    {
        var exitTag = exit switch
        {
            HtfDiExit.E0FixedHold => $"e0h{hold}",
            HtfDiExit.E2TrailXChannel => "e2",
            HtfDiExit.E3HeikenAshi => "e3",
            HtfDiExit.E5DiFlip => "e5",
            _ => "e6"
        };
        var gateTag = gate switch
        {
            HtfDiGateMode.Di => "di",
            HtfDiGateMode.AdxSentinel => "adx",
            HtfDiGateMode.Battery => $"bat{seed}",
            _ => "state"
        };
        var shiftTag = shift > 0 ? $"_shift{shift}" : "";
        return $"htfdi_x{x}_{exitTag}_{gateTag}{shiftTag}";
    }
}
