from pydantic import BaseModel


class Status(BaseModel):
    success: bool
    status: str
    message: str
    version: str

    class Config:
        from_attributes = True  # If any ORM object, though not needed here technically