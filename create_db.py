"""
One-time script to create the SAGE database and all its tables.
Run with:  python create_db.py
"""

import asyncio

from backend.database.connection import init_db


async def main():
    print("Creating SAGE database and tables...\n")
    await init_db()
    print("\nDatabase created successfully at data/sage.db")
    print("All tables are ready.")


if __name__ == "__main__":
    asyncio.run(main())