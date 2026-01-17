# Ads tooling (Google Ads + Search Console)

This folder documents the ad-related scripts in `ads/` and how to run them.

## Quick links
- Google Ads auth/setup guide: `docs/integrations/google-ads-setup.md`
- Scripts:
  - `ads/google_ads_adc_test.py` — verify ADC auth + list accessible customers
  - `ads/google_ads_keyword_ideas.py` — export keyword ideas + metrics to CSV
  - `ads/gsc_export.py` — export Search Console queries/pages to CSV

## Prereqs (Google Ads API)
Follow `docs/integrations/google-ads-setup.md`. Key points:
- gcloud installed
- Application Default Credentials (ADC) configured
- Dedicated quota project set
- `GOOGLE_ADS_DEVELOPER_TOKEN` available

## Environment variables
Google Ads:
- `GOOGLE_ADS_DEVELOPER_TOKEN`
- `GOOGLE_ADS_LOGIN_CUSTOMER_ID` (MCC / manager ID)
- `GOOGLE_ADS_CUSTOMER_ID` (client account ID)
- `GOOGLE_ADS_API_VERSION` (optional; default in script is `v19`)

Search Console export (`ads/gsc_export.py`):
- `GSC_SITE_URL` (Search Console property URL)
- `GSC_START_DATE`, `GSC_END_DATE` (optional; defaults to last 90 days)
- `GSC_SERVICE_ACCOUNT_FILE` (optional; service account JSON)
- `GSC_CLIENT_SECRET_FILE` (optional; OAuth client JSON, defaults to `client_secret.json`)
- `GSC_AUTH_MODE` (`local` default or `console`)
- `GSC_AUTH_CODE` (only for console auth)
- `GSC_OUT` (output CSV path; default `gsc_queries_pages.csv`)

## Common workflows
### 1) Sanity-check Google Ads API access
```bash
GOOGLE_ADS_DEVELOPER_TOKEN="***" \
GOOGLE_ADS_LOGIN_CUSTOMER_ID="4420697458" \
GOOGLE_ADS_CUSTOMER_ID="6407135192" \
python3 ads/google_ads_adc_test.py
```

### 2) Export keyword ideas
```bash
GOOGLE_ADS_DEVELOPER_TOKEN="***" \
GOOGLE_ADS_LOGIN_CUSTOMER_ID="4420697458" \
GOOGLE_ADS_CUSTOMER_ID="6407135192" \
python3 ads/google_ads_keyword_ideas.py \
  --seed-file ads/keyword_seeds_autotouch.txt \
  --seed-url "https://autotouch.ai/" \
  --out "ads/keyword_ideas_us.csv"
```

### 3) Export Search Console queries + pages
```bash
GSC_SITE_URL="https://www.autotouch.ai/" \
python3 ads/gsc_export.py
```

## Outputs
- Keyword ideas: CSV file from `--out` (default `keyword_ideas.csv`)
- GSC export: CSV file from `GSC_OUT` (default `gsc_queries_pages.csv`)

## Notes
- Keyword Planner requires an approved developer token (Basic/Standard access) for full metrics.
- The Search Console exporter can authenticate via OAuth or service account.
- Keep tokens and JSON credentials out of version control.
