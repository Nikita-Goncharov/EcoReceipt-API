from aiohttp import ClientSession
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import StatesGroup, State
from aiogram.filters import CommandStart
from aiogram.types import Message, KeyboardButton, ReplyKeyboardMarkup
from aiogram import F, Router

from redis_db import save_user_auth_status, get_user_auth_status

router = Router()

user_logged_in_buttons = [
    [KeyboardButton(text="Register card"), KeyboardButton(text="Logout")],
]

user_anon_buttons = [
    [KeyboardButton(text="Create profile"), KeyboardButton(text="Login")],
]
keyboard_for_logged_in = ReplyKeyboardMarkup(keyboard=user_logged_in_buttons, resize_keyboard=True)
keyboard_for_anon = ReplyKeyboardMarkup(keyboard=user_anon_buttons, resize_keyboard=True)


class RegisterUserData(StatesGroup):
    first_name = State()
    last_name = State()
    email = State()
    password = State()
    telegram_chat_id = State()


class RegisterCardData(StatesGroup):
    card_uid = State()


class LoginData(StatesGroup):
    email = State()
    password = State()


@router.message(CommandStart())
async def command_start_handler(message: Message):
    user_auth_data = await get_user_auth_status(message.from_user.id)
    if user_auth_data["is_logged_in"]:
        keyboard = keyboard_for_logged_in
    else:
        keyboard = keyboard_for_anon

    await message.answer(f"Welcome to EcoReceipt bot!\nSelect action:", reply_markup=keyboard)


@router.message(F.text.lower() == "login")
async def login_handler(message: Message, state: FSMContext):
    instructions = ("Please send your login email english.\n"
                    "For example: `test@gmail.com`")

    await message.answer(instructions, parse_mode="Markdown")
    await state.set_state(LoginData.email)


@router.message(LoginData.email)
async def get_login_email(message: Message, state: FSMContext):
    await state.update_data(email=message.text)

    instructions = ("Now send your password.\n"
                    "For example: `mypass123`\n"
                    "It will be deleted after sending.")

    await message.answer(instructions, parse_mode="Markdown")
    await state.set_state(LoginData.password)


@router.message(LoginData.password)
async def get_login_password(message: Message, state: FSMContext):
    await state.update_data(password=message.text)
    await message.delete()
    data = await state.get_data()

    user_auth_data = await get_user_auth_status(message.from_user.id)
    if not user_auth_data["is_logged_in"]:
        async with ClientSession() as session:
            async with session.post(
                    "http://192.168.0.106:8000/client_api/login/",
                    json={"email": data["email"], "password": data["password"]}
            ) as response:
                if response.status == 200:
                    reply = "You were successfully logged in"
                    response_data = await response.json()
                    await save_user_auth_status(message.from_user.id, True, response_data["token"])
                    keyboard = keyboard_for_logged_in
                else:
                    reply = "Error. You were not successfully logged in. Try again."
                    keyboard = keyboard_for_anon
    else:
        reply = "Error. You were not successfully logged in. Try again."
        keyboard = keyboard_for_anon

    await message.answer(reply, reply_markup=keyboard)
    await state.clear()


@router.message(F.text.lower() == "logout")
async def logout_handler(message: Message):
    user_auth_data = await get_user_auth_status(message.from_user.id)
    if user_auth_data["is_logged_in"]:
        async with ClientSession() as session:
            async with session.post(
                    "http://192.168.0.106:8000/client_api/logout/",
                    headers={"Authorization": f'Token {user_auth_data["token"]}'},
            ) as response:
                if response.status == 200:
                    reply = "You were successfully logged out"
                    await save_user_auth_status(message.from_user.id)
                    keyboard = keyboard_for_anon
                else:
                    reply = "Error. You were not successfully logged out. Try again."
                    keyboard = keyboard_for_logged_in
    else:
        reply = "Error. You were not successfully logged out. Try again."
        keyboard = keyboard_for_anon
    await message.answer(reply, reply_markup=keyboard)


@router.message(F.text.lower() == "create profile")
async def register_user(message: Message, state: FSMContext):
    instructions = ("Please send your first name in english.\n"
                    "For example: `Bob`")

    await message.answer(instructions, parse_mode="Markdown")
    await state.set_state(RegisterUserData.first_name)


@router.message(RegisterUserData.first_name)
async def get_first_name(message: Message, state: FSMContext):
    await state.update_data(first_name=message.text)
    await state.update_data(telegram_chat_id=message.chat.id)
    instructions = ("Now send your last name in english.\n"
                    "For example: `Smith`")

    await message.answer(instructions, parse_mode="Markdown")
    await state.set_state(RegisterUserData.last_name)


@router.message(RegisterUserData.last_name)
async def get_last_name(message: Message, state: FSMContext):
    await state.update_data(last_name=message.text)

    instructions = ("Now send your email.\n"
                    "For example: `test@gmail.com`")

    await message.answer(instructions, parse_mode="Markdown")
    await state.set_state(RegisterUserData.email)


@router.message(RegisterUserData.email)
async def get_email(message: Message, state: FSMContext):
    await state.update_data(email=message.text)

    instructions = ("Now send your password.\n"
                    "For example: `mypass123`\n"
                    "It will be deleted after sending.")

    await message.answer(instructions, parse_mode="Markdown")
    await state.set_state(RegisterUserData.password)


@router.message(RegisterUserData.password)
async def get_password(message: Message, state: FSMContext):
    await state.update_data(password=message.text)
    await message.delete()
    data = await state.get_data()

    first_name, last_name = data.get("first_name", ""), data.get("last_name", "")
    json_data = {
        "telegram_chat_id": data.get("telegram_chat_id", ""),
        "username": f"{first_name}_{last_name}".lower().replace(" ", "_"),
        "first_name": first_name,
        "last_name": last_name,
        "email": data.get("email", ""),
        "password": data.get("password", "")
    }
    async with ClientSession() as session:
        async with session.post(
                "http://192.168.0.106:8000/client_api/register_user/",
                json=json_data
        ) as response:
            if response.status == 200:
                reply = "Your user was created"
            else:
                reply = "Error. Your user was not created. Try again."

    await message.answer(reply, parse_mode="Markdown")
    await state.clear()


@router.message(F.text.lower() == "register card")
async def register_card(message: Message, state: FSMContext):
    instructions = ("Now send unique card id.\n"
                    "For example: `b3a5c7ac`\n"
                    "It will be deleted after sending.")

    await message.answer(instructions, parse_mode="Markdown")
    await state.set_state(RegisterCardData.card_uid)


@router.message(RegisterCardData.card_uid)
async def register_card(message: Message, state: FSMContext):
    await state.update_data(card_uid=message.text)  # TODO add check for card_uid
    await message.delete()
    data = await state.get_data()
    user_auth_data = await get_user_auth_status(message.from_user.id)

    json_data = {
        "card_uid": data.get("card_uid", "")
    }
    async with ClientSession() as session:
        async with session.post(
                "http://192.168.0.106:8000/client_api/register_card/",
                headers={"Authorization": f'Token {user_auth_data["token"]}'},
                json=json_data
        ) as response:
            if response.status == 200:
                reply = "Your card was created"
            else:
                reply = "Error. Your card was not created. Try again."

    await message.answer(reply, parse_mode="Markdown")
    await state.clear()


@router.message()
async def no_matched_handler(message: Message):
    await message.answer(f"There is no this variant")
