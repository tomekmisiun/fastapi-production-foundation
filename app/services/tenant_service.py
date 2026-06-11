from fastapi import HTTPException, Request, status
from sqlalchemy.orm import Session

from app.core.tenant_context import DEFAULT_TENANT_SLUG, get_tenant_id
from app.models.tenant import Tenant


def get_tenant_by_slug(db: Session, slug: str) -> Tenant | None:
    return db.query(Tenant).filter(Tenant.slug == slug).first()


def get_tenant_by_id(db: Session, tenant_id: int) -> Tenant | None:
    return db.query(Tenant).filter(Tenant.id == tenant_id).first()


def resolve_tenant_slug(request: Request) -> str:
    return request.headers.get("X-Tenant-Slug", DEFAULT_TENANT_SLUG)


def get_active_tenant_by_slug(db: Session, slug: str) -> Tenant:
    tenant = get_tenant_by_slug(db, slug)

    if tenant is None or not tenant.is_active:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Tenant not found",
        )

    return tenant


def get_required_tenant_id() -> int:
    tenant_id = get_tenant_id()

    if tenant_id is None:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Tenant context is required",
        )

    return tenant_id


def build_tenant_cache_prefix(tenant_id: int) -> str:
    return f"tenant:{tenant_id}"


def build_tenant_object_key_prefix(tenant_id: int) -> str:
    return f"tenants/{tenant_id}"
