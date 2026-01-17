# Attio (Worksuite) quick guide

This project uses the Attio REST API. The API key is stored in `clients/worksuite/.env` as `ATTIO_API_KEY`.

## 1) Load the API key
```bash
set -a; source clients/worksuite/.env; set +a
```

## 2) List objects
```bash
curl -s -H "Authorization: Bearer $ATTIO_API_KEY" \
  -H "Content-Type: application/json" \
  https://api.attio.com/v2/objects | jq -r '.data[] | [.api_slug,.singular_noun,.plural_noun,.created_at] | @tsv'
```

Common objects in this workspace (as of 2026-01-09): `people`, `companies`, `deals`.

## 3) List attributes for an object
```bash
curl -s -H "Authorization: Bearer $ATTIO_API_KEY" \
  -H "Content-Type: application/json" \
  "https://api.attio.com/v2/objects/companies/attributes" | jq -r '.data[] | [.api_slug,.title,.type] | @tsv' | sort
```

## 4) Create a field (attribute)
### Select field (single select)
```bash
curl -s -H "Authorization: Bearer $ATTIO_API_KEY" \
  -H "Content-Type: application/json" \
  -X POST "https://api.attio.com/v2/objects/companies/attributes" \
  -d '{
    "data": {
      "title": "Account Health",
      "description": "",
      "api_slug": "account_health",
      "type": "select",
      "is_multiselect": false,
      "is_required": false,
      "is_unique": false,
      "config": {}
    }
  }'
```

### Currency field
```bash
curl -s -H "Authorization: Bearer $ATTIO_API_KEY" \
  -H "Content-Type: application/json" \
  -X POST "https://api.attio.com/v2/objects/deals/attributes" \
  -d '{
    "data": {
      "title": "Opportunity ARR",
      "description": "",
      "api_slug": "opportunity_arr",
      "type": "currency",
      "is_multiselect": false,
      "is_required": false,
      "is_unique": false,
      "config": {
        "currency": {"default_currency_code": "USD", "display_type": "symbol"}
      }
    }
  }'
```

## 5) Add options to a select field
1) Find the attribute ID:
```bash
curl -s -H "Authorization: Bearer $ATTIO_API_KEY" \
  -H "Content-Type: application/json" \
  "https://api.attio.com/v2/objects/companies/attributes" | jq -r '.data[] | select(.api_slug=="account_health") | .id.attribute_id'
```
2) Add options:
```bash
ATTR_ID="<attribute_id>"
for opt in "Healthy" "At-risk"; do
  curl -s -H "Authorization: Bearer $ATTIO_API_KEY" \
    -H "Content-Type: application/json" \
    -X POST "https://api.attio.com/v2/objects/companies/attributes/$ATTR_ID/options" \
    -d "{\"data\":{\"title\":\"$opt\"}}"
done
```

## 6) Write values to records
### Create a company record
```bash
curl -s -H "Authorization: Bearer $ATTIO_API_KEY" \
  -H "Content-Type: application/json" \
  -X POST "https://api.attio.com/v2/objects/companies/records" \
  -d '{
    "data": {
      "values": {
        "name": "Acme Co",
        "domains": ["acme.com"],
        "account_health": "Healthy",
        "account_priority": "Tier 1"
      }
    }
  }'
```

### Update a deal with currency value
```bash
curl -s -H "Authorization: Bearer $ATTIO_API_KEY" \
  -H "Content-Type: application/json" \
  -X PUT "https://api.attio.com/v2/objects/deals/records/<record_id>" \
  -d '{
    "data": {
      "values": {
        "opportunity_arr": {"value": 120000, "currency": "USD"}
      }
    }
  }'
```

## 7) Useful quick checks
- **Required fields**:
```bash
curl -s -H "Authorization: Bearer $ATTIO_API_KEY" \
  -H "Content-Type: application/json" \
  "https://api.attio.com/v2/objects/deals/attributes" | jq -r '.data[] | select(.is_required==true) | .api_slug'
```
- **Unique fields**:
```bash
curl -s -H "Authorization: Bearer $ATTIO_API_KEY" \
  -H "Content-Type: application/json" \
  "https://api.attio.com/v2/objects/companies/attributes" | jq -r '.data[] | select(.is_unique==true) | .api_slug'
```

## Notes
- Keep `.env` out of version control.
- For list-specific fields, use list entry endpoints instead of object records.
- When adding a new select option, you must create the option first or the value will be rejected.
