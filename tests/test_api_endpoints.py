"""
API Endpoint Tests for ChatBot Application

This module contains pytest tests for the ChatBot API endpoints.
Tests cover status, chat management, and search functionality.

Prerequisites:
- Run test_setup.py before executing these tests
"""

import os
import sys
import uuid
import pytest
from unittest.mock import patch
from asgiref.sync import async_to_sync
from sqlalchemy.sql import text


# Add the project root directory to the Python path
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
sys.path.insert(0, project_root)

from fastapi.testclient import TestClient

from main.app import app
from main.db.session import get_db
from tests.test_env import get_test_schema_name, TestingSessionLocal

try:
    # Verify test schema is set up
    TEST_SCHEMA = get_test_schema_name()
except (FileNotFoundError, ValueError) as e:
    pytest.exit(f"Test setup error: {e}")

# Create a synchronous wrapper for the async database generator
async def _get_test_db():
    async with TestingSessionLocal() as session:
        # Explicitly set the search path to use the test schema
        await session.execute(text(f"SET search_path TO {TEST_SCHEMA}"))
        try:
            yield session
            # Ensure changes are committed (optional)
            await session.commit()
        except Exception:
            # Rollback any errors
            await session.rollback()
            raise
        finally:
            # Make sure the connection is properly closed
            await session.close()

# Create a sync version that FastAPI's TestClient can use
def get_sync_db():
    # Create an async generator
    async_gen = _get_test_db()
    try:
        # Get the first value from the async generator
        db = async_to_sync(lambda: anext(async_gen))()
        # Make sure we always close the session
        yield db
    finally:
        # Ensure we close the generator
        async_to_sync(lambda: async_gen.aclose())()

# Override the database dependency
app.dependency_overrides[get_db] = get_sync_db

# Create test client
client = TestClient(app)

# Test the status endpoint
def test_status_endpoint():
    response = client.get("/api/v1/status")
    assert response.status_code == 200
    data = response.json()
    assert data["success"] is True
    assert data["status"] == "ok"
    assert "version" in data

# Test creating a chat through search
def test_search_create_chat():
    # Mock YouAPI for search operations to avoid external calls
    with patch("main.services.you_api.YouApiService.get_response") as mock_api:
        # Configure the mock to return a predefined response
        mock_api.return_value = {
            "answer": "This is a mock response from the API",
            "search_results": []
        }
        
        # Use test database with the correct schema
        response = client.post(
            "/api/v1/search",
            json={
                "user_id": "test_user",
                "chat_title": "Test Chat",
                "question": "What is the capital of France?"
            }
        )
        
        # Debug information if there's an error
        if response.status_code != 200:
            print(f"Error status code: {response.status_code}")
            print(f"Response content: {response.content.decode()}")
        
        assert response.status_code == 200
        data = response.json()
        assert data["role"] == "assistant"
        assert data["content"] == "This is a mock response from the API"

# Test retrieving chats for a user
def test_get_user_chats():
    # Mock YouAPI for search operations
    with patch("main.services.you_api.YouApiService.get_response") as mock_api:
        mock_api.return_value = {
            "answer": "This is a mock response from the API",
            "search_results": []
        }
        
        # First create a chat in the test schema
        client.post(
            "/api/v1/search",
            json={
                "user_id": "test_user2",
                "chat_title": "User Chats Test",
                "question": "Hello chatbot"
            }
        )
        
        # Now get the chats for this user
        response = client.get("/api/v1/chats/test_user2")
        
        # Debug
        if response.status_code != 200:
            print(f"Error status code: {response.status_code}")
            print(f"Response content: {response.content.decode()}")
        
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        assert len(data) >= 1
        assert data[0]["user_id"] == "test_user2"
        assert data[0]["chat_title"] == "User Chats Test"

# Test getting a specific chat
def test_get_specific_chat():
    # Mock YouAPI for search operations
    with patch("main.services.you_api.YouApiService.get_response") as mock_api:
        mock_api.return_value = {
            "answer": "This is a mock response from the API",
            "search_results": []
        }
        
        # First create a chat in the test schema
        client.post(
            "/api/v1/search",
            json={
                "user_id": "test_user3",
                "chat_title": "Specific Chat Test",
                "question": "Hello chatbot"
            }
        )
        
        # Now get the specific chat
        response = client.get("/api/v1/chats/test_user3/title/Specific Chat Test")
        
        # Debug
        if response.status_code != 200:
            print(f"Error status code: {response.status_code}")
            print(f"Response content: {response.content.decode()}")
            
        assert response.status_code == 200
        data = response.json()
        assert data["user_id"] == "test_user3"
        assert data["chat_title"] == "Specific Chat Test"
        assert "messages" in data
        assert len(data["messages"]) == 2  # User question and assistant response

# Test updating a chat title
def test_update_chat_title():
    # Mock YouAPI for search operations
    with patch("main.services.you_api.YouApiService.get_response") as mock_api:
        mock_api.return_value = {
            "answer": "This is a mock response from the API",
            "search_results": []
        }
        
        # First create a chat in the test schema
        client.post(
            "/api/v1/search",
            json={
                "user_id": "test_user4",
                "chat_title": "Old Title",
                "question": "Hello chatbot"
            }
        )
        
        # Update the chat title
        response = client.patch(
            "/api/v1/chats/test_user4/title/Old Title",
            json={"chat_title": "New Title"}
        )
        
        # Debug
        if response.status_code != 200:
            print(f"Error status code: {response.status_code}")
            print(f"Response content: {response.content.decode()}")
        
        assert response.status_code == 200
        data = response.json()
        assert data["chat_title"] == "New Title"
        
        # Verify old title doesn't exist
        response = client.get("/api/v1/chats/test_user4/title/Old Title")
        assert response.status_code == 404
        
        # Verify new title exists
        response = client.get("/api/v1/chats/test_user4/title/New Title")
        assert response.status_code == 200

# Test deleting a chat
def test_delete_chat():
    # Mock YouAPI for search operations
    with patch("main.services.you_api.YouApiService.get_response") as mock_api:
        mock_api.return_value = {
            "answer": "This is a mock response from the API",
            "search_results": []
        }
        
        # First create a chat in the test schema
        client.post(
            "/api/v1/search",
            json={
                "user_id": "test_user5",
                "chat_title": "Delete Test",
                "question": "Hello chatbot"
            }
        )
        
        # Verify it exists
        response = client.get("/api/v1/chats/test_user5/title/Delete Test")
        assert response.status_code == 200
        
        # Delete the chat
        response = client.delete("/api/v1/chats/test_user5/title/Delete Test")
        
        # Debug
        if response.status_code != 204:
            print(f"Error status code: {response.status_code}")
            print(f"Response content: {response.content.decode()}")
            
        assert response.status_code == 204
        
        # Verify it's gone
        response = client.get("/api/v1/chats/test_user5/title/Delete Test")
        assert response.status_code == 404

# Test chat history preservation
def test_chat_history_preserved():
    # Mock YouAPI for all operations
    with patch("main.services.you_api.YouApiService.get_response") as mock_api:
        mock_api.return_value = {
            "answer": "This is a mock response from the API",
            "search_results": []
        }
        
        # Create a chat and ask first question in test schema
        response1 = client.post(
            "/api/v1/search",
            json={
                "user_id": "test_user6",
                "chat_title": "History Test",
                "question": "What is the capital of France?"
            }
        )
        assert response1.status_code == 200
        
        # Ask a follow-up question
        response2 = client.post(
            "/api/v1/search",
            json={
                "user_id": "test_user6",
                "chat_title": "History Test",
                "question": "What about Germany?"
            }
        )
        assert response2.status_code == 200
        
        # Get the chat and verify it has 4 messages (2 questions, 2 answers)
        response = client.get("/api/v1/chats/test_user6/title/History Test")
        
        # Debug
        if response.status_code != 200:
            print(f"Error status code: {response.status_code}")
            print(f"Response content: {response.content.decode()}")
            
        assert response.status_code == 200
        data = response.json()
        assert len(data["messages"]) == 4
        
        # Verify the message order: first question, first answer, second question, second answer
        messages = data["messages"]
        assert messages[0]["role"] == "user"
        assert messages[0]["content"] == "What is the capital of France?"
        assert messages[1]["role"] == "assistant"
        assert messages[2]["role"] == "user"
        assert messages[2]["content"] == "What about Germany?"
        assert messages[3]["role"] == "assistant"

# Test error handling for non-existent chat
def test_nonexistent_chat():
    random_title = str(uuid.uuid4())
    response = client.get(f"/api/v1/chats/nonexistent_user/title/{random_title}")
    assert response.status_code == 404

# Test error handling for invalid search request
def test_invalid_search_request():
    response = client.post(
        "/api/v1/search",
        json={
            # Missing required fields
            "user_id": "test_user"
        }
    )
    assert response.status_code == 422  # Unprocessable Entity

# Add a cleanup fixture to ensure all database connections are properly closed
@pytest.fixture(scope="module", autouse=True)
def cleanup_connections():
    # Setup - before all tests
    yield
    # Teardown - after all tests
    # Reset the dependency override to avoid affecting other tests
    app.dependency_overrides.clear()

if __name__ == "__main__":
    print(f"Running tests against schema: {TEST_SCHEMA}")
    pytest.main(["-xvs", __file__])