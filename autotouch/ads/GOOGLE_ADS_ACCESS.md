# Google Ads API access (working setup)

This folder contains scripts for interacting with the Google Ads API.

The setup below is the path that finally worked reliably on this machine:
- **Google Cloud CLI (gcloud)** installed locally
- **Application Default Credentials (ADC)** for auth
- A dedicated **quota project** (so we don’t depend on other projects’ billing/quota state)

## What you need

- A **Google Ads Manager Account (MCC)** with API access
- A **Google Ads developer token**
  - Note: if the token is *test-only*, some APIs (notably Keyword Planner / keyword idea metrics) will be blocked until you’re approved for Basic/Standard access.
- IDs (remove dashes):
  - `GOOGLE_ADS_LOGIN_CUSTOMER_ID` = manager/MCC customer ID (e.g. `4420697458`)
  - `GOOGLE_ADS_CUSTOMER_ID` = client customer ID you want to query (e.g. `6407135192`)

## 1) Install gcloud (macOS)

If `gcloud` isn’t installed:

```bash
curl -s https://sdk.cloud.google.com | bash
```

Then either:
- start a new terminal, or
- load gcloud into your shell:

```bash
source "$HOME/google-cloud-sdk/path.zsh.inc"
```

If you don’t want to touch PATH, you can always run gcloud via:

```bash
~/google-cloud-sdk/bin/gcloud ...
```

## 2) Authenticate gcloud (for project/service management)

To create projects / enable APIs you need a gcloud user session:

```bash
~/google-cloud-sdk/bin/gcloud auth login
```

Optional: list projects to confirm you’re logged in:

```bash
~/google-cloud-sdk/bin/gcloud projects list --format='table(projectId,name)'
```

## 3) Create a dedicated quota project (recommended)

We created a dedicated project for Ads API quota/billing isolation:

```bash
~/google-cloud-sdk/bin/gcloud projects create autotouch-ads
```

Enable the Google Ads API on that project:

```bash
~/google-cloud-sdk/bin/gcloud services enable googleads.googleapis.com --project autotouch-ads
```

Notes:
- This “quota project” is **not** your Google Ads spend. It’s just the GCP project used for API quota/billing metadata.
- If you just created the project, some APIs can take a few minutes to recognize it; retry after ~5–10 minutes if you see “project not found” style errors.

## 4) Create ADC credentials (the auth that scripts use)

Run ADC login with the Ads scope (and cloud-platform is fine to include):

```bash
~/google-cloud-sdk/bin/gcloud auth application-default login --no-launch-browser \
  --scopes https://www.googleapis.com/auth/adwords,https://www.googleapis.com/auth/cloud-platform
```

Follow the URL, approve, and paste the verification code back into the terminal.

This will write credentials to:
- `~/.config/gcloud/application_default_credentials.json` (treat as a secret)

### Set the ADC quota project (required by Google Ads API)

```bash
~/google-cloud-sdk/bin/gcloud auth application-default set-quota-project autotouch-ads
```

If you skip this, you’ll get an error that the API “requires a quota project”.

## 5) Install Python dependencies

Use a modern Python (3.10+ recommended). Then:

```bash
python3 -m pip install --user google-ads
```

## 6) Sanity check: list accessible customers

Run the included test script:

```bash
GOOGLE_ADS_DEVELOPER_TOKEN="***" \
GOOGLE_ADS_LOGIN_CUSTOMER_ID="4420697458" \
GOOGLE_ADS_CUSTOMER_ID="6407135192" \
python3 autotouch/ads/google_ads_adc_test.py
```

Expected output includes `customers/<client>` and `customers/<manager>`.

## Common errors / fixes

### `gcloud: command not found`
- Use `~/google-cloud-sdk/bin/gcloud` or `source "$HOME/google-cloud-sdk/path.zsh.inc"`.

### `parse error near '&'`
- You pasted an OAuth URL into the shell. Open OAuth URLs in a browser instead.

### `requires a quota project`
- Run:
  - `~/google-cloud-sdk/bin/gcloud auth application-default set-quota-project <PROJECT_ID>`

### `User doesn't have permission... login-customer-id`
- Ensure `GOOGLE_ADS_LOGIN_CUSTOMER_ID` is your **manager** ID (no dashes).

### `DEVELOPER_TOKEN_NOT_APPROVED` / “token is only approved for test accounts”
- You can authenticate, but many endpoints (including keyword planning metrics) will be blocked.
- Fix: apply for Basic/Standard access for the developer token in the Google Ads API Center and provide the required tool documentation.

## Keyword idea exporter (once token is approved)

- Seeds live in `autotouch/ads/keyword_seeds_autotouch.txt`
- Export script: `autotouch/ads/google_ads_keyword_ideas.py`

Example:

```bash
GOOGLE_ADS_DEVELOPER_TOKEN="***" \
GOOGLE_ADS_LOGIN_CUSTOMER_ID="4420697458" \
GOOGLE_ADS_CUSTOMER_ID="6407135192" \
python3 autotouch/ads/google_ads_keyword_ideas.py \
  --seed-file autotouch/ads/keyword_seeds_autotouch.txt \
  --seed-url "https://autotouch.ai/" \
  --out "autotouch/ads/keyword_ideas_us.csv"
```
