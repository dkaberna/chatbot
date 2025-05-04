"""
ChatService: Service layer for chat-related operations.

This service handles business logic related to chats and messages,
providing a clean interface between controllers and repositories,
including atomic deletion via transaction manager.
"""

from typing import Dict, List, Any, Optional
from sqlalchemy.ext.asyncio import AsyncSession

from main.db.repositories.chat import ChatRepository, MessageRepository
from main.schemas.chat import ChatCreate, ChatUpdate
from main.core.transaction_manager import get_transaction_manager
from main.core.logger import logger


class ChatService:
    """
    Service for handling chat operations.
    """

    def __init__(self, db: AsyncSession):
        self.db = db
        self.chat_repo = ChatRepository(db)
        self.message_repo = MessageRepository(db)
        self.transaction_manager = get_transaction_manager()

    async def get_chat_by_user_and_title(self, user_id: str, chat_title: str) -> Optional[Dict[str, Any]]:
        """
        Retrieve a single chat and its messages by user ID and chat title.

        Args:
            user_id: The user identifier
            chat_title: The chat title

        Returns:
            A dictionary containing chat metadata and associated messages,
            or None if the chat does not exist.
        """
        logger.info(f"Retrieving chat for user_id={user_id}, chat_title={chat_title}")
        chat = await self.chat_repo.get_by_user_and_title(user_id, chat_title)
        if not chat:
            return None

        messages = await self.message_repo.get_by_chat(chat.id)

        return {
            "id": chat.id,
            "user_id": chat.user_id,
            "chat_title": chat.chat_title,
            "created_at": chat.created_at,
            "updated_at": chat.updated_at,
            "messages": messages
        }

    async def get_all_chats_by_user(self, user_id: str) -> List[Dict[str, Any]]:
        """
        Retrieve all chats and their messages for a specific user.

        Args:
            user_id: The user identifier

        Returns:
            A list of dictionaries, each containing chat metadata and messages.
        """
        logger.info(f"Retrieving all chats for user_id={user_id}")
        chats = await self.chat_repo.get_all_by_user(user_id)
        result = []

        for chat in chats:
            messages = await self.message_repo.get_by_chat(chat.id)

            chat_data = {
                "id": chat.id,
                "user_id": chat.user_id,
                "chat_title": chat.chat_title,
                "created_at": chat.created_at,
                "updated_at": chat.updated_at,
                "messages": messages
            }
            result.append(chat_data)

        return result

    async def update_chat_title(
        self,
        user_id: str,
        chat_title: str,
        new_title: str
    ) -> Optional[Dict[str, Any]]:
        """
        Update the title of an existing chat within a transaction block.

        Args:
            user_id: The user identifier
            chat_title: The current title of the chat
            new_title: The new title to update the chat to

        Returns:
            A dictionary containing the updated chat and messages,
            or None if the chat was not found.
        """
        logger.info(f"Updating chat title for user_id={user_id} from '{chat_title}' to '{new_title}'")

        async def _do_update(session: AsyncSession):
            chat = await self.chat_repo.get_by_user_and_title(user_id, chat_title, session=session)
            if not chat:
                return None

            update_data = ChatUpdate(chat_title=new_title)
            updated_chat = await self.chat_repo.update(db_obj=chat, obj_in=update_data, session=session)
            messages = await self.message_repo.get_by_chat(chat.id)
            return {
                "id": updated_chat.id,
                "user_id": updated_chat.user_id,
                "chat_title": updated_chat.chat_title,
                "created_at": updated_chat.created_at,
                "updated_at": updated_chat.updated_at,
                "messages": messages
            }

        results = await self.transaction_manager.execute_in_transaction([_do_update])
        return results[0]

    async def delete_chat(self, user_id: str, chat_title: str) -> Optional[Dict[str, Any]]:
        """
        Delete a chat and its associated messages atomically using raw SQL.

        Args:
            user_id: The user identifier
            chat_title: The title of the chat to be deleted

        Returns:
            A success message dict if deletion succeeded,
            otherwise a failure message dict.
        """
        logger.info(f"Attempting to delete chat for user_id={user_id}, chat_title={chat_title}")
        chat = await self.chat_repo.get_by_user_and_title(user_id, chat_title)
        if not chat:
            return None

        async def op(session):
            logger.info(f"Calling delete_chat_with_messages for chat_id: {chat.id}")
            return await self.chat_repo.delete_chat_with_messages(chat.id, session=session)

        logger.info(f"Beginning transaction for deletion of chat: {chat_title}")
        results = await self.transaction_manager.execute_in_transaction([op])
        success = results[0]

        if success:
            return {
                "success": True,
                "message": f"Chat '{chat_title}' for user '{user_id}' has been successfully deleted"
            }
        else:
            return {
                "success": False,
                "message": f"Failed to delete chat '{chat_title}' for user '{user_id}'"
            }
