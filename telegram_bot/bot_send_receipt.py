import asyncio

from aiogram.types import URLInputFile

from telegram_bot.bot import bot


async def send_receipt(photo_path: str, chat_id: str, caption: str):
    try:
        photo = URLInputFile(photo_path)
        await bot.send_photo(chat_id=chat_id, photo=photo, caption=caption)
    except:  # can be error if bot not started
        pass


def run_async_in_process(receipt_url: str, chat_id: str, caption: str):
    asyncio.run(send_receipt(receipt_url, chat_id, caption))