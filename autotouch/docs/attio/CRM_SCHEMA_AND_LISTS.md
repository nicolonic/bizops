# Attio CRM schema and list usage (Autotouch)

This doc describes our current Attio object schema, how to view it, and how to update it safely.

## Environment setup
- API key is stored in `/.env` as `ATTIO_API_KEY`.
- Load it for your shell session:

```bash
set -a; source .env; set +a
```

## Objects in our workspace
List objects (standard + custom):

```bash
curl -s -H "Authorization: Bearer $ATTIO_API_KEY" \
  -H "Content-Type: application/json" \
  https://api.attio.com/v2/objects | jq -r '.data[] | [.api_slug,.singular_noun,.plural_noun,.created_at] | @tsv'
```

Common objects we use: `people`, `companies`, `deals`.

## People object (key fields)
System fields:
- `name` (personal-name)
- `email_addresses` (email-address, unique, multiselect)
- `company` (record-reference -> companies)
- `job_title` (text)
- `phone_numbers` (phone-number, multiselect)
- `primary_location` (location)
- `description` (text)

Attribution fields (current):
- `acquisition_direction` (select): Inbound, Outbound
- `acquisition_channel` (select): Email, Paid Search, Organic Search, Referral, Partner, Event, Social, Content, Direct, Other
- `source_detail` (text)
- `campaign` (text)
- `last_outbound_date` (date)
- `utm_source`, `utm_medium`, `utm_campaign`, `utm_content`, `utm_term` (text)

Legacy/older attribution fields (still present but redundant):
- `inbound_channel` (select)
- `source` (text)
- `first_attribution` (text)
- `outbound_campaign` (text)

## Companies object (key fields)
System fields:
- `name` (text)
- `domains` (domain, unique, multiselect)
- `primary_location` (location)
- `description` (text)
- `categories` (select, multiselect)
- `employee_range` (select)
- `estimated_arr_usd` (select)
- `funding_raised_usd` (currency)
- `linkedin` (text), `twitter` (text)

Attribution fields (current):
- `acquisition_direction` (select): Inbound, Outbound
- `acquisition_channel` (select): Email, Paid Search, Organic Search, Referral, Partner, Event, Social, Content, Direct, Other
- `source_detail` (text)
- `campaign` (text)

Legacy/older attribution fields (still present but redundant):
- `initial_channel` (select)

## How to view schema (attributes)
People attributes:
```bash
curl -s -H "Authorization: Bearer $ATTIO_API_KEY" \
  -H "Content-Type: application/json" \
  https://api.attio.com/v2/objects/people/attributes \
  | jq -r '.data[] | [.api_slug,.title,.type,.is_required,.is_unique,.is_multiselect] | @tsv' \
  | sort
```

Company attributes:
```bash
curl -s -H "Authorization: Bearer $ATTIO_API_KEY" \
  -H "Content-Type: application/json" \
  https://api.attio.com/v2/objects/companies/attributes \
  | jq -r '.data[] | [.api_slug,.title,.type,.is_required,.is_unique,.is_multiselect] | @tsv' \
  | sort
```

### Select options (example)
```bash
# Replace ATTR_ID with the attribute_id from the attributes list
curl -s -H "Authorization: Bearer $ATTIO_API_KEY" \
  -H "Content-Type: application/json" \
  https://api.attio.com/v2/objects/people/attributes/<ATTR_ID>/options
```

## How to update schema
### Create a new attribute
```bash
curl -s -H "Authorization: Bearer $ATTIO_API_KEY" \
  -H "Content-Type: application/json" \
  -X POST https://api.attio.com/v2/objects/people/attributes \
  -d '{
    "data": {
      "title": "Acquisition Direction",
      "description": "",
      "api_slug": "acquisition_direction",
      "type": "select",
      "is_multiselect": false,
      "is_required": false,
      "is_unique": false,
      "config": {}
    }
  }'
```

### Add options to a select attribute
```bash
ATTR_ID="<attribute_id>"
for opt in "Inbound" "Outbound"; do
  curl -s -H "Authorization: Bearer $ATTIO_API_KEY" \
    -H "Content-Type: application/json" \
    -X POST "https://api.attio.com/v2/objects/people/attributes/$ATTR_ID/options" \
    -d "{\"data\":{\"title\":\"$opt\"}}"
done
```

### Archive an attribute (use after data migration)
```bash
ATTR_ID="<attribute_id>"
curl -s -H "Authorization: Bearer $ATTIO_API_KEY" \
  -H "Content-Type: application/json" \
  -X PATCH "https://api.attio.com/v2/objects/people/attributes/$ATTR_ID" \
  -d '{"data":{"is_archived":true}}'
```

## Lists and views
Attio lists use list entry endpoints. List entries are not the same as object records.

### List lists (metadata)
```bash
curl -s -H "Authorization: Bearer $ATTIO_API_KEY" \
  -H "Content-Type: application/json" \
  https://api.attio.com/v2/lists | jq -r '.data[] | [.id.list_id,.title,.api_slug,.object_slug] | @tsv'
```

### List entries for a list
```bash
LIST_ID="<list_id>"
curl -s -H "Authorization: Bearer $ATTIO_API_KEY" \
  -H "Content-Type: application/json" \
  https://api.attio.com/v2/lists/$LIST_ID/entries \
  | jq -r '.data[] | .id.record_id'
```

### Add a record to a list
```bash
LIST_ID="<list_id>"
RECORD_ID="<record_id>"
OBJECT_SLUG="people" # or companies
curl -s -H "Authorization: Bearer $ATTIO_API_KEY" \
  -H "Content-Type: application/json" \
  -X POST https://api.attio.com/v2/lists/$LIST_ID/entries \
  -d "{\"data\":{\"record_id\":\"$RECORD_ID\",\"object_slug\":\"$OBJECT_SLUG\"}}"
```

## Notes
- Keep `.env` out of version control.
- For selects, you must create the option before you can set it.
- When in doubt, fetch the attribute list and confirm the type before writing values.
