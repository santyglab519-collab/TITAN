from datetime import datetime, timezone
from typing import AsyncGenerator, List

from sqlalchemy import JSON, DateTime, ForeignKey, String
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column

from apps.backend.core.config import settings


# Modern SQLAlchemy 2.0 DeclarativeBase for correct type validation
class Base(DeclarativeBase):
    pass


# Async Engine and SessionMaker
engine = create_async_engine(settings.database_url, echo=False)
AsyncSessionLocal = async_sessionmaker(
    bind=engine, class_=AsyncSession, expire_on_commit=False
)


async def get_db() -> AsyncGenerator[AsyncSession, None]:
    """
    Dependency to yield an active database session.
    """
    async with AsyncSessionLocal() as session:
        yield session


class ProjectModel(Base):
    """
    SQLAlchemy Model representing a user project.
    """

    __tablename__ = "projects"

    id: Mapped[str] = mapped_column(String, primary_key=True)
    user_id: Mapped[str] = mapped_column(String, nullable=False)
    session_id: Mapped[str] = mapped_column(String, unique=True, nullable=False)
    intent: Mapped[str] = mapped_column(String, nullable=False)
    domain_classified: Mapped[str] = mapped_column(String, nullable=False)
    status: Mapped[str] = mapped_column(String, default="pending")
    created_at: Mapped[datetime] = mapped_column(
        DateTime, default=lambda: datetime.now(timezone.utc)
    )


class TaskModel(Base):
    """
    SQLAlchemy Model representing a task belonging to a project.
    """

    __tablename__ = "tasks"

    id: Mapped[str] = mapped_column(String, primary_key=True)
    project_id: Mapped[str] = mapped_column(
        String, ForeignKey("projects.id", ondelete="CASCADE"), nullable=False
    )
    agent_role: Mapped[str] = mapped_column(String, nullable=False)
    description: Mapped[str] = mapped_column(String, nullable=False)
    dependencies: Mapped[List[str]] = mapped_column(JSON, default=list)
    status: Mapped[str] = mapped_column(String, default="pending")
    output: Mapped[str] = mapped_column(String, nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime, default=lambda: datetime.now(timezone.utc)
    )
