"""
SAGE - Database models (SQLAlchemy ORM).

Each class here is a database table. SQLAlchemy turns these Python
classes into real SQL tables when init_db() runs.

Tables: User, Session, Message, StudentProfile, Document,
        QuizAttempt, Task, ConfidenceLog.

Owner: Tanjid (Backend) - scaffolded by Abrar
"""

import uuid
from datetime import datetime, timezone

from sqlalchemy import (
    JSON,
    DateTime,
    Float,
    ForeignKey,
    Integer,
    String,
    Text,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from backend.database.connection import Base


def _uuid() -> str:
    """Generate a unique string ID for a row."""
    return str(uuid.uuid4())


def _now() -> datetime:
    """Current UTC timestamp."""
    return datetime.now(timezone.utc)


class User(Base):
    """A student using SAGE."""
    __tablename__ = "users"

    id: Mapped[str] = mapped_column(String, primary_key=True, default=_uuid)
    email: Mapped[str] = mapped_column(String, unique=True, index=True)
    password_hash: Mapped[str] = mapped_column(String)
    name: Mapped[str] = mapped_column(String)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=_now)

    # Relationships: a user has many sessions, documents, tasks, etc.
    sessions: Mapped[list["Session"]] = relationship(back_populates="user")
    documents: Mapped[list["Document"]] = relationship(back_populates="user")
    tasks: Mapped[list["Task"]] = relationship(back_populates="user")
    profile: Mapped["StudentProfile"] = relationship(back_populates="user")


class Session(Base):
    """A conversation session (a chat thread)."""
    __tablename__ = "sessions"

    id: Mapped[str] = mapped_column(String, primary_key=True, default=_uuid)
    user_id: Mapped[str] = mapped_column(ForeignKey("users.id"))
    title: Mapped[str] = mapped_column(String, default="New Conversation")
    created_at: Mapped[datetime] = mapped_column(DateTime, default=_now)

    user: Mapped["User"] = relationship(back_populates="sessions")
    messages: Mapped[list["Message"]] = relationship(back_populates="session")


class Message(Base):
    """A single message in a conversation."""
    __tablename__ = "messages"

    id: Mapped[str] = mapped_column(String, primary_key=True, default=_uuid)
    session_id: Mapped[str] = mapped_column(ForeignKey("sessions.id"))
    role: Mapped[str] = mapped_column(String)  # "user" or "assistant"
    content: Mapped[str] = mapped_column(Text)
    tools_used: Mapped[dict] = mapped_column(JSON, default=dict)  # which MCP tools fired
    created_at: Mapped[datetime] = mapped_column(DateTime, default=_now)

    session: Mapped["Session"] = relationship(back_populates="messages")


class StudentProfile(Base):
    """Long-term memory: what SAGE knows about a student."""
    __tablename__ = "student_profiles"

    id: Mapped[str] = mapped_column(String, primary_key=True, default=_uuid)
    user_id: Mapped[str] = mapped_column(ForeignKey("users.id"), unique=True)
    major: Mapped[str] = mapped_column(String, default="")
    year_of_study: Mapped[int] = mapped_column(Integer, default=1)
    weak_topics: Mapped[list] = mapped_column(JSON, default=list)
    strong_topics: Mapped[list] = mapped_column(JSON, default=list)
    goals: Mapped[list] = mapped_column(JSON, default=list)

    user: Mapped["User"] = relationship(back_populates="profile")


class Document(Base):
    """An uploaded PDF/notes file, indexed for RAG."""
    __tablename__ = "documents"

    id: Mapped[str] = mapped_column(String, primary_key=True, default=_uuid)
    user_id: Mapped[str] = mapped_column(ForeignKey("users.id"))
    filename: Mapped[str] = mapped_column(String)
    status: Mapped[str] = mapped_column(String, default="processing")  # processing | ready | failed
    collection_name: Mapped[str] = mapped_column(String, default="")  # ChromaDB collection
    uploaded_at: Mapped[datetime] = mapped_column(DateTime, default=_now)

    user: Mapped["User"] = relationship(back_populates="documents")


class Task(Base):
    """A study task or deadline."""
    __tablename__ = "tasks"

    id: Mapped[str] = mapped_column(String, primary_key=True, default=_uuid)
    user_id: Mapped[str] = mapped_column(ForeignKey("users.id"))
    title: Mapped[str] = mapped_column(String)
    subject: Mapped[str] = mapped_column(String, default="")
    priority: Mapped[str] = mapped_column(String, default="medium")  # low | medium | high
    status: Mapped[str] = mapped_column(String, default="pending")  # pending | in_progress | done
    due_date: Mapped[datetime] = mapped_column(DateTime, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=_now)

    user: Mapped["User"] = relationship(back_populates="tasks")


class QuizAttempt(Base):
    """A record of a quiz the student took."""
    __tablename__ = "quiz_attempts"

    id: Mapped[str] = mapped_column(String, primary_key=True, default=_uuid)
    user_id: Mapped[str] = mapped_column(ForeignKey("users.id"))
    topic: Mapped[str] = mapped_column(String)
    questions: Mapped[list] = mapped_column(JSON, default=list)
    answers: Mapped[list] = mapped_column(JSON, default=list)
    score: Mapped[float] = mapped_column(Float, default=0.0)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=_now)


class ConfidenceLog(Base):
    """Tracks how confident a student feels about a topic over time."""
    __tablename__ = "confidence_logs"

    id: Mapped[str] = mapped_column(String, primary_key=True, default=_uuid)
    user_id: Mapped[str] = mapped_column(ForeignKey("users.id"))
    topic: Mapped[str] = mapped_column(String)
    score: Mapped[float] = mapped_column(Float)  # e.g. 0.0 to 1.0
    created_at: Mapped[datetime] = mapped_column(DateTime, default=_now)