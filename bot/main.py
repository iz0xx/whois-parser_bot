import asyncio

from aiogram import Dispatcher
from bot import bot
from handlers.user_router import user_router

async def main() -> None:
    dp = Dispatcher()

    register_routers(dp)

    await dp.start_polling(bot)

def register_routers(dp: Dispatcher) -> None:
    dp.include_router(user_router)

if __name__ == '__main__':
    asyncio.run(main())