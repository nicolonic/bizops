#!/usr/bin/env python3
import argparse
import json
import os
import sys
import urllib.error
import urllib.request
from pathlib import Path
from typing import Any, Dict, Iterable, List, Optional

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
    build_record,
    fetch_jobs,
    normalize_keywords,
)

DEFAULT_WEBHOOK_URL = (
    "https://app.autotouch.ai/api/webhooks/tables/697a500b57002fdbff95a9cb/ingest"
)

def post_records(
    url: str,
    token: str,
    records: List[Dict[str, Any]],
) -> None:
    payload = json.dumps({"records": records}).encode("utf-8")
    request = urllib.request.Request(
        url,
        data=payload,
        headers={
            "Content-Type": "application/json",
            "X-Autotouch-Token": token,
        },
        method="POST",
    )
    try:
        with urllib.request.urlopen(request, timeout=30) as response:
            if response.status != 200:
                body = response.read().decode("utf-8", errors="replace")
                raise RuntimeError(
                    f"Webhook returned {response.status}: {body}"
                )
    except urllib.error.HTTPError as exc:
        body = exc.read().decode("utf-8", errors="replace")
        raise RuntimeError(f"Webhook error {exc.code}: {body}") from exc


def chunked(items: List[Dict[str, Any]], size: int) -> Iterable[List[Dict[str, Any]]]:
    for i in range(0, len(items), size):
        yield items[i : i + size]


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Fetch SDR/BDR job signals and send to Autotouch table webhook."
    )
    parser.add_argument(
        "--window",
        choices=("24h", "7d"),
        default="24h",
        help="Time window to query.",
    )
    parser.add_argument(
        "--employees-lte",
        type=int,
        default=None,
        help="Max company headcount (uses LinkedIn org employees when available).",
    )
    parser.add_argument(
        "--employees-gte",
        type=int,
        default=None,
        help="Min company headcount (uses LinkedIn org employees when available).",
    )
    parser.add_argument(
        "--keywords",
        nargs="*",
        default=[],
        help="Keywords to search in job descriptions (comma-separated or space-separated).",
    )
    parser.add_argument(
        "--limit",
        type=int,
        default=50,
        help="Limit per source per keyword.",
    )
    parser.add_argument(
        "--batch-size",
        type=int,
        default=100,
        help="Records per webhook POST.",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Do not send to webhook; just print summary.",
    )
    args = parser.parse_args()

    keywords = normalize_keywords(args.keywords)
    title_filter = to_or_query(SDR_TITLES)

    linkedin_client = RapidApiLinkedInJobsClient()
    active_client = RapidApiActiveJobsDbClient()

    jobs_by_key, sources_by_key, keywords_by_key = fetch_jobs(
        linkedin_client,
        active_client,
        args.window,
        title_filter,
        keywords,
        args.employees_lte,
        args.employees_gte,
        args.limit,
    )

    records: List[Dict[str, Any]] = []
    for key, job in jobs_by_key.items():
        record = build_record(
            key,
            job,
            sources_by_key.get(key, set()),
            keywords_by_key.get(key, set()),
            args.window,
            args.employees_lte,
            args.employees_gte,
        )
        records.append(record)

    print(f"Fetched {len(records)} unique jobs.")
    if args.dry_run or not records:
        return 0

    webhook_url = os.getenv("AUTOTOUCH_TABLE_WEBHOOK_URL", DEFAULT_WEBHOOK_URL)
    token = os.getenv("AUTOTOUCH_TABLE_WEBHOOK_TOKEN")
    if not token:
        print(
            "Missing AUTOTOUCH_TABLE_WEBHOOK_TOKEN in environment.",
            file=sys.stderr,
        )
        return 1

    for batch in chunked(records, args.batch_size):
        post_records(webhook_url, token, batch)

    print(f"Sent {len(records)} records to webhook.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
