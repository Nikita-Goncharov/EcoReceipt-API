import os
import logging

from aiohttp import ClientSession
from aiogram.fsm.context import FSMContext
from aiogram.filters import CommandStart
from aiogram.types import Message, URLInputFile, CallbackQuery
from aiogram import F, Router

from bot import bot
from fsmcontext_types import SendIncreaseBalanceRequest
from redis_db import save_user_auth_status, get_user_auth_status
from keyboards import show_10_receipts, show_cards, send_increase_balance_request, view_increase_balance_request, keyboard_for_admin, keyboard_for_anon, keyboard_for_logged_in, generate_view_requests_inline_keyboard

manage_router = Router()
SERVER_API_DOMAIN = os.getenv("SERVER_API_DOMAIN")


@manage_router.message(CommandStart())
async def command_start_handler(message: Message):
    user_auth_data = await get_user_auth_status(message.from_user.id)
    if user_auth_data["is_logged_in"]:
        if user_auth_data["role"] == "admin":
            keyboard = keyboard_for_admin
        else:
            keyboard = keyboard_for_logged_in
    else:
        keyboard = keyboard_for_anon

    await message.answer(f"Welcome to EcoReceipt bot!\nSelect action:", reply_markup=keyboard)


@manage_router.message(F.text == show_10_receipts.text)
async def show_receipts_handler(message: Message):
    user_auth_data = await get_user_auth_status(message.from_user.id)
    headers = {
        "Authorization": f'Token {user_auth_data["token"]}'
    }

    async with ClientSession() as session:
        async with session.get(f"{SERVER_API_DOMAIN}get_user_transactions?count=10&offset=0", headers=headers) as response:
            response_data = await response.json()  # TODO: process errors
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


@manage_router.message(F.text == show_cards.text)
async def show_cards_handler(message: Message):
    user_auth_data = await get_user_auth_status(message.from_user.id)
    headers = {
        "Authorization": f'Token {user_auth_data["token"]}'
    }

    async with ClientSession() as session:
        async with session.get(f"{SERVER_API_DOMAIN}get_cards/", headers=headers) as response:
            response_data = await response.json()  # TODO: process errors
            answer_text = ""
            for card in response_data["data"]:
                answer_text += (
                    "<b>------💳Card------</b>\n"
                    f"Card number: {card['_card_number']}\n"
                    f"Balance: {card['_balance']}\n"
                    
                    f"Cvv: <span class='tg-spoiler'>{card['_cvv']}</span>\n"
                    f"Card uid: <span class='tg-spoiler'>{card['_card_uid']}</span>\n"
                    "\n"
                )

            await message.answer(answer_text, parse_mode="html")


@manage_router.message(F.text == send_increase_balance_request.text)
async def send_increase_request(message: Message, state: FSMContext):
    instructions = ("Send amount with which you want to increase your balance.\n"
                    "For example: `10`")

    await message.answer(instructions, parse_mode="Markdown")
    await state.set_state(SendIncreaseBalanceRequest.amount)


@manage_router.message(SendIncreaseBalanceRequest.amount)
async def get_amount(message: Message, state: FSMContext):
    await state.update_data(amount=message.text)

    instructions = ("Now send card number for increasing.\n"
                    "For example: `1111111111111111`")

    await message.answer(instructions, parse_mode="Markdown")
    await state.set_state(SendIncreaseBalanceRequest.card_number)


@manage_router.message(SendIncreaseBalanceRequest.card_number)
async def get_message(message: Message, state: FSMContext):
    await state.update_data(card_number=message.text)

    instructions = "Now send additional message for reviewing your request."

    await message.answer(instructions, parse_mode="Markdown")
    await state.set_state(SendIncreaseBalanceRequest.message)


@manage_router.message(SendIncreaseBalanceRequest.message)
async def get_message(message: Message, state: FSMContext):
    await state.update_data(message=message.text)

    user_auth_data = await get_user_auth_status(message.from_user.id)
    headers = {
        "Authorization": f'Token {user_auth_data["token"]}'
    }
    data = await state.get_data()

    if not data["amount"].isdigit():
        await message.answer("Error. Amount is not digit")

    body = {
        "amount": int(data["amount"]),
        "card_number": data["card_number"],
        "message": data["message"]
    }

    async with ClientSession() as session:
        async with session.post(f"{SERVER_API_DOMAIN}create_increase_balance_request/", headers=headers, json=body) as response:
            if response.status == 200:
                answer_text = "Your request was successfully sent"
            else:
                answer_text = "Error. Your request was not successfully sent"
            await message.answer(answer_text)

    await state.clear()


# TODO
@manage_router.message(F.text == view_increase_balance_request.text)
async def view_increase_request(message: Message):
    user_auth_data = await get_user_auth_status(message.from_user.id)
    headers = {
        "Authorization": f'Token {user_auth_data["token"]}'
    }

    async with ClientSession() as session:
        async with session.get(f"{SERVER_API_DOMAIN}get_increase_balance_requests/", headers=headers) as response:
            if response.status == 200:
                response_data = await response.json()
                for money_request in response_data["data"]:
                    answer_text = (
                        "<b>------💰Request------</b>\n"
                        f"Requested money: {money_request['requested_money']}\n"
                        f"Card number: {money_request['card']['_card_number']}\n"
    
                        f"Status: {money_request['request_status']}\n"
                        f"Message: {money_request['attached_message']}\n"
                        "\n"
                    )

                    await message.answer(
                        answer_text,
                        parse_mode="html",
                        reply_markup=generate_view_requests_inline_keyboard(money_request["id"])
                    )
            else:
                await message.answer(
                    "Error. While fetching money requests. Try again."
                )


@manage_router.callback_query(F.data.contains("accept_request") | F.data.contains("deny_request"))
async def consider_increase_balance_request(call: CallbackQuery):
    user_auth_data = await get_user_auth_status(call.from_user.id)
    headers = {
        "Authorization": f'Token {user_auth_data["token"]}'
    }
    action, request_id = call.data.split(":")
    body = {"request_id": request_id}
    if action == "accept_request":
        body["status"] = "accepted"
    else:
        body["status"] = "denied"

    async with ClientSession() as session:
        async with session.post(f"{SERVER_API_DOMAIN}consider_increase_balance_request/", headers=headers, json=body) as response:
            await call.message.delete_reply_markup()


@manage_router.message()
async def no_matched_handler(message: Message):
    await message.answer(f"There is no this variant")
