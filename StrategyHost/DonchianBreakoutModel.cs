namespace Xen.StrategyHost;

// ===========================================================================
// Donchian(20) breakout reference model (EXP-019 D-dogfood-book reference R).
//
// In-engine port of xen.referee_calibration.donchian_breakout_positions so the
// EXP-023 portfolio-fitness reference book is emitted on the SAME cTrader feed as
// the AVWAP candidate. Both models run in Mode=StrategyHost over the same
// instrument/domain, so their positions align by SourceCloseTime on the emitted
// RealClose return basis (no local-Parquet re-derivation; scope reference-book
// alignment requirement).
//
// Rule (look-ahead-safe, identical to the Python reference): at domain bar t, the
// upper/lower channel is the max High / min Low of the prior `lookback` completed
// bars (t-lookback .. t-1, excluding t). Position is +1 if Close[t] breaks above
// the upper channel, -1 if it breaks below the lower channel, else 0. The suite
// evaluates Position[t] on the t -> t+1 real-close return and drops the final bar.
// ===========================================================================
public sealed class DonchianBreakoutModel : ISignalModel
{
    private readonly int _lookback;
    private readonly Queue<double> _priorHighs = new();
    private readonly Queue<double> _priorLows = new();
    private int _previousPosition;
    private bool _readySeen;
    private long _tradeSequence;

    public DonchianBreakoutModel(int lookback = 20, string strategyName = "donchian_20")
    {
        if (lookback < 1)
            throw new ArgumentOutOfRangeException(nameof(lookback), "lookback must be >= 1.");
        _lookback = lookback;
        StrategyName = strategyName;
    }

    public int Lookback => _lookback;
    public string StrategyName { get; }

    public SignalUpdate OnBar(TimeBar bar, string domain)
    {
        var warmup = _priorHighs.Count < _lookback;
        var position = 0;
        var signalValue = double.NaN;
        if (!warmup)
        {
            // Channel from the prior `lookback` completed bars only (excludes t).
            var upper = double.NegativeInfinity;
            var lower = double.PositiveInfinity;
            foreach (var high in _priorHighs)
                upper = Math.Max(upper, high);
            foreach (var low in _priorLows)
                lower = Math.Min(lower, low);

            if (bar.Close > upper)
                position = 1;
            else if (bar.Close < lower)
                position = -1;
            signalValue = position == 1 ? bar.Close - upper : (position == -1 ? bar.Close - lower : 0.0);
        }

        var events = new List<SignalEventRecord>();
        var trades = new List<StrategyTradeRecord>();
        if (!warmup && (!_readySeen || position != _previousPosition))
        {
            if (position != _previousPosition)
            {
                events.Add(new SignalEventRecord(
                    bar.CloseTime,
                    domain,
                    StrategyName,
                    "breakout",
                    position,
                    _previousPosition,
                    signalValue));
                trades.Add(new StrategyTradeRecord(
                    bar.CloseTime,
                    domain,
                    StrategyName,
                    TradeAction(_previousPosition, position),
                    _previousPosition,
                    position,
                    bar.Close,
                    Math.Abs(position - _previousPosition),
                    _tradeSequence++));
            }
            _readySeen = true;
        }

        _previousPosition = position;

        // Push the current completed bar so it becomes part of the prior window for
        // the NEXT bar; evict the oldest beyond the lookback.
        _priorHighs.Enqueue(bar.High);
        _priorLows.Enqueue(bar.Low);
        if (_priorHighs.Count > _lookback)
        {
            _priorHighs.Dequeue();
            _priorLows.Dequeue();
        }

        return new SignalUpdate(
            new SignalPositionRecord(
                bar.CloseTime,
                domain,
                StrategyName,
                position,
                signalValue,
                bar.Open,
                bar.High,
                bar.Low,
                bar.Close,
                warmup,
                position == 0),
            events,
            trades);
    }

    private static string TradeAction(int previousPosition, int position)
    {
        if (previousPosition == 0 && position > 0)
            return "enter_long";
        if (previousPosition == 0 && position < 0)
            return "enter_short";
        if (previousPosition > 0 && position == 0)
            return "exit_long";
        if (previousPosition < 0 && position == 0)
            return "exit_short";
        if (previousPosition > 0 && position < 0)
            return "reverse_short";
        if (previousPosition < 0 && position > 0)
            return "reverse_long";
        return "position_change";
    }
}
