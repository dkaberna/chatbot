from typing import Annotated
from fastapi import Depends, status
from fastapi.security import OAuth2PasswordBearer

from main.core.exceptions import (
    InactiveUserAccountException,
)
from main.core.config import get_app_settings


settings = get_app_settings()



