namespace Xen.StrategyHost;

// EXP-010 (CF-MR-003 CONC-1) — the S5_SPREAD basket feed abstraction.
//
// Isolates the multi-symbol coupling: the model asks for the equal-weight mean of the
// class-mate log-Close (class minus self) at a traded exec-bar CloseTime, and the concrete
// feed resolves it CAUSALLY — using only mate bars whose CloseTime <= the requested time.
// Production (Xen.cs) implements this over cAlgo `MarketData.GetBars(TimeFrame.Hour, mate)`
// (the XRSI-V1 multi-symbol pattern); tests implement it over in-memory arrays. Keeping the
// model free of cAlgo.API types makes the edge logic offline-testable.
public interface IBasketFeed
{
    // Equal-weight mean of the mates' log(Close) using only mate bars with CloseTime <= at.
    // Returns NaN when no mate has a closed bar at/before `at` (basket UNPOWERED -> flat).
    double LogPriceAt(DateTime at);
}
