"""
AIConversation ORM model.

Table: ai_conversations
- UUID PK
- Stores individual chat messages (each row = one turn)
- conversation_id groups messages of a single conversation session
- role ENUM (user | assistant)
- Indexes: conversation_id (schema doc requirement), user_id
"""
import uuid

from sqlalchemy import ForeignKey, Index, String, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base
from app.models.mixins import CreatedAtMixin
from app.models.enums import ConversationRole


class AIConversation(Base, CreatedAtMixin):
    __tablename__ = "ai_conversations"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, nullable=False
    )

    # Groups all turns in a single conversation session
    conversation_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), nullable=False
    )

    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
    )

    role: Mapped[ConversationRole] = mapped_column(String(10), nullable=False)
    message: Mapped[str] = mapped_column(Text, nullable=False)

    # Relationship
    user: Mapped["User"] = relationship("User", back_populates="ai_conversations")

    __table_args__ = (
        Index("ix_ai_conversations_conversation_id", "conversation_id"),  # schema doc requirement
        Index("ix_ai_conversations_user_id", "user_id"),
        Index("ix_ai_conversations_user_conversation", "user_id", "conversation_id"),
        Index("ix_ai_conversations_created_at", "created_at"),
    )

    def __repr__(self) -> str:
        return (
            f"<AIConversation id={self.id} conv_id={self.conversation_id} "
            f"role={self.role!r}>"
        )
