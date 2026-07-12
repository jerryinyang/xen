//! XENA oracle event-fold kernel (INFR-007) — byte-identical Rust port of the sequential
//! state-update loop in `xen.xena.oracle.evaluate`.
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
//! Heap-order parity: the Python heap holds tuples `(t, phase, cid, k_or_seq, payload)`
//! with phase mark(0) < exit(1) < entry(2), cid compared as a string, and a global push
//! counter `seq` for mark/exit tiebreaks. Keys are unique, so heapq pop order is the
//! total tuple order. Here cid is replaced by its rank in the sorted included-id list
//! (order-isomorphic to the string compare) and the same `seq` counter is replayed, so
//! the pop order — and therefore every float accumulation order — is identical.

use numpy::{IntoPyArray, PyReadonlyArray1};
use pyo3::exceptions::PyValueError;
use pyo3::prelude::*;
use std::cmp::Ordering;
use std::collections::BinaryHeap;

const RECONCILE_TOL_MONEY: f64 = 1e-6; // relative to initial equity (mirror of oracle.py)

const PH_MARK: u8 = 0;
const PH_EXIT: u8 = 1;
const PH_ENTRY: u8 = 2;

enum Payload {
    Entry(usize),     // index into the flat trade arrays
    Mark(f64),        // money increment
    Exit(usize),      // index into the flat trade arrays
}

struct Ev {
    t: i64,
    phase: u8,
    rank: u32,
    seq: i64, // trade k for entry/exit events, global push counter for marks
    payload: Payload,
}

impl PartialEq for Ev {
    fn eq(&self, other: &Self) -> bool {
        (self.t, self.phase, self.rank, self.seq) == (other.t, other.phase, other.rank, other.seq)
    }
}
impl Eq for Ev {}
impl Ord for Ev {
    fn cmp(&self, other: &Self) -> Ordering {
        // reversed: BinaryHeap is a max-heap, we need heapq's min-heap pop order
        (other.t, other.phase, other.rank, other.seq)
            .cmp(&(self.t, self.phase, self.rank, self.seq))
    }
}
impl PartialOrd for Ev {
    fn partial_cmp(&self, other: &Self) -> Option<Ordering> {
        Some(self.cmp(other))
    }
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

    let n = entry_t.len();
    if mark_off.len() != n + 1 {
        return Err(PyValueError::new_err("mark_off must have length n_trades+1"));
    }

    let mut heap: BinaryHeap<Ev> = BinaryHeap::with_capacity(n + mark_t.len() + 16);
    for i in 0..n {
        heap.push(Ev {
            t: entry_t[i],
            phase: PH_ENTRY,
            rank: cand_rank[i],
            seq: trade_k[i],
            payload: Payload::Entry(i),
        });
    }

    let mut equity = initial_equity;
    let mut open_risk = 0.0_f64;
    let mut eq_t: Vec<i64> = Vec::with_capacity(mark_t.len() + n + 1);
    let mut eq_v: Vec<f64> = Vec::with_capacity(mark_t.len() + n + 1);
    eq_t.push(heap.peek().map_or(0, |e| e.t));
    eq_v.push(equity);

    let mut risk_by_trade = vec![0.0_f64; n];
    let mut seq: i64 = 0;

    // ledger columns (admission order)
    let mut adm_idx: Vec<i64> = Vec::new();
    let mut adm_exit_t: Vec<i64> = Vec::new();
    let mut adm_units: Vec<f64> = Vec::new();
    let mut adm_risk: Vec<f64> = Vec::new();
    let mut adm_gross: Vec<f64> = Vec::new();
    let mut adm_cost: Vec<f64> = Vec::new();
    // rejected columns (rejection order)
    let mut rej_idx: Vec<i64> = Vec::new();
    let mut rej_t: Vec<i64> = Vec::new();
    let mut rej_risk: Vec<f64> = Vec::new();
    let mut rej_open: Vec<f64> = Vec::new();
    let mut rej_cap: Vec<f64> = Vec::new();

    while let Some(ev) = heap.pop() {
        match ev.payload {
            Payload::Mark(money) => {
                equity += money;
                eq_t.push(ev.t);
                eq_v.push(equity);
            }
            Payload::Exit(i) => {
                open_risk -= risk_by_trade[i];
            }
            Payload::Entry(i) => {
                let rank = ev.rank as usize;
                let w = weight[rank];
                let fm = equity;
                let r_i = risk_per_position * fm * w;
                if open_risk + r_i > r_max * fm + 1e-12 {
                    rej_idx.push(i as i64);
                    rej_t.push(ev.t);
                    rej_risk.push(r_i);
                    rej_open.push(open_risk);
                    rej_cap.push(r_max * fm);
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
                eq_t.push(ev.t);
                eq_v.push(equity);
                open_risk += r_i;
                risk_by_trade[i] = r_i;

                let (m0, m1) = (mark_off[i] as usize, mark_off[i + 1] as usize);
                if m1 <= m0 {
                    return Err(PyValueError::new_err("empty mark schedule for a trade"));
                }
                let mut gross = 0.0_f64;
                for j in m0..m1 {
                    let money = direction[i] * unit_inc[j] * units * mpu;
                    gross += money;
                    seq += 1;
                    heap.push(Ev {
                        t: mark_t[j],
                        phase: PH_MARK,
                        rank: ev.rank,
                        seq,
                        payload: Payload::Mark(money),
                    });
                }
                let exit_time = mark_t[m1 - 1];
                seq += 1;
                heap.push(Ev {
                    t: exit_time,
                    phase: PH_EXIT,
                    rank: ev.rank,
                    seq: trade_k[i],
                    payload: Payload::Exit(i),
                });
                adm_idx.push(i as i64);
                adm_exit_t.push(exit_time);
                adm_units.push(units);
                adm_risk.push(r_i);
                adm_gross.push(gross);
                adm_cost.push(cost);
            }
        }
    }

    // reconciliation invariant (L-18), kernel-side; Python re-checks (belt and braces)
    let mut ledger_net = 0.0_f64;
    for j in 0..adm_gross.len() {
        ledger_net += adm_gross[j] - adm_cost[j];
    }
    let diff = ((equity - initial_equity) - ledger_net).abs();
    if diff > RECONCILE_TOL_MONEY * initial_equity {
        return Err(PyValueError::new_err(format!(
            "kernel reconciliation failed: equity delta {:.6} vs ledger net {:.6} (diff {:.6})",
            equity - initial_equity,
            ledger_net,
            diff
        )));
    }

    let items: Vec<Bound<'py, PyAny>> = vec![
        eq_t.into_pyarray(py).into_any(),
        eq_v.into_pyarray(py).into_any(),
        adm_idx.into_pyarray(py).into_any(),
        adm_exit_t.into_pyarray(py).into_any(),
        adm_units.into_pyarray(py).into_any(),
        adm_risk.into_pyarray(py).into_any(),
        adm_gross.into_pyarray(py).into_any(),
        adm_cost.into_pyarray(py).into_any(),
        rej_idx.into_pyarray(py).into_any(),
        rej_t.into_pyarray(py).into_any(),
        rej_risk.into_pyarray(py).into_any(),
        rej_open.into_pyarray(py).into_any(),
        rej_cap.into_pyarray(py).into_any(),
    ];
    Ok(pyo3::types::PyTuple::new(py, items)?)
}

#[pymodule]
fn xena_fold(m: &Bound<'_, PyModule>) -> PyResult<()> {
    m.add_function(wrap_pyfunction!(fold, m)?)?;
    Ok(())
}
