import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import requests
import re
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime

# ─────────────────────────────────────────────
# CONFIG
# ─────────────────────────────────────────────
AUTO_REFRESH_SEC = 60

st.set_page_config(
    page_title="Dyeing Operations Dashboard",
    page_icon="🎨",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# ─────────────────────────────────────────────
# CSS  (original kept verbatim + a few cost classes)
# ─────────────────────────────────────────────
st.markdown("""
<style>
@import url('https://fonts.googleapis.in/css2?family=Inter:wght@300;400;500;600;700;800&family=JetBrains+Mono:wght@400;500&display=swap');

html, body, [class*="css"] { font-family: 'Inter', sans-serif; }
.stApp { background-color: #f5f6fa; }

[data-testid="stSidebar"] { background: #ffffff !important; border-right: 1px solid #e2e6ed !important; box-shadow: 2px 0 12px rgba(0,0,0,0.04); }
[data-testid="stSidebar"] * { color: #374151 !important; }
[data-testid="stSidebar"] h3 { color: #111827 !important; font-weight: 700 !important; }

[data-testid="metric-container"] {
  background: #ffffff; border: 1px solid #e8ecf2; border-radius: 16px;
  padding: 20px 24px !important; box-shadow: 0 1px 4px rgba(0,0,0,0.05);
  transition: box-shadow .2s, border-color .2s;
}
[data-testid="metric-container"]:hover { box-shadow: 0 4px 16px rgba(0,0,0,0.10); border-color: #d97706; }
[data-testid="stMetricValue"] { font-family: 'JetBrains Mono', monospace !important; font-size: 1.75rem !important; font-weight: 700 !important; color: #111827 !important; }
[data-testid="stMetricLabel"] { font-size: 0.72rem !important; color: #6b7280 !important; text-transform: uppercase; letter-spacing: .07em; font-weight: 600 !important; }

.ratio-metric-card { background: linear-gradient(135deg, #fffbeb, #fef3c7); border: 1.5px solid #fde68a; border-radius: 16px; padding: 20px 24px; box-shadow: 0 1px 4px rgba(217,119,6,0.10); transition: box-shadow .2s, border-color .2s; height: 100%; }
.ratio-metric-card:hover { box-shadow: 0 4px 16px rgba(217,119,6,0.18); border-color: #d97706; }
.ratio-metric-label { font-size: 0.72rem; color: #92400e; text-transform: uppercase; letter-spacing: .07em; font-weight: 600; margin-bottom: 6px; }
.ratio-metric-value { font-family: 'JetBrains Mono', monospace; font-size: 1.75rem; font-weight: 700; color: #92400e; line-height: 1.1; }
.ratio-metric-sub { font-size: 0.72rem; color: #b45309; margin-top: 5px; font-weight: 500; }

/* cost variant of the ratio widget (blue/green) */
.cost-metric-card { background: linear-gradient(135deg,#ecfdf5,#d1fae5); border:1.5px solid #a7f3d0; border-radius:16px; padding:20px 24px; box-shadow:0 1px 4px rgba(5,150,105,0.10); height:100%; }
.cost-metric-label { font-size:0.72rem;color:#065f46;text-transform:uppercase;letter-spacing:.07em;font-weight:600;margin-bottom:6px; }
.cost-metric-value { font-family:'JetBrains Mono',monospace;font-size:1.75rem;font-weight:700;color:#065f46;line-height:1.1; }
.cost-metric-sub { font-size:0.72rem;color:#047857;margin-top:5px;font-weight:500; }

.filter-bar-wrap { background:#ffffff;border:1px solid #e8ecf2;border-radius:16px;padding:16px 20px 10px;margin-bottom:20px;box-shadow:0 1px 4px rgba(0,0,0,0.04); }
.filter-bar-title { font-size:0.75rem;font-weight:700;color:#6b7280;text-transform:uppercase;letter-spacing:.08em;margin-bottom:10px; }

[data-testid="stPlotlyChart"] > div { border-radius:16px !important;overflow:hidden;box-shadow:0 1px 4px rgba(0,0,0,0.06); }
.stMultiSelect [data-baseweb="tag"] { background:#fef3c7 !important;color:#92400e !important;border-radius:6px !important; }
[data-testid="stExpander"] { background:#ffffff !important;border:1px solid #e8ecf2 !important;border-radius:14px !important;box-shadow:0 1px 4px rgba(0,0,0,0.04); }

.live-badge { display:inline-flex;align-items:center;gap:6px;background:#f0fdf4;border:1px solid #bbf7d0;border-radius:20px;padding:5px 12px;font-size:12px;color:#15803d;font-weight:500; }
.live-dot { width:7px;height:7px;border-radius:50%;background:#22c55e;animation:pulse 2s infinite; }
@keyframes pulse { 0%,100%{opacity:1}50%{opacity:.3} }

.sum-table { width:100%;border-collapse:collapse;font-family:'Inter',sans-serif;font-size:13px;background:#ffffff;border-radius:12px;overflow:hidden; }
.sum-table th { background:#f3f4f6;color:#6b7280;text-transform:uppercase;font-size:11px;letter-spacing:.06em;padding:11px 16px;border-bottom:1px solid #e5e7eb;text-align:left;font-weight:600; }
.sum-table td { padding:10px 16px;color:#1f2937;border-bottom:1px solid #f3f4f6;font-family:'JetBrains Mono',monospace;font-size:12px; }
.sum-table td:first-child { font-family:'Inter',sans-serif;color:#d97706;font-weight:600; }
.sum-table tr:hover td { background:#fafafa; }

.section-header { background:linear-gradient(135deg,#1e3a5f,#2d5f8a);color:#fff;border-radius:14px;padding:14px 22px;margin:24px 0 16px;display:flex;align-items:center;gap:12px;font-size:1rem;font-weight:700;letter-spacing:-.2px; }

.insight-card { background:#ffffff;border:1px solid #e8ecf2;border-radius:14px;padding:14px 18px;margin-bottom:10px;box-shadow:0 1px 4px rgba(0,0,0,0.05);display:flex;align-items:flex-start;gap:12px;font-size:13px;color:#374151; }
.insight-icon { font-size:20px;flex-shrink:0;margin-top:1px; }
.insight-text strong { color:#111827; }
.insight-card.warn  { border-left:4px solid #f59e0b;background:#fffbeb; }
.insight-card.risk  { border-left:4px solid #ef4444;background:#fef2f2; }
.insight-card.good  { border-left:4px solid #10b981;background:#f0fdf4; }
.insight-card.info  { border-left:4px solid #3b82f6;background:#eff6ff; }

.leaderboard-table { width:100%;border-collapse:collapse;font-family:'Inter',sans-serif;font-size:12px;background:#ffffff;border-radius:12px;overflow:hidden; }
.leaderboard-table th { background:#1e3a5f;color:#ffffff;padding:9px 14px;text-align:left;font-size:11px;letter-spacing:.05em;font-weight:600; }
.leaderboard-table td { padding:9px 14px;color:#1f2937;border-bottom:1px solid #f3f4f6;font-family:'JetBrains Mono',monospace;font-size:11px; }
.leaderboard-table td:first-child { font-family:'Inter',sans-serif;font-weight:700;color:#d97706;text-align:center; }
.leaderboard-table td:nth-child(2) { font-family:'Inter',sans-serif;color:#111827;font-weight:600; }
.leaderboard-table tr:hover td { background:#fef3c7; }

.mom-card { background:#ffffff;border:1px solid #e8ecf2;border-radius:14px;padding:18px 20px;text-align:center;box-shadow:0 1px 4px rgba(0,0,0,0.05); }
.mom-card .val { font-family:'JetBrains Mono',monospace;font-size:1.6rem;font-weight:700;color:#111827; }
.mom-card .lbl { font-size:11px;color:#6b7280;text-transform:uppercase;letter-spacing:.07em;margin-top:4px;font-weight:600; }
.mom-card .delta-pos { color:#10b981;font-size:13px;font-weight:600;margin-top:4px; }
.mom-card .delta-neg { color:#ef4444;font-size:13px;font-weight:600;margin-top:4px; }
.mom-card .delta-neu { color:#6b7280;font-size:13px;font-weight:600;margin-top:4px; }

.day-header { background:linear-gradient(135deg,#1e3a5f,#2d5f8a);color:#fff;border-radius:14px;padding:16px 24px;margin-bottom:16px;display:flex;align-items:center;justify-content:space-between; }

.prod-sheet-table { width:100%;border-collapse:collapse;font-family:'Inter',sans-serif;font-size:12px; }
.prod-sheet-table th { background:#1e3a5f;color:#ffffff;padding:8px 10px;text-align:center;font-size:11px;letter-spacing:.04em;border:1px solid #2d4f7a; }
.prod-sheet-table td { padding:7px 10px;border:1px solid #e5e7eb;color:#1f2937;text-align:center;font-family:'JetBrains Mono',monospace;font-size:11px; }
.prod-sheet-table tr:nth-child(even) td { background:#f8faff; }
.prod-sheet-table tr:hover td { background:#fef3c7; }
.prod-sheet-total td { background:#1e3a5f !important;color:#ffffff !important;font-weight:700; }

.stButton > button { border-radius:10px !important;font-weight:600 !important;font-size:0.85rem !important;transition:all .15s !important; }
.chart-card { background:#ffffff;border:1px solid #e8ecf2;border-radius:16px;padding:4px;box-shadow:0 1px 4px rgba(0,0,0,0.05);margin-bottom:4px; }

.section-divider-label { display:flex;align-items:center;gap:12px;margin:28px 0 20px; }
.section-divider-label span { font-size:1.05rem;font-weight:800;color:#111827;letter-spacing:-.3px;white-space:nowrap; }
.section-divider-label hr { flex:1;border:none;border-top:2px solid #e8ecf2;margin:0; }

hr { border-color:#e8ecf2 !important; }
h2, h3 { color:#111827 !important;font-weight:700 !important; }
</style>
""", unsafe_allow_html=True)

# ─────────────────────────────────────────────
# HELPERS
# ─────────────────────────────────────────────
def fmt_in(n):
    try:
        n = int(n)
        s = str(abs(n))
        sign = "-" if n < 0 else ""
        if len(s) <= 3:
            return sign + s
        last3 = s[-3:]
        rest  = s[:-3]
        groups = []
        while len(rest) > 2:
            groups.append(rest[-2:]); rest = rest[:-2]
        if rest:
            groups.append(rest)
        return sign + ",".join(reversed(groups)) + "," + last3
    except:
        return str(n)

def fmt_cur(n):
    try:
        return "₹" + fmt_in(int(round(float(n))))
    except:
        return "₹0"

PLOTLY_CFG = dict(
    scrollZoom=True, displayModeBar=True,
    modeBarButtonsToRemove=["select2d", "lasso2d", "autoScale2d"],
    modeBarButtonsToAdd=["pan2d"], displaylogo=False, dragmode="pan",
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
    fig.update_layout(**PLOTLY_LAYOUT,
        title=dict(text=title, font=dict(size=14, color="#111827"), x=0),
        height=height, showlegend=show_legend)
    fig.update_xaxes(showgrid=True, gridwidth=1)
    fig.update_yaxes(showgrid=True, gridwidth=1)
    return fig

def pc(fig, **kwargs):
    st.plotly_chart(fig, use_container_width=True, config=PLOTLY_CFG, **kwargs)

def parse_dates(series):
    formats = ["%d-%b-%Y","%d %B %Y","%d-%m-%Y","%Y-%m-%d","%m/%d/%Y","%d/%m/%Y","%d %b %Y","%d/%b/%Y","%d-%b-%y"]
    for fmt in formats:
        parsed = pd.to_datetime(series, format=fmt, errors="coerce")
        if parsed.notna().sum() > len(series) * 0.5:
            mask = parsed.isna()
            if mask.any():
                parsed[mask] = pd.to_datetime(series[mask], errors="coerce")
            return parsed
    return pd.to_datetime(series, errors="coerce")

def section_header(icon, title, subtitle=""):
    sub_html = f"<div style='font-size:.78rem;opacity:.75;margin-top:3px;font-weight:400;'>{subtitle}</div>" if subtitle else ""
    st.markdown(f"""<div class="section-header"><div style="font-size:22px;">{icon}</div>
      <div><div>{title}</div>{sub_html}</div></div>""", unsafe_allow_html=True)

def insight_card(text, kind="info", icon=None):
    icons = {"warn": "⚠️", "risk": "🔴", "good": "✅", "info": "💡"}
    ic = icon or icons.get(kind, "💡")
    st.markdown(f"""<div class="insight-card {kind}"><div class="insight-icon">{ic}</div>
      <div class="insight-text">{text}</div></div>""", unsafe_allow_html=True)

def section_divider(label):
    st.markdown(f"""<div class="section-divider-label"><span>{label}</span><hr/></div>""", unsafe_allow_html=True)

def ratio_widget(ratio_val):
    st.markdown(f"""<div class="ratio-metric-card">
      <div class="ratio-metric-label">📐 Mtr ÷ KG Ratio</div>
      <div class="ratio-metric-value">{ratio_val}x</div>
      <div class="ratio-metric-sub">Every 1 kg = {ratio_val} metres</div></div>""", unsafe_allow_html=True)

def cost_widget(value, label, sub):
    st.markdown(f"""<div class="cost-metric-card">
      <div class="cost-metric-label">{label}</div>
      <div class="cost-metric-value">{value}</div>
      <div class="cost-metric-sub">{sub}</div></div>""", unsafe_allow_html=True)

# ─────────────────────────────────────────────
# ZOHO CREATOR — TOKEN & DATA
# ─────────────────────────────────────────────
def get_access_token():
    cfg = st.secrets["zoho_creator"]
    resp = requests.post(
        "https://accounts.zoho.in/oauth/v2/token",
        params={
            "refresh_token": cfg["refresh_token"],
            "client_id":     cfg["client_id"],
            "client_secret": cfg["client_secret"],
            "grant_type":    "refresh_token",
        }, timeout=15,
    )
    resp.raise_for_status()
    data = resp.json()
    if "access_token" not in data:
        raise RuntimeError(f"Zoho token error: {data}")
    return data["access_token"]


def dv(val):
    """Extract a Zoho display value (handles lookup/dropdown dict shapes)."""
    if isinstance(val, dict):
        out = (val.get("display_value") or val.get("display_Value")
               or val.get("value") or val.get("zc_display_value") or "")
        if isinstance(out, dict):           # zc_display_value can itself be a dict
            return " ".join(str(x) for x in out.values())
        return out
    return val


def _to_num(x):
    try:
        return float(re.sub(r"[^0-9.\-]", "", str(x)) or 0)
    except Exception:
        return 0.0


def _parse_delimited_subrow(text):
    """Parse a Zoho sub-form display string into clean fields.
    Layout (validated against live data, Cost = Qty_kg × Rate holds for every row):
        Chemical: Name, Cost, Quantity_g, Percentage, Rate_per_Kg
        Dye:      Name, Cost, Percentage, Quantity_g, Rate_per_Kg
    Cost is always first number, Rate always last; the two middles are Qty & % in
    some order, disambiguated by which one reproduces Cost = (Qty/1000) × Rate."""
    parts = [p.strip() for p in str(text).split(",")]
    if len(parts) < 5:
        return None
    name = ", ".join(parts[:-4]).strip()
    nums = [_to_num(p) for p in parts[-4:]]
    cost, rate = nums[0], nums[3]
    m1, m2 = nums[1], nums[2]
    if rate > 0:
        qty, pct = (m1, m2) if abs((m1/1000)*rate - cost) <= abs((m2/1000)*rate - cost) else (m2, m1)
    else:
        qty, pct = (m1, m2) if m1 >= m2 else (m2, m1)
    return {"Item": name or "Unknown", "Cost": cost, "Quantity_g": qty,
            "Rate_per_Kg": rate, "Percentage": pct}


def _subrow_from_item(item):
    """Build one clean sub-form row from any Zoho shape (delimited display_value,
    zc_display_value key-value map, or fully expanded field dict)."""
    if not isinstance(item, dict):
        if isinstance(item, str):
            return _parse_delimited_subrow(item)
        return None
    # 1) collapsed display_value carrying comma-delimited data
    disp = item.get("display_value")
    if isinstance(disp, str) and disp.count(",") >= 4:
        parsed = _parse_delimited_subrow(disp)
        if parsed:
            return parsed
    # 2) expanded fields (zc_display_value map or direct keys)
    flat = {}
    for k, v in item.items():
        if k == "zc_display_value" and isinstance(v, dict):
            for kk, vv in v.items():
                flat[str(kk).split(".")[-1].lower()] = dv(vv)
        elif k in ("display_value", "zc_display_value", "ID", "id"):
            continue
        else:
            flat[str(k).split(".")[-1].lower()] = dv(v)
    if not flat:
        return None
    row = {"Item": None, "Quantity_g": 0, "Rate_per_Kg": 0, "Cost": 0, "Percentage": 0}
    leftover = []
    for k, val in flat.items():
        if "rate" in k:
            row["Rate_per_Kg"] = _to_num(val)
        elif "percent" in k or k.endswith("%"):
            row["Percentage"] = _to_num(val)
        elif "cost" in k or "amount" in k:
            row["Cost"] = _to_num(val)
        elif "quant" in k or "gram" in k or "qty" in k:
            row["Quantity_g"] = _to_num(val)
        elif "chemical" in k or "dye" in k or k in ("name", "item"):
            row["Item"] = val
        else:
            leftover.append(val)
    if not row["Item"] and leftover:
        row["Item"] = leftover[0]
    row["Item"] = row["Item"] or "Unknown"
    return row


def _collect_subform(lst, fieldname, rid, lot, chem_rows, dye_rows):
    """Classify a sub-form by its FIELD NAME (chem vs dye) and append one row per line-item.
    The line-item text doesn't contain the words chemical/dye, so the column name is the
    only reliable signal."""
    fn = str(fieldname).lower()
    if "dye" in fn:
        target = dye_rows
    elif "chem" in fn:
        target = chem_rows
    else:
        return
    for it in lst:
        r = _subrow_from_item(it)
        if r and r.get("Item") not in (None, "", "Unknown") or (r and (r["Cost"] or r["Quantity_g"])):
            r["_parent"] = rid
            r["LOT NO."] = lot
            target.append(r)


def _explode_record(rec, chem_rows, dye_rows):
    """Pull every sub-form list out of a record (a main row or a lines-report row)."""
    rid = rec.get("ID") or rec.get("id")
    lot = (dv(rec.get("LOT_NO")) or dv(rec.get("Lot_No")) or dv(rec.get("LOT NO.")) or "")
    found = False
    for k, v in rec.items():
        if isinstance(v, list) and v:
            _collect_subform(v, k, rid, lot, chem_rows, dye_rows)
            found = True
    return found


def _fetch_record_detail(base_url, headers, rid):
    try:
        resp = requests.get(f"{base_url}/{rid}", headers=headers,
                            params={"field_config": "all"}, timeout=20)
        if resp.status_code == 200:
            return resp.json().get("data", {})
    except Exception:
        pass
    return {}


@st.cache_data(ttl=900, show_spinner="Loading recipe line-items…")
def _load_lines_report(report_name):
    """Fetch a dedicated sub-form report (one row per parent lot, with the chemical & dye
    sub-form columns) and explode it into flat chem / dye tables.
    Returns (chem_rows, dye_rows, ldiag) — ldiag surfaces what was seen for debugging."""
    cfg   = st.secrets["zoho_creator"]
    owner = cfg["account_owner"]; app = cfg["app_name"]
    token = get_access_token()
    base_url = f"https://creator.zoho.in/api/v2/{owner}/{app}/report/{report_name}"
    headers  = {"Authorization": f"Zoho-oauthtoken {token}"}
    chem_rows, dye_rows = [], []
    ldiag = {"report": report_name, "error": None, "records": 0,
             "list_fields": {}, "all_fields": []}
    start = 0; limit = 200
    while True:
        try:
            resp = requests.get(base_url, headers=headers,
                                params={"from": start, "limit": limit, "field_config": "all"}, timeout=25)
            resp.raise_for_status()
        except Exception as e:
            ldiag["error"] = str(e)
            break
        recs = resp.json().get("data", [])
        if not recs:
            break
        if not ldiag["all_fields"]:                     # capture shape from first record
            ldiag["all_fields"] = list(recs[0].keys())
            for k, v in recs[0].items():
                if isinstance(v, list):
                    ldiag["list_fields"][k] = v[0] if v else None
        for rec in recs:
            _explode_record(rec, chem_rows, dye_rows)
        ldiag["records"] += len(recs)
        if len(recs) < limit:
            break
        start += limit
    return chem_rows, dye_rows, ldiag



@st.cache_data(ttl=900, show_spinner="Loading recipe line-items (per-record — set 'lines_report' in secrets to make this instant)…")
def _load_subform_details(record_ids, detail_cap=1500):
    """Fallback when no dedicated lines-report is configured: pull sub-forms per record
    via detail fetch, run in parallel. Probes the first record; only fetches the rest if
    detail carries sub-forms. Cached 15 min so the 60s auto-refresh doesn't re-hit the API."""
    cfg    = st.secrets["zoho_creator"]
    owner  = cfg["account_owner"]; app = cfg["app_name"]; report = cfg["report_name"]
    token  = get_access_token()
    base_url = f"https://creator.zoho.in/api/v2/{owner}/{app}/report/{report}"
    headers  = {"Authorization": f"Zoho-oauthtoken {token}"}

    chem_rows, dye_rows = [], []
    if not record_ids:
        return chem_rows, dye_rows
    probe = _fetch_record_detail(base_url, headers, record_ids[0])
    has_sub = any(isinstance(v, list) and v for v in probe.values())
    if not has_sub:
        return chem_rows, dye_rows

    def _work(rid):
        detail = _fetch_record_detail(base_url, headers, rid)
        detail.setdefault("ID", rid)
        c, y = [], []
        _explode_record(detail, c, y)
        return c, y

    ids = list(record_ids[:detail_cap])
    workers = int(cfg.get("detail_fetch_workers", 16))
    with ThreadPoolExecutor(max_workers=max(1, workers)) as ex:
        for c, y in ex.map(_work, ids):
            chem_rows.extend(c); dye_rows.extend(y)
    return chem_rows, dye_rows


@st.cache_data(ttl=AUTO_REFRESH_SEC, show_spinner="Loading production data…")
def load_data():
    cfg          = st.secrets["zoho_creator"]
    owner        = cfg["account_owner"]      # e.g. fibernomad
    app          = cfg["app_name"]           # e.g. data-analytics
    report       = cfg["report_name"]        # e.g. Production_Entry_Form_Report
    access_token = get_access_token()

    base_url = f"https://creator.zoho.in/api/v2/{owner}/{app}/report/{report}"
    headers  = {"Authorization": f"Zoho-oauthtoken {access_token}"}
    # field_config=all returns detail-layout fields (needed so sub-forms aren't collapsed)
    detail_cap = int(cfg.get("detail_fetch_cap", 1500))

    all_records = []
    start_index = 0
    limit       = 200
    while True:
        resp = requests.get(base_url, headers=headers,
                            params={"from": start_index, "limit": limit, "field_config": "all"}, timeout=20)
        resp.raise_for_status()
        records = resp.json().get("data", [])
        if not records:
            break
        all_records.extend(records)
        if len(records) < limit:
            break
        start_index += limit

    if not all_records:
        return pd.DataFrame(), pd.DataFrame(), pd.DataFrame(), datetime.now(), 0, {}

    # ── lightweight field snapshot (kept tiny; only surfaced when sub-forms fail) ──
    diag = {"columns": list(all_records[0].keys()) if all_records else [],
            "main_list_fields": {}, "subform_path": "none", "lines": {}}
    for k, v in all_records[0].items():
        if isinstance(v, list):
            diag["main_list_fields"][k] = (len(v), v[0] if v else None)

    # ── split main fields from sub-forms; explode any inline sub-forms ──
    main_rows, chem_rows, dye_rows = [], [], []
    for rec in all_records:
        rid  = rec.get("ID") or rec.get("id") or len(main_rows)
        main = {"_id": rid}
        for k, v in rec.items():
            if isinstance(v, list):
                continue
            main[k] = dv(v)
        _explode_record(rec, chem_rows, dye_rows)
        main_rows.append(main)
    if chem_rows or dye_rows:
        diag["subform_path"] = "inline (production report)"

    # ── line-items aren't in the production report → dedicated lines-report (preferred)
    #    or per-record detail fetch (fallback) ──
    lines_report = cfg.get("lines_report") or cfg.get("subform_report")
    if not (chem_rows or dye_rows):
        if lines_report:
            d_chem, d_dye, ldiag = _load_lines_report(lines_report)
            diag["lines"] = ldiag
            diag["subform_path"] = f"lines report '{lines_report}'"
        else:
            record_ids = [m["_id"] for m in main_rows if m.get("_id") is not None]
            d_chem, d_dye = _load_subform_details(tuple(record_ids), detail_cap)
            diag["subform_path"] = "per-record detail fetch (slow — set 'lines_report')"
        chem_rows.extend(d_chem); dye_rows.extend(d_dye)

    df      = pd.DataFrame(main_rows)
    df_chem = pd.DataFrame(chem_rows)
    df_dye  = pd.DataFrame(dye_rows)

    # ── main column normalisation (clean names now, but stay tolerant) ──
    col_map = {
        "Production_Date": "Production Date", "Production Date": "Production Date",
        "Party_Name": "Party Name", "Party Name": "Party Name",
        "QUALITY": "QUALITY", "Quality": "QUALITY",
        "SHADE": "SHADE", "Shade": "SHADE",
        "SIZE": "SIZE", "Size": "SIZE",
        "MTRS": "MTRS", "Mtrs": "MTRS",
        "Weight": "Weight", "WEIGHT": "Weight",
        "LOT_NO": "LOT NO.", "Lot_No": "LOT NO.", "Lot No.": "LOT NO.", "LOT NO.": "LOT NO.",
        "MASTER_NAME": "MASTER NAME", "Master_Name": "MASTER NAME", "Masrer_Name": "MASTER NAME",
        "Master Name": "MASTER NAME", "Masrer Name": "MASTER NAME", "MASTER NAME": "MASTER NAME",
        "M_No": "M.No.", "M_NO": "M.No.", "Machine_No": "M.No.", "M.No.": "M.No.", "M_No_": "M.No.",
        "Business_Type": "Business Type", "Business Type": "Business Type",
        "Total_Chemical_Cost": "Total Chemical Cost", "Total Chemical Cost": "Total Chemical Cost",
        "Total_Dye_Cost": "Total Dye Cost", "Total Dye Cost": "Total Dye Cost",
        "Total_Chemical_Percentage": "Total Chemical %", "Total Chemical Percentage": "Total Chemical %",
        "Total_Dye_Percentage": "Total Dye %", "Total Dye Percentage": "Total Dye %",
        "Total_Cost": "Total Cost", "Total Cost": "Total Cost",
        "Total_Cost_Amount": "Total Cost Amount", "Total Cost Amount": "Total Cost Amount",
        "Last_Updated": "Last Updated", "Last Updated": "Last Updated",
    }
    df.rename(columns={k: v for k, v in col_map.items() if k in df.columns}, inplace=True)

    # tolerant pass: catch Zoho variants like collision-suffixed names (Total_Chemical_Cost1),
    # case/separator differences, etc. Normalise → strip non-alphanumerics → strip trailing digits.
    def _norm(s):
        return re.sub(r"\d+$", "", re.sub(r"[^a-z0-9]", "", str(s).lower()))
    canon = {
        "productiondate": "Production Date", "partyname": "Party Name", "quality": "QUALITY",
        "shade": "SHADE", "size": "SIZE", "mtrs": "MTRS", "weight": "Weight", "lotno": "LOT NO.",
        "mastername": "MASTER NAME", "mno": "M.No.", "machineno": "M.No.", "businesstype": "Business Type",
        "totalchemicalcost": "Total Chemical Cost", "totaldyecost": "Total Dye Cost",
        "totalchemicalpercentage": "Total Chemical %", "totaldyepercentage": "Total Dye %",
        "totalcost": "Total Cost", "totalcostamount": "Total Cost Amount", "lastupdated": "Last Updated",
    }
    for col in list(df.columns):
        if col in canon.values() or "." in str(col):   # already clean, or lookup-metadata like Shade.Added_Time
            continue
        target = canon.get(_norm(col))
        if target and target not in df.columns:
            df.rename(columns={col: target}, inplace=True)

    # numeric coercion — main
    for c in ["MTRS", "Weight", "Total Cost", "Total Cost Amount", "Total Chemical Cost", "Total Dye Cost",
              "Total Chemical %", "Total Dye %"]:
        if c in df.columns:
            df[c] = pd.to_numeric(df[c], errors="coerce").fillna(0)
        else:
            df[c] = 0.0
    # derive Total Cost if missing
    if df["Total Cost"].sum() == 0 and (df["Total Chemical Cost"].sum() or df["Total Dye Cost"].sum()):
        df["Total Cost"] = df["Total Chemical Cost"] + df["Total Dye Cost"]

    # dates
    if "Production Date" in df.columns:
        df["Production Date"] = parse_dates(df["Production Date"].astype(str))
    else:
        date_cols = [c for c in df.columns if "date" in c.lower()]
        if date_cols:
            df.rename(columns={date_cols[0]: "Production Date"}, inplace=True)
            df["Production Date"] = parse_dates(df["Production Date"].astype(str))
        else:
            raise KeyError(f"'Production Date' not found. Columns: {list(df.columns)}")

    # categoricals
    for col in ["Party Name", "QUALITY", "SHADE", "MASTER NAME", "Business Type", "M.No."]:
        if col in df.columns:
            df[col] = df[col].fillna("Unknown").astype(str).str.strip()
            df[col] = df[col].replace({"": "Unknown", "None": "Unknown", "nan": "Unknown"})
        else:
            df[col] = "Unknown"

    failed = df["Production Date"].isna().sum()
    df = df.dropna(subset=["Production Date"])
    df = df[df["Party Name"].str.strip().ne("")]

    # ── sub-form numeric cleanup ──
    for sub in (df_chem, df_dye):
        if not sub.empty:
            for c in ["Quantity_g", "Rate_per_Kg", "Cost", "Percentage"]:
                if c in sub.columns:
                    sub[c] = pd.to_numeric(sub[c], errors="coerce").fillna(0)
            sub["Item"] = sub.get("Item", "Unknown")
            sub["Item"] = sub["Item"].fillna("Unknown").astype(str).str.strip().replace(
                {"": "Unknown", "None": "Unknown", "nan": "Unknown"})

    # attach key dimensions to sub-forms for filtering / grouping
    if not df.empty:
        id_set = set(df["_id"])
        lot_to_id = {}
        if "LOT NO." in df.columns:
            lot_to_id = {str(l).strip(): i for i, l in zip(df["_id"], df["LOT NO."])
                         if str(l).strip() not in ("", "nan", "Unknown", "None")}
        for sub in (df_chem, df_dye):
            if sub.empty or "_parent" not in sub.columns:
                continue
            match = sub["_parent"].isin(id_set).mean()
            if match < 0.5 and lot_to_id and "LOT NO." in sub.columns:
                remapped = sub["LOT NO."].astype(str).str.strip().map(lot_to_id)
                sub["_parent"] = remapped.fillna(sub["_parent"])

        dims = df[["_id", "Production Date", "Party Name", "QUALITY", "SHADE",
                   "MASTER NAME", "Business Type", "Weight"]].copy()
        if not df_chem.empty:
            df_chem = df_chem.merge(dims, left_on="_parent", right_on="_id", how="left")
        if not df_dye.empty:
            df_dye = df_dye.merge(dims, left_on="_parent", right_on="_id", how="left")

    return df, df_chem, df_dye, datetime.now(), failed, diag


def subset_sub(parent_df, sub_df):
    """Filter a sub-form frame down to the parent rows currently in scope."""
    if sub_df is None or sub_df.empty or "_id" not in parent_df.columns:
        return pd.DataFrame()
    return sub_df[sub_df["_parent"].isin(set(parent_df["_id"]))].copy()


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
        <div style="font-size:.82rem;color:#9ca3af;margin-top:2px;">Live · Zoho Creator · Production + Costing</div>
      </div>
    </div>""", unsafe_allow_html=True)
with hcol2:
    st.markdown("<div style='padding-top:18px;'></div>", unsafe_allow_html=True)
    if st.button("🔄 Refresh", use_container_width=True, type="primary"):
        st.cache_data.clear(); st.rerun()

# ─────────────────────────────────────────────
# LOAD DATA
# ─────────────────────────────────────────────
try:
    raw, raw_chem, raw_dye, fetched_at, date_parse_fails, diag = load_data()
    fetch_error = None
except Exception as e:
    fetch_error = str(e)
    raw = pd.DataFrame(); raw_chem = pd.DataFrame(); raw_dye = pd.DataFrame()
    fetched_at = None; date_parse_fails = 0; diag = {}

if fetch_error:
    st.error(f"❌ Could not connect to Zoho Creator: `{fetch_error}`")
    st.info("""
**Setup checklist:**
1. Add credentials to `.streamlit/secrets.toml` under `[zoho_creator]`
   (`account_owner`, `app_name`, `report_name`, `client_id`, `client_secret`, `refresh_token`)
2. Make sure the report is not IP-restricted in Zoho Creator
3. Verify field link names match what Zoho returns
4. Redeploy / restart the app
    """)
    st.stop()

if raw.empty:
    st.warning("⚠️ No records found in Zoho Creator report.")
    st.stop()

HAS_COST = raw["Total Cost"].sum() > 0
HAS_DYE  = not raw_dye.empty
HAS_CHEM = not raw_chem.empty

# Auto-diagnostic: shows ONLY when sub-forms didn't load (stakeholders never see it once it works).
# Force-show anytime with  debug = true  under [zoho_creator] in secrets.toml.
_debug_on = bool(st.secrets["zoho_creator"].get("debug"))
if _debug_on or not (HAS_CHEM or HAS_DYE):
    with st.expander("🔧 Recipe line-items — load diagnostic", expanded=not (HAS_CHEM or HAS_DYE)):
        st.markdown(f"**Path used:** {diag.get('subform_path','?')}  ·  "
                    f"**Chemical rows:** {len(raw_chem)}  ·  **Dye rows:** {len(raw_dye)}  ·  "
                    f"**Production rows:** {len(raw)}")
        # production report's list-fields (are sub-forms even present there?)
        mlf = diag.get("main_list_fields", {})
        if mlf:
            st.markdown("**Sub-form arrays in the production report:**")
            for k, (n, sample) in mlf.items():
                st.markdown(f"• `{k}` — {n} row(s)"); st.code(str(sample), language="json")
        else:
            st.write("Production report returns **no sub-form arrays** (expected — use the lines report).")
        # lines report results
        ld = diag.get("lines", {})
        if ld:
            if ld.get("error"):
                st.error(f"Lines report `{ld.get('report')}` error: {ld['error']}  "
                         "→ check the report link name and that it isn't IP-restricted.")
            st.caption(f"Lines report `{ld.get('report')}` — {ld.get('records',0)} records read. "
                       f"Columns: " + ", ".join(f"`{c}`" for c in ld.get("all_fields", [])))
            for k, sample in ld.get("list_fields", {}).items():
                st.markdown(f"• sub-form column `{k}`"); st.code(str(sample), language="json")
        elif diag.get("subform_path","").startswith("per-record"):
            st.warning("Using the slow per-record path. Add  `lines_report = \"Chemical_Lines_Report\"`  "
                       "under `[zoho_creator]` in secrets.toml to make this fast and reliable.")
        if not raw_chem.empty:
            st.markdown("**Chemical sample**"); st.dataframe(raw_chem.head(6), use_container_width=True)
        if not raw_dye.empty:
            st.markdown("**Dye sample**"); st.dataframe(raw_dye.head(6), use_container_width=True)


# ─────────────────────────────────────────────
# TOP FILTER BAR
# ─────────────────────────────────────────────
valid_dates = raw["Production Date"].dropna()
min_date    = valid_dates.min().date()
max_date    = valid_dates.max().date()
all_parties = sorted(raw["Party Name"].dropna().unique())
all_quality = sorted(raw["QUALITY"].dropna().unique())
all_shades  = sorted(raw["SHADE"].dropna().unique())
all_masters = sorted(raw["MASTER NAME"].dropna().unique())
all_biztypes = sorted(raw["Business Type"].dropna().unique())

with st.expander("🔍  Filters — click to expand", expanded=False):
    st.markdown("<div class='filter-bar-title'>Filter the data below</div>", unsafe_allow_html=True)
    fc1, fc2, fc3, fc4, fc5 = st.columns([2, 2, 2, 2, 2])
    with fc1:
        st.markdown("**📅 Date Range**")
        date_range = st.date_input("date_range", value=(min_date, max_date),
            min_value=min_date, max_value=max_date, label_visibility="collapsed")
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

    fb1, fb2, fb3 = st.columns([2, 6, 1])
    with fb1:
        st.markdown("**🏷️ Business Type**")
        sel_biztypes = st.multiselect("Business Type", all_biztypes, default=all_biztypes, label_visibility="collapsed")
    with fb3:
        st.markdown("<div style='height:28px'></div>", unsafe_allow_html=True)
        if st.button("↩️ Reset All", use_container_width=True):
            st.rerun()

# status strip
scol1, scol2 = st.columns([6, 2])
with scol1:
    if date_parse_fails > 0:
        st.warning(f"⚠️ {date_parse_fails} rows had unreadable dates and were skipped.")
with scol2:
    st.markdown(f"""<div style="text-align:right;padding-top:4px;">
      <span class="live-badge"><span class="live-dot"></span> Live &nbsp;·&nbsp; {fetched_at.strftime('%H:%M:%S') if fetched_at else '—'} &nbsp;·&nbsp; {len(raw):,} records</span>
    </div>""", unsafe_allow_html=True)

# ─────────────────────────────────────────────
# APPLY FILTERS
# ─────────────────────────────────────────────
df = raw.copy()
if len(date_range) == 2:
    s, e = pd.Timestamp(date_range[0]), pd.Timestamp(date_range[1])
    df = df[(df["Production Date"] >= s) & (df["Production Date"] <= e)]
if sel_parties:  df = df[df["Party Name"].isin(sel_parties)]
if sel_quality:  df = df[df["QUALITY"].isin(sel_quality)]
if sel_shades:   df = df[df["SHADE"].isin(sel_shades)]
if sel_masters:  df = df[df["MASTER NAME"].isin(sel_masters)]
if sel_biztypes: df = df[df["Business Type"].isin(sel_biztypes)]

if df.empty:
    st.warning("⚠️ No data matches the selected filters.")
    st.stop()

df_chem = subset_sub(df, raw_chem)
df_dye  = subset_sub(df, raw_dye)

# ─────────────────────────────────────────────
# VIEW TOGGLE
# ─────────────────────────────────────────────
st.markdown("<div style='height:4px'></div>", unsafe_allow_html=True)
vt_col1, vt_col2, vt_spacer = st.columns([1, 1, 5])
with vt_col1:
    day_btn = st.button("📅  Day Wise", use_container_width=True,
        type="primary" if st.session_state.get("view", "month") == "day" else "secondary")
with vt_col2:
    month_btn = st.button("📆  Month Wise", use_container_width=True,
        type="primary" if st.session_state.get("view", "month") == "month" else "secondary")
if day_btn:   st.session_state["view"] = "day"
if month_btn: st.session_state["view"] = "month"
current_view = st.session_state.get("view", "month")
st.divider()


# ═══════════════════════════════════════════════════════════
# EXISTING BUSINESS-DECISION SECTIONS  (kept intact)
# ═══════════════════════════════════════════════════════════
def render_machine_utilization(data):
    if "M.No." not in data.columns:
        st.info("ℹ️ Machine Number (M.No.) column not found in data."); return
    section_header("⚙️", "Machine Utilization Analysis", "Performance by machine number")
    mach = data.groupby("M.No.").agg(Lots=("MTRS","count"), Weight=("Weight","sum"), Metres=("MTRS","sum")).reset_index()
    mach["Avg KG/Lot"] = (mach["Weight"] / mach["Lots"]).round(1)
    mach = mach.sort_values("Weight", ascending=False)
    avg_weight = mach["Weight"].mean()
    mach["Status"] = mach["Weight"].apply(lambda w: "🔴 Under" if w < avg_weight*0.7 else ("🟢 Normal" if w <= avg_weight*1.3 else "🟡 Overloaded"))
    k1, k2, k3, k4 = st.columns(4)
    k1.metric("⚙️ Total Machines", len(mach))
    k2.metric("🔴 Underutilized", int((mach["Weight"] < avg_weight*0.7).sum()))
    k3.metric("🟡 Overloaded", int((mach["Weight"] > avg_weight*1.3).sum()))
    k4.metric("📈 Avg KG/Machine", fmt_in(int(avg_weight)))
    c1, c2 = st.columns([2, 3])
    with c1:
        rows = "".join(f"<tr><td>{r['M.No.']}</td><td>{fmt_in(r['Weight'])}</td><td>{int(r['Lots'])}</td><td>{r['Avg KG/Lot']:.1f}</td><td>{r['Status']}</td></tr>" for _, r in mach.iterrows())
        st.markdown(f"""<div style="overflow-x:auto;border-radius:12px;border:1px solid #e5e7eb;"><table class="leaderboard-table"><thead><tr><th>Machine</th><th>Weight (kg)</th><th>Lots</th><th>Avg KG/Lot</th><th>Status</th></tr></thead><tbody>{rows}</tbody></table></div>""", unsafe_allow_html=True)
    with c2:
        colors = ["#ef4444" if s.startswith("🔴") else ("#f59e0b" if s.startswith("🟡") else "#10b981") for s in mach["Status"]]
        fig_m = go.Figure(go.Bar(y=mach["M.No."], x=mach["Weight"], orientation="h",
            marker=dict(color=colors, line=dict(width=0)),
            text=[f"{fmt_in(v)} kg" for v in mach["Weight"]], textposition="outside",
            textfont=dict(color="#374151", size=11, family="JetBrains Mono")))
        fig_m.add_vline(x=avg_weight, line_dash="dot", line_color="#6366f1", line_width=2, annotation_text="Avg", annotation_font_color="#6366f1")
        apply_layout(fig_m, "Machine-wise Production Weight (KG)", height=max(280, len(mach)*40), show_legend=False)
        fig_m.update_yaxes(showgrid=False); pc(fig_m)
    if data["Production Date"].nunique() > 1:
        heat_data = data.groupby(["M.No.", data["Production Date"].dt.strftime("%d %b")])["Weight"].sum().reset_index()
        heat_data.columns = ["Machine", "Date", "Weight"]
        heat_pivot = heat_data.pivot(index="Machine", columns="Date", values="Weight").fillna(0)
        fig_heat = go.Figure(go.Heatmap(z=heat_pivot.values, x=heat_pivot.columns.tolist(), y=heat_pivot.index.tolist(),
            colorscale=[[0,"#f9fafb"],[0.5,"#fef3c7"],[1,"#d97706"]],
            text=[[fmt_in(int(v)) if v>0 else "" for v in row] for row in heat_pivot.values],
            texttemplate="%{text}", textfont=dict(size=9, color="#374151"),
            hovertemplate="Machine: %{y}<br>Date: %{x}<br>Weight: %{z} kg<extra></extra>", showscale=True))
        apply_layout(fig_heat, "Daily Production Heatmap — Machine × Date", height=max(280, len(heat_pivot)*32), show_legend=False)
        fig_heat.update_layout(margin=dict(l=60, r=10, t=40, b=60)); pc(fig_heat)


def render_master_productivity(data):
    section_header("👤", "Master Productivity Dashboard", "Ranked leaderboard with KPIs per master")
    agg = dict(Weight=("Weight","sum"), Metres=("MTRS","sum"), Lots=("MTRS","count"), Days=("Production Date","nunique"))
    if HAS_COST: agg["Cost"] = ("Total Cost", "sum")
    masters = data.groupby("MASTER NAME").agg(**agg).reset_index()
    masters["Avg KG/Lot"]   = (masters["Weight"] / masters["Lots"]).round(1)
    masters["Avg Mtrs/Day"] = (masters["Metres"] / masters["Days"]).round(0).astype(int)
    masters["Share %"]      = (masters["Weight"] / masters["Weight"].sum() * 100).round(1)
    if HAS_COST:
        masters["Cost/KG"] = (masters["Cost"] / masters["Weight"].replace(0, pd.NA)).round(2)
    masters = masters.sort_values("Weight", ascending=False).reset_index(drop=True)
    rank_icons = {0:"🥇",1:"🥈",2:"🥉"}
    cost_h  = "<th>Cost/KG</th>" if HAS_COST else ""
    rows = ""
    for i, r in masters.iterrows():
        badge = rank_icons.get(i, f"#{i+1}")
        cost_c = f"<td>₹{r['Cost/KG']:.2f}</td>" if HAS_COST and pd.notna(r['Cost/KG']) else ("<td>—</td>" if HAS_COST else "")
        rows += (f"<tr><td>{badge}</td><td>{r['MASTER NAME']}</td><td>{fmt_in(r['Weight'])}</td><td>{fmt_in(r['Metres'])}</td>"
                 f"<td>{int(r['Lots'])}</td><td>{r['Avg KG/Lot']:.1f}</td><td>{fmt_in(r['Avg Mtrs/Day'])}</td><td>{r['Share %']:.1f}%</td>{cost_c}</tr>")
    c1, c2 = st.columns([3, 2])
    with c1:
        st.markdown(f"""<div style="overflow-x:auto;border-radius:12px;border:1px solid #e5e7eb;"><table class="leaderboard-table">
          <thead><tr><th>Rank</th><th>Master</th><th>Weight (kg)</th><th>Metres</th><th>Lots</th><th>Avg KG/Lot</th><th>Avg Mtrs/Day</th><th>Share %</th>{cost_h}</tr></thead>
          <tbody>{rows}</tbody></table></div>""", unsafe_allow_html=True)
    with c2:
        fig_mp = go.Figure(go.Bar(x=masters["MASTER NAME"], y=masters["Weight"],
            marker=dict(color=PALETTE[:len(masters)], line=dict(width=0)),
            text=[f"{fmt_in(v)}" for v in masters["Weight"]], textposition="outside",
            textfont=dict(color="#374151", size=11, family="JetBrains Mono")))
        apply_layout(fig_mp, "Master-wise Total Weight (KG)", height=300, show_legend=False)
        fig_mp.update_xaxes(showgrid=False); pc(fig_mp)


def render_small_lot_analysis(data):
    section_header("📦", "Small Lot Analysis", "Lot size distribution and operational cost risk")
    data = data.copy()
    data["Lot Size"] = pd.cut(data["Weight"], bins=[-1, 99.99, 300, float("inf")],
        labels=["Small (<100 kg)", "Medium (100–300 kg)", "Large (>300 kg)"])
    lot_counts = data["Lot Size"].value_counts().reindex(
        ["Small (<100 kg)", "Medium (100–300 kg)", "Large (>300 kg)"]).fillna(0).reset_index()
    lot_counts.columns = ["Category", "Count"]
    lot_counts["Pct"] = (lot_counts["Count"] / lot_counts["Count"].sum() * 100).round(1)
    small_pct = lot_counts.loc[lot_counts["Category"]=="Small (<100 kg)", "Pct"].values
    small_pct = small_pct[0] if len(small_pct) else 0
    c1, c2, c3 = st.columns(3)
    for col, (_, row) in zip([c1, c2, c3], lot_counts.iterrows()):
        col.metric(f"{row['Category']}", f"{int(row['Count'])} lots", delta=f"{row['Pct']:.1f}% of total")
    c_chart, c_warn = st.columns([2, 3])
    with c_chart:
        colors_lot = ["#ef4444", "#f59e0b", "#10b981"]
        fig_lot = go.Figure(go.Pie(labels=lot_counts["Category"], values=lot_counts["Count"], hole=0.55,
            marker=dict(colors=colors_lot, line=dict(color="#ffffff", width=2)),
            textinfo="label+percent", textfont=dict(size=12, color="#374151")))
        apply_layout(fig_lot, "Lot Size Distribution", height=300); pc(fig_lot)
    with c_warn:
        st.markdown("<div style='height:16px'></div>", unsafe_allow_html=True)
        if small_pct >= 40:
            insight_card(f"<strong>{small_pct:.1f}% of all lots are Small (&lt;100 kg).</strong> Critically high — increases setup time, labour cost/kg, and dye wastage. Consider lot consolidation.", kind="risk")
        elif small_pct >= 20:
            insight_card(f"<strong>{small_pct:.1f}% of lots are Small (&lt;100 kg)</strong> — moderate overhead. Review batching opportunities.", kind="warn")
        else:
            insight_card(f"<strong>Small lot percentage is {small_pct:.1f}%</strong> — within acceptable range.", kind="good")
        if HAS_COST:
            small_df = data[data["Lot Size"] == "Small (<100 kg)"]
            big_df   = data[data["Lot Size"] == "Large (>300 kg)"]
            if small_df["Weight"].sum() and big_df["Weight"].sum():
                ckg_small = small_df["Total Cost"].sum() / small_df["Weight"].sum()
                ckg_big   = big_df["Total Cost"].sum() / big_df["Weight"].sum()
                if ckg_big:
                    diff = (ckg_small - ckg_big) / ckg_big * 100
                    insight_card(f"Small lots cost <strong>₹{ckg_small:.2f}/kg</strong> vs <strong>₹{ckg_big:.2f}/kg</strong> for large lots — <strong>{diff:+.0f}%</strong> difference in processing cost per kg.", kind="info")
        party_small = (data[data["Lot Size"]=="Small (<100 kg)"].groupby("Party Name").size().reset_index(name="Small Lots").sort_values("Small Lots", ascending=False).head(5))
        if not party_small.empty:
            insight_card("Top parties by small lot count: <strong>" + ", ".join(f"{r['Party Name']} ({int(r['Small Lots'])})" for _, r in party_small.iterrows()) + "</strong>. Negotiate minimum batch sizes with these parties.", kind="info")


def render_party_dependency(data):
    section_header("🏭", "Party Dependency & Pareto Analysis", "Concentration risk and business dependency")
    party = data.groupby("Party Name").agg(Weight=("Weight","sum"), Lots=("MTRS","count")).reset_index().sort_values("Weight", ascending=False).reset_index(drop=True)
    party["Contribution %"] = (party["Weight"] / party["Weight"].sum() * 100).round(2)
    party["Cumulative %"]   = party["Contribution %"].cumsum().round(2)
    party["Risk"] = party["Contribution %"].apply(lambda p: "🔴 High Risk" if p > 30 else ("🟡 Watch" if p > 15 else "🟢 Safe"))
    c1, c2 = st.columns([3, 2])
    with c1:
        bar_colors = ["#ef4444" if p>30 else ("#f59e0b" if p>15 else "#d97706") for p in party["Contribution %"]]
        fig_pareto = go.Figure()
        fig_pareto.add_trace(go.Bar(x=party["Party Name"], y=party["Weight"], name="Weight (kg)",
            marker=dict(color=bar_colors, line=dict(width=0)),
            text=[f"{fmt_in(v)}" for v in party["Weight"]], textposition="outside",
            textfont=dict(color="#374151", size=10, family="JetBrains Mono"), yaxis="y1"))
        fig_pareto.add_trace(go.Scatter(x=party["Party Name"], y=party["Cumulative %"], name="Cumulative %",
            mode="lines+markers", line=dict(color="#6366f1", width=2.5), marker=dict(size=6, color="#6366f1"), yaxis="y2"))
        fig_pareto.add_hline(y=80, line_dash="dot", line_color="#ef4444", annotation_text="80% line",
            annotation_font_color="#ef4444", yref="y2", line_width=1.5)
        fig_pareto.update_layout(paper_bgcolor="rgba(255,255,255,1)", plot_bgcolor="rgba(248,249,252,1)",
            font=dict(family="Inter", color="#6b7280", size=12), margin=dict(l=10, r=10, t=44, b=10),
            title=dict(text="Pareto Chart — Party-wise Production Weight", font=dict(size=14, color="#111827"), x=0),
            height=360, dragmode="pan",
            yaxis=dict(title="Weight (kg)", gridcolor="#f0f0f0", zerolinecolor="#e5e7eb", linecolor="#e5e7eb"),
            yaxis2=dict(title="Cumulative %", overlaying="y", side="right", range=[0,110], showgrid=False, ticksuffix="%"),
            xaxis=dict(tickangle=-30, showgrid=False, gridcolor="#f0f0f0", zerolinecolor="#e5e7eb", linecolor="#e5e7eb"),
            legend=dict(orientation="h", x=0, y=1.12, bgcolor="rgba(255,255,255,0.9)", bordercolor="#e5e7eb", borderwidth=1, font=dict(color="#374151", size=11)))
        pc(fig_pareto)
    with c2:
        rows = "".join(f"<tr><td>{r['Party Name']}</td><td>{fmt_in(r['Weight'])}</td><td>{int(r['Lots'])}</td><td>{r['Contribution %']:.1f}%</td><td>{r['Cumulative %']:.1f}%</td><td>{r['Risk']}</td></tr>" for _, r in party.iterrows())
        st.markdown(f"""<div style="overflow-x:auto;border-radius:12px;border:1px solid #e5e7eb;max-height:360px;overflow-y:auto;"><table class="leaderboard-table"><thead><tr><th>Party</th><th>Weight</th><th>Lots</th><th>Share%</th><th>Cumul%</th><th>Risk</th></tr></thead><tbody>{rows}</tbody></table></div>""", unsafe_allow_html=True)
    high_risk = party[party["Contribution %"] > 30]
    if not high_risk.empty:
        for _, r in high_risk.iterrows():
            insight_card(f"<strong>{r['Party Name']}</strong> contributes <strong>{r['Contribution %']:.1f}%</strong> of total production weight — <strong>high business dependency risk</strong>.", kind="risk")
    parties_80 = int((party["Cumulative %"] <= 80).sum()) + 1
    insight_card(f"<strong>Top {parties_80} parties</strong> account for 80% of total production. Diversify beyond these to reduce risk.", kind="info")


def render_quality_efficiency(data):
    section_header("📐", "Quality Efficiency Analysis", "Metres per KG ratio by fabric quality")
    qual_eff = data.groupby("QUALITY").agg(Weight=("Weight","sum"), Metres=("MTRS","sum"), Lots=("MTRS","count")).reset_index()
    qual_eff = qual_eff[qual_eff["Weight"] > 0]
    qual_eff["MTRS/KG"] = (qual_eff["Metres"] / qual_eff["Weight"]).round(3)
    qual_eff = qual_eff.sort_values("MTRS/KG", ascending=False)
    avg_ratio = qual_eff["MTRS/KG"].mean()
    qual_eff["Outlier"] = qual_eff["MTRS/KG"].apply(lambda v: "🔴 Low" if v < avg_ratio*0.75 else ("🟡 High" if v > avg_ratio*1.25 else "🟢 Normal"))
    c1, c2 = st.columns([3, 2])
    with c1:
        colors_qe = ["#ef4444" if o.startswith("🔴") else ("#f59e0b" if o.startswith("🟡") else "#10b981") for o in qual_eff["Outlier"]]
        fig_qe = go.Figure(go.Bar(x=qual_eff["QUALITY"], y=qual_eff["MTRS/KG"],
            marker=dict(color=colors_qe, line=dict(width=0)),
            text=[f"{v:.2f}" for v in qual_eff["MTRS/KG"]], textposition="outside",
            textfont=dict(color="#374151", size=10, family="JetBrains Mono")))
        fig_qe.add_hline(y=avg_ratio, line_dash="dot", line_color="#6366f1", line_width=2, annotation_text=f"Avg {avg_ratio:.2f}", annotation_font_color="#6366f1")
        apply_layout(fig_qe, "MTRS per KG by Quality (Efficiency Ratio)", height=340, show_legend=False)
        fig_qe.update_xaxes(tickangle=-30, showgrid=False); pc(fig_qe)
    with c2:
        rows = "".join(f"<tr><td>{r['QUALITY']}</td><td>{fmt_in(r['Weight'])}</td><td>{fmt_in(r['Metres'])}</td><td><strong>{r['MTRS/KG']:.3f}</strong></td><td>{r['Outlier']}</td></tr>" for _, r in qual_eff.iterrows())
        st.markdown(f"""<div style="overflow-x:auto;border-radius:12px;border:1px solid #e5e7eb;max-height:360px;overflow-y:auto;"><table class="leaderboard-table"><thead><tr><th>Quality</th><th>Weight</th><th>Metres</th><th>MTRS/KG</th><th>Status</th></tr></thead><tbody>{rows}</tbody></table></div>""", unsafe_allow_html=True)
    low_eff = qual_eff[qual_eff["Outlier"].str.startswith("🔴")]
    if not low_eff.empty:
        insight_card(f"Qualities <strong>{', '.join(low_eff['QUALITY'])}</strong> have a significantly <strong>low MTRS/KG ratio</strong> — worth investigating for heavy fabrics or data anomalies.", kind="risk")
    high_eff = qual_eff[qual_eff["Outlier"].str.startswith("🟡")]
    if not high_eff.empty:
        insight_card(f"Qualities <strong>{', '.join(high_eff['QUALITY'])}</strong> have a notably <strong>high MTRS/KG ratio</strong> — lightweight fabrics needing careful handling.", kind="info")


def render_mom_comparison(data, sel_month):
    section_header("📅", "Month-over-Month Performance", "Selected month vs previous month")
    data = data.copy()
    data["Month"] = data["Production Date"].dt.to_period("M")
    cur_df  = data[data["Month"] == sel_month]
    prev_m  = sel_month - 1
    prev_df = data[data["Month"] == prev_m]
    if prev_df.empty:
        st.info(f"ℹ️ No data for {prev_m.strftime('%B %Y')} to compare against."); return
    metrics = {"⚖️ Weight (kg)": ("Weight","sum"), "📏 Metres": ("MTRS","sum"), "🧵 Lots": ("MTRS","count")}
    if HAS_COST: metrics["💰 Total Cost"] = ("Total Cost","sum")
    cols = st.columns(len(metrics))
    for col, (label, (field, agg)) in zip(cols, metrics.items()):
        cur_val  = cur_df[field].sum()  if agg=="sum" else len(cur_df)
        prev_val = prev_df[field].sum() if agg=="sum" else len(prev_df)
        delta    = ((cur_val - prev_val) / prev_val * 100) if prev_val else 0
        delta_cls   = "delta-pos" if delta >= 0 else "delta-neg"
        delta_arrow = "▲" if delta > 0 else ("▼" if delta < 0 else "–")
        disp_cur  = fmt_cur(cur_val)  if "Cost" in label else fmt_in(int(cur_val))
        disp_prev = fmt_cur(prev_val) if "Cost" in label else fmt_in(int(prev_val))
        col.markdown(f"""<div class="mom-card"><div class="lbl">{label}</div><div class="val">{disp_cur}</div>
          <div class="{delta_cls}">{delta_arrow} {abs(delta):.1f}% vs {prev_m.strftime('%b %Y')}</div>
          <div style="font-size:11px;color:#9ca3af;margin-top:4px;">Prev: {disp_prev}</div></div>""", unsafe_allow_html=True)
    st.markdown("<div style='height:16px'></div>", unsafe_allow_html=True)
    trend_data = data[data["Month"].isin([prev_m, sel_month])].copy()
    trend_data["Month_str"] = trend_data["Production Date"].dt.strftime("%B %Y")
    daily_trend = trend_data.groupby(["Month_str","Production Date"]).agg(Weight=("Weight","sum"), Metres=("MTRS","sum")).reset_index().sort_values("Production Date")
    daily_trend["Day"] = daily_trend["Production Date"].dt.day
    fig_trend = go.Figure()
    month_colors = {prev_m.strftime("%B %Y"): "#94a3b8", sel_month.strftime("%B %Y"): "#d97706"}
    for mname, grp in daily_trend.groupby("Month_str"):
        fig_trend.add_trace(go.Scatter(x=grp["Day"], y=grp["Weight"], name=mname, mode="lines+markers",
            line=dict(color=month_colors.get(mname, "#d97706"), width=2.5), marker=dict(size=5)))
    apply_layout(fig_trend, "Daily Weight Trend — Current vs Previous Month", height=280)
    fig_trend.update_xaxes(title_text="Day of Month"); fig_trend.update_yaxes(title_text="Weight (kg)"); pc(fig_trend)
    cur_wt, prev_wt = cur_df["Weight"].sum(), prev_df["Weight"].sum()
    if prev_wt:
        d = (cur_wt - prev_wt) / prev_wt * 100
        if d > 5:
            insight_card(f"Production weight <strong>increased by {d:.1f}%</strong> vs {prev_m.strftime('%B %Y')}. Ensure machine and staffing capacity can sustain this.", kind="good")
        elif d < -5:
            insight_card(f"Production weight <strong>declined by {abs(d):.1f}%</strong> vs {prev_m.strftime('%B %Y')}. Investigate order pipeline, machine downtime, or seasonal demand shifts.", kind="risk")
        else:
            insight_card(f"Production weight is <strong>relatively stable</strong> ({d:+.1f}% vs {prev_m.strftime('%B %Y')}). Consistent performance.", kind="info")


# ═══════════════════════════════════════════════════════════
# ADAPTED SECTIONS  (chemical / shade now sub-form sourced)
# ═══════════════════════════════════════════════════════════
def render_chemical_consumption(data, chem):
    section_header("🧪", "Chemical Consumption & Cost", "Itemised chemical usage and spend")
    if chem is None or chem.empty:
        st.info("ℹ️ No chemical sub-form data found for the current selection."); return
    g = chem.groupby("Item").agg(Cost=("Cost","sum"), Qty=("Quantity_g","sum"),
        AvgRate=("Rate_per_Kg","mean"), Uses=("Cost","count")).reset_index().sort_values("Cost", ascending=False)
    total_weight = data["Weight"].sum()
    g["Per KG (g)"] = (g["Qty"] / total_weight).round(2) if total_weight else 0
    c1, c2 = st.columns([2, 3])
    with c1:
        rows = ""
        for i, (_, r) in enumerate(g.iterrows()):
            badge = ["🥇","🥈","🥉"][i] if i < 3 else f"#{i+1}"
            rows += f"<tr><td>{badge}</td><td>{r['Item']}</td><td>{fmt_cur(r['Cost'])}</td><td>{r['Qty']:,.0f}</td><td>₹{r['AvgRate']:.1f}</td></tr>"
        st.markdown(f"""<div style="overflow-x:auto;border-radius:12px;border:1px solid #e5e7eb;max-height:360px;overflow-y:auto;"><table class="leaderboard-table"><thead><tr><th>Rank</th><th>Chemical</th><th>Total Cost</th><th>Qty (g)</th><th>Avg Rate/Kg</th></tr></thead><tbody>{rows}</tbody></table></div>""", unsafe_allow_html=True)
    with c2:
        fig_chem = go.Figure(go.Bar(x=g["Item"].head(15), y=g["Cost"].head(15),
            marker=dict(color=PALETTE[:15], line=dict(width=0)),
            text=[fmt_cur(v) for v in g["Cost"].head(15)], textposition="outside", textfont=dict(color="#374151", size=10)))
        apply_layout(fig_chem, "Top Chemicals by Total Cost", height=320, show_legend=False)
        fig_chem.update_xaxes(tickangle=-30, showgrid=False); pc(fig_chem)
    # Quality × chemical cost heatmap
    if "QUALITY" in chem.columns:
        top_items = g["Item"].head(8).tolist()
        qc = chem[chem["Item"].isin(top_items)].groupby(["QUALITY","Item"])["Cost"].sum().reset_index()
        if not qc.empty:
            piv = qc.pivot(index="QUALITY", columns="Item", values="Cost").fillna(0)
            piv = piv.loc[piv.sum(axis=1).nlargest(15).index]
            fig_hm = go.Figure(go.Heatmap(z=piv.values, x=piv.columns.tolist(), y=piv.index.tolist(),
                colorscale=[[0,"#f9fafb"],[0.5,"#fef3c7"],[1,"#d97706"]],
                text=[[fmt_in(int(v)) for v in row] for row in piv.values], texttemplate="%{text}", textfont=dict(size=9),
                hovertemplate="Quality: %{y}<br>Chemical: %{x}<br>Cost: ₹%{z}<extra></extra>", showscale=True))
            apply_layout(fig_hm, "Top Qualities × Chemical Cost (₹)", height=max(300, len(piv)*28), show_legend=False)
            fig_hm.update_layout(margin=dict(l=100, r=10, t=40, b=60)); pc(fig_hm)
    top = g.iloc[0]
    insight_card(f"<strong>{top['Item']}</strong> is the highest-spend chemical ({fmt_cur(top['Cost'])}, avg ₹{top['AvgRate']:.1f}/kg). Prioritise rate negotiation here.", kind="info")


def render_shade_complexity(data, chem, dye):
    section_header("🎨", "Shade Complexity Analysis", "Cost intensity by shade — pricing signals")
    parts = []
    if chem is not None and not chem.empty and "SHADE" in chem.columns:
        parts.append(chem.groupby("SHADE")["Cost"].sum().rename("Chem Cost"))
    if dye is not None and not dye.empty and "SHADE" in dye.columns:
        parts.append(dye.groupby("SHADE")["Cost"].sum().rename("Dye Cost"))
    if not parts:
        st.info("ℹ️ No chemical/dye sub-form data for shade complexity."); return
    sc = pd.concat(parts, axis=1).fillna(0).reset_index()
    sc["Total Cost"] = sc.drop(columns=["SHADE"]).sum(axis=1)
    wt = data.groupby("SHADE")["Weight"].sum().rename("Weight")
    sc = sc.merge(wt, on="SHADE", how="left")
    sc["Cost/KG"] = (sc["Total Cost"] / sc["Weight"].replace(0, pd.NA)).round(2)
    sc = sc.sort_values("Cost/KG", ascending=False).head(12)
    c1, c2 = st.columns([3, 2])
    with c1:
        fig_sc = go.Figure(go.Bar(y=sc["SHADE"], x=sc["Cost/KG"], orientation="h",
            marker=dict(color=sc["Cost/KG"], colorscale=[[0,"#fef3c7"],[0.5,"#f59e0b"],[1,"#d97706"]], showscale=False, line=dict(width=0)),
            text=[f"₹{v:.2f}" for v in sc["Cost/KG"]], textposition="outside", textfont=dict(color="#374151", size=11, family="JetBrains Mono")))
        apply_layout(fig_sc, "Top Shades by Cost per KG", height=360, show_legend=False)
        fig_sc.update_yaxes(showgrid=False); pc(fig_sc)
    with c2:
        rows = "".join(f"<tr><td>{r['SHADE']}</td><td>{fmt_cur(r.get('Dye Cost',0))}</td><td>{fmt_cur(r.get('Chem Cost',0))}</td><td><strong>₹{r['Cost/KG']:.2f}</strong></td></tr>" for _, r in sc.iterrows())
        st.markdown(f"""<div style="overflow-x:auto;border-radius:12px;border:1px solid #e5e7eb;max-height:360px;overflow-y:auto;"><table class="leaderboard-table"><thead><tr><th>Shade</th><th>Dye Cost</th><th>Chem Cost</th><th>Cost/KG</th></tr></thead><tbody>{rows}</tbody></table></div>""", unsafe_allow_html=True)
    if not sc.empty:
        insight_card(f"Shade <strong>{sc.iloc[0]['SHADE']}</strong> has the highest cost per kg (₹{sc.iloc[0]['Cost/KG']:.2f}) — consider a <strong>premium pricing surcharge</strong>.", kind="warn")


def render_business_insights(data, chem, dye, scope_label=""):
    section_header("💡", "Business Insights Panel", f"Auto-generated insights · {scope_label}")
    insights = []
    party = data.groupby("Party Name")["Weight"].sum(); total_wt = party.sum()
    for pname, wt in party.items():
        pct = wt / total_wt * 100 if total_wt else 0
        if pct > 40:
            insights.append(("risk","🔴", f"<strong>{pname}</strong> contributes <strong>{pct:.1f}%</strong> of production weight — <strong>critically high</strong> dependency risk."))
        elif pct > 30:
            insights.append(("warn","⚠️", f"<strong>{pname}</strong> contributes <strong>{pct:.1f}%</strong> of production. Diversify order intake."))
    if "M.No." in data.columns:
        mach_wt = data.groupby("M.No.")["Weight"].sum(); avg_mwt = mach_wt.mean()
        for mno, wt in mach_wt.items():
            if avg_mwt and wt < avg_mwt*0.6:
                insights.append(("warn","⚙️", f"Machine <strong>{mno}</strong> processed <strong>{(1-wt/avg_mwt)*100:.0f}% less</strong> than average. Check for downtime or underallocation."))
    small_pct = (data["Weight"] < 100).sum() / len(data) * 100 if len(data) else 0
    if small_pct > 30:
        insights.append(("risk","📦", f"Small lots (&lt;100 kg) account for <strong>{small_pct:.1f}%</strong> of all lots — increasing cost per kg."))
    elif small_pct > 15:
        insights.append(("warn","📦", f"Small lots represent <strong>{small_pct:.1f}%</strong> of total lots. Monitor — above 30% is costly."))
    if dye is not None and not dye.empty:
        ds = dye.groupby("SHADE")["Cost"].sum() if "SHADE" in dye.columns else pd.Series(dtype=float)
        if not ds.empty:
            insights.append(("info","🎨", f"Shade <strong>{ds.idxmax()}</strong> carries the highest total dye spend ({fmt_cur(ds.max())}) — verify pricing covers it."))
    if HAS_COST and data["Weight"].sum():
        ckg = data["Total Cost"].sum() / data["Weight"].sum()
        insights.append(("info","💰", f"Blended processing cost is <strong>₹{ckg:.2f}/kg</strong> across {fmt_in(len(data))} lots. Track this against your charge-out rate."))
    master_wt = data.groupby("MASTER NAME")["Weight"].sum()
    if not master_wt.empty:
        tm = master_wt.idxmax()
        insights.append(("good","👤", f"Master <strong>{tm}</strong> supervised the highest production weight (<strong>{fmt_in(int(master_wt[tm]))} kg</strong>). Recognise and retain."))
    working_days = data["Production Date"].nunique()
    total_days = (data["Production Date"].max() - data["Production Date"].min()).days + 1
    if total_days > 0:
        util = working_days / total_days * 100
        if util < 70:
            insights.append(("warn","📅", f"Factory operational for only <strong>{working_days} of {total_days} days</strong> ({util:.0f}% utilization). Review downtime causes."))
    qual_eff = data.groupby("QUALITY").agg(Weight=("Weight","sum"), Metres=("MTRS","sum")).reset_index()
    qual_eff = qual_eff[qual_eff["Weight"] > 0]
    qual_eff["ratio"] = qual_eff["Metres"] / qual_eff["Weight"]
    if not qual_eff.empty:
        low_q = qual_eff[qual_eff["ratio"] < qual_eff["ratio"].mean()*0.6]
        if not low_q.empty:
            insights.append(("info","📐", f"Qualities <strong>{', '.join(low_q['QUALITY'])}</strong> have unusually low MTRS/KG ratios — verify data accuracy or processing parameters."))
    if not insights:
        insights.append(("good","✅", "No major risk signals detected. Operations appear within normal parameters."))
    for kind, icon, text in insights:
        insight_card(text, kind=kind, icon=icon)


# ═══════════════════════════════════════════════════════════
# NEW COST SECTIONS
# ═══════════════════════════════════════════════════════════
def render_cost_overview(data):
    if not HAS_COST:
        st.info("ℹ️ Cost data not available yet — once Total Cost / Dye / Chemical costs flow in, this section activates."); return
    section_header("💰", "Cost Overview", "Total spend, unit economics and dye-vs-chemical split")
    tot_cost = data["Total Cost"].sum()
    dye_cost = data["Total Dye Cost"].sum()
    chem_cost = data["Total Chemical Cost"].sum()
    weight  = data["Weight"].sum(); metres = data["MTRS"].sum()
    ckg = tot_cost / weight if weight else 0
    cmtr = tot_cost / metres if metres else 0
    dye_share = dye_cost / (dye_cost + chem_cost) * 100 if (dye_cost + chem_cost) else 0
    k1, k2, k3, k4, k5, k6 = st.columns(6)
    k1.metric("💰 Total Cost", fmt_cur(tot_cost))
    k2.metric("🧴 Dye Cost", fmt_cur(dye_cost))
    k3.metric("🧪 Chemical Cost", fmt_cur(chem_cost))
    with k4: cost_widget(f"₹{ckg:.2f}", "⚖️ Cost / KG", "blended processing cost")
    with k5: cost_widget(f"₹{cmtr:.2f}", "📏 Cost / Metre", "per running metre")
    with k6: cost_widget(f"{dye_share:.0f}%", "🧴 Dye Share", f"vs {100-dye_share:.0f}% chemical")
    c1, c2 = st.columns([2, 3])
    with c1:
        fig_split = go.Figure(go.Pie(labels=["Dye Cost","Chemical Cost"], values=[dye_cost, chem_cost], hole=0.58,
            marker=dict(colors=["#8b5cf6","#06b6d4"], line=dict(color="#fff", width=2)),
            textinfo="label+percent", textfont=dict(size=12, color="#374151")))
        apply_layout(fig_split, "Cost Split — Dye vs Chemical", height=300); pc(fig_split)
    with c2:
        if data["Production Date"].nunique() > 1:
            daily = data.groupby("Production Date").agg(Cost=("Total Cost","sum"), Weight=("Weight","sum")).reset_index().sort_values("Production Date")
            daily["Cost/KG"] = (daily["Cost"] / daily["Weight"].replace(0, pd.NA)).round(2)
            fig_ck = go.Figure(go.Scatter(x=daily["Production Date"], y=daily["Cost/KG"], mode="lines+markers",
                line=dict(color="#10b981", width=2.5), marker=dict(size=5), fill="tozeroy", fillcolor="rgba(16,185,129,0.08)"))
            avg_ck = (daily["Cost/KG"]).mean()
            fig_ck.add_hline(y=avg_ck, line_dash="dot", line_color="#059669", annotation_text=f"Avg ₹{avg_ck:.2f}", annotation_font_color="#059669")
            apply_layout(fig_ck, "Cost per KG — Daily Trend", height=300, show_legend=False)
            fig_ck.update_yaxes(title_text="₹ / kg"); pc(fig_ck)
        else:
            party_ck = data.groupby("Party Name").agg(Cost=("Total Cost","sum"), Weight=("Weight","sum")).reset_index()
            party_ck["Cost/KG"] = (party_ck["Cost"] / party_ck["Weight"].replace(0, pd.NA)).round(2)
            party_ck = party_ck.sort_values("Cost/KG", ascending=True)
            fig_pk = go.Figure(go.Bar(y=party_ck["Party Name"], x=party_ck["Cost/KG"], orientation="h",
                marker=dict(color="#10b981", line=dict(width=0)),
                text=[f"₹{v:.2f}" for v in party_ck["Cost/KG"]], textposition="outside", textfont=dict(color="#374151", size=10, family="JetBrains Mono")))
            apply_layout(fig_pk, "Cost per KG by Party", height=300, show_legend=False)
            fig_pk.update_yaxes(showgrid=False); pc(fig_pk)
    # cost/kg by party + quality
    c3, c4 = st.columns(2)
    with c3:
        pk = data.groupby("Party Name").agg(Cost=("Total Cost","sum"), Weight=("Weight","sum")).reset_index()
        pk["Cost/KG"] = (pk["Cost"] / pk["Weight"].replace(0, pd.NA)).round(2)
        pk = pk.sort_values("Cost/KG", ascending=False)
        avg_pk = (data["Total Cost"].sum()/data["Weight"].sum()) if data["Weight"].sum() else 0
        colors = ["#ef4444" if v > avg_pk*1.15 else ("#10b981" if v < avg_pk*0.85 else "#f59e0b") for v in pk["Cost/KG"]]
        fig = go.Figure(go.Bar(x=pk["Party Name"], y=pk["Cost/KG"], marker=dict(color=colors, line=dict(width=0)),
            text=[f"₹{v:.1f}" for v in pk["Cost/KG"]], textposition="outside", textfont=dict(color="#374151", size=10, family="JetBrains Mono")))
        fig.add_hline(y=avg_pk, line_dash="dot", line_color="#6366f1", annotation_text=f"Avg ₹{avg_pk:.2f}", annotation_font_color="#6366f1")
        apply_layout(fig, "Cost/KG by Party (red = above average)", height=320, show_legend=False)
        fig.update_xaxes(tickangle=-30, showgrid=False); pc(fig)
    with c4:
        qk = data.groupby("QUALITY").agg(Cost=("Total Cost","sum"), Weight=("Weight","sum")).reset_index()
        qk["Cost/KG"] = (qk["Cost"] / qk["Weight"].replace(0, pd.NA)).round(2)
        qk = qk.sort_values("Cost/KG", ascending=False).head(12)
        fig = go.Figure(go.Bar(x=qk["QUALITY"], y=qk["Cost/KG"],
            marker=dict(color=list(range(len(qk))), colorscale="Tealgrn", showscale=False, line=dict(width=0)),
            text=[f"₹{v:.1f}" for v in qk["Cost/KG"]], textposition="outside", textfont=dict(color="#374151", size=10, family="JetBrains Mono")))
        apply_layout(fig, "Cost/KG by Quality", height=320, show_legend=False)
        fig.update_xaxes(tickangle=-30, showgrid=False); pc(fig)


def render_dye_cost(data, dye):
    section_header("🧴", "Dye Cost Analysis", "Itemised dye spend, rates and Pareto")
    if dye is None or dye.empty:
        st.info("ℹ️ No dye sub-form data found for the current selection."); return
    g = dye.groupby("Item").agg(Cost=("Cost","sum"), Qty=("Quantity_g","sum"),
        AvgRate=("Rate_per_Kg","mean"), Uses=("Cost","count")).reset_index().sort_values("Cost", ascending=False).reset_index(drop=True)
    g["Share %"] = (g["Cost"] / g["Cost"].sum() * 100).round(1)
    g["Cumul %"] = g["Share %"].cumsum().round(1)
    k1, k2, k3, k4 = st.columns(4)
    k1.metric("🧴 Distinct Dyes", len(g))
    k2.metric("💰 Total Dye Spend", fmt_cur(g["Cost"].sum()))
    k3.metric("⚖️ Total Dye Qty", f"{g['Qty'].sum():,.0f} g")
    n80 = int((g["Cumul %"] <= 80).sum()) + 1
    k4.metric("🎯 Dyes = 80% spend", n80)
    c1, c2 = st.columns([3, 2])
    with c1:
        bar_colors = ["#ef4444" if c>80 else ("#f59e0b" if c>50 else "#8b5cf6") for c in g["Cumul %"]]
        fig = go.Figure()
        fig.add_trace(go.Bar(x=g["Item"], y=g["Cost"], name="Dye Cost", marker=dict(color=bar_colors, line=dict(width=0)),
            text=[fmt_cur(v) for v in g["Cost"]], textposition="outside", textfont=dict(color="#374151", size=9, family="JetBrains Mono"), yaxis="y1"))
        fig.add_trace(go.Scatter(x=g["Item"], y=g["Cumul %"], name="Cumulative %", mode="lines+markers",
            line=dict(color="#6366f1", width=2.5), marker=dict(size=6), yaxis="y2"))
        fig.add_hline(y=80, line_dash="dot", line_color="#ef4444", yref="y2", annotation_text="80%", annotation_font_color="#ef4444")
        fig.update_layout(**{k:v for k,v in PLOTLY_LAYOUT.items() if k not in ("yaxis","legend")},
            title=dict(text="Dye Spend Pareto", font=dict(size=14, color="#111827"), x=0), height=360,
            yaxis=dict(title="Cost (₹)", gridcolor="#f0f0f0"),
            yaxis2=dict(title="Cumul %", overlaying="y", side="right", range=[0,110], showgrid=False, ticksuffix="%"),
            legend=dict(orientation="h", x=0, y=1.12))
        fig.update_xaxes(tickangle=-30, showgrid=False); pc(fig)
    with c2:
        rows = ""
        for i, r in g.iterrows():
            badge = ["🥇","🥈","🥉"][i] if i < 3 else f"#{i+1}"
            rows += f"<tr><td>{badge}</td><td>{r['Item']}</td><td>{fmt_cur(r['Cost'])}</td><td>₹{r['AvgRate']:.1f}</td><td>{r['Share %']:.1f}%</td></tr>"
        st.markdown(f"""<div style="overflow-x:auto;border-radius:12px;border:1px solid #e5e7eb;max-height:360px;overflow-y:auto;"><table class="leaderboard-table"><thead><tr><th>Rank</th><th>Dye</th><th>Cost</th><th>Avg Rate/Kg</th><th>Share</th></tr></thead><tbody>{rows}</tbody></table></div>""", unsafe_allow_html=True)
    # dye usage by shade
    if "SHADE" in dye.columns:
        top_dyes = g["Item"].head(8).tolist()
        ds = dye[dye["Item"].isin(top_dyes)].groupby(["SHADE","Item"])["Cost"].sum().reset_index()
        if not ds.empty:
            piv = ds.pivot(index="SHADE", columns="Item", values="Cost").fillna(0)
            piv = piv.loc[piv.sum(axis=1).nlargest(15).index]
            fig_hm = go.Figure(go.Heatmap(z=piv.values, x=piv.columns.tolist(), y=piv.index.tolist(),
                colorscale=[[0,"#faf5ff"],[0.5,"#c4b5fd"],[1,"#7c3aed"]],
                text=[[fmt_in(int(v)) for v in row] for row in piv.values], texttemplate="%{text}", textfont=dict(size=9),
                hovertemplate="Shade: %{y}<br>Dye: %{x}<br>Cost: ₹%{z}<extra></extra>", showscale=True))
            apply_layout(fig_hm, "Top Shades × Dye Cost (₹)", height=max(300, len(piv)*28), show_legend=False)
            fig_hm.update_layout(margin=dict(l=100, r=10, t=40, b=60)); pc(fig_hm)
    top = g.iloc[0]
    insight_card(f"<strong>{top['Item']}</strong> drives {top['Share %']:.1f}% of dye spend ({fmt_cur(top['Cost'])}). A small rate cut here moves the total — prioritise this supplier negotiation.", kind="info")


def render_recipe_consistency(data):
    section_header("🧬", "Recipe Consistency & Waste Signals", "Cost-per-kg variation within the same shade × quality")
    if not HAS_COST:
        st.info("ℹ️ Needs cost data — activates once Total Cost flows in."); return
    d = data[data["Weight"] > 0].copy()
    d["Cost/KG"] = d["Total Cost"] / d["Weight"]
    grp = d.groupby(["SHADE","QUALITY"]).agg(Lots=("Cost/KG","count"), Avg=("Cost/KG","mean"),
        Std=("Cost/KG","std"), Min=("Cost/KG","min"), Max=("Cost/KG","max")).reset_index()
    grp = grp[grp["Lots"] >= 2].copy()
    if grp.empty:
        st.info("ℹ️ Not enough repeated shade × quality combinations in this selection to assess consistency."); return
    grp["CV %"] = (grp["Std"] / grp["Avg"] * 100).round(1)
    grp = grp.sort_values("CV %", ascending=False)
    high = grp[grp["CV %"] > 25]
    k1, k2, k3 = st.columns(3)
    k1.metric("🔁 Repeated combos", len(grp))
    k2.metric("⚠️ High variance (>25%)", len(high))
    k3.metric("📊 Avg variation", f"{grp['CV %'].mean():.1f}%")
    rows = ""
    for _, r in grp.head(20).iterrows():
        flag = "🔴" if r["CV %"] > 25 else ("🟡" if r["CV %"] > 12 else "🟢")
        rows += (f"<tr><td>{r['SHADE']}</td><td>{r['QUALITY']}</td><td>{int(r['Lots'])}</td>"
                 f"<td>₹{r['Avg']:.2f}</td><td>₹{r['Min']:.2f}</td><td>₹{r['Max']:.2f}</td><td>{flag} {r['CV %']:.1f}%</td></tr>")
    st.markdown(f"""<div style="overflow-x:auto;border-radius:12px;border:1px solid #e5e7eb;max-height:380px;overflow-y:auto;"><table class="leaderboard-table"><thead><tr><th>Shade</th><th>Quality</th><th>Lots</th><th>Avg ₹/kg</th><th>Min</th><th>Max</th><th>Variation (CV)</th></tr></thead><tbody>{rows}</tbody></table></div>""", unsafe_allow_html=True)
    if not high.empty:
        worst = high.iloc[0]
        insight_card(f"<strong>{worst['SHADE']} / {worst['QUALITY']}</strong> swings from ₹{worst['Min']:.2f} to ₹{worst['Max']:.2f} per kg ({worst['CV %']:.0f}% variation) across {int(worst['Lots'])} lots. Same recipe should cost the same — high spread points to <strong>over-dosing, weighing errors, or inconsistent process</strong>. Standardise the recipe here first.", kind="risk")
    else:
        insight_card("Cost per kg is consistent within repeated shade × quality combos — recipes look well controlled.", kind="good")


def render_business_type(data):
    if "Business Type" not in data.columns or data["Business Type"].nunique() <= 1:
        return
    section_header("🏷️", "Business Type Breakdown", "Volume and cost split by business type")
    agg = dict(Weight=("Weight","sum"), Metres=("MTRS","sum"), Lots=("MTRS","count"))
    if HAS_COST: agg["Cost"] = ("Total Cost","sum")
    bt = data.groupby("Business Type").agg(**agg).reset_index().sort_values("Weight", ascending=False)
    if HAS_COST:
        bt["Cost/KG"] = (bt["Cost"] / bt["Weight"].replace(0, pd.NA)).round(2)
    c1, c2 = st.columns(2)
    with c1:
        fig = go.Figure(go.Pie(labels=bt["Business Type"], values=bt["Weight"], hole=0.55,
            marker=dict(colors=PALETTE[:len(bt)], line=dict(color="#fff", width=2)),
            textinfo="label+percent", textfont=dict(size=12, color="#374151")))
        apply_layout(fig, "Weight Share by Business Type", height=300); pc(fig)
    with c2:
        ckg_h = "<th>Cost/KG</th>" if HAS_COST else ""
        rows = ""
        for _, r in bt.iterrows():
            ckg_c = (f"<td>₹{r['Cost/KG']:.2f}</td>" if HAS_COST and pd.notna(r['Cost/KG']) else ("<td>—</td>" if HAS_COST else ""))
            cost_c = f"{fmt_cur(r['Cost'])}" if HAS_COST else "—"
            rows += f"<tr><td>{r['Business Type']}</td><td>{fmt_in(r['Weight'])}</td><td>{int(r['Lots'])}</td><td>{cost_c}</td>{ckg_c}</tr>"
        st.markdown(f"""<div style="overflow-x:auto;border-radius:12px;border:1px solid #e5e7eb;"><table class="leaderboard-table"><thead><tr><th>Business Type</th><th>Weight (kg)</th><th>Lots</th><th>Total Cost</th>{ckg_h}</tr></thead><tbody>{rows}</tbody></table></div>""", unsafe_allow_html=True)


def render_cost_flag_table(data):
    """Full lot-wise flag table — Airmesh / Towel / Thin Quality only.
    < 8 → no color, 8 to <10 → yellow, >= 10 → red on the Total Cost Amount cell only.
    Lycra is excluded (rule pending)."""
    section_header("🚦", "Cost Amount Flags", "Lot-wise Total Cost Amount check — Airmesh, Towel & Thin Quality")
    if "Total Cost Amount" not in data.columns or data["Total Cost Amount"].sum() == 0:
        st.info("ℹ️ Total_Cost_Amount field not available yet for this selection."); return
    target_types = ["Airmesh", "Towel", "Thin Quality"]
    d = data[data["Business Type"].isin(target_types)].copy()
    if d.empty:
        st.info("ℹ️ No Airmesh / Towel / Thin Quality lots found in this selection."); return

    def _flag(v):
        if v >= 10:
            return "🔴", "background:#fee2e2;color:#b91c1c;font-weight:700;"
        elif v >= 8:
            return "🟡", "background:#fef9c3;color:#92400e;font-weight:700;"
        return "—", ""

    d = d.sort_values(["Business Type", "Production Date"])

    # same column set as the Day-view Production Sheet, plus Total Cost Amount at the end
    cost_cols = [c for c in ["Total Dye Cost", "Total Chemical Cost", "Total Cost"] if c in d.columns]
    display_cols = (["LOT NO.", "Party Name", "QUALITY", "SHADE", "SIZE", "M.No.", "MTRS", "Weight"]
                     + cost_cols + ["Business Type", "MASTER NAME"])
    display_cols = [c for c in display_cols if c in d.columns]
    money_cols = {"Total Dye Cost", "Total Chemical Cost", "Total Cost"}
    num_cols = {"MTRS", "Weight"}

    headers_html = "".join(f"<th>{c}</th>" for c in display_cols) + "<th>Total Cost Amount</th>"
    rows = ""
    for _, r in d.iterrows():
        cells = ""
        for col in display_cols:
            if col in num_cols:
                cells += f"<td>{fmt_in(r[col])}</td>"
            elif col in money_cols:
                cells += f"<td>{fmt_cur(r[col])}</td>"
            else:
                cells += f"<td>{r[col]}</td>"
        val = r["Total Cost Amount"]
        badge, style = _flag(val)
        cells += f"<td style='{style}'>{val:.2f} {badge}</td>"
        rows += f"<tr>{cells}</tr>"
    st.markdown(f"""<div style="overflow-x:auto;border-radius:12px;border:1px solid #e5e7eb;max-height:460px;overflow-y:auto;">
      <table class="leaderboard-table"><thead><tr>{headers_html}</tr></thead>
      <tbody>{rows}</tbody></table></div>""", unsafe_allow_html=True)

    n_red = int((d["Total Cost Amount"] >= 10).sum())
    n_yellow = int(((d["Total Cost Amount"] >= 8) & (d["Total Cost Amount"] < 10)).sum())
    n_ok = len(d) - n_red - n_yellow
    k1, k2, k3, k4 = st.columns(4)
    k1.metric("🔴 Red (≥10)", n_red)
    k2.metric("🟡 Yellow (8–9.99)", n_yellow)
    k3.metric("⚪ No Flag (<8)", n_ok)
    k4.metric("🧵 Lots Checked", len(d))
    if n_red > 0:
        insight_card(f"<strong>{n_red} lot(s)</strong> among Airmesh / Towel / Thin Quality have a Total Cost Amount of <strong>₹10 or more</strong> — review pricing / recipe for these immediately.", kind="risk")
    elif n_yellow > 0:
        insight_card(f"<strong>{n_yellow} lot(s)</strong> are in the caution zone (₹8–9.99). Keep an eye on these before they cross ₹10.", kind="warn")
    else:
        insight_card("All checked lots are under ₹8 — no cost flags raised.", kind="good")


def render_cost_block(scope_df, scope_chem, scope_dye, scope_label=""):
    """The whole 💰 cost section, reused by day & month views."""
    section_divider("💰 Cost & Profitability Analysis")
    render_cost_overview(scope_df)
    st.divider()
    render_dye_cost(scope_df, scope_dye)
    st.divider()
    render_recipe_consistency(scope_df)
    st.divider()
    render_business_type(scope_df)
    st.divider()
    render_cost_flag_table(scope_df)


# ═══════════════════════════════════════════════════════════
# DAY WISE VIEW
# ═══════════════════════════════════════════════════════════
if current_view == "day":
    available_days = sorted(df["Production Date"].dt.date.unique(), reverse=True)
    sel_day = st.selectbox("📅 Select Date", available_days,
        format_func=lambda d: d.strftime("%d %B %Y — %A"), label_visibility="visible")
    day_df = df[df["Production Date"].dt.date == sel_day]
    if day_df.empty:
        st.warning("No data for this date."); st.stop()
    day_chem = subset_sub(day_df, df_chem)
    day_dye  = subset_sub(day_df, df_dye)

    master_today = day_df["MASTER NAME"].value_counts().idxmax()
    cost_strip = f" &nbsp;·&nbsp; Cost: {fmt_cur(day_df['Total Cost'].sum())}" if HAS_COST else ""
    st.markdown(f"""<div class="day-header"><div>
        <div style="font-size:1.1rem;font-weight:800;letter-spacing:-.3px;">📋 Production Sheet — {sel_day.strftime('%d %B %Y')}</div>
        <div style="font-size:.82rem;opacity:.8;margin-top:4px;">Master: {master_today} &nbsp;·&nbsp; {sel_day.strftime('%A')}</div></div>
      <div style="text-align:right;font-size:.82rem;opacity:.7;">Lots: {len(day_df)} &nbsp;·&nbsp; Metres: {fmt_in(day_df['MTRS'].sum())} &nbsp;·&nbsp; Weight: {fmt_in(day_df['Weight'].sum())} kg{cost_strip}</div>
    </div>""", unsafe_allow_html=True)

    d_weight = int(day_df["Weight"].sum()); d_mtrs = int(day_df["MTRS"].sum())
    d_lots = len(day_df); d_parties = day_df["Party Name"].nunique()
    d_ratio = round(d_mtrs / d_weight, 2) if d_weight else 0
    k1, k2, k3, k4, k5 = st.columns(5)
    k1.metric("⚖️ Weight (kg)", fmt_in(d_weight))
    k2.metric("📏 Metres", fmt_in(d_mtrs))
    k3.metric("🧵 Lots", d_lots)
    k4.metric("🏭 Parties", d_parties)
    k5.metric("📐 Mtr ÷ KG Ratio", f"{d_ratio}x")
    if HAS_COST:
        kk1, kk2, kk3, kk4 = st.columns(4)
        kk1.metric("💰 Total Cost", fmt_cur(day_df["Total Cost"].sum()))
        kk2.metric("🧴 Dye Cost", fmt_cur(day_df["Total Dye Cost"].sum()))
        kk3.metric("🧪 Chemical Cost", fmt_cur(day_df["Total Chemical Cost"].sum()))
        ckg = day_df["Total Cost"].sum()/d_weight if d_weight else 0
        kk4.metric("⚖️ Cost / KG", f"₹{ckg:.2f}")

    st.divider()
    st.markdown("#### 📋 Lot-wise Production Sheet")
    cost_cols = [c for c in ["Total Dye Cost","Total Chemical Cost","Total Cost"] if c in day_df.columns and HAS_COST]
    display_cols = ["LOT NO.","Party Name","QUALITY","SHADE","SIZE","M.No.","MTRS","Weight"] + cost_cols + ["Business Type","MASTER NAME"]
    display_cols = [c for c in display_cols if c in day_df.columns]
    sheet_df = day_df[display_cols].copy().reset_index(drop=True); sheet_df.index = sheet_df.index + 1
    headers_html = "".join(f"<th>{c}</th>" for c in display_cols)
    money_cols = set(["Total Dye Cost","Total Chemical Cost","Total Cost"])
    rows_html_sheet = ""
    for i, row in sheet_df.iterrows():
        cells = ""
        for col in display_cols:
            if col in ["MTRS","Weight"]:
                cells += f"<td><b>{fmt_in(row[col])}</b></td>"
            elif col in money_cols:
                cells += f"<td>{fmt_cur(row[col])}</td>"
            else:
                cells += f"<td>{row[col]}</td>"
        rows_html_sheet += f"<tr><td><b>{i}</b></td>{cells}</tr>"
    total_cells = ""
    for col in display_cols:
        if col in ["MTRS","Weight"]:
            total_cells += f"<td><b>{fmt_in(day_df[col].sum())}</b></td>"
        elif col in money_cols:
            total_cells += f"<td><b>{fmt_cur(day_df[col].sum())}</b></td>"
        elif col == "LOT NO.":
            total_cells += "<td><b>TOTAL</b></td>"
        else:
            total_cells += "<td>—</td>"
    st.markdown(f"""<div style="overflow-x:auto;border-radius:12px;border:1px solid #e5e7eb;margin-bottom:16px;"><table class="prod-sheet-table">
      <thead><tr><th>#</th>{headers_html}</tr></thead>
      <tbody>{rows_html_sheet}<tr class="prod-sheet-total"><td><b>∑</b></td>{total_cells}</tr></tbody></table></div>""", unsafe_allow_html=True)

    st.divider()
    dc1, dc2 = st.columns(2)
    with dc1:
        p_day = day_df.groupby("Party Name").agg(Weight=("Weight","sum"), Metres=("MTRS","sum")).reset_index().sort_values("Weight", ascending=True)
        p_day["Share"] = (p_day["Weight"] / p_day["Weight"].sum() * 100).round(1)
        fig_pd = go.Figure(go.Bar(y=p_day["Party Name"], x=p_day["Weight"], orientation="h",
            marker=dict(color=p_day["Weight"], colorscale=[[0,"#fef3c7"],[0.5,"#f59e0b"],[1,"#d97706"]], showscale=False, line=dict(width=0)),
            text=[f"{fmt_in(v)} kg ({s}%)" for v,s in zip(p_day["Weight"], p_day["Share"])], textposition="outside",
            textfont=dict(color="#374151", size=11, family="JetBrains Mono")))
        apply_layout(fig_pd, "Party-wise Production (KG) — Today", height=320, show_legend=False)
        fig_pd.update_yaxes(showgrid=False); pc(fig_pd)
    with dc2:
        q_day = day_df.groupby("QUALITY").agg(Weight=("Weight","sum")).reset_index().sort_values("Weight", ascending=False).head(10)
        q_day["Share"] = (q_day["Weight"] / q_day["Weight"].sum() * 100).round(1)
        fig_qd = go.Figure(go.Bar(x=q_day["QUALITY"], y=q_day["Weight"],
            marker=dict(color=list(range(len(q_day))), colorscale="Oranges", showscale=False, line=dict(width=0)),
            text=[f"{fmt_in(v)}\n({s}%)" for v,s in zip(q_day["Weight"], q_day["Share"])], textposition="outside",
            textfont=dict(color="#374151", size=10, family="JetBrains Mono")))
        apply_layout(fig_qd, "Quality-wise (KG) — Today", height=320, show_legend=False)
        fig_qd.update_xaxes(tickangle=-30, showgrid=False); pc(fig_qd)
    dc3, dc4 = st.columns(2)
    with dc3:
        shade_day = day_df.groupby("SHADE").agg(Lots=("MTRS","count"), Weight=("Weight","sum")).reset_index().sort_values("Lots", ascending=False)
        fig_sd = go.Figure(go.Pie(labels=shade_day["SHADE"], values=shade_day["Lots"], hole=0.52,
            marker=dict(colors=PALETTE[:len(shade_day)], line=dict(color="#ffffff", width=2)),
            textinfo="label+percent", textfont=dict(size=11, color="#374151"),
            customdata=shade_day["Weight"],
            hovertemplate="<b>%{label}</b><br>Lots: %{value}<br>Share: %{percent}<br>Weight: %{customdata:,.0f} kg<extra></extra>"))
        apply_layout(fig_sd, "Shade Distribution — Today", height=300); pc(fig_sd)
    with dc4:
        master_day = day_df.groupby("MASTER NAME").agg(Lots=("MTRS","count"), Weight=("Weight","sum")).reset_index().sort_values("Lots", ascending=False)
        fig_md = go.Figure(go.Pie(labels=master_day["MASTER NAME"], values=master_day["Lots"], hole=0.55,
            marker=dict(colors=["#d97706","#3b82f6","#8b5cf6","#10b981","#ef4444"], line=dict(color="#ffffff", width=2)),
            textinfo="label+percent", textfont=dict(size=12, color="#374151"),
            customdata=master_day["Weight"],
            hovertemplate="<b>%{label}</b><br>Lots: %{value}<br>Share: %{percent}<br>Weight: %{customdata:,.0f} kg<extra></extra>"))
        apply_layout(fig_md, "Master Allocation — Today", height=300); pc(fig_md)

    section_divider("📋 Party-wise Summary — Today")
    day_sum = day_df.groupby("Party Name").agg(Metres=("MTRS","sum"), Weight_kg=("Weight","sum"), Lots=("MTRS","count")).reset_index().sort_values("Weight_kg", ascending=False)
    day_sum["Avg KG/Lot"] = (day_sum["Weight_kg"] / day_sum["Lots"]).round(1)
    day_sum["Avg Mtrs/Lot"] = (day_sum["Metres"] / day_sum["Lots"]).round(0).astype(int)
    day_sum["Share % (Weight)"] = (day_sum["Weight_kg"] / day_sum["Weight_kg"].sum() * 100).round(1)
    rows_day = "".join(f"<tr><td>{r['Party Name']}</td><td>{fmt_in(r['Metres'])}</td><td>{fmt_in(r['Weight_kg'])}</td><td>{int(r['Lots'])}</td><td>{r['Avg KG/Lot']:.1f}</td><td>{fmt_in(r['Avg Mtrs/Lot'])}</td><td>{r['Share % (Weight)']:.1f}%</td></tr>" for _, r in day_sum.iterrows())
    st.markdown(f"""<div style="background:#fff;border:1px solid #e8ecf2;border-radius:14px;overflow:hidden;box-shadow:0 1px 4px rgba(0,0,0,0.05);"><table class="sum-table"><thead><tr><th>Party</th><th>Metres</th><th>Weight (kg)</th><th>Lots</th><th>Avg KG/Lot</th><th>Avg Mtrs/Lot</th><th>Share % (Weight)</th></tr></thead><tbody>{rows_day}</tbody></table></div>""", unsafe_allow_html=True)

    st.divider()
    section_divider("🧠 Business Decision Analysis — Day View")
    render_machine_utilization(day_df); st.divider()
    render_master_productivity(day_df); st.divider()
    render_small_lot_analysis(day_df); st.divider()
    render_party_dependency(day_df); st.divider()
    render_chemical_consumption(day_df, day_chem); st.divider()
    render_shade_complexity(day_df, day_chem, day_dye); st.divider()
    render_quality_efficiency(day_df)

    st.divider()
    render_cost_block(day_df, day_chem, day_dye, scope_label=sel_day.strftime("%d %B %Y"))

    st.divider()
    render_business_insights(day_df, day_chem, day_dye, scope_label=sel_day.strftime("%d %B %Y"))


# ═══════════════════════════════════════════════════════════
# MONTH WISE VIEW
# ═══════════════════════════════════════════════════════════
else:
    df["Month"]     = df["Production Date"].dt.to_period("M")
    df["Month_str"] = df["Production Date"].dt.strftime("%B %Y")
    available_months = sorted(df["Month"].unique(), reverse=True)
    month_labels = {str(m): df[df["Month"]==m]["Month_str"].iloc[0] for m in available_months}
    sel_month_str = st.selectbox("📆 Select Month", [str(m) for m in available_months],
        format_func=lambda m: month_labels[m], label_visibility="visible")
    sel_month = pd.Period(sel_month_str, freq="M")
    month_df  = df[df["Month"] == sel_month]
    if month_df.empty:
        st.warning("No data for this month."); st.stop()
    month_chem = subset_sub(month_df, df_chem)
    month_dye  = subset_sub(month_df, df_dye)

    total_weight = int(month_df["Weight"].sum()); total_mtrs = int(month_df["MTRS"].sum())
    total_lots = len(month_df); active_parties = month_df["Party Name"].nunique()
    working_days = month_df["Production Date"].nunique()
    mtr_kg_ratio = round(total_mtrs / total_weight, 2) if total_weight else 0
    avg_kg_day   = int(round(total_weight / working_days)) if working_days else 0
    all_mtrs = int(df["MTRS"].sum()); all_weight = int(df["Weight"].sum())
    delta_weight = f"{(total_weight/all_weight*100):.1f}% of total" if total_weight != all_weight else None
    delta_mtrs   = f"{(total_mtrs/all_mtrs*100):.1f}% of total" if total_mtrs != all_mtrs else None
    delta_lots   = f"{(total_lots/len(df)*100):.1f}% of total" if total_lots != len(df) else None

    k1, k2, k3, k4, k5, k6, k7 = st.columns(7)
    k1.metric("⚖️ Total Weight (kg)", fmt_in(total_weight), delta=delta_weight)
    k2.metric("📏 Total Metres", fmt_in(total_mtrs), delta=delta_mtrs)
    k3.metric("🧵 Total Lots", fmt_in(total_lots), delta=delta_lots)
    k4.metric("🏭 Active Parties", active_parties)
    k5.metric("📅 Working Days", working_days)
    k6.metric("📦 Avg KG/Day", fmt_in(avg_kg_day))
    k7.metric("📐 Mtr ÷ KG Ratio", f"{mtr_kg_ratio}x")
    if HAS_COST:
        kk1, kk2, kk3, kk4, kk5, kk6 = st.columns(6)
        kk1.metric("💰 Total Cost", fmt_cur(month_df["Total Cost"].sum()))
        kk2.metric("🧴 Dye Cost", fmt_cur(month_df["Total Dye Cost"].sum()))
        kk3.metric("🧪 Chemical Cost", fmt_cur(month_df["Total Chemical Cost"].sum()))
        ckg = month_df["Total Cost"].sum()/total_weight if total_weight else 0
        cmtr = month_df["Total Cost"].sum()/total_mtrs if total_mtrs else 0
        kk4.metric("⚖️ Cost / KG", f"₹{ckg:.2f}")
        kk5.metric("📏 Cost / Metre", f"₹{cmtr:.2f}")
        dye_share = month_df["Total Dye Cost"].sum()/(month_df["Total Dye Cost"].sum()+month_df["Total Chemical Cost"].sum())*100 if (month_df["Total Dye Cost"].sum()+month_df["Total Chemical Cost"].sum()) else 0
        kk6.metric("🧴 Dye Share %", f"{dye_share:.0f}%")

    st.divider()
    daily = month_df.groupby("Production Date").agg(Metres=("MTRS","sum"), Weight=("Weight","sum"), Lots=("MTRS","count")).reset_index().sort_values("Production Date")
    avg_wt = daily["Weight"].mean()
    bar_colors_wt = ["#d97706" if v >= avg_wt*1.1 else "#ef4444" if v < avg_wt*0.7 else "#f59e0b" for v in daily["Weight"]]
    fig_wt_day = go.Figure(go.Bar(x=daily["Production Date"], y=daily["Weight"], marker_color=bar_colors_wt,
        text=[fmt_in(int(v)) for v in daily["Weight"]], textposition="outside", textfont=dict(size=9, family="JetBrains Mono", color="#374151")))
    fig_wt_day.add_hline(y=avg_wt, line_dash="dot", line_color="#d97706", line_width=1.5, annotation_text=f"Avg {fmt_in(int(avg_wt))} kg", annotation_font_color="#374151", annotation_position="top right")
    apply_layout(fig_wt_day, "Daily Production Weight (KG)", height=280, show_legend=False); pc(fig_wt_day)

    row2_c1, row2_c2 = st.columns(2)
    with row2_c1:
        party_df = month_df.groupby("Party Name").agg(Weight=("Weight","sum"), Metres=("MTRS","sum"), Lots=("MTRS","count")).reset_index().sort_values("Weight", ascending=True)
        party_df["Share"] = (party_df["Weight"] / party_df["Weight"].sum() * 100).round(1)
        fig_party = go.Figure(go.Bar(y=party_df["Party Name"], x=party_df["Weight"], orientation="h",
            marker=dict(color=party_df["Weight"], colorscale=[[0,"#fef3c7"],[0.5,"#f59e0b"],[1,"#d97706"]], showscale=False, line=dict(width=0)),
            text=[f"{fmt_in(v)} ({s}%)" for v,s in zip(party_df["Weight"], party_df["Share"])], textposition="outside",
            textfont=dict(color="#374151", size=10, family="JetBrains Mono")))
        apply_layout(fig_party, "Party-wise Production (KG)", height=380, show_legend=False)
        fig_party.update_yaxes(showgrid=False); pc(fig_party)
    with row2_c2:
        quality_df = month_df.groupby("QUALITY").agg(Weight=("Weight","sum"), Lots=("MTRS","count")).reset_index().sort_values("Weight", ascending=False).head(12)
        quality_df["Share"] = (quality_df["Weight"] / quality_df["Weight"].sum() * 100).round(1)
        fig_qual = go.Figure(go.Bar(x=quality_df["QUALITY"], y=quality_df["Weight"],
            marker=dict(color=list(range(len(quality_df))), colorscale="Oranges", showscale=False, line=dict(width=0)),
            text=[f"{fmt_in(int(v))}\n({s}%)" for v,s in zip(quality_df["Weight"], quality_df["Share"])], textposition="outside",
            textfont=dict(color="#374151", size=10, family="JetBrains Mono")))
        apply_layout(fig_qual, "Top Fabric Qualities by KG", height=380, show_legend=False)
        fig_qual.update_xaxes(tickangle=-30, showgrid=False); pc(fig_qual)

    c3, c4 = st.columns(2)
    with c3:
        shade_df = month_df.groupby("SHADE").agg(Lots=("MTRS","count"), Weight=("Weight","sum")).reset_index().sort_values("Lots", ascending=False)
        top_shades = shade_df.head(10).copy()
        others_lots = shade_df.iloc[10:]["Lots"].sum(); others_wt = shade_df.iloc[10:]["Weight"].sum()
        if others_lots > 0:
            top_shades = pd.concat([top_shades, pd.DataFrame([{"SHADE":"Others","Lots":others_lots,"Weight":others_wt}])], ignore_index=True)
        fig_shade = go.Figure(go.Pie(labels=top_shades["SHADE"], values=top_shades["Lots"], hole=0.52,
            marker=dict(colors=PALETTE[:len(top_shades)], line=dict(color="#ffffff", width=2)),
            textinfo="label+percent", textfont=dict(size=11, color="#374151"),
            customdata=top_shades["Weight"],
            hovertemplate="<b>%{label}</b><br>Lots: %{value}<br>Share: %{percent}<br>Weight: %{customdata:,.0f} kg<extra></extra>"))
        apply_layout(fig_shade, "Shade Distribution (Lots)", height=320)
        fig_shade.update_layout(legend=dict(orientation="v", x=1.02, y=0.5, font=dict(size=11, color="#374151"))); pc(fig_shade)
    with c4:
        master_df = month_df.groupby("MASTER NAME").agg(Lots=("MTRS","count"), Weight=("Weight","sum")).reset_index().sort_values("Lots", ascending=False)
        fig_master = go.Figure(go.Pie(labels=master_df["MASTER NAME"], values=master_df["Lots"], hole=0.55,
            marker=dict(colors=["#d97706","#3b82f6","#8b5cf6","#10b981","#ef4444"], line=dict(color="#ffffff", width=2)),
            textinfo="label+percent", textfont=dict(size=12, color="#374151"),
            customdata=master_df["Weight"],
            hovertemplate="<b>%{label}</b><br>Lots: %{value}<br>Share: %{percent}<br>Weight: %{customdata:,.0f} kg<extra></extra>"))
        apply_layout(fig_master, "Master Allocation", height=320); pc(fig_master)

    c5, c6 = st.columns(2)
    with c5:
        lots_df = month_df.groupby("Production Date").size().reset_index(name="Lots").sort_values("Production Date")
        avg_lots = lots_df["Lots"].mean()
        bar_colors_lots = ["#d97706" if v >= avg_lots*1.1 else "#ef4444" if v < avg_lots*0.7 else "#f59e0b" for v in lots_df["Lots"]]
        fig_lots = go.Figure(go.Bar(x=lots_df["Production Date"], y=lots_df["Lots"], marker_color=bar_colors_lots,
            text=lots_df["Lots"], textposition="outside", textfont=dict(size=10, family="JetBrains Mono", color="#374151")))
        fig_lots.add_hline(y=avg_lots, line_dash="dot", line_color="#d97706", line_width=1.5, annotation_text=f"Avg {avg_lots:.1f} lots/day", annotation_font_color="#374151", annotation_position="top right")
        apply_layout(fig_lots, "Lots Processed Per Day", height=280, show_legend=False); pc(fig_lots)
    with c6:
        scatter_df = month_df.groupby("Party Name").agg(Metres=("MTRS","sum"), Weight=("Weight","sum"), Lots=("MTRS","count")).reset_index()
        fig_scatter = px.scatter(scatter_df, x="Metres", y="Weight", size="Lots", color="Party Name",
            color_discrete_sequence=PALETTE, text="Party Name", size_max=50,
            hover_data={"Lots":True,"Metres":":,.0f","Weight":":,.0f"})
        fig_scatter.update_traces(textposition="top center", textfont=dict(size=10, color="#374151"))
        apply_layout(fig_scatter, "Metres vs Weight by Party (bubble = lots)", height=280); pc(fig_scatter)

    section_divider("📋 Party-wise Summary")
    summary = month_df.groupby("Party Name").agg(Metres=("MTRS","sum"), Weight_kg=("Weight","sum"), Lots=("MTRS","count")).reset_index().sort_values("Weight_kg", ascending=False)
    summary["Avg KG/Lot"] = (summary["Weight_kg"] / summary["Lots"]).round(1)
    summary["Avg Mtrs/Lot"] = (summary["Metres"] / summary["Lots"]).round(0).astype(int)
    summary["Share % (Weight)"] = (summary["Weight_kg"] / summary["Weight_kg"].sum() * 100).round(1)
    rows_html = "".join(f"<tr><td>{r['Party Name']}</td><td>{fmt_in(r['Metres'])}</td><td>{fmt_in(r['Weight_kg'])}</td><td>{int(r['Lots'])}</td><td>{r['Avg KG/Lot']:.1f}</td><td>{fmt_in(r['Avg Mtrs/Lot'])}</td><td>{r['Share % (Weight)']:.1f}%</td></tr>" for _, r in summary.iterrows())
    st.markdown(f"""<div style="background:#fff;border:1px solid #e8ecf2;border-radius:14px;overflow:hidden;box-shadow:0 1px 4px rgba(0,0,0,0.05);"><table class="sum-table"><thead><tr><th>Party</th><th>Metres</th><th>Weight (kg)</th><th>Lots</th><th>Avg KG/Lot</th><th>Avg Mtrs/Lot</th><th>Share % (Weight)</th></tr></thead><tbody>{rows_html}</tbody></table></div>""", unsafe_allow_html=True)

    with st.expander("🧵 Quality-wise Breakdown"):
        q_summary = month_df.groupby(["QUALITY","SHADE"]).agg(Metres=("MTRS","sum"), Weight=("Weight","sum"), Lots=("MTRS","count")).reset_index().sort_values("Weight", ascending=False)
        col_a, col_b = st.columns([2,1])
        with col_a:
            q_rows = "".join(f"<tr><td>{r['QUALITY']}</td><td>{r['SHADE']}</td><td>{fmt_in(r['Weight'])}</td><td>{fmt_in(r['Metres'])}</td><td>{int(r['Lots'])}</td></tr>" for _, r in q_summary.iterrows())
            q_style = "<style>.q-table{width:100%;border-collapse:collapse;font-size:12px;}.q-table th{background:#f3f4f6;color:#6b7280;text-transform:uppercase;font-size:10px;letter-spacing:.06em;padding:9px 12px;border-bottom:1px solid #e5e7eb;text-align:left;font-weight:600;}.q-table td{padding:8px 12px;color:#1f2937;border-bottom:1px solid #f9fafb;font-family:'JetBrains Mono',monospace;font-size:11px;}.q-table td:first-child{color:#d97706;font-family:'Inter',sans-serif;font-weight:600;}.q-table td:nth-child(2){color:#3b82f6;font-family:'Inter',sans-serif;}.q-table tr:hover td{background:#fafafa;}</style>"
            q_table = f'<div style="max-height:360px;overflow-y:auto;border-radius:10px;border:1px solid #e5e7eb;"><table class="q-table"><thead><tr><th>Quality</th><th>Shade</th><th>Weight (kg)</th><th>Metres</th><th>Lots</th></tr></thead><tbody>{q_rows}</tbody></table></div>'
            st.markdown(q_style + q_table, unsafe_allow_html=True)
        with col_b:
            fig_qtree = px.treemap(q_summary.head(30), path=["QUALITY","SHADE"], values="Weight", color="Weight", color_continuous_scale="Oranges")
            fig_qtree.update_layout(paper_bgcolor="rgba(255,255,255,1)", font=dict(color="#374151"), height=380, margin=dict(l=0,r=0,t=0,b=0))
            fig_qtree.update_coloraxes(showscale=False); pc(fig_qtree)

    st.divider()
    section_divider("🧠 Business Decision Analysis — Month View")
    render_machine_utilization(month_df); st.divider()
    render_master_productivity(month_df); st.divider()
    render_small_lot_analysis(month_df); st.divider()
    render_party_dependency(month_df); st.divider()
    render_chemical_consumption(month_df, month_chem); st.divider()
    render_shade_complexity(month_df, month_chem, month_dye); st.divider()
    render_quality_efficiency(month_df); st.divider()
    render_mom_comparison(df, sel_month)

    st.divider()
    render_cost_block(month_df, month_chem, month_dye, scope_label=month_labels[sel_month_str])

    st.divider()
    render_business_insights(month_df, month_chem, month_dye, scope_label=month_labels[sel_month_str])


# ─────────────────────────────────────────────
# RAW DATA EXPANDER
# ─────────────────────────────────────────────
view_df = day_df if current_view == "day" else month_df
with st.expander("🗃️ View Raw Data — Excel Mode"):
    st.markdown(f"**{len(view_df):,} rows** after filters")
    display_df = view_df.copy()
    display_df["Production Date"] = display_df["Production Date"].dt.strftime("%d-%b-%Y")
    drop_helpers = [c for c in ["_id","Month","Month_str"] if c in display_df.columns]
    display_df = display_df.drop(columns=drop_helpers)

    # ── reorder columns to match the Zoho report exactly ──
    # maps the dashboard's internal column name → Zoho report header, in report order.
    zoho_order = [
        ("Production Date", "Production Date"),
        ("Party Name",      "Party Name"),
        ("QUALITY",         "Quality"),
        ("SIZE",            "Size"),
        ("SHADE",           "Shade"),
        ("M.No.",           "M.No."),
        ("MTRS",            "Mtrs"),
        ("Weight",          "Weight"),
        ("LOT NO.",         "Lot No."),
        ("MASTER NAME",     "Masrer Name"),
        ("Business Type",   "Business Type"),
        ("Total Cost",          "Total Cost"),
        ("Total Chemical Cost", "Total Chemical Cost"),
        ("Total Dye Cost",      "Total Dye Cost"),
        ("Total Chemical %",    "Total Chemical Percentage"),
        ("Total Dye %",         "Total Dye Percentage"),
        ("Total Cost Amount",   "Total_Cost_Amount"),
    ]
    ordered_internal = [src for src, _ in zoho_order if src in display_df.columns]
    rename_to_zoho   = {src: dst for src, dst in zoho_order if src in display_df.columns}
    display_df = display_df[ordered_internal].rename(columns=rename_to_zoho)
    col_search, col_download = st.columns([3, 1])
    with col_search:
        search = st.text_input("🔍 Search", placeholder="Type to filter any column...", label_visibility="collapsed")
    with col_download:
        csv = display_df.to_csv(index=False).encode("utf-8")
        st.download_button("⬇️ Download CSV", csv, "dyeing_data.csv", "text/csv", use_container_width=True)
    if search:
        mask = display_df.apply(lambda col: col.astype(str).str.contains(search, case=False, na=False)).any(axis=1)
        display_df = display_df[mask]
    st.markdown(f"<div style='color:#6b7280;font-size:11px;margin-bottom:6px;'>Showing <b>{len(display_df):,}</b> rows · MTRS: <b style='color:#d97706'>{fmt_in(display_df['Mtrs'].sum())}</b> · Weight: <b style='color:#3b82f6'>{fmt_in(display_df['Weight'].sum())}</b></div>", unsafe_allow_html=True)
    st.dataframe(display_df, use_container_width=True, hide_index=True, height=400)
    agg1, agg2, agg3, agg4 = st.columns(4)
    agg1.metric("Sum MTRS", fmt_in(display_df['Mtrs'].sum()))
    agg2.metric("Avg MTRS", fmt_in(int(display_df['Mtrs'].mean())) if len(display_df) else "0")
    agg3.metric("Sum Weight", fmt_in(display_df['Weight'].sum()))
    agg4.metric("Avg Weight", fmt_in(int(display_df['Weight'].mean())) if len(display_df) else "0")

# ─────────────────────────────────────────────
# AUTO REFRESH
# ─────────────────────────────────────────────
st.markdown(f"<script>setTimeout(function(){{window.location.reload();}},{AUTO_REFRESH_SEC*1000});</script>", unsafe_allow_html=True)

# ─────────────────────────────────────────────
# FOOTER
# ─────────────────────────────────────────────
min_d = df['Production Date'].min().strftime('%b %d') if not df.empty else ''
max_d = df['Production Date'].max().strftime('%b %d, %Y') if not df.empty else ''
cost_foot = f" · {fmt_cur(df['Total Cost'].sum())} cost" if HAS_COST else ""
st.markdown(f"""<div style="text-align:center;margin-top:32px;color:#9ca3af;font-size:.8rem;border-top:1px solid #e8ecf2;padding-top:16px;">
  🎨 Dyeing Operations Dashboard · {min_d} – {max_d} ·
  {fmt_in(len(df))} lots · {fmt_in(int(df['MTRS'].sum()))} metres · {fmt_in(int(df['Weight'].sum()))} kg{cost_foot} ·
  <span style="color:#16a34a;">● Live</span> · Zoho Creator · Refreshes every {AUTO_REFRESH_SEC}s
</div>""", unsafe_allow_html=True)