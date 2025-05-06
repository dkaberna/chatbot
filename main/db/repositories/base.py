"""
Base repository for database operations.

This module provides a generic base repository class that implements
common CRUD operations for SQLAlchemy models, with support for
transaction-aware operations.
"""

from typing import Any, Dict, Generic, List, Optional, Type, TypeVar, Union
import uuid

from fastapi import status
from fastapi.encoders import jsonable_encoder
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy import update, delete

from main.db.base_class import Base
from main.core.exceptions import BaseInternalException
from main.core.logger import logger

ModelType = TypeVar("ModelType", bound=Base)
CreateSchemaType = TypeVar("CreateSchemaType", bound=BaseModel)
UpdateSchemaType = TypeVar("UpdateSchemaType", bound=BaseModel)


class BaseRepository(Generic[ModelType, CreateSchemaType, UpdateSchemaType]):
    """
    Base repository class with basic CRUD operations.
    
    Generic parameters:
        ModelType: SQLAlchemy model type
        CreateSchemaType: Pydantic model for create operations
        UpdateSchemaType: Pydantic model for update operations
    """
    
    def __init__(self, model: Type[ModelType], db: AsyncSession):
        self.model = model
        self.db = db

    async def get(self, id: uuid.UUID) -> Optional[ModelType]:
        try:
            query = select(self.model).where(self.model.id == id)
            result = await self.db.execute(query)
            return result.scalars().first()
        except Exception as e:
            raise BaseInternalException(
                message=f"Error retrieving {self.model.__name__} with ID {id}: {str(e)}",
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

    async def get_by_field(self, field_name: str, value: Any) -> Optional[ModelType]:
        try:
            query = select(self.model).where(getattr(self.model, field_name) == value)
            result = await self.db.execute(query)
            return result.scalars().first()
        except Exception as e:
            raise BaseInternalException(
                message=f"Error retrieving {self.model.__name__} by field {field_name}: {str(e)}",
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

    async def get_multi(self, *, skip: int = 0, limit: int = 100) -> List[ModelType]:
        try:
            query = select(self.model).offset(skip).limit(limit)
            result = await self.db.execute(query)
            return result.scalars().all()
        except Exception as e:
            raise BaseInternalException(
                message=f"Error retrieving multiple {self.model.__name__} records: {str(e)}",
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

    async def create(self, *, obj_in: CreateSchemaType, session: Optional[AsyncSession] = None) -> ModelType:
        """
        Create a new record with transaction safety. 
        Commits and refreshes only if not already inside a transaction.
        """

        # Allows the method to work both in standalone mode and as part of a larger transaction
        session = session or self.db

        try:
            # Convert the Pydantic model to a dictionary using FastAPI's jsonable_encoder
            # This transforms the Pydantic model into a format that can be used to initialize a SQLAlchemy model
            obj_in_data = jsonable_encoder(obj_in)
            
            # Create a new instance of the SQLAlchemy model (self.model)
            # Pass all fields from the converted dictionary as keyword arguments
            db_obj = self.model(**obj_in_data)
            
            # Add the new object to the SQLAlchemy session
            # This stages the object for insertion but does not yet send the SQL to the database
            session.add(db_obj)
            
            # Check if the session is already part of an ongoing transaction
            # Crucial for supporting both standalone operations and transaction block
            if not session.in_transaction():
                # Finalizes the INSERT operation and makes it permanent
                await session.commit()
                # Reload the object from the database to populate auto-generated fields
                await session.refresh(db_obj)
            else:
                # session.flush() sends the INSERT to the DB without committing the transaction.
                await session.flush()
                # session.refresh() re-fetches the auto-generated fields (id, created_at) from the DB row into the Python object.
                await session.refresh(db_obj)

            logger.info(f"Created new {self.model.__name__}: {db_obj}")
            return db_obj
        
        except Exception as e:
            await session.rollback()
            raise BaseInternalException(
                message=f"Error creating {self.model.__name__}: {str(e)}",
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

    async def update(self, *, db_obj: ModelType, obj_in: Union[UpdateSchemaType, Dict[str, Any]], session: Optional[AsyncSession] = None) -> ModelType:
        """
        Only updates fields that were explicitly provided in the input.
        Handles both complete and partial updates. 
        Works with both dictionary and schema inputs.
        Can operate both standalone and within transactions.
        """
        # Allows the method to work both in standalone mode and as part of a larger transaction
        session = session or self.db
        
        try:
            # Convert the Pydantic model to a dictionary using FastAPI's jsonable_encoder
            # This transforms the Pydantic model into a format that can be used to initialize a SQLAlchemy model
            obj_data = jsonable_encoder(db_obj)

            # If obj_in is already a dictionary, use it directly
            # Otherwise, convert the Pydantic model to a dictionary using model_dump()
            # exclude_unset=True only includes fields that were explicitly set in the input model,
            # and allows for partial updates where only some fields are changed
            update_data = obj_in if isinstance(obj_in, dict) else obj_in.model_dump(exclude_unset=True)

            # Iterate through each field in the original object
            for field in obj_data:
                # Check if this field is one of the fields being updated
                if field in update_data:
                    # If the field should be updated, set the new value on the database object
                    setattr(db_obj, field, update_data[field])
            
            # Add the modified object back to the session
            # This marks it for update in the database but doesn't execute the SQL yet
            session.add(db_obj)

            # Check if the session is already part of an ongoing transaction
            # Crucial for supporting both standalone operations and transaction block
            if not session.in_transaction():
                # Finalizes the INSERT operation and makes it permanent
                await session.commit()
                # Reload the object from the database to populate auto-generated fields
                await session.refresh(db_obj)
            else:
                # session.flush() sends the INSERT to the DB without committing the transaction.
                await session.flush()
                # session.refresh() re-fetches the auto-generated fields (id, created_at) from the DB row into the Python object.
                await session.refresh(db_obj)

            logger.info(f"Updated {self.model.__name__} ID {db_obj.id}")
            return db_obj
        
        except Exception as e:
            await session.rollback()
            raise BaseInternalException(
                message=f"Error updating {self.model.__name__} with ID {db_obj.id}: {str(e)}",
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

    async def delete(self, *, id: uuid.UUID, session: Optional[AsyncSession] = None) -> bool:
        
        # Allows the method to work both in standalone mode and as part of a larger transaction
        session = session or self.db
        
        try:
            # Create a SQL DELETE query for the repository's model type
            query = delete(self.model).where(self.model.id == id)
            # Execute the DELETE query asynchronously using the provided session
            result = await session.execute(query)

            # Check if the session is already part of a transaction
            if not session.in_transaction():
                # Commit changes to make them permanent
                await session.commit()
            else:
                # If already in a transaction, just flush changes to the database without committing
                await session.flush()

            deleted = result.rowcount > 0
            logger.info(f"Deleted {self.model.__name__} ID {id}: {deleted}")
            return deleted
        except Exception as e:
            await session.rollback()
            raise BaseInternalException(
                message=f"Error deleting {self.model.__name__} with ID {id}: {str(e)}",
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
