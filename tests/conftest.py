import os
from threading import Thread

import pytest

from support.client import AttendanceClient
from support.mock_api import create_server
from support.payloads import attendance_payload


@pytest.fixture(scope="session")
def mock_server():
    if os.getenv("ATTENDANCE_API_URL"):
        yield None
        return
    server = create_server()
    thread = Thread(target=server.serve_forever, daemon=True)
    thread.start()
    try:
        yield server
    finally:
        server.shutdown()
        server.server_close()
        thread.join(timeout=5)


@pytest.fixture(scope="session")
def base_url(mock_server):
    return os.getenv("ATTENDANCE_API_URL") or f"http://127.0.0.1:{mock_server.server_port}"


@pytest.fixture
def client(base_url):
    api = AttendanceClient(base_url)
    try:
        yield api
    finally:
        api.close()


@pytest.fixture
def valid_payload():
    return attendance_payload()
