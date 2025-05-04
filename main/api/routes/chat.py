"""
API endpoints for chat operations.

This module defines the API endpoints for chat operations including:
- Getting all chats for a user
- Getting a specific chat
- Updating a chat title
- Deleting a chat
"""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List


from main.db.session import get_db
from main.schemas.chat import ChatUpdate, ChatResponse
from main.services.chat_service import ChatService

router = APIRouter()

@router.get("/{user_id}/title/{chat_title}", response_model=ChatResponse, status_code=status.HTTP_200_OK)
async def get_chat_by_title(user_id: str, chat_title: str, db: AsyncSession = Depends(get_db)):
    """
    Get all chats for a specific user and title.
    
    Args:
        user_id: ID of the user
        chat_title: chat title
        db: Database session
        
    Returns:
        List of chats belonging to the user by title
        
    Raises:
        HTTPException: If no chats found for the user
    """
    service = ChatService(db)
    chat = await service.get_chat_by_user_and_title(user_id, chat_title)
    
    if not chat:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Chat with title '{chat_title}' not found for user '{user_id}'"
        )
    
    return chat

# Route for getting all chats
@router.get("/{user_id}", response_model=List[ChatResponse], status_code=status.HTTP_200_OK)
async def get_all_chats(user_id: str, db: AsyncSession = Depends(get_db)):
    """
    Get all chats for a specific user.
    
    Args:
        user_id: ID of the user
        db: Database session
        
    Returns:
        List of chats belonging to the user
        
    Raises:
        HTTPException: If no chats found for the user
    """
    service = ChatService(db)
    chats = await service.get_all_chats_by_user(user_id)
    
    # Explicitly check if the list is empty
    if not chats:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"No chats found for user '{user_id}'"
        )
    
    return chats


# Update the DELETE route to match
@router.delete("/{user_id}/title/{chat_title}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_chat(user_id: str, chat_title: str, db: AsyncSession = Depends(get_db)):
    """
    Delete a specific chat by user_id and chat_title.
    
    Args:
        user_id: ID of the user
        chat_title: Title of the chat
        db: Database session
        
    Returns:
        Confirmation message
        
    Raises:
        HTTPException: If the chat is not found or deletion fails
    """
    service = ChatService(db)
    
    result = await service.delete_chat(user_id, chat_title)
    
    if result is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Chat with title '{chat_title}' not found for user '{user_id}'"
        )
    
    if not result["success"]:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=result["message"]
        )
    
    return result
    
# Update the PATCH route to match
@router.patch("/{user_id}/title/{chat_title}", response_model=ChatResponse)
async def update_chat_title(
    user_id: str, 
    chat_title: str, 
    update_data: ChatUpdate, 
    db: AsyncSession = Depends(get_db)
):
    """
    Update the title of a specific chat.
    
    Args:
        user_id: ID of the user
        chat_title: Current title of the chat
        update_data: New data for the chat (contains new title)
        db: Database session
        
    Returns:
        The updated chat
        
    Raises:
        HTTPException: If the chat is not found
    """
    service = ChatService(db)
    updated_chat = await service.update_chat_title(user_id, chat_title, update_data.chat_title)
    
    if not updated_chat:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Chat with title '{chat_title}' not found for user '{user_id}'"
        )
    
    return updated_chat