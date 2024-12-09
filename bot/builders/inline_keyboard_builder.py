from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton

def create_button(text, url):
    inline_btn = [[InlineKeyboardButton(text=text, url=url)]]
    return InlineKeyboardMarkup(inline_keyboard=inline_btn)