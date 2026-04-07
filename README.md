# 🏷️ ZATCA TaxSense Pro — Saudi Taxation Engine for Clothing Retailers
### نظام الضريبة الذكي لمتاجر الملابس

[![Streamlit](https://img.shields.io/badge/Streamlit-1.35-FF4B4B?logo=streamlit)](https://streamlit.io)
[![Python](https://img.shields.io/badge/Python-3.11-3776AB?logo=python)](https://python.org)
[![ZATCA](https://img.shields.io/badge/ZATCA-Phase%202%20Compliant-006C35)](https://zatca.gov.sa)
[![License](https://img.shields.io/badge/License-MIT-green)](LICENSE)

> **The most domain-specific Saudi tax compliance tool for clothing retailers** — covering VAT, Zakat, Nitaqat, ZATCA e-invoicing, anomaly detection, and scenario planning in one production-grade Streamlit app.

---

## 🔥 Why This Exists

Most Saudi retail businesses — especially clothing shops — suffer from:

| Problem | Impact |
|---|---|
| Misclassifying children's clothing as VAT-exempt (it's NOT in KSA) | Underpayment penalties up to 100% of tax |
| Manual quarterly VAT return calculations | Errors, late filing (min SAR 1,000 fine) |
| No Zakat vs Income Tax split for mixed-ownership firms | GAZT audit risk |
| No visibility on Nitaqat cost impact before hiring | Budget surprises |
| ZATCA Phase 2 e-invoice non-compliance | Up to SAR 50,000 per violation |

**TaxSense Pro solves all five problems in one app.**

---

## 🧩 Modules

### 1. 🏠 Dashboard
- Live Hijri/Gregorian date display
- 12-month quarterly VAT deadline calendar
- Clothing supply classification table (Standard / Zero / Exempt)
- Critical KSA-specific rule: **children's clothing is 15% VAT, NOT exempt**

### 2. 📊 VAT Return Calculator
- Full ZATCA Form VAT-01 simulator
- Output VAT → Input VAT → Net Payable waterfall chart
- **Late payment penalty calculator** (2%/month, capped at 50%)
- **Late filing penalty** (2.5% of tax, min SAR 1,000)

### 3. 🕌 Zakat Calculator
- GAZT simplified Zakat base method for trading companies
- Separates zakatable vs non-zakatable assets
- Mixed-ownership split: Zakat (Saudi share) + Income Tax (foreign share)
- Asset composition donut chart

### 4. 🔍 Transaction Anomaly Detector
- Upload CSV or use synthetic 50-transaction dataset
- Rule-based engine flags: VAT_MISMATCH, ROUND_NUMBER, HIGH_VALUE, MISSING_CREDIT_NOTE
- Color-coded anomaly table with downloadable CSV report
- Anomaly frequency bar chart

### 5. ⚖️ Nitaqat Compliance Modeler
- Current Saudization band gauge (Platinum / High Green / Low Green / Yellow / Red)
- Calculates exact number of Saudi hires needed to reach target band
- Monthly and annual extra cost of compliance
- Part-timer optimization tip (0.5 Nitaqat unit)

### 6. 🧾 ZATCA E-Invoice Builder
- Phase 2 compliant invoice layout (Arabic + English)
- Multi-line item entry with automatic VAT calculation
- Hijri date on invoice (ZATCA requirement)
- SHA-256 QR code hash (TLV-style)

### 7. 📅 Tax Calendar & Deadlines
- Full 2025–2026 compliance calendar (VAT, Zakat, Nitaqat, E-Invoice audits)
- Days-away countdown with status flags
- Interactive timeline scatter chart

### 8. 📈 Profit-After-Tax Scenario Planner
- Revenue sensitivity analysis at 5 scales (70%–130%)
- EBITDA vs Net Profit after VAT, Zakat, and Nitaqat costs
- Net margin by scenario

### 9. ℹ️ ZATCA Rules Reference
- Clothing-specific VAT rules (incl. the children's wear myth)
- Registration thresholds, filing frequencies, penalty schedule
- Quick-reference tables for compliance teams

---

## 🚀 Run Locally (Google Colab → Streamlit)

### Option A: Streamlit Cloud (Recommended)
```bash
# 1. Fork this repo to your GitHub
# 2. Go to https://share.streamlit.io
# 3. Connect your GitHub, select this repo, set app.py as entry point
# 4. Deploy — done in ~60 seconds
```

### Option B: Google Colab
```python
# Cell 1 — Install
!pip install streamlit pyngrok -q

# Cell 2 — Run with tunnel
from pyngrok import ngrok
import subprocess, time

proc = subprocess.Popen(["streamlit", "run", "app.py", "--server.port", "8501"])
time.sleep(3)
public_url = ngrok.connect(8501)
print("App URL:", public_url)
```

### Option C: Local
```bash
git clone https://github.com/BaqarW-tech/zatca-taxsense-pro
cd zatca-taxsense-pro
pip install -r requirements.txt
streamlit run app.py
```

---

## 🗂️ Project Structure

```
zatca-taxsense-pro/
├── app.py              # Main Streamlit application (9 modules)
├── requirements.txt    # Pinned dependencies for Streamlit Cloud
├── runtime.txt         # Python 3.11 pin
└── README.md           # This file
```

---

## ⚙️ Technical Stack

| Layer | Technology |
|---|---|
| Frontend | Streamlit 1.35 + Custom CSS (Space Mono / IBM Plex Sans Arabic) |
| Visualization | Plotly (waterfall, gauge, timeline, donut, grouped bar) |
| Data | Pandas 2.2 + NumPy |
| Tax Engine | Pure Python rules engine (no external tax API dependency) |
| Anomaly Detection | Rule-based heuristics (extendable to Isolation Forest) |
| Date | Custom Hijri conversion algorithm |
| QR | SHA-256 TLV hash (ZATCA Phase 2 compatible) |

---

## 📐 Tax Rules Implemented

| Rule | Source | Value |
|---|---|---|
| Standard VAT Rate | ZATCA VAT Law | 15% |
| Zero-Rated (Exports) | ZATCA VAT Law Art. 33 | 0% |
| Children's Clothing | ZATCA FAQ 2024 | **15% (NOT exempt)** |
| Zakat Rate | GAZT Regulation | 2.5% on zakatable base |
| Late Payment Penalty | ZATCA Penalty Schedule | 2% / month, max 50% |
| Late Filing Penalty | ZATCA Penalty Schedule | 2.5%, min SAR 1,000 |
| Mandatory VAT Registration | ZATCA VAT Law | SAR 375,000 turnover |
| E-Invoice Phase 2 | ZATCA Resolution 2021 | SHA-256 + TLV QR |
| Nitaqat Retail Band (Green) | MHRSD 2024 | 30–40% Saudi |

---

## 🎯 Portfolio Value Proposition

This project demonstrates:
- **Domain expertise**: Deep KSA tax law knowledge, not generic tutorials
- **Problem-solving**: Addresses real pain points of Saudi clothing retailers
- **Technical breadth**: Full-stack data app (UI + computation + visualization + export)
- **Vision 2030 alignment**: Saudization modeling directly supports national employment targets
- **Bilingual interface**: Arabic + English for Saudi market readiness

---

## 👤 Author

**Muhammad Baqar Wagan**
MA Economics | Accounting Background | Saudi Market Specialist

[![GitHub](https://img.shields.io/badge/GitHub-BaqarW--tech-181717?logo=github)](https://github.com/BaqarW-tech)

---

## ⚖️ Disclaimer

This application is for educational and planning purposes only. Tax figures are based on publicly available ZATCA regulations as of 2024. Always verify obligations with a licensed Saudi tax advisor (محاسب قانوني معتمد).

---

*Built to stand out. Designed for the KSA market. Powered by domain expertise.*
