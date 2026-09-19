import uuid
from typing import AsyncGenerator
from fastapi import Depends
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.core.database import get_async_session
from app.core.errors import AuthenticationError, PermissionDeniedError
from app.core.security import decode_access_token
from app.models.user import User

# OAuth2 scheme pointing to our login endpoint for Swagger UI authorization
oauth2_scheme = OAuth2PasswordBearer(
    tokenUrl=f"{settings.API_V1_STR}/auth/login",
    auto_error=False,
)


async def get_db() -> AsyncGenerator[AsyncSession, None]:
    """Dependency for injecting async database sessions into API endpoints."""
    async for session in get_async_session():
        yield session


async def get_current_user(
    token: str = Depends(oauth2_scheme),
    db: AsyncSession = Depends(get_db),
) -> User:
    """Dependency that extracts and validates the Bearer JWT and returns the User model."""
    if not token:
        raise AuthenticationError("Authorization token is missing")

    try:
        payload = decode_access_token(token)
        user_id_str: str = payload.get("sub")
        if not user_id_str:
            raise AuthenticationError("Token payload missing subject identifier")
        user_id = uuid.UUID(user_id_str)
    except Exception:
        raise AuthenticationError("Invalid or expired authentication token")

    query = select(User).where(User.id == user_id)
    result = await db.execute(query)
    user = result.scalar_one_or_none()

    if not user:
        raise AuthenticationError("User associated with this token does not exist")

    if not user.is_active:
        raise PermissionDeniedError("User account is deactivated")

    return user
