"""Local HTTP mock with in-memory storage; not the production API."""

import json
from copy import deepcopy
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from threading import Lock

from support.validation import validate_attendance

ATTENDANCE_PATH = "/api/v1/attendance"


class AttendanceHandler(BaseHTTPRequestHandler):
    def do_POST(self):
        if self.path != ATTENDANCE_PATH:
            self.respond(404, {"success": False, "error": "Not found"})
            return
        try:
            payload = json.loads(self.rfile.read(int(self.headers.get("Content-Length", "0"))))
        except (ValueError, UnicodeDecodeError):
            self.respond(400, {"success": False, "error": {"field": "body", "message": "Invalid JSON"}})
            return
        error = validate_attendance(payload)
        if error:
            self.respond(400, {"success": False, "error": error})
            return
        # Validate the whole request before storing any attendance.
        with self.server.records_lock:
            self.server.records.append(deepcopy(payload))
        self.respond(201, {
            "success": True,
            "data": {
                **payload,
                "recorded_count": len(payload["participants"]),
                "present_count": sum(p["status"] == "PRESENT" for p in payload["participants"]),
                "absent_count": sum(p["status"] == "ABSENT" for p in payload["participants"]),
            },
        })

    def respond(self, status, body, headers=None):
        encoded = json.dumps(body).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(encoded)))
        for name, value in (headers or {}).items():
            self.send_header(name, value)
        self.end_headers()
        self.wfile.write(encoded)

    def method_not_allowed(self):
        self.respond(405, {"success": False, "error": "Method not allowed"}, {"Allow": "POST"})

    do_GET = do_PUT = do_PATCH = do_DELETE = method_not_allowed

    def log_message(self, format, *args):
        pass


class AttendanceServer(ThreadingHTTPServer):
    daemon_threads = True

    def __init__(self):
        super().__init__(("127.0.0.1", 0), AttendanceHandler)
        self.records = []
        self.records_lock = Lock()


def create_server():
    return AttendanceServer()
