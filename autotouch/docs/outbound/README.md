# Outbound tooling

This repo has two related areas:
- **Website tracking (GTM)** lives under `website/` (see links below).
- **Outbound automation scripts** in `outbound/` (jobs + shared utilities).

## Tracking setup (GTM API)
For programmatic changes to the GTM container, use the GTM API setup documented in:
- `website/docs/gtm-api-setup.md`

That doc includes:
- OAuth setup
- Token cache location
- Account/container IDs
- Listing tags/triggers/variables
- Publish flow

## Event schema (data layer)
The canonical data layer spec is in:
- `website/tracking-data-layer.md`

When adding new events or parameters, update that doc and keep names `snake_case`.

## Outbound jobs (market intel)
The `outbound/jobs/` folder includes scripts that compare job listings from RapidAPI sources.

### Scripts
- `outbound/jobs/compare_sdr_clay_7d.py`
- `outbound/jobs/compare_sdr_clay_24h.py`
- `outbound/jobs/send_sdr_webhook.py` (fetch SDR jobs + send to table webhook)

Both scripts:
- Load `.env` from repo root
- Query RapidAPI job sources for SDR/BDR roles mentioning a keyword (currently "Clay")
- Deduplicate listings and print overlap stats
- Emit sample results to stdout

### Dependencies
These scripts import `shared.integrations.rapidapi.jobs.*`. That package is not in this repo; make sure the `shared` module is available on `PYTHONPATH` before running.

### Run (example)
```bash
python3 outbound/jobs/compare_sdr_clay_7d.py
```

### Webhook export (table ingest)
`send_sdr_webhook.py` can push records into the Autotouch table webhook.

Required env:
- `AUTOTOUCH_TABLE_WEBHOOK_TOKEN` (X-Autotouch-Token header)
Optional:
- `AUTOTOUCH_TABLE_WEBHOOK_URL` (defaults to the current table ingest URL)

Examples:
```bash
# SDR/BDR roles at companies <= 25 employees (last 24h)
python3 outbound/jobs/send_sdr_webhook.py --window 24h --employees-lte 25

# SDR/BDR roles mentioning Clay or Apollo (last 24h)
python3 outbound/jobs/send_sdr_webhook.py --window 24h --keywords Clay Apollo

# Last 7 days with both filters
python3 outbound/jobs/send_sdr_webhook.py --window 7d --employees-lte 25 --keywords Clay Apollo
```

## Shared utilities
- Job title lists: `outbound/shared/job_titles.py`
  - SDR/BDR and AE title variants
  - `to_or_query()` helper builds a query string for RapidAPI filters

## Notes
- If the RapidAPI module changes, update the jobs scripts accordingly.
- Outputs are console-only by default; if you need files, add a CSV export and write to `outbound/jobs/outputs/`.
