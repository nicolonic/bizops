# GTM + tracking tooling

This repo has two GTM-related areas:
- **Website tracking** (main site): `website/src/utils/tracking.js` + `website/tracking-data-layer.md`
- **Automation scripts** in `gtm/` (jobs + shared utilities)

## GTM setup (API)
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

## GTM jobs (market intel)
The `gtm/jobs/` folder includes scripts that compare job listings from RapidAPI sources.

### Scripts
- `gtm/jobs/compare_sdr_clay_7d.py`
- `gtm/jobs/compare_sdr_clay_24h.py`

Both scripts:
- Load `.env` from repo root
- Query RapidAPI job sources for SDR/BDR roles mentioning "Clay"
- Deduplicate listings and print overlap stats
- Emit sample results to stdout

### Dependencies
These scripts import `shared.integrations.rapidapi.jobs.*`. That package is not in this repo; make sure the `shared` module is available on `PYTHONPATH` before running.

### Run (example)
```bash
python3 gtm/jobs/compare_sdr_clay_7d.py
```

## Shared utilities
- Job title lists: `gtm/shared/job_titles.py`
  - SDR/BDR and AE title variants
  - `to_or_query()` helper builds a query string for RapidAPI filters

## Notes
- If the RapidAPI module changes, update the jobs scripts accordingly.
- Outputs are console-only by default; if you need files, add a CSV export and write to `gtm/jobs/outputs/`.
