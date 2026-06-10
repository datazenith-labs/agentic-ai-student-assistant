"""
SAGE - Seed a student profile for testing the advisor server.

Creates or updates one StudentProfile row for the test user so the
advisor tools have real data to work with.

Run once with:
    python seed_profile.py
"""

import asyncio

from sqlalchemy import select

from backend.database.connection import AsyncSessionLocal
from backend.database.models import StudentProfile, User


TEST_USER_EMAIL = "abrar@sage.test"


async def seed():
    async with AsyncSessionLocal() as db:
        # 1. Find the test user
        stmt = select(User).where(User.email == TEST_USER_EMAIL)
        result = await db.execute(stmt)
        user = result.scalar_one_or_none()
        if user is None:
            print(f"  ERROR: User '{TEST_USER_EMAIL}' not found.")
            print(f"  Run test_client.py once to create it, then retry.")
            return

        print(f"  Found user: {user.email} ({user.id})")

        # 2. Check if a profile already exists
        stmt = select(StudentProfile).where(StudentProfile.user_id == user.id)
        result = await db.execute(stmt)
        profile = result.scalar_one_or_none()

        if profile is None:
            profile = StudentProfile(
                user_id=user.id,
                major="Computer Science",
                year_of_study=3,
                weak_topics=["layer normalization", "multi-head attention"],
                strong_topics=["positional encoding", "linear algebra", "data structures"],
                goals="Become an AI engineer specialising in production LLM systems. Complete the bachelor's in CS this year with focus on machine learning electives.",
            )
            db.add(profile)
            print("  Created new student profile.")
        else:
            # Update with the same demo data (idempotent)
            profile.major = "Computer Science"
            profile.year_of_study = 3
            profile.weak_topics = ["layer normalization", "multi-head attention"]
            profile.strong_topics = ["positional encoding", "linear algebra", "data structures"]
            profile.goals = "Become an AI engineer specialising in production LLM systems. Complete the bachelor's in CS this year with focus on machine learning electives."
            print("  Updated existing student profile.")

        await db.commit()
        await db.refresh(profile)

        print()
        print("  Profile:")
        print(f"    major:         {profile.major}")
        print(f"    year_of_study: {profile.year_of_study}")
        print(f"    weak_topics:   {profile.weak_topics}")
        print(f"    strong_topics: {profile.strong_topics}")
        print(f"    goals:         {profile.goals}")


if __name__ == "__main__":
    asyncio.run(seed())