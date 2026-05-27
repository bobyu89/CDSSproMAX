"""Seed demo participants — codes match cdss-training conventions.

Codes:
  P001  學員（student）
  P002  學員
  T001  教師（teacher）
  ADMIN001  管理員

Usage:
    uv run --project apps/api python scripts/seed_users.py
"""

from __future__ import annotations

import asyncio
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO_ROOT / "apps" / "api"))

import bcrypt  # noqa: E402
from sqlalchemy import select  # noqa: E402

from src.db.models import Participant  # noqa: E402
from src.db.session import AsyncSessionLocal  # noqa: E402


DEMO_USERS = [
    {
        "code": "P001",
        "name": "示範學員一號",
        "email": "p001@ticdss.local",
        "role": "student",
        "password": "demo1234",
    },
    {
        "code": "P002",
        "name": "示範學員二號",
        "email": "p002@ticdss.local",
        "role": "student",
        "password": "demo1234",
    },
    {
        "code": "T001",
        "name": "示範教師",
        "email": "t001@ticdss.local",
        "role": "teacher",
        "password": "demo1234",
    },
    {
        "code": "ADMIN001",
        "name": "系統管理員",
        "email": "admin@ticdss.local",
        "role": "admin",
        "password": "admin1234",
    },
]


async def main():
    async with AsyncSessionLocal() as db:
        for u in DEMO_USERS:
            existing = await db.scalar(
                select(Participant).where(Participant.participant_code == u["code"])
            )
            if existing:
                print(f"SKIP {u['code']} (already exists)")
                continue
            hashed = bcrypt.hashpw(u["password"].encode(), bcrypt.gensalt()).decode()
            db.add(
                Participant(
                    participant_code=u["code"],
                    name=u["name"],
                    email=u["email"],
                    role=u["role"],
                    hashed_password=hashed,
                )
            )
            await db.commit()
            print(f"OK   {u['code']} ({u['role']}) — password: {u['password']}")


if __name__ == "__main__":
    asyncio.run(main())
