"""
ChatService: Service layer for chat-related operations.

This service handles business logic related to chats and messages,
providing a clean interface between controllers and repositories.
"""

from typing import Dict, List, Any, Optional
import uuid
from sqlalchemy.ext.asyncio import AsyncSession

from main.db.repositories.chat import ChatRepository, MessageRepository
from main.schemas.chat import ChatCreate, ChatUpdate


class ChatService:
    """
    Service for handling chat operations.
    """
    
    def __init__(self, db: AsyncSession):
        """Initialize with database session."""
        self.db = db
        self.chat_repo = ChatRepository(db)
        self.message_repo = MessageRepository(db)
    
    async def get_chat_by_user_and_title(self, user_id: str, chat_title: str) -> Optional[Dict[str, Any]]:
        """
        Get a chat by user ID and title with its messages.
        
        Args:
            user_id: ID of the user
            chat_title: Title of the chat
            
        Returns:
            Chat data with messages or None if not found
        """
        chat = await self.chat_repo.get_by_user_and_title(user_id, chat_title)
        if not chat:
            return None
            
        # Load messages
        messages = await self.message_repo.get_by_chat(chat.id)
        
        # Construct response
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
        Get all chats for a user with their messages.
        
        Args:
            user_id: ID of the user
            
        Returns:
            List of chat data with messages (may be empty)
        """
        chats = await self.chat_repo.get_all_by_user(user_id)
        result = []
        
        for chat in chats:
            # Load messages for each chat
            messages = await self.message_repo.get_by_chat(chat.id)
            
            # Construct response for this chat
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
    
    async def update_chat_title(self, user_id: str, chat_title: str, new_title: str) -> Optional[Dict[str, Any]]:
        """
        Update a chat's title.
        
        Args:
            user_id: ID of the user
            chat_title: Current title of the chat
            new_title: New title for the chat
            
        Returns:
            Updated chat data with messages or None if not found
        """
        chat = await self.chat_repo.get_by_user_and_title(user_id, chat_title)
        if not chat:
            return None
            
        # Update chat
        update_data = ChatUpdate(chat_title=new_title)
        updated_chat = await self.chat_repo.update(db_obj=chat, obj_in=update_data)
        
        # Load messages
        messages = await self.message_repo.get_by_chat(updated_chat.id)
        
        # Construct response
        return {
            "id": updated_chat.id,
            "user_id": updated_chat.user_id,
            "chat_title": updated_chat.chat_title,
            "created_at": updated_chat.created_at,
            "updated_at": updated_chat.updated_at,
            "messages": messages
        }
    
    async def delete_chat(self, user_id: str, chat_title: str) -> bool:
        """
        Delete a chat and its messages.
        
        Args:
            user_id: ID of the user
            chat_title: Title of the chat
            
        Returns:
            Dictionary with success status and message, or None if chat not found
        """
        chat = await self.chat_repo.get_by_user_and_title(user_id, chat_title)
        if not chat:
            return None
            
        # Delete chat with messages
        success = await self.chat_repo.delete_chat_with_messages(chat.id)
        
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