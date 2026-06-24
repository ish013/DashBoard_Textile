"""
zoho_find_costed_record.py
────────────────────────────────────────────────────────────────────────────
Scans records until it finds ones where Total_Cost > 0, then fetches their
full detail to confirm Dye_Cost and Total_Chemical_Cost sub-form rows exist.

We already know:
  - Sub-form field names: 'Dye_Cost' and 'Total_Chemical_Cost'
  - Records with cost=0 have empty sub-forms (staff haven't filled them)
  - We need a costed record to confirm the line-item shape

Usage:
    python zoho_find_costed_record.py
────────────────────────────────────────────────────────────────────────────
"""

import json, re, sys, requests
from datetime import datetime

# ── secrets.toml loader ──────────────────────────────────────────────────────
def load_secrets(path=".streamlit/secrets.toml"):
    secrets, section = {}, None
    try:
        for line in open(path):
            line = line.strip()
            if not line or line.startswith("#"): continue
            m = re.match(r'^\[([^\]]+)\]$', line)
            if m:
                section = m.group(1).strip(); secrets[section] = {}; continue
            m = re.match(r'^([\w]+)\s*=\s*"([^"]*)"', line)
            if m and section:
                secrets[section][m.group(1)] = m.group(2)
    except FileNotFoundError:
        print(f"❌  .streamlit/secrets.toml not found"); sys.exit(1)
    return secrets

cfg  = load_secrets().get("zoho_creator", {})
BASE = f"https://creator.zoho.com/api/v2/{cfg['account_owner']}/{cfg['app_name']}/report/{cfg['report_name']}"

def get_token():
    r = requests.post("https://accounts.zoho.com/oauth/v2/token", params={
        "refresh_token": cfg["refresh_token"], "client_id": cfg["client_id"],
        "client_secret": cfg["client_secret"], "grant_type": "refresh_token",
    }, timeout=15)
    r.raise_for_status()
    d = r.json()
    if "access_token" not in d: raise RuntimeError(str(d))
    return d["access_token"]

def dv(v):
    if isinstance(v, dict):
        return v.get("display_value") or v.get("value") or str(v)
    return str(v) if v is not None else ""

def has_cost(rec):
    for key in ("Total_Cost", "Total_Chemical_Cost", "Total_Chemical_Cost1",
                "Total_Dye_Cost", "Total_Chemical_Percentage", "Total_Dye_Percentage"):
        val = rec.get(key, "")
        try:
            if float(str(val).replace(",", "").strip() or "0") > 0:
                return True
        except: pass
    return False

# ────────────────────────────────────────────────────────────────────────────
print("=" * 65)
print("  Zoho — Find Costed Record & Inspect Sub-Forms")
print(f"  {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
print("=" * 65)

token   = get_token()
headers = {"Authorization": f"Zoho-oauthtoken {token}"}
print("✅  Token OK\n")

# ── Scan pages until we find costed records ──────────────────────────────────
print("[1] Scanning records for non-zero Total_Cost …")
costed = []
start  = 0
limit  = 200
pages_scanned = 0

while len(costed) < 5:
    r = requests.get(BASE, headers=headers,
                     params={"from": start, "limit": limit, "field_config": "all"}, timeout=20)
    r.raise_for_status()
    batch = r.json().get("data", [])
    if not batch:
        break
    pages_scanned += 1
    for rec in batch:
        if has_cost(rec):
            costed.append(rec)
            if len(costed) >= 5:
                break
    print(f"    Page {pages_scanned} ({start}–{start+len(batch)-1}): "
          f"found {len(costed)} costed record(s) so far")
    if len(batch) < limit:
        break
    start += limit

if not costed:
    print("\n❌  No records with non-zero cost found in entire dataset.")
    print("    This means staff have not yet entered Chemical/Dye sub-form")
    print("    data for ANY production entry.")
    print("    → Once they do, run this script again.")
    sys.exit(0)

print(f"\n    ✅ Found {len(costed)} costed record(s):")
for rec in costed:
    print(f"       ID={rec.get('ID')}  LOT={dv(rec.get('LOT_NO','?'))}  "
          f"Cost={dv(rec.get('Total_Cost','0'))}  "
          f"Chem={dv(rec.get('Total_Chemical_Cost1', rec.get('Total_Chemical_Cost','')))}  "
          f"Dye={dv(rec.get('Total_Dye_Cost',''))}")

# ── Fetch detail for each costed record ──────────────────────────────────────
print("\n[2] Fetching per-record detail for costed records …")

results = []
for rec in costed:
    rid = rec.get("ID")
    r2  = requests.get(f"{BASE}/{rid}", headers=headers,
                       params={"field_config": "all"}, timeout=20)
    r2.raise_for_status()
    detail = r2.json().get("data", {})

    chem_field = detail.get("Total_Chemical_Cost", [])
    dye_field  = detail.get("Dye_Cost", [])

    print(f"\n  ── Record {rid}  LOT={dv(rec.get('LOT_NO','?'))} ──")
    print(f"     Total_Cost              : {dv(detail.get('Total_Cost',''))}")
    print(f"     Total_Chemical_Cost1    : {dv(detail.get('Total_Chemical_Cost1',''))}")
    print(f"     Total_Dye_Cost          : {dv(detail.get('Total_Dye_Cost',''))}")
    print(f"     Total_Chemical_Cost rows: {len(chem_field)}")
    print(f"     Dye_Cost rows           : {len(dye_field)}")

    def show_rows(label, rows):
        if not rows:
            print(f"     {label}: (empty)")
            return
        first = rows[0]
        if not isinstance(first, dict):
            print(f"     {label}: non-dict items → {rows[:2]}")
            return
        zc = first.get("zc_display_value")
        meaningful = [k for k in first if k not in ("display_value","ID","zc_display_value","id")]
        if meaningful:
            print(f"     {label}: ✅ EXPANDED — columns: {list(first.keys())}")
            for i, row in enumerate(rows[:3]):
                flat = {}
                if isinstance(row.get("zc_display_value"), dict):
                    flat = {k: dv(v) for k, v in row["zc_display_value"].items()}
                else:
                    flat = {k: dv(v) for k, v in row.items()
                            if k not in ("display_value","zc_display_value")}
                print(f"       row {i+1}: {json.dumps(flat, default=str)}")
        elif isinstance(zc, dict) and zc:
            print(f"     {label}: ⚠️  COLLAPSED stub — zc keys: {list(zc.keys())}")
            print(f"       display: {json.dumps(zc, default=str)[:300]}")
        else:
            print(f"     {label}: ⚠️  stub only — keys: {list(first.keys())}")

    show_rows("Total_Chemical_Cost", chem_field)
    show_rows("Dye_Cost",            dye_field)
    results.append({"record_id": rid, "detail": detail})

# Save all detail
with open("zoho_costed_records_detail.json", "w") as f:
    json.dump(results, f, indent=2, default=str)
print(f"\n    Saved → zoho_costed_records_detail.json")

# ── Final verdict ─────────────────────────────────────────────────────────────
print("\n" + "=" * 65)
print("  VERDICT")
print("=" * 65)

any_chem_rows = any(len(r["detail"].get("Total_Chemical_Cost", [])) > 0 for r in results)
any_dye_rows  = any(len(r["detail"].get("Dye_Cost", [])) > 0 for r in results)

if any_chem_rows or any_dye_rows:
    print("""
✅  Sub-form line items ARE accessible via per-record detail fetch.

DASHBOARD FIX (2 changes in the existing code):

1. In load_data(), the sub-form field names to pass to _classify_and_collect
   are confirmed as:
       Chemical sub-form : 'Total_Chemical_Cost'
       Dye sub-form      : 'Dye_Cost'

2. In _classify_and_collect(), the auto-detection uses keyword matching on
   field names. Because 'Total_Chemical_Cost' contains 'chem' it should
   already route correctly. 'Dye_Cost' contains 'dye' — also fine.

3. Make sure secrets.toml has:
       detail_fetch_cap = "2000"   (or however many total records you have)

4. The _load_subform_details() cache TTL is 900s — keep it, it's correct.

That's it. No Zoho-side changes needed.
""")
else:
    print("""
⚠️  Costed records found BUT sub-form arrays are still empty in detail.

This means Zoho Creator is not exposing line-item rows via the report's
/report/{ID} endpoint even for records that have cost data entered.

REQUIRED: Create two dedicated sub-form reports in Zoho Creator.

STEPS (5 minutes):
  1. Zoho Creator → your app → Reports → + Add Report
     Name  : Chemical_Lines_Report
     Source: your Production Entry form
     In the column picker, expand "Total Chemical Cost" sub-form section
     Add columns: Chemical, Quantity_in_grams, Rate_per_Kg, Cost, Percentage
     Also add the parent form's ID as a lookup column (so we can join back)
     Save & publish.

  2. Repeat → Name: Dye_Lines_Report
     Source: same form, expand "Dye Cost" sub-form
     Add: Dye, Quantity_in_grams, Rate_per_Kg, Cost, Percentage + parent ID
     Save & publish.

  3. Add to .streamlit/secrets.toml:
       chem_report_name = "Chemical_Lines_Report"
       dye_report_name  = "Dye_Lines_Report"

  4. Run this script again — it will confirm the rows come through.
  5. Share the output and the dashboard will be updated to use those reports.
""")

print("=" * 65)