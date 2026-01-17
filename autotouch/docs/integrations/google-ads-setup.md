# Google Ads API access (Autotouch)

This doc is the canonical setup guide for Google Ads API access. It replaces the old access notes that lived under `ads/`.

## Overview
We use Google Ads API via **Application Default Credentials (ADC)** on this machine. The setup relies on:
- gcloud installed locally
- a dedicated GCP quota project
- Google Ads developer token
- MCC (manager) login customer ID

## Required IDs / tokens
- `GOOGLE_ADS_DEVELOPER_TOKEN` (from Google Ads API Center)
- `GOOGLE_ADS_LOGIN_CUSTOMER_ID` (MCC/manager ID, no dashes)
- `GOOGLE_ADS_CUSTOMER_ID` (client account ID, no dashes)

## 1) Install gcloud (macOS)
```bash
curl -s https://sdk.cloud.google.com | bash
```

Reload your shell:
```bash
source "$HOME/google-cloud-sdk/path.zsh.inc"
```

## 2) Login (project admin)
```bash
gcloud auth login
```

## 3) Create a dedicated quota project
```bash
gcloud projects create autotouch-ads
```

Enable the Google Ads API:
```bash
gcloud services enable googleads.googleapis.com --project autotouch-ads
```

## 4) Create ADC credentials (the auth that scripts use)
```bash
gcloud auth application-default login --no-launch-browser \
  --scopes https://www.googleapis.com/auth/adwords,https://www.googleapis.com/auth/cloud-platform
```

Set the ADC quota project:
```bash
gcloud auth application-default set-quota-project autotouch-ads
```

ADC credentials are stored here (treat as a secret):
- `~/.config/gcloud/application_default_credentials.json`

## 5) Install Python dependency
```bash
python3 -m pip install --user google-ads
```

## 6) Sanity check
Use the included script:
```bash
GOOGLE_ADS_DEVELOPER_TOKEN="***" \
GOOGLE_ADS_LOGIN_CUSTOMER_ID="4420697458" \
GOOGLE_ADS_CUSTOMER_ID="6407135192" \
python3 ads/google_ads_adc_test.py
```

Expected output includes `customers/<client>` and `customers/<manager>`.

## Common errors
- `gcloud: command not found`
  - Use `~/google-cloud-sdk/bin/gcloud` or `source "$HOME/google-cloud-sdk/path.zsh.inc"`.
- `requires a quota project`
  - Run: `gcloud auth application-default set-quota-project autotouch-ads`.
- `User doesn't have permission... login-customer-id`
  - Ensure `GOOGLE_ADS_LOGIN_CUSTOMER_ID` is the manager (MCC) ID.
- `DEVELOPER_TOKEN_NOT_APPROVED` / test-only token
  - Keyword Planner metrics are blocked until Basic/Standard access is approved.

## Security notes
- Never commit tokens or client secrets.
- The ADC JSON is sensitive; keep it local.
