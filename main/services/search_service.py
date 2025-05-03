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
    
    async def process_search_request(self, user_id, chat_title, question):
        """
        Process a search request and maintain conversation history.
        
        Steps:
        1. Find or create the chat session
        2. Retrieve conversation history
        3. Save the user's question
        4. Send formatted conversation to You.com API
        5. Save the assistant's response
        6. Return the response for the API
        
        Returns:
            MessageResponse: The saved assistant message
        """
        
        # Get or create chat
        chat = await self.chat_repo.get_by_user_and_title(user_id, chat_title)
        if not chat:
            new_chat = ChatCreate(user_id=user_id, chat_title=chat_title)
            chat = await self.chat_repo.create(obj_in=new_chat)
        
        # Get previous messages and format for API
        previous_messages = await self.message_repo.get_by_chat(chat.id)
        formatted_messages = [
            {"role": msg.role, "content": msg.content}
            for msg in previous_messages
        ]
        formatted_messages.append({"role": "user", "content": question})
        
        # Save user message
        user_message = MessageCreate(
            chat_id=chat.id,
            role="user",
            content=question
        )
        await self.message_repo.create(obj_in=user_message)
        
        # Call API and save response
        api_response = await self.you_api_service.get_response(formatted_messages)
        bot_response = api_response.get("answer", "No response")
        
        assistant_message = MessageCreate(
            chat_id=chat.id,
            role="assistant",
            content=bot_response
        )
        saved_message = await self.message_repo.create(obj_in=assistant_message)
        
        return saved_message