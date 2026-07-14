namespace Xen.StrategyHost;

public sealed class MovingAverageCrossoverModel : ISignalModel
{
    private readonly Queue<double> _fastValues = new();
    private readonly Queue<double> _slowValues = new();
    private double _fastSum;
    private double _slowSum;
    private int _previousPosition;
    private bool _readySeen;
    private long _tradeSequence;

    public MovingAverageCrossoverModel(int fast = 20, int slow = 50, string strategyName = "ma_20_50")
    {
        if (fast < 1 || slow < 1)
            throw new ArgumentOutOfRangeException(nameof(fast), "MA windows must be >= 1.");
        if (fast >= slow)
            throw new ArgumentException("fast window must be smaller than slow window.");

        Fast = fast;
        Slow = slow;
        StrategyName = strategyName;
    }

    public int Fast { get; }
    public int Slow { get; }
    public string StrategyName { get; }

    public SignalUpdate OnBar(TimeBar bar, string domain)
    {
        _fastSum = PushWindow(_fastValues, _fastSum, bar.Close, Fast);
        _slowSum = PushWindow(_slowValues, _slowSum, bar.Close, Slow);

        var fastValue = _fastValues.Count == Fast ? _fastSum / Fast : double.NaN;
        var slowValue = _slowValues.Count == Slow ? _slowSum / Slow : double.NaN;
        var warmup = !(double.IsFinite(fastValue) && double.IsFinite(slowValue));
        var signalValue = warmup ? double.NaN : fastValue - slowValue;

        var position = 0;
        if (!warmup)
        {
            if (fastValue > slowValue)
                position = 1;
            else if (fastValue < slowValue)
                position = -1;
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
                    "crossover",
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

    private static double PushWindow(Queue<double> values, double total, double value, int window)
    {
        values.Enqueue(value);
        total += value;
        if (values.Count > window)
            total -= values.Dequeue();
        return total;
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
