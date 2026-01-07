import http.client
import json
import os
import urllib.parse
from typing import Any, Dict, Optional, Tuple

DEFAULT_JOBS_HOST = "linkedin-job-search-api.p.rapidapi.com"


def _bool_param(value: Optional[bool]) -> Optional[str]:
    if value is None:
        return None
    if isinstance(value, bool):
        return "true" if value else "false"
    return str(value)


def _clean_params(params: Dict[str, Any]) -> Dict[str, Any]:
    cleaned: Dict[str, Any] = {}
    for key, value in params.items():
        if value is None:
            continue
        if isinstance(value, bool):
            cleaned[key] = _bool_param(value)
        else:
            cleaned[key] = value
    return cleaned


class RapidApiLinkedInJobsClient:
    def __init__(
        self,
        api_key: Optional[str] = None,
        host: Optional[str] = None,
        timeout: int = 30,
    ) -> None:
        self.api_key = api_key or os.getenv("RAPID_API_KEY") or os.getenv("RAPIDAPI_KEY")
        if not self.api_key:
            raise ValueError("Missing RAPID_API_KEY (or RAPIDAPI_KEY) in environment")
        self.host = host or os.getenv("RAPIDAPI_JOBS_HOST") or DEFAULT_JOBS_HOST
        self.timeout = timeout

    def _headers(self, extra: Optional[Dict[str, str]] = None) -> Dict[str, str]:
        headers = {
            "x-rapidapi-key": self.api_key,
            "x-rapidapi-host": self.host,
        }
        if extra:
            headers.update(extra)
        return headers

    def _request(
        self,
        method: str,
        path: str,
        params: Optional[Dict[str, Any]] = None,
        body: Optional[Dict[str, Any]] = None,
        headers: Optional[Dict[str, str]] = None,
    ) -> Tuple[int, Dict[str, str], bytes]:
        if params:
            encoded = urllib.parse.urlencode(params, doseq=True)
            path = f"{path}?{encoded}"

        payload = None
        merged_headers = headers or {}
        if body is not None:
            payload = json.dumps(body).encode("utf-8")
            merged_headers = {"Content-Type": "application/json", **merged_headers}

        conn = http.client.HTTPSConnection(self.host, timeout=self.timeout)
        conn.request(method, path, body=payload, headers=self._headers(merged_headers))
        res = conn.getresponse()
        data = res.read()
        return res.status, dict(res.getheaders()), data

    def _request_json(
        self,
        method: str,
        path: str,
        params: Optional[Dict[str, Any]] = None,
        body: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        status, headers, data = self._request(method, path, params=params, body=body)
        text = data.decode("utf-8", errors="replace")
        try:
            payload = json.loads(text)
        except json.JSONDecodeError:
            payload = {"raw": text}
        return {"status": status, "headers": headers, "data": payload}

    def get_jobs_24h(
        self,
        limit: Optional[int] = None,
        offset: Optional[int] = None,
        title_filter: Optional[str] = None,
        location_filter: Optional[str] = None,
        description_filter: Optional[str] = None,
        organization_description_filter: Optional[str] = None,
        organization_specialties_filter: Optional[str] = None,
        organization_slug_filter: Optional[str] = None,
        description_type: Optional[str] = None,
        type_filter: Optional[str] = None,
        remote: Optional[bool] = None,
        agency: Optional[bool] = None,
        industry_filter: Optional[str] = None,
        seniority_filter: Optional[str] = None,
        exclude_ats_duplicate: Optional[bool] = None,
        external_apply_url: Optional[bool] = None,
        directapply: Optional[bool] = None,
        employees_lte: Optional[int] = None,
        employees_gte: Optional[int] = None,
        date_filter: Optional[str] = None,
        order: Optional[str] = None,
        advanced_title_filter: Optional[str] = None,
        advanced_organization_filter: Optional[str] = None,
        include_ai: Optional[bool] = None,
        ai_work_arrangement_filter: Optional[str] = None,
        ai_experience_level_filter: Optional[str] = None,
        ai_visa_sponsorship_filter: Optional[bool] = None,
        ai_taxonomies_a_filter: Optional[str] = None,
        ai_taxonomies_a_primary_filter: Optional[str] = None,
        ai_taxonomies_a_exclusion_filter: Optional[str] = None,
        ai_education_requirements_filter: Optional[str] = None,
        ai_has_salary: Optional[bool] = None,
        organization_filter: Optional[str] = None,
    ) -> Dict[str, Any]:
        params = _clean_params(
            {
                "limit": limit,
                "offset": offset,
                "title_filter": title_filter,
                "location_filter": location_filter,
                "description_filter": description_filter,
                "organization_description_filter": organization_description_filter,
                "organization_specialties_filter": organization_specialties_filter,
                "organization_slug_filter": organization_slug_filter,
                "description_type": description_type,
                "type_filter": type_filter,
                "remote": remote,
                "agency": agency,
                "industry_filter": industry_filter,
                "seniority_filter": seniority_filter,
                "exclude_ats_duplicate": exclude_ats_duplicate,
                "external_apply_url": external_apply_url,
                "directapply": directapply,
                "employees_lte": employees_lte,
                "employees_gte": employees_gte,
                "date_filter": date_filter,
                "order": order,
                "advanced_title_filter": advanced_title_filter,
                "advanced_organization_filter": advanced_organization_filter,
                "include_ai": include_ai,
                "ai_work_arrangement_filter": ai_work_arrangement_filter,
                "ai_experience_level_filter": ai_experience_level_filter,
                "ai_visa_sponsorship_filter": ai_visa_sponsorship_filter,
                "ai_taxonomies_a_filter": ai_taxonomies_a_filter,
                "ai_taxonomies_a_primary_filter": ai_taxonomies_a_primary_filter,
                "ai_taxonomies_a_exclusion_filter": ai_taxonomies_a_exclusion_filter,
                "ai_education_requirements_filter": ai_education_requirements_filter,
                "ai_has_salary": ai_has_salary,
                "organization_filter": organization_filter,
            }
        )
        return self._request_json("GET", "/active-jb-24h", params=params)

    def get_jobs_7d(
        self,
        limit: Optional[int] = None,
        offset: Optional[int] = None,
        title_filter: Optional[str] = None,
        location_filter: Optional[str] = None,
        description_filter: Optional[str] = None,
        organization_description_filter: Optional[str] = None,
        organization_specialties_filter: Optional[str] = None,
        organization_slug_filter: Optional[str] = None,
        description_type: Optional[str] = None,
        type_filter: Optional[str] = None,
        remote: Optional[bool] = None,
        agency: Optional[bool] = None,
        industry_filter: Optional[str] = None,
        seniority_filter: Optional[str] = None,
        date_filter: Optional[str] = None,
        exclude_ats_duplicate: Optional[bool] = None,
        external_apply_url: Optional[bool] = None,
        directapply: Optional[bool] = None,
        employees_lte: Optional[int] = None,
        employees_gte: Optional[int] = None,
        order: Optional[str] = None,
        advanced_title_filter: Optional[str] = None,
        advanced_organization_filter: Optional[str] = None,
        include_ai: Optional[bool] = None,
        ai_work_arrangement_filter: Optional[str] = None,
        ai_experience_level_filter: Optional[str] = None,
        ai_visa_sponsorship_filter: Optional[bool] = None,
        ai_taxonomies_a_filter: Optional[str] = None,
        ai_taxonomies_a_primary_filter: Optional[str] = None,
        ai_taxonomies_a_exclusion_filter: Optional[str] = None,
        ai_has_salary: Optional[bool] = None,
        organization_filter: Optional[str] = None,
    ) -> Dict[str, Any]:
        params = _clean_params(
            {
                "limit": limit,
                "offset": offset,
                "title_filter": title_filter,
                "location_filter": location_filter,
                "description_filter": description_filter,
                "organization_description_filter": organization_description_filter,
                "organization_specialties_filter": organization_specialties_filter,
                "organization_slug_filter": organization_slug_filter,
                "description_type": description_type,
                "type_filter": type_filter,
                "remote": remote,
                "agency": agency,
                "industry_filter": industry_filter,
                "seniority_filter": seniority_filter,
                "date_filter": date_filter,
                "exclude_ats_duplicate": exclude_ats_duplicate,
                "external_apply_url": external_apply_url,
                "directapply": directapply,
                "employees_lte": employees_lte,
                "employees_gte": employees_gte,
                "order": order,
                "advanced_title_filter": advanced_title_filter,
                "advanced_organization_filter": advanced_organization_filter,
                "include_ai": include_ai,
                "ai_work_arrangement_filter": ai_work_arrangement_filter,
                "ai_experience_level_filter": ai_experience_level_filter,
                "ai_visa_sponsorship_filter": ai_visa_sponsorship_filter,
                "ai_taxonomies_a_filter": ai_taxonomies_a_filter,
                "ai_taxonomies_a_primary_filter": ai_taxonomies_a_primary_filter,
                "ai_taxonomies_a_exclusion_filter": ai_taxonomies_a_exclusion_filter,
                "ai_has_salary": ai_has_salary,
                "organization_filter": organization_filter,
            }
        )
        return self._request_json("GET", "/active-jb-7d", params=params)
