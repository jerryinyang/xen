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
    double Beta = double.NaN,
    // EXP-014 (CF-MR-004 HYP-002) — faithful full-exit cross-instrument MR. Per-4h-bar rich
    // state so the Python audit can quantify every leg (§11 emission spec). All ≤ t-1; forming
    // 4h OHLC never read. Default sentinels keep every other model's emission byte-unchanged.
    // Arming state (flat-or-armable bar): base-level (z*=2.0) resting-bracket band prices + σ +
    // spread window mean. Deeper ladder levels (extend) live in cis_trades per fill, not per bar.
    double ArmSellPrice = double.NaN,   // exp(anchorLog + Z*σ) armed upper band (short entry)
    double ArmBuyPrice = double.NaN,    // exp(anchorLog − Z*σ) armed lower band (long entry)
    double Sigma = double.NaN,          // rolling spread σ (band half-width in log units)
    double SpreadMean = double.NaN,     // rolling spread window mean (form-1 reference for S6/7/8)
    // Basket-feed validity (min-mate-count rule, design §4): a basket bar is valid only if the
    // full predeclared mate set aligned; a gap → armed no new order that bar (β/anchor fixed).
    int MateCount = -1,                 // resolved mates used this bar (-1 non-CIS)
    int MateExpected = -1,              // full predeclared mate membership
    bool MateGap = false,               // MateCount < MateExpected → basket bar invalid (no new arm)
    // Conditioner state per bar (informative slices, L-12) — trend on the TRADED 4h instrument,
    // vol regime on the spread-σ history. Emitted; Python derives trend/vol variants as slices.
    double TrendZ = double.NaN,         // (EMA20 − EMA50)/σ_close(WZ)
    int TrendDir = 0,                   // sign(TrendZ)
    int VolRegime = -1,                 // 0 low / 1 mid / 2 high spread-σ tercile (-1 warmup)
    // Breach-skip disclosure (design §5 breach policy): a band already through the ≤t-1 confirmed
    // close is not chased (predeclared test); the live bid/ask skip is recorded additionally.
    bool BreachSkipSell = false,        // sell band ≤ ≤t-1 close (would arm through) → skipped
    bool BreachSkipBuy = false,         // buy band ≥ ≤t-1 close → skipped
    bool LiveBreachSkipSell = false,    // sell band ≤ live Bid at arm time (disclosure)
    bool LiveBreachSkipBuy = false,     // buy band ≥ live Ask at arm time (disclosure)
    // Concurrent-leg aggregate state (multi-leg engine): open legs held during the bar + summed
    // intra-position mark-to-market (L-09 — required for the per-bar referee + comparability).
    int OpenLegs = 0,                   // concurrent open legs during this bar
    double MtmBps = double.NaN,         // Σ_leg dir·(RealClose − entryFill)/entryFill·1e4 (unrealized)
    double RefreshedTp = double.NaN,    // current (refreshed) form-2 TP price for the active side
    bool Form1Any = false);             // any open leg's spread reverted through mean this bar

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

// EXP-014 (CF-MR-004 HYP-002) — per-closed-trade record. One row per leg round-trip so the
// Python audit can split P&L by exit reason / ladder level / trend bucket / vol regime and
// separate form-1 event-reversion from form-2 static-limit fills (finding C fix). Gross bps
// (price-based, engine-realized fills); the referee cost map is applied in Python (§8, L-02).
// Written to cis_trades.parquet (empty for every non-CIS model).
public sealed record CisTradeRecord(
    DateTime SourceCloseTime,   // exit-bar 4h CloseTime (fence-asserted)
    string Domain,
    string Strategy,
    string Series,
    DateTime EntryTime,
    DateTime ExitTime,
    int Direction,              // +1 long / −1 short
    int LadderLevel,            // 0 = z*=2.0, 1 = 2.5, 2 = 3.0 (extend); 0 otherwise
    double EntryFillPrice,      // engine-realized limit fill
    double ExitFillPrice,       // engine-realized (limit for form-2; market for form-1; last mark for open_at_end)
    string ExitReason,          // form1_reversion | form2_favorable_limit | open_at_end (EXP-014b: no horizon)
    int BarsHeld,
    double RealizedBps,         // Direction·(ExitFill − EntryFill)/EntryFill·1e4 (GROSS; NaN-safe for censored)
    double EntryZ,
    double EntrySpread,
    double EntryAnchorPrice,
    double EntrySigma,
    double ExitAnchorPrice,
    double ExitSpread,
    double EntryTrendZ,
    int EntryTrendDir,
    int EntryVolRegime,
    double FixedExitPrice,      // EXP-014b: entry-referential locked TP = EntryFill·exp(dir·band) (NaN if trailing)
    double MaeBps,              // EXP-014b: max ADVERSE excursion over the hold (dir-signed min, bps)
    double MfeBps,              // EXP-014b: max FAVORABLE excursion over the hold (dir-signed max, bps)
    int Censored,               // EXP-014b: 1 = open_at_end (excluded from realized-P&L referee), 0 = completed
    string LegSymbol = "",      // HYP-003 both-leg: the leg's traded symbol ("" for single-leg = traded instrument)
    long SpreadPositionId = 0,  // HYP-003 both-leg: groups the N+1 legs of one spread position (0 for single-leg)
    double SlPrice = double.NaN, // HYP-004 E2/E3: frozen outward SL o±D (NaN otherwise); FixedExitPrice = frozen TP under E1-E3
    int HorizonBars = 0);       // HYP-004 E3: frozen ⌈3·HL_entry⌉ time-stop horizon, cap 48 (0 = none)

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
