from fastapi import APIRouter, Cookie, Depends, HTTPException, Response, status
from fastapi.security import OAuth2PasswordRequestForm
from jose import JWTError

from app.core.config import settings
from app.core.deps import get_current_user
from app.core.security import (
    create_access_token,
    create_refresh_token,
    decode_token,
    verify_password,
)
from app.models.auth import Token

router = APIRouter(prefix="/auth", tags=["auth"])

_REFRESH_COOKIE = "refresh_token"


@router.post("/login", response_model=Token)
async def login(
    response: Response,
    form_data: OAuth2PasswordRequestForm = Depends(),
) -> Token:
    if form_data.username != settings.APP_USERNAME or not verify_password(
        form_data.password, settings.APP_PASSWORD_HASH
    ):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    response.set_cookie(
        key=_REFRESH_COOKIE,
        value=create_refresh_token(form_data.username),
        httponly=True,
        samesite="lax",
        max_age=settings.REFRESH_TOKEN_EXPIRE_DAYS * 86_400,
    )
    return Token(access_token=create_access_token(form_data.username))


@router.post("/refresh", response_model=Token)
async def refresh(
    refresh_token: str | None = Cookie(default=None, alias=_REFRESH_COOKIE),
) -> Token:
    unauthorized = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Invalid or expired refresh token",
    )
    if not refresh_token:
        raise unauthorized
    try:
        payload = decode_token(refresh_token)
        if payload.get("type") != "refresh":
            raise unauthorized
        username: str | None = payload.get("sub")
        if not username or username != settings.APP_USERNAME:
            raise unauthorized
    except JWTError:
        raise unauthorized
    return Token(access_token=create_access_token(username))


@router.post("/logout")
async def logout(response: Response) -> dict[str, str]:
    response.delete_cookie(_REFRESH_COOKIE)
    return {"message": "Logged out"}


@router.get("/me")
async def me(username: str = Depends(get_current_user)) -> dict[str, str]:
    return {"username": username}
