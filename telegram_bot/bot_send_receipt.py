from aiogram.types import URLInputFile

from telegram_bot.bot import bot


async def send_receipt(receipt_path, chat_id):
    photo = URLInputFile(receipt_path)
    await bot.send_photo(chat_id=chat_id, photo=photo)
