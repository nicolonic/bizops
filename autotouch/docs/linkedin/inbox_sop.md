# LinkedIn Inbox SOP (Autotouch)

Goal: once per day, pull **unread LinkedIn messages** for a given LinkedIn profile, do lightweight **person + company research**, and produce **draft replies** that fit our style (short, relevant, not overbearing). The output is a single markdown file per profile that the human can edit by adding an “Approved reply” under each suggested “LLM reply”.

This SOP is written so a future LLM can run it end-to-end.

---

## What exists today (capabilities)

### 1) Pull unread messages (per profile)
- We can fetch the **Unread** inbox (conversation list) and then fetch each unread **thread** using LinkedIn’s private Voyager GraphQL endpoints.
- Script: `linkedin/scripts/fetch_linkedin_unread_threads.sh`
- Supports multiple profiles via `--profile jane|nic` and `linkedin/.env.<profile>`.

### 2) Turn raw JSON into clean LLM-readable markdown
- We format the raw thread JSONs into a single markdown file with:
  - participants + LinkedIn URLs
  - full transcript bullets
- Script: `linkedin/scripts/format_linkedin_threads.py`

### 3) Enrich a person + company from a LinkedIn URL
- We use RapidAPI “Fresh LinkedIn Profile Data” `enrich-lead` to get:
  - person name/title/location
  - company name/domain/industry/size + description
  - a **vanity LinkedIn URL**, even when the input is an opaque `ACoA...` profile URL
- Key: `RAPID_API_KEY` in `/Users/nicolo/Projects/bizops/.env`

### 4) Produce reply drafts + learn from edits
- We write one “draft replies” file per profile that includes:
  - `LLM reply:` (assistant’s suggested response)
  - `Approved reply:` (human final edit)
- Before writing any new `LLM reply:` blocks, the LLM should read prior “Approved reply” examples to stay consistent with voice and tighten future drafts.

---

## Inputs / secrets (where to find them)

### RapidAPI (profile enrichment)
- File: `/Users/nicolo/Projects/bizops/.env`
- Variable: `RAPID_API_KEY`
- Do **not** copy the key into repo docs or commit it.

### Attio (CRM)
- Variable: `ATTIO_API_KEY` (see `docs/attio/CRM_SCHEMA_AND_LISTS.md`)
- Load for curl examples (from the Autotouch repo root): `set -a; source .env; set +a`
- Do **not** commit new keys.

### LinkedIn session cookies (per profile)
We use the authenticated browser session cookies:
- `LI_AT` (from cookie `li_at`)
- `JSESSIONID` (from cookie `JSESSIONID`, looks like `ajax:...`)

Store them locally per profile:
- `linkedin/.env.jane`
- `linkedin/.env.nic`

Each file must contain (at minimum):
```bash
LI_AT="..."
JSESSIONID="ajax:..."
INBOX_URL="https://www.linkedin.com/voyager/api/voyagerMessagingGraphQL/graphql?queryId=messengerConversations.<HASH>&variables=(...,read:false,mailboxUrn:urn%3Ali%3Afsd_profile%3A<PROFILE_URN>,...)"
```

Important:
- Wrap `INBOX_URL` in quotes. The URL contains parentheses `(...)` and will break `source` if unquoted.
- These cookie files must be **gitignored** (see “Repo hygiene” below).

---

## Repo hygiene (don’t commit secrets)

Required:
- `linkedin/.env.*` must never be committed.
- Raw inbox/thread exports contain private message content; treat as local artifacts.

We keep these ignored via the repo-level `.gitignore` (it already ignores `**/.env.*` and `**/data/**`).

---

## Step-by-step daily run (start with Jane)

### Step 0 — Confirm Jane is configured
Check:
- `linkedin/.env.jane` exists and contains `LI_AT`, `JSESSIONID`, and `INBOX_URL` with `read:false`.

If `INBOX_URL` is missing or stale:
1) Open LinkedIn in Chrome as Jane
2) Go to Messaging → select “Unread”
3) DevTools → Network → search `messengerConversations` or `read:false`
4) Copy the **Request URL** for the unread conversation list
5) Paste into `INBOX_URL="..."` in `linkedin/.env.jane`

### Step 1 — Fetch unread inbox + threads (Jane)
Run:
```bash
./linkedin/scripts/fetch_linkedin_unread_threads.sh --profile jane
```

This writes:
- unread list: `linkedin/data/raw/linkedin_unread_inbox_<timestamp>.json`
- thread files: `linkedin/data/raw/threads/thread_<...>.json`

Troubleshooting:
- If you see 401/403: cookies expired → refresh `LI_AT` and `JSESSIONID` from DevTools and re-run.
- If you see empty results: confirm the inbox URL includes `read:false` and the correct `mailboxUrn`.

### Step 2 — Format threads into LLM-readable markdown
Run:
```bash
python3 linkedin/scripts/format_linkedin_threads.py \
  --out linkedin/data/processed/unread_threads_jane_latest.md
```

This produces a clean, structured file the LLM can read:
- `linkedin/data/processed/unread_threads_jane_latest.md`

### Step 2.5 — Review past “Approved reply” examples (Jane)
Before drafting new replies, read prior runs so wording stays consistent and improves over time:
- Latest: `linkedin/data/processed/unread_reply_drafts_jane_latest.md` (if it exists)
- Archive (if you keep snapshots): `linkedin/data/processed/archive/`

Guidance:
- Treat `Approved reply:` as the source of truth for tone/length/CTA.
- If `Approved reply:` is blank, do not learn from that section.

### Step 3 — For each unread thread: do research
For each thread in `unread_threads_jane_latest.md`:
1) Identify the prospect (the participant who is not “Jane Thompson”).
2) Copy their `profileUrl` from the “Participants” section (may be an opaque `ACoA...` URL).
3) Run RapidAPI enrichment to get person + company details.

RapidAPI enrich (curl):
```bash
set -a; source /Users/nicolo/Projects/bizops/.env; set +a

curl -sG \
  -H "x-rapidapi-key: $RAPID_API_KEY" \
  -H "x-rapidapi-host: fresh-linkedin-profile-data.p.rapidapi.com" \
  --data-urlencode "linkedin_url=<PASTE_LINKEDIN_PROFILE_URL>" \
  --data-urlencode "include_skills=false" \
  --data-urlencode "include_certifications=false" \
  --data-urlencode "include_publications=false" \
  --data-urlencode "include_honors=false" \
  --data-urlencode "include_volunteers=false" \
  --data-urlencode "include_projects=false" \
  --data-urlencode "include_patents=false" \
  --data-urlencode "include_courses=false" \
  --data-urlencode "include_organizations=false" \
  --data-urlencode "include_profile_status=false" \
  --data-urlencode "include_company_public_url=false"
```

Extract the minimum fields for reply context:
- Person: `full_name`, `job_title`, `headline`, `location`, `linkedin_url` (vanity)
- Company: `company`, `company_domain`, `company_industry`, `company_employee_range`, `company_description`

#### Important: do NOT run email lookup unless CRM-approved
Findymail is credit-based. Do **not** run it for every unread message.
Only run Findymail after the human marks the lead as a **CRM-approved candidate** (see Step 4.1).

#### Optional (CRM-approved only): find a verified email (Findymail)
If RapidAPI does not return an email and the lead is CRM-approved, use Findymail for dedupe:
- Key: `FINDYMAIL_API_KEY` in `/Users/nicolo/Projects/bizops/.env`
- Endpoint: `POST https://app.findymail.com/api/search/business-profile`
- Cost: uses finder credits when a verified email is found (per Findymail docs)

```bash
set -a; source /Users/nicolo/Projects/bizops/.env; set +a

curl -s https://app.findymail.com/api/search/business-profile \
  --request POST \
  --header 'Content-Type: application/json' \
  --header "Authorization: Bearer $FINDYMAIL_API_KEY" \
  --data '{"linkedin_url":"https://linkedin.com/in/<public_id_or_full_url>","webhook_url":null}'
```

If an email is found:
- Write it into Attio `people.email_addresses`
- Use it as your primary dedupe key (query by email before creating a person record)

Company “light research” (keep it minimal):
- Use the company domain and pull the homepage title/meta description for 1 relevance hook.
- Only use **1–2** facts; do not write a long research paragraph.

### Step 4 — Draft replies (Jane)
Output file:
- `linkedin/data/processed/unread_reply_drafts_jane_latest.md`

For each unread thread, include:
- Prospect name + title + company + domain
- Company one-liner + 1 extra context clause (what they do / who they sell to)
- Last inbound message (or the latest relevant message in thread)
- `LLM reply:` (your suggested reply)
- `Approved reply:` (leave blank; human fills in)

Reply style rules (important):
- Personalization should be **light-touch**: one relevant line max (role, company, industry, or a simple trigger).
- Use research **when it improves relevance** (e.g., who they sell to, what they sell, buyer persona, common workflow). If it’s not clearly useful, skip it.
- Keep it short and action-oriented (1–4 sentences).
- Avoid “tool salad” and avoid sounding like a bot.
- Use our core value prop, adapted to their role:
  - automate account research
  - verified phone/email (waterfall enrichment)
  - call + sequence from one place (dialing + sequencing)
  - reps spend less time researching and more time in relevant conversations

### Step 4.1 — CRM gating + Attio actions (only after approval)
We do **not** add leads/companies to Attio by default.

For each thread, the LLM may *recommend* CRM action, but it should not run Findymail or create Attio records unless the lead is explicitly approved as a CRM candidate (either the user says “add to Attio” or you capture it in the draft file as an “Approved” field).

If the latest inbound message indicates interest, the draft output should include a **CRM recommendation** under that thread.

What “interested” looks like (examples):
- “Sure. Send me info.”
- “Yes, send the demo link.”
- “Open to a quick call / demo.”
- “Can you share details / pricing / deck?”
- “Can you connect me with the right person?” (soft interest)

What to include in the output (under the thread):
- `CRM candidate (LLM):` yes/no + why
- `CRM approved (human):` leave blank (human fills in `yes` / `no`)
- If approved: `Email lookup (Findymail):` plan + result
- If approved: `Attio create/update:` plan (company → person → task) with fields
- If approved: `Task:` suggestion (content + deadline)

Attio reference docs:
- Lead + company flow: `docs/attio/LEADS_COMPANIES_AND_RESEARCH.md`
- Tasks + API calls: `docs/attio/API_CALLS_REFERENCE.md`
- Schema + attribution fields: `docs/attio/CRM_SCHEMA_AND_LISTS.md`

Email-first rule (approved only):
- If the lead is **CRM-approved**, try to find a verified email **before creating the Attio person record**.
- Preferred order:
  1) RapidAPI enrichment (profile + company)
  2) Findymail `business-profile` lookup (verified email) using the LinkedIn URL
  3) Attio: query person by email → create/update person → link to company → create task
- If no email is found, you can still create the person record, but it should be flagged in `description` and updated later when an email is obtained.

Recommended Attio flow (copy the pattern from `docs/attio/LEADS_COMPANIES_AND_RESEARCH.md`):
1) **Company**: query by domain → create or update company record
2) **Person**: query by email if known → create or update person record
3) Link the person to the company record
4) Set attribution fields on both company + person
5) Create a follow-up task linked to the person record

Attribution mapping for LinkedIn outbound:
- `acquisition_direction`: `Outbound` (we initiated)
- `acquisition_channel`: `Social`
- `source_detail`: `LinkedIn`
- `campaign`: use your current outbound batch name (or leave blank if unknown)
- `last_outbound_date`: set to today (people record)

Important nuance (email may be missing):
- If RapidAPI returns no email/phone, still create the person record with:
  - `name`, `job_title`, `company` link, `description`
  - Put the prospect’s LinkedIn URL + a short thread note into `description`
- If you later obtain an email, update the record and use that for dedupe going forward.

Task creation guidance (Attio):
- Create a task when:
  - they asked for info (send link + follow up)
  - they said “maybe” (follow up in a few days)
  - they’re not the decision maker (task: find owner + ask for intro)
- Use a short, specific task content:
  - “Send founder demo link; follow up in 2 days if no reply.”
  - “Find correct owner for sales engagement tool; ask for intro.”
- Set `deadline_at` to a reasonable date/time (next business day or +2 days).

### Step 5 — Learning loop (approved replies)
After the human edits `unread_reply_drafts_jane_latest.md`:
- They add their final wording under `Approved reply:`
- Future runs must read previous `Approved reply` blocks and:
  - keep tone consistent
  - prefer the proven phrasing patterns
  - tighten over-explanations (as seen in approvals)

Where to look for examples:
- Current run drafts: `linkedin/data/processed/unread_reply_drafts_jane_latest.md`
- Prior runs (recommended): keep daily snapshots in an archive folder, e.g.
  - `linkedin/data/processed/archive/unread_reply_drafts_jane_YYYY-MM-DD.md`

---

## Running for Nic (when asked)

Same workflow as Jane, but with Nic’s cookies and inbox URL:
```bash
./linkedin/scripts/fetch_linkedin_unread_threads.sh --profile nic
python3 linkedin/scripts/format_linkedin_threads.py --out linkedin/data/processed/unread_threads_nic_latest.md
```

Prereqs:
- `linkedin/.env.nic` must include Nic’s `LI_AT`, `JSESSIONID`, and `INBOX_URL` (with Nic’s `mailboxUrn` and `read:false`).

---

## Troubleshooting checklist

### INBOX_URL breaks the script
Symptom: `syntax error near unexpected token '('` when sourcing `.env.<profile>`.
- Fix: wrap `INBOX_URL` in double quotes inside the env file.

### Raw JSON looks like binary / formatter fails
Symptom: python `UnicodeDecodeError` when reading `linkedin_unread_inbox_*.json`.
- Fix: the fetch script must use `curl --compressed` so the output is decompressed JSON.

### 401 / 403 responses
- Cookies expired or wrong profile.
- Refresh `LI_AT` and `JSESSIONID` from DevTools for that profile.

### LinkedIn queryId changes
If the unread inbox queryId changes:
- Update `INBOX_URL` in the profile env file.

If the messages queryId changes:
- Find the `messengerMessages.<HASH>` call in DevTools while viewing a thread.
- Set `LI_MESSAGE_QUERY_ID=messengerMessages.<HASH>` in `linkedin/.env.<profile>`.
