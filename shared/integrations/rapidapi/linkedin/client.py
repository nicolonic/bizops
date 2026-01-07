import http.client
import json
import os
import urllib.parse
from typing import Any, Dict, Optional, Tuple

DEFAULT_LINKEDIN_HOST = "fresh-linkedin-profile-data.p.rapidapi.com"


def _bool_param(value: Optional[bool]) -> Optional[str]:
    if value is None:
        return None
    if isinstance(value, bool):
        return "true" if value else "false"
    return str(value)


class RapidApiLinkedInClient:
    def __init__(
        self,
        api_key: Optional[str] = None,
        host: Optional[str] = None,
        timeout: int = 30,
    ) -> None:
        self.api_key = api_key or os.getenv("RAPID_API_KEY") or os.getenv("RAPIDAPI_KEY")
        if not self.api_key:
            raise ValueError("Missing RAPID_API_KEY (or RAPIDAPI_KEY) in environment")
        self.host = host or os.getenv("RAPIDAPI_LINKEDIN_HOST") or DEFAULT_LINKEDIN_HOST
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
            encoded = urllib.parse.urlencode(
                {k: v for k, v in params.items() if v is not None}, doseq=True
            )
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

    def get_profile_details(
        self,
        linkedin_url: str,
        include_skills: Optional[bool] = False,
        include_certifications: Optional[bool] = False,
        include_publications: Optional[bool] = False,
        include_honors: Optional[bool] = False,
        include_volunteers: Optional[bool] = False,
        include_projects: Optional[bool] = False,
        include_patents: Optional[bool] = False,
        include_courses: Optional[bool] = False,
        include_organizations: Optional[bool] = False,
        include_profile_status: Optional[bool] = False,
        include_company_public_url: Optional[bool] = False,
    ) -> Dict[str, Any]:
        params = {
            "linkedin_url": linkedin_url,
            "include_skills": _bool_param(include_skills),
            "include_certifications": _bool_param(include_certifications),
            "include_publications": _bool_param(include_publications),
            "include_honors": _bool_param(include_honors),
            "include_volunteers": _bool_param(include_volunteers),
            "include_projects": _bool_param(include_projects),
            "include_patents": _bool_param(include_patents),
            "include_courses": _bool_param(include_courses),
            "include_organizations": _bool_param(include_organizations),
            "include_profile_status": _bool_param(include_profile_status),
            "include_company_public_url": _bool_param(include_company_public_url),
        }
        return self._request_json("GET", "/enrich-lead", params=params)

    def get_profile_posts(
        self,
        linkedin_url: str,
        post_type: Optional[str] = "posts",
        start: Optional[int] = 0,
        pagination_token: Optional[str] = None,
    ) -> Dict[str, Any]:
        params = {
            "linkedin_url": linkedin_url,
            "type": post_type,
            "start": start,
            "pagination_token": pagination_token,
        }
        return self._request_json("GET", "/get-profile-posts", params=params)

    def get_post_comments(
        self,
        urn: str,
        sort_by: Optional[str] = "Most relevant",
        page: Optional[int] = 1,
        pagination_token: Optional[str] = None,
    ) -> Dict[str, Any]:
        params = {
            "urn": urn,
            "sort_by": sort_by,
            "page": page,
            "pagination_token": pagination_token,
        }
        return self._request_json("GET", "/get-post-comments", params=params)

    def get_post_reactions(
        self,
        urn: str,
        reaction_type: Optional[str] = "ALL",
        page: Optional[int] = 1,
    ) -> Dict[str, Any]:
        params = {"urn": urn, "type": reaction_type, "page": page}
        return self._request_json("GET", "/get-post-reactions", params=params)

    def search_posts(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        return self._request_json("POST", "/search-posts", body=payload)
