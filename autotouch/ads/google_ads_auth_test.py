#!/usr/bin/env python3
import json
import os
import sys
from pathlib import Path

try:
    from google_auth_oauthlib.flow import InstalledAppFlow
    from google.ads.googleads.client import GoogleAdsClient
except Exception:
    print("Missing deps. Install with: pip install google-auth-oauthlib google-ads", file=sys.stderr)
    raise

SCOPE = ["https://www.googleapis.com/auth/adwords"]


def get_refresh_token(client_secret_path):
    flow = InstalledAppFlow.from_client_secrets_file(client_secret_path, scopes=SCOPE)
    port = int(os.environ.get("GOOGLE_ADS_LOCAL_PORT", "8081"))
    auth_mode = os.environ.get("GOOGLE_ADS_AUTH_MODE", "local")
    flow.redirect_uri = f"http://localhost:{port}/"
    if auth_mode == "console":
        auth_url, _ = flow.authorization_url(access_type="offline", prompt="consent")
        print("Authorize this app by visiting this URL:", file=sys.stderr)
        print(auth_url, file=sys.stderr)
        code = os.environ.get("GOOGLE_ADS_AUTH_CODE")
        if not code:
            code = input("Paste the code parameter from the redirect URL: ").strip()
        flow.fetch_token(code=code)
        creds = flow.credentials
    else:
        print(f"Starting local OAuth server on http://localhost:{port}/", file=sys.stderr)
        creds = flow.run_local_server(port=port, open_browser=False)
    token = creds.refresh_token
    if not token:
        raise RuntimeError("No refresh token returned. Ensure prompt=consent and access_type=offline.")
    return token


def main():
    client_json = os.environ.get("GOOGLE_ADS_OAUTH_CLIENT")
    if not client_json:
        print("Set GOOGLE_ADS_OAUTH_CLIENT to your OAuth client JSON path.", file=sys.stderr)
        sys.exit(1)

    developer_token = os.environ.get("GOOGLE_ADS_DEVELOPER_TOKEN")
    if not developer_token:
        print("Set GOOGLE_ADS_DEVELOPER_TOKEN.", file=sys.stderr)
        sys.exit(1)

    login_customer_id = os.environ.get("GOOGLE_ADS_LOGIN_CUSTOMER_ID")
    customer_id = os.environ.get("GOOGLE_ADS_CUSTOMER_ID")

    refresh_token = os.environ.get("GOOGLE_ADS_REFRESH_TOKEN")
    if not refresh_token:
        refresh_token = get_refresh_token(client_json)
        out_path = os.environ.get("GOOGLE_ADS_REFRESH_TOKEN_PATH")
        if out_path:
            Path(out_path).write_text(refresh_token, encoding="utf-8")
            print(f"Wrote refresh token to {out_path}", file=sys.stderr)

    with open(client_json, "r") as f:
        data = json.load(f)
    if "installed" in data:
        cfg = data["installed"]
    elif "web" in data:
        cfg = data["web"]
    else:
        raise ValueError("Unknown OAuth client format")

    config = {
        "developer_token": developer_token,
        "client_id": cfg["client_id"],
        "client_secret": cfg["client_secret"],
        "refresh_token": refresh_token,
        "use_proto_plus": True,
    }
    if login_customer_id:
        config["login_customer_id"] = login_customer_id

    api_version = os.environ.get("GOOGLE_ADS_API_VERSION", "v19")
    client = GoogleAdsClient.load_from_dict(config, version=api_version)

    customer_service = client.get_service("CustomerService")
    accessible = customer_service.list_accessible_customers()
    print("Accessible customers:")
    for resource_name in accessible.resource_names:
        print(resource_name)

    if customer_id:
        target = f"customers/{customer_id}"
        if target in accessible.resource_names:
            print(f"OK: found {target}")
        else:
            print(f"WARN: {target} not in accessible list")


if __name__ == "__main__":
    main()
