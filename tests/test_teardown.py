"""
Test Environment Teardown Script

This script cleans up the test database environment.
- Drops the test database entirely
- Removes the configuration file

Run this script after testing is complete to clean up the test environment.
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

from main.core.config import settings

# Configuration
CONFIG_FILE = os.path.join(os.path.dirname(__file__), "test_config.json")

# Extract parts from the database URL
parts = settings.database_url.split('/')
base_url = '/'.join(parts[:-1])
ADMIN_DB_URL = f"{base_url}/postgres"  # Connect to postgres DB to drop the test DB

async def teardown_test_environment():
    """Clean up the test environment."""
    print(f"Cleaning up test environment...")
    
    # Check if config file exists
    if not os.path.exists(CONFIG_FILE):
        print(f"Configuration file not found: {CONFIG_FILE}")
        print(f"Nothing to clean up.")
        return
    
    # Load configuration
    with open(CONFIG_FILE, 'r') as f:
        config = json.load(f)
    
    database_name = config.get('database_name')
    if not database_name:
        print(f"Database name not found in configuration.")
        print(f"Nothing to clean up.")
        return
    
    # Connect to admin database to be able to drop the test database
    admin_engine = create_async_engine(ADMIN_DB_URL, isolation_level="AUTOCOMMIT")
    
    try:
        async with admin_engine.connect() as conn:
            # Check if database exists
            result = await conn.execute(
                text(f"SELECT 1 FROM pg_database WHERE datname = '{database_name}'")
            )
            db_exists = result.scalar() is not None
            
            if not db_exists:
                print(f"Database '{database_name}' does not exist.")
            else:
                # Force disconnect all existing connections
                await conn.execute(text(f"""
                    SELECT pg_terminate_backend(pg_stat_activity.pid)
                    FROM pg_stat_activity
                    WHERE pg_stat_activity.datname = '{database_name}'
                    AND pid <> pg_backend_pid()
                """))
                
                # Drop the database
                await conn.execute(text(f"DROP DATABASE {database_name}"))
                print(f"Dropped database '{database_name}'.")
        
        # Remove configuration file
        os.remove(CONFIG_FILE)
        print(f"Removed configuration file: {CONFIG_FILE}")
        
        print(f"Test environment cleanup complete.")
    
    except Exception as e:
        print(f"Error cleaning up test environment: {e}")
        print(f"You may need to manually drop the database: DROP DATABASE {database_name};")


if __name__ == "__main__":
    asyncio.run(teardown_test_environment())