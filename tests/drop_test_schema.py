"""
Script to safely remove the chatbot_test_schema

This script connects to your database and drops the chatbot_test_schema.
"""

import os
import sys
import asyncio
from sqlalchemy.ext.asyncio import create_async_engine
from sqlalchemy.sql import text

# Add the project root directory to the Python path
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
sys.path.insert(0, project_root)

from main.core.config import settings

async def drop_test_schema():
    """Drop the test schema from the production database."""
    print("Preparing to drop chatbot_test_schema...")
    
    # Schema name to drop
    schema_name = "chatbot_test_schema"
    
    # Create engine using the production database URL
    engine = create_async_engine(settings.database_url, echo=True)
    
    try:
        async with engine.begin() as conn:
            # Check if schema exists
            result = await conn.execute(
                text(f"SELECT schema_name FROM information_schema.schemata WHERE schema_name = '{schema_name}'")
            )
            schema_exists = result.scalar() is not None
            
            if not schema_exists:
                print(f"Schema '{schema_name}' does not exist. Nothing to do.")
                return
            
            # List tables in the schema (for confirmation)
            result = await conn.execute(
                text(f"""
                SELECT table_name 
                FROM information_schema.tables 
                WHERE table_schema = '{schema_name}'
                """)
            )
            tables = [row[0] for row in result.fetchall()]
            
            print(f"Found the following tables in '{schema_name}':")
            for table in tables:
                print(f"  - {table}")
            
            # Drop the schema with CASCADE option to drop all objects within it
            print(f"Dropping schema '{schema_name}' and all its objects...")
            await conn.execute(text(f"DROP SCHEMA {schema_name} CASCADE"))
            
            # Verify schema was dropped
            result = await conn.execute(
                text(f"SELECT schema_name FROM information_schema.schemata WHERE schema_name = '{schema_name}'")
            )
            schema_still_exists = result.scalar() is not None
            
            if schema_still_exists:
                print(f"ERROR: Schema '{schema_name}' still exists after drop attempt!")
            else:
                print(f"SUCCESS: Schema '{schema_name}' has been dropped.")
    
    except Exception as e:
        print(f"Error: {e}")
        print("Failed to drop the schema.")

if __name__ == "__main__":
    asyncio.run(drop_test_schema())