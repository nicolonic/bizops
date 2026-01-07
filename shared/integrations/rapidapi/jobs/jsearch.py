import http.client
import json
import os
import urllib.parse
from typing import Any, Dict, Optional, Tuple

DEFAULT_JSEARCH_HOST = "jsearch.p.rapidapi.com"


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


class RapidApiJSearchClient:
    def __init__(
        self,
        api_key: Optional[str] = None,
        host: Optional[str] = None,
        timeout: int = 30,
    ) -> None:
        self.api_key = api_key or os.getenv("RAPID_API_KEY") or os.getenv("RAPIDAPI_KEY")
        if not self.api_key:
            raise ValueError("Missing RAPID_API_KEY (or RAPIDAPI_KEY) in environment")
        self.host = host or os.getenv("RAPIDAPI_JSEARCH_HOST") or DEFAULT_JSEARCH_HOST
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

    def search_jobs(
        self,
        query: str,
        page: Optional[int] = None,
        num_pages: Optional[int] = None,
        country: Optional[str] = None,
        language: Optional[str] = None,
        date_posted: Optional[str] = None,
        work_from_home: Optional[bool] = None,
        employment_types: Optional[str] = None,
        job_requirements: Optional[str] = None,
        radius: Optional[int] = None,
        exclude_job_publishers: Optional[str] = None,
        fields: Optional[str] = None,
    ) -> Dict[str, Any]:
        params = _clean_params(
            {
                "query": query,
                "page": page,
                "num_pages": num_pages,
                "country": country,
                "language": language,
                "date_posted": date_posted,
                "work_from_home": work_from_home,
                "employment_types": employment_types,
                "job_requirements": job_requirements,
                "radius": radius,
                "exclude_job_publishers": exclude_job_publishers,
                "fields": fields,
            }
        )
        return self._request_json("GET", "/search", params=params)
