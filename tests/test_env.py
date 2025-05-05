"""
Test Environment Configuration

This module provides functions for accessing the test database with the 
correct schema.
"""

import os
import sys
import json
from sqlalchemy.sql import text
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import sessionmaker

# Add the project root directory to the Python path
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
sys.path.insert(0, project_root)

# Configuration
CONFIG_FILE = os.path.join(os.path.dirname(__file__), "test_config.json")

def get_test_schema_name():
    """Get the test schema name from the configuration file."""
    if not os.path.exists(CONFIG_FILE):
        raise FileNotFoundError(f"Test configuration file not found: {CONFIG_FILE}")
    
    with open(CONFIG_FILE, 'r') as f:
        config = json.load(f)
    
    schema_name = config.get('schema_name')
    if not schema_name:
        raise ValueError("Schema name not found in configuration")
    
    return schema_name

# Database URL - Use a separate test database instead of schemas
from main.core.config import get_app_settings
settings = get_app_settings()

# Extract database name from the connection URL
# Assuming URL format is: postgresql+asyncpg://username:password@host:port/dbname
parts = settings.database_url.split('/')
base_url = '/'.join(parts[:-1])
prod_db_name = parts[-1]

# Create the test database URL
TEST_DATABASE_URL = f"{base_url}/chatbot_test_db"
print(f"Using test database URL: {TEST_DATABASE_URL}")

# Create test engine with NullPool to avoid connection leaks
from sqlalchemy.pool import NullPool
# Modify this in your test_env.py
test_engine = create_async_engine(
    TEST_DATABASE_URL,
    poolclass=NullPool,  # This is good for tests
    echo=True,
    future=True
)

# Define TestingSessionLocal with explicit connection closing behavior
TestingSessionLocal = sessionmaker(
    bind=test_engine,
    expire_on_commit=False,
    class_=AsyncSession,
    autocommit=False,
    autoflush=False
)

# Get test schema name for compatibility with existing code
TEST_SCHEMA = get_test_schema_name()

async def get_test_db():
    """Provide a test database session."""
    async with TestingSessionLocal() as session:
        try:
            # No need to set search_path since we're using a different database
            # Run a test query to verify database
            result = await session.execute(text("SELECT current_database()"))
            current_db = result.scalar()
            print(f"Current database in session: {current_db}")
            
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise
# """
# Test Environment Configuration

# This module provides functions for accessing the test database with the 
# correct schema.
# """

# import os
# import sys
# import json
# from sqlalchemy.sql import text
# from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
# from sqlalchemy.orm import sessionmaker
# from sqlalchemy.pool import NullPool

# # Add the project root directory to the Python path
# project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
# sys.path.insert(0, project_root)

# # Configuration
# CONFIG_FILE = os.path.join(os.path.dirname(__file__), "test_config.json")

# def get_test_schema_name():
#     """Get the test schema name from the configuration file."""
#     if not os.path.exists(CONFIG_FILE):
#         raise FileNotFoundError(f"Test configuration file not found: {CONFIG_FILE}")
    
#     with open(CONFIG_FILE, 'r') as f:
#         config = json.load(f)
    
#     schema_name = config.get('schema_name')
#     if not schema_name:
#         raise ValueError("Schema name not found in configuration")
    
#     return schema_name

# # Database URL - Use a separate test database instead of schemas
# from main.core.config import get_app_settings
# settings = get_app_settings()

# # Extract database name from the connection URL
# parts = settings.database_url.split('/')
# base_url = '/'.join(parts[:-1])

# # Create the test database URL
# TEST_DATABASE_URL = f"{base_url}/chatbot_test_db"
# print(f"Using test database URL: {TEST_DATABASE_URL}")

# # Create test engine with NullPool to avoid connection leaks
# test_engine = create_async_engine(
#     TEST_DATABASE_URL,
#     poolclass=NullPool,
#     echo=False,
#     future=True
# )

# # Define TestingSessionLocal with explicit connection closing behavior
# TestingSessionLocal = sessionmaker(
#     bind=test_engine,
#     expire_on_commit=False,
#     class_=AsyncSession,
#     autocommit=False,
#     autoflush=False
# )

# TEST_SCHEMA = get_test_schema_name()

# async def get_test_db():
#     """Provide a test database session."""
#     async with TestingSessionLocal() as session:
#         try:
#             await session.execute(text(f"SET search_path TO {TEST_SCHEMA}"))
#             yield session
#             await session.commit()
#         except Exception:
#             await session.rollback()
#             raise
