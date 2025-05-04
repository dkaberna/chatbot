"""
Test that ChatRepository.delete_chat_with_messages deletes both the chat and its messages.
"""

import pytest
import uuid
import asyncio
from main.db.repositories.chat import ChatRepository
from main.models.chat import Chat, Message
from main.schemas.chat import ChatCreate, MessageCreate
from tests.test_env import TestingSessionLocal, test_engine
from sqlalchemy.future import select
from sqlalchemy.sql import text

@pytest.mark.asyncio
async def test_chat_repository_delete_function():
    # 1. Set up test data
    test_user_id = f"test_repo_user_{uuid.uuid4()}"
    test_chat_title = f"Test_Repo_Chat_{uuid.uuid4()}"
    
    # Create a chat and some messages
    async with TestingSessionLocal() as session:
        # Create chat directly using the model
        chat = Chat(
            user_id=test_user_id,
            chat_title=test_chat_title
        )
        session.add(chat)
        await session.flush()  # Get the ID assigned by the database
        
        # Create messages for the chat
        message1 = Message(
            chat_id=chat.id,
            role="user",
            content="Test message 1"
        )
        message2 = Message(
            chat_id=chat.id,
            role="assistant",
            content="Test response 1"
        )
        
        session.add(message1)
        session.add(message2)
        await session.commit()
        
        # Verify chat and messages exist
        result = await session.execute(
            select(Chat).where(Chat.id == chat.id)
        )
        db_chat = result.scalars().first()
        assert db_chat is not None, "Chat was not created successfully"
        
        result = await session.execute(
            select(Message).where(Message.chat_id == chat.id)
        )
        messages = result.scalars().all()
        assert len(messages) == 2, "Messages were not created successfully"
        
        # 2. Initialize repository and delete the chat
        chat_repo = ChatRepository(session)
        success = await chat_repo.delete_chat_with_messages(chat.id)
        assert success is True, "Delete operation reported failure"
        
        # 3. Verify chat was deleted
        result = await session.execute(
            select(Chat).where(Chat.id == chat.id)
        )
        deleted_chat = result.scalars().first()
        assert deleted_chat is None, "Chat was not actually deleted"
        
        # 4. Verify messages were deleted
        result = await session.execute(
            select(Message).where(Message.chat_id == chat.id)
        )
        deleted_messages = result.scalars().all()
        assert len(deleted_messages) == 0, "Messages were not deleted"

# Run the test when the module is executed
if __name__ == "__main__":
    # Use pytest to run the test
    pytest.main(["-xvs", __file__, "-k", "test_chat_repository_delete_function"])