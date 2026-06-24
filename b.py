"""
zoho_final_probe.py
Confirmed names:
  Form      : Production_Entry_Form
  Chem field: Total_Chemical_Cost
  Dye field : Dye_Cost

Tries every known Zoho Creator v2 URL pattern for fetching a single record
with expanded sub-form rows.
"""
import json, re, sys, requests
from datetime import datetime

FORM_LINK   = "Production_Entry_Form"
CHEM_FIELD  = "Total_Chemical_Cost"
DYE_FIELD   = "Dye_Cost"

def load_secrets(path=".streamlit/secrets.toml"):
    secrets, section = {}, None
    for line in open(path):
        line = line.strip()
        if not line or line.startswith("#"): continue
        m = re.match(r'^\[([^\]]+)\]$', line)
        if m: section = m.group(1); secrets[section] = {}; continue
        m = re.match(r'^([\w]+)\s*=\s*"([^"]*)"', line)
        if m and section: secrets[section][m.group(1)] = m.group(2)
    return secrets

cfg = load_secrets().get("zoho_creator", {})
owner, app = cfg["account_owner"], cfg["app_name"]
REPORT_BASE = f"https://creator.zoho.com/api/v2/{owner}/{app}/report/{cfg['report_name']}"

def get_token():
    r = requests.post("https://accounts.zoho.com/oauth/v2/token", params={
        "refresh_token": cfg["refresh_token"], "client_id": cfg["client_id"],
        "client_secret": cfg["client_secret"], "grant_type": "refresh_token",
    }, timeout=15)
    d = r.json()
    if "access_token" not in d: raise RuntimeError(str(d))
    return d["access_token"]

def dv(v):
    if isinstance(v, dict): return v.get("display_value") or v.get("value") or str(v)
    return str(v) if v else ""

def has_cost(rec):
    for k in ("Total_Cost","Total_Chemical_Cost","Total_Chemical_Cost1","Total_Dye_Cost"):
        try:
            if float(str(rec.get(k,"") or "0").replace(",","")) > 0: return True
        except: pass
    return False

def flatten(item):
    if not isinstance(item, dict): return {}
    zc = item.get("zc_display_value")
    if isinstance(zc, dict) and zc:
        return {k: dv(v) for k, v in zc.items()}
    keys = [k for k in item if k not in ("display_value","zc_display_value","id","ID")]
    if len(keys) > 1:
        return {k: dv(item[k]) for k in keys}
    return {}   # stub

# ── get token + costed record ────────────────────────────────────────────────
print("="*65)
print("  Zoho Final Sub-Form Probe")
print(f"  {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
print("="*65)

token   = get_token()
headers = {"Authorization": f"Zoho-oauthtoken {token}"}
print("✅  Token OK")

r = requests.get(REPORT_BASE, headers=headers,
                 params={"from":0,"limit":200,"field_config":"all"}, timeout=20)
r.raise_for_status()
costed = [rec for rec in r.json().get("data",[]) if has_cost(rec)]
if not costed:
    print("❌  No costed records found"); sys.exit(1)
rid = costed[0].get("ID")
print(f"✅  Costed record: {rid}  LOT={dv(costed[0].get('LOT_NO','?'))}")

# ── try every known URL pattern ──────────────────────────────────────────────
patterns = [
    # v2 form record endpoint variants
    f"https://creator.zoho.com/api/v2/{owner}/{app}/form/{FORM_LINK}/record/{rid}",
    f"https://creator.zoho.com/api/v2/{owner}/{app}/form/{FORM_LINK}/{rid}",
    # v2.1
    f"https://creator.zoho.com/api/v2.1/{owner}/{app}/form/{FORM_LINK}/record/{rid}",
    f"https://creator.zoho.com/api/v2.1/{owner}/{app}/report/{cfg['report_name']}/{rid}",
    # report detail with different field_config values
    f"REPORT_DETAIL|field_config=all",
    f"REPORT_DETAIL|field_config=detail",
    f"REPORT_DETAIL|field_config=subform",
    f"REPORT_DETAIL|no_param",
]

print(f"\nTrying {len(patterns)} URL patterns for record {rid} …\n")

working = None
for pattern in patterns:
    # special handling for report detail variants
    if pattern.startswith("REPORT_DETAIL"):
        variant = pattern.split("|")[1]
        url = f"{REPORT_BASE}/{rid}"
        if variant == "no_param":
            params = {}
        elif variant == "field_config=subform":
            params = {"field_config": "subform"}
        else:
            params = {"field_config": variant.split("=")[1]}
    else:
        url    = pattern
        params = {"field_config": "all"}

    try:
        resp = requests.get(url, headers=headers, params=params, timeout=15)
        data = resp.json()

        if resp.status_code != 200:
            print(f"  ✗  [{resp.status_code}] {url}")
            print(f"       {str(data)[:120]}")
            continue

        rec_data = data.get("data", {})
        if not rec_data:
            print(f"  ✗  [200 empty] {url}")
            continue

        # Check if sub-form fields are expanded
        chem = rec_data.get(CHEM_FIELD, [])
        dye  = rec_data.get(DYE_FIELD,  [])
        chem_expanded = any(flatten(i) for i in chem) if isinstance(chem, list) else False
        dye_expanded  = any(flatten(i) for i in dye)  if isinstance(dye,  list) else False

        status = "✅ EXPANDED" if (chem_expanded or dye_expanded) else "⚠️  stubs/empty"
        print(f"  {status} [{resp.status_code}] {url}")
        if params: print(f"       params={params}")
        print(f"       {CHEM_FIELD}: {len(chem) if isinstance(chem,list) else 'not-list'} rows  "
              f"expanded={chem_expanded}   "
              f"{DYE_FIELD}: {len(dye) if isinstance(dye,list) else 'not-list'} rows  "
              f"expanded={dye_expanded}")

        if chem_expanded or dye_expanded:
            working = (url, params, rec_data)
            print(f"\n  🎯  WORKING URL FOUND — stopping search")
            break

    except Exception as e:
        print(f"  ✗  exception: {url}  →  {e}")

# ── print expanded rows if found ─────────────────────────────────────────────
if working:
    url, params, rec_data = working
    chem_rows = rec_data.get(CHEM_FIELD, [])
    dye_rows  = rec_data.get(DYE_FIELD,  [])

    print(f"\n{'='*65}")
    print(f"  EXPANDED SUB-FORM DATA")
    print(f"{'='*65}")

    print(f"\n  Chemical rows ({len(chem_rows)}):")
    for i, row in enumerate(chem_rows):
        f = flatten(row)
        if f: print(f"    {i+1}: {json.dumps(f, default=str)}")
        else: print(f"    {i+1}: stub → {row}")

    print(f"\n  Dye rows ({len(dye_rows)}):")
    for i, row in enumerate(dye_rows):
        f = flatten(row)
        if f: print(f"    {i+1}: {json.dumps(f, default=str)}")
        else: print(f"    {i+1}: stub → {row}")

    with open("zoho_expanded_subforms.json", "w") as f:
        json.dump({"url": url, "params": params, "data": rec_data}, f, indent=2, default=str)
    print(f"\n  Saved → zoho_expanded_subforms.json")

    print(f"""
{'='*65}
  DASHBOARD FIX SUMMARY
{'='*65}
  Working URL pattern : {url.replace(str(rid), '{record_id}')}
  Params              : {params}
  Chemical field      : {CHEM_FIELD}
  Dye field           : {DYE_FIELD}

  → Share this output. The dashboard _fetch_record_detail() function
    will be patched to use this URL pattern.
""")

else:
    print(f"""
{'='*65}
  ALL URL PATTERNS FAILED — Sub-forms are NOT accessible via API
{'='*65}

  The only remaining option is to create two dedicated reports in
  Zoho Creator — one per sub-form, with one row per line item.

  STEPS:
  1. Zoho Creator → your app → Reports → + Add Report
     Name        : Chemical_Lines_Report
     Source form : Production Entry Form
     In columns, expand 'Total Chemical Cost' sub-form → add all fields
     Also add parent record ID as a column for joining
     Save & note the Report Link Name

  2. Repeat for dyes:
     Name        : Dye_Lines_Report
     Source form : Production Entry Form  
     Expand 'Dye Cost' sub-form → add all fields + parent ID
     Save & note the Report Link Name

  3. Add to secrets.toml:
       chem_report_name = "Chemical_Lines_Report"   (use actual link name)
       dye_report_name  = "Dye_Lines_Report"

  4. Share a screenshot of step 1 and I'll build the full fetch logic.
""")