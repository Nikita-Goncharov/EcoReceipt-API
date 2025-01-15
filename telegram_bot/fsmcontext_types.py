from aiogram.fsm.state import StatesGroup, State


class RegisterUserData(StatesGroup):
    first_name = State()
    last_name = State()
    email = State()
    password = State()
    telegram_chat_id = State()


class RegisterCardData(StatesGroup):
    card_uid = State()


class RegisterCompanyData(StatesGroup):
    name = State()
    hotline_phone = State()
    country = State()
    city = State()
    street = State()
    building = State()


class LoginData(StatesGroup):
    email = State()
    password = State()


class SendIncreaseBalanceRequest(StatesGroup):
    amount = State()
    card_number = State()
    message = State()
