"""Auth — minimal JWT login.

Wave 1 scope: password-based login against ``participants`` table, returns
a JWT bearer token. No registration flow yet (seed users via script).
"""

from __future__ import annotations

import uuid
from datetime import datetime, timedelta, timezone

import bcrypt
import jwt
from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from pydantic import BaseModel, EmailStr
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.config import get_settings
from src.db.models import Participant
from src.db.session import get_db

router = APIRouter(prefix="/auth", tags=["auth"])
bearer_scheme = HTTPBearer(auto_error=False)


class LoginRequest(BaseModel):
    email: EmailStr
    password: str


class LoginResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    participant_id: uuid.UUID
    role: str
    name: str


class MeResponse(BaseModel):
    participant_id: uuid.UUID
    role: str
    name: str


def _make_token(participant: Participant) -> str:
    settings = get_settings()
    payload = {
        "sub": str(participant.id),
        "role": participant.role,
        "name": participant.name,
        "exp": datetime.now(timezone.utc) + timedelta(hours=settings.jwt_expire_hours),
    }
    return jwt.encode(payload, settings.jwt_secret, algorithm=settings.jwt_algorithm)


@router.post("/login", response_model=LoginResponse)
async def login(payload: LoginRequest, db: AsyncSession = Depends(get_db)) -> LoginResponse:
    p = await db.scalar(select(Participant).where(Participant.email == payload.email))
    if p is None or p.hashed_password is None:
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, detail="invalid credentials")
    if not bcrypt.checkpw(payload.password.encode(), p.hashed_password.encode()):
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, detail="invalid credentials")
    return LoginResponse(
        access_token=_make_token(p),
        participant_id=p.id,
        role=p.role,
        name=p.name,
    )


async def get_current_participant(
    credentials: HTTPAuthorizationCredentials | None = Depends(bearer_scheme),
    db: AsyncSession = Depends(get_db),
) -> Participant:
    if credentials is None:
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, detail="missing bearer token")
    settings = get_settings()
    try:
        payload = jwt.decode(
            credentials.credentials,
            settings.jwt_secret,
            algorithms=[settings.jwt_algorithm],
        )
    except jwt.PyJWTError as exc:
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, detail=f"invalid token: {exc}") from exc

    p = await db.scalar(select(Participant).where(Participant.id == uuid.UUID(payload["sub"])))
    if p is None:
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, detail="participant not found")
    return p


def require_role(*allowed: str):
    """Dependency factory — gates an endpoint by participant.role."""

    async def _check(p: Participant = Depends(get_current_participant)) -> Participant:
        if p.role not in allowed:
            raise HTTPException(
                status.HTTP_403_FORBIDDEN,
                detail=f"role '{p.role}' not in {allowed}",
            )
        return p

    return _check


@router.get("/me", response_model=MeResponse)
async def me(p: Participant = Depends(get_current_participant)) -> MeResponse:
    return MeResponse(participant_id=p.id, role=p.role, name=p.name)
