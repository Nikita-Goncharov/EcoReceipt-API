import os
import asyncio
import logging

from aiogram.fsm.storage.memory import MemoryStorage
from aiogram import Bot, Dispatcher
from dotenv import load_dotenv


load_dotenv()

TOKEN = os.getenv("BOT_TOKEN")
DEBUG = True

bot = Bot(TOKEN)
dp = Dispatcher(storage=MemoryStorage())


async def main():
    dp.include_routers(auth_router, manage_router)
    await dp.start_polling(bot)


if __name__ == "__main__":
    from handlers.auth_handlers import auth_router
    from handlers.manage_handlers import manage_router

    if DEBUG:
        logging.basicConfig(level=logging.INFO)

    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logging.log(logging.INFO, "Telegram bot stopped")
