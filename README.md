# Haul Road Analyzer
**Mining Road Engineering — Gap Analysis & Sensitivity Analysis**

> PT Rahman Abdijaya · Cat OHT 777-D · Jalan Amaris–Novotel
> Based on: Arip Wibowo Saputra et al., Jurnal GEOSAPTA Vol.5 No.1, 2019

---

## Quick Start

```bash
# 1. Clone / buka folder di VS Code
cd haul_road_portfolio

# 2. Buat virtual environment
python -m venv venv
source venv/bin/activate        # Mac/Linux
venv\Scripts\activate           # Windows

# 3. Install dependencies
pip install -r requirements.txt

# 4. Run Streamlit dashboard
streamlit run app.py

# 5. Run tests
pytest tests/ -v
```

Browser otomatis terbuka di `http://localhost:8501`

---

## Struktur Project

```
haul_road_portfolio/
├── app.py                  ← Streamlit dashboard (entry point)
├── requirements.txt
├── README.md
│
├── src/
│   ├── __init__.py
│   ├── config.py           ← Semua konstanta: truck specs, standar, ranges
│   └── engineering.py      ← Semua fungsi kalkulasi (Phase 1 & 2)
│
├── data/
│   ├── segments_geometry.csv   ← Input data 14 segmen dari jurnal
│   └── truck_specs.csv         ← Spesifikasi Cat 777D
│
├── tests/
│   └── test_engineering.py  ← 25+ unit tests, validasi vs jurnal
│
├── notebooks/               ← Jupyter notebooks (Phase 2 exploration)
├── assets/                  ← Charts, screenshots
└── .vscode/
    ├── settings.json        ← Python interpreter, formatter
    └── launch.json          ← Debug configs untuk Streamlit & pytest
```

---

## Fitur Dashboard

| Tab | Isi |
|-----|-----|
| Overview | Status donut, grade chart, effective grade, TR reduction |
| Phase 1 — Gap | Width vs minimum, grade, tabel gap analysis per segmen |
| Resistance | TR aktual vs ideal, tabel resistance detail |
| Phase 2 — Sensitivity | OAT sweep: grade, RR, distance |
| Tornado Chart | ±20% sensitivity ranking semua parameter |
| Heatmap | 2D grade × RR → cycle time |
| What-If | 4 skenario perbaikan komparatif |
| Validasi | Semua output vs journal Table 8 |
| BI Insights | Executive summary + rekomendasi prioritas |
| Data & Export | Semua tabel + Excel export |

---

## Key Insights (dari analisis Phase 1 & 2)

- **12/14 segmen (86%) berstatus WARNING** — penyebab utama: cross slope tidak memenuhi standar 2–4%
- **Grade kritis**: A-B (8.3%), B-C (9.0%), E-F (8.6%) melebihi batas KEPMEN 8%
- **RR aktual 124 lb/ton** vs ideal 65 lb/ton — perbaikan menghasilkan CT −16.3% per trip
- **Fleet impact**: +520 cycles/hari (10 truck, 20 jam) jika RR diperbaiki ke ideal
- **Tornado**: haul distance paling sensitif (swing 1.793 min), diikuti RR (0.745 min)
- **Heatmap zona merah**: grade >10% AND RR >100 lb/ton → CT >4.8 min

---

## Validasi Model

Semua output telah divalidasi terhadap Jurnal GEOSAPTA Table 8 (delta < 0.05):

| Metric | Script | Jurnal |
|--------|--------|--------|
| Speed loaded actual | 18.59 km/h | 18.59 km/h |
| Speed loaded ideal  | 21.59 km/h | 21.59 km/h |
| Speed empty actual  | 20.73 km/h | 20.73 km/h |
| Speed empty ideal   | 25.59 km/h | 25.59 km/h |
| Total delta CT/cycle | 0.73 min | 0.73 min |

---

## Adaptasi ke Tambang Lain

1. Edit `src/config.py` → ganti TRUCK specs dan SITE parameters
2. Ganti `data/segments_geometry.csv` dengan data segmen baru
3. Re-run dashboard — semua kalkulasi otomatis menyesuaikan

---

## Roadmap (Phase 3+)

- **Phase 3**: Monte Carlo simulation — P10/P50/P90 cycle time dari distribusi parameter
- **Phase 4**: ML predictive maintenance — butuh ≥50 segmen data historis
- **Phase 5**: Real-time decision support system — integrasi sensor/dispatch data

---

## References

- KEPMEN ESDM No. 1827 K/30/MEM/2018
- AASHTO Manual Rural Highway Design
- Tannant & Regensburg — Guidelines for Mine Haul Road Design (ResearchGate)
- KSU CE417 — Loading and Hauling (grade & rolling resistance formulas)
- Arip Wibowo Saputra et al., Jurnal GEOSAPTA Vol.5 No.1, Jan 2019
