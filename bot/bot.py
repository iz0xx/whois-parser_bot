from aiogram import Bot
from aiogram.client.default import DefaultBotProperties
from token_api import TOKEN_API


bot = Bot(
    token=TOKEN_API,
    default = DefaultBotProperties(parse_mode='HTML')
)