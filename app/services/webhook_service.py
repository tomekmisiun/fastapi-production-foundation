from fastapi import HTTPException, status
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.core.webhook_security import WebhookSignatureError, hash_payload, verify_hmac_signature
from app.models.webhook_event import WebhookEvent


def persist_webhook_event(
    db: Session,
    *,
    provider: str,
    event_id: str,
    payload: bytes,
) -> WebhookEvent:
    event = WebhookEvent(
        provider=provider,
        event_id=event_id,
        payload_hash=hash_payload(payload),
    )

    db.add(event)

    try:
        db.commit()
    except IntegrityError:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Webhook event already processed",
        )

    db.refresh(event)

    return event


def verify_inbound_webhook_signature(
    *,
    payload: bytes,
    signature: str | None,
    secret: str,
) -> None:
    if signature is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Webhook signature header is required",
        )

    try:
        verify_hmac_signature(payload, signature, secret)
    except WebhookSignatureError as exc:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=str(exc),
        ) from exc
