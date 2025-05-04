"""
Repository for chat and message operations.

This module provides repositories for performing database operations
on Chat and Message models, including safe transaction-aware deletion.
"""

from typing import List, Optional

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy.sql import text

from main.db.repositories.base import BaseRepository
from main.models.chat import Chat, Message
from main.schemas.chat import ChatCreate, ChatUpdate, MessageCreate
from main.core.logger import logger
from main.core.exceptions import BaseInternalException
from fastapi import status


class ChatRepository(BaseRepository[Chat, ChatCreate, ChatUpdate]):
    """
    Repository for chat operations.
    """

    def __init__(self, db: AsyncSession):
        super().__init__(Chat, db)

    async def get_by_user_and_title(self, user_id: str, chat_title: str, session: Optional[AsyncSession] = None) -> Optional[Chat]:
        """
        Get all chats for a user id and title
        """

        # If a session is explicitly passed into the method (e.g. from a transaction block), that session is used.
        # If no session is passed, it falls back to the repository’s default session
        session = session or self.db
        try:
            query = select(self.model).where(
                # self.model ensures the method works for any model type — not just Chat
                self.model.user_id == user_id,
                self.model.chat_title == chat_title
            )
            result = await session.execute(query)
            return result.scalars().first()
        except Exception as e:
            logger.error(f"Error in get_by_user_and_title {str(e)}")
            raise BaseInternalException(
                message=f"Error retrieving chat for user {user_id} and title {chat_title}: {str(e)}",
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


    async def get_all_by_user(self, user_id: str, session: Optional[AsyncSession] = None) -> List[Chat]:
        """
        Get all chats for a user id
        """
        
        # If a session is explicitly passed into the method (e.g. from a transaction block), that session is used.
        # If no session is passed, it falls back to the repository’s default session
        session = session or self.db 
        try:
            logger.info(f"Retrieving chats for user_id: {user_id}")

            #query = select(Chat).where(Chat.user_id == user_id)
            query = select(self.model).where(
                # self.model ensures the method works for any model type — not just Chat
                self.model.user_id == user_id
            )
            result = await session.execute(query)
            #result = await self.db.execute(query)
            return result.scalars().all()
        except Exception as e:
            logger.error(f"Error in get_all_by_user {str(e)}")
            raise BaseInternalException(
                message=f"Error retrieving all chats for user_id {user_id}: {str(e)}",
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

    async def delete_chat_with_messages(self, chat_id: int, session: AsyncSession) -> bool:
        """
        Deletes all messages for a chat, followed by the chat itself using raw SQL.
        This must be run inside a transaction block, and will throw an exception otherwise.
        """
        try:
            if not session.in_transaction():
                raise BaseInternalException(message=f"This operation must be called inside a transaction", status_code=status.HTTP_500_INTERNAL_SERVER_ERROR)

            logger.info(f"Deleting messages for chat_id: {chat_id}")
            message_query = text("DELETE FROM messages WHERE chat_id = :chat_id")
            await session.execute(message_query, {"chat_id": chat_id})

            logger.info(f"Deleting chat row for chat_id: {chat_id}")
            chat_query = text("DELETE FROM chats WHERE id = :chat_id")
            await session.execute(chat_query, {"chat_id": chat_id})

            logger.info(f"Deleted chat and messages for chat_id: {chat_id}")
            return True
        except Exception as e:
            logger.error(f"Error during raw SQL delete: {str(e)}")
            await session.rollback()
            raise BaseInternalException(
                message=f"Error deleting all chats for chat_id {chat_id}: {str(e)}",
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
            #return False


class MessageRepository(BaseRepository[Message, MessageCreate, MessageCreate]):
    """
    Repository for message operations.
    """

    def __init__(self, db: AsyncSession):
        super().__init__(Message, db)

    async def get_by_chat(self, chat_id: int) -> List[Message]:
        try:
            logger.info(f"Retrieving messages for chat_id: {chat_id}")
            query = select(Message).where(Message.chat_id == chat_id)
            result = await self.db.execute(query)
            return result.scalars().all()
        except Exception as e:
            logger.error(f"Error in get_by_chat {str(e)}")
            raise BaseInternalException(
                message=f"Error retrieving chat for chat_id {chat_id}: {str(e)}",
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
