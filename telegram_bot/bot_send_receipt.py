import asyncio
import logging

from aiogram.types import URLInputFile

from telegram_bot.bot import bot


async def send_receipt(photo_path: str, chat_id: str, caption: str):
    try:
        logging.log(logging.INFO, f"photo_path: {photo_path}, chat_id: {chat_id}, caption: {caption}")
        photo = URLInputFile(photo_path)
        logging.log(logging.INFO, photo)
        await bot.send_photo(chat_id=chat_id, photo=photo, caption=caption)
    except Exception as ex:  # can be error if bot not started
        logging.log(logging.INFO, f"Error. Caught exception while trying to send receipt photo to user: {ex}")


def run_async_in_process(receipt_url: str, chat_id: str, caption: str):
    asyncio.run(send_receipt(receipt_url, chat_id, caption))
