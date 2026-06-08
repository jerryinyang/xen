namespace Xen.StrategyHost;

// ===========================================================================
// CF-AVWAP-001 baseline strategy-host model (Phase 004, EXP-023).
//
// This is the in-engine port of the frozen first-branch AVWAP signal defined in
// python/src/xen/avwap.py (registry docs/signal-registry/candidate-families/avwap.md)
// plus the EXP-023 baseline strategy-position overlay scoped in
// python/experiments/EXP-023/scope.md.
//
// SIGNAL (transcription target = xen.avwap.generate_avwap_events):
//   - regime: causal MA(fast,slow) on domain Close (+1 bull / -1 bear / 0 warmup);
//   - anchor: on a confirmed regime change, bullish -> lowest Low / bearish ->
//     highest High of the just-ended segment (viable pivots from completed bars);
//   - AVWAP: cumulative TickVolume**0.75-weighted typical price (H+L+C)/3 from the
//     active anchor through the current completed domain bar;
//   - band: median absolute deviation of typical price from the anchored AVWAP
//     path since the anchor, multiplier 1.0;
//   - bounce: a completed close crosses AVWAP in the regime direction after first
//     moving to the opposite side (arm then trigger; re-arm before the next).
//
// POSITION OVERLAY (EXP-023 scope baseline rule, EXP-022 completion rule):
//   - flat + bounce trigger -> enter one unit in the bounce direction;
//   - hold until the first completed close hits the frozen favorable or adverse
//     target, or the opposite MA regime is confirmed (trend-change), favorable
//     winning a same-bar tie (mirrors EXP-022 scan_lifetime);
//   - flat at completion; no second position while active (record a non-executed
//     pyramid opportunity); unfinished moves at the analysis-set end are left open
//     (no forced exit).
//
// Streaming and deterministic: every update uses only the current and prior
// completed domain bars, identical output for identical input. One position row is
// emitted per domain bar; bounce events and entry/exit/pyramid trades are emitted
// as diagnostics. The full per-bounce detail used for the EXP-023 transcription
// smoke is exposed via EventDetails.
// ===========================================================================

/// <summary>Append-only running median over two binary heaps.</summary>
/// <remarks>
/// Faithful port of <c>xen.avwap._StreamingMedian</c>: <c>_low</c> is a max-heap
/// (a min-heap of negated values) holding the lower half, <c>_high</c> a min-heap
/// holding the upper half. The median depends only on the pushed multiset, so it is
/// deterministic regardless of insertion order.
/// </remarks>
internal sealed class StreamingMedian
{
    private readonly MinHeap _low = new();   // max-heap via negation (lower half)
    private readonly MinHeap _high = new();  // min-heap (upper half)

    public void Push(double value)
    {
        if (_low.Count == 0 || value <= -_low.Peek())
            _low.Push(-value);
        else
            _high.Push(value);

        if (_low.Count > _high.Count + 1)
            _high.Push(-_low.Pop());
        else if (_high.Count > _low.Count)
            _low.Push(-_high.Pop());
    }

    public double Median()
    {
        if (_low.Count == 0)
            return double.NaN;
        if (_low.Count > _high.Count)
            return -_low.Peek();
        return ((-_low.Peek()) + _high.Peek()) / 2.0;
    }

    /// <summary>Binary min-heap of doubles mirroring CPython's <c>heapq</c> order.</summary>
    private sealed class MinHeap
    {
        private readonly List<double> _items = new();

        public int Count => _items.Count;

        public double Peek() => _items[0];

        public void Push(double value)
        {
            _items.Add(value);
            SiftDown(0, _items.Count - 1);
        }

        public double Pop()
        {
            var last = _items[^1];
            _items.RemoveAt(_items.Count - 1);
            if (_items.Count == 0)
                return last;
            var returnItem = _items[0];
            _items[0] = last;
            SiftUp(0);
            return returnItem;
        }

        // CPython heapq _siftdown: bubble newly added leaf toward the root.
        private void SiftDown(int startPos, int pos)
        {
            var newItem = _items[pos];
            while (pos > startPos)
            {
                var parentPos = (pos - 1) >> 1;
                var parent = _items[parentPos];
                if (newItem < parent)
                {
                    _items[pos] = parent;
                    pos = parentPos;
                    continue;
                }
                break;
            }
            _items[pos] = newItem;
        }

        // CPython heapq _siftup: sink the root then bubble back via _siftdown.
        private void SiftUp(int pos)
        {
            var endPos = _items.Count;
            var startPos = pos;
            var newItem = _items[pos];
            var childPos = 2 * pos + 1;
            while (childPos < endPos)
            {
                var rightPos = childPos + 1;
                if (rightPos < endPos && !(_items[childPos] < _items[rightPos]))
                    childPos = rightPos;
                _items[pos] = _items[childPos];
                pos = childPos;
                childPos = 2 * pos + 1;
            }
            _items[pos] = newItem;
            SiftDown(startPos, pos);
        }
    }
}

/// <summary>Full per-bounce detail for the EXP-023 transcription smoke.</summary>
/// <remarks>Mirrors the columns of <c>xen.avwap.EVENT_SCHEMA</c> so a fixed-Parquet
/// replay can be compared row-for-row against the Python reference events.</remarks>
public sealed record AvwapEventDetail(
    string Domain,
    int RegimeId,
    int Direction,
    int BounceIndexInRegime,
    bool IsPyramidBounce,
    int AnchorIdx,
    DateTime AnchorTime,
    double AnchorPrice,
    DateTime ArmedTime,
    int TriggerIdx,
    DateTime TriggerTime,
    double TriggerClose,
    double AvwapAtTrigger,
    double BandSpreadAtTrigger,
    double UpperBandAtTrigger,
    double LowerBandAtTrigger,
    double FavorableTargetAtTrigger,
    double AdverseTargetAtTrigger,
    int AnchorAgeBars);

public sealed class AvwapBounceModel : ISignalModel
{
    public const double VolumeExponent = 0.75;
    public const double BandMultiplier = 1.0;

    private readonly int _fast;
    private readonly int _slow;
    private readonly List<AvwapEventDetail> _eventDetails = new();

    // Rolling SMA windows (same incremental running-sum convention as
    // MovingAverageCrossoverModel; warmup defined when each queue is full).
    private readonly Queue<double> _fastValues = new();
    private readonly Queue<double> _slowValues = new();
    private double _fastSum;
    private double _slowSum;

    // Global domain-bar index (0-based), matching xen.avwap row indices.
    private int _i;

    // Viable-pivot window since the last regime confirmation, with the buffer of
    // completed bars needed to re-seed the anchored AVWAP without look-ahead.
    private double _segMinLow = double.PositiveInfinity;
    private int _segMinLowIdx = -1;
    private double _segMaxHigh = double.NegativeInfinity;
    private int _segMaxHighIdx = -1;
    private readonly List<SegBar> _segBuffer = new();

    // Regime / anchor / AVWAP state.
    private int _activeRegime;
    private bool _anchorActive;
    private int _anchorIdx = -1;
    private DateTime _anchorTime;
    private double _anchorPrice = double.NaN;
    private int _regimeId;
    private double _cumWp;
    private double _cumW;
    private StreamingMedian _med = new();

    // Bounce arm/trigger state.
    private int _bounceCount;
    private bool _armed;
    private DateTime _armedTime;

    // Position overlay state.
    private int _position;
    private double _favorableTarget = double.NaN;
    private double _adverseTarget = double.NaN;
    private long _tradeSequence;

    public AvwapBounceModel(int fast = 20, int slow = 50, string strategyName = "avwap_baseline")
    {
        if (fast < 1 || slow < 1)
            throw new ArgumentOutOfRangeException(nameof(fast), "MA windows must be >= 1.");
        if (fast >= slow)
            throw new ArgumentException("fast window must be smaller than slow window.");

        _fast = fast;
        _slow = slow;
        StrategyName = strategyName;
    }

    public string StrategyName { get; }

    /// <summary>Per-bounce detail accumulated across the run (transcription smoke).</summary>
    public IReadOnlyList<AvwapEventDetail> EventDetails => _eventDetails;

    public SignalUpdate OnBar(TimeBar bar, string domain)
    {
        var idx = _i;
        var typical = (bar.High + bar.Low + bar.Close) / 3.0;
        var weight = Math.Pow(bar.TickVolume, VolumeExponent);

        var regimeSign = UpdateRegimeSign(bar.Close);

        // Step 1: extend the viable-pivot window with the completed bar.
        if (bar.Low < _segMinLow)
        {
            _segMinLow = bar.Low;
            _segMinLowIdx = idx;
        }
        if (bar.High > _segMaxHigh)
        {
            _segMaxHigh = bar.High;
            _segMaxHighIdx = idx;
        }
        _segBuffer.Add(new SegBar(idx, bar.CloseTime, bar.Low, bar.High, typical, weight));

        var events = new List<SignalEventRecord>();
        var trades = new List<StrategyTradeRecord>();

        // Step 2: position completion BEFORE the regime change resets state. The
        // trend-change boundary is the opposite-regime confirmation bar; targets
        // take precedence at that bar (EXP-022 scan_lifetime).
        MaybeCompletePosition(bar, regimeSign, domain, trades);

        // Step 3: confirmed regime change (or initial establishment).
        var regimeChanged = regimeSign != 0 && regimeSign != _activeRegime;
        if (regimeChanged)
        {
            ConfirmRegime(regimeSign, idx, bar);
            // Signals from the new regime occur only AFTER the confirmation bar
            // (mirrors the `continue` in xen.avwap): emit a flat position only.
            _i++;
            var avwapConfirm = _cumW > 0.0 ? _cumWp / _cumW : double.NaN;
            return BuildUpdate(bar, domain, avwapConfirm, warmup: false, events, trades);
        }

        if (!_anchorActive)
        {
            // No regime confirmed yet: warmup, no AVWAP, flat.
            _i++;
            return BuildUpdate(bar, domain, double.NaN, warmup: true, events, trades);
        }

        // Step 4: advance the anchored AVWAP with the completed bar and run the
        // arm/trigger bounce logic (this bar is strictly after the confirmation).
        _cumWp += typical * weight;
        _cumW += weight;
        if (_cumW <= 0.0)
        {
            _i++;
            return BuildUpdate(bar, domain, double.NaN, warmup: false, events, trades);
        }
        var avwap = _cumWp / _cumW;
        _med.Push(Math.Abs(typical - avwap));

        var triggered = StepArmTrigger(bar.Close, avwap);
        if (triggered)
            HandleTrigger(bar, domain, avwap, idx, events, trades);

        _i++;
        return BuildUpdate(bar, domain, avwap, warmup: false, events, trades);
    }

    // ----------------------------------------------------------------------- //
    // Regime / SMA helpers
    // ----------------------------------------------------------------------- //
    private int UpdateRegimeSign(double close)
    {
        _fastSum = PushWindow(_fastValues, _fastSum, close, _fast);
        _slowSum = PushWindow(_slowValues, _slowSum, close, _slow);
        if (_fastValues.Count < _fast || _slowValues.Count < _slow)
            return 0;
        var fastValue = _fastSum / _fast;
        var slowValue = _slowSum / _slow;
        if (fastValue > slowValue)
            return 1;
        if (fastValue < slowValue)
            return -1;
        return 0;
    }

    private static double PushWindow(Queue<double> values, double total, double value, int window)
    {
        values.Enqueue(value);
        total += value;
        if (values.Count > window)
            total -= values.Dequeue();
        return total;
    }

    private void ConfirmRegime(int regimeSign, int idx, TimeBar bar)
    {
        int anchorIdx;
        double anchorPrice;
        DateTime anchorTime;
        if (regimeSign == 1)
        {
            anchorIdx = _segMinLowIdx;
            anchorPrice = _segMinLow;
            anchorTime = SegTime(anchorIdx);
        }
        else
        {
            anchorIdx = _segMaxHighIdx;
            anchorPrice = _segMaxHigh;
            anchorTime = SegTime(anchorIdx);
        }

        _regimeId++;
        _bounceCount = 0;
        _armed = false;
        _activeRegime = regimeSign;
        _anchorIdx = anchorIdx;
        _anchorPrice = anchorPrice;
        _anchorTime = anchorTime;

        // Re-seed the anchored AVWAP and band window from the chosen pivot through
        // the confirmation bar (all completed; no look-ahead).
        _cumWp = 0.0;
        _cumW = 0.0;
        _med = new StreamingMedian();
        foreach (var seg in _segBuffer)
        {
            if (seg.Idx < anchorIdx)
                continue;
            _cumWp += seg.Typical * seg.Weight;
            _cumW += seg.Weight;
            if (_cumW > 0.0)
                _med.Push(Math.Abs(seg.Typical - _cumWp / _cumW));
        }
        _anchorActive = true;

        // Start the next segment's pivot window at the confirmation bar.
        _segMinLow = bar.Low;
        _segMinLowIdx = idx;
        _segMaxHigh = bar.High;
        _segMaxHighIdx = idx;
        _segBuffer.Clear();
        _segBuffer.Add(new SegBar(idx, bar.CloseTime, bar.Low, bar.High,
            (bar.High + bar.Low + bar.Close) / 3.0, Math.Pow(bar.TickVolume, VolumeExponent)));
    }

    private DateTime SegTime(int idx)
    {
        foreach (var seg in _segBuffer)
        {
            if (seg.Idx == idx)
                return seg.Time;
        }
        throw new InvalidOperationException($"anchor index {idx} not found in segment buffer.");
    }

    // ----------------------------------------------------------------------- //
    // Bounce arm/trigger + position overlay
    // ----------------------------------------------------------------------- //
    private bool StepArmTrigger(double close, double avwap)
    {
        if (_activeRegime == 1)
        {
            if (!_armed)
            {
                if (close < avwap)
                {
                    _armed = true;
                    _armedTime = CurrentTime();
                }
                return false;
            }
            if (close > avwap)
                return true;
            return false;
        }

        // bearish regime
        if (!_armed)
        {
            if (close > avwap)
            {
                _armed = true;
                _armedTime = CurrentTime();
            }
            return false;
        }
        if (close < avwap)
            return true;
        return false;
    }

    private DateTime CurrentTime() => _segBuffer.Count > 0 ? _segBuffer[^1].Time : default;

    private void HandleTrigger(
        TimeBar bar,
        string domain,
        double avwap,
        int idx,
        List<SignalEventRecord> events,
        List<StrategyTradeRecord> trades)
    {
        _bounceCount++;
        var direction = _activeRegime;
        var bandSpread = _med.Median();
        var upper = avwap + BandMultiplier * bandSpread;
        var lower = avwap - BandMultiplier * bandSpread;
        double favorable;
        double adverse;
        if (direction == 1)
        {
            favorable = upper;
            adverse = lower;
        }
        else
        {
            favorable = lower;
            adverse = upper;
        }
        var isPyramid = _bounceCount > 1;

        _eventDetails.Add(new AvwapEventDetail(
            domain, _regimeId, direction, _bounceCount, isPyramid,
            _anchorIdx, _anchorTime, _anchorPrice, _armedTime,
            idx, bar.CloseTime, bar.Close, avwap, bandSpread, upper, lower,
            favorable, adverse, idx - _anchorIdx));

        var previousPosition = _position;
        events.Add(new SignalEventRecord(
            bar.CloseTime,
            domain,
            StrategyName,
            isPyramid ? "bounce_pyramid" : "bounce",
            direction,
            previousPosition,
            avwap));

        if (_position == 0)
        {
            // Enter one unit in the bounce direction; freeze lifetime targets.
            _position = direction;
            _favorableTarget = favorable;
            _adverseTarget = adverse;
            trades.Add(new StrategyTradeRecord(
                bar.CloseTime,
                domain,
                StrategyName,
                direction == 1 ? "enter_long" : "enter_short",
                previousPosition,
                _position,
                bar.Close,
                Math.Abs(_position - previousPosition),
                NextTradeSequence()));
        }
        else
        {
            // Active position: record a non-executed pyramid opportunity (no size add).
            trades.Add(new StrategyTradeRecord(
                bar.CloseTime,
                domain,
                StrategyName,
                "pyramid_skipped",
                _position,
                _position,
                bar.Close,
                0.0,
                NextTradeSequence()));
        }

        _armed = false;
    }

    private void MaybeCompletePosition(
        TimeBar bar,
        int regimeSign,
        string domain,
        List<StrategyTradeRecord> trades)
    {
        if (_position == 0)
            return;

        var direction = _position;
        var favorableHit = direction * (bar.Close - _favorableTarget) >= 0.0;
        var adverseHit = direction * (bar.Close - _adverseTarget) <= 0.0;
        var oppositeRegime = regimeSign != 0 && regimeSign != _activeRegime;

        string? reason = null;
        if (favorableHit)
            reason = "favorable";
        else if (adverseHit)
            reason = "adverse";
        else if (oppositeRegime)
            reason = "trend_change";

        if (reason is null)
            return;

        var previousPosition = _position;
        trades.Add(new StrategyTradeRecord(
            bar.CloseTime,
            domain,
            StrategyName,
            "exit_" + reason,
            previousPosition,
            0,
            bar.Close,
            Math.Abs(previousPosition),
            NextTradeSequence()));
        _position = 0;
        _favorableTarget = double.NaN;
        _adverseTarget = double.NaN;
    }

    private long NextTradeSequence()
    {
        return _tradeSequence++;
    }

    private SignalUpdate BuildUpdate(
        TimeBar bar,
        string domain,
        double avwap,
        bool warmup,
        List<SignalEventRecord> events,
        List<StrategyTradeRecord> trades)
    {
        var signalValue = warmup || double.IsNaN(avwap) ? double.NaN : bar.Close - avwap;
        var position = new SignalPositionRecord(
            bar.CloseTime,
            domain,
            StrategyName,
            _position,
            signalValue,
            bar.Open,
            bar.High,
            bar.Low,
            bar.Close,
            warmup,
            _position == 0);
        return new SignalUpdate(position, events, trades);
    }

    private readonly record struct SegBar(
        int Idx,
        DateTime Time,
        double Low,
        double High,
        double Typical,
        double Weight);
}
