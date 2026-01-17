#!/usr/bin/env python3
import csv
import os
import sys
from datetime import date, timedelta

try:
    from google_auth_oauthlib.flow import InstalledAppFlow
    from google.auth.transport.requests import Request
    from google.oauth2 import service_account
except Exception:
    print("Missing deps. Install with: pip install google-auth-oauthlib requests", file=sys.stderr)
    raise
import json
import urllib.request
import urllib.error
import urllib.parse

SCOPES = ["https://www.googleapis.com/auth/webmasters.readonly"]


def get_dates():
    # Default to last 90 days
    end = date.today() - timedelta(days=1)
    start = end - timedelta(days=89)
    return start.isoformat(), end.isoformat()


def main():
    site_url = os.environ.get("GSC_SITE_URL")
    if not site_url:
        print("Set GSC_SITE_URL to your Search Console property URL.", file=sys.stderr)
        sys.exit(1)

    start_date = os.environ.get("GSC_START_DATE")
    end_date = os.environ.get("GSC_END_DATE")
    if not (start_date and end_date):
        start_date, end_date = get_dates()

    sa_file = os.environ.get("GSC_SERVICE_ACCOUNT_FILE")
    if sa_file:
        if not os.path.exists(sa_file):
            print(f"Service account key not found at: {sa_file}", file=sys.stderr)
            sys.exit(1)
        creds = service_account.Credentials.from_service_account_file(sa_file, scopes=SCOPES)
    else:
        client_secret = os.environ.get("GSC_CLIENT_SECRET_FILE", "client_secret.json")
        if not os.path.exists(client_secret):
            print(f"OAuth client secret not found at: {client_secret}", file=sys.stderr)
            print("Download an OAuth client JSON and set GSC_CLIENT_SECRET_FILE.", file=sys.stderr)
            sys.exit(1)
        flow = InstalledAppFlow.from_client_secrets_file(client_secret, SCOPES)
        auth_mode = os.environ.get("GSC_AUTH_MODE", "local")
        if auth_mode == "console":
            auth_url, _ = flow.authorization_url(access_type="offline", prompt="consent")
            print("Authorize this app by visiting this URL:", file=sys.stderr)
            print(auth_url, file=sys.stderr)
            code = os.environ.get("GSC_AUTH_CODE")
            if not code:
                code = input("Paste the code parameter from the redirect URL: ").strip()
            flow.fetch_token(code=code)
            creds = flow.credentials
        else:
            port = int(os.environ.get("GSC_LOCAL_PORT", "8080"))
            print(f"Starting local OAuth server on http://localhost:{port}/", file=sys.stderr)
            creds = flow.run_local_server(port=port, open_browser=False)

    dimensions_raw = os.environ.get("GSC_DIMENSIONS", "query,page")
    dimensions = [d.strip() for d in dimensions_raw.split(",") if d.strip()]
    if not dimensions:
        print("GSC_DIMENSIONS is empty. Provide at least one dimension.", file=sys.stderr)
        sys.exit(1)

    request = {
        "startDate": start_date,
        "endDate": end_date,
        "dimensions": dimensions,
        "rowLimit": 25000,
    }

    out_path = os.environ.get("GSC_OUT", "gsc_queries_pages.csv")
    rows = []

    if not creds.valid:
        creds.refresh(Request())

    endpoint = "https://www.googleapis.com/webmasters/v3/sites/{}/searchAnalytics/query".format(
        urllib.parse.quote(site_url, safe="")
    )
    data = json.dumps(request).encode("utf-8")
    req = urllib.request.Request(
        endpoint,
        data=data,
        headers={
            "Authorization": f"Bearer {creds.token}",
            "Content-Type": "application/json",
        },
        method="POST",
    )
    try:
        with urllib.request.urlopen(req) as resp:
            payload = resp.read().decode("utf-8")
    except urllib.error.HTTPError as e:
        payload = e.read().decode("utf-8", errors="replace")
        print(f"HTTP {e.code}: {payload}", file=sys.stderr)
        raise

    response = json.loads(payload)
    for row in response.get("rows", []):
        keys = row.get("keys", [])
        entry = {dim: (keys[i] if i < len(keys) else "") for i, dim in enumerate(dimensions)}
        entry.update({
            "clicks": row.get("clicks", 0),
            "impressions": row.get("impressions", 0),
            "ctr": row.get("ctr", 0),
            "position": row.get("position", 0),
        })
        rows.append(entry)

    with open(out_path, "w", newline="", encoding="utf-8") as f:
        fieldnames = [*dimensions, "clicks", "impressions", "ctr", "position"]
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)

    print(f"Wrote {len(rows)} rows to {out_path}")


if __name__ == "__main__":
    main()
