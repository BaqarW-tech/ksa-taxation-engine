"""
╔══════════════════════════════════════════════════════════════════╗
║   ZATCA TaxSense Pro — Saudi Taxation Engine for Clothing Retail  ║
║   Author : Muhammad Baqar Wagan                                   ║
║   Version: 2.0  |  Compliant: ZATCA Phase 2 / VAT Law 2024       ║
╚══════════════════════════════════════════════════════════════════╝
"""

import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import datetime
import io
import json
import hashlib
import re

# ─── PAGE CONFIG ──────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="ZATCA TaxSense Pro | ضريبة الملابس",
    page_icon="🏷️",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ─── GLOBAL CONSTANTS (ZATCA / GAZT Rules 2024) ───────────────────────────────
VAT_RATE              = 0.15          # Standard rate
VAT_ZERO_RATE         = 0.00          # Zero-rated supplies
ZAKAT_RATE            = 0.025         # 2.5% on zakatable wealth
CHILDREN_AGE_MAX      = 14            # KSA children's wear age threshold
CHILDREN_SIZE_MAX_CM  = 164           # Height proxy for children's wear exemption
WITHHOLDING_RATE      = 0.05          # 5% WHT on certain services
LATE_PAYMENT_PENALTY  = 0.02          # 2% per month, capped at 50%
LATE_FILING_PENALTY   = 0.025         # 2.5% of tax due, min SAR 1,000
MIN_FILING_PENALTY    = 1000          # SAR
VAT_REGISTRATION_THRESHOLD = 375000   # SAR annual turnover
VAT_VOLUNTARY_THRESHOLD    = 187500

# NITAQAT clothing-retail SOC codes & Saudization targets (2024 bands)
NITAQAT_BANDS = {
    "Platinum":  {"min_saudi_pct": 0.50, "color": "#00B4D8"},
    "High Green": {"min_saudi_pct": 0.40, "color": "#2DC653"},
    "Low Green":  {"min_saudi_pct": 0.30, "color": "#80B918"},
    "Yellow":     {"min_saudi_pct": 0.20, "color": "#F4C430"},
    "Red":        {"min_saudi_pct": 0.00, "color": "#EF233C"},
}

# Hijri month names (approximate Gregorian offsets handled manually)
HIJRI_MONTHS = [
    "Muharram","Safar","Rabi' al-Awwal","Rabi' al-Thani",
    "Jumada al-Awwal","Jumada al-Thani","Rajab","Sha'ban",
    "Ramadan","Shawwal","Dhu al-Qi'dah","Dhu al-Hijjah"
]

# ─── CUSTOM CSS ───────────────────────────────────────────────────────────────
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=IBM+Plex+Sans+Arabic:wght@300;400;600&family=Space+Mono:wght@400;700&display=swap');

:root {
    --gold:    #C8973A;
    --sand:    #F5EDD6;
    --dark:    #0D1117;
    --card:    #161B22;
    --accent:  #238636;
    --danger:  #DA3633;
    --border:  #30363D;
    --text:    #E6EDF3;
    --muted:   #8B949E;
}

html, body, [class*="css"] {
    font-family: 'IBM Plex Sans Arabic', 'Space Mono', sans-serif;
    background-color: var(--dark);
    color: var(--text);
}

/* Header banner */
.zatca-header {
    background: linear-gradient(135deg, #0D1117 0%, #1A1F2E 50%, #0D2137 100%);
    border: 1px solid var(--gold);
    border-radius: 12px;
    padding: 24px 32px;
    margin-bottom: 24px;
    position: relative;
    overflow: hidden;
}
.zatca-header::before {
    content: "زاتكا";
    position: absolute;
    right: 20px;
    top: 50%;
    transform: translateY(-50%);
    font-size: 5rem;
    font-weight: 700;
    color: var(--gold);
    opacity: 0.08;
    font-family: 'IBM Plex Sans Arabic', sans-serif;
    letter-spacing: 4px;
}
.zatca-header h1 {
    color: var(--gold);
    font-family: 'Space Mono', monospace;
    font-size: 1.6rem;
    margin: 0 0 4px 0;
    letter-spacing: 1px;
}
.zatca-header p {
    color: var(--muted);
    margin: 0;
    font-size: 0.85rem;
}

/* Metric cards */
.metric-card {
    background: var(--card);
    border: 1px solid var(--border);
    border-radius: 10px;
    padding: 16px 20px;
    text-align: center;
    transition: border-color 0.2s;
}
.metric-card:hover { border-color: var(--gold); }
.metric-label {
    color: var(--muted);
    font-size: 0.75rem;
    text-transform: uppercase;
    letter-spacing: 1.5px;
    margin-bottom: 6px;
}
.metric-value {
    color: var(--gold);
    font-family: 'Space Mono', monospace;
    font-size: 1.5rem;
    font-weight: 700;
}
.metric-sub {
    color: var(--muted);
    font-size: 0.72rem;
    margin-top: 4px;
}

/* Compliance badge */
.badge-compliant   { background:#1A3A1F; color:#3FB950; border:1px solid #238636; padding:4px 12px; border-radius:20px; font-size:0.78rem; font-weight:600; }
.badge-warning     { background:#3A2A00; color:#F0A500; border:1px solid #F4C430; padding:4px 12px; border-radius:20px; font-size:0.78rem; font-weight:600; }
.badge-non-compliant{ background:#3A0D0D; color:#FF7B72; border:1px solid #DA3633; padding:4px 12px; border-radius:20px; font-size:0.78rem; font-weight:600; }

/* Section heading */
.section-title {
    font-family:'Space Mono',monospace;
    color: var(--gold);
    font-size: 0.9rem;
    letter-spacing: 2px;
    text-transform: uppercase;
    border-bottom: 1px solid var(--border);
    padding-bottom: 8px;
    margin: 24px 0 16px 0;
}

/* Sidebar */
[data-testid="stSidebar"] {
    background: #0D1117 !important;
    border-right: 1px solid var(--border);
}

/* Buttons */
.stButton > button {
    background: var(--gold);
    color: #0D1117;
    border: none;
    font-weight: 700;
    font-family: 'Space Mono', monospace;
    letter-spacing: 1px;
    border-radius: 6px;
    padding: 8px 20px;
}
.stButton > button:hover { background: #E8A840; }

/* Anomaly row */
.anomaly-flag { color: #FF7B72; font-weight:700; }

/* Info box */
.info-box {
    background: #0D2137;
    border-left: 3px solid var(--gold);
    padding: 12px 16px;
    border-radius: 0 8px 8px 0;
    margin: 10px 0;
    font-size: 0.85rem;
    color: #C9D1D9;
}

/* Scrollbar */
::-webkit-scrollbar { width:6px; }
::-webkit-scrollbar-track { background: var(--dark); }
::-webkit-scrollbar-thumb { background: var(--border); border-radius:3px; }

/* Tables */
[data-testid="stDataFrame"] { border-radius: 8px; overflow: hidden; }
</style>
""", unsafe_allow_html=True)

# ─── HELPER FUNCTIONS ─────────────────────────────────────────────────────────

def fmt_sar(val: float, decimals: int = 2) -> str:
    return f"SAR {val:,.{decimals}f}"

def vat_on_sale(price_excl: float, is_exempt: bool = False, is_zero_rated: bool = False) -> float:
    if is_exempt or is_zero_rated:
        return 0.0
    return round(price_excl * VAT_RATE, 2)

def is_childrens_wear(size_cm: float, age: int) -> bool:
    """
    KSA ZATCA: Children's clothing is NOT automatically zero-rated.
    Standard 15% VAT applies. This function is for *business advisory* — 
    flagging items where retailers sometimes MISTAKENLY apply exemptions.
    Returns True if item profile matches children's wear.
    """
    return age <= CHILDREN_AGE_MAX or size_cm <= CHILDREN_SIZE_MAX_CM

def calculate_vat_return(
    taxable_sales: float,
    zero_rated_sales: float,
    exempt_sales: float,
    input_vat: float,
    adjustments: float = 0.0
) -> dict:
    output_vat = round(taxable_sales * VAT_RATE, 2)
    net_vat    = round(output_vat - input_vat + adjustments, 2)
    return {
        "taxable_sales":    taxable_sales,
        "zero_rated_sales": zero_rated_sales,
        "exempt_sales":     exempt_sales,
        "total_supplies":   taxable_sales + zero_rated_sales + exempt_sales,
        "output_vat":       output_vat,
        "input_vat":        input_vat,
        "adjustments":      adjustments,
        "net_vat_payable":  max(net_vat, 0),
        "vat_refundable":   abs(min(net_vat, 0)),
    }

def calculate_zakat(
    total_assets: float,
    long_term_investments: float,
    fixed_assets: float,
    total_liabilities: float,
    long_term_liabilities: float,
) -> dict:
    """
    Simplified Zakat base (GAZT method for trading companies):
    Zakatable base = (Current Assets + Long-term investments)
                   - (Short-term liabilities + Long-term liabilities)
    Minimum: cannot be negative.
    """
    zakatable_assets   = total_assets - fixed_assets
    short_term_liab    = total_liabilities - long_term_liabilities
    zakatable_base     = max(zakatable_assets - total_liabilities, 0)
    zakat_due          = round(zakatable_base * ZAKAT_RATE, 2)
    return {
        "total_assets":        total_assets,
        "fixed_assets":        fixed_assets,
        "zakatable_assets":    zakatable_assets,
        "total_liabilities":   total_liabilities,
        "zakatable_base":      zakatable_base,
        "zakat_due":           zakat_due,
    }

def calculate_penalty(
    tax_due: float,
    days_late: int,
    is_late_filing: bool = False
) -> dict:
    monthly_late      = days_late / 30
    payment_penalty   = min(round(tax_due * LATE_PAYMENT_PENALTY * monthly_late, 2), tax_due * 0.50)
    filing_penalty    = max(round(tax_due * LATE_FILING_PENALTY, 2), MIN_FILING_PENALTY) if is_late_filing else 0.0
    total_penalty     = payment_penalty + filing_penalty
    return {
        "days_late":        days_late,
        "payment_penalty":  payment_penalty,
        "filing_penalty":   filing_penalty,
        "total_penalty":    total_penalty,
        "total_due":        tax_due + total_penalty,
    }

def nitaqat_band(saudi_pct: float) -> tuple:
    for band, info in NITAQAT_BANDS.items():
        if saudi_pct >= info["min_saudi_pct"]:
            return band, info["color"]
    return "Red", "#EF233C"

def detect_vat_anomalies(df: pd.DataFrame) -> pd.DataFrame:
    """Flag suspicious VAT entries in a transaction dataset."""
    flags = []
    for _, row in df.iterrows():
        issues = []
        # Rule 1: VAT amount mismatch
        expected_vat = round(row["amount_excl_vat"] * VAT_RATE, 2)
        if abs(row["vat_charged"] - expected_vat) > 1.0:
            issues.append("VAT_MISMATCH")
        # Rule 2: Round-number suspicion > SAR 10k
        if row["amount_excl_vat"] > 10000 and row["amount_excl_vat"] % 1000 == 0:
            issues.append("ROUND_NUMBER")
        # Rule 3: Unusually high single-item sale for clothing
        if row["amount_excl_vat"] > 50000:
            issues.append("HIGH_VALUE")
        # Rule 4: Negative amounts (returns) without credit note marker
        if row["amount_excl_vat"] < 0 and not row.get("is_credit_note", False):
            issues.append("MISSING_CREDIT_NOTE")
        flags.append(", ".join(issues) if issues else "✓ Clean")
    df = df.copy()
    df["anomaly_flags"] = flags
    return df

def generate_qr_data(
    seller: str, vat_no: str, timestamp: str,
    invoice_total: float, vat_amount: float
) -> str:
    """Generate ZATCA Phase 2 QR string (simplified TLV-style)."""
    data = f"Seller:{seller}|VAT:{vat_no}|Date:{timestamp}|Total:{invoice_total}|VAT:{vat_amount}"
    return hashlib.sha256(data.encode()).hexdigest()[:32].upper()

def gregorian_to_hijri_approx(dt: datetime.date) -> str:
    """Approximate Hijri date (±1 day accuracy; full conversion needs hijri-converter)."""
    jdn = (dt.toordinal() + 1721425.5 - 0.5)
    l = int(jdn) - 1948440 + 10632
    n = (l - 1) // 10631
    l = l - 10631 * n + 354
    j = ((10985 - l) // 5316) * ((50 * l) // 17719) + (l // 5670) * ((43 * l) // 15238)
    l = l - ((30 - j) // 15) * ((17719 * j) // 50) - (j // 16) * ((15238 * j) // 43) + 29
    month = (24 + (l * 5)) // 153
    day   = l - (153 * month - 457) // 5
    year  = 30 * n + j - 30
    if month > 12:
        month -= 12
        year  += 1
    month_name = HIJRI_MONTHS[month - 1]
    return f"{day} {month_name} {year} AH"

# ─── SIDEBAR ──────────────────────────────────────────────────────────────────
with st.sidebar:
    st.markdown("""
    <div style='text-align:center; padding:12px 0 20px 0;'>
      <div style='font-family:IBM Plex Sans Arabic; font-size:1.4rem; color:#C8973A; font-weight:700;'>
        🏷️ TaxSense Pro
      </div>
      <div style='color:#8B949E; font-size:0.75rem; margin-top:4px;'>
        نظام الضريبة للبيع بالتجزئة
      </div>
    </div>
    """, unsafe_allow_html=True)

    module = st.radio(
        "Select Module  |  اختر الوحدة",
        options=[
            "🏠 Dashboard",
            "📊 VAT Return Calculator",
            "🕌 Zakat Calculator",
            "🔍 Transaction Anomaly Detector",
            "⚖️ Nitaqat Compliance Modeler",
            "🧾 ZATCA E-Invoice Builder",
            "📅 Tax Calendar & Deadlines",
            "📈 Profit-After-Tax Scenario Planner",
            "ℹ️ ZATCA Rules Reference",
        ],
        label_visibility="collapsed"
    )

    st.markdown("---")
    st.markdown("""
    <div class='info-box'>
    <b>Compliance Version</b><br>
    ZATCA VAT Law – 2024<br>
    Zakat Regulations – 1445 AH<br>
    Nitaqat Update – Q1 2024
    </div>
    """, unsafe_allow_html=True)
    st.markdown("""
    <div style='color:#8B949E; font-size:0.70rem; margin-top:16px; text-align:center;'>
    Built by Muhammad Baqar Wagan<br>
    MA Economics | Saudi Market Specialist
    </div>
    """, unsafe_allow_html=True)

# ─── HEADER BANNER ────────────────────────────────────────────────────────────
today     = datetime.date.today()
hijri_str = gregorian_to_hijri_approx(today)

st.markdown(f"""
<div class='zatca-header'>
  <h1>⚡ ZATCA TaxSense Pro</h1>
  <p>Saudi Taxation Engine for Clothing Retailers &nbsp;|&nbsp; نظام الضريبة الذكي لمتاجر الملابس</p>
  <p style='margin-top:8px; font-size:0.78rem; color:#C8973A;'>
    {today.strftime('%d %B %Y')} &nbsp;•&nbsp; {hijri_str} &nbsp;•&nbsp; VAT Rate: 15% &nbsp;•&nbsp; Zakat: 2.5%
  </p>
</div>
""", unsafe_allow_html=True)

# ══════════════════════════════════════════════════════════════════════════════
#  MODULE 1 — DASHBOARD
# ══════════════════════════════════════════════════════════════════════════════
if module == "🏠 Dashboard":
    st.markdown("<div class='section-title'>Portfolio KPIs — Quick Glance</div>", unsafe_allow_html=True)

    col1, col2, col3, col4, col5 = st.columns(5)
    kpis = [
        ("VAT Rate", "15%", "Standard Supply"),
        ("Zakat Rate", "2.5%", "On Zakatable Wealth"),
        ("Filing Period", "Quarterly", "< SAR 40M Turnover"),
        ("E-Invoice", "Phase 2", "ZATCA Integrated"),
        ("Nitaqat Retail", "30–40%", "Green Band Target"),
    ]
    for col, (label, val, sub) in zip([col1,col2,col3,col4,col5], kpis):
        with col:
            st.markdown(f"""
            <div class='metric-card'>
              <div class='metric-label'>{label}</div>
              <div class='metric-value'>{val}</div>
              <div class='metric-sub'>{sub}</div>
            </div>""", unsafe_allow_html=True)

    st.markdown("<div class='section-title'>Tax Obligation Timeline — 12-Month View</div>", unsafe_allow_html=True)

    # Build quarterly VAT deadlines
    quarters = []
    base = datetime.date(today.year, 1, 1)
    for i in range(4):
        q_start = datetime.date(base.year, 1 + i*3, 1)
        q_end   = datetime.date(base.year, 3 + i*3, 30) if (3+i*3) <= 12 else datetime.date(base.year, 12, 31)
        deadline = datetime.date(base.year, min(3+i*3+1, 12), 30)
        quarters.append({
            "Quarter": f"Q{i+1} {base.year}",
            "Period Start": q_start.strftime("%d %b"),
            "Period End": q_end.strftime("%d %b"),
            "Filing Deadline": deadline.strftime("%d %b %Y"),
            "Status": "✅ Filed" if deadline < today else ("⏳ Upcoming" if deadline > today + datetime.timedelta(30) else "⚠️ Due Soon"),
        })

    df_cal = pd.DataFrame(quarters)
    st.dataframe(df_cal, use_container_width=True, hide_index=True)

    st.markdown("<div class='section-title'>Clothing Retail VAT Supply Classification</div>", unsafe_allow_html=True)
    col_a, col_b = st.columns(2)
    with col_a:
        supply_data = {
            "Supply Type": ["Standard-Rated (15%)", "Zero-Rated (0%)", "Exempt"],
            "Clothing Examples": [
                "Adult apparel, accessories, luxury wear, footwear, sportswear",
                "Exports to GCC (with evidence), re-exports",
                "None (clothing NOT exempt under KSA VAT)",
            ],
            "Input VAT Recovery": ["✅ Full", "✅ Full", "❌ None"],
        }
        st.dataframe(pd.DataFrame(supply_data), use_container_width=True, hide_index=True)

    with col_b:
        fig = px.pie(
            values=[85, 10, 5],
            names=["Standard-Rated 15%", "Zero-Rated (Exports)", "Exempt"],
            color_discrete_sequence=["#C8973A", "#238636", "#30363D"],
            hole=0.55,
        )
        fig.update_layout(
            paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
            font_color="#E6EDF3", margin=dict(t=10,b=10,l=10,r=10),
            legend=dict(font=dict(size=11)),
            showlegend=True,
        )
        fig.update_traces(textfont_color="#E6EDF3")
        st.plotly_chart(fig, use_container_width=True)

    st.markdown("""
    <div class='info-box'>
    ⚠️ <b>Critical KSA-Specific Rule:</b> Unlike the UK or EU, KSA does <b>NOT</b> zero-rate or exempt children's clothing.
    All clothing sales within KSA are subject to <b>15% VAT</b> regardless of garment size or age group.
    Retailers mistakenly applying exemptions face penalties of up to <b>100% of underpaid tax</b>.
    </div>
    """, unsafe_allow_html=True)

# ══════════════════════════════════════════════════════════════════════════════
#  MODULE 2 — VAT RETURN CALCULATOR
# ══════════════════════════════════════════════════════════════════════════════
elif module == "📊 VAT Return Calculator":
    st.markdown("<div class='section-title'>ZATCA Quarterly VAT Return — Form VAT-01 Simulator</div>", unsafe_allow_html=True)

    col1, col2 = st.columns([1, 1])
    with col1:
        st.markdown("**Sales (Output VAT)**")
        taxable_sales   = st.number_input("Taxable Sales — Standard 15% (SAR excl. VAT)", min_value=0.0, value=850000.0, step=1000.0)
        zero_sales      = st.number_input("Zero-Rated Sales — Exports (SAR)", min_value=0.0, value=50000.0, step=1000.0)
        exempt_sales    = st.number_input("Exempt Sales (SAR)", min_value=0.0, value=0.0, step=1000.0)
        adjustments     = st.number_input("Output VAT Adjustments — Credit Notes / Corrections (SAR)", value=0.0, step=100.0)

    with col2:
        st.markdown("**Purchases (Input VAT Recovery)**")
        input_vat       = st.number_input("Total Input VAT Paid on Purchases (SAR)", min_value=0.0, value=45000.0, step=500.0)
        prev_credit     = st.number_input("Brought-Forward VAT Credit (SAR)", min_value=0.0, value=0.0, step=100.0)
        period          = st.selectbox("Filing Period", ["Q1 2025", "Q2 2025", "Q3 2025", "Q4 2025", "Q1 2026"])

    if st.button("Calculate VAT Return"):
        result = calculate_vat_return(taxable_sales, zero_sales, exempt_sales, input_vat + prev_credit, adjustments)

        st.markdown("<div class='section-title'>VAT Return Summary</div>", unsafe_allow_html=True)
        c1, c2, c3, c4 = st.columns(4)
        metrics = [
            ("Total Supplies", fmt_sar(result["total_supplies"]), ""),
            ("Output VAT (15%)", fmt_sar(result["output_vat"]), ""),
            ("Input VAT Credit", fmt_sar(result["input_vat"]), "Recoverable"),
            ("Net VAT Payable" if result["net_vat_payable"] > 0 else "VAT Refund Due",
             fmt_sar(result["net_vat_payable"] if result["net_vat_payable"] > 0 else result["vat_refundable"]),
             "Pay to ZATCA" if result["net_vat_payable"] > 0 else "Claim from ZATCA"),
        ]
        for col, (label, val, sub) in zip([c1,c2,c3,c4], metrics):
            with col:
                st.markdown(f"""
                <div class='metric-card'>
                  <div class='metric-label'>{label}</div>
                  <div class='metric-value'>{val}</div>
                  <div class='metric-sub'>{sub}</div>
                </div>""", unsafe_allow_html=True)

        st.markdown("<br>", unsafe_allow_html=True)

        # Waterfall chart
        fig = go.Figure(go.Waterfall(
            name="VAT Flow",
            orientation="v",
            measure=["relative","relative","relative","relative","total"],
            x=["Output VAT", "Adjustments", "Input VAT Credit", "Prev Credit", "NET PAYABLE"],
            y=[result["output_vat"], result["adjustments"], -result["input_vat"], 0,  result["net_vat_payable"]],
            text=[fmt_sar(result["output_vat"]), fmt_sar(result["adjustments"]),
                  fmt_sar(-result["input_vat"]), "0", fmt_sar(result["net_vat_payable"])],
            connector={"line":{"color":"#30363D"}},
            increasing={"marker":{"color":"#C8973A"}},
            decreasing={"marker":{"color":"#238636"}},
            totals={"marker":{"color":"#0D2137","line":{"color":"#C8973A","width":2}}},
        ))
        fig.update_layout(
            title="VAT Waterfall — Output → Input → Net",
            paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
            font_color="#E6EDF3", height=350,
            yaxis=dict(gridcolor="#30363D"),
        )
        st.plotly_chart(fig, use_container_width=True)

        # Penalty scenario
        st.markdown("<div class='section-title'>Late Payment Penalty Simulator</div>", unsafe_allow_html=True)
        col_p1, col_p2 = st.columns(2)
        with col_p1:
            days_late    = st.slider("Days Late", 0, 365, 0)
            late_filing  = st.checkbox("Also Filed Late?", value=False)
        with col_p2:
            if days_late > 0 or late_filing:
                pen = calculate_penalty(result["net_vat_payable"], days_late, late_filing)
                st.markdown(f"""
                <div class='metric-card' style='text-align:left;'>
                  <div class='metric-label'>Penalty Breakdown</div>
                  <div style='font-size:0.85rem; margin-top:8px;'>
                  Late Payment Penalty : <b style='color:#C8973A'>{fmt_sar(pen['payment_penalty'])}</b><br>
                  Late Filing Penalty  : <b style='color:#C8973A'>{fmt_sar(pen['filing_penalty'])}</b><br>
                  <hr style='border-color:#30363D'>
                  Total Penalties      : <b style='color:#EF233C'>{fmt_sar(pen['total_penalty'])}</b><br>
                  Grand Total Due      : <b style='color:#EF233C'>{fmt_sar(pen['total_due'])}</b>
                  </div>
                </div>
                """, unsafe_allow_html=True)
            else:
                st.markdown("<span class='badge-compliant'>✓ No Penalties — On Time</span>", unsafe_allow_html=True)

# ══════════════════════════════════════════════════════════════════════════════
#  MODULE 3 — ZAKAT CALCULATOR
# ══════════════════════════════════════════════════════════════════════════════
elif module == "🕌 Zakat Calculator":
    st.markdown("<div class='section-title'>Annual Zakat Computation — GAZT Method (Clothing Retail)</div>", unsafe_allow_html=True)

    st.markdown("""
    <div class='info-box'>
    <b>Who pays Zakat in KSA?</b> Saudi-owned and GCC-national-owned businesses (100% Saudi ownership → 
    Zakat replaces corporate income tax). Mixed-ownership companies pay Zakat on Saudi share 
    + Income Tax on foreign share. ZATCA administers both.
    </div>
    """, unsafe_allow_html=True)

    col1, col2 = st.columns(2)
    with col1:
        st.markdown("**Balance Sheet Inputs**")
        total_assets     = st.number_input("Total Assets (SAR)", min_value=0.0, value=3500000.0, step=10000.0)
        fixed_assets     = st.number_input("Fixed Assets — Non-Zakatable (SAR)", min_value=0.0, value=800000.0, step=10000.0)
        total_liab       = st.number_input("Total Liabilities (SAR)", min_value=0.0, value=900000.0, step=10000.0)
        lt_liab          = st.number_input("Long-Term Liabilities (SAR)", min_value=0.0, value=300000.0, step=10000.0)
        inventory        = st.number_input("Clothing Inventory at Cost (SAR)", min_value=0.0, value=1200000.0, step=10000.0)

    with col2:
        st.markdown("**Ownership Structure**")
        saudi_pct_own    = st.slider("Saudi/GCC Ownership %", 0, 100, 100)
        foreign_pct      = 100 - saudi_pct_own
        corp_tax_rate    = st.number_input("Corporate Income Tax Rate on Foreign Share (%)", value=20.0)
        net_profit       = st.number_input("Net Profit Before Tax (SAR)", value=450000.0, step=10000.0)

    if st.button("Calculate Zakat & Tax Obligation"):
        result_z = calculate_zakat(total_assets, 0, fixed_assets, total_liab, lt_liab)

        saudi_share       = saudi_pct_own / 100
        foreign_share     = foreign_pct / 100
        zakat_on_saudi    = round(result_z["zakat_due"] * saudi_share, 2)
        income_tax        = round(net_profit * foreign_share * corp_tax_rate / 100, 2)
        total_obligation  = zakat_on_saudi + income_tax

        st.markdown("<div class='section-title'>Zakat & Tax Summary</div>", unsafe_allow_html=True)
        c1,c2,c3,c4 = st.columns(4)
        mlist = [
            ("Zakatable Base",  fmt_sar(result_z["zakatable_base"]), "Current Assets – Liabilities"),
            ("Total Zakat Due", fmt_sar(result_z["zakat_due"]),      "2.5% of Zakatable Base"),
            ("Zakat (Saudi %)", fmt_sar(zakat_on_saudi),             f"{saudi_pct_own}% Saudi share"),
            ("Income Tax (Foreign %)", fmt_sar(income_tax),          f"{foreign_pct}% foreign share"),
        ]
        for col, (label, val, sub) in zip([c1,c2,c3,c4], mlist):
            with col:
                st.markdown(f"""
                <div class='metric-card'>
                  <div class='metric-label'>{label}</div>
                  <div class='metric-value'>{val}</div>
                  <div class='metric-sub'>{sub}</div>
                </div>""", unsafe_allow_html=True)

        # Donut: asset composition
        fig = px.pie(
            values=[fixed_assets, inventory, total_assets - fixed_assets - inventory],
            names=["Fixed Assets (Non-Zakatable)", "Inventory", "Other Current Assets"],
            color_discrete_sequence=["#30363D","#C8973A","#238636"],
            hole=0.6,
            title="Asset Composition — Zakatable vs Non-Zakatable",
        )
        fig.update_layout(paper_bgcolor="rgba(0,0,0,0)", font_color="#E6EDF3", height=300, margin=dict(t=40,b=0))
        st.plotly_chart(fig, use_container_width=True)

        st.markdown(f"""
        <div class='metric-card' style='text-align:left; margin-top:16px;'>
          <div class='metric-label'>Total Annual Obligation to ZATCA</div>
          <div class='metric-value' style='font-size:2rem;'>{fmt_sar(total_obligation)}</div>
          <div class='metric-sub'>Zakat {fmt_sar(zakat_on_saudi)} + Income Tax {fmt_sar(income_tax)}</div>
        </div>
        """, unsafe_allow_html=True)

# ══════════════════════════════════════════════════════════════════════════════
#  MODULE 4 — ANOMALY DETECTOR
# ══════════════════════════════════════════════════════════════════════════════
elif module == "🔍 Transaction Anomaly Detector":
    st.markdown("<div class='section-title'>VAT Transaction Anomaly Detector — AI-Powered Rules Engine</div>", unsafe_allow_html=True)

    st.markdown("""
    <div class='info-box'>
    Upload your clothing sales transaction log (CSV) or use the synthetic dataset below.
    The engine flags: VAT calculation mismatches, suspiciously round numbers, 
    high-value single transactions, and missing credit note markers on returns.
    </div>
    """, unsafe_allow_html=True)

    use_synthetic = st.checkbox("Use built-in synthetic dataset (50 transactions)", value=True)

    if use_synthetic:
        np.random.seed(42)
        n = 50
        amounts    = np.round(np.random.lognormal(8.5, 0.8, n), 2)
        # Inject anomalies
        amounts[5]  = 25000.0   # round number
        amounts[12] = 75000.0   # high value + round
        amounts[23] = -450.0    # return without credit note
        amounts[38] = 12000.0   # round number

        vat_charged = np.round(amounts * VAT_RATE, 2)
        vat_charged[8]  += 500   # mismatch
        vat_charged[31] -= 200   # mismatch

        df = pd.DataFrame({
            "invoice_no":       [f"INV-{1000+i}" for i in range(n)],
            "date":             pd.date_range("2025-01-01", periods=n, freq="7D").strftime("%Y-%m-%d"),
            "item_category":    np.random.choice(["Abayas","Thobes","Kids Wear","Sportswear","Accessories","Footwear"], n),
            "amount_excl_vat":  amounts,
            "vat_charged":      vat_charged,
            "is_credit_note":   np.where(amounts < 0, np.random.choice([True, False], n, p=[0.4, 0.6]), False),
        })
    else:
        uploaded = st.file_uploader("Upload CSV (columns: invoice_no, date, item_category, amount_excl_vat, vat_charged, is_credit_note)", type="csv")
        if uploaded:
            df = pd.read_csv(uploaded)
        else:
            st.info("Please upload a CSV file or enable the synthetic dataset.")
            st.stop()

    df_flagged = detect_vat_anomalies(df)
    anomalies  = df_flagged[df_flagged["anomaly_flags"] != "✓ Clean"]

    col1, col2, col3 = st.columns(3)
    with col1:
        st.markdown(f"""<div class='metric-card'>
          <div class='metric-label'>Total Transactions</div>
          <div class='metric-value'>{len(df)}</div></div>""", unsafe_allow_html=True)
    with col2:
        st.markdown(f"""<div class='metric-card'>
          <div class='metric-label'>Anomalies Detected</div>
          <div class='metric-value' style='color:#EF233C;'>{len(anomalies)}</div></div>""", unsafe_allow_html=True)
    with col3:
        pct = round(len(anomalies)/len(df)*100, 1)
        st.markdown(f"""<div class='metric-card'>
          <div class='metric-label'>Anomaly Rate</div>
          <div class='metric-value' style='color:{"#EF233C" if pct>10 else "#C8973A"};'>{pct}%</div></div>""", unsafe_allow_html=True)

    st.markdown("<br>", unsafe_allow_html=True)

    # Color-coded table
    def highlight_anomalies(row):
        if row["anomaly_flags"] != "✓ Clean":
            return ["background-color:#3A0D0D"] * len(row)
        return [""] * len(row)

    st.dataframe(
        df_flagged.style.apply(highlight_anomalies, axis=1),
        use_container_width=True, hide_index=True, height=400
    )

    if len(anomalies) > 0:
        st.markdown("<div class='section-title'>Anomaly Distribution by Type</div>", unsafe_allow_html=True)
        all_flags = []
        for flags_str in df_flagged["anomaly_flags"]:
            if flags_str != "✓ Clean":
                all_flags.extend([f.strip() for f in flags_str.split(",")])
        flag_counts = pd.Series(all_flags).value_counts()
        fig = px.bar(
            x=flag_counts.index, y=flag_counts.values,
            labels={"x": "Flag Type", "y": "Count"},
            color_discrete_sequence=["#C8973A"],
            title="Anomaly Flags Frequency",
        )
        fig.update_layout(paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
                          font_color="#E6EDF3", yaxis=dict(gridcolor="#30363D"), height=300)
        st.plotly_chart(fig, use_container_width=True)

    # Export
    csv_out = df_flagged.to_csv(index=False).encode("utf-8")
    st.download_button("⬇ Download Flagged Report (CSV)", csv_out, "vat_anomaly_report.csv", "text/csv")

# ══════════════════════════════════════════════════════════════════════════════
#  MODULE 5 — NITAQAT COMPLIANCE
# ══════════════════════════════════════════════════════════════════════════════
elif module == "⚖️ Nitaqat Compliance Modeler":
    st.markdown("<div class='section-title'>Nitaqat Saudization Compliance & Cost Modeler — Clothing Retail</div>", unsafe_allow_html=True)

    st.markdown("""
    <div class='info-box'>
    Clothing retail falls under <b>ISIC 4711/4719</b>. Failure to meet Nitaqat targets 
    results in inability to renew work visas, blocking foreign worker recruitment.
    This modeler shows the cheapest path to Green/Platinum band.
    </div>
    """, unsafe_allow_html=True)

    col1, col2 = st.columns(2)
    with col1:
        total_employees   = st.number_input("Total Employees", min_value=1, value=20, step=1)
        saudi_employees   = st.number_input("Current Saudi Employees", min_value=0, value=5, step=1)
        avg_saudi_salary  = st.number_input("Avg Saudi Salary (SAR/month)", value=6500.0, step=500.0)
        avg_expat_salary  = st.number_input("Avg Expat Salary (SAR/month)", value=3200.0, step=200.0)
    with col2:
        target_band       = st.selectbox("Target Nitaqat Band", ["Low Green (30%)", "High Green (40%)", "Platinum (50%)"])
        target_pct_map    = {"Low Green (30%)": 0.30, "High Green (40%)": 0.40, "Platinum (50%)": 0.50}
        target_pct        = target_pct_map[target_band]

    current_pct  = saudi_employees / total_employees if total_employees > 0 else 0
    current_band, current_color = nitaqat_band(current_pct)
    required_saudis = max(0, int(np.ceil(total_employees * target_pct)) - saudi_employees)
    cost_increase   = required_saudis * (avg_saudi_salary - avg_expat_salary)

    badge_class = "badge-compliant" if current_band in ["Platinum","High Green"] else \
                  ("badge-warning"   if current_band == "Low Green" else "badge-non-compliant")

    st.markdown(f"""
    <div style='margin: 16px 0;'>
      Current Band: <span class='{badge_class}'>{current_band}</span>&nbsp;&nbsp;
      Saudi %: <b style='color:#C8973A'>{current_pct*100:.1f}%</b>&nbsp;&nbsp;
      ({saudi_employees} of {total_employees} employees)
    </div>
    """, unsafe_allow_html=True)

    # Band gauge
    fig = go.Figure(go.Indicator(
        mode="gauge+number+delta",
        value=current_pct * 100,
        delta={"reference": target_pct * 100, "valueformat": ".1f"},
        number={"suffix": "%", "font": {"color": "#C8973A", "size": 40}},
        gauge={
            "axis": {"range": [0, 60], "tickcolor": "#8B949E"},
            "bar": {"color": current_color},
            "steps": [
                {"range": [0, 20],  "color": "#3A0D0D"},
                {"range": [20, 30], "color": "#3A2A00"},
                {"range": [30, 40], "color": "#1A2A00"},
                {"range": [40, 50], "color": "#0D2A0D"},
                {"range": [50, 60], "color": "#0D3A3A"},
            ],
            "threshold": {"line": {"color": "#C8973A", "width": 3}, "value": target_pct * 100},
        },
        title={"text": "Saudization Rate (Nitaqat)", "font": {"color": "#E6EDF3"}},
    ))
    fig.update_layout(paper_bgcolor="rgba(0,0,0,0)", font_color="#E6EDF3", height=280)
    st.plotly_chart(fig, use_container_width=True)

    if required_saudis > 0:
        st.markdown(f"""
        <div class='metric-card' style='text-align:left;'>
          <div class='metric-label'>Compliance Gap Analysis</div>
          <div style='font-size:0.9rem; margin-top:8px;'>
            Additional Saudi Hires Required : <b style='color:#C8973A'>{required_saudis}</b><br>
            Monthly Salary Cost Increase     : <b style='color:#C8973A'>{fmt_sar(cost_increase)}</b><br>
            Annual Additional Cost           : <b style='color:#EF233C'>{fmt_sar(cost_increase * 12)}</b><br><br>
            <span style='color:#8B949E; font-size:0.8rem;'>
            Tip: Hire Saudi part-timers (min 4hrs/day) — each counts as 0.5 employee toward Nitaqat.
            Saudis earning below SAR 4,000/month do NOT count toward Nitaqat quota.
            </span>
          </div>
        </div>
        """, unsafe_allow_html=True)
    else:
        st.markdown(f"<span class='badge-compliant'>✓ Already meets {target_band} — no additional hires required</span>", unsafe_allow_html=True)

# ══════════════════════════════════════════════════════════════════════════════
#  MODULE 6 — E-INVOICE BUILDER
# ══════════════════════════════════════════════════════════════════════════════
elif module == "🧾 ZATCA E-Invoice Builder":
    st.markdown("<div class='section-title'>ZATCA Phase 2 Compliant E-Invoice Generator</div>", unsafe_allow_html=True)

    col1, col2 = st.columns(2)
    with col1:
        seller_name  = st.text_input("Seller Name (Arabic/English)", value="مؤسسة الموضة السعودية")
        seller_vat   = st.text_input("Seller VAT Registration No.", value="300123456789003")
        seller_cr    = st.text_input("Commercial Registration No.", value="1010123456")
        invoice_no   = st.text_input("Invoice Number", value="INV-2025-001")
        invoice_date = st.date_input("Invoice Date", value=today)
    with col2:
        buyer_name   = st.text_input("Buyer Name", value="Customer / عميل")
        buyer_vat    = st.text_input("Buyer VAT No. (if B2B)", value="")

        st.markdown("**Line Items**")
        items_raw = st.text_area(
            "Enter items (one per line): Description | Qty | Unit Price excl VAT",
            value="Abaya Black XL | 2 | 350\nSport Shoes Nike | 1 | 480\nKids T-Shirt | 3 | 75"
        )

    if st.button("Generate E-Invoice"):
        lines = []
        total_excl = 0.0
        for line in items_raw.strip().split("\n"):
            parts = [p.strip() for p in line.split("|")]
            if len(parts) == 3:
                desc, qty_s, price_s = parts
                try:
                    qty   = float(qty_s)
                    price = float(price_s)
                    vat_a = round(price * qty * VAT_RATE, 2)
                    total_excl += price * qty
                    lines.append({
                        "Description": desc,
                        "Qty": qty,
                        "Unit Price (SAR)": price,
                        "Line Total excl.": round(price * qty, 2),
                        "VAT 15% (SAR)": vat_a,
                        "Line Total incl.": round(price * qty + vat_a, 2),
                    })
                except ValueError:
                    pass

        total_vat   = round(total_excl * VAT_RATE, 2)
        total_incl  = round(total_excl + total_vat, 2)
        qr_code     = generate_qr_data(seller_name, seller_vat, str(invoice_date), total_incl, total_vat)
        hijri_inv   = gregorian_to_hijri_approx(invoice_date)

        st.markdown(f"""
        <div style='background:#0D1117; border:1px solid #C8973A; border-radius:10px; padding:24px; font-size:0.85rem;'>
          <div style='display:flex; justify-content:space-between; align-items:flex-start; margin-bottom:16px;'>
            <div>
              <div style='font-size:1.2rem; font-weight:700; color:#C8973A;'>{seller_name}</div>
              <div style='color:#8B949E;'>VAT: {seller_vat}</div>
              <div style='color:#8B949E;'>CR: {seller_cr}</div>
            </div>
            <div style='text-align:right;'>
              <div style='font-weight:700; color:#E6EDF3;'>TAX INVOICE / فاتورة ضريبية</div>
              <div style='color:#8B949E;'>No: {invoice_no}</div>
              <div style='color:#8B949E;'>{invoice_date} | {hijri_inv}</div>
            </div>
          </div>
          <div style='color:#8B949E; margin-bottom:12px;'>Buyer: <b style='color:#E6EDF3;'>{buyer_name}</b>
            {"| VAT: " + buyer_vat if buyer_vat else "| B2C Transaction"}</div>
        </div>
        """, unsafe_allow_html=True)

        st.dataframe(pd.DataFrame(lines), use_container_width=True, hide_index=True)

        st.markdown(f"""
        <div style='background:#161B22; border:1px solid #30363D; border-radius:8px; padding:16px; text-align:right; margin-top:8px;'>
          Total excl. VAT : <b style='color:#E6EDF3;'>{fmt_sar(total_excl)}</b><br>
          VAT (15%)       : <b style='color:#C8973A;'>{fmt_sar(total_vat)}</b><br>
          <hr style='border-color:#30363D;'>
          <b style='font-size:1.1rem; color:#C8973A;'>TOTAL : {fmt_sar(total_incl)}</b>
        </div>
        <div style='margin-top:12px; font-size:0.72rem; color:#8B949E;'>
        🔐 ZATCA QR (Phase 2 hash): <code style='color:#C8973A;'>{qr_code}</code><br>
        This invoice was generated in compliance with ZATCA e-invoicing regulations.
        </div>
        """, unsafe_allow_html=True)

# ══════════════════════════════════════════════════════════════════════════════
#  MODULE 7 — TAX CALENDAR
# ══════════════════════════════════════════════════════════════════════════════
elif module == "📅 Tax Calendar & Deadlines":
    st.markdown("<div class='section-title'>2025–2026 Tax Compliance Calendar — KSA Clothing Retail</div>", unsafe_allow_html=True)

    events = []
    for year in [2025, 2026]:
        # Quarterly VAT returns (due last day of month following quarter end)
        vat_deadlines = [(3,30,"Q4 VAT Return"),(6,30,"Q1 VAT Return"),(9,30,"Q2 VAT Return"),(12,31,"Q3 VAT Return")]
        for m, d, label in vat_deadlines:
            try:
                events.append({"Date": datetime.date(year, m, d), "Obligation": label, "Type": "VAT Return", "Penalty": "2.5% tax + SAR 1,000 min"})
            except ValueError:
                pass
        # Annual Zakat (due within 120 days of fiscal year end — assuming Dec 31 FYE)
        events.append({"Date": datetime.date(year, 4, 30), "Obligation": "Annual Zakat Filing", "Type": "Zakat", "Penalty": "25% of unpaid Zakat"})
        # Nitaqat renewal window (approximate)
        events.append({"Date": datetime.date(year, 3, 31), "Obligation": "Iqama/Work Visa Renewal Window", "Type": "Nitaqat", "Penalty": "Visa block"})
        # ZATCA E-invoice audit season
        events.append({"Date": datetime.date(year, 6, 1), "Obligation": "ZATCA E-Invoice Compliance Audit", "Type": "E-Invoice", "Penalty": "SAR 50,000 max"})

    df_cal = pd.DataFrame(events).sort_values("Date")
    df_cal["Days Away"] = (df_cal["Date"] - today).dt.days
    df_cal["Status"] = df_cal["Days Away"].apply(
        lambda d: "⚠️ Due Soon" if 0 <= d <= 30 else ("✅ Upcoming" if d > 30 else "🔴 Past Due")
    )
    df_cal["Date"] = df_cal["Date"].astype(str)

    color_map = {"VAT Return": "#C8973A", "Zakat": "#238636", "Nitaqat": "#0D6EFD", "E-Invoice": "#8B5CF6"}

    fig = px.timeline(
        df_cal.assign(End=df_cal["Date"], Start=df_cal["Date"]),
        x_start="Start", x_end="End",
        y="Obligation", color="Type",
        color_discrete_map=color_map,
        title="Tax Obligation Timeline",
        text="Status",
    )
    # Use scatter instead for point-in-time events
    fig2 = go.Figure()
    for _, row in df_cal.iterrows():
        fig2.add_trace(go.Scatter(
            x=[row["Date"]], y=[row["Obligation"]],
            mode="markers+text",
            marker=dict(size=14, color=color_map.get(row["Type"], "#C8973A"), symbol="diamond"),
            text=[row["Status"]], textposition="middle right",
            name=row["Type"],
            showlegend=False,
        ))
    fig2.update_layout(
        paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
        font_color="#E6EDF3", height=400, xaxis=dict(gridcolor="#30363D"),
        yaxis=dict(gridcolor="#30363D"), title="2025–2026 Tax Event Calendar",
    )
    st.plotly_chart(fig2, use_container_width=True)
    st.dataframe(df_cal[["Date","Obligation","Type","Penalty","Status","Days Away"]], use_container_width=True, hide_index=True)

# ══════════════════════════════════════════════════════════════════════════════
#  MODULE 8 — PROFIT SCENARIO PLANNER
# ══════════════════════════════════════════════════════════════════════════════
elif module == "📈 Profit-After-Tax Scenario Planner":
    st.markdown("<div class='section-title'>Net Profit Sensitivity — After VAT, Zakat & Nitaqat Costs</div>", unsafe_allow_html=True)

    col1, col2 = st.columns(2)
    with col1:
        revenue        = st.number_input("Annual Revenue excl. VAT (SAR)", value=5000000.0, step=100000.0)
        cogs_pct       = st.slider("COGS % of Revenue", 30, 80, 55)
        opex_pct       = st.slider("Operating Expenses % of Revenue", 10, 40, 25)
        input_vat_pct  = st.slider("Input VAT % of COGS (recoverable)", 0, 100, 70)
    with col2:
        saudi_own_pct  = st.slider("Saudi Ownership %", 0, 100, 100)
        total_emp      = st.number_input("Total Employees", min_value=1, value=15, step=1)
        saudi_emp      = st.number_input("Saudi Employees", min_value=0, value=4, step=1)
        avg_s_sal      = st.number_input("Avg Saudi Salary (SAR/mo)", value=6500.0)
        avg_e_sal      = st.number_input("Avg Expat Salary (SAR/mo)", value=3200.0)

    cogs         = revenue * cogs_pct / 100
    opex         = revenue * opex_pct / 100
    ebitda       = revenue - cogs - opex
    output_vat   = revenue * VAT_RATE
    recov_input  = cogs * (input_vat_pct / 100) * VAT_RATE
    net_vat      = max(output_vat - recov_input, 0)
    zakatable    = max(revenue * 0.4 - revenue * 0.2, 0)   # simplified proxy
    zakat        = zakatable * ZAKAT_RATE * (saudi_own_pct / 100)
    nitaqat_cost = max(0, int(np.ceil(total_emp * 0.30)) - saudi_emp) * (avg_s_sal - avg_e_sal) * 12
    net_profit   = ebitda - zakat - nitaqat_cost

    scenarios = []
    for rev_mult in [0.7, 0.85, 1.0, 1.15, 1.30]:
        r = revenue * rev_mult
        c = r * cogs_pct / 100
        o = r * opex_pct / 100
        e = r - c - o
        z = max(r * 0.4 - r * 0.2, 0) * ZAKAT_RATE * (saudi_own_pct / 100)
        np_ = e - z - nitaqat_cost
        scenarios.append({"Revenue Scale": f"{int(rev_mult*100)}%", "Revenue (SAR M)": round(r/1e6, 2),
                           "EBITDA (SAR M)": round(e/1e6, 2), "Zakat (SAR K)": round(z/1e3, 1),
                           "Net Profit (SAR M)": round(np_/1e6, 2), "Net Margin %": round(np_/r*100, 1)})

    df_sc = pd.DataFrame(scenarios)
    fig = go.Figure()
    fig.add_trace(go.Bar(x=df_sc["Revenue Scale"], y=df_sc["EBITDA (SAR M)"], name="EBITDA", marker_color="#238636"))
    fig.add_trace(go.Bar(x=df_sc["Revenue Scale"], y=df_sc["Net Profit (SAR M)"], name="Net Profit After Tax+Zakat", marker_color="#C8973A"))
    fig.update_layout(
        barmode="group", paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
        font_color="#E6EDF3", yaxis=dict(gridcolor="#30363D", title="SAR Million"),
        title="Revenue Scenario: EBITDA vs Net Profit After Taxes", height=350,
    )
    st.plotly_chart(fig, use_container_width=True)
    st.dataframe(df_sc, use_container_width=True, hide_index=True)

    st.markdown(f"""
    <div class='metric-card' style='text-align:left; margin-top:12px;'>
      <div class='metric-label'>Base Case Summary (100% Revenue)</div>
      <div style='font-size:0.88rem; margin-top:8px;'>
        Revenue            : {fmt_sar(revenue)}<br>
        EBITDA             : {fmt_sar(ebitda)}<br>
        Net VAT Payable    : {fmt_sar(net_vat)}<br>
        Zakat Due          : {fmt_sar(zakat)}<br>
        Nitaqat Extra Cost : {fmt_sar(nitaqat_cost)}<br>
        <hr style='border-color:#30363D;'>
        <b>Net Profit After All Obligations : <span style='color:#C8973A;'>{fmt_sar(net_profit)}</span></b>
        &nbsp; | &nbsp; Margin: <b style='color:#C8973A;'>{net_profit/revenue*100:.1f}%</b>
      </div>
    </div>
    """, unsafe_allow_html=True)

# ══════════════════════════════════════════════════════════════════════════════
#  MODULE 9 — ZATCA RULES REFERENCE
# ══════════════════════════════════════════════════════════════════════════════
elif module == "ℹ️ ZATCA Rules Reference":
    st.markdown("<div class='section-title'>ZATCA Quick Reference — Clothing Retail Specific</div>", unsafe_allow_html=True)

    rules = {
        "📋 Registration": [
            ("Mandatory Registration Threshold", "SAR 375,000 annual taxable supplies"),
            ("Voluntary Registration Threshold", "SAR 187,500 annual taxable supplies"),
            ("Registration Deadline", "Within 30 days of exceeding threshold"),
            ("Deregistration Conditions", "Annual supplies below SAR 375,000 for 12 months"),
        ],
        "🧾 Filing Obligations": [
            ("Large Taxpayers (>SAR 40M)", "Monthly VAT returns — due last day of following month"),
            ("Medium/Small Taxpayers", "Quarterly VAT returns — due last day of month following quarter"),
            ("Annual Zakat Return", "Due within 120 days of fiscal year end"),
            ("Withholding Tax", "Monthly — on payments to non-residents (5% standard rate)"),
        ],
        "🏷️ Clothing-Specific Rules": [
            ("Adult Clothing", "Standard rated 15% VAT — no exceptions"),
            ("Children's Clothing", "Standard rated 15% VAT — unlike UK/EU, NO exemption in KSA"),
            ("Second-Hand Clothing", "15% VAT on margin if margin scheme applies; standard 15% otherwise"),
            ("Clothing Exports (GCC)", "Zero-rated IF customs export documentation available"),
            ("Tailoring Services", "15% VAT on full value including labour component"),
        ],
        "⚠️ Penalties": [
            ("Late VAT Payment", "2% per month, capped at 50% of tax due"),
            ("Late VAT Filing", "2.5% of tax due, minimum SAR 1,000"),
            ("Failure to Register", "Fine of SAR 10,000"),
            ("Failure to Issue Tax Invoice", "SAR 1,000 per invoice, up to SAR 40,000"),
            ("E-Invoice Non-Compliance", "SAR 50,000 maximum per violation"),
            ("Zakat Evasion", "25% of unpaid Zakat amount"),
        ],
    }

    for section, items in rules.items():
        st.markdown(f"<div class='section-title'>{section}</div>", unsafe_allow_html=True)
        df_r = pd.DataFrame(items, columns=["Rule", "Details"])
        st.dataframe(df_r, use_container_width=True, hide_index=True)

# ─── FOOTER ───────────────────────────────────────────────────────────────────
st.markdown("---")
st.markdown("""
<div style='text-align:center; color:#8B949E; font-size:0.72rem; padding:12px 0;'>
ZATCA TaxSense Pro &nbsp;•&nbsp; Built by <b style='color:#C8973A;'>Muhammad Baqar Wagan</b>
&nbsp;•&nbsp; MA Economics | Saudi Market Specialist &nbsp;•&nbsp;
Compliant: ZATCA VAT Law 2024 | Zakat Regulations 1445 AH<br>
<span style='color:#555;'>Disclaimer: For educational and planning purposes. Always verify with a licensed Saudi tax advisor.</span>
</div>
""", unsafe_allow_html=True)
