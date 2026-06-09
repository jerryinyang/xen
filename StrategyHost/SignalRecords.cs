namespace Xen.StrategyHost;

// Generic, model-agnostic position record. The real domain-bar OHLC the strategy
// executed on is emitted alongside the position so the Python suite evaluates on
// the cAlgo's own prices (design.md v2 fence #4), not a re-derived local source.
// Model-specific diagnostics (e.g. MA fast/slow) live in events, not here.
public sealed record SignalPositionRecord(
    DateTime SourceCloseTime,
    string Domain,
    string Strategy,
    int Position,
    double SignalValue,
    double RealOpen,
    double RealHigh,
    double RealLow,
    double RealClose,
    bool Warmup,
    bool IsFlat,
    // EXP-029: per-bar regime state, serialized as already-computed model state so
    // the Python parity harness can rebuild the regime LUT / trend-change boundaries
    // without re-deriving the AVWAP signal. Default sentinels for non-regime models
    // (MA/Donchian) keep their emission unchanged.
    int RegimeId = -1,
    int RegimeDirection = 0);

public sealed record SignalEventRecord(
    DateTime SourceCloseTime,
    string Domain,
    string Strategy,
    string EventType,
    int Position,
    int PreviousPosition,
    double SignalValue);

public sealed record StrategyTradeRecord(
    DateTime SourceCloseTime,
    string Domain,
    string Strategy,
    string Action,
    int PreviousPosition,
    int Position,
    double Price,
    double PositionDelta,
    long TradeSequence = 0);

public sealed record SignalUpdate(
    SignalPositionRecord Position,
    IReadOnlyList<SignalEventRecord> Events,
    IReadOnlyList<StrategyTradeRecord> Trades)
{
    public static SignalUpdate PositionOnly(SignalPositionRecord position)
    {
        return new SignalUpdate(position, Array.Empty<SignalEventRecord>(), Array.Empty<StrategyTradeRecord>());
    }
}
