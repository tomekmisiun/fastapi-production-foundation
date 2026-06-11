from fastapi import APIRouter, Depends, Header, HTTPException, Request, status
from fastapi.responses import JSONResponse
from sqlalchemy.orm import Session

from app.api.dependencies.idempotency import get_idempotency_key
from app.api.openapi import AUTH_ERROR_RESPONSES
from app.core.config import settings
from app.db.session import get_db
from app.schemas.webhook import WebhookInboundRequest, WebhookInboundResponse
from app.services.idempotency_service import (
    build_scope_key,
    get_cached_response,
    parse_cached_response_body,
    store_response,
)
from app.services.webhook_service import (
    persist_webhook_event,
    verify_inbound_webhook_signature,
)


router = APIRouter(prefix="/webhooks", tags=["webhooks"])


@router.post(
    "/inbound",
    response_model=WebhookInboundResponse,
    summary="Receive a signed inbound webhook",
    description=(
        "Provider-neutral webhook entrypoint with HMAC signature verification, "
        "event replay protection, and Idempotency-Key replay-safe response caching."
    ),
    responses=AUTH_ERROR_RESPONSES,
)
async def inbound_webhook(
    request: Request,
    db: Session = Depends(get_db),
    idempotency_key: str = Depends(get_idempotency_key),
    signature: str | None = Header(default=None, alias="X-Webhook-Signature"),
):
    raw_body = await request.body()
    scope_key = build_scope_key("webhooks:inbound", idempotency_key)
    cached_record = get_cached_response(db, scope_key)

    if cached_record is not None:
        return JSONResponse(
            status_code=cached_record.status_code,
            content=parse_cached_response_body(cached_record),
        )

    verify_inbound_webhook_signature(
        payload=raw_body,
        signature=signature,
        secret=settings.webhook_signature_secret,
    )

    payload = WebhookInboundRequest.model_validate_json(raw_body)

    try:
        persist_webhook_event(
            db,
            provider=payload.provider,
            event_id=payload.event_id,
            payload=raw_body,
        )
    except HTTPException as exc:
        if exc.status_code == status.HTTP_409_CONFLICT:
            response_body = {
                "status": "duplicate",
                "provider": payload.provider,
                "event_id": payload.event_id,
            }
            store_response(
                db,
                scope_key=scope_key,
                status_code=status.HTTP_409_CONFLICT,
                response_body=response_body,
            )
            return JSONResponse(status_code=status.HTTP_409_CONFLICT, content=response_body)

        raise

    response_body = {
        "status": "accepted",
        "provider": payload.provider,
        "event_id": payload.event_id,
    }
    store_response(
        db,
        scope_key=scope_key,
        status_code=status.HTTP_200_OK,
        response_body=response_body,
    )

    return response_body
