"""
Test the adaptive engine end-to-end.

Verifies:
  - Turn 1: Multiple confidence ratings get logged in one message (log_confidence x3)
  - Turn 2: identify_weak_topics correctly returns the lowest-scoring topics
  - Turn 3: generate_revision_plan produces a real, dated schedule
            (autonomously chained with identify_weak_topics)

Run with:  python test_adaptive.py
"""

import asyncio
from datetime import datetime, timezone

from sqlalchemy import select

from backend.assistant.client import chat
from backend.database.connection import AsyncSessionLocal
from backend.database.models import ConfidenceLog, Session as DBSession, User


TEST_USER_EMAIL = "abrar@sage.test"


async def get_or_create_user_and_session(db) -> tuple[str, str]:
    """Return existing test user's ID and create a fresh session for this run."""
    stmt = select(User).where(User.email == TEST_USER_EMAIL)
    result = await db.execute(stmt)
    user = result.scalar_one_or_none()
    if user is None:
        print("  Creating test user...")
        user = User(
            email=TEST_USER_EMAIL,
            password_hash="not-a-real-hash-for-testing",
            name="Abrar (test)",
        )
        db.add(user)
        await db.commit()
        await db.refresh(user)

    session = DBSession(user_id=user.id, title="Step 9 adaptive test")
    db.add(session)
    await db.commit()
    await db.refresh(session)
    print(f"  User ID:    {user.id}")
    print(f"  Session ID: {session.id}")
    return user.id, session.id


async def show_confidence_logs(db, user_id: str) -> None:
    stmt = (
        select(ConfidenceLog)
        .where(ConfidenceLog.user_id == user_id)
        .order_by(ConfidenceLog.created_at.desc())
        .limit(10)
    )
    result = await db.execute(stmt)
    logs = result.scalars().all()
    print(f"\n  Latest confidence_logs entries for this user ({len(logs)} shown):")
    for log in logs:
        print(f"    [{log.created_at:%Y-%m-%d %H:%M:%S}] {log.topic:30}  score={log.score}")


async def main():
    print("=" * 75)
    print("SETUP")
    print("=" * 75)
    async with AsyncSessionLocal() as db:
        user_id, session_id = await get_or_create_user_and_session(db)

    # ── Turn 1 — log multiple ratings ──────────────────────────────
    print("\n" + "=" * 75)
    print("TURN 1 — Student rates several topics in one message")
    print("=" * 75)
    message_1 = (
        "Quick self-assessment for you: I feel very confident on positional "
        "encoding (about 0.9), only medium on multi-head attention (around 0.5), "
        "and pretty weak on layer normalization (maybe 0.2). "
        "Please record these for me."
    )
    print(f"Student: {message_1}\n")

    async with AsyncSessionLocal() as db:
        result_1 = await chat(db, user_id, session_id, message_1)

    print(f"SAGE (iter={result_1['iterations']}, tools={result_1['tools_used']}):")
    print("-" * 75)
    print(result_1["reply"])
    print("-" * 75)

    # Show the database changed
    async with AsyncSessionLocal() as db:
        await show_confidence_logs(db, user_id)

    # ── Turn 2 — ask for weak topics ──────────────────────────────
    print("\n" + "=" * 75)
    print("TURN 2 — Student asks what to focus on")
    print("=" * 75)
    message_2 = "Based on my ratings, what should I focus on?"
    print(f"Student: {message_2}\n")

    async with AsyncSessionLocal() as db:
        result_2 = await chat(db, user_id, session_id, message_2)

    print(f"SAGE (iter={result_2['iterations']}, tools={result_2['tools_used']}):")
    print("-" * 75)
    print(result_2["reply"])
    print("-" * 75)

    # ── Turn 3 — ask for a revision plan ──────────────────────────
    print("\n" + "=" * 75)
    print("TURN 3 — Student asks for a study plan for an exam in 10 days")
    print("=" * 75)
    today = datetime.now(timezone.utc).date()
    message_3 = (
        f"My exam is in 10 days (today is {today.isoformat()}). "
        f"Build me a revision plan focused on my weak areas. "
        f"2 hours per day is fine."
    )
    print(f"Student: {message_3}\n")

    async with AsyncSessionLocal() as db:
        result_3 = await chat(db, user_id, session_id, message_3)

    print(f"SAGE (iter={result_3['iterations']}, tools={result_3['tools_used']}):")
    print("-" * 75)
    print(result_3["reply"])
    print("-" * 75)

    print("\n" + "=" * 75)
    print("Adaptive engine test complete.")
    print("If Turn 1 called log_confidence (1-3 times), Turn 2 called")
    print("identify_weak_topics, and Turn 3 chained identify_weak_topics ->")
    print("generate_revision_plan, the adaptive loop is working end-to-end.")
    print("=" * 75)


if __name__ == "__main__":
    asyncio.run(main())