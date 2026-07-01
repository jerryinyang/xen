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
    int RegimeDirection = 0,
    // EXP-006 (CF-MR-002): the causal reversion-completion limit fill price P*_{t-1}
    // on a bar where the resting limit was touched and the position exited intrabar;
    // NaN on every other bar (and for all non-RSI-fade models). Lets the Python
    // adjudication truncate the exit bar's open-to-open return at the realized
    // favourable fill (engine-realized; no Python rct recompute — L-01/P-09).
    double ExitFillPrice = double.NaN,
    // EXP-010 (CF-MR-003 CONC-1): engine-realized limit-entry fill price on a bar
    // where the resting entry limit (rested from t-1) filled intrabar; NaN otherwise
    // and for all non-CONC-1 models. Paired with ExitFillPrice, this lets the Python
    // adjudication assemble the exact-fill realized return with no re-derived edge.
    double EntryFillPrice = double.NaN,
    // EXP-010 causal decision provenance (all rested from t-1; the T2 causal-provenance
    // trace audits these). Anchor = exec-grid-β fitted a[t-1] (the form-2 exit-limit
    // target); Dev = log(price)-a; Z = std-z(dev); Vr/Hl = the VR∧HL selector legs;
    // Beta = the rolling-β on the exec-grid basket. NaN in warmup / non-CONC-1 models.
    double Anchor = double.NaN,
    double Dev = double.NaN,
    double Z = double.NaN,
    double Vr = double.NaN,
    double Hl = double.NaN,
    double Beta = double.NaN);

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
