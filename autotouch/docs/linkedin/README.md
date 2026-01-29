# LinkedIn

This directory documents LinkedIn outreach workflows, enrichment via RapidAPI, and how we store reply drafts + approvals for reuse.

Inbox workflow SOP: `docs/linkedin/inbox_sop.md`

## When working in this area
- Read this doc first and create a short plan before making changes.
- Mirror the structure used in `docs/seo/README.md` (overview, quick facts, workflows, storage, notes).

## How we add new LinkedIn workflows (future-proofing)
This repo will grow beyond “inbox unread replies” (e.g., likers/commenters exports, post engagement outreach, etc.).

When adding a new LinkedIn workflow:
- Add a new SOP doc: `docs/linkedin/<workflow>_sop.md`
- Add/extend scripts: `linkedin/scripts/`
- Store raw outputs under: `linkedin/data/raw/<workflow>/` (or a clearly named subfolder)
- Store LLM-readable outputs under: `linkedin/data/processed/`
- If the workflow produces drafts that humans approve, use the same pattern:
  - `LLM reply:` (assistant suggestion)
  - `Approved reply:` (human final)
  - and ensure future runs read prior `Approved reply:` blocks first
- Update this README under “Future endpoints / workflows (planned)” with:
  - endpoint + example request
  - response fields we care about
  - how results map into outreach and/or Attio
  - rate limits / safety constraints

## Quick facts
- RapidAPI key lives in `/Users/nicolo/Projects/bizops/.env` as `RAPID_API_KEY`.
- Current endpoint we use: Fresh LinkedIn Profile Data (RapidAPI) → `enrich-lead`.

## Standard workflow (when given a LinkedIn URL)
1) Confirm the LinkedIn URL and run the `enrich-lead` API query (see below).
2) Summarize the person + company data (title, company, location, size, domain).
3) Do light company research (website or public sources) to add 1–2 relevant context points.
4) Draft a response that uses research in a way that’s not overbearing—just enough to show relevance.
5) Before drafting, review prior `Approved reply:` examples in `linkedin/data/processed/unread_reply_drafts_*.md` so tone/length/CTA stays consistent.
6) Only if the lead is **approved as a CRM candidate**: run email lookup (Findymail) and add the person/company to Attio.

## How we ran the API query
Use the `RAPID_API_KEY` from `.env` and call the RapidAPI endpoint with the LinkedIn profile URL.

```bash
set -a; source /Users/nicolo/Projects/bizops/.env; set +a

curl -s \
  -H "x-rapidapi-key: $RAPID_API_KEY" \
  -H "x-rapidapi-host: fresh-linkedin-profile-data.p.rapidapi.com" \
  "https://fresh-linkedin-profile-data.p.rapidapi.com/enrich-lead?linkedin_url=https%3A%2F%2Fwww.linkedin.com%2Fin%2Fkellygilgenbach%2F&include_skills=false&include_certifications=false&include_publications=false&include_honors=false&include_volunteers=false&include_projects=false&include_patents=false&include_courses=false&include_organizations=false&include_profile_status=false&include_company_public_url=false"
```

Notes:
- Keep all `include_*` flags explicit so responses are predictable.
- Do not paste API keys in docs or chats.

## LinkedIn messaging thread export (private voyager API)
LinkedIn message threads require authenticated session cookies. Use the script below with `LI_AT` and `JSESSIONID` set in your shell.

Script: `linkedin/scripts/fetch_linkedin_thread.sh`

```bash
LI_AT="..." JSESSIONID="ajax:..." \
  ./linkedin/scripts/fetch_linkedin_thread.sh "<voyager URL>"
```

Notes:
- `JSESSIONID` is also used as the `csrf-token` header.
- Do not store cookies in the repo or paste them into docs.
- Store local cookies in `linkedin/.env.<profile>` (gitignored) and put `LI_AT` and `JSESSIONID` there.

## Multiple LinkedIn profiles
You can keep separate cookie files per profile:
- `linkedin/.env.jane`
- `linkedin/.env.nic`

Each file can contain:
```
LI_AT=...
JSESSIONID=ajax:...
INBOX_URL=...   # unread messengerConversations URL
```

Run with the profile flag:
```bash
./linkedin/scripts/fetch_linkedin_unread_threads.sh --profile jane
./linkedin/scripts/fetch_linkedin_unread_threads.sh --profile nic
```

Alternatively, keep a single `linkedin/.env` and set prefixed vars:
```
LI_AT_JANE=...
JSESSIONID_JANE=ajax:...
INBOX_URL_JANE=...
LI_AT_NIC=...
JSESSIONID_NIC=ajax:...
INBOX_URL_NIC=...
```

Both scripts will use the `--profile` value to resolve the prefixed vars.

## Unread inbox export
To pull only unread conversations, use the unread-filtered `messengerConversations` URL (it includes `read:false` in the variables).

Script: `linkedin/scripts/fetch_linkedin_unread_threads.sh`

```bash
LI_AT="..." JSESSIONID="ajax:..." \
  ./linkedin/scripts/fetch_linkedin_unread_threads.sh "<messengerConversations URL>"
```

Notes:
- The script writes the inbox list JSON plus one JSON per thread to `linkedin/data/raw/`.
- If LinkedIn rotates `messengerMessages` query IDs, set `LI_MESSAGE_QUERY_ID` in your shell.
- To limit threads, set `MAX_THREADS=10` (0 = all).

## Reply draft storage (preferred)
We do not store one file per conversation by default. Instead, each run produces a single per-profile output file under `linkedin/data/processed/` (see `docs/linkedin/inbox_sop.md`) that contains:
- `LLM reply:` the suggested response
- `Approved reply:` the human-edited final response

Future runs should read prior `Approved reply` blocks as examples so we stay consistent in tone and avoid repeating mistakes.

## Future endpoints / workflows (planned)
We expect to add more LinkedIn endpoints soon, such as:
- Post engagement (people who liked a post)
- Commenters on a post
- Company page followers

When we add these, document:
- The endpoint + example request
- Response fields we care about
- How we map results into outreach lists
- Any rate limits or constraints

## Doc organization guidance
Follow the pattern in `docs/seo/README.md` when adding new workflows: start with quick facts, add step-by-step calls, and define where outputs should be stored.
