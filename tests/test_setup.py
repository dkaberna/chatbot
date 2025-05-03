"""
Test Environment Setup Script

This script initializes the test database environment.
- Creates the test database if it doesn't exist
- Creates all necessary tables in the test database
- Stores the configuration information

Run this script before executing tests to prepare the test environment.
"""

import os
import sys
import asyncio
import json

# Add the project root directory to the Python path
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
sys.path.insert(0, project_root)

from sqlalchemy.ext.asyncio import create_async_engine
from sqlalchemy.sql import text

from main.db.base import Base
from main.core.config import settings

# Configuration
TEST_DATABASE_NAME = "chatbot_test_db"
CONFIG_FILE = os.path.join(os.path.dirname(__file__), "test_config.json")

# Extract parts from the database URL
parts = settings.database_url.split('/')
base_url = '/'.join(parts[:-1])
prod_db_name = parts[-1]

# Create URLs for different databases
ADMIN_DB_URL = f"{base_url}/postgres"  # Connect to postgres DB to create/drop the test DB
TEST_DB_URL = f"{base_url}/{TEST_DATABASE_NAME}"  # Test database URL


async def setup_test_environment():
    """Set up the test environment."""
    print(f"Setting up test environment...")
    
    # First connect to admin database to create test database if needed
    admin_engine = create_async_engine(ADMIN_DB_URL, isolation_level="AUTOCOMMIT")
    
    async with admin_engine.connect() as conn:
        # Check if test database exists
        result = await conn.execute(
            text(f"SELECT 1 FROM pg_database WHERE datname = '{TEST_DATABASE_NAME}'")
        )
        db_exists = result.scalar() is not None
        
        if db_exists:
            print(f"Test database '{TEST_DATABASE_NAME}' already exists.")
        else:
            # Create the test database
            await conn.execute(text(f"CREATE DATABASE {TEST_DATABASE_NAME}"))
            print(f"Created test database '{TEST_DATABASE_NAME}'.")
    
    # Now connect to the test database to create tables
    test_engine = create_async_engine(TEST_DB_URL)
    
    async with test_engine.begin() as conn:
        # Create all tables
        await conn.run_sync(Base.metadata.create_all)
        print(f"Created all tables in database '{TEST_DATABASE_NAME}'.")
    
    # Store configuration
    with open(CONFIG_FILE, 'w') as f:
        json.dump({
            'schema_name': "public",  # Use public schema in the test database
            'database_name': TEST_DATABASE_NAME
        }, f)
    
    print(f"Test environment setup complete.")
    print(f"Test database: {TEST_DATABASE_NAME}")
    print(f"Configuration saved to: {CONFIG_FILE}")
    print(f"You can now run the tests.")


if __name__ == "__main__":
    asyncio.run(setup_test_environment())