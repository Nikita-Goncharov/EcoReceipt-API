import os

from aiogram.types import Message
from aiohttp import ClientSession

SERVER_API_DOMAIN = os.getenv("SERVER_API_DOMAIN")


async def send_user_analytics(message: Message):
    body = {
        "user_full_name": message.from_user.full_name,
        "username": message.from_user.username,
        "telegram_user_id": message.from_user.id,
        "telegram_chat_id": message.chat.id,
    }

    async with ClientSession() as session:
        async with session.post(
                f"{SERVER_API_DOMAIN}send_user_analytics/", json=body
        ):
            pass
