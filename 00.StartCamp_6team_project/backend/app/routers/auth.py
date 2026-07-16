from dataclasses import dataclass
from datetime import datetime, timedelta

from fastapi import APIRouter, Depends, Header, HTTPException
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from ..database import get_db
from ..models import AuthSession, User
from ..schemas import AuthResponse, LoginRequest, SignUpRequest, UserOut
from ..security import (
    create_session_token,
    hash_password,
    hash_session_token,
    verify_password,
)

router = APIRouter(prefix="/api/auth", tags=["auth"])

_SESSION_LIFETIME = timedelta(days=14)
# A real hash keeps unknown-user login timing close to wrong-password timing.
_DUMMY_PASSWORD_HASH = hash_password("not-a-real-account-password")


@dataclass(frozen=True)
class AuthContext:
    user: User
    session: AuthSession


def _unauthorized(detail: str = "로그인이 필요합니다.") -> HTTPException:
    return HTTPException(
        status_code=401,
        detail=detail,
        headers={"WWW-Authenticate": "Bearer"},
    )


def get_optional_auth_context(
    authorization: str | None = Header(default=None),
    db: Session = Depends(get_db),
) -> AuthContext | None:
    if authorization is None:
        return None

    scheme, separator, token = authorization.partition(" ")
    if separator != " " or scheme.lower() != "bearer" or not token:
        raise _unauthorized("올바른 Bearer 인증 정보가 아닙니다.")
    if len(token) > 512:
        raise _unauthorized("올바르지 않은 세션입니다.")

    auth_session = db.get(AuthSession, hash_session_token(token))
    if auth_session is None:
        raise _unauthorized("세션이 만료되었거나 올바르지 않습니다.")

    now = datetime.utcnow()
    if auth_session.expires_at <= now:
        db.delete(auth_session)
        db.commit()
        raise _unauthorized("세션이 만료되었습니다. 다시 로그인해 주세요.")

    return AuthContext(user=auth_session.user, session=auth_session)


def get_optional_user(
    context: AuthContext | None = Depends(get_optional_auth_context),
) -> User | None:
    return context.user if context else None


def get_current_user(
    context: AuthContext | None = Depends(get_optional_auth_context),
) -> User:
    if context is None:
        raise _unauthorized()
    return context.user


def _new_session(user: User, db: Session) -> tuple[str, datetime]:
    raw_token = create_session_token()
    expires_at = datetime.utcnow() + _SESSION_LIFETIME
    db.add(
        AuthSession(
            token_hash=hash_session_token(raw_token),
            user_id=user.id,
            expires_at=expires_at,
        )
    )
    return raw_token, expires_at


def _auth_response(user: User, raw_token: str, expires_at: datetime) -> AuthResponse:
    return AuthResponse(
        token=raw_token,
        access_token=raw_token,
        expires_at=expires_at,
        user=UserOut.model_validate(user),
    )


@router.post("/signup", response_model=AuthResponse, status_code=201)
def signup(payload: SignUpRequest, db: Session = Depends(get_db)) -> AuthResponse:
    email = payload.email.strip().lower()
    if db.scalar(select(User.id).where(User.email == email)) is not None:
        raise HTTPException(status_code=409, detail="이미 가입된 이메일입니다.")

    user = User(
        email=email,
        nickname=payload.nickname,
        password_hash=hash_password(payload.password),
    )
    db.add(user)
    try:
        db.flush()
        raw_token, expires_at = _new_session(user, db)
        db.commit()
        db.refresh(user)
    except IntegrityError:
        db.rollback()
        raise HTTPException(status_code=409, detail="이미 가입된 이메일입니다.")
    return _auth_response(user, raw_token, expires_at)


@router.post("/login", response_model=AuthResponse)
def login(payload: LoginRequest, db: Session = Depends(get_db)) -> AuthResponse:
    email = payload.email.strip().lower()
    user = db.scalar(select(User).where(User.email == email))
    password_hash = user.password_hash if user else _DUMMY_PASSWORD_HASH
    password_matches = verify_password(payload.password, password_hash)
    if user is None or not password_matches:
        raise _unauthorized("이메일 또는 비밀번호가 올바르지 않습니다.")

    raw_token, expires_at = _new_session(user, db)
    db.commit()
    return _auth_response(user, raw_token, expires_at)


@router.get("/me", response_model=UserOut)
def me(user: User = Depends(get_current_user)) -> User:
    return user


@router.post("/logout", status_code=204)
def logout(
    context: AuthContext | None = Depends(get_optional_auth_context),
    db: Session = Depends(get_db),
) -> None:
    if context is None:
        raise _unauthorized()
    db.delete(context.session)
    db.commit()
