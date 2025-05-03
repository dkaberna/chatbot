"""
API endpoint for search operations.

This module defines the API endpoint for search operations 

The endpoint processes search requests by:
1. Accepting a SearchRequest with user_id, chat_title, and question
2. Delegating processing to the SearchService
3. Returning the assistant's response as a MessageResponse

"""
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from main.db.session import get_db
from main.services.search_service import SearchService
from main.schemas.chat import MessageResponse, SearchRequest

router = APIRouter()

@router.post("", response_model=MessageResponse)
async def search(request: SearchRequest, db: AsyncSession = Depends(get_db)):
    """
    Process a search request, call the You.com API, and save the conversation.
    """
    try:
        service = SearchService(db)
        saved_message = await service.process_search_request(
            request.user_id, 
            request.chat_title, 
            request.question
        )
        return saved_message
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )