"""
run_debug.py
────────────────────────────────────────────────────────────
Drop this file next to your .streamlit/secrets.toml folder.
It reads the Zoho credentials from secrets.toml automatically
and runs the full sub-form diagnostic.

Usage:
    pip install requests toml
    python run_debug.py
────────────────────────────────────────────────────────────
"""

import json
import os
import re
import sys

# ── 1. Read secrets.toml ──────────────────────────────────
def load_secrets(path=".streamlit/secrets.toml"):
    """Minimal TOML parser — handles [section] and key = "value" lines."""
    secrets = {}
    current_section = None
    try:
        with open(path, "r") as f:
            for line in f:
                line = line.strip()
                if not line or line.startswith("#"):
                    continue
                # Section header
                m = re.match(r'^\[([^\]]+)\]$', line)
                if m:
                    current_section = m.group(1).strip()
                    secrets[current_section] = {}
                    continue
                # Key = value
                m = re.match(r'^(\w+)\s*=\s*"([^"]*)"', line)
                if m and current_section:
                    secrets[current_section][m.group(1)] = m.group(2)
    except FileNotFoundError:
        print(f"❌  Could not find {path}")
        print("    Make sure you run this script from your project root folder")
        print("    (the folder that contains the .streamlit/ directory).")
        sys.exit(1)
    return secrets

secrets = load_secrets()
cfg_raw = secrets.get("zoho_creator", {})

if not cfg_raw:
    print("❌  No [zoho_creator] section found in secrets.toml")
    sys.exit(1)

print("✅  Loaded secrets.toml")
print(f"    account_owner : {cfg_raw.get('account_owner')}")
print(f"    app_name      : {cfg_raw.get('app_name')}")
print(f"    report_name   : {cfg_raw.get('report_name')}")
print(f"    chem_report   : {cfg_raw.get('chem_report_name', '(not set)')}")
print(f"    dye_report    : {cfg_raw.get('dye_report_name', '(not set)')}")

# ── 2. Patch CFG into the debug script and run inline ─────
# (avoids any import path issues — just exec the debug module)

CFG = {
    "client_id":        cfg_raw.get("client_id", ""),
    "client_secret":    cfg_raw.get("client_secret", ""),
    "refresh_token":    cfg_raw.get("refresh_token", ""),
    "account_owner":    cfg_raw.get("account_owner", ""),
    "app_name":         cfg_raw.get("app_name", ""),
    "report_name":      cfg_raw.get("report_name", ""),
    "chem_report_name": cfg_raw.get("chem_report_name", ""),
    "dye_report_name":  cfg_raw.get("dye_report_name", ""),
    "probe_limit":      int(cfg_raw.get("detail_fetch_cap", "5")),   # keep small for debug
}

# Override probe_limit to a small number for fast debugging
CFG["probe_limit"] = 5

# ── 3. Run the diagnostic ──────────────────────────────────
import requests
from datetime import datetime

SEPARATOR = "─" * 72
OUT_RAW    = "zoho_debug_raw_sample.json"
OUT_DETAIL = "zoho_debug_detail_sample.json"
OUT_REPORT = "zoho_debug_report.txt"


def get_token():
    resp = requests.post(
        "https://accounts.zoho.com/oauth/v2/token",
        params={
            "refresh_token": CFG["refresh_token"],
            "client_id":     CFG["client_id"],
            "client_secret": CFG["client_secret"],
            "grant_type":    "refresh_token",
        }, timeout=15,
    )
    resp.raise_for_status()
    data = resp.json()
    if "access_token" not in data:
        raise RuntimeError(f"Token error: {json.dumps(data, indent=2)}")
    return data["access_token"]


def base_url(report=None):
    r = report or CFG["report_name"]
    return f"https://creator.zoho.com/api/v2/{CFG['account_owner']}/{CFG['app_name']}/report/{r}"


def fetch_records(url, headers, limit=5):
    resp = requests.get(url, headers=headers,
                        params={"from": 0, "limit": limit, "field_config": "all"},
                        timeout=20)
    resp.raise_for_status()
    return resp.json().get("data", [])


def fetch_one(url, record_id, headers):
    resp = requests.get(f"{url}/{record_id}", headers=headers,
                        params={"field_config": "all"}, timeout=20)
    resp.raise_for_status()
    return resp.json().get("data", {})


def dv(val):
    if isinstance(val, dict):
        return (val.get("display_value") or val.get("display_Value")
                or val.get("value") or val.get("zc_display_value") or val)
    return val


def classify(name, items):
    blob = (name + " " + json.dumps(items[:1])).lower()
    if "dye" in blob:   return "dye"
    if "chem" in blob:  return "chem"
    return "unknown"


def describe_item(item):
    if not isinstance(item, dict):
        return str(item)
    zc = item.get("zc_display_value")
    if isinstance(zc, dict):
        return f"⚠️  COLLAPSED stub — zc_display_value keys: {list(zc.keys())}"
    keys = [k for k in item.keys() if k not in ("display_value", "ID", "zc_display_value", "id")]
    if keys:
        sample = {k: item[k] for k in keys[:6]}
        return f"✅  EXPANDED — keys: {keys}\n      sample: {json.dumps(sample, default=str)}"
    return f"⚠️  COLLAPSED — only: {list(item.keys())}"


def extract_rows(details):
    chem, dye, unk = [], [], []
    for rid, detail in details:
        for k, v in detail.items():
            if not (isinstance(v, list) and v and isinstance(v[0], dict)):
                continue
            kind = classify(k, v)
            for item in v:
                flat = {}
                zc = item.get("zc_display_value")
                if isinstance(zc, dict):
                    for kk, vv in zc.items():
                        flat[kk] = dv(vv)
                else:
                    for kk, vv in item.items():
                        if kk not in ("display_value", "zc_display_value"):
                            flat[kk] = dv(vv)
                flat["_parent_id"] = rid
                flat["_source_field"] = k
                {"chem": chem, "dye": dye}.get(kind, unk).append(flat)
    return chem, dye, unk


def probe_separate_report(report_name, label, headers):
    if not report_name:
        return [f"  {label}: ⏭️  Not configured (add chem_report_name / dye_report_name to secrets.toml to test)"], False
    url = base_url(report_name)
    try:
        recs = fetch_records(url, headers, limit=3)
    except Exception as e:
        return [f"  {label}: ❌  {e}"], False
    if not recs:
        return [f"  {label}: ⚠️  Report exists but 0 records returned"], False
    cols = list(recs[0].keys())
    sample = {k: dv(v) for k, v in list(recs[0].items())[:8]}
    return [
        f"  {label}: ✅  {len(recs)} record(s) — columns: {cols}",
        f"    sample: {json.dumps(sample, indent=4, default=str)}",
    ], True


def build_recommendations(report_list_fields, chem_rows, dye_rows, unk_rows,
                           chem_ok, dye_ok):
    lines = [SEPARATOR, "RECOMMENDATIONS", SEPARATOR, ""]
    if chem_ok and dye_ok:
        lines += [
            "✅ BEST PATH — Use the two separate sub-form reports.",
            "   Add two new API calls in load_data() for those reports.",
            "   Join to the main df on the parent/lookup ID field.",
        ]
    elif chem_rows or dye_rows:
        lines += [
            "✅ WORKABLE PATH — Per-record detail fetches ARE returning sub-form rows.",
            "   The existing _load_subform_details() in the dashboard should work.",
            "   ACTION: in secrets.toml set   detail_fetch_cap = <total record count>",
            "   and make sure the cache TTL is ≥ 900s so every auto-refresh doesn't",
            "   re-hit the API.",
        ]
    elif report_list_fields:
        lines += [
            "⚠️  Sub-form fields appear in report BUT are collapsed stubs.",
            "   Zoho is only returning display_value / ID — not the line items.",
            "",
            "   FIX A (recommended): In Zoho Creator → your form → each sub-form →",
            "     create a new Report where every row is ONE sub-form line-item.",
            "     Add a Lookup column back to the parent production entry.",
            "     Put those two report names in secrets.toml.",
            "",
            "   FIX B: In your existing report settings, add sub-form columns",
            "     explicitly — Zoho sometimes expands them in that case.",
        ]
    else:
        lines += [
            "❌  NO sub-form data found via any method.",
            "",
            "   REQUIRED STEPS:",
            "   1. In Zoho Creator → your app → Reports → New Report",
            "      Source: your production entry FORM, section: Chemical sub-form",
            "      Every row = one chemical line-item.  Add a Lookup to parent entry.",
            "      Repeat for dyes.",
            "   2. Add to secrets.toml:",
            '      chem_report_name = "Chemical_Lines_Report"',
            '      dye_report_name  = "Dye_Lines_Report"',
            "   3. Re-run this script to confirm.",
        ]
    if unk_rows:
        lines += ["", f"ℹ️  {len(unk_rows)} unclassified sub-form rows — check zoho_debug_detail_sample.json"]
    return lines


# ──────────────────────────────────────────────────────────
print("\n" + SEPARATOR)
print("  Zoho Sub-Form Diagnostic")
print(f"  {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
print(SEPARATOR)

# Token
print("\n[1/5] Getting access token …")
token   = get_token()
headers = {"Authorization": f"Zoho-oauthtoken {token}"}
print("      ✅ OK")

# Report-level
print(f"\n[2/5] Fetching {CFG['probe_limit']} records from report …")
url     = base_url()
records = fetch_records(url, headers, limit=CFG["probe_limit"])
print(f"      Fetched {len(records)} record(s)")
with open(OUT_RAW, "w") as f:
    json.dump(records[:3], f, indent=2, default=str)
print(f"      → {OUT_RAW}")

report_lines = [SEPARATOR, "ZOHO SUB-FORM DIAGNOSTIC",
                f"Generated: {datetime.now().isoformat()}", SEPARATOR, "",
                "SECTION 1 — Sub-form fields in report response", ""]
report_list_fields = {}
for rec in records:
    rid = rec.get("ID") or rec.get("id", "?")
    for k, v in rec.items():
        if isinstance(v, list) and v:
            report_list_fields.setdefault(k, []).append((rid, v))
if not report_list_fields:
    report_lines.append("  ❌  No list/sub-form fields in report response at all.")
else:
    for fname, samples in report_list_fields.items():
        rid, items = samples[0]
        desc = describe_item(items[0])
        kind = classify(fname, items)
        report_lines.append(f"  Field '{fname}' [{kind}] — {len(items)} row(s)")
        report_lines.append(f"    {desc}")
report_lines.append("")

# Per-record detail
print(f"\n[3/5] Fetching per-record detail for first {min(3,len(records))} records …")
details = []
for rec in records[:3]:
    rid = rec.get("ID") or rec.get("id")
    if rid is None:
        continue
    d = fetch_one(url, rid, headers)
    details.append((rid, d))
    list_keys = [k for k, v in d.items() if isinstance(v, list) and v]
    print(f"      Record {rid} — list fields: {list_keys or 'none'}")
with open(OUT_DETAIL, "w") as f:
    json.dump([{"record_id": rid, "data": d} for rid, d in details], f, indent=2, default=str)
print(f"      → {OUT_DETAIL}")

report_lines += ["SECTION 2 — Per-record detail sub-form fields", ""]
for rid, detail in details:
    list_fields = {k: v for k, v in detail.items() if isinstance(v, list) and v and isinstance(v[0], dict)}
    if not list_fields:
        report_lines.append(f"  Record {rid}: ❌  No sub-form arrays in detail.")
    for fname, items in list_fields.items():
        kind = classify(fname, items)
        report_lines.append(f"  Record {rid} — '{fname}' [{kind}] — {len(items)} row(s)")
        report_lines.append(f"    {describe_item(items[0])}")
report_lines.append("")

# Separate reports
print("\n[4/5] Probing separate sub-form reports …")
report_lines += ["SECTION 3 — Separate sub-form report probes", ""]
c_lines, chem_ok = probe_separate_report(CFG["chem_report_name"], "Chemical report", headers)
d_lines, dye_ok  = probe_separate_report(CFG["dye_report_name"],  "Dye report",      headers)
report_lines += c_lines + [""] + d_lines + [""]

# Row extraction
print("\n[5/5] Extracting sub-form rows …")
chem_rows, dye_rows, unk_rows = extract_rows(details)
print(f"      Chemical rows : {len(chem_rows)}")
print(f"      Dye rows      : {len(dye_rows)}")
print(f"      Unknown rows  : {len(unk_rows)}")
report_lines += [
    "SECTION 4 — Extracted rows (from first 3 record details)", "",
    f"  Chemical rows : {len(chem_rows)}",
    f"  Dye rows      : {len(dye_rows)}",
    f"  Unknown rows  : {len(unk_rows)}", "",
]
if chem_rows:
    report_lines.append(f"  Chem sample: {json.dumps(chem_rows[0], default=str)}")
if dye_rows:
    report_lines.append(f"  Dye sample : {json.dumps(dye_rows[0], default=str)}")
report_lines.append("")

# Recommendations
recs = build_recommendations(report_list_fields, chem_rows, dye_rows, unk_rows, chem_ok, dye_ok)
report_lines += recs

# All columns on first record
if records:
    report_lines += [
        "", SEPARATOR, "ALL FIELDS ON FIRST RECORD", SEPARATOR,
    ]
    for k, v in records[0].items():
        vtype = type(v).__name__
        vpreview = json.dumps(v, default=str)[:120]
        report_lines.append(f"  {k:40s} [{vtype:6s}]  {vpreview}")

report_text = "\n".join(report_lines)
with open(OUT_REPORT, "w") as f:
    f.write(report_text)

print(f"\n{'═'*56}")
print(f"  ✅ Report  → {OUT_REPORT}")
print(f"  ✅ Raw     → {OUT_RAW}")
print(f"  ✅ Detail  → {OUT_DETAIL}")
print(f"{'═'*56}\n")
print(report_text)