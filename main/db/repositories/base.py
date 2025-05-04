"""
Base repository for database operations.

This module provides a generic base repository class that implements
common CRUD operations for SQLAlchemy models.

This repositoriy is designed to:

     - Use the provided session when one is passed in
     - Manage its own transaction when no session is provided
     - Properly handle commits/rollbacks based on whether they own the transaction
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
        """
        Initialize the repository with model type and database session.
        
        Args:
            model: The SQLAlchemy model class
            db: SQLAlchemy async session
        """
        self.model = model
        self.db = db

    async def get(self, id: uuid.UUID) -> Optional[ModelType]:
        """
        Get a record by ID.
        
        Args:
            id: The UUID of the record to get
            
        Returns:
            The record if found, None otherwise
            
        Raises:
            BaseInternalException: If there's a database error
        """
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
        """
        Get a record by field value.
        
        Args:
            field_name: Name of the field to filter by
            value: Value to filter for
            
        Returns:
            The record if found, None otherwise
            
        Raises:
            BaseInternalException: If there's a database error
        """
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
        """
        Get multiple records with pagination.
        
        Args:
            skip: Number of records to skip
            limit: Maximum number of records to return
            
        Returns:
            List of records
            
        Raises:
            BaseInternalException: If there's a database error
        """
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
        Create a new record.
        
        Args:
            obj_in: Data for creating the record
            session: Optional session to use instead of self.db
            
        Returns:
            The created record
            
        Raises:
            BaseInternalException: If there's a database error
        """
        try:
            db_session = session or self.db
            obj_in_data = jsonable_encoder(obj_in)
            db_obj = self.model(**obj_in_data)
            db_session.add(db_obj)
            
            # Only commit if using the default session (no external transaction)
            if session is None:
                await self.db.commit()
                await self.db.refresh(db_obj)
            
            return db_obj
        except Exception as e:
            if session is None:
                await self.db.rollback()
            raise BaseInternalException(
                message=f"Error creating {self.model.__name__}: {str(e)}",
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

    async def update(
        self, *, db_obj: ModelType, obj_in: Union[UpdateSchemaType, Dict[str, Any]], 
        session: Optional[AsyncSession] = None
    ) -> ModelType:
        """
        Update a record.
        
        Args:
            db_obj: Database object to update
            obj_in: New data to update with
            session: Optional session to use instead of self.db
            
        Returns:
            The updated record
            
        Raises:
            BaseInternalException: If there's a database error
        """
        try:
            db_session = session or self.db
            obj_data = jsonable_encoder(db_obj)
            if isinstance(obj_in, dict):
                update_data = obj_in
            else:
                update_data = obj_in.dict(exclude_unset=True)
            for field in obj_data:
                if field in update_data:
                    setattr(db_obj, field, update_data[field])
            db_session.add(db_obj)
            
            # Only commit if using the default session (no external transaction)
            if session is None:
                await self.db.commit()
                await self.db.refresh(db_obj)
            
            return db_obj
        except Exception as e:
            if session is None:
                await self.db.rollback()
            raise BaseInternalException(
                message=f"Error updating {self.model.__name__} with ID {db_obj.id}: {str(e)}",
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

    async def delete(self, *, id: uuid.UUID, session: Optional[AsyncSession] = None) -> bool:
        """
        Delete a record by ID.
        
        Args:
            id: The UUID of the record to delete
            session: Optional session to use instead of self.db
            
        Returns:
            True if the record was deleted, False otherwise
            
        Raises:
            BaseInternalException: If there's a database error
        """
        try:
            db_session = session or self.db
            query = delete(self.model).where(self.model.id == id)
            result = await db_session.execute(query)
            
            # Only commit if using the default session (no external transaction)
            if session is None:
                await self.db.commit()
            
            return result.rowcount > 0
        except Exception as e:
            if session is None:
                await self.db.rollback()
            raise BaseInternalException(
                message=f"Error deleting {self.model.__name__} with ID {id}: {str(e)}",
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR
            )