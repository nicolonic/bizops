from typing import Any, Dict, Iterable, List, Optional, Set, Tuple

from shared.integrations.rapidapi.jobs.active_jobs_db import RapidApiActiveJobsDbClient
from shared.integrations.rapidapi.jobs.client import RapidApiLinkedInJobsClient

ID_KEYS = (
    "id",
    "job_id",
    "jobId",
    "job_post_id",
    "job_posting_id",
    "posting_id",
    "urn",
)


def pick(job: Dict[str, Any], *keys: str) -> Optional[Any]:
    for key in keys:
        value = job.get(key)
        if value not in (None, "", []):
            return value
    return None


def extract_jobs(resp: Dict[str, Any]) -> List[Dict[str, Any]]:
    data = resp.get("data") or {}
    if isinstance(data, list):
        return data
    for key in ("data", "jobs", "results"):
        if isinstance(data.get(key), list):
            return data[key]
    return []


def job_key(job: Dict[str, Any]) -> str:
    for key in ID_KEYS:
        job_id = job.get(key)
        if job_id:
            return f"id:{str(job_id).strip().lower()}"
    title = (pick(job, "job_title", "title") or "").strip().lower()
    company = (
        pick(job, "employer_name", "company_name", "organization") or ""
    ).strip().lower()
    location = (
        pick(job, "job_city", "location", "job_location") or ""
    ).strip().lower()
    url = (
        pick(job, "job_apply_link", "job_apply_url", "job_url", "job_link") or ""
    ).strip().lower()
    return url or f"{title}|{company}|{location}"


def dedupe_jobs(jobs: Iterable[Dict[str, Any]]) -> Tuple[List[Dict[str, Any]], List[Dict[str, Any]]]:
    unique: Dict[str, Dict[str, Any]] = {}
    duplicates: List[Dict[str, Any]] = []
    for job in jobs:
        key = job_key(job)
        if key in unique:
            duplicates.append(job)
        else:
            unique[key] = job
    return list(unique.values()), duplicates


def summarize_job(job: Dict[str, Any]) -> Dict[str, Any]:
    return {
        "title": pick(job, "job_title", "title"),
        "company": pick(job, "employer_name", "company_name", "organization"),
        "location": pick(job, "job_city", "location", "job_location"),
        "url": pick(job, "job_apply_link", "job_apply_url", "job_url", "job_link"),
        "posted_at": pick(
            job,
            "job_posted_at_datetime_utc",
            "posted_at",
            "date_posted",
        ),
    }


def normalize_keywords(values: Iterable[str]) -> List[str]:
    keywords: List[str] = []
    for raw in values:
        if not raw:
            continue
        parts = [p.strip() for p in raw.replace(";", ",").split(",")]
        for part in parts:
            if part:
                keywords.append(part)
    seen: Set[str] = set()
    ordered: List[str] = []
    for keyword in keywords:
        key = keyword.lower()
        if key in seen:
            continue
        seen.add(key)
        ordered.append(keyword)
    return ordered


def _request_jobs(
    client: Any,
    window: str,
    params: Dict[str, Any],
) -> Dict[str, Any]:
    if window == "7d":
        return client.get_jobs_7d(**params)
    return client.get_jobs_24h(**params)


def fetch_jobs(
    linkedin_client: RapidApiLinkedInJobsClient,
    active_client: RapidApiActiveJobsDbClient,
    window: str,
    title_filter: Optional[str],
    keywords: List[str],
    employees_lte: Optional[int],
    employees_gte: Optional[int],
    limit: int,
) -> Tuple[Dict[str, Dict[str, Any]], Dict[str, Set[str]], Dict[str, Set[str]]]:
    jobs_by_key: Dict[str, Dict[str, Any]] = {}
    sources_by_key: Dict[str, Set[str]] = {}
    keywords_by_key: Dict[str, Set[str]] = {}

    def add_job(job: Dict[str, Any], source: str, keyword: Optional[str]) -> None:
        key = job_key(job)
        if key not in jobs_by_key:
            jobs_by_key[key] = job
        sources_by_key.setdefault(key, set()).add(source)
        if keyword:
            keywords_by_key.setdefault(key, set()).add(keyword)

    linkedin_params = {
        "limit": limit,
        "offset": 0,
        "title_filter": title_filter,
        "description_type": "text",
        "employees_lte": employees_lte,
        "employees_gte": employees_gte,
    }
    active_params = {
        "limit": limit,
        "offset": 0,
        "title_filter": title_filter,
        "description_type": "text",
        "li_organization_employees_lte": employees_lte,
        "li_organization_employees_gte": employees_gte,
    }

    keyword_list: List[Optional[str]] = keywords or [None]
    for keyword in keyword_list:
        if keyword:
            linkedin_params["description_filter"] = keyword
            active_params["description_filter"] = keyword
        else:
            linkedin_params.pop("description_filter", None)
            active_params.pop("description_filter", None)

        linkedin_resp = _request_jobs(linkedin_client, window, linkedin_params)
        if linkedin_resp.get("status") not in (200, 201):
            status = linkedin_resp.get("status")
            print(f"LinkedIn jobs {window} request failed: {status}")
        for job in extract_jobs(linkedin_resp):
            add_job(job, "linkedin", keyword)

        active_resp = _request_jobs(active_client, window, active_params)
        if active_resp.get("status") not in (200, 201):
            status = active_resp.get("status")
            print(f"Active jobs {window} request failed: {status}")
        for job in extract_jobs(active_resp):
            add_job(job, "active_jobs_db", keyword)

    return jobs_by_key, sources_by_key, keywords_by_key


def build_record(
    key: str,
    job: Dict[str, Any],
    sources: Set[str],
    keywords: Set[str],
    window: str,
    employees_lte: Optional[int],
    employees_gte: Optional[int],
) -> Dict[str, Any]:
    company_domain = pick(
        job,
        "company_domain",
        "organization_domain",
        "employer_domain",
        "domain",
    )
    website = pick(
        job,
        "company_website",
        "organization_website",
        "employer_website",
        "company_url",
        "organization_url",
        "website",
        "url",
        "company_link",
        "employer_link",
        "company_domain",
        "organization_domain",
        "employer_domain",
        "domain",
    )
    if isinstance(website, str) and website and not website.startswith(("http://", "https://")):
        website = f"https://{website}"

    company_linkedin_url = pick(
        job,
        "organization_url",
        "linkedin_org_url",
        "company_linkedin_url",
        "company_linkedin",
        "linkedin_url",
    )
    job_url = pick(
        job,
        "job_apply_link",
        "job_apply_url",
        "job_url",
        "job_link",
        "external_apply_url",
        "url",
    )
    external_apply_url = pick(job, "external_apply_url")
    if isinstance(job_url, str) and job_url and not job_url.startswith(("http://", "https://")):
        job_url = f"https://{job_url}"
    if isinstance(external_apply_url, str) and external_apply_url and not external_apply_url.startswith(("http://", "https://")):
        external_apply_url = f"https://{external_apply_url}"

    job_description = pick(
        job,
        "description",
        "job_description",
        "description_text",
        "description_raw",
    )

    employment_type = pick(job, "employment_type", "job_employment_type")
    seniority = pick(job, "seniority", "job_seniority")
    remote = pick(job, "remote_derived", "remote")

    record = {
        "unknown_id": key,
        "job_title": pick(job, "job_title", "title"),
        "company": pick(job, "employer_name", "company_name", "organization"),
        "location": pick(job, "job_city", "location", "job_location"),
        "job_url": job_url,
        "external_apply_url": external_apply_url,
        "posted_at": pick(
            job,
            "job_posted_at_datetime_utc",
            "posted_at",
            "date_posted",
        ),
        "website": website,
        "company_domain": company_domain,
        "company_linkedin_url": company_linkedin_url,
        "job_description": job_description,
        "employment_type": employment_type,
        "seniority": seniority,
        "remote": remote,
        "sources": ", ".join(sorted(sources)),
        "keywords": ", ".join(sorted(keywords)),
        "window": window,
    }
    if employees_lte is not None:
        record["employees_lte"] = employees_lte
    if employees_gte is not None:
        record["employees_gte"] = employees_gte

    employee_fields = (
        "company_employee_count",
        "company_size",
        "organization_num_employees",
        "organization_employees",
        "employees",
    )
    employee_value = pick(job, *employee_fields)
    if employee_value is not None:
        record["company_employee_count"] = employee_value

    return record
