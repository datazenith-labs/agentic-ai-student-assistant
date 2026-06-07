"""
Test the production assistant client end-to-end.

Verifies:
  - A user and session can be created
  - Three sequential messages all get saved
  - Turn 3 correctly references something from Turn 1 (memory works!)
  - Tools are recorded with each assistant message

Run with:  python test_client.py
"""

import asyncio

from sqlalchemy import select

from backend.assistant.client import chat
from backend.database.connection import AsyncSessionLocal
from backend.database.models import Message, Session as DBSession, User


TEST_USER_EMAIL = "abrar@sage.test"


async def get_or_create_test_user_and_session(db) -> tuple[str, str]:
    """Create a test user and session if they don't exist; return both IDs."""
    # Look for an existing test user
    stmt = select(User).where(User.email == TEST_USER_EMAIL)
    result = await db.execute(stmt)
    user = result.scalar_one_or_none()

    if user is None:
        print(f"  Creating test user: {TEST_USER_EMAIL}")
        user = User(
            email=TEST_USER_EMAIL,
            password_hash="not-a-real-hash-for-testing",
            name="Abrar (test)",
        )
        db.add(user)
        await db.commit()
        await db.refresh(user)
    else:
        print(f"  Test user already exists: {user.id}")

    # Always create a fresh session for this test run
    session = DBSession(user_id=user.id, title="Step 7A test conversation")
    db.add(session)
    await db.commit()
    await db.refresh(session)
    print(f"  Created fresh session: {session.id}")

    return user.id, session.id


async def show_saved_messages(db, session_id: str) -> None:
    """Read all messages from this session and print them."""
    stmt = (
        select(Message)
        .where(Message.session_id == session_id)
        .order_by(Message.created_at.asc())
    )
    result = await db.execute(stmt)
    messages = result.scalars().all()

    print(f"\nMessages saved to DB for this session: {len(messages)}")
    for i, m in enumerate(messages, start=1):
        preview = m.content[:100].replace("\n", " ")
        tools_part = ""
        if m.tools_used and m.tools_used.get("tools"):
            tools_part = f"  [tools: {m.tools_used['tools']}]"
        print(f"  {i}. [{m.role:9}] {preview}...{tools_part}")


async def main():
    print("=" * 70)
    print("SETUP")
    print("=" * 70)

    async with AsyncSessionLocal() as db:
        user_id, session_id = await get_or_create_test_user_and_session(db)

    # ── Turn 1 ─────────────────────────────────────────────────────
    print("\n" + "=" * 70)
    print("TURN 1 - Document-grounded question")
    print("=" * 70)
    message_1 = (
        "I just uploaded a paper to my collection 'test_collection_5'. "
        "What does it say about positional encoding? Keep it short."
    )
    print(f"Student: {message_1}\n")

    async with AsyncSessionLocal() as db:
        result_1 = await chat(db, user_id, session_id, message_1)

    print(f"SAGE (after {result_1['iterations']} iteration(s), "
          f"tools: {result_1['tools_used']}):")
    print("-" * 70)
    print(result_1["reply"])
    print("-" * 70)

    # ── Turn 2 ─────────────────────────────────────────────────────
    print("\n" + "=" * 70)
    print("TURN 2 - Follow-up requesting a quiz on the SAME topic")
    print("=" * 70)
    message_2 = "Great. Now quiz me on that topic with 2 questions."
    print(f"Student: {message_2}\n")

    async with AsyncSessionLocal() as db:
        result_2 = await chat(db, user_id, session_id, message_2)

    print(f"SAGE (after {result_2['iterations']} iteration(s), "
          f"tools: {result_2['tools_used']}):")
    print("-" * 70)
    print(result_2["reply"])
    print("-" * 70)

    # ── Turn 3 - the memory test ───────────────────────────────────
    print("\n" + "=" * 70)
    print("TURN 3 - The memory test (references Turn 1 without restating)")
    print("=" * 70)
    message_3 = (
        "Without searching again, what was the very first thing I asked you about?"
    )
    print(f"Student: {message_3}\n")

    async with AsyncSessionLocal() as db:
        result_3 = await chat(db, user_id, session_id, message_3)

    print(f"SAGE (after {result_3['iterations']} iteration(s), "
          f"tools: {result_3['tools_used']}):")
    print("-" * 70)
    print(result_3["reply"])
    print("-" * 70)

    # ── Inspect what got saved ─────────────────────────────────────
    print("\n" + "=" * 70)
    print("DATABASE INSPECTION")
    print("=" * 70)
    async with AsyncSessionLocal() as db:
        await show_saved_messages(db, session_id)

    print("\n" + "=" * 70)
    print("If Turn 3 correctly mentioned 'positional encoding' (or similar)")
    print("WITHOUT calling search_materials again, conversation memory works.")
    print("=" * 70)


if __name__ == "__main__":
    asyncio.run(main())