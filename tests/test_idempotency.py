from datetime import datetime, timedelta, timezone

import pytest
from fastapi import HTTPException

from app.services.idempotency_service import (
    build_scope_key,
    get_cached_response,
    store_response,
)


def test_build_scope_key_normalizes_input():
    first_scope = build_scope_key("webhooks:inbound", "  key-1  ")
    second_scope = build_scope_key("webhooks:inbound", "key-1")

    assert first_scope == second_scope


def test_build_scope_key_requires_non_empty_key():
    with pytest.raises(HTTPException) as exc_info:
        build_scope_key("webhooks:inbound", "   ")

    assert exc_info.value.status_code == 400


def test_get_cached_response_ignores_expired_records(db):
    scope_key = build_scope_key("webhooks:inbound", "expired-key")
    expired_record = store_response(
        db,
        scope_key=scope_key,
        status_code=200,
        response_body={"status": "accepted"},
    )
    expired_record.expires_at = datetime.now(timezone.utc) - timedelta(seconds=1)
    db.commit()

    assert get_cached_response(db, scope_key) is None
