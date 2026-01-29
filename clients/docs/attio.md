# Addio (Attio) API reference

This is a general, cross-client reference for the Attio REST API (often called “Addio” in client notes). Use it for common API patterns. For workspace-specific setup, see each client’s local docs.

## Auth
- API key is stored per client in that client’s `.env` as `ATTIO_API_KEY`.
- Example:
```bash
set -a; source /path/to/client/.env; set +a
```

## Common API calls
### List objects
```bash
curl -s -H "Authorization: Bearer $ATTIO_API_KEY" \
  -H "Content-Type: application/json" \
  https://api.attio.com/v2/objects | jq -r '.data[] | [.api_slug,.singular_noun,.plural_noun,.created_at] | @tsv'
```

### List attributes for an object
```bash
curl -s -H "Authorization: Bearer $ATTIO_API_KEY" \
  -H "Content-Type: application/json" \
  "https://api.attio.com/v2/objects/companies/attributes" | jq -r '.data[] | [.api_slug,.title,.type] | @tsv' | sort
```

### Create an attribute (field)
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

### Add options to a select attribute
```bash
ATTR_ID="<attribute_id>"
for opt in "Healthy" "At-risk"; do
  curl -s -H "Authorization: Bearer $ATTIO_API_KEY" \
    -H "Content-Type: application/json" \
    -X POST "https://api.attio.com/v2/objects/companies/attributes/$ATTR_ID/options" \
    -d "{\"data\":{\"title\":\"$opt\"}}"
done
```

### Create a record
```bash
curl -s -H "Authorization: Bearer $ATTIO_API_KEY" \
  -H "Content-Type: application/json" \
  -X POST "https://api.attio.com/v2/objects/companies/records" \
  -d '{
    "data": {
      "values": {
        "name": "Acme Co",
        "domains": ["acme.com"]
      }
    }
  }'
```

### Update a record
```bash
curl -s -H "Authorization: Bearer $ATTIO_API_KEY" \
  -H "Content-Type: application/json" \
  -X PUT "https://api.attio.com/v2/objects/deals/records/<record_id>" \
  -d '{
    "data": {
      "values": {
        "value": {"value": 120000, "currency": "USD"}
      }
    }
  }'
```

### List workspace members (for owner assignment)
```bash
curl -s -H "Authorization: Bearer $ATTIO_API_KEY" \
  -H "Content-Type: application/json" \
  "https://api.attio.com/v2/workspace_members" | jq -r '.data[] | [.first_name,.last_name,.email_address,.id.workspace_member_id] | @tsv'
```

## Record references (linking)
- Use record-reference fields to link objects (e.g., deal → company).
- Most CSV imports accept “Associated <object> (Record ID)” columns for linking.

## Import + dedupe tips
- New records do **not** have Attio Record IDs yet.
- To avoid duplicates on import, create a custom **unique** field (e.g., `external_deal_id`) and populate it with a deterministic key.
- Use that unique field as the match key on future imports.

## Notes
- Keep `.env` out of version control.
- When adding new select options, create the option first or the value will be rejected.
