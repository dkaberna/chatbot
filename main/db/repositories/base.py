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
        Create a new record with transaction safety. Commits and refreshes only
        if not already inside a transaction.
        """
        session = session or self.db
        try:
            obj_in_data = jsonable_encoder(obj_in)
            db_obj = self.model(**obj_in_data)
            session.add(db_obj)

            if not session.in_transaction():
                await session.commit()
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
        session = session or self.db
        try:
            obj_data = jsonable_encoder(db_obj)
            update_data = obj_in if isinstance(obj_in, dict) else obj_in.model_dump(exclude_unset=True)

            for field in obj_data:
                if field in update_data:
                    setattr(db_obj, field, update_data[field])

            session.add(db_obj)

            if not session.in_transaction():
                await session.commit()
                await session.refresh(db_obj)
            else:
                await session.flush()
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
        session = session or self.db
        try:
            query = delete(self.model).where(self.model.id == id)
            result = await session.execute(query)

            if not session.in_transaction():
                await session.commit()
            else:
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
