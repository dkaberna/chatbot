"""
Chat ORM model definition.

Chat and Message models for the chatbot application.

This module defines the database models for storing chats and messages.
Each chat belongs to a user and contains a series of messages.
"""
from uuid6 import uuid7
from sqlalchemy import Column, String, Text, ForeignKey, DateTime
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from main.db.base_class import Base


class Chat(Base):
    """
    Chat model representing a conversation between a user and the chatbot.
    
    Attributes:
        id: Unique identifier for the chat (UUID)
        user_id: Identifier of the user who owns the chat
        chat_title: Title of the chat
        created_at: Timestamp when the chat was created
        updated_at: Timestamp when the chat was last updated
        messages: Relationship to the messages in this chat
    """
    __tablename__ = "chats"

    __table_args__ = (
        Index('ix_user_chat_title', 'user_id', 'chat_title'),
    )

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid7)
    user_id = Column(String, index=True, nullable=False)
    chat_title = Column(String, nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    # Relationship with Message model
    messages = relationship("Message", back_populates="chat", cascade="all, delete-orphan")


class Message(Base):
    """
    Message model representing a single message in a chat.
    
    Attributes:
        id: Unique identifier for the message (UUID)
        chat_id: Foreign key to the chat this message belongs to
        role: Role of the sender ('user' or 'assistant')
        content: Content of the message
        created_at: Timestamp when the message was created
        chat: Relationship to the parent chat
    """
    __tablename__ = "messages"

    # Speeds up filtering by chat_id and sorting by created_at at the same time
    # No need to maintain a separate index on just chat_id
    __table_args__ = (
        Index('ix_chat_id_created_at', 'chat_id', 'created_at'),
    )

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid7)
    chat_id = Column(UUID(as_uuid=True), ForeignKey("chats.id"), nullable=False)
    role = Column(String, nullable=False)  # Either "user" or "assistant"
    content = Column(Text, nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    # Relationship with Chat model
    chat = relationship("Chat", back_populates="messages")

# For possible discussion, usage of UUID Primary Key
# Benefits of UUID Primary Keys

# Global Uniqueness: UUIDs are globally unique across systems, which makes database merging or data sharing easier.
# Security: UUIDs don't expose sequential information like auto-incrementing integers, making it harder to guess valid IDs.
# Distributed Systems: UUIDs can be generated client-side without coordination, which is valuable in distributed systems.
# No Collisions: When inserting data across multiple servers, there's no risk of primary key collisions.
