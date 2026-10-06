"""Reusable HTTP client; assertions stay in the tests."""

from urllib.parse import urlsplit

import requests


class AttendanceClient:
    def __init__(self, base_url: str, timeout: float = 5):
        self.url = f"{base_url.rstrip('/')}/api/v1/attendance"
        self.timeout = timeout
        self.session = requests.Session()
        # Isolate local mocks from proxies; preserve staging proxy/auth settings.
        if urlsplit(base_url).hostname in {"127.0.0.1", "localhost", "::1"}:
            self.session.trust_env = False

    def submit(self, payload):
        return self.session.post(self.url, json=payload, timeout=self.timeout)

    def submit_raw(self, data):
        return self.session.post(self.url, data=data,
                                 headers={"Content-Type": "application/json"},
                                 timeout=self.timeout)

    def request(self, method):
        return self.session.request(method, self.url, timeout=self.timeout)

    def close(self):
        self.session.close()
