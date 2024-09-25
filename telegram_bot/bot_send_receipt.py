from aiogram.types import URLInputFile

from telegram_bot.bot import bot


# TODO: somehow check how user logged in and does \logged in really
async def send_receipt(receipt_path, chat_id):
    photo = URLInputFile(receipt_path)
    await bot.send_photo(chat_id=chat_id, photo=photo)
