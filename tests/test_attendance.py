"""Black-box HTTP checks of the documented mock attendance contract."""

from copy import deepcopy

import pytest

from support.payloads import many_participants


def assert_bad_request(response, field):
    assert response.status_code == 400, response.text
    assert response.headers["Content-Type"].startswith("application/json")
    body = response.json()
    assert body["success"] is False
    assert body["error"]["field"] == field
    assert isinstance(body["error"]["message"], str)
    assert body["error"]["message"]
    assert "data" not in body


@pytest.mark.happy_path
def test_valid_attendance_returns_created_and_success(client, valid_payload):
    response = client.submit(valid_payload)

    assert response.status_code == 201, response.text
    assert response.headers["Content-Type"].startswith("application/json")
    body = response.json()
    assert body["success"] is True
    assert body["data"] == {**valid_payload, "recorded_count": 2,
                            "present_count": 1, "absent_count": 1}


@pytest.mark.parametrize("field", ["mentor_id", "bootcamp_id", "session_date", "participants"])
@pytest.mark.validation
def test_missing_required_field_returns_bad_request(client, valid_payload, field):
    del valid_payload[field]
    assert_bad_request(client.submit(valid_payload), field)


@pytest.mark.parametrize("value", ["", "   ", None, 1042])
@pytest.mark.validation
def test_invalid_mentor_id_returns_bad_request(client, valid_payload, value):
    valid_payload["mentor_id"] = value
    assert_bad_request(client.submit(valid_payload), "mentor_id")


@pytest.mark.parametrize("status", ["LATE", "present", "", None, True])
@pytest.mark.validation
def test_invalid_status_returns_bad_request(client, valid_payload, status):
    valid_payload["participants"][0]["status"] = status
    assert_bad_request(client.submit(valid_payload), "participants[0].status")


@pytest.mark.edge_case
def test_empty_participants_returns_bad_request(client, valid_payload):
    valid_payload["participants"] = []
    assert_bad_request(client.submit(valid_payload), "participants")


@pytest.mark.edge_case
def test_duplicate_participant_ids_returns_bad_request(client, valid_payload):
    # Different statuses must not conceal the duplicate ID.
    valid_payload["participants"][1]["participant_id"] = "YTH-8821"
    response = client.submit(valid_payload)
    assert_bad_request(response, "participants[1].participant_id")
    assert response.json()["error"]["message"] == "Duplicate participant_id"


@pytest.mark.parametrize("participants", [None, {}, "YTH-8821", [None]])
@pytest.mark.validation
def test_invalid_participants_structure_returns_bad_request(client, valid_payload, participants):
    valid_payload["participants"] = participants
    field = "participants[0]" if participants == [None] else "participants"
    assert_bad_request(client.submit(valid_payload), field)


@pytest.mark.validation
def test_missing_participant_id_returns_bad_request(client, valid_payload):
    del valid_payload["participants"][0]["participant_id"]
    assert_bad_request(client.submit(valid_payload), "participants[0].participant_id")


@pytest.mark.parametrize("session_date", ["2026-02-30", "11/09/2026"])
@pytest.mark.validation
def test_invalid_session_date_returns_bad_request(client, valid_payload, session_date):
    valid_payload["session_date"] = session_date
    assert_bad_request(client.submit(valid_payload), "session_date")


@pytest.mark.validation
@pytest.mark.parametrize("raw", ["{not json", "", "null", "[]"],
                         ids=["malformed", "empty-body", "null-body", "array-body"])
def test_invalid_json_body_returns_bad_request(client, raw):
    assert_bad_request(client.submit_raw(raw), "body")


@pytest.mark.edge_case
@pytest.mark.parametrize("count", [1, 3, 500], ids=["single", "uneven-counts", "large-class"])
def test_attendance_counts_match_participants(client, valid_payload, count):
    valid_payload["participants"] = many_participants(count)
    response = client.submit(valid_payload)
    assert response.status_code == 201, response.text
    assert response.headers["Content-Type"].startswith("application/json")
    body = response.json()
    assert body["success"] is True
    assert body["data"] == {
        **valid_payload,
        "recorded_count": count,
        "present_count": (count + 1) // 2,
        "absent_count": count // 2,
    }


@pytest.mark.edge_case
def test_leap_day_is_accepted(client, valid_payload):
    valid_payload["session_date"] = "2024-02-29"
    response = client.submit(valid_payload)
    assert response.status_code == 201, response.text
    assert response.json()["success"] is True
    assert response.json()["data"]["session_date"] == "2024-02-29"


@pytest.mark.edge_case
@pytest.mark.parametrize("failure", ["empty", "invalid-second-status", "duplicate"])
def test_rejected_batch_stores_nothing(client, mock_server, valid_payload, failure):
    if mock_server is None:
        pytest.skip("Storage verification needs the local mock; real API needs a read endpoint")
    # Establish a stored record so we also detect accidental deletion.
    response = client.submit(valid_payload)
    assert response.status_code == 201, response.text
    before = deepcopy(mock_server.records)
    if failure == "empty":
        valid_payload["participants"] = []
        field = "participants"
    elif failure == "invalid-second-status":
        valid_payload["participants"][1]["status"] = "LATE"
        field = "participants[1].status"
    else:
        valid_payload["participants"][1]["participant_id"] = "YTH-8821"
        field = "participants[1].participant_id"
    assert_bad_request(client.submit(valid_payload), field)
    assert mock_server.records == before


@pytest.mark.contract
@pytest.mark.parametrize("method", ["GET", "PUT", "PATCH", "DELETE"])
def test_unsupported_methods_return_405(client, method):
    response = client.request(method)
    assert response.status_code == 405, response.text
    assert response.headers["Allow"] == "POST"
    assert response.headers["Content-Type"].startswith("application/json")
    assert response.json()["success"] is False
