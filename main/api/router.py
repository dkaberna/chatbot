from fastapi import APIRouter
from main.api.routes import status, chat, search

router = APIRouter()

router.include_router(status.router, prefix="/status", tags=["status"])
router.include_router(chat.router, prefix="/chats", tags=["chats"])
router.include_router(search.router, prefix="/search", tags=["search"])