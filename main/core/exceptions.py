from typing import List

from fastapi import FastAPI, HTTPException, status
from fastapi.exceptions import RequestValidationError
from jwt.exceptions import InvalidTokenError
from pydantic import ValidationError
from starlette.requests import Request
from starlette.responses import JSONResponse



def form_error_message(errors: List[dict]) -> List[str]:
    """
    Make valid pydantic `ValidationError` messages list.
    """
    messages = []
    for error in errors:
        field, message = error["loc"][-1], error["msg"]
        messages.append(f"`{field}` {message}")
    return messages


class BaseInternalException(Exception):
    """
    Base error class for inherit all internal errors.
    """

    def __init__(self, message: str, status_code: int) -> None:
        self.message = message
        self.status_code = status_code


class UserAlreadyExistException(BaseInternalException):
    """
    Exception raised when user try to login with invalid username.
    """


class UserNotFoundException(BaseInternalException):
    """
    Exception raised when user try to register with already exist username.
    """


class InvalidUserCredentialsException(BaseInternalException):
    """
    Exception raised when user try to login with invalid credentials.
    """


class InactiveUserAccountException(BaseInternalException):
    """
    Exception raised when user try to login to inactive account.
    """

class InvalidTokenException(BaseInternalException):
    """
    Exception raised when user try to login with invalid token.
    """


def add_internal_exception_handler(app: FastAPI) -> None:
    """
    Handle all internal exceptions.
    """

    @app.exception_handler(BaseInternalException)
    async def _exception_handler(
        _: Request, exc: BaseInternalException
    ) -> JSONResponse:
        import traceback
        traceback.print_exc()
        return JSONResponse(
            status_code=exc.status_code,
            content={
                "success": False,
                "status": exc.status_code,
                "type": type(exc).__name__,
                "message": exc.message,
            },
        )


def add_validation_exception_handler(app: FastAPI) -> None:
    """
    Handle `pydantic` validation errors exceptions.
    """

    @app.exception_handler(ValidationError)
    async def _exception_handler(_: Request, exc: ValidationError) -> JSONResponse:
        return JSONResponse(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            content={
                "success": False,
                "status": status.HTTP_422_UNPROCESSABLE_ENTITY,
                "type": "ValidationError",
                "message": "Schema validation error",
                "errors": form_error_message(errors=exc.errors()),
            },
        )


def add_request_exception_handler(app: FastAPI) -> None:
    """
    Handle request validation errors exceptions.
    """

    @app.exception_handler(RequestValidationError)
    async def _exception_handler(
        _: Request, exc: RequestValidationError
    ) -> JSONResponse:
        return JSONResponse(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            content={
                "success": False,
                "status": status.HTTP_422_UNPROCESSABLE_ENTITY,
                "type": "RequestValidationError",
                "message": "Schema validation error",
                "errors": form_error_message(errors=exc.errors()),
            },
        )


def add_http_exception_handler(app: FastAPI) -> None:
    """
    Handle http exceptions.
    """

    @app.exception_handler(HTTPException)
    async def _exception_handler(_: Request, exc: HTTPException) -> JSONResponse:
        return JSONResponse(
            status_code=exc.status_code,
            content={
                "success": False,
                "status": exc.status_code,
                "type": "HTTPException",
                "message": exc.detail,
            },
        )

def add_invalid_token_exception_handler(app: FastAPI) -> None:
    """
    Handle invalid token exceptions.
    """

    @app.exception_handler(InvalidTokenError)
    async def _exception_handler(_: Request, exc: InvalidTokenError) -> JSONResponse:
        return JSONResponse(
            status_code=exc.status_code,
            content={
                "success": False,
                "status": exc.status_code,
                "type": "InvalidTokenError",
                "message": exc.detail,
            },
        )


def add_internal_server_error_handler(app: FastAPI) -> None:
    """
    Handle server exceptions.
    """

    @app.exception_handler(Exception)
    async def _exception_handler(_: Request, exc: Exception) -> JSONResponse:
        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content={
                "success": False,
                "status": status.HTTP_500_INTERNAL_SERVER_ERROR,
                "type": "Base Exception",
                "message": "Internal Server Error!",
            },
        )


def add_exceptions_handlers(app: FastAPI) -> None:
    """
    Base exception handlers.
    """
    add_internal_exception_handler(app=app)
    add_validation_exception_handler(app=app)
    add_request_exception_handler(app=app)
    add_http_exception_handler(app=app)
    add_internal_server_error_handler(app=app)
    add_invalid_token_exception_handler(app=app)