"""Seed demo users — one teacher + one student for development.

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
        "name": "示範教師",
        "email": "teacher@ticdss.local",
        "role": "teacher",
        "password": "demo-teacher-pwd",
    },
    {
        "name": "示範學生",
        "email": "student@ticdss.local",
        "role": "student",
        "password": "demo-student-pwd",
    },
]


async def main():
    async with AsyncSessionLocal() as db:
        for u in DEMO_USERS:
            existing = await db.scalar(
                select(Participant).where(Participant.email == u["email"])
            )
            if existing:
                print(f"SKIP {u['email']} (already exists)")
                continue
            hashed = bcrypt.hashpw(u["password"].encode(), bcrypt.gensalt()).decode()
            db.add(
                Participant(
                    name=u["name"],
                    email=u["email"],
                    role=u["role"],
                    hashed_password=hashed,
                )
            )
            await db.commit()
            print(f"OK   {u['email']} ({u['role']}) — password: {u['password']}")


if __name__ == "__main__":
    asyncio.run(main())
