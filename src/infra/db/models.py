from __future__ import annotations

from datetime import UTC, datetime
from typing import Any
from uuid import UUID, uuid4

from pgvector.sqlalchemy import Vector  # type: ignore[import-untyped]
from sqlalchemy import Boolean, DateTime, ForeignKey, Integer, String, Text, event, text
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship


class Base(DeclarativeBase):
    pass


def _ensure_pgvector(target: Any, connection: Any, **_: Any) -> None:
    connection.execute(text("CREATE EXTENSION IF NOT EXISTS vector"))


event.listen(Base.metadata, "before_create", _ensure_pgvector)


class UserTable(Base):
    """
    SQL Table for User Profile.
    Maps to src.domain.entities.user.UserProfile
    """

    __tablename__ = "users"

    id: Mapped[UUID] = mapped_column(primary_key=True, default=uuid4)
    email: Mapped[str] = mapped_column(String, unique=True, index=True, nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(UTC), nullable=False
    )

    # Optional fields
    full_name: Mapped[str | None] = mapped_column(String, nullable=True)
    profession: Mapped[str | None] = mapped_column(String, nullable=True)
    experience_years: Mapped[int] = mapped_column(Integer, default=0, nullable=False)

    def __repr__(self) -> str:
        return f"<UserTable(id={self.id}, email={self.email})>"


class SphereTable(Base):
    """Biographical sphere container."""

    __tablename__ = "spheres"

    id: Mapped[UUID] = mapped_column(primary_key=True, default=uuid4)
    user_id: Mapped[UUID] = mapped_column(ForeignKey("users.id"), index=True)

    name: Mapped[str] = mapped_column(String, nullable=False)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    status: Mapped[str] = mapped_column(String, nullable=False, default="not_started")

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(UTC), nullable=False
    )


class RawInteractionTable(Base):
    """Immutable capture of every inbound payload."""

    __tablename__ = "raw_interactions"

    id: Mapped[UUID] = mapped_column(primary_key=True, default=uuid4)
    user_id: Mapped[UUID] = mapped_column(ForeignKey("users.id"), nullable=False)
    source_type: Mapped[str] = mapped_column(String, nullable=False)
    external_id: Mapped[str | None] = mapped_column(String, nullable=True)
    raw_content: Mapped[str | None] = mapped_column(Text, nullable=True)
    audio_path: Mapped[str | None] = mapped_column(String, nullable=True)
    meta: Mapped[dict[str, object]] = mapped_column(JSONB, default=dict, nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(UTC), nullable=False
    )

    transcript_segments: Mapped[list[TranscriptSegmentTable]] = relationship(
        "TranscriptSegmentTable",
        back_populates="interaction",
        cascade="all, delete-orphan",
    )


class TranscriptSegmentTable(Base):
    """Normalized text segments derived from raw interactions."""

    __tablename__ = "transcript_segments"

    id: Mapped[UUID] = mapped_column(primary_key=True, default=uuid4)
    interaction_id: Mapped[UUID | None] = mapped_column(
        ForeignKey("raw_interactions.id"), nullable=True
    )
    user_id: Mapped[UUID] = mapped_column(ForeignKey("users.id"), nullable=False)
    content: Mapped[str] = mapped_column(Text, nullable=False)
    role: Mapped[str] = mapped_column(String, nullable=False)
    segment_order: Mapped[int] = mapped_column(Integer, nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(UTC), nullable=False
    )

    interaction: Mapped[RawInteractionTable | None] = relationship(
        "RawInteractionTable", back_populates="transcript_segments"
    )
    embeddings: Mapped[list[EmbeddingTable]] = relationship(
        "EmbeddingTable", back_populates="segment", cascade="all, delete-orphan"
    )
    provenance_links: Mapped[list[FactProvenanceTable]] = relationship(
        "FactProvenanceTable", back_populates="segment", cascade="all, delete-orphan"
    )


class EmbeddingTable(Base):
    """pgvector embeddings tied to transcript segments."""

    __tablename__ = "embeddings"

    id: Mapped[UUID] = mapped_column(primary_key=True, default=uuid4)
    segment_id: Mapped[UUID] = mapped_column(
        ForeignKey("transcript_segments.id", ondelete="CASCADE"), nullable=False
    )
    model_name: Mapped[str] = mapped_column(String, nullable=False)
    model_version: Mapped[str | None] = mapped_column(String, nullable=True)
    vector: Mapped[list[float]] = mapped_column(Vector(1536))
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(UTC), nullable=False
    )

    segment: Mapped[TranscriptSegmentTable] = relationship(
        "TranscriptSegmentTable", back_populates="embeddings"
    )


class FactTable(Base):
    """Structured facts derived from conversations."""

    __tablename__ = "facts"

    id: Mapped[UUID] = mapped_column(primary_key=True, default=uuid4)
    user_id: Mapped[UUID] = mapped_column(ForeignKey("users.id"), nullable=False)
    category: Mapped[str | None] = mapped_column(String, nullable=True)
    content: Mapped[dict[str, object]] = mapped_column(JSONB, nullable=False)
    confidence: Mapped[float | None] = mapped_column(nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(UTC), nullable=False
    )

    provenance: Mapped[list[FactProvenanceTable]] = relationship(
        "FactProvenanceTable", back_populates="fact", cascade="all, delete-orphan"
    )


class FactProvenanceTable(Base):
    """Join table linking facts back to transcript segments."""

    __tablename__ = "fact_provenance"

    fact_id: Mapped[UUID] = mapped_column(
        ForeignKey("facts.id", ondelete="CASCADE"), primary_key=True
    )
    segment_id: Mapped[UUID] = mapped_column(
        ForeignKey("transcript_segments.id", ondelete="CASCADE"), primary_key=True
    )
    start_offset: Mapped[int | None] = mapped_column(Integer, nullable=True)
    end_offset: Mapped[int | None] = mapped_column(Integer, nullable=True)

    fact: Mapped[FactTable] = relationship("FactTable", back_populates="provenance")
    segment: Mapped[TranscriptSegmentTable] = relationship(
        "TranscriptSegmentTable", back_populates="provenance_links"
    )
