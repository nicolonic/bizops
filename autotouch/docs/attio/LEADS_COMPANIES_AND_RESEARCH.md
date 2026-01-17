# Adding leads and companies + research/field fill guide

This doc covers how to add leads (people) and companies, how to link them, and how to enrich records with research and attribution.

## Recommended flow
1) Check if the company exists (by domain).
2) Create or update the company record.
3) Check if the person exists (by email).
4) Create or update the person record, link to company.
5) Add a follow-up task if needed.

## 1) Find or create a company
Query by domain:
```bash
DOMAIN="outlierjets.com"
curl -s -H "Authorization: Bearer $ATTIO_API_KEY" \
  -H "Content-Type: application/json" \
  -X POST https://api.attio.com/v2/objects/companies/records/query \
  -d "{\"filter\":{\"domains\":\"$DOMAIN\"},\"limit\":1}"
```

Create a company (example):
```bash
curl -s -H "Authorization: Bearer $ATTIO_API_KEY" \
  -H "Content-Type: application/json" \
  -X POST https://api.attio.com/v2/objects/companies/records \
  -d '{
    "data": {
      "values": {
        "name": "Outlier Jets",
        "domains": ["outlierjets.com"],
        "description": "Private aviation services including fixed-rate jet cards and on-demand charter.",
        "acquisition_direction": "Outbound",
        "acquisition_channel": "Email",
        "source_detail": "Outbound email sequencing",
        "campaign": "SMB <20 employees, >=2 sales reps"
      }
    }
  }'
```

## 2) Find or create a person (lead)
Query by email:
```bash
EMAIL="patrick.hill@outlierjets.com"
curl -s -H "Authorization: Bearer $ATTIO_API_KEY" \
  -H "Content-Type: application/json" \
  -X POST https://api.attio.com/v2/objects/people/records/query \
  -d "{\"filter\":{\"email_addresses\":\"$EMAIL\"},\"limit\":1}"
```

Create a person and link to company:
```bash
COMPANY_RECORD_ID="<company_record_id>"

curl -s -H "Authorization: Bearer $ATTIO_API_KEY" \
  -H "Content-Type: application/json" \
  -X POST https://api.attio.com/v2/objects/people/records \
  -d "{\"data\":{\"values\":{\
    \"name\":[{\"first_name\":\"Patrick\",\"last_name\":\"Hill\",\"full_name\":\"Patrick Hill\"}],\
    \"email_addresses\":[\"patrick.hill@outlierjets.com\"],\
    \"job_title\":\"VP of Sales\",\
    \"company\":{\"target_object\":\"companies\",\"target_record_id\":\"$COMPANY_RECORD_ID\"},\
    \"description\":\"Requested a meeting next week; no time booked yet.\",\
    \"acquisition_direction\":\"Outbound\",\
    \"acquisition_channel\":\"Email\",\
    \"source_detail\":\"Outbound email sequencing\",\
    \"campaign\":\"SMB <20 employees, >=2 sales reps\",\
    \"last_outbound_date\":\"2026-01-16\"\
  }}}"
```

## 3) Add a follow-up task
```bash
PERSON_RECORD_ID="<person_record_id>"

curl -s -H "Authorization: Bearer $ATTIO_API_KEY" \
  -H "Content-Type: application/json" \
  -X POST https://api.attio.com/v2/tasks \
  -d "{\"data\":{\
    \"content\":\"Schedule intro meeting — requested next week, no time booked yet.\",\
    \"format\":\"plaintext\",\
    \"deadline_at\":\"2026-01-19T18:00:00.000000000Z\",\
    \"is_completed\":false,\
    \"assignees\":[],\
    \"linked_records\":[{\"target_object\":\"people\",\"target_record_id\":\"$PERSON_RECORD_ID\"}]\
  }}"
```

## Attribution standards (new schema)
Use these fields across people and companies:
- `acquisition_direction` (Inbound/Outbound)
- `acquisition_channel` (Email, Paid Search, Organic Search, Referral, Partner, Event, Social, Content, Direct, Other)
- `source_detail` (free text, vendor-agnostic: "Outbound email sequencing")
- `campaign` (free text or select: "Q1 2026 Outbound - SMB")

Avoid putting inbound/outbound inside `acquisition_channel`.

## Research + enrichment guidelines
Use public sources to fill:
- Company description: what they sell + customer type + HQ
- Industry hints for `categories` (if Attio suggests defaults)
- Company size: map to `employee_range` if available
- Person role: job title, seniority
- Website domain and LinkedIn URL

Focus on stable, public facts. Keep `source_detail` vendor-agnostic unless explicitly required.

## Field fill guidance
- If lead came from outbound email:
  - `acquisition_direction`: Outbound
  - `acquisition_channel`: Email
  - `source_detail`: Outbound email sequencing
  - `campaign`: segment or batch name
- If lead came from a demo request form:
  - `acquisition_direction`: Inbound
  - `acquisition_channel`: Content
  - `source_detail`: Demo request
  - `campaign`: any UTM campaign if available
- If lead came from LinkedIn:
  - `acquisition_direction`: Inbound or Outbound (depends on who initiated)
  - `acquisition_channel`: Social
  - `source_detail`: LinkedIn

## Notes
- Prefer linking the person to a company record.
- Use lists for process stages (e.g., "Prospecting", "In pipeline").
- If you need a new select option, create it before writing the value.
