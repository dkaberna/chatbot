"""
Service for interacting with the You.com API.

This module provides a service for making requests to the You.com API
to generate chatbot responses.
"""

import httpx
import os
from typing import List, Dict, Any
from fastapi import HTTPException

from main.core.logger import logger


class YouApiService:
    """
    Service for interacting with the You.com API.
    """
    
    def __init__(self):
        """
        Initialize the service with API key and URL.
        """
        self.api_key = os.getenv("YOU_API_KEY")
        self.api_url = "https://chat-api.you.com/smart"
        logger.info("YouApiService initialized")
        
    async def get_response(self, messages: List[Dict[str, str]]) -> Dict[str, Any]:
        """
        Get a response from the You.com API.
        
        Args:
            messages: List of message objects with 'role' and 'content' fields
            
        Returns:
            API response data
            
        Raises:
            HTTPException: If the API request fails
        """
        if not self.api_key:
            logger.error("YOU_API_KEY environment variable not set")
            raise HTTPException(status_code=500, detail="YOU_API_KEY environment variable not set")
        
        # Log the conversation being sent (excluding potentially sensitive content)
        logger.debug(f"Sending request to You.com API with {len(messages)} messages")
        logger.debug(f"Last message: {messages[-1]['role']}")
        
        async with httpx.AsyncClient() as client:
            try:
                logger.debug(f"Making request to {self.api_url}")
                response = await client.post(
                    self.api_url,
                    headers={
                        "X-API-Key": self.api_key,
                        "Content-Type": "application/json"
                    },
                    json={"messages": messages},
                    timeout=30.0
                )
                
                if response.status_code != 200:
                    error_message = f"You.com API error: {response.status_code} - {response.text}"
                    logger.error(error_message)
                    raise HTTPException(
                        status_code=response.status_code, 
                        detail=error_message
                    )
                
                logger.info(f"Successfully received response from You.com API")
                logger.debug(f"Response status code: {response.status_code}")
                
                logger.debug(f"🔎 Full response from You.com: {response.json()}")
                return response.json()
            except httpx.RequestError as exc:
                error_message = f"Service unavailable: {str(exc)}"
                logger.error(error_message)
                raise HTTPException(status_code=503, detail=error_message)