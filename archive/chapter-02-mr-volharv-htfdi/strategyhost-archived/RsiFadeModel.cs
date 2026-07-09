namespace Xen.StrategyHost;

// ===========================================================================
// CF-MR-002 — causal RSI-2 mean-reversion fade (EXP-006, D-benchmark).
//
// Frozen first-branch (cf-mr-002.md / Phase-001 D0; NO tuning):
//   * Entry: RSI(2) Wilder on Close; extremes 10 / 90. RSI2 < 10 -> long (+1),
//     RSI2 > 90 -> short (-1), evaluated at the bar OPEN on confirmed bars <= t-1.
//   * Exit: reversion-completion target rested ONLY from the prior bar's closed
//     state — P*_{t-1} = Close_{t-1} + (period-1)*(AL_{t-1} - AG_{t-1}). A long
//     exits at P* when High_t >= P*_{t-1}; a short when Low_t <= P*_{t-1}. The
//     same-bar rct[di] limit (rested from bar_t's OWN close) is BANNED (L-01/P-05).
//   * No stop / second target / re-anchor in batch 1; re-entry allowed next bar.
//
// CAUSAL CONTRACT (decision-before-state-update). Entering OnBar(bar_t), the
// model's `_restedRsi` / `_restedPStar` reflect state THROUGH t-1 (folded at the
// end of the previous call). All decisions for bar_t use only those rested values
// and bar_t's execution prices (Open, and High/Low for the resting-limit touch —
// a limit placed before the bar opened fills intrabar without look-ahead). Only
// AFTER emitting does the model fold bar_t.Close into the Wilder state and refresh
// the rested values for t+1. The forming bar's own Close is never read for a decision.
//
// Wilder seeding/recursion is byte-identical to xen.mean_reversion.wilder_avg_gain_loss:
// simple mean of the first `period` deltas, then avg = (avg*(p-1) + x)/p; the first
// `period` bars are warmup (no RSI, no position).
//
// EMISSION: per bar, Position (the position HELD over bar_t, incl. an exit bar),
// real domain-bar OHLC, and ExitFillPrice (= P* on an exit bar, else NaN) so the
// Python suite truncates the exit bar's open-to-open return at the engine-realized
// favourable fill (EXP-006 amendment A1, Option C). SignalValue carries the rested
// RSI(2) that drove the decision.
// ===========================================================================
public sealed class RsiFadeModel : ISignalModel
{
    private const int Period = 2;
    private const double LowExtreme = 10.0;
    private const double HighExtreme = 90.0;

    // Wilder state (through the last folded bar).
    private readonly List<double> _seedDeltas = new();
    private double _avgGain;
    private double _avgLoss;
    private double _prevClose = double.NaN;
    private bool _seeded;
    private int _barsSeen;

    // Rested decision inputs computed from state THROUGH t-1 (refreshed at end of OnBar).
    private double _restedRsi = double.NaN;
    private double _restedPStar = double.NaN;

    private int _position;            // held position carried INTO the next bar (-1/0/+1)
    private long _tradeSequence;

    public RsiFadeModel(string strategyName = "rsi2_fade_causal")
    {
        StrategyName = strategyName;
    }

    public string StrategyName { get; }

    public SignalUpdate OnBar(TimeBar bar, string domain)
    {
        var warmup = double.IsNaN(_restedRsi);
        var events = new List<SignalEventRecord>();
        var trades = new List<StrategyTradeRecord>();

        var heldPosition = _position;   // position held over bar_t (pre any exit this bar)
        var exitFill = double.NaN;
        var entryThisBar = false;

        if (!warmup)
        {
            // --- Exit leg first: a resting limit from t-1 can fill on a currently open position.
            if (_position != 0 && TryFillRestedLimit(bar, _position))
            {
                exitFill = _restedPStar;
                trades.Add(MakeTrade(bar, domain, _position, 0, exitFill));
                events.Add(MakeEvent(bar, domain, "exit_rct", 0, _position));
                _position = 0;
            }

            // --- Entry leg: only when flat (post-exit). Re-entry allowed same bar after an exit.
            if (_position == 0)
            {
                var newPosition = _restedRsi < LowExtreme ? 1 : (_restedRsi > HighExtreme ? -1 : 0);
                if (newPosition != 0)
                {
                    _position = newPosition;
                    heldPosition = newPosition;     // this bar is held by the fresh entry
                    entryThisBar = true;
                    trades.Add(MakeTrade(bar, domain, 0, newPosition, bar.Open));
                    events.Add(MakeEvent(bar, domain, "enter_fade", newPosition, 0));

                    // A fresh entry's resting limit (still P*_{t-1}) may fill the SAME bar.
                    if (double.IsNaN(exitFill) && TryFillRestedLimit(bar, newPosition))
                    {
                        exitFill = _restedPStar;
                        trades.Add(MakeTrade(bar, domain, newPosition, 0, exitFill));
                        events.Add(MakeEvent(bar, domain, "exit_rct", 0, newPosition));
                        _position = 0;
                    }
                }
            }
        }

        var emitted = BuildPosition(bar, domain, heldPosition, exitFill, warmup);

        // --- Fold bar_t.Close into the Wilder state, then refresh rested values for t+1.
        UpdateWilder(bar.Close);
        RefreshRested(bar.Close);

        // Suppress an unused-variable warning path while keeping the entry flag self-documenting.
        _ = entryThisBar;
        return new SignalUpdate(emitted, events, trades);
    }

    private bool TryFillRestedLimit(TimeBar bar, int position)
    {
        if (double.IsNaN(_restedPStar))
            return false;
        return position == 1 ? bar.High >= _restedPStar : bar.Low <= _restedPStar;
    }

    private SignalPositionRecord BuildPosition(
        TimeBar bar, string domain, int heldPosition, double exitFill, bool warmup)
    {
        return new SignalPositionRecord(
            bar.CloseTime,
            domain,
            StrategyName,
            heldPosition,
            warmup ? double.NaN : _restedRsi,
            bar.Open,
            bar.High,
            bar.Low,
            bar.Close,
            warmup,
            heldPosition == 0,
            RegimeId: -1,
            RegimeDirection: 0,
            ExitFillPrice: exitFill);
    }

    private SignalEventRecord MakeEvent(
        TimeBar bar, string domain, string eventType, int position, int previousPosition)
    {
        return new SignalEventRecord(
            bar.CloseTime, domain, StrategyName, eventType, position, previousPosition, _restedRsi);
    }

    private StrategyTradeRecord MakeTrade(
        TimeBar bar, string domain, int previousPosition, int position, double price)
    {
        var action = position != 0
            ? (position > 0 ? "enter_long" : "enter_short")
            : (previousPosition > 0 ? "exit_long" : "exit_short");
        return new StrategyTradeRecord(
            bar.CloseTime, domain, StrategyName, action, previousPosition, position,
            price, Math.Abs(position - previousPosition), _tradeSequence++);
    }

    // Wilder average gain/loss — byte-identical seeding/recursion to wilder_avg_gain_loss.
    private void UpdateWilder(double close)
    {
        _barsSeen++;
        if (double.IsNaN(_prevClose))
        {
            _prevClose = close;
            return;
        }
        var delta = close - _prevClose;
        var gain = delta > 0.0 ? delta : 0.0;
        var loss = delta < 0.0 ? -delta : 0.0;
        if (!_seeded)
        {
            _seedDeltas.Add(delta);
            if (_seedDeltas.Count == Period)
            {
                _avgGain = _seedDeltas.Where(d => d > 0.0).Sum() / Period;
                _avgLoss = _seedDeltas.Where(d => d < 0.0).Select(d => -d).Sum() / Period;
                _seeded = true;
            }
        }
        else
        {
            _avgGain = (_avgGain * (Period - 1) + gain) / Period;
            _avgLoss = (_avgLoss * (Period - 1) + loss) / Period;
        }
        _prevClose = close;
    }

    // Refresh RSI(2) and the reversion-completion limit from the just-folded (through-t) state.
    // These become the rested values used to DECIDE on bar t+1 (the causal rct[di-1] limit).
    private void RefreshRested(double close)
    {
        if (!_seeded)
        {
            _restedRsi = double.NaN;
            _restedPStar = double.NaN;
            return;
        }
        _restedRsi = RsiValue(_avgGain, _avgLoss);
        // P*_t = Close_t + (period-1)*(AL_t - AG_t); signed offset works for both directions.
        _restedPStar = close + (Period - 1) * (_avgLoss - _avgGain);
    }

    private static double RsiValue(double avgGain, double avgLoss)
    {
        if (avgLoss == 0.0)
            return avgGain > 0.0 ? 100.0 : 50.0;
        if (avgGain == 0.0)
            return 0.0;
        return 100.0 - 100.0 / (1.0 + avgGain / avgLoss);
    }
}
