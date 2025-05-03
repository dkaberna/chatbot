from typing import Any, Dict, Generic, TypeVar, Optional
from pydantic import BaseModel

T = TypeVar('T')


# More info: https://docs.pydantic.dev/latest/concepts/models/#generic-models
class Response(BaseModel, Generic[T]):
    success: bool = True
    data: Optional[T] = None
    message: Optional[str] = None
    errors: Optional[list] = None

    def model_dump(self, *args, **kwargs) -> Dict[str, Any]:  # type: ignore
        """Exclude `null` values from the response."""
        kwargs.pop("exclude_none", None)
        return super().model_dump(*args, exclude_none=True, **kwargs)
