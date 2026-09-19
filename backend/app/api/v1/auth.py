from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_user, get_db
from app.core.config import settings
from app.core.errors import AppError, AuthenticationError
from app.core.security import create_access_token, hash_password, verify_password
from app.models.user import User
from app.schemas.auth import Token, UserCreate, UserLogin, UserResponse

router = APIRouter(prefix="/auth", tags=["Authentication"])


@router.post(
    "/register",
    response_model=UserResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Register a new user account",
)
async def register(
    user_in: UserCreate,
    db: AsyncSession = Depends(get_db),
) -> User:
    """Creates a new user with hashed password and returns the public user profile."""
    query = select(User).where(User.email == user_in.email)
    existing_user = (await db.execute(query)).scalar_one_or_none()
    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="A user with this email address already exists",
        )

    user = User(
        email=user_in.email,
        hashed_password=hash_password(user_in.password),
        is_active=True,
    )
    db.add(user)
    await db.commit()
    await db.refresh(user)
    return user


@router.post(
    "/login",
    response_model=Token,
    summary="Obtain a JWT Bearer access token",
)
async def login(
    user_in: UserLogin,
    db: AsyncSession = Depends(get_db),
) -> Token:
    """Authenticates credentials and issues a signed JSON Web Token."""
    query = select(User).where(User.email == user_in.email)
    user = (await db.execute(query)).scalar_one_or_none()

    if not user or not verify_password(user_in.password, user.hashed_password):
        raise AuthenticationError("Incorrect email or password")

    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="User account is deactivated",
        )

    token = create_access_token(
        subject=str(user.id),
        extra_claims={"email": user.email},
    )
    return Token(
        access_token=token,
        token_type="bearer",
        expires_in_minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES,
    )


@router.get(
    "/me",
    response_model=UserResponse,
    summary="Get profile of the currently authenticated user",
)
async def get_current_user_profile(
    current_user: User = Depends(get_current_user),
) -> User:
    """Returns the authenticated user's profile information."""
    return current_user
