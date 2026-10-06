"""Assumed attendance validation; sample ID prefixes are not enforced."""

from datetime import date


def validate_attendance(payload):
    if not isinstance(payload, dict):
        return {"field": "body", "message": "Must be a JSON object"}
    for field in ("mentor_id", "bootcamp_id", "session_date"):
        value = payload.get(field)
        if not isinstance(value, str) or not value.strip():
            return {"field": field, "message": "Required non-empty string"}
    try:
        value = payload["session_date"]
        if date.fromisoformat(value).isoformat() != value:
            raise ValueError
    except ValueError:
        return {"field": "session_date", "message": "Must be a valid YYYY-MM-DD date"}

    participants = payload.get("participants")
    if not isinstance(participants, list) or not participants:
        return {"field": "participants", "message": "Must be a non-empty array"}
    seen = set()
    for index, participant in enumerate(participants):
        prefix = f"participants[{index}]"
        if not isinstance(participant, dict):
            return {"field": prefix, "message": "Must be an object"}
        participant_id = participant.get("participant_id")
        if not isinstance(participant_id, str) or not participant_id.strip():
            return {"field": f"{prefix}.participant_id", "message": "Required non-empty string"}
        if participant_id in seen:
            return {"field": f"{prefix}.participant_id", "message": "Duplicate participant_id"}
        seen.add(participant_id)
        if participant.get("status") not in ("PRESENT", "ABSENT"):
            return {"field": f"{prefix}.status", "message": "Must be PRESENT or ABSENT"}
    return None
