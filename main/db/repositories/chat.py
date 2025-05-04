"""
Repository for chat and message operations.

This module provides repositories for performing database operations
on Chat and Message models.
"""

from typing import List, Optional
import uuid 

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy.sql import text
from fastapi import status


from main.db.repositories.base import BaseRepository
from main.models.chat import Chat, Message
from main.schemas.chat import ChatCreate, ChatUpdate, MessageCreate
from main.core.exceptions import BaseInternalException


class ChatRepository(BaseRepository[Chat, ChatCreate, ChatUpdate]):
    """
    Repository for chat operations.
    
    Extends the BaseRepository with chat-specific methods.
    """
    
    def __init__(self, db: AsyncSession):
        """
        Initialize the repository with database session.
        
        Args:
            db: SQLAlchemy async session
        """
        super().__init__(Chat, db)

    async def delete_chat_with_messages(self, chat_id: uuid.UUID, session: Optional[AsyncSession] = None) -> bool:
        """
        Delete a chat and all its associated messages in a transaction.
        
        Args:
            chat_id: The UUID of the chat to delete
            session: Optional session to use instead of self.db
            
        Returns:
            True if deletion was successful, False otherwise
            
        Raises:
            BaseInternalException: If there's a database error
        """
        try:
            db_session = session or self.db
            

            # Ensure we're in a transaction before executing database operations
            if not db_session.in_transaction():
                await db_session.begin()
            
            # Delete all messages associated with this chat first
            message_query = text("DELETE FROM messages WHERE chat_id = :chat_id")
            await db_session.execute(message_query, {"chat_id": str(chat_id)})
                        
            # Then delete the chat itself
            chat_query = text("DELETE FROM chats WHERE id = :chat_id")
            await db_session.execute(chat_query, {"chat_id": str(chat_id)})
            
            # Only commit if using the default session (no external transaction)
            if session is None:
                await self.db.commit()
            
            return True
        except Exception as e:
            if session is None:
                await self.db.rollback()
            raise BaseInternalException(
                message=f"Error deleting chat with ID {chat_id} and its messages: {str(e)}",
                status_code=500
            )
        
    async def get_by_user_and_title(self, user_id: str, chat_title: str) -> Optional[Chat]:
        """
        Get a chat by user ID and chat title.
        
        Args:
            user_id: ID of the user who owns the chat
            chat_title: Title of the chat
            
        Returns:
            The chat if found, None otherwise
        """
        try:
            query = select(Chat).where(
                Chat.user_id == user_id,
                Chat.chat_title == chat_title
            )
            result = await self.db.execute(query)
            return result.scalars().first()
        except Exception as e:
            raise BaseInternalException(
                message=f"Error retrieving {self.model.__name__} with user_id {user_id} and chat title {chat_title}: {str(e)}",
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
    async def get_all_by_user(self, user_id: str) -> List[Chat]:
        """
        Get all chats for a specific user.
        
        Args:
            user_id: ID of the user
            
        Returns:
            List of chats belonging to the user
        """
        try:
            query = select(Chat).where(Chat.user_id == user_id)
            result = await self.db.execute(query)
            return result.scalars().all()
        except Exception as e:
            raise BaseInternalException(
                message=f"Error retrieving chats for user {user_id}: {str(e)}",
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

class MessageRepository(BaseRepository[Message, MessageCreate, MessageCreate]):
    """
    Repository for message operations.
    
    Extends the BaseRepository with message-specific methods.
    """
    
    def __init__(self, db: AsyncSession):
        """
        Initialize the repository with database session.
        
        Args:
            db: SQLAlchemy async session
        """
        super().__init__(Message, db)

    async def get_by_chat(self, chat_id: int) -> List[Message]:
        """
        Get all messages for a specific chat, ordered by creation time.
        
        Args:
            chat_id: ID of the chat
            
        Returns:
            List of messages in the chat
        """
        try:
            query = select(Message).where(Message.chat_id == chat_id).order_by(Message.created_at)
            result = await self.db.execute(query)
            return result.scalars().all()
        except Exception as e:
            raise BaseInternalException(
                message=f"Error retrieving messages for chat {chat_id}: {str(e)}",
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR
            )