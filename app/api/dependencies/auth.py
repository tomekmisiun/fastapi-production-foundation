from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from jose import JWTError
from sqlalchemy.orm import Session

from app.core.permissions import Permission
from app.core.security import decode_token
from app.db.session import get_db
from app.models.user import User
from app.services.permission_service import role_includes, user_has_any_permission


bearer_scheme = HTTPBearer()


def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(bearer_scheme),
    db: Session = Depends(get_db),
) -> User:
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )

    try:
        payload = decode_token(credentials.credentials)
        token_type = payload.get("type")
        user_id = payload.get("sub")

        if token_type != "access" or user_id is None:
            raise credentials_exception
        parsed_user_id = int(user_id)

    except (JWTError, ValueError):
        raise credentials_exception

    user = db.query(User).filter(User.id == parsed_user_id).first()

    if user is None or not user.is_active:
        raise credentials_exception

    return user


def _forbidden() -> HTTPException:
    return HTTPException(
        status_code=status.HTTP_403_FORBIDDEN,
        detail="Insufficient permissions",
    )


def require_permission(*permissions: Permission):
    def checker(current_user: User = Depends(get_current_user)) -> User:
        if not user_has_any_permission(current_user, *permissions):
            raise _forbidden()

        return current_user

    return checker


def require_role(required_role: str):
    def checker(current_user: User = Depends(get_current_user)) -> User:
        if not role_includes(current_user.role, required_role):
            raise _forbidden()

        return current_user

    return checker
