# SEO project (artifacts)

This folder stores SEO artifacts and weekly reporting outputs for Autotouch.
If you are an LLM or human starting an SEO task, start here.

## Start here (LLM kickoff)
Ask the user this exact question:
"What do we want to do?"

Then offer these options:
1) Generate the weekly SEO report
2) Export Search Console data
3) Run SERP research (SERPER)
4) Troubleshoot Search Console auth/access

If the user picks a path, follow the instructions below.

## If the user asks "what should we do?" (propose next actions)
1) Check the most recent weekly report in `seo/weekly/` and note its date.
2) Compare that date to today:
   - If it is more than 7 days old, propose running the weekly report next.
3) Check the calendar:
   - If today is within the first 7 days of the month, propose the monthly health check.
   - If today is within the first 7 days of Jan/Apr/Jul/Oct, propose the quarterly content gap review.
4) Ask which path they want to run, then proceed.

## When asked "what next?" or "do the weekly report"
1) Open the most recent report in `seo/weekly/` and read the Synopsis + Next actions.
2) Determine the reporting window:
   - Default is the last 7 **complete** days ending yesterday.
   - The comparison window is the 7 days immediately before that.
3) Ask for confirmation using this exact question:
   "I can run the weekly report for YYYY-MM-DD to YYYY-MM-DD (compare to prior week). Proceed?"
4) If confirmed, run the exports and write a new report file named `YYYY-MM-DD.md` (use the end date).

## Schedule
- Weekly (every Friday or Monday): run the weekly report workflow for the prior 7 days.
- Monthly (first week of the month): review index coverage, Core Web Vitals, and crawl stats.
- Quarterly: review content gaps and prioritize new comparison pages.

## 1) Generate the weekly SEO report
Ask for the date range (7 days) and whether to compare with the prior 7 days.
Then:
- Export GSC data for the current range into `seo/data/gsc/`.
- Export GSC data for the prior range into `seo/data/gsc/`.
  - Required exports: query+page, page-only, query-only, device, country.
- If SERP research is needed, save JSON output in `seo/data/serper/`.
- Summarize results into a new weekly markdown file in `seo/weekly/`.

Use the template at:
`seo/weekly/TEMPLATE.md`

When done, ask:
"Do you want me to commit the weekly report file (not the raw data)?"

## 2) Export Search Console data
Use the commands in `docs/seo/README.md` (runbook).
Save raw exports to:
- `seo/data/gsc/`

If you need a snapshot for website docs, copy the latest CSV to:
- `website/data/Autotouch - Search Console Rankings.csv`

## 3) Run SERP research (SERPER)
Use the commands in `docs/seo/README.md`.
Save JSON outputs to:
- `seo/data/serper/`

## 4) Troubleshoot Search Console auth/access
Use the verify-access steps in `docs/seo/README.md`.
If access fails, report:
- the exact error
- the property being accessed (e.g., `sc-domain:autotouch.ai`)
- which credential file was used

## Notes
- Raw exports live under `seo/data/` and are excluded from git.
- Only commit weekly summaries under `seo/weekly/`.
- Runbooks live in `docs/seo/README.md`.
