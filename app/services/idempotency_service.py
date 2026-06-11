import hashlib
import json
from datetime import datetime, timedelta, timezone

from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from app.core.config import settings
from app.models.idempotency_record import IdempotencyRecord


def build_scope_key(scope: str, idempotency_key: str) -> str:
    normalized_key = idempotency_key.strip()

    if not normalized_key:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Idempotency-Key header is required",
        )

    digest = hashlib.sha256(
        f"{scope}:{normalized_key}".encode("utf-8")
    ).hexdigest()

    return f"{scope}:{digest}"


def get_cached_response(db: Session, scope_key: str) -> IdempotencyRecord | None:
    now = datetime.now(timezone.utc)

    return (
        db.query(IdempotencyRecord)
        .filter(
            IdempotencyRecord.scope_key == scope_key,
            IdempotencyRecord.expires_at > now,
        )
        .first()
    )


def store_response(
    db: Session,
    *,
    scope_key: str,
    status_code: int,
    response_body: dict,
) -> IdempotencyRecord:
    expires_at = datetime.now(timezone.utc) + timedelta(
        seconds=settings.idempotency_ttl_seconds
    )
    record = IdempotencyRecord(
        scope_key=scope_key,
        status_code=status_code,
        response_body=json.dumps(response_body),
        expires_at=expires_at,
    )

    db.add(record)
    db.commit()
    db.refresh(record)

    return record


def parse_cached_response_body(record: IdempotencyRecord) -> dict:
    return json.loads(record.response_body)
