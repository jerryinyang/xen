"""A6 acceptance discriminators and their outcome labels (INFR-018 HYP-I3).

Source ``SIGNAL-SIGNED.md`` A6 and Phase 2: acceptance at a boundary is defined
from closes, follow-through and value migration, *"with signed flow admitted as
a candidate component of the discriminator … to be raced with the price-only
definitions in Phase 2, not presumed better."* The winner is frozen and
inherited everywhere downstream, which is why this is the most-ordered item in
the source document.

Two structural rules are enforced here rather than assumed:

**One shared qualifying window.** Every candidate reads its rule inside the same
fixed 30-minute post-poke window, so the outcome window opens at the same
instant for all of them. Letting each candidate define its own window would
confound the race with horizon: a rule reading 30 bars would be compared against
a rule reading 1 bar on a *different* outcome distribution, and the winner would
partly be "the candidate whose horizon happened to suit the label".

**The qualifying window strictly precedes the outcome window**, asserted by
:func:`assert_windows_disjoint`. This is the item's most leak-prone seam: a
discriminator that could see one bar of its own outcome would win by
construction.

No expectancy, cost, direction claim or grade is emitted from these labels. They
exist solely to select a classifier (design.md §0).
"""

from __future__ import annotations

from dataclasses import dataclass

import polars as pl

#: Shared post-poke qualifying window, minutes. Fixed across candidates so the
#: outcome window is identical for every rule in the race.
QUALIFY_MINUTES = 30

#: Poke depths raced, as fractions of IB width (source S3 "a poke >= delta").
POKE_DELTAS: tuple[float, ...] = (0.0, 0.05, 0.10)

LABEL_ACCEPTANCE = "ACCEPTANCE"
LABEL_TRAP = "TRAP"
LABEL_UNRESOLVED = "UNRESOLVED"


@dataclass(frozen=True)
class Discriminator:
    """One pre-registered A6 candidate.

    Attributes
    ----------
    disc_id :
        Identifier written into the frozen race grid and the registry pin.
    family :
        ``D1``…``D4`` price-only, ``D5``…``D8`` their flow-augmented twins.
    flow_augmented :
        Whether the rule additionally requires same-direction net delta with a
        positive **seasonal residual** (A5 — never a raw delta number).
    params :
        Family-specific parameters.
    """

    disc_id: str
    family: str
    flow_augmented: bool
    params: dict


def race_grid() -> list[Discriminator]:
    """The frozen candidate enumeration (design.md §4.2).

    Written to ``results/a6_race_grid.json`` and hashed **before** execution; QA
    diffs the executed set against it. Adding a cell afterwards is a design
    amendment carrying a direction (L-23), not a code change.
    """
    grid: list[Discriminator] = []
    for flow in (False, True):
        tag = "D5" if flow else "D1"
        for n in (1, 2, 3):
            grid.append(Discriminator(f"{tag}-n{n}{'-flow' if flow else ''}", "D1", flow, {"n": n}))
        tag = "D6" if flow else "D2"
        grid.append(Discriminator(f"{tag}-ft{'-flow' if flow else ''}", "D2", flow, {}))
        tag = "D7" if flow else "D3"
        for w in (15, 30):
            grid.append(Discriminator(f"{tag}-w{w}{'-flow' if flow else ''}", "D3", flow, {"w": w}))
        tag = "D8" if flow else "D4"
        for tau in (0.50, 0.75):
            for w in (15, 30):
                grid.append(
                    Discriminator(
                        f"{tag}-t{int(tau*100)}-w{w}{'-flow' if flow else ''}",
                        "D4", flow, {"tau": tau, "w": w},
                    )
                )
    return grid


def assert_windows_disjoint(events: pl.DataFrame) -> None:
    """Raise unless every outcome window opens strictly after its qualifying window.

    The one check that makes the HYP-I3 race meaningful. A single overlapping
    bar would let a discriminator read its own answer.

    Both windows are half-open: the qualifying window is ``[poke_ts, qualify_end)``
    and the outcome window is ``[outcome_start, session_end)``. Equality is
    therefore the correct adjacent-and-disjoint construction — no bar belongs to
    both — so the comparison is strict. QA run 1 (I-1) caught the ``<=`` form,
    which rejected every correctly-built event and stopped Phase 2 dead.
    """
    if events.height == 0:
        return
    bad = events.filter(pl.col("outcome_start") < pl.col("qualify_end")).height
    if bad:
        raise RuntimeError(
            f"WINDOW OVERLAP: {bad} events have outcome_start < qualify_end — the "
            "discriminator could see its own outcome; the race would be vacuous"
        )


def find_pokes(
    bars: pl.DataFrame, sessions: pl.DataFrame, delta_frac: float
) -> pl.DataFrame:
    """First boundary poke per session, with its qualifying and outcome windows.

    A poke is the first bar whose **High** exceeds ``ib_high + delta*ib_width``
    (or whose **Low** falls below ``ib_low − delta*ib_width``) — an extremum
    touch, not a close. That is deliberate and is the B-4 identity: the source's
    S3 premise is *"a poke beyond a boundary"*, i.e. price traded there. The
    close-based question is precisely what the discriminator is being raced to
    answer, so conditioning the event on a close would assume the answer.

    Parameters
    ----------
    bars :
        One symbol's fenced bars with ``anchor_ts`` already joined.
    sessions :
        Output of :func:`xen.sigbar.sessions.session_breaks` (IB per session).
    delta_frac :
        Poke depth as a fraction of IB width.

    Returns
    -------
    polars.DataFrame
        One row per poked session: ``anchor_ts, poke_ts, poke_side, poke_extreme,
        ib_high, ib_low, ib_width, qualify_end, outcome_start``.
    """
    ib = sessions.select("anchor_ts", "ib_high", "ib_low", "ib_width", "session_end")
    joined = bars.join(ib, on="anchor_ts", how="inner").filter(pl.col("ib_width") > 0)
    thresh = joined.with_columns(
        (pl.col("ib_high") + delta_frac * pl.col("ib_width")).alias("up_level"),
        (pl.col("ib_low") - delta_frac * pl.col("ib_width")).alias("dn_level"),
    ).filter(pl.col("mins_since") >= pl.col("ib_minutes"))

    poked = thresh.with_columns(
        pl.when(pl.col("High") > pl.col("up_level"))
        .then(pl.lit(1))
        .when(pl.col("Low") < pl.col("dn_level"))
        .then(pl.lit(-1))
        .otherwise(pl.lit(0))
        .alias("poke_side")
    ).filter(pl.col("poke_side") != 0)

    first = (
        poked.sort("OpenTime")
        .group_by("anchor_ts")
        .agg(
            pl.col("OpenTime").first().alias("poke_ts"),
            pl.col("poke_side").first().alias("poke_side"),
            pl.when(pl.col("poke_side").first() == 1)
            .then(pl.col("High").first())
            .otherwise(pl.col("Low").first())
            .alias("poke_extreme"),
            pl.col("session_end").first().alias("session_end"),
            pl.col("ib_high").first().alias("ib_high"),
            pl.col("ib_low").first().alias("ib_low"),
            pl.col("ib_width").first().alias("ib_width"),
        )
        .with_columns(
            (pl.col("poke_ts") + pl.duration(minutes=QUALIFY_MINUTES)).alias("qualify_end")
        )
        .with_columns(pl.col("qualify_end").alias("outcome_start"))
    )
    # Drop pokes whose qualifying window would run past the session end — their
    # rule input is truncated, so they are not comparable events.
    first = first.filter(pl.col("qualify_end") < pl.col("session_end"))
    assert_windows_disjoint(first)
    return first


def _bars_join_pokes(bars: pl.DataFrame, pokes: pl.DataFrame, poke_cols: list[str]) -> pl.DataFrame:
    """Inner-join poke metadata onto bars without bar columns shadowing poke columns.

    ``attach_sessions`` leaves ``session_end`` (and related session fields) on the
    bar frame. A naive join of poke columns that share those names lets polars
    keep the LEFT (bars) copy and suffix the poke copy to ``*_right``, so
    ``pl.col("session_end")`` silently resolves to the **bars'** value. On a
    path-swapped frame the bars carry the donor session's end while the poke
    carries the target's — the outcome filter then empties half the events as a
    monotone function of calendar time (INFR-018 QA I-56). Dropping the
    colliding bar-side columns makes every joined name mean the poke's value.
    """
    poke = pokes.select(poke_cols)
    collide = [c for c in poke.columns if c != "anchor_ts" and c in bars.columns]
    base = bars.drop(collide) if collide else bars
    return base.join(poke, on="anchor_ts", how="inner")


def evaluate_discriminator(
    bars: pl.DataFrame,
    pokes: pl.DataFrame,
    disc: Discriminator,
    *,
    read_past_qualify: bool = False,
) -> pl.DataFrame:
    """Apply one candidate rule inside the shared qualifying window.

    Parameters
    ----------
    read_past_qualify :
        When True, the rule may read bars past ``qualify_end`` up to
        ``session_end`` (windowed families still apply their own ``w`` cap).
        **Only** for the path-swap tripwire's deliberately leaky positive
        control (QA run 2, I-30). Real race candidates keep the default False.

    Returns
    -------
    polars.DataFrame
        ``anchor_ts, says_accept`` (bool) for every poke event.
    """
    poke_cols = ["anchor_ts", "poke_ts", "poke_side", "qualify_end", "ib_high", "ib_low"]
    if read_past_qualify:
        if "session_end" not in pokes.columns:
            raise RuntimeError(
                "read_past_qualify requires session_end on pokes (leak-probe only)"
            )
        poke_cols = poke_cols + ["session_end"]
        window_end = pl.col("session_end")
    else:
        window_end = pl.col("qualify_end")

    q = (
        _bars_join_pokes(bars, pokes, poke_cols)
        .filter((pl.col("OpenTime") >= pl.col("poke_ts")) & (pl.col("OpenTime") < window_end))
        .with_columns(
            # "beyond" is signed by the poke direction so up and down pokes share one rule.
            pl.when(pl.col("poke_side") == 1)
            .then(pl.col("Close") > pl.col("ib_high"))
            .otherwise(pl.col("Close") < pl.col("ib_low"))
            .alias("close_beyond")
        )
        .sort("OpenTime")
    )

    fam, p = disc.family, disc.params
    if fam == "D1":
        # n consecutive closes beyond, anywhere in the qualifying window.
        agg = (
            q.with_columns(
                (~pl.col("close_beyond")).cum_sum().over("anchor_ts").alias("run_id")
            )
            .filter(pl.col("close_beyond"))
            .group_by("anchor_ts", "run_id")
            .agg(pl.len().alias("run_len"))
            .group_by("anchor_ts")
            .agg(pl.col("run_len").max().alias("max_run"))
        )
        base = agg.with_columns((pl.col("max_run") >= p["n"]).alias("rule_hit")).select(
            "anchor_ts", "rule_hit"
        )
    elif fam == "D2":
        # close beyond, then the NEXT bar's close extends further beyond.
        agg = (
            q.with_columns(
                pl.when(pl.col("poke_side") == 1)
                .then(pl.col("Close"))
                .otherwise(-pl.col("Close"))
                .alias("signed_close")
            )
            .with_columns(
                (
                    pl.col("close_beyond")
                    & pl.col("close_beyond").shift(1).over("anchor_ts")
                    & (pl.col("signed_close") > pl.col("signed_close").shift(1).over("anchor_ts"))
                ).alias("ft")
            )
            .group_by("anchor_ts")
            .agg(pl.col("ft").any().alias("rule_hit"))
        )
        base = agg
    elif fam == "D3":
        # Proxy-value migration: the window's VOLUME-WEIGHTED MEDIAN typical price
        # moves beyond the edge.
        #
        # The median, not a mean, and the distinction is the point of the rule: a
        # single wide vacuum bar drags a volume-weighted mean beyond the edge
        # without any value having migrated there, which is exactly the regime D3
        # exists to tell apart from genuine acceptance. QA run 1 (I-9) found a
        # mean here, justified by the claim that a weighted median "would need
        # per-level placement". That claim is wrong: sorting BARS by typical
        # price and taking the volume-cumulative 50% crossing places nothing
        # inside any bar, so card ban 2 is untouched. This is a per-BAR aggregate
        # throughout, uses no §2.1 kernel, and attributes no volume to a level.
        w = p["w"]
        agg = (
            q.filter(pl.col("OpenTime") < pl.col("poke_ts") + pl.duration(minutes=w))
            .with_columns(((pl.col("High") + pl.col("Low") + pl.col("Close")) / 3).alias("tp"))
            .sort(["anchor_ts", "tp"])
            .with_columns(
                pl.col("Volume").cum_sum().over("anchor_ts").alias("cum_v"),
                pl.col("Volume").sum().over("anchor_ts").alias("tot_v"),
            )
            .filter(pl.col("cum_v") >= 0.5 * pl.col("tot_v"))
            .group_by("anchor_ts")
            .agg(
                pl.col("tp").first().alias("vw_median"),
                pl.col("poke_side").first().alias("side"),
                pl.col("ib_high").first().alias("ibh"),
                pl.col("ib_low").first().alias("ibl"),
            )
            .with_columns(
                pl.when(pl.col("side") == 1)
                .then(pl.col("vw_median") > pl.col("ibh"))
                .otherwise(pl.col("vw_median") < pl.col("ibl"))
                .alias("rule_hit")
            )
        )
        base = agg.select("anchor_ts", "rule_hit")
    elif fam == "D4":
        tau, w = p["tau"], p["w"]
        agg = (
            q.filter(pl.col("OpenTime") < pl.col("poke_ts") + pl.duration(minutes=w))
            .group_by("anchor_ts")
            .agg(pl.col("close_beyond").mean().alias("frac"))
            .with_columns((pl.col("frac") >= tau).alias("rule_hit"))
        )
        base = agg.select("anchor_ts", "rule_hit")
    else:
        raise ValueError(f"unknown discriminator family {fam!r}")

    if not disc.flow_augmented:
        return base.with_columns(pl.col("rule_hit").alias("says_accept")).select(
            "anchor_ts", "says_accept"
        )

    # Flow augmentation — TWO conditions, and this is why A5 fits the two delta
    # baselines SEPARATELY (|Δ| scales with volume; Δ/V does not):
    #   (a) DIRECTION, from the Δ/V baseline: the mean `delta_ratio_resid` over
    #       the qualifying bars leans in the POKE's direction — the flow is more
    #       buy-side than this minute-of-week normally is, for an up-poke, and
    #       more sell-side than normal for a down-poke. This is the source's
    #       "acceptance accompanied by same-direction Δ vs against it", stated
    #       against the seasonal norm rather than against zero.
    #   (b) MAGNITUDE, from the |Δ| baseline: `delta_abs_resid > 0` — there was
    #       more net aggression than this minute-of-week normally carries. This
    #       leg is direction-free, so it cannot invert between sides.
    #
    # QA run 1 (I-10) read design §4.2's `delta_ratio_resid > 0` literally and
    # found the down-poke case inverted. The literal reading is the one that is
    # wrong: written unsigned it silently assumes an up-poke, and would require a
    # down-poke to show ABOVE-normal BUYING to qualify as same-direction flow.
    # Signing the residual by the poke side is what makes the rule mean the same
    # thing on both sides. Design §4.2 is corrected to match (AMENDMENT-3).
    #
    # A5 is intact throughout: both legs read residuals, never a raw Δ number.
    need = ("delta_ratio_resid", "delta_abs_resid")
    missing = [c for c in need if c not in q.columns]
    if missing:
        raise RuntimeError(
            f"flow-augmented discriminator requires {missing} from the frozen A5 baselines; "
            "a raw delta threshold is barred (A5 / design.md hard constraints)"
        )
    flow = (
        q.group_by("anchor_ts")
        .agg(
            pl.col("delta_ratio_resid").mean().alias("ratio_resid_mean"),
            pl.col("delta_abs_resid").mean().alias("abs_resid_mean"),
            pl.col("poke_side").first().alias("side"),
        )
        .with_columns(
            (
                ((pl.col("ratio_resid_mean") * pl.col("side")) > 0)  # (a) direction vs baseline
                & (pl.col("abs_resid_mean") > 0)                      # (b) elevated aggression
            ).alias("flow_ok")
        )
        .select("anchor_ts", "flow_ok")
    )
    return (
        base.join(flow, on="anchor_ts", how="left")
        .with_columns((pl.col("rule_hit") & pl.col("flow_ok").fill_null(False)).alias("says_accept"))
        .select("anchor_ts", "says_accept")
    )


def label_outcomes(bars: pl.DataFrame, pokes: pl.DataFrame) -> pl.DataFrame:
    """Assign ACCEPTANCE / TRAP / UNRESOLVED from the outcome window.

    These labels are the ground truth the whole HYP-I3 race is scored against and
    the frozen A6 rule is whichever candidate best predicts them, so each carries
    **both** of its clauses (source S3 and S4 test specs; design §4.3). QA run 1
    (I-15) found both qualifying clauses missing and ``poke_extreme`` unused:

    - ``ACCEPTANCE`` — price travels >= 1 IB width further beyond the edge
      **before returning inside the IB range**. Without the second clause an
      event that round-tripped back inside and only later ran would count as
      acceptance, which is the opposite reading.
    - ``TRAP`` — price returns inside and touches the **opposite** IB edge
      **before exceeding the poke extreme**. Without the second clause an event
      that first pushed past its own poke extreme still counts as a trap, even
      though S3 treats a second poke beyond the first extreme as the trap's
      explicit invalidation ("Exit; never average").

    All four candidate instants are first-passage times over the outcome window,
    resolved in one pass, so an event cannot be double-labelled. Neither
    resolving by session end is ``UNRESOLVED`` — reported with its rate, never
    dropped and never folded into a class (B-5).
    """
    poke_cols = [
        "anchor_ts", "outcome_start", "session_end", "poke_side", "poke_extreme",
        "ib_high", "ib_low", "ib_width",
    ]
    o = (
        _bars_join_pokes(bars, pokes, poke_cols)
        .filter(
            (pl.col("OpenTime") >= pl.col("outcome_start"))
            & (pl.col("OpenTime") < pl.col("session_end"))
        )
        .with_columns(
            pl.when(pl.col("poke_side") == 1)
            .then(pl.col("ib_high") + pl.col("ib_width"))
            .otherwise(pl.col("ib_low") - pl.col("ib_width"))
            .alias("accept_level"),
            pl.when(pl.col("poke_side") == 1)
            .then(pl.col("ib_low"))
            .otherwise(pl.col("ib_high"))
            .alias("trap_level"),
            # "inside the IB range" for an up-poke means back below the IB high.
            pl.when(pl.col("poke_side") == 1)
            .then(pl.col("ib_high"))
            .otherwise(pl.col("ib_low"))
            .alias("reentry_level"),
        )
        .with_columns(
            pl.when(pl.col("poke_side") == 1)
            .then(pl.col("High") >= pl.col("accept_level"))
            .otherwise(pl.col("Low") <= pl.col("accept_level"))
            .alias("hit_accept"),
            pl.when(pl.col("poke_side") == 1)
            .then(pl.col("Low") <= pl.col("trap_level"))
            .otherwise(pl.col("High") >= pl.col("trap_level"))
            .alias("hit_trap"),
            pl.when(pl.col("poke_side") == 1)
            .then(pl.col("Low") <= pl.col("reentry_level"))
            .otherwise(pl.col("High") >= pl.col("reentry_level"))
            .alias("hit_reentry"),
            # The poke extreme exceeded — S3's own invalidation of a trap.
            pl.when(pl.col("poke_side") == 1)
            .then(pl.col("High") > pl.col("poke_extreme"))
            .otherwise(pl.col("Low") < pl.col("poke_extreme"))
            .alias("hit_beyond_poke"),
        )
        .sort("OpenTime")
    )
    res = o.group_by("anchor_ts").agg(
        pl.col("OpenTime").filter(pl.col("hit_accept")).min().alias("t_accept"),
        pl.col("OpenTime").filter(pl.col("hit_trap")).min().alias("t_trap"),
        pl.col("OpenTime").filter(pl.col("hit_reentry")).min().alias("t_reentry"),
        pl.col("OpenTime").filter(pl.col("hit_beyond_poke")).min().alias("t_beyond_poke"),
    )

    # A null first-passage time means "never happened", which must compare as
    # LATER than any real instant — not as earlier, which is how a null sorts.
    far = pl.datetime(2262, 1, 1)
    t_acc = pl.col("t_accept").fill_null(far)
    t_trp = pl.col("t_trap").fill_null(far)
    t_re = pl.col("t_reentry").fill_null(far)
    t_bp = pl.col("t_beyond_poke").fill_null(far)

    return res.with_columns(
        # ACCEPTANCE qualifies only if the run happened BEFORE re-entry.
        (pl.col("t_accept").is_not_null() & (t_acc < t_re)).alias("accept_ok"),
        # TRAP qualifies only if the opposite edge was touched BEFORE the poke
        # extreme was exceeded.
        (pl.col("t_trap").is_not_null() & (t_trp < t_bp)).alias("trap_ok"),
    ).with_columns(
        pl.when(~pl.col("accept_ok") & ~pl.col("trap_ok"))
        .then(pl.lit(LABEL_UNRESOLVED))
        .when(pl.col("accept_ok") & ~pl.col("trap_ok"))
        .then(pl.lit(LABEL_ACCEPTANCE))
        .when(pl.col("trap_ok") & ~pl.col("accept_ok"))
        .then(pl.lit(LABEL_TRAP))
        .when(t_acc < t_trp)
        .then(pl.lit(LABEL_ACCEPTANCE))
        .otherwise(pl.lit(LABEL_TRAP))
        .alias("label")
    ).select(
        "anchor_ts", "label", "t_accept", "t_trap", "t_reentry", "t_beyond_poke",
        "accept_ok", "trap_ok",
    )


def separation(events: pl.DataFrame) -> dict:
    """``S = P(ACCEPTANCE | says accept) − P(ACCEPTANCE | says reject)``.

    Invariant to the accept/reject call rate, which differs by an order of
    magnitude across candidates — a raw accuracy would simply reward whichever
    rule matched the base rate. The base rate is returned alongside so the lift
    is always read against the matched unconditional rate (source §6.3).
    """
    res = events.filter(pl.col("label") != LABEL_UNRESOLVED)
    n = res.height
    if n == 0:
        return {"S": None, "n": 0, "base_rate": None, "call_rate": None}
    is_acc = pl.col("label") == LABEL_ACCEPTANCE
    yes = res.filter(pl.col("says_accept"))
    no = res.filter(~pl.col("says_accept"))
    if yes.height == 0 or no.height == 0:
        return {
            "S": None, "n": n, "base_rate": res.select(is_acc.mean()).item(),
            "call_rate": yes.height / n, "degenerate": True,
        }
    p_yes = yes.select(is_acc.mean()).item()
    p_no = no.select(is_acc.mean()).item()
    return {
        "S": p_yes - p_no,
        "n": n,
        "n_yes": yes.height,
        "n_no": no.height,
        "p_accept_given_yes": p_yes,
        "p_accept_given_no": p_no,
        "base_rate": res.select(is_acc.mean()).item(),
        "call_rate": yes.height / n,
        "unresolved_rate": 1 - n / max(events.height, 1),
    }
