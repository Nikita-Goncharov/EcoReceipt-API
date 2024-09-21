import os
import asyncio

from aiogram.filters import CommandStart
from aiogram import Bot, Dispatcher, F
from aiogram.types import Message, KeyboardButton, ReplyKeyboardMarkup, FSInputFile
from dotenv import load_dotenv

load_dotenv()

is_user_logged = False
TOKEN = os.getenv("BOT_TOKEN")
bot = Bot(TOKEN)
dp = Dispatcher()


async def send_receipt(receipt_path):
    photo = FSInputFile(receipt_path)
    await bot.send_photo(chat_id=983240870, photo=photo)


user_logged_in_buttons = [
    [KeyboardButton(text="Register card"), KeyboardButton(text="Logout")],
]

user_anon_buttons = [
    [KeyboardButton(text="Create profile"), KeyboardButton(text="Login")],
]


@dp.message(CommandStart())
async def command_start_handler(message: Message):
    print(message.chat.id)
    if is_user_logged:
        buttons = user_logged_in_buttons
    else:
        buttons = user_anon_buttons

    keyboard = ReplyKeyboardMarkup(keyboard=buttons, resize_keyboard=True)
    await message.answer(f"Welcome to EcoReceipt bot!\nSelect action:", reply_markup=keyboard)


@dp.message(F.text.lower() == "login")
async def login_handler(message: Message):
    global is_user_logged
    is_user_logged = True

    keyboard = ReplyKeyboardMarkup(keyboard=user_logged_in_buttons, resize_keyboard=True)
    await message.answer(f"You are logged in", reply_markup=keyboard)


@dp.message(F.text.lower() == "logout")
async def logout_handler(message: Message):
    global is_user_logged
    is_user_logged = False

    keyboard = ReplyKeyboardMarkup(keyboard=user_anon_buttons, resize_keyboard=True)
    await message.answer(f"You are logged out", reply_markup=keyboard)


@dp.message(F.text.lower() == "create profile")
async def create_profile_handler(message: Message):
    await message.answer(f"Profile created")


@dp.message(F.text.lower() == "register card")
async def register_card_handler(message: Message):
    await message.answer(f"Card registered")


async def main():
    await dp.start_polling(bot)


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        pass
