import asyncio

from aiogram.types import URLInputFile

from telegram_bot.bot import bot


async def send_receipt(receipt_path, chat_id):
    try:
        photo = URLInputFile(receipt_path)
        await bot.send_photo(chat_id=chat_id, photo=photo)
    except:  # can be error if bot not started
        pass

def run_async_in_process(receipt_url, chat_id):
    asyncio.run(send_receipt(receipt_url, chat_id))