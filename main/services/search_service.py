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
from main.schemas.chat import ChatCreate, MessageCreate, MessageResponse
from main.core.logger import logger
from main.core.transaction_manager import get_transaction_manager

class SearchService:
    """
    Service for handling search operations and chat history.
    """

    def __init__(self, db):
        """Initialize repositories and API service with database session."""
        self.db = db
        self.chat_repo = ChatRepository(db)
        self.message_repo = MessageRepository(db)
        self.you_api_service = YouApiService()
        self.transaction_manager = get_transaction_manager()
    
    async def process_search_request(self, user_id, chat_title, question):
        """
        Process a search request and maintain conversation history.
        
        This method handles:
        1. Finding or creating the chat session
        2. Retrieving conversation history
        3. Calling the You.com API
        4. Saving messages to the database
        
        The method works with an existing transaction if one is present,
        or handles its own transaction management if needed.
        """
        try:
            # Step 1: Get chat (or prepare to create one) - read operation
            logger.info(f"Looking up chat for user {user_id} with title {chat_title}")
            chat = await self.chat_repo.get_by_user_and_title(user_id, chat_title)
            
            # Step 2: Get previous messages for API context - read operation  
            messages = []
            if chat:
                logger.info(f"Found existing chat with ID {chat.id}")
                previous_messages = await self.message_repo.get_by_chat(chat.id)
                messages = [
                    {"role": msg.role, "content": msg.content}
                    for msg in previous_messages
                ]
            else:
                logger.info("No existing chat found, will create a new one")
            
            # Add current question to messages for API
            messages.append({"role": "user", "content": question})
            
            # Step 3: Make API call outside of any transaction
            logger.info("Calling You.com API with the conversation history")
            try:
                api_response = await self.you_api_service.get_response(messages)
                bot_response = api_response.get("answer", "No response")
                logger.info("Successfully received response from You.com API")
            except Exception as e:
                logger.error(f"API call failed: {str(e)}")
                raise
            
            # Step 4: Handle database operations without starting a new transaction
            logger.info("Saving messages to database")
            
            # First, create the chat if needed
            if not chat:
                logger.info("Creating new chat")
                new_chat = ChatCreate(user_id=user_id, chat_title=chat_title)
                chat = await self.chat_repo.create(obj_in=new_chat)
                # Ensure the ID is assigned by flushing if needed
                if not getattr(chat, 'id', None):
                    await self.db.flush()
                logger.info(f"Created new chat with ID {chat.id}")
            
            # Create user message
            logger.info(f"Creating user message for chat ID {chat.id}")
            user_message = MessageCreate(
                chat_id=chat.id,
                role="user",
                content=question
            )
            user_msg = await self.message_repo.create(obj_in=user_message)
            
            # Create assistant message
            logger.info(f"Creating assistant message for chat ID {chat.id}")
            assistant_message = MessageCreate(
                chat_id=chat.id,
                role="assistant",
                content=bot_response
            )
            assistant_msg = await self.message_repo.create(obj_in=assistant_message)
            logger.info("Successfully saved all messages")
            
            return assistant_msg
            
        except Exception as e:
            logger.error(f"Error in process_search_request: {str(e)}", exc_info=True)
            raise Exception(f"Failed to process search request: {str(e)}")