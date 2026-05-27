"""Auth — code+password login (mirrors cdss-training's participant_code flow).

Wave 1 scope: participant_code-based login (e.g. P001, T001, ADMIN001),
returns a JWT bearer token + expires_at timestamp the frontend store
uses for auto-expiry.
"""

from __future__ import annotations

import uuid
from datetime import datetime, timedelta, timezone

import bcrypt
import jwt
from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from pydantic import BaseModel
from sqlalchemy import or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from src.config import get_settings
from src.db.models import Participant
from src.db.session import get_db

router = APIRouter(prefix="/auth", tags=["auth"])
bearer_scheme = HTTPBearer(auto_error=False)


class LoginRequest(BaseModel):
    code: str  # participant_code, e.g. "P001"
    password: str


class ParticipantPublic(BaseModel):
    id: uuid.UUID
    participant_code: str
    role: str
    name: str


class LoginResponse(BaseModel):
    token: str
    expires_at: int  # unix seconds
    participant: ParticipantPublic


class MeResponse(ParticipantPublic):
    pass


def _make_token(p: Participant) -> tuple[str, int]:
    settings = get_settings()
    exp_dt = datetime.now(timezone.utc) + timedelta(hours=settings.jwt_expire_hours)
    expires_at = int(exp_dt.timestamp())
    payload = {
        "sub": str(p.id),
        "code": p.participant_code,
        "role": p.role,
        "name": p.name,
        "exp": expires_at,
    }
    return (
        jwt.encode(payload, settings.jwt_secret, algorithm=settings.jwt_algorithm),
        expires_at,
    )


@router.post("/login", response_model=LoginResponse)
async def login(payload: LoginRequest, db: AsyncSession = Depends(get_db)) -> LoginResponse:
    code = payload.code.strip()
    p = await db.scalar(
        select(Participant).where(
            or_(Participant.participant_code == code, Participant.email == code)
        )
    )
    if p is None or p.hashed_password is None:
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, detail="invalid credentials")
    if not bcrypt.checkpw(payload.password.encode(), p.hashed_password.encode()):
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, detail="invalid credentials")

    token, expires_at = _make_token(p)
    return LoginResponse(
        token=token,
        expires_at=expires_at,
        participant=ParticipantPublic(
            id=p.id,
            participant_code=p.participant_code,
            role=p.role,
            name=p.name,
        ),
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
    return MeResponse(
        id=p.id, participant_code=p.participant_code, role=p.role, name=p.name
    )
