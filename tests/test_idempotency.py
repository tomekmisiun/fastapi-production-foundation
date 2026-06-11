from app.services.idempotency_service import build_scope_key


def test_build_scope_key_normalizes_input():
    first_scope = build_scope_key("webhooks:inbound", "  key-1  ")
    second_scope = build_scope_key("webhooks:inbound", "key-1")

    assert first_scope == second_scope
