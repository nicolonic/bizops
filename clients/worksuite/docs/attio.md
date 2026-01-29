# Attio (Worksuite) setup

This doc is Worksuite-specific. For general Addio/Attio API patterns, see `../../docs/attio.md`.

## API key
The API key is stored in `clients/worksuite/.env` as `ATTIO_API_KEY`.
```bash
set -a; source clients/worksuite/.env; set +a
```

## Workspace objects (as of 2026-01-21)
`companies`, `deals`, `people`, `customer_requests`.

## Deals: required + key fields
Required fields (per API):
- `name` (Deal name)
- `owner` (Deal owner, actor/workspace member id)
- `stage` (Deal stage)

Commonly used fields:
- `deal_type` (Type)
- `value` (Deal value)
- `opportunity_arr` (Opportunity ARR)
- `expected_close_date` (Expected close date)
- `associated_company` (Associated company)
- `associated_people` (Associated people)

## Companies: key fields used in renewals
- `name` (Company name)
- `record_id` (Company Record ID)
- `term_start_date`, `term_end_date`
- `total_arr_5` (Total ARR)

## Record references in this workspace
- `deals.associated_company` → `companies`
- `deals.associated_people` → `people`
- `companies.associated_deals` → `deals`
- `companies.team` → `people`
- `companies.customer_requests` → `customer_requests`

## Owner lookup (workspace members)
```bash
curl -s -H "Authorization: Bearer $ATTIO_API_KEY" \
  -H "Content-Type: application/json" \
  "https://api.attio.com/v2/workspace_members" | jq -r '.data[] | [.first_name,.last_name,.email_address,.id.workspace_member_id] | @tsv'
```
Example (Worksuite): Diana Upson → `087574ee-a863-4688-886a-6862b2932dab`.

## Renewal import recipe (Jan 2026 workflow)
Source file: `data/Companies - Customers (1).csv`

Filter:
- `Term End Date` within the next 91 days (relative to run date).

Deal field mapping:
- Deal name: `"<Company> - Renewal"` (no date)
- Deal value: `Total ARR`
- Type: `Renewal`
- Stage: `0 - Renewal Initiated`
- Expected close date: `Term End Date`
- Associated company: `Record ID`
- Deal owner: workspace_member_id (e.g., Diana Upson)

Latest output file: `data/renewals_next_91_days.csv`.

## Notes
- Use company Record ID to link deals to accounts.
- If importing new deals, you can’t supply Attio Record IDs; use a unique external ID if you need dedupe.
