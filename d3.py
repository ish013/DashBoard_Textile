import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import requests
from datetime import datetime

# ─────────────────────────────────────────────
# CONFIG
# ─────────────────────────────────────────────
AUTO_REFRESH_SEC = 60

st.set_page_config(
    page_title="Dyeing Operations Dashboard",
    page_icon="🎨",
    layout="wide",
    initial_sidebar_state="collapsed"          # ← sidebar collapsed by default now
)

# ─────────────────────────────────────────────
# CSS  (colors unchanged — only layout polish)
# ─────────────────────────────────────────────
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700;800&family=JetBrains+Mono:wght@400;500&display=swap');

html, body, [class*="css"] { font-family: 'Inter', sans-serif; }
.stApp { background-color: #f5f6fa; }

/* ── Sidebar (kept for collapse toggle only) ── */
[data-testid="stSidebar"] { background: #ffffff !important; border-right: 1px solid #e2e6ed !important; box-shadow: 2px 0 12px rgba(0,0,0,0.04); }
[data-testid="stSidebar"] * { color: #374151 !important; }
[data-testid="stSidebar"] h3 { color: #111827 !important; font-weight: 700 !important; }

/* ── Metric cards ── */
[data-testid="metric-container"] {
  background: #ffffff;
  border: 1px solid #e8ecf2;
  border-radius: 16px;
  padding: 20px 24px !important;
  box-shadow: 0 1px 4px rgba(0,0,0,0.05);
  transition: box-shadow .2s, border-color .2s;
}
[data-testid="metric-container"]:hover { box-shadow: 0 4px 16px rgba(0,0,0,0.10); border-color: #d97706; }
[data-testid="stMetricValue"] { font-family: 'JetBrains Mono', monospace !important; font-size: 1.75rem !important; font-weight: 700 !important; color: #111827 !important; }
[data-testid="stMetricLabel"] { font-size: 0.72rem !important; color: #6b7280 !important; text-transform: uppercase; letter-spacing: .07em; font-weight: 600 !important; }

/* ── Ratio metric widget ── */
.ratio-metric-card {
  background: linear-gradient(135deg, #fffbeb, #fef3c7);
  border: 1.5px solid #fde68a;
  border-radius: 16px;
  padding: 20px 24px;
  box-shadow: 0 1px 4px rgba(217,119,6,0.10);
  transition: box-shadow .2s, border-color .2s;
  height: 100%;
}
.ratio-metric-card:hover { box-shadow: 0 4px 16px rgba(217,119,6,0.18); border-color: #d97706; }
.ratio-metric-label { font-size: 0.72rem; color: #92400e; text-transform: uppercase; letter-spacing: .07em; font-weight: 600; margin-bottom: 6px; }
.ratio-metric-value { font-family: 'JetBrains Mono', monospace; font-size: 1.75rem; font-weight: 700; color: #92400e; line-height: 1.1; }
.ratio-metric-sub { font-size: 0.72rem; color: #b45309; margin-top: 5px; font-weight: 500; }

/* ── Filter bar ── */
.filter-bar-wrap {
  background: #ffffff;
  border: 1px solid #e8ecf2;
  border-radius: 16px;
  padding: 16px 20px 10px;
  margin-bottom: 20px;
  box-shadow: 0 1px 4px rgba(0,0,0,0.04);
}
.filter-bar-title {
  font-size: 0.75rem;
  font-weight: 700;
  color: #6b7280;
  text-transform: uppercase;
  letter-spacing: .08em;
  margin-bottom: 10px;
}

/* ── Charts ── */
[data-testid="stPlotlyChart"] > div { border-radius: 16px !important; overflow: hidden; box-shadow: 0 1px 4px rgba(0,0,0,0.06); }
.stMultiSelect [data-baseweb="tag"] { background: #fef3c7 !important; color: #92400e !important; border-radius: 6px !important; }
[data-testid="stExpander"] { background: #ffffff !important; border: 1px solid #e8ecf2 !important; border-radius: 14px !important; box-shadow: 0 1px 4px rgba(0,0,0,0.04); }

/* ── Live badge ── */
.live-badge { display:inline-flex;align-items:center;gap:6px;background:#f0fdf4;border:1px solid #bbf7d0;border-radius:20px;padding:5px 12px;font-size:12px;color:#15803d;font-weight:500; }
.live-dot { width:7px;height:7px;border-radius:50%;background:#22c55e;animation:pulse 2s infinite; }
@keyframes pulse { 0%,100%{opacity:1}50%{opacity:.3} }

/* ── Summary tables ── */
.sum-table { width:100%;border-collapse:collapse;font-family:'Inter',sans-serif;font-size:13px;background:#ffffff;border-radius:12px;overflow:hidden; }
.sum-table th { background:#f3f4f6;color:#6b7280;text-transform:uppercase;font-size:11px;letter-spacing:.06em;padding:11px 16px;border-bottom:1px solid #e5e7eb;text-align:left;font-weight:600; }
.sum-table td { padding:10px 16px;color:#1f2937;border-bottom:1px solid #f3f4f6;font-family:'JetBrains Mono',monospace;font-size:12px; }
.sum-table td:first-child { font-family:'Inter',sans-serif;color:#d97706;font-weight:600; }
.sum-table tr:hover td { background:#fafafa; }

/* ── Section headers ── */
.section-header {
  background: linear-gradient(135deg, #1e3a5f, #2d5f8a);
  color: #fff; border-radius: 14px; padding: 14px 22px;
  margin: 24px 0 16px; display: flex; align-items: center; gap: 12px;
  font-size: 1rem; font-weight: 700; letter-spacing: -.2px;
}

/* ── Insight cards ── */
.insight-card {
  background: #ffffff; border: 1px solid #e8ecf2; border-radius: 14px;
  padding: 14px 18px; margin-bottom: 10px;
  box-shadow: 0 1px 4px rgba(0,0,0,0.05);
  display: flex; align-items: flex-start; gap: 12px; font-size: 13px; color: #374151;
}
.insight-icon { font-size: 20px; flex-shrink: 0; margin-top: 1px; }
.insight-text strong { color: #111827; }
.insight-card.warn  { border-left: 4px solid #f59e0b; background: #fffbeb; }
.insight-card.risk  { border-left: 4px solid #ef4444; background: #fef2f2; }
.insight-card.good  { border-left: 4px solid #10b981; background: #f0fdf4; }
.insight-card.info  { border-left: 4px solid #3b82f6; background: #eff6ff; }

/* ── Leaderboard table ── */
.leaderboard-table { width:100%;border-collapse:collapse;font-family:'Inter',sans-serif;font-size:12px;background:#ffffff;border-radius:12px;overflow:hidden; }
.leaderboard-table th { background:#1e3a5f;color:#ffffff;padding:9px 14px;text-align:left;font-size:11px;letter-spacing:.05em;font-weight:600; }
.leaderboard-table td { padding:9px 14px;color:#1f2937;border-bottom:1px solid #f3f4f6;font-family:'JetBrains Mono',monospace;font-size:11px; }
.leaderboard-table td:first-child { font-family:'Inter',sans-serif;font-weight:700;color:#d97706;text-align:center; }
.leaderboard-table td:nth-child(2) { font-family:'Inter',sans-serif;color:#111827;font-weight:600; }
.leaderboard-table tr:hover td { background:#fef3c7; }

/* ── Lot pills ── */
.lot-pill-small  { background:#fee2e2;color:#991b1b;border-radius:6px;padding:2px 8px;font-size:11px;font-weight:600; }
.lot-pill-medium { background:#fef3c7;color:#92400e;border-radius:6px;padding:2px 8px;font-size:11px;font-weight:600; }
.lot-pill-large  { background:#d1fae5;color:#065f46;border-radius:6px;padding:2px 8px;font-size:11px;font-weight:600; }

/* ── MoM cards ── */
.mom-card { background:#ffffff;border:1px solid #e8ecf2;border-radius:14px;padding:18px 20px;text-align:center;box-shadow:0 1px 4px rgba(0,0,0,0.05); }
.mom-card .val { font-family:'JetBrains Mono',monospace;font-size:1.6rem;font-weight:700;color:#111827; }
.mom-card .lbl { font-size:11px;color:#6b7280;text-transform:uppercase;letter-spacing:.07em;margin-top:4px;font-weight:600; }
.mom-card .delta-pos { color:#10b981;font-size:13px;font-weight:600;margin-top:4px; }
.mom-card .delta-neg { color:#ef4444;font-size:13px;font-weight:600;margin-top:4px; }
.mom-card .delta-neu { color:#6b7280;font-size:13px;font-weight:600;margin-top:4px; }

/* ── Day header ── */
.day-header { background:linear-gradient(135deg,#1e3a5f,#2d5f8a);color:#fff;border-radius:14px;padding:16px 24px;margin-bottom:16px;display:flex;align-items:center;justify-content:space-between; }

/* ── Production sheet table ── */
.prod-sheet-table { width:100%;border-collapse:collapse;font-family:'Inter',sans-serif;font-size:12px; }
.prod-sheet-table th { background:#1e3a5f;color:#ffffff;padding:8px 10px;text-align:center;font-size:11px;letter-spacing:.04em;border:1px solid #2d4f7a; }
.prod-sheet-table td { padding:7px 10px;border:1px solid #e5e7eb;color:#1f2937;text-align:center;font-family:'JetBrains Mono',monospace;font-size:11px; }
.prod-sheet-table tr:nth-child(even) td { background:#f8faff; }
.prod-sheet-table tr:hover td { background:#fef3c7; }
.prod-sheet-total td { background:#1e3a5f !important;color:#ffffff !important;font-weight:700; }

/* ── View toggle buttons ── */
.stButton > button {
  border-radius: 10px !important;
  font-weight: 600 !important;
  font-size: 0.85rem !important;
  transition: all .15s !important;
}

/* ── Chart card wrapper ── */
.chart-card {
  background: #ffffff;
  border: 1px solid #e8ecf2;
  border-radius: 16px;
  padding: 4px;
  box-shadow: 0 1px 4px rgba(0,0,0,0.05);
  margin-bottom: 4px;
}

/* ── Section divider label ── */
.section-divider-label {
  display: flex; align-items: center; gap: 12px;
  margin: 28px 0 20px;
}
.section-divider-label span {
  font-size: 1.05rem; font-weight: 800; color: #111827; letter-spacing: -.3px;
  white-space: nowrap;
}
.section-divider-label hr {
  flex: 1; border: none; border-top: 2px solid #e8ecf2; margin: 0;
}

hr { border-color: #e8ecf2 !important; }
h2, h3 { color: #111827 !important; font-weight: 700 !important; }
</style>
""", unsafe_allow_html=True)

# ─────────────────────────────────────────────
# HELPERS
# ─────────────────────────────────────────────
def fmt_in(n):
    try:
        n = int(n)
        s = str(n)
        if len(s) <= 3:
            return s
        elif len(s) <= 5:
            return s[:-3] + "," + s[-3:]
        else:
            last3 = s[-3:]
            rest  = s[:-3]
            groups = []
            while len(rest) > 2:
                groups.append(rest[-2:])
                rest = rest[:-2]
            if rest:
                groups.append(rest)
            return ",".join(reversed(groups)) + "," + last3
    except:
        return str(n)

# ── Plotly config: PAN mode by default ──────
PLOTLY_CFG = dict(
    scrollZoom=True,
    displayModeBar=True,
    modeBarButtonsToRemove=["select2d", "lasso2d", "autoScale2d"],
    modeBarButtonsToAdd=["pan2d"],
    displaylogo=False,
    dragmode="pan",
)

PLOTLY_LAYOUT = dict(
    paper_bgcolor="rgba(255,255,255,1)", plot_bgcolor="rgba(248,249,252,1)",
    font=dict(family="Inter", color="#6b7280", size=12),
    margin=dict(l=10, r=10, t=44, b=10),
    legend=dict(bgcolor="rgba(255,255,255,0.9)", bordercolor="#e5e7eb", borderwidth=1, font=dict(color="#374151", size=11)),
    xaxis=dict(gridcolor="#f0f0f0", zerolinecolor="#e5e7eb", linecolor="#e5e7eb"),
    yaxis=dict(gridcolor="#f0f0f0", zerolinecolor="#e5e7eb", linecolor="#e5e7eb"),
    dragmode="pan",
)

PALETTE = ["#d97706","#3b82f6","#8b5cf6","#10b981","#ef4444","#f59e0b","#06b6d4","#ec4899","#84cc16","#f43f5e","#6366f1","#14b8a6","#fb923c","#a855f7","#64748b"]

def apply_layout(fig, title="", height=320, show_legend=True):
    fig.update_layout(
        **PLOTLY_LAYOUT,
        title=dict(
            text=title,
            font=dict(size=14, color="#111827"),
            x=0,
        ),
        height=height,
        showlegend=show_legend,
    )

    fig.update_xaxes(showgrid=True, gridwidth=1)
    fig.update_yaxes(showgrid=True, gridwidth=1)

    return fig

def pc(fig, **kwargs):
    """Wrapper for st.plotly_chart with pan config always applied."""
    st.plotly_chart(fig, use_container_width=True, config=PLOTLY_CFG, **kwargs)

def parse_dates(series):
    formats = ["%d-%b-%Y","%d %B %Y","%d-%m-%Y","%Y-%m-%d","%m/%d/%Y","%d/%m/%Y","%d %b %Y","%d/%b/%Y","%d-%b-%y"]
    for fmt in formats:
        parsed = pd.to_datetime(series, format=fmt, errors="coerce")
        if parsed.notna().sum() > len(series) * 0.5:
            mask = parsed.isna()
            if mask.any():
                parsed[mask] = pd.to_datetime(series[mask], infer_datetime_format=True, errors="coerce")
            return parsed
    return pd.to_datetime(series, infer_datetime_format=True, errors="coerce")

def section_header(icon, title, subtitle=""):
    sub_html = f"<div style='font-size:.78rem;opacity:.75;margin-top:3px;font-weight:400;'>{subtitle}</div>" if subtitle else ""
    st.markdown(f"""
    <div class="section-header">
      <div style="font-size:22px;">{icon}</div>
      <div><div>{title}</div>{sub_html}</div>
    </div>""", unsafe_allow_html=True)

def insight_card(text, kind="info", icon=None):
    icons = {"warn": "⚠️", "risk": "🔴", "good": "✅", "info": "💡"}
    ic = icon or icons.get(kind, "💡")
    st.markdown(f"""<div class="insight-card {kind}">
      <div class="insight-icon">{ic}</div>
      <div class="insight-text">{text}</div>
    </div>""", unsafe_allow_html=True)

def section_divider(label):
    st.markdown(f"""
    <div class="section-divider-label">
      <span>{label}</span><hr/>
    </div>""", unsafe_allow_html=True)

def ratio_widget(ratio_val):
    """Render Mtr ÷ KG as a premium metric widget (not a text pill)."""
    st.markdown(f"""
    <div class="ratio-metric-card">
      <div class="ratio-metric-label">📐 Mtr ÷ KG Ratio</div>
      <div class="ratio-metric-value">{ratio_val}x</div>
      <div class="ratio-metric-sub">Every 1 kg = {ratio_val} metres</div>
    </div>""", unsafe_allow_html=True)

# ─────────────────────────────────────────────
# ZOHO CREATOR — TOKEN & DATA
# ─────────────────────────────────────────────
def get_access_token():
    cfg = st.secrets["zoho_creator"]
    resp = requests.post(
        "https://accounts.zoho.com/oauth/v2/token",
        params={
            "refresh_token": cfg["refresh_token"],
            "client_id":     cfg["client_id"],
            "client_secret": cfg["client_secret"],
            "grant_type":    "refresh_token",
        },
        timeout=15,
    )
    resp.raise_for_status()
    data = resp.json()
    if "access_token" not in data:
        raise RuntimeError(f"Zoho token error: {data}")
    return data["access_token"]


@st.cache_data(ttl=AUTO_REFRESH_SEC)
def load_data():
    cfg          = st.secrets["zoho_creator"]
    owner        = cfg["account_owner"]
    app          = cfg["app_name"]
    report       = cfg["report_name"]
    access_token = get_access_token()

    base_url = f"https://creator.zoho.com/api/v2/{owner}/{app}/report/{report}"
    headers  = {"Authorization": f"Zoho-oauthtoken {access_token}"}

    all_records = []
    start_index = 0
    limit       = 200

    while True:
        resp = requests.get(
            base_url,
            headers=headers,
            params={"from": start_index, "limit": limit},
            timeout=20,
        )
        resp.raise_for_status()
        payload = resp.json()
        records = payload.get("data", [])
        if not records:
            break
        all_records.extend(records)
        if len(records) < limit:
            break
        start_index += limit

    if not all_records:
        return pd.DataFrame(), datetime.now(), 0

    df = pd.DataFrame(all_records)

    def extract_display(val):
        if isinstance(val, dict):
            return val.get("display_value") or val.get("display_Value") or str(val)
        return val

    for col in df.columns:
        if df[col].dtype == object:
            df[col] = df[col].apply(extract_display)

    col_map = {
        "Production_Date": "Production Date",
        "Party_Name": "Party Name", "Party Name": "Party Name",
        "QUALITY": "QUALITY", "Quality": "QUALITY",
        "SHADE": "SHADE", "Shade": "SHADE",
        "SIZE": "SIZE", "Size": "SIZE",
        "MTRS": "MTRS", "Mtrs": "MTRS",
        "Weight": "Weight", "WEIGHT": "Weight",
        "LOT_NO": "LOT NO.", "LOT_NO_": "LOT NO.", "Lot_No": "LOT NO.", "LOT NO.": "LOT NO.",
        "G_ACID": "G/ACID", "G_Acid": "G/ACID",
        "DFT": "DFT", "RC": "RC", "XNI": "XNI",
        "SOFTNER": "SOFTNER", "Softner": "SOFTNER",
        "MB": "MB", "MB_per": "MB %", "MB_Per": "MB %", "MB_percent": "MB %",
        "MASTER_NAME": "MASTER NAME", "Master_Name": "MASTER NAME", "MASTER NAME": "MASTER NAME",
        "M_No": "M.No.", "M_NO": "M.No.", "Machine_No": "M.No.",
    }
    df.rename(columns={k: v for k, v in col_map.items() if k in df.columns}, inplace=True)

    df["MTRS"]   = pd.to_numeric(df.get("MTRS",   pd.Series(dtype=float)), errors="coerce").fillna(0)
    df["Weight"] = pd.to_numeric(df.get("Weight", pd.Series(dtype=float)), errors="coerce").fillna(0)

    for chem in ["G/ACID", "DFT", "RC", "XNI", "SOFTNER", "MB", "MB %"]:
        if chem in df.columns:
            df[chem] = pd.to_numeric(df[chem], errors="coerce").fillna(0)

    if "Production Date" in df.columns:
        df["Production Date"] = parse_dates(df["Production Date"].astype(str))
    else:
        date_cols = [c for c in df.columns if "date" in c.lower() or "Date" in c]
        if date_cols:
            df.rename(columns={date_cols[0]: "Production Date"}, inplace=True)
            df["Production Date"] = parse_dates(df["Production Date"].astype(str))
        else:
            raise KeyError(f"'Production Date' column not found. Available: {list(df.columns)}")

    for col in ["Party Name", "QUALITY", "SHADE", "MASTER NAME"]:
        if col in df.columns:
            df[col] = df[col].fillna("Unknown").astype(str).str.strip()
            df[col] = df[col].replace({"": "Unknown", "None": "Unknown", "nan": "Unknown"})
        else:
            df[col] = "Unknown"

    if "M.No." in df.columns:
        df["M.No."] = df["M.No."].fillna("Unknown").astype(str).str.strip()
        df["M.No."] = df["M.No."].replace({"": "Unknown", "None": "Unknown", "nan": "Unknown"})

    failed = df["Production Date"].isna().sum()
    df = df.dropna(subset=["Production Date"])
    df = df[df["Party Name"].str.strip().ne("")]

    return df, datetime.now(), failed


# ─────────────────────────────────────────────
# HEADER
# ─────────────────────────────────────────────
hcol1, hcol2 = st.columns([6, 1])
with hcol1:
    st.markdown("""
    <div style="display:flex;align-items:center;gap:16px;padding:8px 0 20px;">
      <div style="width:48px;height:48px;border-radius:14px;background:linear-gradient(135deg,#1e3a5f,#2d5f8a);
        display:flex;align-items:center;justify-content:center;font-size:24px;box-shadow:0 4px 14px rgba(30,58,95,0.25);">🎨</div>
      <div>
        <div style="font-size:1.55rem;font-weight:800;color:#111827;letter-spacing:-.5px;">Dyeing Operations Dashboard</div>
        <div style="font-size:.82rem;color:#9ca3af;margin-top:2px;">Singhania Finishers · Live · Zoho Creator</div>
      </div>
    </div>
    """, unsafe_allow_html=True)
with hcol2:
    st.markdown("<div style='padding-top:18px;'></div>", unsafe_allow_html=True)
    if st.button("🔄 Refresh", use_container_width=True, type="primary"):
        st.cache_data.clear()
        st.rerun()

# ─────────────────────────────────────────────
# LOAD DATA
# ─────────────────────────────────────────────
try:
    raw, fetched_at, date_parse_fails = load_data()
    fetch_error = None
except Exception as e:
    fetch_error = str(e)
    raw = pd.DataFrame()
    fetched_at = None
    date_parse_fails = 0

if fetch_error:
    st.error(f"❌ Could not connect to Zoho Creator: `{fetch_error}`")
    st.info("""
**Setup checklist:**
1. Add credentials to `.streamlit/secrets.toml` under `[zoho_creator]`
2. Make sure the report is not restricted by IP in Zoho Creator
3. Verify field link names match what Zoho Creator returns
4. Redeploy / restart the app
    """)
    st.stop()

if raw.empty:
    st.warning("⚠️ No records found in Zoho Creator report.")
    st.stop()

# ─────────────────────────────────────────────
# ── TOP FILTER BAR  (replaces sidebar filters)
# ─────────────────────────────────────────────
valid_dates   = raw["Production Date"].dropna()
min_date      = valid_dates.min().date()
max_date      = valid_dates.max().date()
all_parties   = sorted(raw["Party Name"].dropna().unique())
all_quality   = sorted(raw["QUALITY"].dropna().unique())
all_shades    = sorted(raw["SHADE"].dropna().unique())
all_masters   = sorted(raw["MASTER NAME"].dropna().unique())

with st.expander("🔍  Filters — click to expand", expanded=False):
    st.markdown("<div class='filter-bar-title'>Filter the data below</div>", unsafe_allow_html=True)
    fc1, fc2, fc3, fc4, fc5 = st.columns([2, 2, 2, 2, 2])
    with fc1:
        st.markdown("**📅 Date Range**")
        date_range = st.date_input(
            "date_range", value=(min_date, max_date),
            min_value=min_date, max_value=max_date,
            label_visibility="collapsed"
        )
    with fc2:
        st.markdown("**🏭 Party**")
        sel_parties = st.multiselect("Party", all_parties, default=all_parties, label_visibility="collapsed")
    with fc3:
        st.markdown("**🧵 Quality**")
        sel_quality = st.multiselect("Quality", all_quality, default=all_quality, label_visibility="collapsed")
    with fc4:
        st.markdown("**🎨 Shade**")
        sel_shades = st.multiselect("Shade", all_shades, default=all_shades, label_visibility="collapsed")
    with fc5:
        st.markdown("**👤 Master**")
        sel_masters = st.multiselect("Master", all_masters, default=all_masters, label_visibility="collapsed")
    _, reset_col = st.columns([4, 1])
    with reset_col:
        if st.button("↩️ Reset All", use_container_width=True):
            st.rerun()

# status strip
scol1, scol2 = st.columns([6, 2])
with scol1:
    if date_parse_fails > 0:
        st.warning(f"⚠️ {date_parse_fails} rows had unreadable dates and were skipped.")
with scol2:
    st.markdown(f"""
    <div style="text-align:right;padding-top:4px;">
      <span class="live-badge"><span class="live-dot"></span> Live &nbsp;·&nbsp; {fetched_at.strftime('%H:%M:%S') if fetched_at else '—'} &nbsp;·&nbsp; {len(raw):,} records</span>
    </div>""", unsafe_allow_html=True)

# ─────────────────────────────────────────────
# APPLY FILTERS
# ─────────────────────────────────────────────
df = raw.copy()
if len(date_range) == 2:
    s, e = pd.Timestamp(date_range[0]), pd.Timestamp(date_range[1])
    df = df[(df["Production Date"] >= s) & (df["Production Date"] <= e)]
if sel_parties: df = df[df["Party Name"].isin(sel_parties)]
if sel_quality: df = df[df["QUALITY"].isin(sel_quality)]
if sel_shades:  df = df[df["SHADE"].isin(sel_shades)]
if sel_masters: df = df[df["MASTER NAME"].isin(sel_masters)]

if df.empty:
    st.warning("⚠️ No data matches the selected filters.")
    st.stop()

# ─────────────────────────────────────────────
# VIEW TOGGLE
# ─────────────────────────────────────────────
st.markdown("<div style='height:4px'></div>", unsafe_allow_html=True)
vt_col1, vt_col2, vt_spacer = st.columns([1, 1, 5])
with vt_col1:
    day_btn = st.button(
        "📅  Day Wise", use_container_width=True,
        type="primary" if st.session_state.get("view", "month") == "day" else "secondary"
    )
with vt_col2:
    month_btn = st.button(
        "📆  Month Wise", use_container_width=True,
        type="primary" if st.session_state.get("view", "month") == "month" else "secondary"
    )
if day_btn:   st.session_state["view"] = "day"
if month_btn: st.session_state["view"] = "month"
current_view = st.session_state.get("view", "month")
st.divider()


# ═══════════════════════════════════════════════════════════
# ── BUSINESS DECISION SECTION HELPERS
# ═══════════════════════════════════════════════════════════

def render_machine_utilization(data):
    if "M.No." not in data.columns:
        st.info("ℹ️ Machine Number (M.No.) column not found in data.")
        return

    section_header("⚙️", "Machine Utilization Analysis", "Performance by machine number")

    mach = data.groupby("M.No.").agg(
        Lots=("MTRS", "count"),
        Weight=("Weight", "sum"),
        Metres=("MTRS", "sum"),
    ).reset_index()
    mach["Avg KG/Lot"] = (mach["Weight"] / mach["Lots"]).round(1)
    mach = mach.sort_values("Weight", ascending=False)

    avg_weight = mach["Weight"].mean()
    mach["Status"] = mach["Weight"].apply(
        lambda w: "🔴 Under" if w < avg_weight * 0.7
        else ("🟢 Normal" if w <= avg_weight * 1.3 else "🟡 Overloaded")
    )

    k1, k2, k3, k4 = st.columns(4)
    k1.metric("⚙️ Total Machines",   len(mach))
    k2.metric("🔴 Underutilized",    int((mach["Weight"] < avg_weight * 0.7).sum()))
    k3.metric("🟡 Overloaded",       int((mach["Weight"] > avg_weight * 1.3).sum()))
    k4.metric("📈 Avg KG/Machine",   fmt_in(int(avg_weight)))

    c1, c2 = st.columns([2, 3])
    with c1:
        rows = ""
        for _, r in mach.iterrows():
            rows += (f"<tr><td>{r['M.No.']}</td><td>{fmt_in(r['Weight'])}</td>"
                     f"<td>{int(r['Lots'])}</td><td>{r['Avg KG/Lot']:.1f}</td>"
                     f"<td>{r['Status']}</td></tr>")
        st.markdown(f"""
        <div style="overflow-x:auto;border-radius:12px;border:1px solid #e5e7eb;">
        <table class="leaderboard-table">
          <thead><tr><th>Machine</th><th>Weight (kg)</th><th>Lots</th><th>Avg KG/Lot</th><th>Status</th></tr></thead>
          <tbody>{rows}</tbody>
        </table></div>""", unsafe_allow_html=True)

    with c2:
        colors = ["#ef4444" if s.startswith("🔴") else ("#f59e0b" if s.startswith("🟡") else "#10b981")
                  for s in mach["Status"]]
        fig_m = go.Figure(go.Bar(
            y=mach["M.No."], x=mach["Weight"], orientation="h",
            marker=dict(color=colors, line=dict(width=0)),
            text=[f"{fmt_in(v)} kg" for v in mach["Weight"]],
            textposition="outside", textfont=dict(color="#374151", size=11, family="JetBrains Mono"),
        ))
        fig_m.add_vline(x=avg_weight, line_dash="dot", line_color="#6366f1", line_width=2,
                        annotation_text="Avg", annotation_font_color="#6366f1")
        apply_layout(fig_m, "Machine-wise Production Weight (KG)", height=max(280, len(mach)*40), show_legend=False)
        fig_m.update_yaxes(showgrid=False)
        pc(fig_m)

    if data["Production Date"].nunique() > 1:
        heat_data = data.groupby(["M.No.", data["Production Date"].dt.strftime("%d %b")])["Weight"].sum().reset_index()
        heat_data.columns = ["Machine", "Date", "Weight"]
        heat_pivot = heat_data.pivot(index="Machine", columns="Date", values="Weight").fillna(0)
        fig_heat = go.Figure(go.Heatmap(
            z=heat_pivot.values,
            x=heat_pivot.columns.tolist(),
            y=heat_pivot.index.tolist(),
            colorscale=[[0, "#f9fafb"], [0.5, "#fef3c7"], [1, "#d97706"]],
            text=[[fmt_in(int(v)) if v > 0 else "" for v in row] for row in heat_pivot.values],
            texttemplate="%{text}", textfont=dict(size=9, color="#374151"),
            hovertemplate="Machine: %{y}<br>Date: %{x}<br>Weight: %{z} kg<extra></extra>",
            showscale=True,
        ))
        apply_layout(fig_heat, "Daily Production Heatmap — Machine × Date", height=max(280, len(heat_pivot)*32), show_legend=False)
        fig_heat.update_layout(margin=dict(l=60, r=10, t=40, b=60))
        pc(fig_heat)


def render_master_productivity(data):
    section_header("👤", "Master Productivity Dashboard", "Ranked leaderboard with KPIs per master")

    masters = data.groupby("MASTER NAME").agg(
        Weight=("Weight", "sum"),
        Metres=("MTRS", "sum"),
        Lots=("MTRS", "count"),
        Days=("Production Date", "nunique"),
    ).reset_index()
    masters["Avg KG/Lot"]   = (masters["Weight"] / masters["Lots"]).round(1)
    masters["Avg Mtrs/Day"] = (masters["Metres"] / masters["Days"]).round(0).astype(int)
    masters["Share %"]      = (masters["Weight"] / masters["Weight"].sum() * 100).round(1)
    masters = masters.sort_values("Weight", ascending=False).reset_index(drop=True)

    rank_icons = {0: "🥇", 1: "🥈", 2: "🥉"}
    rows = ""
    for i, r in masters.iterrows():
        badge = rank_icons.get(i, f"#{i+1}")
        rows += (f"<tr><td>{badge}</td><td>{r['MASTER NAME']}</td>"
                 f"<td>{fmt_in(r['Weight'])}</td><td>{fmt_in(r['Metres'])}</td>"
                 f"<td>{int(r['Lots'])}</td><td>{r['Avg KG/Lot']:.1f}</td>"
                 f"<td>{fmt_in(r['Avg Mtrs/Day'])}</td><td>{r['Share %']:.1f}%</td></tr>")

    c1, c2 = st.columns([3, 2])
    with c1:
        st.markdown(f"""
        <div style="overflow-x:auto;border-radius:12px;border:1px solid #e5e7eb;">
        <table class="leaderboard-table">
          <thead><tr><th>Rank</th><th>Master</th><th>Weight (kg)</th><th>Metres</th>
          <th>Lots</th><th>Avg KG/Lot</th><th>Avg Mtrs/Day</th><th>Share %</th></tr></thead>
          <tbody>{rows}</tbody>
        </table></div>""", unsafe_allow_html=True)
    with c2:
        fig_mp = go.Figure(go.Bar(
            x=masters["MASTER NAME"], y=masters["Weight"],
            marker=dict(color=PALETTE[:len(masters)], line=dict(width=0)),
            text=[f"{fmt_in(v)}" for v in masters["Weight"]],
            textposition="outside", textfont=dict(color="#374151", size=11, family="JetBrains Mono"),
        ))
        apply_layout(fig_mp, "Master-wise Total Weight (KG)", height=300, show_legend=False)
        fig_mp.update_xaxes(showgrid=False)
        pc(fig_mp)


def render_small_lot_analysis(data):
    section_header("📦", "Small Lot Analysis", "Lot size distribution and operational cost risk")

    data = data.copy()
    data["Lot Size"] = pd.cut(
        data["Weight"],
        bins=[-1, 99.99, 300, float("inf")],
        labels=["Small (<100 kg)", "Medium (100–300 kg)", "Large (>300 kg)"]
    )
    lot_counts = data["Lot Size"].value_counts().reindex(
        ["Small (<100 kg)", "Medium (100–300 kg)", "Large (>300 kg)"]
    ).fillna(0).reset_index()
    lot_counts.columns = ["Category", "Count"]
    lot_counts["Pct"] = (lot_counts["Count"] / lot_counts["Count"].sum() * 100).round(1)

    small_pct = lot_counts.loc[lot_counts["Category"] == "Small (<100 kg)", "Pct"].values
    small_pct = small_pct[0] if len(small_pct) else 0

    c1, c2, c3 = st.columns(3)
    for col, (_, row) in zip([c1, c2, c3], lot_counts.iterrows()):
        col.metric(f"{row['Category']}", f"{int(row['Count'])} lots", delta=f"{row['Pct']:.1f}% of total")

    c_chart, c_warn = st.columns([2, 3])
    with c_chart:
        colors_lot = ["#ef4444", "#f59e0b", "#10b981"]
        fig_lot = go.Figure(go.Pie(
            labels=lot_counts["Category"], values=lot_counts["Count"], hole=0.55,
            marker=dict(colors=colors_lot, line=dict(color="#ffffff", width=2)),
            textinfo="label+percent", textfont=dict(size=12, color="#374151"),
        ))
        apply_layout(fig_lot, "Lot Size Distribution", height=300)
        pc(fig_lot)
    with c_warn:
        st.markdown("<div style='height:16px'></div>", unsafe_allow_html=True)
        if small_pct >= 40:
            insight_card(f"<strong>{small_pct:.1f}% of all lots are Small (&lt;100 kg).</strong> Critically high — increases setup time, labour cost/kg, and dye wastage. Consider lot consolidation.", kind="risk")
        elif small_pct >= 20:
            insight_card(f"<strong>{small_pct:.1f}% of lots are Small (&lt;100 kg)</strong> — moderate overhead. Review batching opportunities.", kind="warn")
        else:
            insight_card(f"<strong>Small lot percentage is {small_pct:.1f}%</strong> — within acceptable range.", kind="good")

        party_small = (
            data[data["Lot Size"] == "Small (<100 kg)"]
            .groupby("Party Name").size().reset_index(name="Small Lots")
            .sort_values("Small Lots", ascending=False).head(5)
        )
        if not party_small.empty:
            insight_card(
                "Top parties by small lot count: <strong>"
                + ", ".join(f"{r['Party Name']} ({int(r['Small Lots'])})" for _, r in party_small.iterrows())
                + "</strong>. Negotiate minimum batch sizes with these parties.",
                kind="info"
            )


def render_party_dependency(data):
    section_header("🏭", "Party Dependency & Pareto Analysis", "Concentration risk and business dependency")

    party = data.groupby("Party Name").agg(
        Weight=("Weight", "sum"),
        Lots=("MTRS", "count"),
    ).reset_index().sort_values("Weight", ascending=False).reset_index(drop=True)
    party["Contribution %"] = (party["Weight"] / party["Weight"].sum() * 100).round(2)
    party["Cumulative %"]   = party["Contribution %"].cumsum().round(2)
    party["Risk"] = party["Contribution %"].apply(
        lambda p: "🔴 High Risk" if p > 30 else ("🟡 Watch" if p > 15 else "🟢 Safe")
    )

    c1, c2 = st.columns([3, 2])
    with c1:
        bar_colors = ["#ef4444" if p > 30 else ("#f59e0b" if p > 15 else "#d97706") for p in party["Contribution %"]]
        fig_pareto = go.Figure()
        fig_pareto.add_trace(go.Bar(
            x=party["Party Name"], y=party["Weight"],
            name="Weight (kg)", marker=dict(color=bar_colors, line=dict(width=0)),
            text=[f"{fmt_in(v)}" for v in party["Weight"]],
            textposition="outside", textfont=dict(color="#374151", size=10, family="JetBrains Mono"),
            yaxis="y1",
        ))
        fig_pareto.add_trace(go.Scatter(
            x=party["Party Name"], y=party["Cumulative %"],
            name="Cumulative %", mode="lines+markers",
            line=dict(color="#6366f1", width=2.5),
            marker=dict(size=6, color="#6366f1"),
            yaxis="y2",
        ))
        fig_pareto.add_hline(y=80, line_dash="dot", line_color="#ef4444",
                             annotation_text="80% line", annotation_font_color="#ef4444",
                             yref="y2", line_width=1.5)
        fig_pareto.update_layout(
            paper_bgcolor="rgba(255,255,255,1)", plot_bgcolor="rgba(248,249,252,1)",
            font=dict(family="Inter", color="#6b7280", size=12),
            margin=dict(l=10, r=10, t=44, b=10),
            title=dict(text="Pareto Chart — Party-wise Production Weight", font=dict(size=14, color="#111827"), x=0),
            height=360, dragmode="pan",
            yaxis=dict(title="Weight (kg)", gridcolor="#f0f0f0", zerolinecolor="#e5e7eb", linecolor="#e5e7eb"),
            yaxis2=dict(title="Cumulative %", overlaying="y", side="right",
                        range=[0, 110], showgrid=False, ticksuffix="%"),
            xaxis=dict(tickangle=-30, showgrid=False, gridcolor="#f0f0f0", zerolinecolor="#e5e7eb", linecolor="#e5e7eb"),
            legend=dict(orientation="h", x=0, y=1.12, bgcolor="rgba(255,255,255,0.9)",
                        bordercolor="#e5e7eb", borderwidth=1, font=dict(color="#374151", size=11)),
        )
        pc(fig_pareto)
    with c2:
        rows = ""
        for _, r in party.iterrows():
            rows += (f"<tr><td>{r['Party Name']}</td><td>{fmt_in(r['Weight'])}</td>"
                     f"<td>{int(r['Lots'])}</td><td>{r['Contribution %']:.1f}%</td>"
                     f"<td>{r['Cumulative %']:.1f}%</td><td>{r['Risk']}</td></tr>")
        st.markdown(f"""
        <div style="overflow-x:auto;border-radius:12px;border:1px solid #e5e7eb;max-height:360px;overflow-y:auto;">
        <table class="leaderboard-table">
          <thead><tr><th>Party</th><th>Weight</th><th>Lots</th><th>Share%</th><th>Cumul%</th><th>Risk</th></tr></thead>
          <tbody>{rows}</tbody>
        </table></div>""", unsafe_allow_html=True)

    high_risk = party[party["Contribution %"] > 30]
    if not high_risk.empty:
        for _, r in high_risk.iterrows():
            insight_card(
                f"<strong>{r['Party Name']}</strong> contributes <strong>{r['Contribution %']:.1f}%</strong> of total production weight — <strong>high business dependency risk</strong>.",
                kind="risk"
            )
    parties_80 = int((party["Cumulative %"] <= 80).sum()) + 1
    insight_card(
        f"<strong>Top {parties_80} parties</strong> account for 80% of total production. Diversify beyond these to reduce risk.",
        kind="info"
    )


def render_chemical_consumption(data):
    chem_cols = [c for c in ["G/ACID", "DFT", "RC", "XNI", "SOFTNER", "MB"] if c in data.columns]
    if not chem_cols:
        st.info("ℹ️ No chemical consumption columns found.")
        return

    section_header("🧪", "Chemical Consumption Analysis", "Usage patterns and cost optimization signals")

    total_weight = data["Weight"].sum()
    chem_totals  = {c: data[c].sum() for c in chem_cols}
    chem_per_kg  = {c: round(chem_totals[c] / total_weight, 4) if total_weight else 0 for c in chem_cols}

    chem_df = pd.DataFrame({
        "Chemical": list(chem_totals.keys()),
        "Total Used": list(chem_totals.values()),
        "Per KG": list(chem_per_kg.values()),
    }).sort_values("Total Used", ascending=False)

    c1, c2 = st.columns([2, 3])
    with c1:
        rows = ""
        for i, (_, r) in enumerate(chem_df.iterrows()):
            badge = ["🥇","🥈","🥉"][i] if i < 3 else f"#{i+1}"
            rows += (f"<tr><td>{badge}</td><td>{r['Chemical']}</td>"
                     f"<td>{r['Total Used']:,.1f}</td><td>{r['Per KG']:.4f}</td></tr>")
        st.markdown(f"""
        <div style="overflow-x:auto;border-radius:12px;border:1px solid #e5e7eb;">
        <table class="leaderboard-table">
          <thead><tr><th>Rank</th><th>Chemical</th><th>Total Used</th><th>Per KG</th></tr></thead>
          <tbody>{rows}</tbody>
        </table></div>""", unsafe_allow_html=True)
    with c2:
        fig_chem = go.Figure(go.Bar(
            x=chem_df["Chemical"], y=chem_df["Total Used"],
            marker=dict(color=PALETTE[:len(chem_df)], line=dict(width=0)),
            text=[f"{v:,.0f}" for v in chem_df["Total Used"]],
            textposition="outside", textfont=dict(color="#374151", size=11),
        ))
        apply_layout(fig_chem, "Total Chemical Usage", height=280, show_legend=False)
        fig_chem.update_xaxes(showgrid=False)
        pc(fig_chem)

    st.markdown("#### Quality vs Chemical Consumption Heatmap")
    qual_chem = data.groupby("QUALITY")[chem_cols].sum()
    qual_chem = qual_chem.loc[qual_chem.sum(axis=1).nlargest(15).index]
    fig_hm = go.Figure(go.Heatmap(
        z=qual_chem.values, x=chem_cols, y=qual_chem.index.tolist(),
        colorscale=[[0,"#f9fafb"],[0.5,"#fef3c7"],[1,"#d97706"]],
        text=[[f"{v:,.0f}" for v in row] for row in qual_chem.values],
        texttemplate="%{text}", textfont=dict(size=9),
        hovertemplate="Quality: %{y}<br>Chemical: %{x}<br>Value: %{z}<extra></extra>",
        showscale=True,
    ))
    apply_layout(fig_hm, "Top 15 Qualities × Chemical Consumption", height=max(300, len(qual_chem)*28), show_legend=False)
    fig_hm.update_layout(margin=dict(l=100, r=10, t=40, b=40))
    pc(fig_hm)

    top_chem = chem_df.iloc[0]
    insight_card(
        f"<strong>{top_chem['Chemical']}</strong> is the highest consumed chemical "
        f"({top_chem['Total Used']:,.0f} units, {top_chem['Per KG']:.4f} per kg). Prioritise cost negotiation for this chemical.",
        kind="info"
    )
    top_qual_by_chem = qual_chem.sum(axis=1).idxmax()
    insight_card(
        f"Quality <strong>{top_qual_by_chem}</strong> has the highest overall chemical consumption. Review pricing for adequate margin.",
        kind="warn"
    )


def render_shade_complexity(data):
    chem_cols = [c for c in ["G/ACID", "DFT", "RC", "XNI", "SOFTNER", "MB"] if c in data.columns]
    if not chem_cols:
        st.info("ℹ️ Chemical columns not available.")
        return

    section_header("🎨", "Shade Complexity Analysis", "Chemical usage by shade — pricing signals")

    shade_chem = data.groupby("SHADE")[chem_cols].mean().reset_index()
    shade_chem["Total Avg Chem"] = shade_chem[chem_cols].sum(axis=1)
    shade_chem = shade_chem.sort_values("Total Avg Chem", ascending=False).head(10)

    c1, c2 = st.columns([3, 2])
    with c1:
        fig_sc = go.Figure(go.Bar(
            y=shade_chem["SHADE"], x=shade_chem["Total Avg Chem"], orientation="h",
            marker=dict(color=shade_chem["Total Avg Chem"],
                        colorscale=[[0,"#fef3c7"],[0.5,"#f59e0b"],[1,"#d97706"]],
                        showscale=False, line=dict(width=0)),
            text=[f"{v:.2f}" for v in shade_chem["Total Avg Chem"]],
            textposition="outside", textfont=dict(color="#374151", size=11, family="JetBrains Mono"),
        ))
        apply_layout(fig_sc, "Top 10 Shades by Avg Chemical Consumption", height=340, show_legend=False)
        fig_sc.update_yaxes(showgrid=False)
        pc(fig_sc)
    with c2:
        rows = ""
        for _, r in shade_chem.iterrows():
            cells = "".join(f"<td>{r[c]:.2f}</td>" for c in chem_cols if c in r.index)
            rows += f"<tr><td>{r['SHADE']}</td>{cells}<td><strong>{r['Total Avg Chem']:.2f}</strong></td></tr>"
        chem_headers = "".join(f"<th>{c}</th>" for c in chem_cols)
        st.markdown(f"""
        <div style="overflow-x:auto;border-radius:12px;border:1px solid #e5e7eb;max-height:360px;overflow-y:auto;">
        <table class="leaderboard-table">
          <thead><tr><th>Shade</th>{chem_headers}<th>Total</th></tr></thead>
          <tbody>{rows}</tbody>
        </table></div>""", unsafe_allow_html=True)

    top_shade = shade_chem.iloc[0]["SHADE"]
    insight_card(f"Shade <strong>{top_shade}</strong> has the highest average chemical consumption — consider <strong>premium pricing</strong> surcharge.", kind="warn")
    insight_card("Top-10 complexity shades consume significantly more chemicals per lot. Review job-costing to avoid processing at a loss.", kind="info")


def render_quality_efficiency(data):
    section_header("📐", "Quality Efficiency Analysis", "Metres per KG ratio by fabric quality")

    qual_eff = data.groupby("QUALITY").agg(
        Weight=("Weight", "sum"), Metres=("MTRS", "sum"), Lots=("MTRS", "count"),
    ).reset_index()
    qual_eff = qual_eff[qual_eff["Weight"] > 0]
    qual_eff["MTRS/KG"] = (qual_eff["Metres"] / qual_eff["Weight"]).round(3)
    qual_eff = qual_eff.sort_values("MTRS/KG", ascending=False)

    avg_ratio = qual_eff["MTRS/KG"].mean()
    qual_eff["Outlier"] = qual_eff["MTRS/KG"].apply(
        lambda v: "🔴 Low" if v < avg_ratio * 0.75 else ("🟡 High" if v > avg_ratio * 1.25 else "🟢 Normal")
    )

    c1, c2 = st.columns([3, 2])
    with c1:
        colors_qe = ["#ef4444" if o.startswith("🔴") else ("#f59e0b" if o.startswith("🟡") else "#10b981")
                     for o in qual_eff["Outlier"]]
        fig_qe = go.Figure(go.Bar(
            x=qual_eff["QUALITY"], y=qual_eff["MTRS/KG"],
            marker=dict(color=colors_qe, line=dict(width=0)),
            text=[f"{v:.2f}" for v in qual_eff["MTRS/KG"]],
            textposition="outside", textfont=dict(color="#374151", size=10, family="JetBrains Mono"),
        ))
        fig_qe.add_hline(y=avg_ratio, line_dash="dot", line_color="#6366f1", line_width=2,
                         annotation_text=f"Avg {avg_ratio:.2f}", annotation_font_color="#6366f1")
        apply_layout(fig_qe, "MTRS per KG by Quality (Efficiency Ratio)", height=340, show_legend=False)
        fig_qe.update_xaxes(tickangle=-30, showgrid=False)
        pc(fig_qe)
    with c2:
        rows = ""
        for _, r in qual_eff.iterrows():
            rows += (f"<tr><td>{r['QUALITY']}</td><td>{fmt_in(r['Weight'])}</td>"
                     f"<td>{fmt_in(r['Metres'])}</td><td><strong>{r['MTRS/KG']:.3f}</strong></td>"
                     f"<td>{r['Outlier']}</td></tr>")
        st.markdown(f"""
        <div style="overflow-x:auto;border-radius:12px;border:1px solid #e5e7eb;max-height:360px;overflow-y:auto;">
        <table class="leaderboard-table">
          <thead><tr><th>Quality</th><th>Weight</th><th>Metres</th><th>MTRS/KG</th><th>Status</th></tr></thead>
          <tbody>{rows}</tbody>
        </table></div>""", unsafe_allow_html=True)

    low_eff = qual_eff[qual_eff["Outlier"].str.startswith("🔴")]
    if not low_eff.empty:
        names = ", ".join(low_eff["QUALITY"].tolist())
        insight_card(f"Qualities <strong>{names}</strong> have a significantly <strong>low MTRS/KG ratio</strong> — worth investigating for heavy fabrics or data anomalies.", kind="risk")
    high_eff = qual_eff[qual_eff["Outlier"].str.startswith("🟡")]
    if not high_eff.empty:
        names = ", ".join(high_eff["QUALITY"].tolist())
        insight_card(f"Qualities <strong>{names}</strong> have a notably <strong>high MTRS/KG ratio</strong> — lightweight fabrics needing careful handling.", kind="info")


def render_mom_comparison(data, sel_month):
    section_header("📅", "Month-over-Month Performance", "Selected month vs previous month")

    data = data.copy()
    data["Month"] = data["Production Date"].dt.to_period("M")
    cur_df  = data[data["Month"] == sel_month]
    prev_m  = sel_month - 1
    prev_df = data[data["Month"] == prev_m]

    if prev_df.empty:
        st.info(f"ℹ️ No data for {prev_m.strftime('%B %Y')} to compare against.")
        return

    metrics = {
        "⚖️ Weight (kg)": ("Weight", "sum"),
        "📏 Metres":      ("MTRS",   "sum"),
        "🧵 Lots":        ("MTRS",   "count"),
    }

    cols = st.columns(len(metrics))
    for col, (label, (field, agg)) in zip(cols, metrics.items()):
        cur_val  = cur_df[field].sum()  if agg == "sum" else len(cur_df)
        prev_val = prev_df[field].sum() if agg == "sum" else len(prev_df)
        delta    = ((cur_val - prev_val) / prev_val * 100) if prev_val else 0
        delta_cls   = "delta-pos" if delta >= 0 else "delta-neg"
        delta_arrow = "▲" if delta > 0 else ("▼" if delta < 0 else "–")
        col.markdown(f"""
        <div class="mom-card">
          <div class="lbl">{label}</div>
          <div class="val">{fmt_in(int(cur_val))}</div>
          <div class="{delta_cls}">{delta_arrow} {abs(delta):.1f}% vs {prev_m.strftime('%b %Y')}</div>
          <div style="font-size:11px;color:#9ca3af;margin-top:4px;">Prev: {fmt_in(int(prev_val))}</div>
        </div>""", unsafe_allow_html=True)

    st.markdown("<div style='height:16px'></div>", unsafe_allow_html=True)
    trend_data = data[data["Month"].isin([prev_m, sel_month])].copy()
    trend_data["Month_str"] = trend_data["Production Date"].dt.strftime("%B %Y")
    daily_trend = trend_data.groupby(["Month_str","Production Date"]).agg(
        Weight=("Weight","sum"), Metres=("MTRS","sum")
    ).reset_index().sort_values("Production Date")
    daily_trend["Day"] = daily_trend["Production Date"].dt.day

    fig_trend = go.Figure()
    month_colors = {prev_m.strftime("%B %Y"): "#94a3b8", sel_month.strftime("%B %Y"): "#d97706"}
    for mname, grp in daily_trend.groupby("Month_str"):
        fig_trend.add_trace(go.Scatter(
            x=grp["Day"], y=grp["Weight"], name=mname, mode="lines+markers",
            line=dict(color=month_colors.get(mname, "#d97706"), width=2.5),
            marker=dict(size=5),
        ))
    apply_layout(fig_trend, "Daily Weight Trend — Current vs Previous Month", height=280)
    fig_trend.update_xaxes(title_text="Day of Month")
    fig_trend.update_yaxes(title_text="Weight (kg)")
    pc(fig_trend)

    cur_wt  = cur_df["Weight"].sum()
    prev_wt = prev_df["Weight"].sum()
    if prev_wt:
        d = (cur_wt - prev_wt) / prev_wt * 100
        if d > 5:
            insight_card(f"Production weight <strong>increased by {d:.1f}%</strong> vs {prev_m.strftime('%B %Y')}. Ensure machine and staffing capacity can sustain this.", kind="good")
        elif d < -5:
            insight_card(f"Production weight <strong>declined by {abs(d):.1f}%</strong> vs {prev_m.strftime('%B %Y')}. Investigate order pipeline, machine downtime, or seasonal demand shifts.", kind="risk")
        else:
            insight_card(f"Production weight is <strong>relatively stable</strong> ({d:+.1f}% vs {prev_m.strftime('%B %Y')}). Consistent performance.", kind="info")


def render_business_insights(data, scope_label=""):
    section_header("💡", "Business Insights Panel", f"Auto-generated insights · {scope_label}")

    insights = []
    party     = data.groupby("Party Name")["Weight"].sum()
    total_wt  = party.sum()
    for pname, wt in party.items():
        pct = wt / total_wt * 100 if total_wt else 0
        if pct > 40:
            insights.append(("risk", "🔴", f"<strong>{pname}</strong> contributes <strong>{pct:.1f}%</strong> of production weight — <strong>critically high</strong> dependency risk."))
        elif pct > 30:
            insights.append(("warn", "⚠️", f"<strong>{pname}</strong> contributes <strong>{pct:.1f}%</strong> of production. Diversify order intake."))

    if "M.No." in data.columns:
        mach_wt = data.groupby("M.No.")["Weight"].sum()
        avg_mwt = mach_wt.mean()
        for mno, wt in mach_wt.items():
            if avg_mwt and wt < avg_mwt * 0.6:
                pct_below = (1 - wt / avg_mwt) * 100
                insights.append(("warn", "⚙️", f"Machine <strong>{mno}</strong> processed <strong>{pct_below:.0f}% less</strong> than average. Check for downtime or underallocation."))

    small_pct = (data["Weight"] < 100).sum() / len(data) * 100 if len(data) else 0
    if small_pct > 30:
        insights.append(("risk", "📦", f"Small lots (&lt;100 kg) account for <strong>{small_pct:.1f}%</strong> of all lots — increasing cost per kg."))
    elif small_pct > 15:
        insights.append(("warn", "📦", f"Small lots represent <strong>{small_pct:.1f}%</strong> of total lots. Monitor — above 30% is costly."))

    chem_cols = [c for c in ["G/ACID","DFT","RC","XNI","SOFTNER","MB"] if c in data.columns]
    if chem_cols:
        shade_chem = data.groupby("SHADE")[chem_cols].mean().sum(axis=1)
        if not shade_chem.empty:
            top_shade = shade_chem.idxmax()
            insights.append(("info", "🎨", f"Shade <strong>{top_shade}</strong> has the highest avg chemical consumption — consider premium pricing."))

    master_wt = data.groupby("MASTER NAME")["Weight"].sum()
    if not master_wt.empty:
        top_master = master_wt.idxmax()
        insights.append(("good", "👤", f"Master <strong>{top_master}</strong> supervised the highest production weight (<strong>{fmt_in(int(master_wt[top_master]))} kg</strong>). Recognise and retain."))

    working_days = data["Production Date"].nunique()
    total_days   = (data["Production Date"].max() - data["Production Date"].min()).days + 1
    if total_days > 0:
        utilization = working_days / total_days * 100
        if utilization < 70:
            insights.append(("warn", "📅", f"Factory operational for only <strong>{working_days} of {total_days} days</strong> ({utilization:.0f}% utilization). Review downtime causes."))

    qual_eff = data.groupby("QUALITY").agg(Weight=("Weight","sum"), Metres=("MTRS","sum")).reset_index()
    qual_eff = qual_eff[qual_eff["Weight"] > 0]
    qual_eff["ratio"] = qual_eff["Metres"] / qual_eff["Weight"]
    if not qual_eff.empty:
        avg_r = qual_eff["ratio"].mean()
        low_q = qual_eff[qual_eff["ratio"] < avg_r * 0.6]
        if not low_q.empty:
            names = ", ".join(low_q["QUALITY"].tolist())
            insights.append(("info", "📐", f"Qualities <strong>{names}</strong> have unusually low MTRS/KG ratios — verify data accuracy or processing parameters."))

    if not insights:
        insights.append(("good", "✅", "No major risk signals detected. Operations appear within normal parameters."))

    for kind, icon, text in insights:
        insight_card(text, kind=kind, icon=icon)


# ═══════════════════════════════════════════════════════════
# DAY WISE VIEW
# ═══════════════════════════════════════════════════════════
if current_view == "day":

    available_days = sorted(df["Production Date"].dt.date.unique(), reverse=True)
    sel_day = st.selectbox(
        "📅 Select Date", available_days,
        format_func=lambda d: d.strftime("%d %B %Y — %A"),
        label_visibility="visible"
    )
    day_df = df[df["Production Date"].dt.date == sel_day]

    if day_df.empty:
        st.warning("No data for this date.")
        st.stop()

    master_today = day_df["MASTER NAME"].value_counts().idxmax()
    st.markdown(f"""
    <div class="day-header">
      <div>
        <div style="font-size:1.1rem;font-weight:800;letter-spacing:-.3px;">
          📋 Production Sheet — {sel_day.strftime('%d %B %Y')}
        </div>
        <div style="font-size:.82rem;opacity:.8;margin-top:4px;">
          Master: {master_today} &nbsp;·&nbsp; {sel_day.strftime('%A')}
        </div>
      </div>
      <div style="text-align:right;font-size:.82rem;opacity:.7;">
        Lots: {len(day_df)} &nbsp;·&nbsp; Metres: {fmt_in(day_df['MTRS'].sum())} &nbsp;·&nbsp; Weight: {fmt_in(day_df['Weight'].sum())} kg
      </div>
    </div>
    """, unsafe_allow_html=True)

    # ── KPI row: Weight first, then Metres, then Lots ──────────────
    d_weight  = int(day_df["Weight"].sum())
    d_mtrs    = int(day_df["MTRS"].sum())
    d_lots    = len(day_df)
    d_parties = day_df["Party Name"].nunique()
    d_ratio   = round(d_mtrs / d_weight, 2) if d_weight else 0

    k1, k2, k3, k4, k5 = st.columns(5)
    k1.metric("⚖️ Weight (kg)",  fmt_in(d_weight))
    k2.metric("📏 Metres",       fmt_in(d_mtrs))
    k3.metric("🧵 Lots",         d_lots)
    k4.metric("🏭 Parties",      d_parties)
    with k5:
        ratio_widget(d_ratio)         # ← widget, not text pill

    st.divider()

    # ── Production sheet ────────────────────────────────────────────
    st.markdown("#### 📋 Lot-wise Production Sheet")
    chem_cols    = [c for c in ["G/ACID","DFT","RC","XNI","SOFTNER","MB","MB %"] if c in day_df.columns]
    display_cols = ["LOT NO.","Party Name","QUALITY","SHADE","SIZE","MTRS","Weight"] + chem_cols + ["MASTER NAME"]
    display_cols = [c for c in display_cols if c in day_df.columns]
    sheet_df     = day_df[display_cols].copy().reset_index(drop=True)
    sheet_df.index = sheet_df.index + 1

    headers_html    = "".join(f"<th>{c}</th>" for c in display_cols)
    rows_html_sheet = ""
    for i, row in sheet_df.iterrows():
        cells = "".join(
            f"<td><b>{fmt_in(row[col])}</b></td>" if col in ["MTRS","Weight"] else f"<td>{row[col]}</td>"
            for col in display_cols
        )
        rows_html_sheet += f"<tr><td><b>{i}</b></td>{cells}</tr>"

    total_cells = "".join(
        f"<td><b>{fmt_in(day_df[col].sum())}</b></td>" if col in ["MTRS","Weight"]
        else ("<td><b>TOTAL</b></td>" if col == "LOT NO." else "<td>—</td>")
        for col in display_cols
    )

    st.markdown(f"""
    <div style="overflow-x:auto;border-radius:12px;border:1px solid #e5e7eb;margin-bottom:16px;">
    <table class="prod-sheet-table">
      <thead><tr><th>#</th>{headers_html}</tr></thead>
      <tbody>
        {rows_html_sheet}
        <tr class="prod-sheet-total"><td><b>∑</b></td>{total_cells}</tr>
      </tbody>
    </table></div>
    """, unsafe_allow_html=True)

    st.divider()

    # ── Charts 2-up ─────────────────────────────────────────────────
    dc1, dc2 = st.columns(2)
    with dc1:
        p_day = day_df.groupby("Party Name").agg(Weight=("Weight","sum"), Metres=("MTRS","sum")).reset_index().sort_values("Weight", ascending=True)
        p_day["Share"] = (p_day["Weight"] / p_day["Weight"].sum() * 100).round(1)
        fig_pd = go.Figure(go.Bar(
            y=p_day["Party Name"], x=p_day["Weight"], orientation="h",
            marker=dict(color=p_day["Weight"], colorscale=[[0,"#fef3c7"],[0.5,"#f59e0b"],[1,"#d97706"]], showscale=False, line=dict(width=0)),
            text=[f"{fmt_in(v)} kg ({s}%)" for v,s in zip(p_day["Weight"], p_day["Share"])],
            textposition="outside", textfont=dict(color="#374151", size=11, family="JetBrains Mono"),
        ))
        apply_layout(fig_pd, "Party-wise Production (KG) — Today", height=320, show_legend=False)
        fig_pd.update_yaxes(showgrid=False)
        pc(fig_pd)

    with dc2:
        q_day = day_df.groupby("QUALITY").agg(Weight=("Weight","sum")).reset_index().sort_values("Weight", ascending=False).head(10)
        q_day["Share"] = (q_day["Weight"] / q_day["Weight"].sum() * 100).round(1)
        fig_qd = go.Figure(go.Bar(
            x=q_day["QUALITY"], y=q_day["Weight"],
            marker=dict(color=list(range(len(q_day))), colorscale="Oranges", showscale=False, line=dict(width=0)),
            text=[f"{fmt_in(v)}\n({s}%)" for v,s in zip(q_day["Weight"], q_day["Share"])],
            textposition="outside", textfont=dict(color="#374151", size=10, family="JetBrains Mono"),
        ))
        apply_layout(fig_qd, "Quality-wise (KG) — Today", height=320, show_legend=False)
        fig_qd.update_xaxes(tickangle=-30, showgrid=False)
        pc(fig_qd)

    dc3, dc4 = st.columns(2)
    with dc3:
        shade_day = day_df.groupby("SHADE").size().reset_index(name="Lots").sort_values("Lots", ascending=False)
        fig_sd = go.Figure(go.Pie(
            labels=shade_day["SHADE"], values=shade_day["Lots"], hole=0.52,
            marker=dict(colors=PALETTE[:len(shade_day)], line=dict(color="#ffffff", width=2)),
            textinfo="label+percent", textfont=dict(size=11, color="#374151"),
        ))
        apply_layout(fig_sd, "Shade Distribution — Today", height=300)
        pc(fig_sd)

    with dc4:
        master_day = day_df.groupby("MASTER NAME").size().reset_index(name="Lots").sort_values("Lots", ascending=False)
        fig_md = go.Figure(go.Pie(
            labels=master_day["MASTER NAME"], values=master_day["Lots"], hole=0.55,
            marker=dict(colors=["#d97706","#3b82f6","#8b5cf6","#10b981","#ef4444"], line=dict(color="#ffffff", width=2)),
            textinfo="label+percent", textfont=dict(size=12, color="#374151"),
        ))
        apply_layout(fig_md, "Master Allocation — Today", height=300)
        pc(fig_md)

    # ── Party summary table ──────────────────────────────────────────
    section_divider("📋 Party-wise Summary — Today")
    day_sum = day_df.groupby("Party Name").agg(Metres=("MTRS","sum"), Weight_kg=("Weight","sum"), Lots=("MTRS","count")).reset_index().sort_values("Weight_kg", ascending=False)
    day_sum["Avg KG/Lot"]       = (day_sum["Weight_kg"] / day_sum["Lots"]).round(1)
    day_sum["Avg Mtrs/Lot"]     = (day_sum["Metres"]    / day_sum["Lots"]).round(0).astype(int)
    day_sum["Share % (Weight)"] = (day_sum["Weight_kg"] / day_sum["Weight_kg"].sum() * 100).round(1)
    rows_day = "".join(
        f"<tr><td>{r['Party Name']}</td><td>{fmt_in(r['Metres'])}</td><td>{fmt_in(r['Weight_kg'])}</td>"
        f"<td>{int(r['Lots'])}</td><td>{r['Avg KG/Lot']:.1f}</td><td>{fmt_in(r['Avg Mtrs/Lot'])}</td>"
        f"<td>{r['Share % (Weight)']:.1f}%</td></tr>"
        for _, r in day_sum.iterrows()
    )
    st.markdown(f"""
    <div style="background:#fff;border:1px solid #e8ecf2;border-radius:14px;overflow:hidden;box-shadow:0 1px 4px rgba(0,0,0,0.05);">
    <table class="sum-table">
      <thead><tr><th>Party</th><th>Metres</th><th>Weight (kg)</th><th>Lots</th><th>Avg KG/Lot</th><th>Avg Mtrs/Lot</th><th>Share % (Weight)</th></tr></thead>
      <tbody>{rows_day}</tbody>
    </table></div>
    """, unsafe_allow_html=True)

    # ── Business Decision Sections ───────────────────────────────────
    st.divider()
    section_divider("🧠 Business Decision Analysis — Day View")
    render_machine_utilization(day_df)
    st.divider()
    render_master_productivity(day_df)
    st.divider()
    render_small_lot_analysis(day_df)
    st.divider()
    render_party_dependency(day_df)
    st.divider()
    render_chemical_consumption(day_df)
    st.divider()
    render_shade_complexity(day_df)
    st.divider()
    render_quality_efficiency(day_df)
    st.divider()
    render_business_insights(day_df, scope_label=sel_day.strftime("%d %B %Y"))


# ═══════════════════════════════════════════════════════════
# MONTH WISE VIEW
# ═══════════════════════════════════════════════════════════
else:
    df["Month"]     = df["Production Date"].dt.to_period("M")
    df["Month_str"] = df["Production Date"].dt.strftime("%B %Y")
    available_months = sorted(df["Month"].unique(), reverse=True)
    month_labels     = {str(m): df[df["Month"]==m]["Month_str"].iloc[0] for m in available_months}
    sel_month_str    = st.selectbox(
        "📆 Select Month", [str(m) for m in available_months],
        format_func=lambda m: month_labels[m], label_visibility="visible"
    )
    sel_month = pd.Period(sel_month_str, freq="M")
    month_df  = df[df["Month"] == sel_month]

    if month_df.empty:
        st.warning("No data for this month.")
        st.stop()

    total_weight   = int(month_df["Weight"].sum())
    total_mtrs     = int(month_df["MTRS"].sum())
    total_lots     = len(month_df)
    active_parties = month_df["Party Name"].nunique()
    working_days   = month_df["Production Date"].nunique()
    avg_kg_per_day = int(total_weight / working_days) if working_days else 0
    mtr_kg_ratio   = round(total_mtrs / total_weight, 2) if total_weight else 0

    all_mtrs   = int(df["MTRS"].sum())
    all_weight = int(df["Weight"].sum())
    delta_weight = f"{(total_weight/all_weight*100):.1f}% of total" if total_weight != all_weight else None
    delta_mtrs   = f"{(total_mtrs/all_mtrs*100):.1f}% of total"    if total_mtrs   != all_mtrs   else None
    delta_lots   = f"{(total_lots/len(df)*100):.1f}% of total"     if total_lots   != len(df)    else None

    # ── KPI row: Weight first, Metres second, ratio as widget ───────
    k1, k2, k3, k4, k5, k6 = st.columns(6)
    k1.metric("⚖️ Total Weight (kg)", fmt_in(total_weight), delta=delta_weight)
    k2.metric("📏 Total Metres",      fmt_in(total_mtrs),   delta=delta_mtrs)
    k3.metric("🧵 Total Lots",        fmt_in(total_lots),   delta=delta_lots)
    k4.metric("🏭 Active Parties",    active_parties)
    k5.metric("📅 Working Days",      working_days)
    with k6:
        ratio_widget(mtr_kg_ratio)    # ← widget, not text pill

    st.divider()

    # ── Daily weight bar chart ───────────────────────────────────────
    daily  = month_df.groupby("Production Date").agg(Metres=("MTRS","sum"), Weight=("Weight","sum"), Lots=("MTRS","count")).reset_index().sort_values("Production Date")
    avg_wt = daily["Weight"].mean()
    bar_colors_wt = ["#d97706" if v >= avg_wt*1.1 else "#ef4444" if v < avg_wt*0.7 else "#f59e0b" for v in daily["Weight"]]
    fig_wt_day = go.Figure(go.Bar(
        x=daily["Production Date"], y=daily["Weight"],
        marker_color=bar_colors_wt,
        text=[fmt_in(int(v)) for v in daily["Weight"]], textposition="outside",
        textfont=dict(size=9, family="JetBrains Mono", color="#374151"),
    ))
    fig_wt_day.add_hline(y=avg_wt, line_dash="dot", line_color="#d97706", line_width=1.5,
                         annotation_text=f"Avg {fmt_in(int(avg_wt))} kg",
                         annotation_font_color="#374151", annotation_position="top right")
    apply_layout(fig_wt_day, "Daily Production Weight (KG)", height=280, show_legend=False)
    pc(fig_wt_day)

    # ── Party bar + Quality bar side-by-side ─────────────────────────
    row2_c1, row2_c2 = st.columns(2)
    with row2_c1:
        party_df = month_df.groupby("Party Name").agg(Weight=("Weight","sum"), Metres=("MTRS","sum"), Lots=("MTRS","count")).reset_index().sort_values("Weight", ascending=True)
        party_df["Share"] = (party_df["Weight"] / party_df["Weight"].sum() * 100).round(1)
        fig_party = go.Figure(go.Bar(
            y=party_df["Party Name"], x=party_df["Weight"], orientation="h",
            marker=dict(color=party_df["Weight"], colorscale=[[0,"#fef3c7"],[0.5,"#f59e0b"],[1,"#d97706"]], showscale=False, line=dict(width=0)),
            text=[f"{fmt_in(v)} ({s}%)" for v,s in zip(party_df["Weight"], party_df["Share"])],
            textposition="outside", textfont=dict(color="#374151", size=10, family="JetBrains Mono"),
        ))
        apply_layout(fig_party, "Party-wise Production (KG)", height=380, show_legend=False)
        fig_party.update_yaxes(showgrid=False)
        pc(fig_party)

    with row2_c2:
        quality_df = month_df.groupby("QUALITY").agg(Weight=("Weight","sum"), Lots=("MTRS","count")).reset_index().sort_values("Weight", ascending=False).head(12)
        quality_df["Share"] = (quality_df["Weight"] / quality_df["Weight"].sum() * 100).round(1)
        fig_qual = go.Figure(go.Bar(
            x=quality_df["QUALITY"], y=quality_df["Weight"],
            marker=dict(color=list(range(len(quality_df))), colorscale="Oranges", showscale=False, line=dict(width=0)),
            text=[f"{fmt_in(int(v))}\n({s}%)" for v,s in zip(quality_df["Weight"], quality_df["Share"])],
            textposition="outside", textfont=dict(color="#374151", size=10, family="JetBrains Mono"),
        ))
        apply_layout(fig_qual, "Top Fabric Qualities by KG", height=380, show_legend=False)
        fig_qual.update_xaxes(tickangle=-30, showgrid=False)
        pc(fig_qual)

    # ── Shade + Master pie side-by-side ──────────────────────────────
    c3, c4 = st.columns(2)
    with c3:
        shade_df   = month_df.groupby("SHADE").size().reset_index(name="Lots").sort_values("Lots", ascending=False)
        top_shades = shade_df.head(10).copy()
        others     = shade_df.iloc[10:]["Lots"].sum()
        if others > 0:
            top_shades = pd.concat([top_shades, pd.DataFrame([{"SHADE":"Others","Lots":others}])], ignore_index=True)
        fig_shade = go.Figure(go.Pie(
            labels=top_shades["SHADE"], values=top_shades["Lots"], hole=0.52,
            marker=dict(colors=PALETTE[:len(top_shades)], line=dict(color="#ffffff", width=2)),
            textinfo="label+percent", textfont=dict(size=11, color="#374151"),
        ))
        apply_layout(fig_shade, "Shade Distribution (Lots)", height=320)
        fig_shade.update_layout(legend=dict(orientation="v", x=1.02, y=0.5, font=dict(size=11, color="#374151")))
        pc(fig_shade)

    with c4:
        master_df = month_df.groupby("MASTER NAME").size().reset_index(name="Lots").sort_values("Lots", ascending=False)
        fig_master = go.Figure(go.Pie(
            labels=master_df["MASTER NAME"], values=master_df["Lots"], hole=0.55,
            marker=dict(colors=["#d97706","#3b82f6","#8b5cf6","#10b981","#ef4444"], line=dict(color="#ffffff", width=2)),
            textinfo="label+percent", textfont=dict(size=12, color="#374151"),
        ))
        apply_layout(fig_master, "Master Allocation", height=320)
        pc(fig_master)

    # ── Lots/day + Bubble side-by-side ───────────────────────────────
    c5, c6 = st.columns(2)
    with c5:
        lots_df  = month_df.groupby("Production Date").size().reset_index(name="Lots").sort_values("Production Date")
        avg_lots = lots_df["Lots"].mean()
        bar_colors_lots = ["#d97706" if v >= avg_lots*1.1 else "#ef4444" if v < avg_lots*0.7 else "#f59e0b" for v in lots_df["Lots"]]
        fig_lots = go.Figure(go.Bar(
            x=lots_df["Production Date"], y=lots_df["Lots"],
            marker_color=bar_colors_lots,
            text=lots_df["Lots"], textposition="outside",
            textfont=dict(size=10, family="JetBrains Mono", color="#374151"),
        ))
        fig_lots.add_hline(y=avg_lots, line_dash="dot", line_color="#d97706", line_width=1.5,
                           annotation_text=f"Avg {avg_lots:.1f} lots/day",
                           annotation_font_color="#374151", annotation_position="top right")
        apply_layout(fig_lots, "Lots Processed Per Day", height=280, show_legend=False)
        pc(fig_lots)

    with c6:
        scatter_df = month_df.groupby("Party Name").agg(Metres=("MTRS","sum"), Weight=("Weight","sum"), Lots=("MTRS","count")).reset_index()
        fig_scatter = px.scatter(
            scatter_df, x="Metres", y="Weight", size="Lots", color="Party Name",
            color_discrete_sequence=PALETTE, text="Party Name", size_max=50,
            hover_data={"Lots":True,"Metres":":,.0f","Weight":":,.0f"}
        )
        fig_scatter.update_traces(textposition="top center", textfont=dict(size=10, color="#374151"))
        apply_layout(fig_scatter, "Metres vs Weight by Party (bubble = lots)", height=280)
        pc(fig_scatter)

    # ── Party summary table ──────────────────────────────────────────
    section_divider("📋 Party-wise Summary")
    summary = month_df.groupby("Party Name").agg(Metres=("MTRS","sum"), Weight_kg=("Weight","sum"), Lots=("MTRS","count")).reset_index().sort_values("Weight_kg", ascending=False)
    summary["Avg KG/Lot"]       = (summary["Weight_kg"] / summary["Lots"]).round(1)
    summary["Avg Mtrs/Lot"]     = (summary["Metres"]    / summary["Lots"]).round(0).astype(int)
    summary["Share % (Weight)"] = (summary["Weight_kg"] / summary["Weight_kg"].sum() * 100).round(1)
    rows_html = "".join(
        f"<tr><td>{r['Party Name']}</td><td>{fmt_in(r['Metres'])}</td><td>{fmt_in(r['Weight_kg'])}</td>"
        f"<td>{int(r['Lots'])}</td><td>{r['Avg KG/Lot']:.1f}</td><td>{fmt_in(r['Avg Mtrs/Lot'])}</td>"
        f"<td>{r['Share % (Weight)']:.1f}%</td></tr>"
        for _, r in summary.iterrows()
    )
    st.markdown(f"""
    <div style="background:#fff;border:1px solid #e8ecf2;border-radius:14px;overflow:hidden;box-shadow:0 1px 4px rgba(0,0,0,0.05);">
    <table class="sum-table">
      <thead><tr><th>Party</th><th>Metres</th><th>Weight (kg)</th><th>Lots</th><th>Avg KG/Lot</th><th>Avg Mtrs/Lot</th><th>Share % (Weight)</th></tr></thead>
      <tbody>{rows_html}</tbody>
    </table></div>
    """, unsafe_allow_html=True)

    # ── Quality breakdown expander ───────────────────────────────────
    with st.expander("🧵 Quality-wise Breakdown"):
        q_summary = month_df.groupby(["QUALITY","SHADE"]).agg(Metres=("MTRS","sum"), Weight=("Weight","sum"), Lots=("MTRS","count")).reset_index().sort_values("Weight", ascending=False)
        col_a, col_b = st.columns([2,1])
        with col_a:
            q_rows = "".join(
                f"<tr><td>{r['QUALITY']}</td><td>{r['SHADE']}</td><td>{fmt_in(r['Weight'])}</td><td>{fmt_in(r['Metres'])}</td><td>{int(r['Lots'])}</td></tr>"
                for _, r in q_summary.iterrows()
            )
            st.markdown(f"""
            <style>
              .q-table{{width:100%;border-collapse:collapse;font-size:12px;}}
              .q-table th{{background:#f3f4f6;color:#6b7280;text-transform:uppercase;font-size:10px;letter-spacing:.06em;padding:9px 12px;border-bottom:1px solid #e5e7eb;text-align:left;font-weight:600;}}
              .q-table td{{padding:8px 12px;color:#1f2937;border-bottom:1px solid #f9fafb;font-family:'JetBrains Mono',monospace;font-size:11px;}}
              .q-table td:first-child{{color:#d97706;font-family:'Inter',sans-serif;font-weight:600;}}
              .q-table td:nth-child(2){{color:#3b82f6;font-family:'Inter',sans-serif;}}
              .q-table tr:hover td{{background:#fafafa;}}
            </style>
            <div style="max-height:360px;overflow-y:auto;border-radius:10px;border:1px solid #e5e7eb;">
            <table class="q-table">
              <thead><tr><th>Quality</th><th>Shade</th><th>Weight (kg)</th><th>Metres</th><th>Lots</th></tr></thead>
              <tbody>{q_rows}</tbody>
            </table></div>
            """, unsafe_allow_html=True)
        with col_b:
            fig_qtree = px.treemap(q_summary.head(30), path=["QUALITY","SHADE"], values="Weight", color="Weight", color_continuous_scale="Oranges")
            fig_qtree.update_layout(paper_bgcolor="rgba(255,255,255,1)", font=dict(color="#374151"), height=380, margin=dict(l=0,r=0,t=0,b=0))
            fig_qtree.update_coloraxes(showscale=False)
            pc(fig_qtree)

    # ── Business Decision Sections ────────────────────────────────────
    st.divider()
    section_divider("🧠 Business Decision Analysis — Month View")
    render_machine_utilization(month_df)
    st.divider()
    render_master_productivity(month_df)
    st.divider()
    render_small_lot_analysis(month_df)
    st.divider()
    render_party_dependency(month_df)
    st.divider()
    render_chemical_consumption(month_df)
    st.divider()
    render_shade_complexity(month_df)
    st.divider()
    render_quality_efficiency(month_df)
    st.divider()
    render_mom_comparison(df, sel_month)
    st.divider()
    render_business_insights(month_df, scope_label=month_labels[sel_month_str])


# ─────────────────────────────────────────────
# RAW DATA EXPANDER
# ─────────────────────────────────────────────
view_df = day_df if current_view == "day" else month_df
with st.expander("🗃️ View Raw Data — Excel Mode"):
    st.markdown(f"**{len(view_df):,} rows** after filters")
    display_df = view_df.copy()
    display_df["Production Date"] = display_df["Production Date"].dt.strftime("%d-%b-%Y")
    col_search, col_download = st.columns([3, 1])
    with col_search:
        search = st.text_input("🔍 Search", placeholder="Type to filter any column...", label_visibility="collapsed")
    with col_download:
        csv = display_df.to_csv(index=False).encode("utf-8")
        st.download_button("⬇️ Download CSV", csv, "dyeing_data.csv", "text/csv", use_container_width=True)
    if search:
        mask = display_df.apply(lambda col: col.astype(str).str.contains(search, case=False, na=False)).any(axis=1)
        display_df = display_df[mask]
    st.markdown(
        f"<div style='color:#6b7280;font-size:11px;margin-bottom:6px;'>"
        f"Showing <b>{len(display_df):,}</b> rows · "
        f"MTRS: <b style='color:#d97706'>{fmt_in(display_df['MTRS'].sum())}</b> · "
        f"Weight: <b style='color:#3b82f6'>{fmt_in(display_df['Weight'].sum())}</b>"
        f"</div>", unsafe_allow_html=True
    )
    st.dataframe(display_df, use_container_width=True, hide_index=True, height=400,
        column_config={
            "Production Date": st.column_config.TextColumn("📅 Date",    width="medium"),
            "Party Name":      st.column_config.TextColumn("🏭 Party",   width="medium"),
            "QUALITY":         st.column_config.TextColumn("🧵 Quality", width="medium"),
            "SHADE":           st.column_config.TextColumn("🎨 Shade",   width="medium"),
            "MTRS":            st.column_config.NumberColumn("📏 Metres", format="%d", width="small"),
            "Weight":          st.column_config.NumberColumn("⚖️ Weight", format="%d", width="small"),
            "LOT NO.":         st.column_config.TextColumn("Lot No.",    width="small"),
            "MASTER NAME":     st.column_config.TextColumn("👤 Master",  width="medium"),
        })
    agg1, agg2, agg3, agg4 = st.columns(4)
    agg1.metric("Sum MTRS",   fmt_in(display_df['MTRS'].sum()))
    agg2.metric("Avg MTRS",   fmt_in(int(display_df['MTRS'].mean())))
    agg3.metric("Sum Weight", fmt_in(display_df['Weight'].sum()))
    agg4.metric("Avg Weight", fmt_in(int(display_df['Weight'].mean())))

# ─────────────────────────────────────────────
# AUTO REFRESH
# ─────────────────────────────────────────────
st.markdown(f"<script>setTimeout(function(){{window.location.reload();}},{AUTO_REFRESH_SEC*1000});</script>", unsafe_allow_html=True)

# ─────────────────────────────────────────────
# FOOTER
# ─────────────────────────────────────────────
min_d = df['Production Date'].min().strftime('%b %d')     if not df.empty else ''
max_d = df['Production Date'].max().strftime('%b %d, %Y') if not df.empty else ''
st.markdown(f"""
<div style="text-align:center;margin-top:32px;color:#9ca3af;font-size:.8rem;border-top:1px solid #e8ecf2;padding-top:16px;">
  🎨 Dyeing Operations Dashboard · {min_d} – {max_d} ·
  {fmt_in(len(df))} lots · {fmt_in(int(df['MTRS'].sum()))} metres · {fmt_in(int(df['Weight'].sum()))} kg ·
  <span style="color:#16a34a;">● Live</span> · Zoho Creator · Refreshes every {AUTO_REFRESH_SEC}s
</div>
""", unsafe_allow_html=True)