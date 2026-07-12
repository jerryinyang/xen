//! XENA oracle event-fold kernel (INFR-007, restructured INFR-008) — byte-identical Rust
//! port of the sequential state-update loop in `xen.xena.oracle.evaluate`.
//!
//! Scope (proposal `xena-infr-update.md`): ONLY the fold. Python keeps parquet loading,
//! per-trade mark schedules, segment clipping/censoring, event construction, all sorting
//! (numpy remains the tie-break authority), `grid_increments`, `bootstrap_F`, and every
//! search/certify/gate layer. This kernel receives pre-sorted flat arrays, replays the
//! exact heap semantics of the Python loop, and returns the equity path + ledger arrays.
//!
//! Float-identity rules:
//! * f64 everywhere; no f32 intermediates.
//! * Exact operation order of the Python implementation, including accumulation order
//!   (`equity += money` in heap-pop order, `gross += money` in mark-schedule order).
//! * No `mul_add`/FMA, no reassociation, no SIMD reductions over accumulators.
//! * Timestamps are i64 nanoseconds end-to-end.
//!
//! Event-order parity (INFR-008 k-way merge): the Python heap holds tuples
//! `(t, phase, cid, k_or_seq, payload)` with phase mark(0) < exit(1) < entry(2), cid
//! compared as a string, and a global push counter `seq` for mark tiebreaks. All keys are
//! unique, so heapq pop order is exactly the total tuple order — which means the pop
//! sequence is a deterministic merge of already-sorted streams and no monolithic heap is
//! needed:
//! * entries, sorted once by `(t, rank, k)`, are consumed through a single cursor
//!   (phase ENTRY is the largest, so the entry key is `(t, 2, rank, k)`);
//! * each admitted trade's marks are pushed in ascending `(t, seq)` order (schedule
//!   order, seq strictly increasing), and its exit key `(exit_t, 1, rank, k)` sorts
//!   after its last mark `(exit_t <= last mark t is impossible — exit_t == last mark t
//!   and phase 1 > 0)` — so ONE cursor per open trade walks marks-then-exit in key order.
//! * a small BinaryHeap holds one cursor per open trade; each pop compares the heap top
//!   against the next entry key. Same total order over the same unique keys ⇒ identical
//!   pop sequence ⇒ identical float accumulation order ⇒ bitwise-identical output,
//!   re-proven by the pinned parity corpus.
//! `cid` is replaced by its rank in the sorted included-id list (order-isomorphic to the
//! string compare) and the same `seq` counter values are replayed (assigned per mark at
//! admission time, in schedule order).
//!
//! GIL: the fold runs under `Python::detach` (INFR-008) — pure computation over borrowed
//! slices, no Python objects touched — enabling thread-parallel evaluations (certification
//! folds, permutation batteries) in one process. No numeric change.

use numpy::{IntoPyArray, PyReadonlyArray1};
use pyo3::exceptions::PyValueError;
use pyo3::prelude::*;
use std::cmp::Ordering;
use std::collections::BinaryHeap;

const RECONCILE_TOL_MONEY: f64 = 1e-6; // relative to initial equity (mirror of oracle.py)

const PH_MARK: u8 = 0;
const PH_EXIT: u8 = 1;
const PH_ENTRY: u8 = 2;

type Key = (i64, u8, u32, i64); // (t, phase, rank, seq_or_k) — Python's heap tuple order

/// One open trade: walks its time-sorted mark schedule, then its exit event.
/// `key` is the cursor's CURRENT event key, kept in sync on every advance.
struct Cursor {
    key: Key,
    i: usize,     // trade index into the flat arrays
    j: usize,     // next mark index (mark_off[i] <= j < m1), or == m1 when at exit
    m0: usize,
    m1: usize,
    seq0: i64,    // seq of mark m0 (marks m0+j get seq0+j — replayed Python counter)
    exit_t: i64,
    exit_k: i64,  // trade_k — Python's exit tiebreak
}

impl Cursor {
    fn advance(&mut self, mark_t: &[i64]) -> bool {
        // move past the current event; returns false when exhausted (exit popped)
        if self.j < self.m1 {
            self.j += 1;
            self.key = if self.j < self.m1 {
                (mark_t[self.j], PH_MARK, self.key.2, self.seq0 + (self.j - self.m0) as i64)
            } else {
                (self.exit_t, PH_EXIT, self.key.2, self.exit_k)
            };
            true
        } else {
            false
        }
    }
}

impl PartialEq for Cursor {
    fn eq(&self, other: &Self) -> bool {
        self.key == other.key
    }
}
impl Eq for Cursor {}
impl Ord for Cursor {
    fn cmp(&self, other: &Self) -> Ordering {
        other.key.cmp(&self.key) // reversed: max-heap → heapq min-pop order
    }
}
impl PartialOrd for Cursor {
    fn partial_cmp(&self, other: &Self) -> Option<Ordering> {
        Some(self.cmp(other))
    }
}

struct FoldOut {
    eq_t: Vec<i64>,
    eq_v: Vec<f64>,
    adm_idx: Vec<i64>,
    adm_exit_t: Vec<i64>,
    adm_units: Vec<f64>,
    adm_risk: Vec<f64>,
    adm_gross: Vec<f64>,
    adm_cost: Vec<f64>,
    rej_idx: Vec<i64>,
    rej_t: Vec<i64>,
    rej_risk: Vec<f64>,
    rej_open: Vec<f64>,
    rej_cap: Vec<f64>,
}

#[allow(clippy::too_many_arguments)]
fn fold_impl(
    entry_t: &[i64],
    trade_k: &[i64],
    cand_rank: &[u32],
    direction: &[f64],
    entry_price: &[f64],
    stop_dist: &[f64],
    mark_off: &[i64],
    mark_t: &[i64],
    unit_inc: &[f64],
    weight: &[f64],
    cost_bps: &[f64],
    money_per_unit: &[f64],
    initial_equity: f64,
    risk_per_position: f64,
    r_max: f64,
    charge_costs: bool,
) -> Result<FoldOut, String> {
    let n = entry_t.len();

    // entries sorted once by their heap key (t, PH_ENTRY, rank, k) — identical to the
    // pop order the Python heapify'd all-entries heap yields among entry events
    let mut order: Vec<u32> = (0..n as u32).collect();
    order.sort_unstable_by_key(|&i| {
        let i = i as usize;
        (entry_t[i], cand_rank[i], trade_k[i])
    });

    let mut heap: BinaryHeap<Cursor> = BinaryHeap::new(); // one cursor per OPEN trade
    let mut money_buf = vec![0.0_f64; unit_inc.len()];    // per-mark money, filled on admit

    let mut equity = initial_equity;
    let mut open_risk = 0.0_f64;
    let mut eq_t: Vec<i64> = Vec::with_capacity(mark_t.len() + n + 1);
    let mut eq_v: Vec<f64> = Vec::with_capacity(mark_t.len() + n + 1);
    eq_t.push(order.first().map_or(0, |&i| entry_t[i as usize]));
    eq_v.push(equity);

    let mut risk_by_trade = vec![0.0_f64; n];
    let mut seq: i64 = 0;

    let mut out = FoldOut {
        eq_t: Vec::new(),
        eq_v: Vec::new(),
        adm_idx: Vec::new(),
        adm_exit_t: Vec::new(),
        adm_units: Vec::new(),
        adm_risk: Vec::new(),
        adm_gross: Vec::new(),
        adm_cost: Vec::new(),
        rej_idx: Vec::new(),
        rej_t: Vec::new(),
        rej_risk: Vec::new(),
        rej_open: Vec::new(),
        rej_cap: Vec::new(),
    };

    let mut ei = 0_usize; // next entry in sorted order
    loop {
        // pick the global minimum key: heap top (marks/exits) vs next entry
        let entry_key: Option<Key> = if ei < n {
            let i = order[ei] as usize;
            Some((entry_t[i], PH_ENTRY, cand_rank[i], trade_k[i]))
        } else {
            None
        };
        let take_cursor = match (heap.peek(), entry_key) {
            (Some(c), Some(ek)) => c.key < ek,
            (Some(_), None) => true,
            (None, Some(_)) => false,
            (None, None) => break,
        };

        if take_cursor {
            let mut cur = heap.pop().expect("peeked");
            if cur.key.1 == PH_MARK {
                let money = money_buf[cur.j];
                equity += money;
                eq_t.push(cur.key.0);
                eq_v.push(equity);
                if cur.advance(mark_t) {
                    heap.push(cur);
                }
            } else {
                // PH_EXIT — trade closes, release its risk; cursor is exhausted
                open_risk -= risk_by_trade[cur.i];
            }
            continue;
        }

        // ENTRY
        let i = order[ei] as usize;
        ei += 1;
        let t = entry_t[i];
        let rank = cand_rank[i] as usize;
        let w = weight[rank];
        let fm = equity;
        let r_i = risk_per_position * fm * w;
        if open_risk + r_i > r_max * fm + 1e-12 {
            out.rej_idx.push(i as i64);
            out.rej_t.push(t);
            out.rej_risk.push(r_i);
            out.rej_open.push(open_risk);
            out.rej_cap.push(r_max * fm);
            continue;
        }
        let mpu = money_per_unit[rank];
        let units = r_i / (stop_dist[i] * mpu);
        let cost = if charge_costs {
            cost_bps[rank] / 1e4 * units * entry_price[i] * mpu
        } else {
            0.0
        };
        equity -= cost;
        eq_t.push(t);
        eq_v.push(equity);
        open_risk += r_i;
        risk_by_trade[i] = r_i;

        let (m0, m1) = (mark_off[i] as usize, mark_off[i + 1] as usize);
        if m1 <= m0 {
            return Err("empty mark schedule for a trade".to_string());
        }
        // per-mark money in schedule order — same expression, operands, and gross
        // accumulation order as the Python loop
        let mut gross = 0.0_f64;
        for j in m0..m1 {
            let money = direction[i] * unit_inc[j] * units * mpu;
            gross += money;
            money_buf[j] = money;
        }
        let seq0 = seq + 1; // Python assigns seq+1..seq+m to these marks, in order
        seq += (m1 - m0) as i64;
        seq += 1; // Python also bumps seq for the exit push (value unused as a key)
        let exit_time = mark_t[m1 - 1];
        heap.push(Cursor {
            key: (mark_t[m0], PH_MARK, cand_rank[i], seq0),
            i,
            j: m0,
            m0,
            m1,
            seq0,
            exit_t: exit_time,
            exit_k: trade_k[i],
        });
        out.adm_idx.push(i as i64);
        out.adm_exit_t.push(exit_time);
        out.adm_units.push(units);
        out.adm_risk.push(r_i);
        out.adm_gross.push(gross);
        out.adm_cost.push(cost);
    }

    // reconciliation invariant (L-18), kernel-side; Python re-checks (belt and braces)
    let mut ledger_net = 0.0_f64;
    for j in 0..out.adm_gross.len() {
        ledger_net += out.adm_gross[j] - out.adm_cost[j];
    }
    let diff = ((equity - initial_equity) - ledger_net).abs();
    if diff > RECONCILE_TOL_MONEY * initial_equity {
        return Err(format!(
            "kernel reconciliation failed: equity delta {:.6} vs ledger net {:.6} (diff {:.6})",
            equity - initial_equity,
            ledger_net,
            diff
        ));
    }

    out.eq_t = eq_t;
    out.eq_v = eq_v;
    Ok(out)
}

/// The fold. All per-trade arrays are parallel, ordered by (candidate rank, trade k) —
/// the same order the Python loop builds its initial entry heap in. `mark_off` has
/// length n_trades+1; trade i's mark schedule is `mark_t[mark_off[i]..mark_off[i+1]]`
/// with per-unit increments `unit_inc` (already segment-clipped/censored by Python).
/// Per-candidate arrays (`weight`, `cost_bps`, `money_per_unit`) are indexed by rank.
#[pyfunction]
#[allow(clippy::too_many_arguments)]
fn fold<'py>(
    py: Python<'py>,
    entry_t: PyReadonlyArray1<'py, i64>,
    trade_k: PyReadonlyArray1<'py, i64>,
    cand_rank: PyReadonlyArray1<'py, u32>,
    direction: PyReadonlyArray1<'py, f64>,
    entry_price: PyReadonlyArray1<'py, f64>,
    stop_dist: PyReadonlyArray1<'py, f64>,
    mark_off: PyReadonlyArray1<'py, i64>,
    mark_t: PyReadonlyArray1<'py, i64>,
    unit_inc: PyReadonlyArray1<'py, f64>,
    weight: PyReadonlyArray1<'py, f64>,
    cost_bps: PyReadonlyArray1<'py, f64>,
    money_per_unit: PyReadonlyArray1<'py, f64>,
    initial_equity: f64,
    risk_per_position: f64,
    r_max: f64,
    charge_costs: bool,
) -> PyResult<Bound<'py, pyo3::types::PyTuple>> {
    let entry_t = entry_t.as_slice()?;
    let trade_k = trade_k.as_slice()?;
    let cand_rank = cand_rank.as_slice()?;
    let direction = direction.as_slice()?;
    let entry_price = entry_price.as_slice()?;
    let stop_dist = stop_dist.as_slice()?;
    let mark_off = mark_off.as_slice()?;
    let mark_t = mark_t.as_slice()?;
    let unit_inc = unit_inc.as_slice()?;
    let weight = weight.as_slice()?;
    let cost_bps = cost_bps.as_slice()?;
    let money_per_unit = money_per_unit.as_slice()?;

    if mark_off.len() != entry_t.len() + 1 {
        return Err(PyValueError::new_err("mark_off must have length n_trades+1"));
    }

    // pure computation over borrowed slices — GIL released (INFR-008)
    let out = py
        .detach(|| {
            fold_impl(
                entry_t, trade_k, cand_rank, direction, entry_price, stop_dist, mark_off,
                mark_t, unit_inc, weight, cost_bps, money_per_unit, initial_equity,
                risk_per_position, r_max, charge_costs,
            )
        })
        .map_err(PyValueError::new_err)?;

    let items: Vec<Bound<'py, PyAny>> = vec![
        out.eq_t.into_pyarray(py).into_any(),
        out.eq_v.into_pyarray(py).into_any(),
        out.adm_idx.into_pyarray(py).into_any(),
        out.adm_exit_t.into_pyarray(py).into_any(),
        out.adm_units.into_pyarray(py).into_any(),
        out.adm_risk.into_pyarray(py).into_any(),
        out.adm_gross.into_pyarray(py).into_any(),
        out.adm_cost.into_pyarray(py).into_any(),
        out.rej_idx.into_pyarray(py).into_any(),
        out.rej_t.into_pyarray(py).into_any(),
        out.rej_risk.into_pyarray(py).into_any(),
        out.rej_open.into_pyarray(py).into_any(),
        out.rej_cap.into_pyarray(py).into_any(),
    ];
    Ok(pyo3::types::PyTuple::new(py, items)?)
}

#[pymodule]
fn xena_fold(m: &Bound<'_, PyModule>) -> PyResult<()> {
    m.add_function(wrap_pyfunction!(fold, m)?)?;
    Ok(())
}
