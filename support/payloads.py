"""Fresh payload builders shared by fixtures and boundary tests."""

from copy import deepcopy

BASE_PAYLOAD = {
    "mentor_id": "MNT-1042",
    "bootcamp_id": "KMP-2026-09",
    "session_date": "2026-09-11",
    "participants": [
        {"participant_id": "YTH-8821", "status": "PRESENT"},
        {"participant_id": "YTH-8822", "status": "ABSENT"},
    ],
}


def attendance_payload(**overrides):
    payload = deepcopy(BASE_PAYLOAD)
    payload.update(overrides)
    return payload


def many_participants(count):
    return [
        {"participant_id": f"YTH-{1000 + index}",
         "status": "PRESENT" if index % 2 == 0 else "ABSENT"}
        for index in range(count)
    ]
