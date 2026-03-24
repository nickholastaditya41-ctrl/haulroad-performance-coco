"""
engineering.py — Core engineering calculation functions
Phase 1: Gap Analysis  |  Phase 2: Sensitivity Analysis

All formulas validated against:
  Arip Wibowo Saputra et al., Jurnal GEOSAPTA Vol.5 No.1, 2019
  KEPMEN ESDM No.1827 K/30/MEM/2018
  AASHTO Manual Rural Highway Design
  Tannant & Regensburg — Guidelines for Mine Haul Road Design
"""

import numpy as np
import pandas as pd
from config import TRUCK, STANDARDS, SPEED_ANCHOR, SITE, FUEL, SWEEP


# ══════════════════════════════════════════════════════════════════════════
#  PHASE 1 — GEOMETRY
# ══════════════════════════════════════════════════════════════════════════

def calc_grade(elev_start: float, elev_end: float, dist_horiz: float) -> float:
    """
    Grade (%) = (delta_h / delta_x) * 100
    Positive = uphill, Negative = downhill
    Ref: KEPMEN 1827, max 8% (warning), 12% (absolute max)
    """
    if dist_horiz == 0:
        return 0.0
    return round((elev_end - elev_start) / dist_horiz * 100, 2)


def grade_status(grade_pct: float) -> str:
    """KEPMEN 1827 grade classification."""
    a = abs(grade_pct)
    if a > STANDARDS["grade_max_pct"]:
        return "CRITICAL"
    if a > STANDARDS["grade_warn_pct"]:
        return "WARNING"
    return "OK"


def calc_width_min(truck_width: float, is_curve: bool = False) -> float:
    """
    Minimum road width per AASHTO.
    2-way straight: W >= 3.5 × truck_width
    2-way curve:    W >= 4.5 × truck_width
    """
    factor = STANDARDS["width_curve_factor"] if is_curve else STANDARDS["width_2way_factor"]
    return round(truck_width * factor, 2)


def width_status(actual: float, required: float) -> tuple[str, float]:
    """Returns (status, delta). Delta = actual - required."""
    delta = round(actual - required, 2)
    if delta < -2:
        return "CRITICAL", delta
    if delta < 0:
        return "WARNING", delta
    return "OK", delta


def cross_slope_status(cs_pct: float) -> str:
    """Cross slope should be 2–4% for adequate drainage (KEPMEN 1827)."""
    if pd.isna(cs_pct):
        return "NO_DATA"
    return "OK" if STANDARDS["cs_min_pct"] <= cs_pct <= STANDARDS["cs_max_pct"] else "WARNING"


def superelevasi_status(se_pct: float) -> str:
    """Superelevasi max 10% per AASHTO."""
    if pd.isna(se_pct):
        return "N/A"
    return "OK" if 0 < se_pct <= STANDARDS["super_max_pct"] else "WARNING"


# ══════════════════════════════════════════════════════════════════════════
#  PHASE 1 — RESISTANCE
# ══════════════════════════════════════════════════════════════════════════

def calc_gr(gvw_ton: float, grade_pct: float) -> float:
    """
    Grade Resistance (kg) = GVW (ton) × grade (%) × 10
    Approximation of GVW × sin(θ), valid for grade ≤ 15%.
    Ref: KSU CE417, USBM Kaufman & Ault 1977
    """
    return round(gvw_ton * abs(grade_pct) * 10, 1)


def calc_rr(gvw_ton: float, rr_coeff_lb_ton: float) -> float:
    """
    Rolling Resistance (kg) = GVW (ton) × RR_coeff (lb/ton) × 0.4536
    (0.4536 = lb to kg conversion factor)
    """
    return round(gvw_ton * rr_coeff_lb_ton * 0.4536, 1)


def calc_tr(gr_kg: float, rr_kg: float) -> float:
    """Total Resistance = Grade Resistance + Rolling Resistance."""
    return round(gr_kg + rr_kg, 1)


def calc_eff_grade(grade_pct: float, rr_coeff_lb_ton: float) -> float:
    """
    Effective Grade (%) = actual grade + RR equivalent grade
    RR equivalent = RR_coeff / 22.0  (approx conversion lb/ton to %)
    Used to find speed from rimpull performance chart.
    """
    return round(grade_pct + rr_coeff_lb_ton / 22.0, 2)


# ══════════════════════════════════════════════════════════════════════════
#  PHASE 1 — SPEED & CYCLE TIME (journal-anchored model)
# ══════════════════════════════════════════════════════════════════════════

def speed_loaded(rr_lbt: float, grade_adj: float = 0) -> float:
    """
    Loaded speed (km/h) — linear interpolation anchored to journal Table 8:
      RR=124 lb/ton → 18.59 km/h  |  RR=65 lb/ton → 21.59 km/h
    Grade penalty: >5% grade adds 0.4 km/h per 1% over threshold.
    """
    a = SPEED_ANCHOR
    base = a["loaded_rr_actual_kmh"] + (
        (a["loaded_rr_ideal_kmh"] - a["loaded_rr_actual_kmh"])
        * (TRUCK["rr_actual"] - rr_lbt)
        / (TRUCK["rr_actual"] - TRUCK["rr_ideal"])
    )
    penalty = max(0, (abs(grade_adj) - 5)) * 0.4
    return round(max(5.0, base - penalty), 2)


def speed_empty(rr_lbt: float) -> float:
    """
    Empty speed (km/h) — anchored to journal Table 8:
      RR=124 lb/ton → 20.73 km/h  |  RR=65 lb/ton → 25.59 km/h
    """
    a = SPEED_ANCHOR
    return round(
        a["empty_rr_actual_kmh"] + (
            (a["empty_rr_ideal_kmh"] - a["empty_rr_actual_kmh"])
            * (TRUCK["rr_actual"] - rr_lbt)
            / (TRUCK["rr_actual"] - TRUCK["rr_ideal"])
        ), 2
    )


def calc_cycle_time(grade_pct: float, rr_lbt: float, dist_m: float, fixed_min: float = 0) -> float:
    """
    Cycle time (min) = haul time + return time + fixed time
    haul time   = (dist_m / 1000) / speed_loaded × 60
    return time = (dist_m / 1000) / speed_empty  × 60
    """
    sl = speed_loaded(rr_lbt, grade_pct)
    se = speed_empty(rr_lbt)
    return round((dist_m / 1000) / sl * 60 + (dist_m / 1000) / se * 60 + fixed_min, 3)


def calc_fuel_ratio(rr_lbt: float, grade_pct: float) -> float:
    """
    Fuel ratio (L/BCM) — empirical model scaled from PT Bukit Asam research.
    Base ratio 0.23 L/BCM at actual operating conditions.
    """
    return round(
        FUEL["base_ratio_l_bcm"] * (rr_lbt / TRUCK["rr_actual"]) * (1 + abs(grade_pct) / 100),
        4
    )


# ══════════════════════════════════════════════════════════════════════════
#  PHASE 1 — GAP ANALYSIS (per segment)
# ══════════════════════════════════════════════════════════════════════════

def analyze_segment(row: pd.Series) -> dict:
    """
    Full gap analysis for one road segment.
    Returns dict with all geometry, resistance, and status fields.
    """
    g   = calc_grade(row["elev_start_m"], row["elev_end_m"], row["dist_horiz_m"])
    cur = bool(row["is_curve"]) if not pd.isna(row["is_curve"]) else False
    se  = row.get("superelevasi_pct", float("nan"))

    wmin       = calc_width_min(TRUCK["width_m"], cur)
    ws, wd     = width_status(row["width_actual_m"], wmin)
    gs         = grade_status(g)
    css        = cross_slope_status(row["cross_slope_loaded_pct"])
    ses        = superelevasi_status(se)

    GR         = calc_gr(TRUCK["gvw_ton"], g)
    RR_act     = calc_rr(TRUCK["gvw_ton"], TRUCK["rr_actual"])
    RR_idl     = calc_rr(TRUCK["gvw_ton"], TRUCK["rr_ideal"])
    TR_act     = calc_tr(GR, RR_act)
    TR_idl     = calc_tr(GR, RR_idl)

    overall = (
        "CRITICAL" if "CRITICAL" in [gs, ws] else
        "WARNING"  if "WARNING"  in [gs, ws, css] else
        "OK"
    )

    return {
        "seg_id":           row["seg_id"],
        "grade_pct":        g,
        "grade_status":     gs,
        "width_m":          row["width_actual_m"],
        "width_min_m":      wmin,
        "width_delta_m":    wd,
        "width_status":     ws,
        "cross_slope_pct":  row["cross_slope_loaded_pct"],
        "cs_status":        css,
        "superelevasi_pct": se,
        "se_status":        ses,
        "is_curve":         cur,
        "GR_kg":            GR,
        "RR_actual_kg":     RR_act,
        "RR_ideal_kg":      RR_idl,
        "TR_actual_kg":     TR_act,
        "TR_ideal_kg":      TR_idl,
        "TR_reduction_kg":  round(TR_act - TR_idl, 1),
        "TR_reduction_pct": round((TR_act - TR_idl) / TR_act * 100, 1),
        "eff_grade_actual": calc_eff_grade(g, TRUCK["rr_actual"]),
        "eff_grade_ideal":  calc_eff_grade(g, TRUCK["rr_ideal"]),
        "overall_status":   overall,
    }


def run_gap_analysis(df: pd.DataFrame) -> pd.DataFrame:
    """Run gap analysis on all segments. Returns results DataFrame."""
    return pd.DataFrame([analyze_segment(row) for _, row in df.iterrows()])


# ══════════════════════════════════════════════════════════════════════════
#  PHASE 2 — SENSITIVITY ANALYSIS
# ══════════════════════════════════════════════════════════════════════════

def sweep_grade(rr: float = None, dist: float = None) -> pd.DataFrame:
    """One-at-a-time sweep: vary grade, fix RR and distance."""
    rr   = rr   or TRUCK["rr_actual"]
    dist = dist or SITE["haul_dist_m"]
    start, stop, step = SWEEP["grade_range"]
    return pd.DataFrame([{
        "grade_pct":       g,
        "cycle_time_min":  calc_cycle_time(g, rr, dist),
        "fuel_ratio":      calc_fuel_ratio(rr, g),
        "speed_loaded_kmh": speed_loaded(rr, g),
        "TR_kg":           calc_tr(calc_gr(TRUCK["gvw_ton"], g), calc_rr(TRUCK["gvw_ton"], rr)),
    } for g in np.arange(start, stop, step)])


def sweep_rr(grade: float = 4.7, dist: float = None) -> pd.DataFrame:
    """One-at-a-time sweep: vary RR, fix grade and distance."""
    dist = dist or SITE["haul_dist_m"]
    start, stop, step = SWEEP["rr_range"]
    return pd.DataFrame([{
        "rr_lb_ton":        r,
        "cycle_time_min":   calc_cycle_time(grade, r, dist),
        "fuel_ratio":       calc_fuel_ratio(r, grade),
        "speed_loaded_kmh": speed_loaded(r, grade),
        "speed_empty_kmh":  speed_empty(r),
        "TR_kg":            calc_tr(calc_gr(TRUCK["gvw_ton"], grade), calc_rr(TRUCK["gvw_ton"], r)),
    } for r in np.arange(start, stop, step)])


def sweep_dist(grade: float = 4.7, rr: float = None) -> pd.DataFrame:
    """One-at-a-time sweep: vary haul distance, fix grade and RR."""
    rr = rr or TRUCK["rr_actual"]
    start, stop, step = SWEEP["dist_range"]
    return pd.DataFrame([{
        "dist_m":          d,
        "cycle_time_min":  calc_cycle_time(grade, rr, d),
    } for d in np.arange(start, stop, step)])


def tornado_analysis(base_grade: float = 4.7, base_rr: float = None,
                     base_dist: float = None) -> pd.DataFrame:
    """
    Tornado chart data: vary each parameter ±20% from baseline.
    Returns DataFrame sorted by swing (most sensitive first).
    """
    base_rr   = base_rr   or TRUCK["rr_actual"]
    base_dist = base_dist or SITE["haul_dist_m"]
    base_ct   = calc_cycle_time(base_grade, base_rr, base_dist)

    params = {
        "grade (%)":    (base_grade * 0.8, base_grade * 1.2),
        "RR (lb/ton)":  (base_rr * 0.8,    base_rr * 1.2),
        "dist (m)":     (base_dist * 0.8,   base_dist * 1.2),
    }
    rows = []
    for pname, (lo, hi) in params.items():
        if pname == "grade (%)":
            ct_lo = calc_cycle_time(lo, base_rr,  base_dist)
            ct_hi = calc_cycle_time(hi, base_rr,  base_dist)
        elif pname == "RR (lb/ton)":
            ct_lo = calc_cycle_time(base_grade, lo,  base_dist)
            ct_hi = calc_cycle_time(base_grade, hi,  base_dist)
        else:
            ct_lo = calc_cycle_time(base_grade, base_rr, lo)
            ct_hi = calc_cycle_time(base_grade, base_rr, hi)
        rows.append({
            "parameter":   pname,
            "baseline_ct": round(base_ct, 3),
            "delta_low":   round(ct_lo - base_ct, 3),
            "delta_high":  round(ct_hi - base_ct, 3),
            "swing":       round(abs(ct_hi - ct_lo), 3),
        })
    return pd.DataFrame(rows).sort_values("swing", ascending=False).reset_index(drop=True)


def heatmap_grade_rr(grade_range: tuple = None, rr_range: tuple = None,
                     dist: float = None) -> tuple:
    """
    2D heatmap: grade × RR → cycle time.
    Returns (matrix, grade_values, rr_values).
    """
    dist = dist or SITE["haul_dist_m"]
    g_start, g_stop, g_step = grade_range or SWEEP["heatmap_grade"]
    r_start, r_stop, r_step = rr_range   or SWEEP["heatmap_rr"]
    gr  = np.arange(g_start, g_stop, g_step)
    rr  = np.arange(r_start, r_stop, r_step)
    mat = np.array([[calc_cycle_time(g, r, dist) for r in rr] for g in gr])
    return mat, gr, rr


def whatif_scenarios(base_grade: float = 4.7, base_rr: float = None,
                     dist: float = None) -> pd.DataFrame:
    """
    Four standard what-if scenarios for recommendation.
    Returns DataFrame with CT, fuel ratio, and delta vs baseline.
    """
    base_rr = base_rr or TRUCK["rr_actual"]
    dist    = dist    or SITE["haul_dist_m"]
    scenarios = [
        ("Aktual (baseline)",    base_grade, base_rr),
        ("RR diperbaiki",        base_grade, TRUCK["rr_ideal"]),
        ("Grade diperbaiki",     3.0,        base_rr),
        ("Keduanya optimal",     3.0,        TRUCK["rr_ideal"]),
    ]
    base_ct = calc_cycle_time(base_grade, base_rr, dist)
    rows = []
    for name, g, r in scenarios:
        ct = calc_cycle_time(g, r, dist)
        rows.append({
            "scenario":       name,
            "grade_pct":      g,
            "rr_lb_ton":      r,
            "cycle_time_min": ct,
            "fuel_ratio":     calc_fuel_ratio(r, g),
            "speed_loaded":   speed_loaded(r, g),
            "delta_ct_min":   round(ct - base_ct, 3),
            "delta_ct_pct":   round((ct - base_ct) / base_ct * 100, 1),
        })
    return pd.DataFrame(rows)


# ══════════════════════════════════════════════════════════════════════════
#  FLEET PRODUCTIVITY
# ══════════════════════════════════════════════════════════════════════════

def fleet_productivity(ct_min: float, n_trucks: int = 10, ops_hours: float = 20) -> dict:
    """Cycles per day and productivity index for a fleet."""
    cycles_per_truck = (ops_hours * 60) / ct_min
    total_cycles     = cycles_per_truck * n_trucks
    return {
        "cycle_time_min":      ct_min,
        "n_trucks":            n_trucks,
        "ops_hours":           ops_hours,
        "cycles_per_truck":    round(cycles_per_truck, 1),
        "total_cycles_day":    round(total_cycles, 0),
    }


# ══════════════════════════════════════════════════════════════════════════
#  VALIDATION (check outputs match journal)
# ══════════════════════════════════════════════════════════════════════════

def validate_against_journal() -> dict:
    """
    Validate key model outputs against journal Table 8.
    Returns dict with computed values, expected values, and pass/fail.
    """
    a = SPEED_ANCHOR
    sl_act = speed_loaded(TRUCK["rr_actual"])
    sl_idl = speed_loaded(TRUCK["rr_ideal"])
    se_act = speed_empty(TRUCK["rr_actual"])
    se_idl = speed_empty(TRUCK["rr_ideal"])
    dist   = SITE["haul_dist_m"]

    checks = {
        "speed_loaded_actual":  (sl_act, a["loaded_rr_actual_kmh"]),
        "speed_loaded_ideal":   (sl_idl, a["loaded_rr_ideal_kmh"]),
        "speed_empty_actual":   (se_act, a["empty_rr_actual_kmh"]),
        "speed_empty_ideal":    (se_idl, a["empty_rr_ideal_kmh"]),
        "travel_loaded_actual": (round((dist/1000)/sl_act*60, 2), 2.37),
        "travel_loaded_ideal":  (round((dist/1000)/sl_idl*60, 2), 2.04),
        "travel_empty_actual":  (round((dist/1000)/se_act*60, 2), 2.12),
        "travel_empty_ideal":   (round((dist/1000)/se_idl*60, 2), 1.72),
    }
    results = {}
    for k, (computed, expected) in checks.items():
        results[k] = {
            "computed": computed,
            "expected": expected,
            "delta":    round(computed - expected, 3),
            "pass":     abs(computed - expected) < 0.05,
        }
    total  = len(results)
    passed = sum(1 for v in results.values() if v["pass"])
    results["_summary"] = {"passed": passed, "total": total, "all_pass": passed == total}
    return results


if __name__ == "__main__":
    # Quick smoke test
    import pandas as pd

    print("=== Validation vs Journal ===")
    val = validate_against_journal()
    for k, v in val.items():
        if k == "_summary":
            continue
        status = "PASS" if v["pass"] else "FAIL"
        print(f"  [{status}] {k}: computed={v['computed']:.3f}, expected={v['expected']:.3f}, delta={v['delta']:+.3f}")
    s = val["_summary"]
    print(f"\n  Result: {s['passed']}/{s['total']} passed — {'ALL PASS' if s['all_pass'] else 'REVIEW NEEDED'}")

    print("\n=== Tornado ===")
    print(tornado_analysis().to_string(index=False))

    print("\n=== What-If Scenarios ===")
    print(whatif_scenarios().to_string(index=False))
