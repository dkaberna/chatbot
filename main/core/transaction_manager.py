"""
Transaction Manager for handling atomic database operations.

This module provides a centralized way to manage database transactions,
ensuring that multiple operations can be executed atomically.
"""

from typing import List, Callable, Any, TypeVar, Generic
from sqlalchemy.ext.asyncio import AsyncSession, AsyncEngine

T = TypeVar('T')

class TransactionManager:
    """
    Manages database transactions to ensure atomic operations.
    """
    
    def __init__(self, engine: AsyncEngine):
        """Initialize with database engine."""
        self.engine = engine
    
    async def execute_in_transaction(self, operations: List[Callable]) -> List[Any]:
        """
        Execute multiple operations within a single transaction.
        
        Args:
            operations: List of async functions that take a session parameter
            
        Returns:
            List of results from each operation
        """
        results = []
        async with self.engine.begin() as conn:
            # Create a new session bound to this connection
            session = AsyncSession(bind=conn)
            
            try:
                for operation in operations:
                    result = await operation(session)
                    results.append(result)
                
                # If we get here, all operations succeeded and will be committed
                # when the context manager exits
                return results
            except Exception as e:
                # Any error will trigger an automatic rollback when the context exits
                raise e

# Singleton pattern for the transaction manager
_transaction_manager = None

def get_transaction_manager(engine: AsyncEngine = None) -> TransactionManager:
    """Get or create the global transaction manager."""
    global _transaction_manager
    if _transaction_manager is None and engine is not None:
        _transaction_manager = TransactionManager(engine)
    return _transaction_manager