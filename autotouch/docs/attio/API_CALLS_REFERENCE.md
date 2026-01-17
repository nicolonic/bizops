# Attio API calls reference (Autotouch)

This is a practical curl-based reference for the most common Attio API calls we use.

## Auth
```bash
set -a; source .env; set +a
```

## Objects
List objects:
```bash
curl -s -H "Authorization: Bearer $ATTIO_API_KEY" \
  -H "Content-Type: application/json" \
  https://api.attio.com/v2/objects
```

## Attributes (schema)
List attributes for an object:
```bash
curl -s -H "Authorization: Bearer $ATTIO_API_KEY" \
  -H "Content-Type: application/json" \
  https://api.attio.com/v2/objects/people/attributes
```

Create a new attribute:
```bash
curl -s -H "Authorization: Bearer $ATTIO_API_KEY" \
  -H "Content-Type: application/json" \
  -X POST https://api.attio.com/v2/objects/people/attributes \
  -d '{
    "data": {
      "title": "Acquisition Channel",
      "description": "",
      "api_slug": "acquisition_channel",
      "type": "select",
      "is_multiselect": false,
      "is_required": false,
      "is_unique": false,
      "config": {}
    }
  }'
```

Add select options:
```bash
ATTR_ID="<attribute_id>"
for opt in "Email" "Referral" "Social"; do
  curl -s -H "Authorization: Bearer $ATTIO_API_KEY" \
    -H "Content-Type: application/json" \
    -X POST "https://api.attio.com/v2/objects/people/attributes/$ATTR_ID/options" \
    -d "{\"data\":{\"title\":\"$opt\"}}"
done
```

Archive attribute:
```bash
ATTR_ID="<attribute_id>"
curl -s -H "Authorization: Bearer $ATTIO_API_KEY" \
  -H "Content-Type: application/json" \
  -X PATCH "https://api.attio.com/v2/objects/people/attributes/$ATTR_ID" \
  -d '{"data":{"is_archived":true}}'
```

## Records
Create record:
```bash
curl -s -H "Authorization: Bearer $ATTIO_API_KEY" \
  -H "Content-Type: application/json" \
  -X POST https://api.attio.com/v2/objects/people/records \
  -d '{
    "data": {
      "values": {
        "name": [{"first_name":"Ada","last_name":"Lovelace","full_name":"Ada Lovelace"}],
        "email_addresses": ["ada@example.com"]
      }
    }
  }'
```

Update record:
```bash
RECORD_ID="<record_id>"
curl -s -H "Authorization: Bearer $ATTIO_API_KEY" \
  -H "Content-Type: application/json" \
  -X PUT https://api.attio.com/v2/objects/people/records/$RECORD_ID \
  -d '{"data":{"values":{"job_title":"VP of Sales"}}}'
```

Query records:
```bash
curl -s -H "Authorization: Bearer $ATTIO_API_KEY" \
  -H "Content-Type: application/json" \
  -X POST https://api.attio.com/v2/objects/people/records/query \
  -d '{"filter":{"email_addresses":"ada@example.com"},"limit":1}'
```

## Lists
List lists:
```bash
curl -s -H "Authorization: Bearer $ATTIO_API_KEY" \
  -H "Content-Type: application/json" \
  https://api.attio.com/v2/lists
```

List entries:
```bash
LIST_ID="<list_id>"
curl -s -H "Authorization: Bearer $ATTIO_API_KEY" \
  -H "Content-Type: application/json" \
  https://api.attio.com/v2/lists/$LIST_ID/entries
```

Add entry:
```bash
LIST_ID="<list_id>"
RECORD_ID="<record_id>"
OBJECT_SLUG="people"
curl -s -H "Authorization: Bearer $ATTIO_API_KEY" \
  -H "Content-Type: application/json" \
  -X POST https://api.attio.com/v2/lists/$LIST_ID/entries \
  -d "{\"data\":{\"record_id\":\"$RECORD_ID\",\"object_slug\":\"$OBJECT_SLUG\"}}"
```

## Tasks
Create a task linked to a record:
```bash
curl -s -H "Authorization: Bearer $ATTIO_API_KEY" \
  -H "Content-Type: application/json" \
  -X POST https://api.attio.com/v2/tasks \
  -d '{
    "data": {
      "content": "Follow up with lead",
      "format": "plaintext",
      "deadline_at": "2026-01-19T18:00:00.000000000Z",
      "is_completed": false,
      "assignees": [],
      "linked_records": [
        {"target_object":"people","target_record_id":"<record_id>"}
      ]
    }
  }'
```

## Notes
- Attio requires `description` for attribute creation payloads.
- `assignees` is required for tasks (empty array is allowed).
- For select fields, values must match existing options.
