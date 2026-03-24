"""
config.py — Central constants for Haul Road Analyzer
All truck specs, engineering standards, and baseline values.
Change values here to adapt to different trucks or sites.
"""

# ── Truck Specs (Cat OHT 777-D) ───────────────────────────────────────────
TRUCK = {
    "model":        "Cat OHT 777-D",
    "gvw_ton":      100,        # Gross Vehicle Weight (ton)
    "width_m":      4.72,       # body width (m)
    "turning_r_m":  9.45,       # turning radius (m)
    "rr_actual":    124,        # Rolling Resistance actual (lb/ton) — measured
    "rr_ideal":     65,         # Rolling Resistance ideal (lb/ton) — after grading
}

# ── Speed anchor points from journal Table 8 ─────────────────────────────
# Used for linear interpolation in speed model
SPEED_ANCHOR = {
    "loaded_rr_actual_kmh": 18.59,
    "loaded_rr_ideal_kmh":  21.59,
    "empty_rr_actual_kmh":  20.73,
    "empty_rr_ideal_kmh":   25.59,
}

# ── Engineering Standards ─────────────────────────────────────────────────
STANDARDS = {
    # Grade
    "grade_warn_pct":   8,      # KEPMEN 1827: warning threshold
    "grade_max_pct":    12,     # KEPMEN 1827: absolute maximum
    # Road Width (AASHTO)
    "width_2way_factor": 3.5,   # W_min = factor × truck_width (2-way traffic)
    "width_1way_factor": 2.0,   # W_min = factor × truck_width (1-way traffic)
    "width_curve_factor": 4.5,  # W_min for curve segments
    # Cross Slope (KEPMEN 1827)
    "cs_min_pct":       2,      # minimum cross slope for drainage
    "cs_max_pct":       4,      # maximum cross slope
    # Superelevasi (AASHTO)
    "super_max_pct":    10,     # maximum superelevasi at curve
    # CBR (Tannant & Regensburg Guidelines)
    "cbr_subgrade_min": 6,
    "cbr_subbase_min":  30,
    "cbr_base_min":     80,
}

# ── Site Parameters (PT Rahman Abdijaya) ─────────────────────────────────
SITE = {
    "name":         "PT Rahman Abdijaya",
    "road_name":    "Jalan Amaris–Novotel",
    "haul_dist_m":  734,        # haul road length (m)
    "n_segments":   14,
    "ref_paper":    "Arip Wibowo Saputra et al., Jurnal GEOSAPTA Vol.5 No.1, 2019",
}

# ── Fuel baseline (from PT Bukit Asam research) ───────────────────────────
FUEL = {
    "base_ratio_l_bcm": 0.23,   # L/BCM at RR=124, grade=4.7%
}

# ── Sensitivity sweep ranges ──────────────────────────────────────────────
SWEEP = {
    "grade_range":  (2.0, 15.0, 0.5),   # start, stop, step
    "rr_range":     (20, 130, 5),
    "dist_range":   (300, 2000, 50),
    "heatmap_grade": (2, 14, 1),
    "heatmap_rr":    (25, 130, 10),
}
