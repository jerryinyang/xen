# Contaminated modules — do NOT re-import into the live tree

`xen/intrabar_fill.py` and `xen/mean_reversion.py` carry the L-01 one-bar look-ahead
(`rct_target[di]` favourable-index leak) that shipped a false `DEPLOYABLE_CONFIRMED`
(CF-MR-001, retracted). Retained for the post-mortem record only. Future intrabar-fill /
favourable-limit logic must be re-derived causal (`rct_target[di-1]`) and generated in the
cTrader engine per Chapter-02 policy — not in a vectorized Python module.
See `docs/knowledge-base/lessons-and-amendments.md` L-01.
