from aiogram.types import KeyboardButton, ReplyKeyboardMarkup, InlineKeyboardButton, InlineKeyboardMarkup

register_profile = KeyboardButton(text="🪪Register profile")
register_card = KeyboardButton(text="📝Register card")
register_company = KeyboardButton(text="🛒Register company")

login = KeyboardButton(text="🙍Login")
logout = KeyboardButton(text="👤Logout")

show_10_receipts = KeyboardButton(text="🧾Show last 10 receipts")
show_cards = KeyboardButton(text="💳Show registered cards")
send_increase_balance_request = KeyboardButton(text="💰Send card balance increasing request")
view_increase_balance_request = KeyboardButton(text="💰View card balance requests")

user_logged_in_buttons = [[register_card, show_10_receipts], [show_cards, send_increase_balance_request], [logout]]

admin_buttons = [[register_card, show_10_receipts], [show_cards, view_increase_balance_request], [logout]]

user_anon_buttons = [[register_profile, register_company], [login]]

keyboard_for_logged_in = ReplyKeyboardMarkup(
    keyboard=user_logged_in_buttons, resize_keyboard=True, input_field_placeholder="Use menu...."
)

keyboard_for_admin = ReplyKeyboardMarkup(
    keyboard=admin_buttons, resize_keyboard=True, input_field_placeholder="Use menu...."
)

keyboard_for_anon = ReplyKeyboardMarkup(
    keyboard=user_anon_buttons, resize_keyboard=True, input_field_placeholder="Use menu...."
)


def generate_view_requests_inline_keyboard(request_id: int, telegram_chat_id: str) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(text="Accept", callback_data=f"accept_request:{request_id}:{telegram_chat_id}"),
                InlineKeyboardButton(text="Deny", callback_data=f"deny_request:{request_id}:{telegram_chat_id}"),
            ]
        ]
    )
