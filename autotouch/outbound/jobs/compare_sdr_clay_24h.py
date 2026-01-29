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
from outbound.shared.job_titles import SDR_TITLES, to_or_query
from outbound.jobs.job_fetch import (
    dedupe_jobs,
    extract_jobs,
    job_key,
    summarize_job,
)

TITLE_FILTER = to_or_query(SDR_TITLES)
DESC_FILTER = "Clay"
LIMIT = 20


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
        print(summarize_job(j))

    print("\nSample Active Jobs DB results:")
    for j in active_unique[:5]:
        print(summarize_job(j))

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
