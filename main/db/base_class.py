"""
Defines a base class for SQLAlchemy ORM models using the declarative approach
"""

from typing import Any
from sqlalchemy.ext.declarative import as_declarative, declared_attr

# transforms the Base class into a declarative base class for SQLAlchemy ORM models.
@as_declarative()
class Base:
    """
    id: Any defines that all derived classes will have an id attribute 
    (though the actual implementation will be in subclasses).

    __name__: str provides type hinting for the class name.
    """
    id: Any
    __name__: str

    @declared_attr
    def __tablename__(cls) -> str:
        """
        Generate __tablename__ automatically.
        """
        return cls.__name__.lower()