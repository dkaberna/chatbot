# AI Chatbot application with Python, FastAPI & Docker
====================

[![FastAPI](https://img.shields.io/badge/FastAPI-005571?style=for-the-badge&logo=fastapi)](https://github.com/tiangolo/fastapi)

## Overview

This is an AI-powered chatbot application built as a RESTful web service with Python and FastAPI. The system enables users to interact with an AI assistant, and is aware of previous questions within the same chat. The chatbot integrates with the You.com API to provide intelligent, context-aware responses.

### Key Features

- Contextual question answering within conversations
- Persistent chat history storage and retrieval
- Full CRUD operations for chat management
- Clean separation of concerns with service-oriented architecture

### Technical Stack

- **FastAPI** – High-performance web framework for building APIs
- **Pydantic** – Data validation and settings management using Python type annotations
- **SQLAlchemy** – SQL toolkit and ORM (async variant used)
- **PostgreSQL** – Robust relational database for persistence
- **Docker** – Containerization for consistent deployment
- **You.com API** – LLM service for AI-powered responses

### Database Design
    CHATS {
        UUID id PK
        String user_id INDEX
        String chat_title
        DateTime created_at
        DateTime updated_at
    }
    
    MESSAGES {
        UUID id PK
        UUID chat_id FK
        String role
        Text content
        DateTime created_at
    }
    

- UUIDv7 is being used as the specific UUID data type rather than UUIDv4 in order to:
  - Improve B-tree index efficiency (less page fragmentation) and decrease maintenance overhead
  - Maintain ability to generate unique IDs across multiple application instances or microservices without coordination

- Composite indexes were created on:
  - CHATS - user_id, chat_title
  - MESSAGES - chat_id, created_at

## Running Locally with Docker

### Prerequisites

- Docker and Docker Compose installed
- A `.env` file in the project root with required environment variables

### Setup & Execution

```bash
git clone https://github.com/dkaberna/chatbot.git
cd chatbot_app
```

Run in Docker
-------------

If you want to run app in `Docker`, confirm that `DATABASE_URL` in `.env` is as follows:
```
DATABASE_URL=postgresql+asyncpg://postgres:postgres@db:5432/chatbot
```

Run project in Docker:
```bash
make docker_build
```
Stop project in Docker:
```bash
make docker_down
```

## Testing the API with cURL
Checking API health/status
```bash
curl http://localhost:5000/api/v1/status
```
Expected result:

```
{"success":true,"status":"ok","message":"ChatBot Application","version":"1.0.0"}
```

Testing POST /search endpoint (Create new chat)
```bash
curl -X POST http://localhost:5000/api/v1/search   -H "Content-Type: application/json"   -d '{
    "user_id": "test123",
    "chat_title": "TestChat", 
    "question": "What is the tallest mountain in the world?"
  }'
```
Testing POST /search endpoint (Continue existing chat)
```bash
curl -X POST http://localhost:5000/api/v1/search   -H "Content-Type: application/json"   -d '{
    "user_id": "test123",
    "chat_title": "TestChat", 
    "question": "How tall is it?"
  }'
```

Testing POST /search endpoint (Create a separate, new chat)
```
curl -X POST http://localhost:5000/api/v1/search   -H "Content-Type: application/json"   -d '{
    "user_id": "test123",
    "chat_title": "TestChatSeparate", 
    "question": "What is the most expensive city in the world?"
  }'
```
Get a specific chat for user 'test123' and chat title 'TestChat'
```
curl -X GET http://localhost:5000/api/v1/chats/test123/title/TestChat
```

Get all chats for user 'test123'
```
curl -X GET http://localhost:5000/api/v1/chats/test123
```

Update a chat
```
curl -X PATCH http://localhost:5000/api/v1/chats/test123/title/TestChat \
  -H "Content-Type: application/json" \
  -d '{"chat_title": "TestChat99"}'
```
Now retrieve chat with the updated title
```
curl -X GET http://localhost:5000/api/v1/chats/test123/title/TestChat99
```

Delete a chat
```
curl -X DELETE http://localhost:5000/api/v1/chats/test123/title/TestChat99
```

Confirm previous deleted chat is gone
```
curl -X GET http://localhost:5000/api/v1/chats/test123/title/TestChat99
```

Get remaining chat for user 'test123'
```
curl -X GET http://localhost:5000/api/v1/chats/test123
```
Test Invalid Request
```
curl -X POST http://localhost:5000/api/v1/search \
  -H "Content-Type: application/json" \
  -d '{"user_id": "test_user"}'
```

## Additional Features Implemented
- Centralized Configuration – All settings managed through a single AppSettings class

- Repository Pattern - Adds abstraction layer allowing for future CRUD operations on additional entities, eliminating code duplication

- Clean API Design – Full CORS support, API versioning, and well-structured REST routes

- Structured Logging – Rich logs with contextual metadata

- API Key Management – Managed via environment variables for non-production usage

- Service Layer Architecture – Business logic decoupled from API routes

- Token Efficiency – Aware of LLM token limits (25000) to reduce API costs


Web routes
----------
All routes are available on ``/`` or ``/redoc`` paths with Swagger or ReDoc.


Project structure
-----------------
Files related to application are in the ``main``, ``tests`` and ``alembic`` directories.

``main`` files are shown below:
```text
.
├── api
│   ├── router.py
│   └── routes
│       ├── chat.py
│       ├── search.py
│       └── status.py
├── app.py
├── backend_pre_start.py
├── core
│   ├── config.py
│   ├── dependencies.py
│   ├── exceptions.py
│   ├── logger.py
│   ├── transaction_manager.py
│   └── settings
│       ├── app.py
│       └── base.py
├── db
│   ├── base_class.py
│   ├── base.py
│   ├── repositories
│   │   ├── base.py
│   │   └── chat.py
│   └── session.py
├── models
│   └── chat.py
├── schemas
│   ├── chat.py
│   ├── response.py
│   └── status.py
├── services
│   ├── chat_service.py
│   ├── search_service.py
│   └── you_api.py

```
Local install
-------------

Setup and activate a python3 virtualenv via your preferred method. e.g. and install production requirements:

```bash
make venv
```
Then activate it manually:
```bash
source ./venv/bin/activate
```
To remove virtualenv:
```bash
make clean
```

Local run
-------------
Run migration to create tables.  Make sure you've already installed PostgreSQL.
```bash
make migrate
```
Run pre-start script to check database:
```bash
make check_db
```
Run server with settings:
```bash
make runserver
```
