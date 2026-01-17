#!/usr/bin/env python3
import os
import sys

try:
    from google.ads.googleads.client import GoogleAdsClient
except Exception:
    print("Missing deps. Install with: python3 -m pip install --user google-ads", file=sys.stderr)
    raise


def main():
    developer_token = os.environ.get("GOOGLE_ADS_DEVELOPER_TOKEN")
    if not developer_token:
        print("Set GOOGLE_ADS_DEVELOPER_TOKEN.", file=sys.stderr)
        sys.exit(1)

    login_customer_id = os.environ.get("GOOGLE_ADS_LOGIN_CUSTOMER_ID")
    customer_id = os.environ.get("GOOGLE_ADS_CUSTOMER_ID")
    api_version = os.environ.get("GOOGLE_ADS_API_VERSION", "v19")

    config = {
        "developer_token": developer_token,
        "use_proto_plus": True,
        "use_application_default_credentials": True,
    }
    if login_customer_id:
        config["login_customer_id"] = login_customer_id

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
