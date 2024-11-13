import os
import logging

from aiohttp import ClientSession
from aiogram.fsm.context import FSMContext
from aiogram.filters import CommandStart
from aiogram.types import Message, URLInputFile
from aiogram import F, Router

from keyboards import keyboard_for_anon, keyboard_for_logged_in
from redis_db import save_user_auth_status, get_user_auth_status
from bot import bot

manage_router = Router()
SERVER_API_DOMAIN = os.getenv("SERVER_API_DOMAIN")


@manage_router.message(CommandStart())
async def command_start_handler(message: Message):
    user_auth_data = await get_user_auth_status(message.from_user.id)
    if user_auth_data["is_logged_in"]:
        keyboard = keyboard_for_logged_in
    else:
        keyboard = keyboard_for_anon

    await message.answer(f"Welcome to EcoReceipt bot!\nSelect action:", reply_markup=keyboard)


@manage_router.message(F.text.lower() == "show last 10 receipts")
async def show_receipts_handler(message: Message, state: FSMContext):
    user_auth_data = await get_user_auth_status(message.from_user.id)
    headers = {
        "Authorization": f'Token {user_auth_data["token"]}'
    }

    async with ClientSession() as session:
        async with session.get(f"{SERVER_API_DOMAIN}get_user_transactions?count=10&offset=0", headers=headers) as response:
            response_data = await response.json()
            for transaction in response_data["results"]:
                receipt_path = transaction["receipt"]["img"]
                photo = URLInputFile(receipt_path)

                card_balance = transaction["card_balance_after"]
                card_number = "**** **** **** " + transaction["card"]["_card_number"][-4:]
                await bot.send_photo(
                    chat_id=message.chat.id,
                    photo=photo,
                    caption=f"Card: {card_number}\nCard balance after this operation: {card_balance}"
                )


@manage_router.message()
async def no_matched_handler(message: Message):
    await message.answer(f"There is no this variant")
