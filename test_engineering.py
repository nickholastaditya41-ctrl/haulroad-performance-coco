"""
tests/test_engineering.py
Run: pytest tests/ -v
"""
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

import pytest
import pandas as pd
from src.engineering import (
    calc_grade, grade_status, calc_width_min, width_status,
    cross_slope_status, calc_gr, calc_rr, calc_tr, calc_eff_grade,
    speed_loaded, speed_empty, calc_cycle_time,
    run_gap_analysis, tornado_analysis, whatif_scenarios,
    validate_against_journal,
)
from src.config import TRUCK, SITE


# ── Grade ────────────────────────────────────────────────────────────────

def test_calc_grade_positive():
    assert calc_grade(64.7, 73.0, 100) == 8.30

def test_calc_grade_negative():
    assert calc_grade(85.4, 76.8, 100) == -8.60

def test_calc_grade_zero_dist():
    assert calc_grade(10.0, 20.0, 0) == 0.0

def test_grade_status_ok():
    assert grade_status(5.0) == "OK"
    assert grade_status(-5.0) == "OK"

def test_grade_status_warning():
    assert grade_status(9.0) == "WARNING"
    assert grade_status(-9.0) == "WARNING"

def test_grade_status_critical():
    assert grade_status(13.0) == "CRITICAL"


# ── Road Width ───────────────────────────────────────────────────────────

def test_width_min_straight():
    # 4.72 × 3.5 = 16.52
    assert calc_width_min(4.72, is_curve=False) == 16.52

def test_width_min_curve():
    # 4.72 × 4.5 = 21.24
    assert calc_width_min(4.72, is_curve=True) == 21.24

def test_width_status_ok():
    status, delta = width_status(27.8, 16.52)
    assert status == "OK"
    assert delta > 0

def test_width_status_warning():
    status, delta = width_status(16.0, 16.52)
    assert status == "WARNING"
    assert delta < 0

def test_width_status_critical():
    status, delta = width_status(10.0, 16.52)
    assert status == "CRITICAL"


# ── Cross Slope ──────────────────────────────────────────────────────────

def test_cross_slope_ok():
    assert cross_slope_status(3.0) == "OK"
    assert cross_slope_status(2.0) == "OK"
    assert cross_slope_status(4.0) == "OK"

def test_cross_slope_warning():
    assert cross_slope_status(-1.0) == "WARNING"
    assert cross_slope_status(5.0) == "WARNING"

def test_cross_slope_no_data():
    import math
    assert cross_slope_status(float("nan")) == "NO_DATA"


# ── Resistance ───────────────────────────────────────────────────────────

def test_calc_gr():
    # GVW=100t, grade=8% → 100 × 8 × 10 = 8000 kg
    assert calc_gr(100, 8.0) == 8000.0

def test_calc_gr_negative_grade():
    # Uses abs(grade)
    assert calc_gr(100, -8.0) == 8000.0

def test_calc_rr():
    # GVW=100t, RR=124 lb/ton → 100 × 124 × 0.4536 = 5624.64 kg
    result = calc_rr(100, 124)
    assert abs(result - 5624.64) < 1.0

def test_calc_tr():
    gr = calc_gr(100, 8.0)
    rr = calc_rr(100, 124)
    tr = calc_tr(gr, rr)
    assert tr == round(gr + rr, 1)

def test_calc_eff_grade():
    # grade=4.7%, RR=124 → eff = 4.7 + 124/22 = 10.34
    result = calc_eff_grade(4.7, 124)
    assert abs(result - 10.34) < 0.1


# ── Speed Model (Journal Validation) ────────────────────────────────────

def test_speed_loaded_actual():
    # RR=124 → exactly 18.59 km/h
    assert speed_loaded(TRUCK["rr_actual"]) == 18.59

def test_speed_loaded_ideal():
    # RR=65 → exactly 21.59 km/h
    assert speed_loaded(TRUCK["rr_ideal"]) == 21.59

def test_speed_empty_actual():
    assert speed_empty(TRUCK["rr_actual"]) == 20.73

def test_speed_empty_ideal():
    assert speed_empty(TRUCK["rr_ideal"]) == 25.59

def test_speed_min_clamp():
    # Very high RR should not go below 5 km/h
    assert speed_loaded(500) >= 5.0


# ── Cycle Time ───────────────────────────────────────────────────────────

def test_cycle_time_journal_validation():
    # Journal: actual CT for 734m loaded=2.37 + empty=2.12 = 4.49 min
    ct = calc_cycle_time(4.7, TRUCK["rr_actual"], SITE["haul_dist_m"])
    assert abs(ct - (2.37 + 2.12)) < 0.05

def test_cycle_time_ideal():
    ct = calc_cycle_time(4.7, TRUCK["rr_ideal"], SITE["haul_dist_m"])
    assert abs(ct - (2.04 + 1.72)) < 0.05

def test_delta_ct_journal():
    ct_actual = calc_cycle_time(4.7, TRUCK["rr_actual"], SITE["haul_dist_m"])
    ct_ideal  = calc_cycle_time(4.7, TRUCK["rr_ideal"],  SITE["haul_dist_m"])
    delta = round(ct_actual - ct_ideal, 2)
    # Journal says 0.73 min total saving
    assert abs(delta - 0.73) < 0.05


# ── Gap Analysis (integration) ───────────────────────────────────────────

@pytest.fixture
def sample_df():
    return pd.DataFrame([{
        "seg_id": "A-B", "elev_start_m": 64.7, "elev_end_m": 73.0,
        "dist_horiz_m": 100, "width_actual_m": 27.8,
        "cross_slope_loaded_pct": 2, "cross_slope_empty_pct": 5,
        "is_curve": False, "superelevasi_pct": float("nan"),
    }])

def test_gap_analysis_returns_df(sample_df):
    result = run_gap_analysis(sample_df)
    assert isinstance(result, pd.DataFrame)
    assert len(result) == 1

def test_gap_analysis_grade_correct(sample_df):
    result = run_gap_analysis(sample_df)
    assert result.iloc[0]["grade_pct"] == 8.30

def test_gap_analysis_has_required_cols(sample_df):
    result = run_gap_analysis(sample_df)
    required = ["seg_id", "grade_pct", "grade_status", "width_m", "width_min_m",
                "TR_actual_kg", "TR_ideal_kg", "TR_reduction_kg", "overall_status"]
    for col in required:
        assert col in result.columns, f"Missing column: {col}"


# ── Sensitivity ──────────────────────────────────────────────────────────

def test_tornado_has_three_params():
    df = tornado_analysis()
    assert len(df) == 3

def test_tornado_swing_positive():
    df = tornado_analysis()
    assert (df["swing"] > 0).all()

def test_whatif_baseline_zero_delta():
    df = whatif_scenarios()
    baseline = df[df["scenario"].str.contains("Aktual")]
    assert baseline.iloc[0]["delta_ct_pct"] == 0.0

def test_whatif_optimal_better_than_baseline():
    df = whatif_scenarios()
    baseline = df[df["scenario"].str.contains("Aktual")].iloc[0]["cycle_time_min"]
    optimal  = df[df["scenario"].str.contains("optimal")].iloc[0]["cycle_time_min"]
    assert optimal < baseline


# ── Full Journal Validation ───────────────────────────────────────────────

def test_all_journal_validations_pass():
    results = validate_against_journal()
    summary = results["_summary"]
    assert summary["all_pass"], (
        f"Validation failed: {summary['passed']}/{summary['total']} passed. "
        "Check speed model anchor points."
    )
