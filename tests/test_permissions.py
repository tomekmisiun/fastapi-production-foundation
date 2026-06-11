from types import SimpleNamespace

from app.core.permissions import Permission
from app.services.permission_service import (
    can_read_user,
    can_update_user,
    get_permissions_for_role,
    role_includes,
    user_has_permission,
)


def make_user(user_id: int, role: str):
    return SimpleNamespace(id=user_id, role=role)


def test_admin_role_has_full_permission_set():
    permissions = get_permissions_for_role("admin")

    assert Permission.USERS_LIST in permissions
    assert Permission.AUDIT_LOGS_LIST in permissions
    assert Permission.ADMIN_ACCESS in permissions


def test_user_role_has_self_service_permissions_only():
    permissions = get_permissions_for_role("user")

    assert Permission.USERS_READ_SELF in permissions
    assert Permission.USERS_UPDATE_SELF in permissions
    assert Permission.FILES_UPLOAD in permissions
    assert Permission.USERS_LIST not in permissions
    assert Permission.ADMIN_ACCESS not in permissions


def test_role_hierarchy_allows_admin_to_satisfy_user_role_checks():
    admin = make_user(1, "admin")

    assert role_includes(admin.role, "admin") is True
    assert role_includes(admin.role, "user") is True


def test_role_hierarchy_does_not_elevate_regular_users():
    user = make_user(2, "user")

    assert role_includes(user.role, "admin") is False
    assert role_includes(user.role, "user") is True


def test_can_read_user_allows_self_read_for_regular_user():
    user = make_user(3, "user")

    assert can_read_user(user, 3) is True
    assert can_read_user(user, 4) is False


def test_can_read_user_allows_admin_to_read_any_user():
    admin = make_user(1, "admin")

    assert can_read_user(admin, 99) is True


def test_can_update_user_allows_self_update_for_regular_user():
    user = make_user(3, "user")

    assert can_update_user(user, 3) is True
    assert can_update_user(user, 4) is False


def test_user_has_permission_reflects_role_policy():
    admin = make_user(1, "admin")
    user = make_user(2, "user")

    assert user_has_permission(admin, Permission.USERS_DELETE) is True
    assert user_has_permission(user, Permission.USERS_DELETE) is False
