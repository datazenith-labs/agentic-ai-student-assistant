"""
Test the advisor server end-to-end + cross-server chaining.

Verifies:
  Turn 1: get_student_profile reads the seeded StudentProfile row
  Turn 2: recommend_courses uses the student's completed courses
  Turn 3: check_prerequisites for a course that's blocked
  Turn 4: CROSS-SERVER chain - get_student_profile (advisor) +
          identify_weak_topics (exam_prep) in one turn

Run with:  python test_advisor.py
"""

import asyncio

from sqlalchemy import select

from backend.assistant.client import chat
from backend.database.connection import AsyncSessionLocal
from backend.database.models import Session as DBSession, User


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

    session = DBSession(user_id=user.id, title="Step 10 advisor test")
    db.add(session)
    await db.commit()
    await db.refresh(session)
    print(f"  User ID:    {user.id}")
    print(f"  Session ID: {session.id}")
    return user.id, session.id


async def run_turn(turn_num: int, label: str, user_id: str, session_id: str, message: str):
    print("\n" + "=" * 75)
    print(f"TURN {turn_num} — {label}")
    print("=" * 75)
    print(f"Student: {message}\n")

    async with AsyncSessionLocal() as db:
        result = await chat(db, user_id, session_id, message)

    print(f"SAGE (iter={result['iterations']}, tools={result['tools_used']}):")
    print("-" * 75)
    print(result["reply"])
    print("-" * 75)
    return result


async def main():
    print("=" * 75)
    print("SETUP")
    print("=" * 75)
    async with AsyncSessionLocal() as db:
        user_id, session_id = await get_or_create_user_and_session(db)

    # ── Turn 1 — profile readback ─────────────────────────────────────
    await run_turn(
        1,
        "Student asks 'what do you know about me?'",
        user_id,
        session_id,
        "What do you know about me from my profile? Just the highlights.",
    )

    # ── Turn 2 — course recommendation ────────────────────────────────
    await run_turn(
        2,
        "Course recommendations",
        user_id,
        session_id,
        (
            "What courses should I take next semester? "
            "I've already completed CS101, CS102, CS201, CS202, MATH201, MATH202."
        ),
    )

    # ── Turn 3 — prerequisite check ───────────────────────────────────
    await run_turn(
        3,
        "Prerequisite check (CS402 — blocked because CS401 not done)",
        user_id,
        session_id,
        "Can I take CS402 next semester? I've done CS101, CS102, CS201, CS202, MATH201, MATH202.",
    )

    # ── Turn 4 — CROSS-SERVER chain (the headline) ────────────────────
    await run_turn(
        4,
        "CROSS-SERVER chain: profile (advisor) + weak topics (exam_prep)",
        user_id,
        session_id,
        (
            "Based on BOTH my profile AND my weak topics from earlier "
            "self-assessments, what should I focus on this month?"
        ),
    )

    print("\n" + "=" * 75)
    print("Advisor server test complete.")
    print()
    print("What to look for:")
    print("  Turn 1: tools contains 'get_student_profile'")
    print("  Turn 2: tools contains 'recommend_courses'")
    print("  Turn 3: tools contains 'check_prerequisites' and Claude")
    print("          notes CS401 is missing")
    print("  Turn 4: tools contains BOTH 'get_student_profile' AND")
    print("          'identify_weak_topics' (cross-server orchestration)")
    print("=" * 75)


if __name__ == "__main__":
    asyncio.run(main())