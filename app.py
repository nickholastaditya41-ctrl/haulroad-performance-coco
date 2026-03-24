"""
app.py — Haul Road Performance Analyzer · Streamlit Dashboard
PT Rahman Abdijaya · Caterpillar OHT 777-D
Phase 1: Gap Analysis  ·  Phase 2: Sensitivity Analysis
=========================================================
Run:  streamlit run app.py
"""

import io
import sys
import os
sys.path.insert(0, os.path.dirname(__file__))

import warnings
import numpy as np
import pandas as pd
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import streamlit as st

from config import TRUCK, STANDARDS, SITE
from engineering import (
    run_gap_analysis, sweep_grade, sweep_rr, sweep_dist,
    tornado_analysis, heatmap_grade_rr, whatif_scenarios,
    fleet_productivity, speed_loaded, speed_empty,
    calc_cycle_time, calc_fuel_ratio, validate_against_journal,
)

warnings.filterwarnings("ignore")

# ─────────────────────────────────────────────
#  PAGE CONFIG
# ─────────────────────────────────────────────
st.set_page_config(
    page_title="Haul Road Performance Analyzer · by Nickholast Aditya",
    page_icon="🛣️",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ─────────────────────────────────────────────
#  THEME
# ─────────────────────────────────────────────
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=JetBrains+Mono:wght@400;600&family=Syne:wght@400;600;700;800&display=swap');
html, body, [class*="css"] { font-family: 'Syne', sans-serif; }
.stApp { background: #090F1A; }
section[data-testid="stSidebar"] { background: #0C1829 !important; border-right: 1px solid #1A2E44; }
section[data-testid="stSidebar"] * { color: #7AAABF !important; }
section[data-testid="stSidebar"] h2, section[data-testid="stSidebar"] h3 {
    color: #4A7A9B !important; font-size:10px !important; letter-spacing:2px !important; text-transform:uppercase !important;
}
.kpi-card { background:#0C1829; border:1px solid #1A2E44; border-radius:10px; padding:16px 18px; }
.kpi-label { font-size:10px; color:#3A6A8A; letter-spacing:2px; text-transform:uppercase;
    margin-bottom:6px; font-family:'JetBrains Mono',monospace; }
.kpi-value { font-size:26px; font-weight:800; font-family:'JetBrains Mono',monospace; line-height:1; }
.kpi-sub   { font-size:11px; font-family:'JetBrains Mono',monospace; margin-top:5px; }
.kpi-red   {color:#E74C3C;} .kpi-amber {color:#F39C12;} .kpi-green {color:#2ECC71;}
.kpi-blue  {color:#5DADE2;} .kpi-teal  {color:#4CC9F0;} .kpi-purple{color:#9B59B6;}
.sub-red   {color:#7B2D2D;} .sub-amber {color:#7B5412;} .sub-green {color:#1D6A40;}
.sub-blue  {color:#1A4A6A;} .sub-teal  {color:#1A4A5A;}
.sec-header { font-size:10px; color:#3A6A8A; letter-spacing:3px; text-transform:uppercase;
    font-weight:700; margin-bottom:14px; font-family:'JetBrains Mono',monospace;
    border-bottom:1px solid #1A2E44; padding-bottom:6px; }
.bi-box { background:#0C1829; border:1px solid #1A2E44; border-left:3px solid #F39C12;
    border-radius:8px; padding:14px 16px; margin-bottom:10px; }
.bi-box.critical {border-left-color:#E74C3C;} .bi-box.good {border-left-color:#2ECC71;}
.bi-box.info     {border-left-color:#5DADE2;} .bi-box.warn {border-left-color:#F39C12;}
.bi-title { font-size:11px; font-weight:700; letter-spacing:1px; text-transform:uppercase;
    margin-bottom:4px; font-family:'JetBrains Mono',monospace; }
.bi-title.critical{color:#E74C3C;} .bi-title.warn{color:#F39C12;}
.bi-title.good{color:#2ECC71;}     .bi-title.info{color:#5DADE2;}
.bi-text { font-size:13px; color:#8AADC2; line-height:1.6; }
.top-title { font-size:22px; font-weight:800; color:#FFFFFF; letter-spacing:1px; }
.top-sub   { font-size:12px; color:#3A6A8A; font-family:'JetBrains Mono',monospace; margin-top:2px; }
div[data-testid="metric-container"] { background:#0C1829; border:1px solid #1A2E44; border-radius:10px; padding:14px; }
.stTabs [data-baseweb="tab-list"] { background:#0C1829; border-bottom:1px solid #1A2E44; gap:0; }
.stTabs [data-baseweb="tab"] { background:transparent; color:#3A6A8A; font-size:12px; font-weight:600;
    letter-spacing:1px; text-transform:uppercase; padding:10px 20px; border-bottom:2px solid transparent; }
.stTabs [aria-selected="true"] { color:#5DADE2 !important; border-bottom:2px solid #5DADE2 !important; background:transparent !important; }
.stDataFrame { border:1px solid #1A2E44 !important; border-radius:8px; }
</style>
""", unsafe_allow_html=True)

# ─────────────────────────────────────────────
#  PLOTLY THEME
# ─────────────────────────────────────────────
DL = dict(
    paper_bgcolor="#0C1829", plot_bgcolor="#090F1A",
    font=dict(color="#7AAABF", family="JetBrains Mono,monospace", size=11),
    title_font=dict(color="#FFFFFF", size=13, family="Syne,sans-serif"),
    margin=dict(t=50, b=40, l=55, r=20),
)
AX  = dict(gridcolor="#1A2E44", linecolor="#1A2E44", tickcolor="#3A6A8A", zerolinecolor="#1A2E44")
LEG = dict(bgcolor="rgba(0,0,0,0)", bordercolor="#1A2E44", borderwidth=1, font=dict(size=11))
RED, AMBER, GREEN, BLUE, TEAL, PURPLE = "#E74C3C","#F39C12","#2ECC71","#5DADE2","#4CC9F0","#9B59B6"
SC = {"OK": GREEN, "WARNING": AMBER, "CRITICAL": RED, "NO_DATA": "#3A6A8A", "N/A": "#3A6A8A"}

# ─────────────────────────────────────────────
#  DEMO DATA
# ─────────────────────────────────────────────
DEMO_CSV = """seg_id,elev_start_m,elev_end_m,dist_horiz_m,width_actual_m,cross_slope_loaded_pct,cross_slope_empty_pct,is_curve,superelevasi_pct
A-B,64.7,73.0,100,27.8,2,5,False,
B-C,73.0,82.0,100,26.7,-1,3,False,
C-D,82.0,84.4,31,24.2,4,0,False,
D-E,84.4,85.4,44,33.0,5,-2,False,
E-F,85.4,76.8,100,48.1,3,1,False,
F-G,76.8,73.8,50,25.0,-2,4,True,1.04
G-H,73.8,72.1,44,31.8,0,5,True,0.95
H-I,72.1,71.8,28,34.0,-1,3,True,0.67
I-J,71.8,71.4,21,36.0,1,0,True,1.50
J-K,71.4,71.6,21,35.3,5,-2,True,2.23
K-L,71.6,72.6,94,28.0,3,1,False,
L-M,72.6,73.3,25,31.0,-2,4,False,
M-N,73.3,73.4,100,30.0,-1,3,False,
N-O,73.4,73.6,100,25.0,1,3,False,
"""

# ─────────────────────────────────────────────
#  SIDEBAR
# ─────────────────────────────────────────────
with st.sidebar:
    st.markdown("## 🛣️ Haul Road Performance Analyzer")
    st.markdown(f"**{SITE['name']} · {TRUCK['model']}**")
    st.divider()

    st.markdown("### Upload Data")
    uploaded  = st.file_uploader("segments_geometry.csv", type=["csv"])
    use_demo  = st.checkbox("Gunakan demo data (PT Rahman Abdijaya)", value=True)

    st.divider()
    st.markdown("### Parameters")
    dist_m    = st.slider("Haul distance (m)",   300, 2000, SITE["haul_dist_m"], 50)
    rr_actual = st.slider("RR aktual (lb/ton)",   20,  150, TRUCK["rr_actual"],  5)
    rr_ideal  = st.slider("RR ideal (lb/ton)",    20,  100, TRUCK["rr_ideal"],   5)
    n_trucks  = st.slider("Jumlah truck",           1,   30, 10, 1)
    ops_hours = st.slider("Jam operasi/hari",       8,   24, 20, 1)

    st.divider()
    st.markdown("### Standar (KEPMEN 1827 + AASHTO)")
    st.markdown(f"""
    <div style='font-family:monospace;font-size:11px;color:#3A6A8A;line-height:2'>
    Grade warn : {STANDARDS['grade_warn_pct']}%<br>
    Grade max  : {STANDARDS['grade_max_pct']}%<br>
    Width 2-way: {STANDARDS['width_2way_factor']}× lebar truck<br>
    Cross slope: {STANDARDS['cs_min_pct']}–{STANDARDS['cs_max_pct']}%<br>
    Super max  : {STANDARDS['super_max_pct']}%<br>
    Truck width: {TRUCK['width_m']}m<br>
    GVW loaded : {TRUCK['gvw_ton']} ton
    </div>
    """, unsafe_allow_html=True)

# ─────────────────────────────────────────────
#  LOAD DATA
# ─────────────────────────────────────────────
if uploaded is not None:
    df_raw = pd.read_csv(uploaded)
elif use_demo:
    df_raw = pd.read_csv(io.StringIO(DEMO_CSV))
else:
    st.markdown("""
    <div style='text-align:center;padding:80px 40px'>
        <div style='font-size:48px;margin-bottom:16px'>🛣️</div>
        <div class='top-title'>Haul Road Performance Analyzer</div>
        <div class='top-sub'>by Nickholast Aditya Pratama</div>
        <div style='margin-top:32px;font-size:14px;color:#3A6A8A;font-family:monospace'>
            ← Upload <b style='color:#5DADE2'>segments_geometry.csv</b> atau aktifkan demo data
        </div>
    </div>
    """, unsafe_allow_html=True)
    st.stop()

# Patch truck params from sidebar (runtime override)
TRUCK["rr_actual"] = rr_actual
TRUCK["rr_ideal"]  = rr_ideal

# ── Run all analyses ──────────────────────────────────────────────────────
df_gap    = run_gap_analysis(df_raw)
df_tor    = tornado_analysis(base_grade=4.7, base_rr=rr_actual, base_dist=dist_m)
df_sw_g   = sweep_grade(rr=rr_actual, dist=dist_m)
df_sw_rr  = sweep_rr(grade=4.7, dist=dist_m)
df_sw_d   = sweep_dist(grade=4.7, rr=rr_actual)
df_wif    = whatif_scenarios(base_rr=rr_actual, dist=dist_m)
hm, gr, rr = heatmap_grade_rr(dist=dist_m)

# ── KPI values ────────────────────────────────────────────────────────────
n_seg  = len(df_gap)
n_ok   = (df_gap["overall_status"] == "OK").sum()
n_warn = (df_gap["overall_status"] == "WARNING").sum()
n_crit = (df_gap["overall_status"] == "CRITICAL").sum()
ct_act = calc_cycle_time(4.7, rr_actual, dist_m)
ct_idl = calc_cycle_time(4.7, rr_ideal,  dist_m)
d_ct   = round(ct_act - ct_idl, 3)
fp_act = fleet_productivity(ct_act, n_trucks, ops_hours)
fp_idl = fleet_productivity(ct_idl, n_trucks, ops_hours)
d_cyc  = int(fp_idl["total_cycles_day"] - fp_act["total_cycles_day"])
spd_la = speed_loaded(rr_actual)
spd_li = speed_loaded(rr_ideal)

# ─────────────────────────────────────────────
#  TOP BAR
# ─────────────────────────────────────────────
st.markdown(f"""
<div style='display:flex;justify-content:space-between;align-items:flex-start;
  margin-bottom:20px;padding:18px 0 12px 0;border-bottom:1px solid #1A2E44'>
  <div>
    <div class='top-title'>Haul Road Performance Analyzer</div>
    <div class='top-sub'>{SITE['name']} · {TRUCK['model']} · {SITE['road_name']} · Phase 1 Gap Analysis + Phase 2 Sensitivity</div>
  </div>
  <div style='font-family:monospace;font-size:11px;color:#3A6A8A;text-align:right'>
    Ref: Arip Wibowo Saputra et al.<br>
    Jurnal GEOSAPTA Vol.5 No.1, Jan 2019
  </div>
</div>
""", unsafe_allow_html=True)

# ─────────────────────────────────────────────
#  KPI ROW
# ─────────────────────────────────────────────
k1, k2, k3, k4, k5, k6 = st.columns(6)
for col, label, val, sub, vc, sc2 in [
    (k1, "Total Segmen",  f"{n_seg}",               f"OK:{n_ok} | WARN:{n_warn} | CRIT:{n_crit}", "kpi-blue",  "sub-blue"),
    (k2, "Segmen WARNING",f"{n_warn}/{n_seg}",       f"{n_warn/n_seg*100:.0f}% perlu perhatian",    "kpi-amber", "sub-amber"),
    (k3, "CT Aktual",     f"{ct_act:.2f} min",       f"RR={rr_actual} lb/t · dist={dist_m}m",       "kpi-red",   "sub-red"),
    (k4, "CT Ideal",      f"{ct_idl:.2f} min",       f"−{d_ct:.3f} min vs aktual",                  "kpi-green", "sub-green"),
    (k5, "Speed ↑",       f"+{spd_li-spd_la:.1f} km/h", f"{spd_la:.2f}→{spd_li:.2f} km/h loaded",  "kpi-teal",  "sub-teal"),
    (k6, "Fleet +cycles", f"+{d_cyc}/hari",          f"{n_trucks}T × {ops_hours}h ops",             "kpi-green", "sub-green"),
]:
    col.markdown(f"""
    <div class='kpi-card'>
      <div class='kpi-label'>{label}</div>
      <div class='kpi-value {vc}'>{val}</div>
      <div class='kpi-sub {sc2}'>{sub}</div>
    </div>
    """, unsafe_allow_html=True)

st.markdown("<br>", unsafe_allow_html=True)

# ─────────────────────────────────────────────
#  TABS
# ─────────────────────────────────────────────
tabs = st.tabs([
    "📊 Overview",
    "📐 Phase 1 — Gap",
    "⚙️ Resistance",
    "📈 Phase 2 — Sensitivity",
    "🌪️ Tornado",
    "🔥 Heatmap",
    "🔀 What-If",
    "✅ Validasi",
    "💡 BI Insights",
    "📋 Data & Export",
])
t_ov, t_gap, t_res, t_sens, t_tor, t_hm, t_wif, t_val, t_bi, t_data = tabs

# ─── helpers ──────────────────────────────────────────────────────────────
def bar_status_colors(col): return [SC.get(v, "#3A6A8A") for v in col]

def ax_update(fig):
    fig.update_xaxes(**AX)
    fig.update_yaxes(**AX)
    return fig

# ══════════════════════════════════════════════════════════════════════════
#  OVERVIEW
# ══════════════════════════════════════════════════════════════════════════
with t_ov:
    st.markdown("<div class='sec-header'>Ringkasan Kondisi Jalan Amaris–Novotel</div>", unsafe_allow_html=True)

    c1, c2 = st.columns([1, 2])
    # Donut
    counts = df_gap["overall_status"].value_counts()
    fig_d = go.Figure(go.Pie(
        labels=counts.index, values=counts.values, hole=0.6,
        marker_colors=[SC.get(s, "#3A6A8A") for s in counts.index],
        textinfo="label+value",
        hovertemplate="<b>%{label}</b><br>%{value} segmen<extra></extra>",
    ))
    fig_d.update_layout(**DL, title="Status per Segmen", showlegend=True, legend=LEG,
                         height=280)
    fig_d.update_layout(margin=dict(t=50, b=10, l=20, r=20))
    c1.plotly_chart(fig_d, use_container_width=True, key="donut")

    # Grade bar
    fig_g = go.Figure()
    fig_g.add_hline(y=8,  line_dash="dash", line_color=AMBER, line_width=1.5, annotation_text="Warn 8%")
    fig_g.add_hline(y=-8, line_dash="dash", line_color=AMBER, line_width=1.0)
    fig_g.add_hline(y=12, line_dash="dash", line_color=RED,   line_width=1.5, annotation_text="Max 12%")
    fig_g.add_trace(go.Bar(
        x=df_gap["seg_id"], y=df_gap["grade_pct"],
        marker_color=bar_status_colors(df_gap["grade_status"]),
        hovertemplate="<b>%{x}</b><br>Grade: %{y:.2f}%<extra></extra>",
    ))
    fig_g.update_layout(**DL, title="Grade per Segmen (%)", xaxis_title="Segmen", yaxis_title="Grade (%)")
    ax_update(fig_g)
    c2.plotly_chart(fig_g, use_container_width=True, key="grade_ov")

    c3, c4 = st.columns(2)
    # Effective grade
    fig_eg = go.Figure()
    fig_eg.add_trace(go.Scatter(x=df_gap["seg_id"], y=df_gap["eff_grade_actual"],
                                mode="lines+markers", name="Aktual",
                                line=dict(color=RED, width=2.2), marker=dict(size=8, color=RED)))
    fig_eg.add_trace(go.Scatter(x=df_gap["seg_id"], y=df_gap["eff_grade_ideal"],
                                mode="lines+markers", name="Ideal",
                                line=dict(color=GREEN, width=2.2), marker=dict(size=8, color=GREEN)))
    fig_eg.add_hline(y=8, line_dash="dot", line_color=AMBER, line_width=1)
    fig_eg.update_layout(**DL, title="Effective Grade per Segmen", legend=LEG)
    ax_update(fig_eg)
    c3.plotly_chart(fig_eg, use_container_width=True, key="effg_ov")

    # TR reduction
    tr_pct = (df_gap["TR_reduction_kg"] / df_gap["TR_actual_kg"] * 100).round(1)
    fig_tr = go.Figure()
    fig_tr.add_trace(go.Bar(x=df_gap["seg_id"], y=tr_pct, marker_color=AMBER,
                            hovertemplate="<b>%{x}</b><br>Reduksi TR: %{y:.1f}%<extra></extra>"))
    fig_tr.add_hline(y=tr_pct.mean(), line_dash="dot", line_color="#7AAABF", line_width=1,
                     annotation_text=f"avg {tr_pct.mean():.1f}%")
    fig_tr.update_layout(**DL, title="Potensi Reduksi TR jika RR Diperbaiki (%)")
    ax_update(fig_tr)
    c4.plotly_chart(fig_tr, use_container_width=True, key="tr_ov")

# ══════════════════════════════════════════════════════════════════════════
#  PHASE 1 — GAP ANALYSIS
# ══════════════════════════════════════════════════════════════════════════
with t_gap:
    st.markdown("<div class='sec-header'>Phase 1 — Gap Analysis Geometri</div>", unsafe_allow_html=True)

    c1, c2 = st.columns(2)
    # Width comparison
    fig_w = go.Figure()
    fig_w.add_trace(go.Bar(name="Aktual", x=df_gap["seg_id"], y=df_gap["width_m"],
                           marker_color=TEAL, marker_opacity=0.85, width=0.35, offset=-0.2,
                           hovertemplate="<b>%{x}</b><br>Aktual: %{y:.1f}m<extra></extra>"))
    fig_w.add_trace(go.Bar(name="Minimum", x=df_gap["seg_id"], y=df_gap["width_min_m"],
                           marker_color=PURPLE, marker_opacity=0.75, width=0.35, offset=0.05,
                           hovertemplate="<b>%{x}</b><br>Minimum: %{y:.1f}m<extra></extra>"))
    fig_w.update_layout(**DL, title="Lebar Jalan — Aktual vs Minimum", barmode="overlay", legend=LEG)
    ax_update(fig_w)
    c1.plotly_chart(fig_w, use_container_width=True, key="width_p1")
    c2.plotly_chart(fig_g, use_container_width=True, key="grade_p1")

    st.markdown("<div class='sec-header'>Tabel Gap Analysis per Segmen</div>", unsafe_allow_html=True)

    def color_status_cell(val):
        mapping = {"OK": "#1D6A40", "WARNING": "#7B5412", "CRITICAL": "#7B2D2D", "NO_DATA": "#1A3A5A"}
        c = mapping.get(val, "")
        return f"background-color:{c};color:white" if c else ""

    show = ["seg_id","grade_pct","grade_status","width_m","width_min_m","width_delta_m",
            "width_status","cross_slope_pct","cs_status","superelevasi_pct","se_status",
            "is_curve","overall_status"]
    st.dataframe(
        df_gap[show].style.applymap(
            color_status_cell,
            subset=["grade_status","width_status","cs_status","se_status","overall_status"]
        ),
        use_container_width=True, hide_index=True
    )

# ══════════════════════════════════════════════════════════════════════════
#  RESISTANCE
# ══════════════════════════════════════════════════════════════════════════
with t_res:
    st.markdown("<div class='sec-header'>Total Resistance — Aktual vs Ideal</div>", unsafe_allow_html=True)

    fig_r = go.Figure()
    fig_r.add_trace(go.Bar(name=f"TR Aktual (RR={rr_actual})", x=df_gap["seg_id"], y=df_gap["TR_actual_kg"],
                           marker_color=RED, marker_opacity=0.85, width=0.35, offset=-0.2,
                           hovertemplate="<b>%{x}</b><br>TR aktual: %{y:,.0f} kg<extra></extra>"))
    fig_r.add_trace(go.Bar(name=f"TR Ideal (RR={rr_ideal})", x=df_gap["seg_id"], y=df_gap["TR_ideal_kg"],
                           marker_color=GREEN, marker_opacity=0.85, width=0.35, offset=0.05,
                           hovertemplate="<b>%{x}</b><br>TR ideal: %{y:,.0f} kg<extra></extra>"))
    fig_r.update_layout(**DL, title="Total Resistance per Segmen (kg)", barmode="overlay", legend=LEG)
    ax_update(fig_r)
    st.plotly_chart(fig_r, use_container_width=True, key="tr_main")

    c1, c2 = st.columns(2)
    c1.plotly_chart(fig_tr, use_container_width=True, key="tr_red_res")
    c2.plotly_chart(fig_eg, use_container_width=True, key="effg_res")

    st.markdown("<div class='sec-header'>Tabel Resistance</div>", unsafe_allow_html=True)
    rc = ["seg_id","grade_pct","GR_kg","RR_actual_kg","RR_ideal_kg",
          "TR_actual_kg","TR_ideal_kg","TR_reduction_kg","TR_reduction_pct",
          "eff_grade_actual","eff_grade_ideal"]
    st.dataframe(df_gap[rc].round(1), use_container_width=True, hide_index=True)

# ══════════════════════════════════════════════════════════════════════════
#  PHASE 2 — SENSITIVITY
# ══════════════════════════════════════════════════════════════════════════
with t_sens:
    st.markdown("<div class='sec-header'>Phase 2 — One-at-a-Time Parameter Sweep</div>", unsafe_allow_html=True)

    c1, c2 = st.columns(2)

    # Grade sweep
    fig_sg = make_subplots(specs=[[{"secondary_y": True}]])
    fig_sg.add_trace(go.Scatter(x=df_sw_g["grade_pct"], y=df_sw_g["cycle_time_min"],
                                mode="lines", name="Cycle time", line=dict(color=TEAL, width=2.5)), secondary_y=False)
    fig_sg.add_trace(go.Scatter(x=df_sw_g["grade_pct"], y=df_sw_g["fuel_ratio"],
                                mode="lines", name="Fuel ratio", line=dict(color=AMBER, width=2, dash="dash")), secondary_y=True)
    fig_sg.add_vline(x=8,   line_dash="dash", line_color=RED,   line_width=1.2, annotation_text="KEPMEN 8%")
    fig_sg.add_vline(x=4.7, line_dash="dot",  line_color=GREEN, line_width=1.0, annotation_text="baseline")
    fig_sg.update_layout(**DL, title="Grade → Cycle Time & Fuel", legend=LEG)
    fig_sg.update_xaxes(**AX, title_text="Grade (%)")
    fig_sg.update_yaxes(**AX, title_text="CT (min)", secondary_y=False)
    fig_sg.update_yaxes(**AX, title_text="Fuel (L/BCM)", secondary_y=True)
    c1.plotly_chart(fig_sg, use_container_width=True, key="sg")

    # RR sweep
    fig_sr = make_subplots(specs=[[{"secondary_y": True}]])
    fig_sr.add_trace(go.Scatter(x=df_sw_rr["rr_lb_ton"], y=df_sw_rr["cycle_time_min"],
                                mode="lines", name="Cycle time", line=dict(color=TEAL, width=2.5)), secondary_y=False)
    fig_sr.add_trace(go.Scatter(x=df_sw_rr["rr_lb_ton"], y=df_sw_rr["speed_loaded_kmh"],
                                mode="lines", name="Speed loaded", line=dict(color=GREEN, width=2, dash="dash")), secondary_y=True)
    fig_sr.add_trace(go.Scatter(x=df_sw_rr["rr_lb_ton"], y=df_sw_rr["speed_empty_kmh"],
                                mode="lines", name="Speed empty", line=dict(color=AMBER, width=2, dash="dot")), secondary_y=True)
    fig_sr.add_vline(x=rr_ideal,  line_dash="dash", line_color=GREEN, line_width=1.2, annotation_text=f"ideal {rr_ideal}")
    fig_sr.add_vline(x=rr_actual, line_dash="dash", line_color=RED,   line_width=1.2, annotation_text=f"aktual {rr_actual}")
    fig_sr.update_layout(**DL, title="RR → Cycle Time & Speed", legend=LEG)
    fig_sr.update_xaxes(**AX, title_text="RR (lb/ton)")
    fig_sr.update_yaxes(**AX, title_text="CT (min)", secondary_y=False)
    fig_sr.update_yaxes(**AX, title_text="Speed (km/h)", secondary_y=True)
    c2.plotly_chart(fig_sr, use_container_width=True, key="sr")

    # Distance sweep
    fig_sd = go.Figure()
    fig_sd.add_trace(go.Scatter(x=df_sw_d["dist_m"], y=df_sw_d["cycle_time_min"],
                                mode="lines", line=dict(color=PURPLE, width=2.5),
                                hovertemplate="<b>%{x}m</b><br>CT: %{y:.3f} min<extra></extra>"))
    fig_sd.add_vline(x=dist_m, line_dash="dash", line_color=GREEN, line_width=1.5,
                     annotation_text=f"{dist_m}m (current)", annotation_font_color=GREEN)
    fig_sd.update_layout(**DL, title="Haul Distance → Cycle Time", xaxis_title="Distance (m)", yaxis_title="CT (min)")
    ax_update(fig_sd)
    st.plotly_chart(fig_sd, use_container_width=True, key="sd")

# ══════════════════════════════════════════════════════════════════════════
#  TORNADO
# ══════════════════════════════════════════════════════════════════════════
with t_tor:
    st.markdown("<div class='sec-header'>Tornado Chart — Parameter Paling Sensitif (±20%)</div>", unsafe_allow_html=True)

    st.markdown(f"""
    <div class='bi-box info'>
      <div class='bi-title info'>Cara Baca Tornado Chart</div>
      <div class='bi-text'>
        Setiap parameter divariasikan ±20% dari baseline (grade=4.7%, RR={rr_actual} lb/ton, dist={dist_m}m).
        <b style='color:{TEAL}'>Bar biru</b> = efek penurunan 20% | <b style='color:{RED}'>Bar merah</b> = efek kenaikan 20%.
        <b>Swing = total range dampak.</b> Parameter paling atas = paling kritis dikendalikan.
      </div>
    </div>
    """, unsafe_allow_html=True)

    fig_t = go.Figure()
    for i, row in df_tor.iterrows():
        fig_t.add_trace(go.Bar(
            y=[row["parameter"]], x=[row["delta_low"]], orientation="h",
            marker_color=TEAL, name="−20%", showlegend=(i == 0),
            hovertemplate=f"<b>{row['parameter']}</b><br>−20%: {row['delta_low']:+.3f} min<extra></extra>",
        ))
        fig_t.add_trace(go.Bar(
            y=[row["parameter"]], x=[row["delta_high"]], orientation="h",
            marker_color=RED, name="+20%", showlegend=(i == 0),
            hovertemplate=f"<b>{row['parameter']}</b><br>+20%: {row['delta_high']:+.3f} min<extra></extra>",
        ))
        fig_t.add_annotation(x=1.1, y=row["parameter"],
                              text=f"swing {row['swing']:.3f} min", showarrow=False,
                              font=dict(color=AMBER, size=10))
    fig_t.add_vline(x=0, line_color="#3A6A8A", line_width=0.8)
    fig_t.update_layout(**DL, title="Tornado — Sensitivitas Cycle Time terhadap ±20% Parameter",
                        barmode="relative", xaxis_title="Delta CT (min)", legend=LEG,
                        xaxis_range=[-1.4, 1.6], height=350)
    ax_update(fig_t)
    st.plotly_chart(fig_t, use_container_width=True, key="tornado")

    st.markdown("<div class='sec-header'>Data Tornado</div>", unsafe_allow_html=True)
    st.dataframe(df_tor, use_container_width=True, hide_index=True)

# ══════════════════════════════════════════════════════════════════════════
#  HEATMAP
# ══════════════════════════════════════════════════════════════════════════
with t_hm:
    st.markdown("<div class='sec-header'>Heatmap 2D — Grade × RR → Cycle Time</div>", unsafe_allow_html=True)

    fig_hm = go.Figure(go.Heatmap(
        z=hm, x=[int(r) for r in rr], y=[f"{int(g)}%" for g in gr],
        colorscale="RdYlGn_r",
        colorbar=dict(title=dict(text="CT (min)", font=dict(color="#7AAABF")), tickfont=dict(color="#7AAABF")),
        hovertemplate="Grade: %{y}<br>RR: %{x} lb/ton<br>CT: %{z:.2f} min<extra></extra>",
    ))
    fig_hm.add_shape(type="line", x0=rr_ideal, x1=rr_ideal, y0=-0.5, y1=len(gr)-0.5,
                     line=dict(color="white", width=2, dash="dash"))
    fig_hm.add_shape(type="line", x0=rr_actual, x1=rr_actual, y0=-0.5, y1=len(gr)-0.5,
                     line=dict(color=RED, width=2, dash="dash"))
    fig_hm.add_annotation(x=rr_ideal,  y=len(gr)-0.5, text=f"ideal {rr_ideal}", showarrow=False,
                          font=dict(color="white", size=10), yshift=12)
    fig_hm.add_annotation(x=rr_actual, y=len(gr)-0.5, text=f"aktual {rr_actual}", showarrow=False,
                          font=dict(color=RED, size=10), yshift=12)
    fig_hm.update_layout(**DL, title="Heatmap: Grade × RR → Cycle Time (min)",
                         xaxis_title="RR (lb/ton)", yaxis_title="Grade (%)")
    ax_update(fig_hm)

    c1, c2 = st.columns([3, 1])
    c1.plotly_chart(fig_hm, use_container_width=True, key="heatmap")
    with c2:
        st.markdown(f"""
        <div class='bi-box critical'>
          <div class='bi-title critical'>Zona Merah (Worst)</div>
          <div class='bi-text'>Grade &gt;10% AND RR &gt;100<br>CT &gt; {hm.max():.2f} min</div>
        </div>
        <div class='bi-box good' style='margin-top:8px'>
          <div class='bi-title good'>Zona Hijau (Best)</div>
          <div class='bi-text'>Grade &lt;4% AND RR &lt;35<br>CT &lt; {hm.min():.2f} min</div>
        </div>
        """, unsafe_allow_html=True)
        st.metric("CT worst zone", f"{hm.max():.2f} min")
        st.metric("CT best zone",  f"{hm.min():.2f} min")
        st.metric("Range",         f"{hm.max()-hm.min():.2f} min")

# ══════════════════════════════════════════════════════════════════════════
#  WHAT-IF
# ══════════════════════════════════════════════════════════════════════════
with t_wif:
    st.markdown("<div class='sec-header'>What-If Scenarios — Kombinasi Perbaikan</div>", unsafe_allow_html=True)

    scenario_colors = [RED, AMBER, PURPLE, GREEN]
    fig_wif = make_subplots(specs=[[{"secondary_y": True}]])
    fig_wif.add_trace(
        go.Bar(name="Cycle time", x=df_wif["scenario"], y=df_wif["cycle_time_min"],
               marker_color=scenario_colors, marker_opacity=0.9,
               hovertemplate="<b>%{x}</b><br>CT: %{y:.3f} min<extra></extra>"),
        secondary_y=False
    )
    fig_wif.add_trace(
        go.Scatter(name="Fuel ratio", x=df_wif["scenario"], y=df_wif["fuel_ratio"],
                   mode="lines+markers", line=dict(color=TEAL, width=2),
                   marker=dict(size=9, color=TEAL),
                   hovertemplate="<b>%{x}</b><br>Fuel: %{y:.4f} L/BCM<extra></extra>"),
        secondary_y=True
    )
    for _, row in df_wif.iterrows():
        label = f"{row['cycle_time_min']:.3f}m"
        if row["delta_ct_pct"] != 0:
            label += f" ({row['delta_ct_pct']:+.1f}%)"
        fig_wif.add_annotation(x=row["scenario"], y=row["cycle_time_min"] + 0.03,
                               text=label, showarrow=False, font=dict(color="white", size=10))
    fig_wif.update_layout(**DL, title="What-If Scenarios — CT & Fuel Ratio", legend=LEG)
    fig_wif.update_xaxes(**AX)
    fig_wif.update_yaxes(**AX, title_text="Cycle time (min)", secondary_y=False)
    fig_wif.update_yaxes(**AX, title_text="Fuel ratio (L/BCM)", secondary_y=True)
    st.plotly_chart(fig_wif, use_container_width=True, key="whatif")

    # Scenario cards
    cols_wif = st.columns(4)
    for col, (_, row), color in zip(cols_wif, df_wif.iterrows(), scenario_colors):
        fp = fleet_productivity(row["cycle_time_min"], n_trucks, ops_hours)
        col.markdown(f"""
        <div class='kpi-card' style='border-left:3px solid {color}'>
          <div class='kpi-label'>{row["scenario"]}</div>
          <div class='kpi-value' style='color:{color}'>{row["cycle_time_min"]:.3f} min</div>
          <div class='kpi-sub' style='color:#3A6A8A'>
            {row["delta_ct_pct"]:+.1f}% vs aktual<br>
            {int(fp["total_cycles_day"])} cycles/hari
          </div>
        </div>
        """, unsafe_allow_html=True)

# ══════════════════════════════════════════════════════════════════════════
#  VALIDASI
# ══════════════════════════════════════════════════════════════════════════
with t_val:
    st.markdown("<div class='sec-header'>Validasi Model vs Jurnal Table 8</div>", unsafe_allow_html=True)

    val = validate_against_journal()
    summary = val.pop("_summary")

    if summary["all_pass"]:
        st.markdown(f"""
        <div class='bi-box good'>
          <div class='bi-title good'>SEMUA VALIDASI PASS — {summary['passed']}/{summary['total']}</div>
          <div class='bi-text'>Semua output model exact match dengan Jurnal GEOSAPTA Table 8.
          Model dapat digunakan dengan kepercayaan penuh untuk kasus PT Rahman Abdijaya.</div>
        </div>
        """, unsafe_allow_html=True)
    else:
        st.markdown(f"""
        <div class='bi-box critical'>
          <div class='bi-title critical'>VALIDASI PARTIAL — {summary['passed']}/{summary['total']}</div>
          <div class='bi-text'>Beberapa output tidak match. Cek parameter RR di sidebar.</div>
        </div>
        """, unsafe_allow_html=True)

    rows_val = []
    for metric, v in val.items():
        rows_val.append({
            "Metric":    metric.replace("_", " "),
            "Script":    v["computed"],
            "Jurnal":    v["expected"],
            "Delta":     v["delta"],
            "Status":    "PASS" if v["pass"] else "FAIL",
        })
    df_val = pd.DataFrame(rows_val)

    def color_pass(val):
        if val == "PASS": return "background-color:#1D6A40;color:white"
        if val == "FAIL": return "background-color:#7B2D2D;color:white"
        return ""

    st.dataframe(
        df_val.style.applymap(color_pass, subset=["Status"]).format({"Script": "{:.3f}", "Jurnal": "{:.3f}", "Delta": "{:+.3f}"}),
        use_container_width=True, hide_index=True
    )

# ══════════════════════════════════════════════════════════════════════════
#  BI INSIGHTS
# ══════════════════════════════════════════════════════════════════════════
with t_bi:
    st.markdown("<div class='sec-header'>Business Intelligence Insights</div>", unsafe_allow_html=True)

    n_crit_seg = (df_gap["overall_status"] == "CRITICAL").sum()
    n_warn_seg = (df_gap["overall_status"] == "WARNING").sum()
    n_cs_warn  = (df_gap["cs_status"] == "WARNING").sum()
    worst_g    = df_gap.loc[df_gap["grade_pct"].abs().idxmax()]
    avg_tr_red = df_gap["TR_reduction_kg"].mean()
    avg_tr_pct = avg_tr_red / df_gap["TR_actual_kg"].mean() * 100

    insights = [
        ("critical", "critical",
         f"Executive Summary — {n_crit_seg} CRITICAL, {n_warn_seg} WARNING dari {n_seg} segmen",
         f"Dari {n_seg} segmen yang dievaluasi, hanya {n_ok} ({n_ok/n_seg*100:.0f}%) memenuhi semua standar. "
         f"Masalah utama: {n_cs_warn} segmen cross slope di luar range 2–4%, "
         f"dan grade di A-B ({df_gap[df_gap.seg_id=='A-B']['grade_pct'].values[0]:.1f}%), "
         f"B-C ({df_gap[df_gap.seg_id=='B-C']['grade_pct'].values[0]:.1f}%), "
         f"E-F ({abs(df_gap[df_gap.seg_id=='E-F']['grade_pct'].values[0]):.1f}%) melebihi batas 8%.",
         "Summary"),
        ("critical", "critical",
         f"RR Aktual {rr_actual} lb/ton — {round((rr_actual-rr_ideal)/rr_ideal*100,0):.0f}% di atas ideal",
         f"Perbaikan RR dari {rr_actual} ke {rr_ideal} lb/ton menurunkan CT {ct_act:.3f} → {ct_idl:.3f} min "
         f"(−{d_ct:.3f} min/trip). Fleet impact: +{d_cyc} cycles/hari untuk {n_trucks} truck {ops_hours} jam. "
         f"Solusi: routine grading + water truck compaction. Tidak perlu perubahan geometri jalan.",
         "RR"),
        ("warn", "",
         f"Segmen kritis grade: {worst_g['seg_id']} = {abs(worst_g['grade_pct']):.2f}%",
         f"Grade {abs(worst_g['grade_pct']):.2f}% melebihi standar 8% sebesar {abs(worst_g['grade_pct'])-8:.2f}%. "
         f"TR aktual di segmen ini: {worst_g['TR_actual_kg']:,.0f} kg vs ideal {worst_g['TR_ideal_kg']:,.0f} kg. "
         f"Rekomendasi: cut/fill untuk reduksi grade ke ≤8%.",
         "Grade"),
        ("good", "good",
         f"Potensi reduksi TR rata-rata {avg_tr_pct:.1f}% hanya dari perbaikan RR",
         f"Jika RR diperbaiki {rr_actual}→{rr_ideal} lb/ton, rata-rata TR turun {avg_tr_red:.0f} kg ({avg_tr_pct:.1f}%). "
         f"Peningkatan speed loaded: {speed_loaded(rr_actual):.2f}→{speed_loaded(rr_ideal):.2f} km/h "
         f"(+{speed_loaded(rr_ideal)-speed_loaded(rr_actual):.2f} km/h). "
         f"Tidak memerlukan earthwork — hanya maintenance schedule.",
         "Resistance"),
        ("warn", "",
         f"{n_cs_warn}/{n_seg} segmen cross slope di luar standar drainase 2–4%",
         f"{n_cs_warn} segmen memiliki cross slope negatif atau >4%. Cross slope negatif (B-C, G-H, H-I, dll) "
         f"= air mengalir ke arah salah → genangan → softening subgrade → rutting → RR naik. "
         f"Solusi: grading ulang untuk reshape crown 3% sebelum musim hujan.",
         "Cross Slope"),
    ]

    for sev, box_cls, title, text, phase in insights:
        st.markdown(f"""
        <div class='bi-box {box_cls}'>
          <div style='display:flex;justify-content:space-between;align-items:center;margin-bottom:6px'>
            <div class='bi-title {sev}'>{title}</div>
            <span style='font-size:10px;padding:2px 8px;border-radius:4px;
              background:#1A2E44;color:#3A6A8A;font-family:monospace'>{phase}</span>
          </div>
          <div class='bi-text'>{text}</div>
        </div>
        """, unsafe_allow_html=True)

# ══════════════════════════════════════════════════════════════════════════
#  DATA & EXPORT
# ══════════════════════════════════════════════════════════════════════════
with t_data:
    st.markdown("<div class='sec-header'>Data Tables & Export</div>", unsafe_allow_html=True)

    sub1, sub2, sub3, sub4 = st.tabs(["Input", "Gap Analysis", "Sensitivity", "What-If"])
    with sub1:
        st.dataframe(df_raw, use_container_width=True, hide_index=True)
    with sub2:
        st.dataframe(df_gap.round(2), use_container_width=True, hide_index=True)
    with sub3:
        c1, c2 = st.columns(2)
        c1.markdown("**Grade Sweep**")
        c1.dataframe(df_sw_g.round(3), use_container_width=True, hide_index=True)
        c2.markdown("**RR Sweep**")
        c2.dataframe(df_sw_rr.round(3), use_container_width=True, hide_index=True)
        st.markdown("**Tornado**")
        st.dataframe(df_tor, use_container_width=True, hide_index=True)
    with sub4:
        st.dataframe(df_wif.round(3), use_container_width=True, hide_index=True)

    st.markdown("<br>", unsafe_allow_html=True)
    try:
        buf = io.BytesIO()
        with pd.ExcelWriter(buf, engine="openpyxl") as w:
            df_raw.to_excel(w,   sheet_name="Input Data",      index=False)
            df_gap.to_excel(w,   sheet_name="Gap Analysis",    index=False)
            df_tor.to_excel(w,   sheet_name="Tornado",         index=False)
            df_sw_g.to_excel(w,  sheet_name="Sweep Grade",     index=False)
            df_sw_rr.to_excel(w, sheet_name="Sweep RR",        index=False)
            df_sw_d.to_excel(w,  sheet_name="Sweep Distance",  index=False)
            df_wif.to_excel(w,   sheet_name="What-If",         index=False)
        st.download_button(
            "⬇ Export Semua Data ke Excel",
            data=buf.getvalue(),
            file_name="haul_road_analysis.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        )
    except Exception:
        st.info("pip install openpyxl untuk enable Excel export")

# ─────────────────────────────────────────────
#  FOOTER
# ─────────────────────────────────────────────
st.markdown(f"""
<div style='text-align:center;padding:24px;margin-top:32px;
  border-top:1px solid #1A2E44;font-family:monospace;font-size:11px;color:#1A3A5A'>
  Haul Road Performance Analyzer ·  by Nickholast Aditya Pratama · Phase 1 Gap Analysis + Phase 2 Sensitivity ·
  {SITE['name']} · {TRUCK['model']} · {SITE['road_name']}<br>
  Ref: {SITE['ref_paper']} |
  Method: KEPMEN 1827 · AASHTO · Tannant & Regensburg · Rimpull Interpolation
</div>
""", unsafe_allow_html=True)