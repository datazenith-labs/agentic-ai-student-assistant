"""
Test the campus server end-to-end + full three-server orchestration.

Verifies:
  Turn 1: add_deadline creates a new task row
  Turn 2: add_deadline again (so we have 2+ tasks to list)
  Turn 3: list_upcoming_deadlines returns them sorted by due date
  Turn 4: get_timetable_summary returns the weekly schedule
  Turn 5: FULL-STACK CHAIN - all three servers in one turn
          (get_timetable_summary + list_upcoming_deadlines +
           identify_weak_topics + get_student_profile)

Run with:  python test_campus.py
"""

import asyncio
from datetime import datetime, timedelta, timezone

from sqlalchemy import select

from backend.assistant.client import chat
from backend.database.connection import AsyncSessionLocal
from backend.database.models import Session as DBSession, Task, User


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

    session = DBSession(user_id=user.id, title="Step 11 campus test")
    db.add(session)
    await db.commit()
    await db.refresh(session)
    print(f"  User ID:    {user.id}")
    print(f"  Session ID: {session.id}")
    return user.id, session.id


async def show_tasks(db, user_id: str) -> None:
    """Print pending tasks for this user — quick verification."""
    stmt = (
        select(Task)
        .where(Task.user_id == user_id)
        .where(Task.status != "done")
        .order_by(Task.due_date.asc())
    )
    result = await db.execute(stmt)
    tasks = result.scalars().all()
    print(f"\n  Pending tasks for this user ({len(tasks)}):")
    for t in tasks:
        due = t.due_date.strftime("%Y-%m-%d") if t.due_date else "no date"
        print(f"    [{due}] [{t.priority:6}] {t.subject:8} — {t.title}")


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

    today = datetime.now(timezone.utc).date()
    in_3_days = (today + timedelta(days=3)).isoformat()
    in_8_days = (today + timedelta(days=8)).isoformat()

    # ── Turn 1 — add first deadline ───────────────────────────────────
    await run_turn(
        1,
        "Add deadline #1 (assignment in 3 days)",
        user_id,
        session_id,
        f"I have a Machine Learning assignment due on {in_3_days} for CS401. "
        f"It's high priority. Please add it.",
    )

    # ── Turn 2 — add second deadline ──────────────────────────────────
    await run_turn(
        2,
        "Add deadline #2 (OS midterm in 8 days)",
        user_id,
        session_id,
        f"Also, my Operating Systems midterm is on {in_8_days} for CS302. "
        f"Medium priority. Add that too.",
    )

    # Show the DB so we can see the rows landed
    async with AsyncSessionLocal() as db:
        await show_tasks(db, user_id)

    # ── Turn 3 — list deadlines ───────────────────────────────────────
    await run_turn(
        3,
        "List upcoming deadlines",
        user_id,
        session_id,
        "What's coming up in the next two weeks?",
    )

    # ── Turn 4 — get timetable ────────────────────────────────────────
    await run_turn(
        4,
        "Get timetable summary",
        user_id,
        session_id,
        "What does my Monday look like? And give me an overview of my whole week.",
    )

    # ── Turn 5 — THE BIG ONE: full three-server orchestration ─────────
    await run_turn(
        5,
        "FULL-STACK CHAIN: timetable + deadlines + weak topics + profile",
        user_id,
        session_id,
        (
            "I need a complete strategy for the next two weeks. "
            "Consider my weekly schedule, my upcoming deadlines, my weak "
            "topics from earlier self-assessments, and my profile. "
            "Where should my study time go, and how do I balance it with "
            "what's already on my plate?"
        ),
    )

    print("\n" + "=" * 75)
    print("Campus server test complete.")
    print()
    print("What to look for:")
    print("  Turn 1: tools contains 'add_deadline'")
    print("  Turn 2: tools contains 'add_deadline' (second insert)")
    print("  Turn 3: tools contains 'list_upcoming_deadlines'")
    print("          and Claude sorts them by due date")
    print("  Turn 4: tools contains 'get_timetable_summary'")
    print("  Turn 5: THE BIG MOMENT — tools should contain at LEAST 3 of:")
    print("            get_timetable_summary, list_upcoming_deadlines,")
    print("            identify_weak_topics, get_student_profile")
    print("          All three MCP servers fire in one turn.")
    print("=" * 75)


if __name__ == "__main__":
    asyncio.run(main())