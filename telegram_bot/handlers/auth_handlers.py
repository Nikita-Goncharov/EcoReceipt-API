import os
import logging

from aiohttp import ClientSession
from aiogram.fsm.context import FSMContext
from aiogram.types import Message, ReplyKeyboardRemove
from aiogram import F, Router

from keyboards import (
    login,
    logout,
    register_profile,
    register_card,
    register_company,
    keyboard_for_anon,
    keyboard_for_logged_in,
    keyboard_for_admin,
)
from fsmcontext_types import RegisterUserData, LoginData, RegisterCardData, RegisterCompanyData
from redis_db import save_user_auth_status, get_user_auth_status

auth_router = Router()
SERVER_API_DOMAIN = os.getenv("SERVER_API_DOMAIN")


@auth_router.message(F.text == login.text)
async def login_handler(message: Message, state: FSMContext):
    instructions = "Please send your login email english.\n" "For example: `test@gmail.com`"

    await message.answer(instructions, parse_mode="Markdown", reply_markup=ReplyKeyboardRemove())
    await state.set_state(LoginData.email)


@auth_router.message(LoginData.email)
async def get_login_email(message: Message, state: FSMContext):
    await state.update_data(email=message.text)

    instructions = "Now send your password.\n" "For example: `mypass123`\n" "It will be deleted after sending."

    await message.answer(instructions, parse_mode="Markdown")
    await state.set_state(LoginData.password)


@auth_router.message(LoginData.password)
async def get_login_password(message: Message, state: FSMContext):
    await state.update_data(password=message.text)
    await message.delete()
    data = await state.get_data()

    user_auth_data = await get_user_auth_status(message.from_user.id)
    if not user_auth_data["is_logged_in"]:
        async with ClientSession() as session:
            async with session.post(
                f"{SERVER_API_DOMAIN}login/", json={"email": data["email"], "password": data["password"]}
            ) as response:
                if response.status == 200:
                    reply = "You were successfully logged in"
                    response_data = await response.json()

                    headers = {"Authorization": f"Token {response_data['token']}"}

                    async with session.get(f"{SERVER_API_DOMAIN}get_user_info/", headers=headers) as get_info_response:
                        if get_info_response.status == 200:
                            get_info_response_data = await get_info_response.json()
                            user_role = get_info_response_data["data"]["role"]
                            await save_user_auth_status(message.from_user.id, user_role, True, response_data["token"])
                            if user_role == "admin":
                                keyboard = keyboard_for_admin
                            else:
                                keyboard = keyboard_for_logged_in
                        else:
                            logging.info(f"Error. {await get_info_response.json()}")
                            reply = "Error. Could not get info about logged in user. Try again."
                            keyboard = keyboard_for_anon
                else:
                    logging.info(f"Error. {await response.json()}")
                    reply = "Error. You were not successfully logged in. Try again."
                    keyboard = keyboard_for_anon
    else:
        reply = "Error. You were not successfully logged in. Try again."
        keyboard = keyboard_for_anon

    await message.answer(reply, reply_markup=keyboard)
    await state.clear()


# TODO: if user logged in again in another way, then from bot you will not can do logout
# because token will be invalid
@auth_router.message(F.text == logout.text)
async def logout_handler(message: Message):
    user_auth_data = await get_user_auth_status(message.from_user.id)
    if user_auth_data["is_logged_in"]:
        async with ClientSession() as session:
            async with session.post(
                f"{SERVER_API_DOMAIN}logout/",
                headers={"Authorization": f'Token {user_auth_data["token"]}'},
            ) as response:
                if response.status == 200:
                    reply = "You were successfully logged out"
                    await save_user_auth_status(message.from_user.id)
                    keyboard = keyboard_for_anon
                else:
                    logging.info(f"Error. {await response.json()}")
                    reply = "Error. You were not successfully logged out. Try again."
                    keyboard = keyboard_for_logged_in
    else:
        reply = "Error. You were not successfully logged out. Try again."
        keyboard = keyboard_for_anon
    await message.answer(reply, reply_markup=keyboard)


@auth_router.message(F.text == register_profile.text)
async def register_user(message: Message, state: FSMContext):
    instructions = "Please send your first name in english.\n" "For example: `Bob`"

    await message.answer(instructions, parse_mode="Markdown", reply_markup=ReplyKeyboardRemove())
    await state.set_state(RegisterUserData.first_name)


@auth_router.message(RegisterUserData.first_name)
async def get_first_name(message: Message, state: FSMContext):
    await state.update_data(first_name=message.text)
    await state.update_data(telegram_chat_id=message.chat.id)
    instructions = "Now send your last name in english.\n" "For example: `Smith`"

    await message.answer(instructions, parse_mode="Markdown")
    await state.set_state(RegisterUserData.last_name)


@auth_router.message(RegisterUserData.last_name)
async def get_last_name(message: Message, state: FSMContext):
    await state.update_data(last_name=message.text)

    instructions = "Now send your email.\n" "For example: `test@gmail.com`"

    await message.answer(instructions, parse_mode="Markdown")
    await state.set_state(RegisterUserData.email)


@auth_router.message(RegisterUserData.email)
async def get_email(message: Message, state: FSMContext):
    await state.update_data(email=message.text)

    instructions = "Now send your password.\n" "For example: `mypass123`\n" "It will be deleted after sending."

    await message.answer(instructions, parse_mode="Markdown")
    await state.set_state(RegisterUserData.password)


@auth_router.message(RegisterUserData.password)
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
        "password": data.get("password", ""),
    }
    async with ClientSession() as session:
        async with session.post(f"{SERVER_API_DOMAIN}register_user/", json=json_data) as response:
            if response.status == 200:
                reply = "Your user was created"
            else:
                logging.info(f"Error. {await response.json()}")
                reply = "Error. Your user was not created. Try again."

    user_auth_data = await get_user_auth_status(message.from_user.id)

    if not user_auth_data["is_logged_in"]:  # TODO: really necessary??
        keyboard = keyboard_for_anon
    else:
        keyboard = keyboard_for_logged_in

    await message.answer(reply, parse_mode="Markdown", reply_markup=keyboard)
    await state.clear()


@auth_router.message(F.text == register_card.text)
async def register_card(message: Message, state: FSMContext):
    instructions = "Now send unique card id.\n" "For example: `b3a5c7ac`\n" "It will be deleted after sending."

    await message.answer(instructions, parse_mode="Markdown", reply_markup=ReplyKeyboardRemove())
    await state.set_state(RegisterCardData.card_uid)


@auth_router.message(RegisterCardData.card_uid)
async def register_card(message: Message, state: FSMContext):
    await state.update_data(card_uid=message.text)  # TODO add check for card_uid
    await message.delete()
    data = await state.get_data()
    user_auth_data = await get_user_auth_status(message.from_user.id)

    headers = {"Authorization": f'Token {user_auth_data["token"]}'}

    json_data = {"card_uid": data.get("card_uid", "")}
    async with ClientSession() as session:
        async with session.post(f"{SERVER_API_DOMAIN}register_card/", headers=headers, json=json_data) as response:
            if response.status == 200:
                reply = "Your card was created"
            else:
                logging.info(f"Error. {await response.json()}")
                reply = "Error. Your card was not created. Try again."

    user_auth_data = await get_user_auth_status(message.from_user.id)

    if not user_auth_data["is_logged_in"]:  # TODO: really necessary??
        keyboard = keyboard_for_anon
    else:
        keyboard = keyboard_for_logged_in

    await message.answer(reply, parse_mode="Markdown", reply_markup=keyboard)
    await state.clear()


@auth_router.message(F.text == register_company.text)
async def register_company(message: Message, state: FSMContext):
    instructions = "Please send name of your company in english.\n" "For example: `Computer store`"

    await message.answer(instructions, parse_mode="Markdown", reply_markup=ReplyKeyboardRemove())
    await state.set_state(RegisterCompanyData.name)


@auth_router.message(RegisterCompanyData.name)
async def get_company_name(message: Message, state: FSMContext):
    await state.update_data(name=message.text)
    instructions = "Now send hotline phone number of your company.\n" "For example: `+380000000000`"

    await message.answer(instructions, parse_mode="Markdown")
    await state.set_state(RegisterCompanyData.hotline_phone)


@auth_router.message(RegisterCompanyData.hotline_phone)
async def get_company_hotline_phone(message: Message, state: FSMContext):
    await state.update_data(hotline_phone=message.text)
    instructions = "Now send your company country in english.\n" "For example: `Ukraine`"

    await message.answer(instructions, parse_mode="Markdown")
    await state.set_state(RegisterCompanyData.country)


@auth_router.message(RegisterCompanyData.country)
async def get_company_country(message: Message, state: FSMContext):
    await state.update_data(country=message.text)
    instructions = "Now send your company city in english.\n" "For example: `Kharkiv`"

    await message.answer(instructions, parse_mode="Markdown")
    await state.set_state(RegisterCompanyData.city)


@auth_router.message(RegisterCompanyData.city)
async def get_company_city(message: Message, state: FSMContext):
    await state.update_data(city=message.text)
    instructions = "Now send your company street in english.\n" "For example: `Sumska`"

    await message.answer(instructions, parse_mode="Markdown")
    await state.set_state(RegisterCompanyData.street)


@auth_router.message(RegisterCompanyData.street)
async def get_company_street(message: Message, state: FSMContext):
    await state.update_data(street=message.text)
    instructions = "Now send your company number of building in english.\n" "For example: `52/2`"

    await message.answer(instructions, parse_mode="Markdown")
    await state.set_state(RegisterCompanyData.building)


@auth_router.message(RegisterCompanyData.building)
async def get_company_building(message: Message, state: FSMContext):
    await state.update_data(building=message.text)
    data = await state.get_data()

    json_data = {
        "name": data.get("name"),
        "hotline_phone": data.get("hotline_phone"),
        "country": data.get("country"),
        "city": data.get("city"),
        "street": data.get("street"),
        "building": data.get("building"),
    }
    async with ClientSession() as session:
        async with session.post(f"{SERVER_API_DOMAIN}register_company/", json=json_data) as response:
            if response.status == 200:
                response_json = await response.json()
                created_company_data = response_json.get("data")
                if created_company_data is not None:
                    company_name, company_token = (
                        created_company_data.get("name", ""),
                        created_company_data.get("company_token", ""),
                    )
                else:
                    company_name, company_token = "", ""
                reply = f"Your company was created\nCompany name: `{company_name}`\nCompany token: `{company_token}`"
            else:
                logging.info(f"Error. {await response.json()}")
                reply = "Error. Your company was not created. Try again."

    await message.answer(
        reply, parse_mode="Markdown", reply_markup=keyboard_for_anon
    )  # if company was created then user is not logged in
    await state.clear()
