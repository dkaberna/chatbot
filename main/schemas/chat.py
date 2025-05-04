"""
Pydantic schemas for the chatbot application.

This module defines the Pydantic models for request and response validation
in the chatbot API endpoints.
"""

from pydantic import BaseModel
from typing import List, Optional
from datetime import datetime
import uuid


class MessageBase(BaseModel):
    """
    Base schema for a message with common fields.
    
    Attributes:
        role: Role of the message sender ('user' or 'assistant')
        content: Content of the message
    """
    role: str
    content: str


class MessageCreate(MessageBase):
    """
    Schema for creating a new message.
    
    Attributes:
        chat_id: ID of the chat this message belongs to
    """
    chat_id: uuid.UUID


class MessageResponse(MessageBase):
    """
    Schema for returning a message in API responses.
    
    Attributes:
        id: Unique identifier for the message
        chat_id: ID of the chat this message belongs to
        created_at: Timestamp when the message was created
    """
    id: uuid.UUID
    chat_id: uuid.UUID
    created_at: datetime

    class Config:
        from_attributes = True


class ChatBase(BaseModel):
    """
    Base schema for a chat with common fields.
    
    Attributes:
        user_id: Identifier of the user who owns the chat
        chat_title: Title of the chat
    """
    user_id: str
    chat_title: str


class ChatCreate(ChatBase):
    """
    Schema for creating a new chat.
    """
    pass


class ChatUpdate(BaseModel):
    """
    Schema for updating an existing chat.
    
    Attributes:
        chat_title: New title for the chat
    """
    chat_title: str


class ChatResponse(ChatBase):
    """
    Schema for returning a chat in API responses.
    
    Attributes:
        id: Unique identifier for the chat
        created_at: Timestamp when the chat was created
        updated_at: Timestamp when the chat was last updated
        messages: List of messages in this chat
    """
    id: uuid.UUID
    created_at: datetime
    updated_at: datetime
    messages: List[MessageResponse] = []

    class Config:
        from_attributes = True


class SearchRequest(BaseModel):
    """
    Schema for a search/question request.
    
    Attributes:
        user_id: Identifier of the user making the request
        chat_title: Title of the chat (either existing or new)
        question: The question to ask the chatbot
    """
    user_id: str
    chat_title: str
    question: str


###################################################################################
## FastAPI and Pydantic need from_attributes = True in a schema when:
##    - You're returning data directly from SQLAlchemy models
##    - You want Pydantic to read attributes from ORM objects, not just dicts
## 
## You don’t need orm_mode on input schemas like ChatCreate
## because they’re used to deserialize request bodies, not SQLAlchemy objects.