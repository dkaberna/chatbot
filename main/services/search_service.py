"""
SearchService: Handles search business logic.

This service encapsulates all business logic related to processing search requests,
interacting with the You.com API, and managing chat history. It follows the
service layer pattern to separate business logic from API routes.

The service is responsible for:
1. Finding or creating chat sessions
2. Managing message history
3. Formatting messages for the external API
4. Processing API responses
5. Persisting messages to the database
"""

from main.db.repositories.chat import ChatRepository, MessageRepository
from main.services.you_api import YouApiService
from main.schemas.chat import ChatCreate, MessageCreate
from main.core.logger import logger
from main.core.transaction_manager import get_transaction_manager
from sqlalchemy.ext.asyncio import AsyncSession
from main.schemas.chat import MessageResponse
from main.core.exceptions import BaseInternalException
from fastapi import status

class SearchService:
    """
    Service for handling search operations and chat history.
    """

    def __init__(self, db):
        self.db = db
        self.chat_repo = ChatRepository(db)
        self.message_repo = MessageRepository(db)
        self.you_api_service = YouApiService()
        self.transaction_manager = get_transaction_manager()

    async def process_search_request(self, user_id, chat_title, question, session: AsyncSession):
        """
        Process a search request and maintain conversation history.
        
        Steps:
        1. Look up or create chat.
        2. Get prior messages for context.
        3. Call You.com API.
        4. Persist user + assistant messages in DB inside transaction.
        """
        try:
            logger.info(f"Looking up chat for user {user_id} with title {chat_title}")
            chat = await self.chat_repo.get_by_user_and_title(user_id, chat_title)
            messages = []

            if chat:
                logger.info(f"Found existing chat with ID {chat.id}")
                previous_messages = await self.message_repo.get_by_chat(chat.id)
                messages = [{"role": msg.role, "content": msg.content} for msg in previous_messages]
            else:
                logger.info("No existing chat found. Will create a new one.")

            messages.append({"role": "user", "content": question})

            logger.info("Calling You.com API with message history")
            api_response = await self.you_api_service.get_response(messages)
            bot_response = api_response.get("answer", "No response")
            logger.info("Successfully received response from You.com API")

            async def persist_messages(session):
                nonlocal chat
                logger.info("Creating new chat inside transaction" if not chat else "Using existing chat")

                if not chat:
                    new_chat = ChatCreate(user_id=user_id, chat_title=chat_title)
                    chat = await self.chat_repo.create(obj_in=new_chat, session=session)

                    # Explicitly flush to get `chat.id`
                    await session.flush()
                    logger.info(f"Flushed session after chat creation. Chat ID = {chat.id}")

                # Proceed safely using chat.id
                user_message = MessageCreate(chat_id=chat.id, role="user", content=question)
                assistant_message = MessageCreate(chat_id=chat.id, role="assistant", content=bot_response)

                await self.message_repo.create(obj_in=user_message, session=session)
                assistant_msg = await self.message_repo.create(obj_in=assistant_message, session=session)

                return assistant_msg

            logger.info("Persisting chat + messages inside transaction block")
            result = await self.transaction_manager.execute_in_transaction([persist_messages])
            return MessageResponse.model_validate(result[0])

        except Exception as e:
            logger.error(f"Error in process_search_request: {str(e)}", exc_info=True)
            #raise Exception(f"Failed to process search request: {str(e)}")
            raise BaseInternalException(
                message=f"Failed to process search request: {str(e)}",
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
