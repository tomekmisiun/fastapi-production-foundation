import hashlib
import hmac


class WebhookSignatureError(ValueError):
    pass


def hash_payload(payload: bytes) -> str:
    return hashlib.sha256(payload).hexdigest()


def compute_hmac_signature(payload: bytes, secret: str) -> str:
    return hmac.new(
        secret.encode("utf-8"),
        payload,
        hashlib.sha256,
    ).hexdigest()


def verify_hmac_signature(
    payload: bytes,
    signature: str,
    secret: str,
) -> None:
    if not secret:
        raise WebhookSignatureError("Webhook signature secret is not configured")

    expected_signature = compute_hmac_signature(payload, secret)

    if not hmac.compare_digest(expected_signature, signature):
        raise WebhookSignatureError("Invalid webhook signature")
