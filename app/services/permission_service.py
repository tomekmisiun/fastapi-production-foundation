from app.core.permissions import ROLE_HIERARCHY, ROLE_PERMISSIONS, Permission
from app.models.user import User


def get_permissions_for_role(role: str) -> frozenset[Permission]:
    return ROLE_PERMISSIONS.get(role, frozenset())


def role_includes(actor_role: str, required_role: str) -> bool:
    return required_role in ROLE_HIERARCHY.get(actor_role, frozenset())


def user_has_permission(user: User, permission: Permission) -> bool:
    return permission in get_permissions_for_role(user.role)


def user_has_any_permission(user: User, *permissions: Permission) -> bool:
    role_permissions = get_permissions_for_role(user.role)

    return any(permission in role_permissions for permission in permissions)


def can_read_user(current_user: User, target_user_id: int) -> bool:
    if user_has_permission(current_user, Permission.USERS_READ):
        return True

    return (
        current_user.id == target_user_id
        and user_has_permission(current_user, Permission.USERS_READ_SELF)
    )


def can_update_user(current_user: User, target_user_id: int) -> bool:
    if user_has_permission(current_user, Permission.USERS_UPDATE):
        return True

    return (
        current_user.id == target_user_id
        and user_has_permission(current_user, Permission.USERS_UPDATE_SELF)
    )
