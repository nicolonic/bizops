# SEO

This directory documents how to review SEO performance (Search Console) and how to use SERPER for SERP research.

Artifacts and weekly reports live in `seo/`. Start there if you want the LLM kickoff flow:
- `seo/README.md`

## Reporting cadence
- Weekly (every Friday or Monday): run the weekly report for the prior 7 days.
- Monthly (first week of the month): review index coverage, Core Web Vitals, and crawl stats.

## Search Console (GSC)

### Quick facts
- The service account already has access to the **domain property**: `sc-domain:autotouch.ai`.
- Credentials live in `configs/` (do not commit new keys):
  - Service account key: `configs/autotouchai-05f671345e58.json`
  - OAuth client: `configs/client_secret_927405040806-dsuaks3ridgd3nisv67r7nr0np3krujn.apps.googleusercontent.com.json`
- Export script: `ads/gsc_export.py`

### Verify access (service account)
This lists the Search Console properties the service account can access:
```bash
SSL_CERT_FILE="$(python3 - <<'PY'
import certifi; print(certifi.where())
PY
)" \
python3 - <<'PY'
import urllib.request
from google.oauth2 import service_account
from google.auth.transport.requests import Request

sa_file = "configs/autotouchai-05f671345e58.json"
scopes = ["https://www.googleapis.com/auth/webmasters.readonly"]
creds = service_account.Credentials.from_service_account_file(sa_file, scopes=scopes)
creds.refresh(Request())
req = urllib.request.Request(
    "https://www.googleapis.com/webmasters/v3/sites",
    headers={"Authorization": f"Bearer {creds.token}"},
)
with urllib.request.urlopen(req) as resp:
    print(resp.read().decode("utf-8"))
PY
```

### Export the last 7 days (queries + pages)
By default, `ads/gsc_export.py` exports the last 90 days. For weekly review, pass explicit dates:
```bash
SSL_CERT_FILE="$(python3 - <<'PY'
import certifi; print(certifi.where())
PY
)" \
GSC_SITE_URL="sc-domain:autotouch.ai" \
GSC_START_DATE="2026-01-09" \
GSC_END_DATE="2026-01-15" \
GSC_SERVICE_ACCOUNT_FILE="configs/autotouchai-05f671345e58.json" \
GSC_DIMENSIONS="query,page" \
GSC_OUT="/tmp/gsc_current.csv" \
python3 ads/gsc_export.py
```

### Export the previous 7 days (for week-over-week)
```bash
SSL_CERT_FILE="$(python3 - <<'PY'
import certifi; print(certifi.where())
PY
)" \
GSC_SITE_URL="sc-domain:autotouch.ai" \
GSC_START_DATE="2026-01-02" \
GSC_END_DATE="2026-01-08" \
GSC_SERVICE_ACCOUNT_FILE="configs/autotouchai-05f671345e58.json" \
GSC_DIMENSIONS="query,page" \
GSC_OUT="/tmp/gsc_previous.csv" \
python3 ads/gsc_export.py
```

### Weekly exports (recommended dimensions)
Run these in addition to `query,page` so we can roll up by page, query, device, and country.
Use the same `SSL_CERT_FILE`, `GSC_SITE_URL`, `GSC_START_DATE`, `GSC_END_DATE`, and `GSC_SERVICE_ACCOUNT_FILE` values as above.
```bash
# Pages only
GSC_DIMENSIONS="page" GSC_OUT="/tmp/gsc_pages.csv" python3 ads/gsc_export.py

# Queries only
GSC_DIMENSIONS="query" GSC_OUT="/tmp/gsc_queries.csv" python3 ads/gsc_export.py

# Device
GSC_DIMENSIONS="device" GSC_OUT="/tmp/gsc_device.csv" python3 ads/gsc_export.py

# Country
GSC_DIMENSIONS="country" GSC_OUT="/tmp/gsc_country.csv" python3 ads/gsc_export.py
```

### Where to store snapshots
Primary location for raw exports:
- `seo/data/gsc/`

If you need a snapshot for the website docs, copy the latest export to:
- `website/data/Autotouch - Search Console Rankings.csv`

When you update the snapshot, overwrite that file with the latest export (keep header row intact). See `website/docs/website-structure.md` for context.

### Troubleshooting
- **SSL CERTIFICATE_VERIFY_FAILED** on macOS: set `SSL_CERT_FILE` to the `certifi` path (as in the examples above).
- **403 Forbidden**: the account/service account doesn’t have access to the property. For domain properties, make sure the service account is added in Search Console with at least Read access.

## SERPER (SERP research)

The SERPER API key is stored in `/Users/nicolo/Projects/bizops/.env` as `SERPER_API_KEY`.

### Quick lookup (top 5 organic results)
```bash
python3 - <<'PY'
import json
import urllib.request
from pathlib import Path

key = None
for line in Path('/Users/nicolo/Projects/bizops/.env').read_text().splitlines():
    if line.strip().startswith('SERPER_API_KEY='):
        key = line.split('=',1)[1].strip().strip('"').strip("'")
        break

query = "exa vs clay"

req = urllib.request.Request(
    'https://google.serper.dev/search',
    data=json.dumps({"q": query, "gl": "us", "hl": "en"}).encode('utf-8'),
    headers={'X-API-KEY': key, 'Content-Type': 'application/json'},
    method='POST'
)

with urllib.request.urlopen(req) as resp:
    payload = json.loads(resp.read().decode('utf-8'))

for r in payload.get('organic', [])[:5]:
    print(f"{r.get('position')}. {r.get('title')} — {r.get('link')}")
PY
```

### Batch lookup (write to JSON)
```bash
python3 - <<'PY'
import json
import urllib.request
from pathlib import Path

key = None
for line in Path('/Users/nicolo/Projects/bizops/.env').read_text().splitlines():
    if line.strip().startswith('SERPER_API_KEY='):
        key = line.split('=',1)[1].strip().strip('"').strip("'")
        break

queries = [
    "exa vs clay",
    "top 10 best ai agents 2024",
    "name2email vs swordfish",
]

results = {}
for q in queries:
    req = urllib.request.Request(
        'https://google.serper.dev/search',
        data=json.dumps({"q": q, "gl": "us", "hl": "en"}).encode('utf-8'),
        headers={'X-API-KEY': key, 'Content-Type': 'application/json'},
        method='POST'
    )
    with urllib.request.urlopen(req) as resp:
        payload = json.loads(resp.read().decode('utf-8'))
    results[q] = [
        {
            'title': r.get('title'),
            'link': r.get('link'),
            'snippet': r.get('snippet'),
            'position': r.get('position'),
        }
        for r in payload.get('organic', [])[:5]
    ]

Path('/tmp/serper_results.json').write_text(json.dumps(results, indent=2))
print('wrote /tmp/serper_results.json')
PY
```

### Notes
- SERPER queries are location/language dependent. Use `gl` and `hl` explicitly.
- Avoid checking in SERPER output (it can include competitor content snippets).
