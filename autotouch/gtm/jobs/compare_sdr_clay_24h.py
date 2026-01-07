import os
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]

# Load .env from repo root
env_path = ROOT / ".env"
if env_path.exists():
    for line in env_path.read_text().splitlines():
        line = line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, value = line.split("=", 1)
        os.environ.setdefault(key.strip(), value.strip())

sys.path.insert(0, str(ROOT))

from shared.integrations.rapidapi.jobs.client import RapidApiLinkedInJobsClient
from shared.integrations.rapidapi.jobs.active_jobs_db import RapidApiActiveJobsDbClient
from autotouch.shared.job_titles import SDR_TITLES, to_or_query

TITLE_FILTER = to_or_query(SDR_TITLES)
DESC_FILTER = "Clay"
LIMIT = 20


def extract_jobs(resp):
    data = resp.get("data") or {}
    if isinstance(data, list):
        return data
    for key in ("data", "jobs", "results"):
        if isinstance(data.get(key), list):
            return data[key]
    return []


ID_KEYS = (
    "id",
    "job_id",
    "jobId",
    "job_post_id",
    "job_posting_id",
    "posting_id",
    "urn",
)


def job_key(job):
    for key in ID_KEYS:
        job_id = job.get(key)
        if job_id:
            return f"id:{str(job_id).strip().lower()}"
    title = (job.get("job_title") or job.get("title") or "").strip().lower()
    company = (
        job.get("employer_name")
        or job.get("company_name")
        or job.get("organization")
        or ""
    ).strip().lower()
    location = (
        job.get("job_city") or job.get("location") or job.get("job_location") or ""
    ).strip().lower()
    url = (
        job.get("job_apply_link")
        or job.get("job_apply_url")
        or job.get("job_url")
        or job.get("job_link")
        or ""
    ).strip().lower()
    return url or f"{title}|{company}|{location}"


def dedupe_jobs(jobs):
    unique = {}
    duplicates = []
    for job in jobs:
        key = job_key(job)
        if key in unique:
            duplicates.append(job)
        else:
            unique[key] = job
    return list(unique.values()), duplicates


def summarize(job):
    return {
        "title": job.get("job_title") or job.get("title"),
        "company": job.get("employer_name")
        or job.get("company_name")
        or job.get("organization"),
        "location": job.get("job_city")
        or job.get("location")
        or job.get("job_location"),
        "url": job.get("job_apply_link")
        or job.get("job_apply_url")
        or job.get("job_url")
        or job.get("job_link"),
        "posted_at": job.get("job_posted_at_datetime_utc")
        or job.get("posted_at")
        or job.get("date_posted"),
    }


def main() -> int:
    linkedin_client = RapidApiLinkedInJobsClient()
    active_client = RapidApiActiveJobsDbClient()

    linkedin_resp = linkedin_client.get_jobs_24h(
        limit=LIMIT,
        offset=0,
        title_filter=TITLE_FILTER,
        description_filter=DESC_FILTER,
        description_type="text",
    )
    active_resp = active_client.get_jobs_24h(
        limit=LIMIT,
        offset=0,
        title_filter=TITLE_FILTER,
        description_filter=DESC_FILTER,
        description_type="text",
    )

    linkedin_jobs = extract_jobs(linkedin_resp)
    active_jobs = extract_jobs(active_resp)

    linkedin_unique, linkedin_dups = dedupe_jobs(linkedin_jobs)
    active_unique, active_dups = dedupe_jobs(active_jobs)

    linkedin_map = {job_key(j): j for j in linkedin_unique}
    active_map = {job_key(j): j for j in active_unique}

    linkedin_keys = set(linkedin_map)
    active_keys = set(active_map)

    overlap = linkedin_keys & active_keys

    print(
        "LinkedIn Job Search API (24h):",
        len(linkedin_jobs),
        "unique:",
        len(linkedin_unique),
        "dups:",
        len(linkedin_dups),
    )
    print(
        "Active Jobs DB (24h):",
        len(active_jobs),
        "unique:",
        len(active_unique),
        "dups:",
        len(active_dups),
    )
    print("Overlap (by url/title+company+location):", len(overlap))

    print("\nSample LinkedIn Job Search API results:")
    for j in linkedin_unique[:5]:
        print(summarize(j))

    print("\nSample Active Jobs DB results:")
    for j in active_unique[:5]:
        print(summarize(j))

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
