from aiogram.types import KeyboardButton, ReplyKeyboardMarkup

user_logged_in_buttons = [
    [KeyboardButton(text="Register card"), KeyboardButton(text="Show last 10 receipts")],
    [KeyboardButton(text="Logout")]
]

user_anon_buttons = [
    [KeyboardButton(text="Register profile"), KeyboardButton(text="Register company")],
    [KeyboardButton(text="Login")]
]

keyboard_for_logged_in = ReplyKeyboardMarkup(
    keyboard=user_logged_in_buttons,
    resize_keyboard=True,
    input_field_placeholder="Use menu...."
)
keyboard_for_anon = ReplyKeyboardMarkup(
    keyboard=user_anon_buttons,
    resize_keyboard=True,
    input_field_placeholder="Use menu...."
)