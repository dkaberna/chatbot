from typing import Any, Dict, Generic, TypeVar, Optional
from pydantic import BaseModel

# Define a generic type variable for flexible response typing
T = TypeVar('T')


# Generic response model that can be used with any data type
# More info: https://docs.pydantic.dev/latest/concepts/models/#generic-models
class Response(BaseModel, Generic[T]):
    success: bool = True
    data: Optional[T] = None
    message: Optional[str] = None
    errors: Optional[list] = None

    def model_dump(self, *args, **kwargs) -> Dict[str, Any]:  # type: ignore
        """
        Convert the model to a dictionary, excluding None values.
        
        This override ensures the JSON response is clean without null values,
        reducing response size and improving readability.
        
        Returns:
            Dict[str, Any]: Dictionary representation of the model without None values.
        """
        kwargs.pop("exclude_none", None)
        return super().model_dump(*args, exclude_none=True, **kwargs)
