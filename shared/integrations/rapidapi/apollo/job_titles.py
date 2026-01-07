import http.client
import json
import os
import urllib.parse
from typing import Any, Dict, Optional, Tuple

DEFAULT_APOLLO_HOST = "apollo-io-no-cookies-required.p.rapidapi.com"


class RapidApiApolloJobTitleClient:
    def __init__(
        self,
        api_key: Optional[str] = None,
        host: Optional[str] = None,
        timeout: int = 30,
    ) -> None:
        self.api_key = api_key or os.getenv("RAPID_API_KEY") or os.getenv("RAPIDAPI_KEY")
        if not self.api_key:
            raise ValueError("Missing RAPID_API_KEY (or RAPIDAPI_KEY) in environment")
        self.host = host or os.getenv("RAPIDAPI_APOLLO_HOST") or DEFAULT_APOLLO_HOST
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

    def suggestion_job_title(self, query: str) -> Dict[str, Any]:
        if not query:
            raise ValueError("query is required")
        params = {"query": query}
        return self._request_json("GET", "/suggestion_job_title", params=params)
