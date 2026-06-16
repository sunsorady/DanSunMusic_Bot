import asyncio
import logging
import os

import httpx
from aiohttp import web
from aiogram import Bot, Dispatcher
from aiogram.client.default import DefaultBotProperties
from aiogram.client.session.aiohttp import AiohttpSession
from aiogram.client.telegram import TelegramAPIServer
from aiogram.enums.parse_mode import ParseMode
from aiocron import crontab

from config import BOT_TOKEN, BOT_COMMANDS, OUTPUT_DIR, custom_api_url, MEASUREMENT_ID, API_SECRET, PORT
from services.db import DataBase

logging.basicConfig(level=logging.INFO)

custom_timeout = 600  # 10 minutes

session = AiohttpSession(
    api=TelegramAPIServer.from_base(custom_api_url),
    timeout=custom_timeout
)

default = DefaultBotProperties(parse_mode=ParseMode.HTML)
bot = Bot(token=BOT_TOKEN, default=default, session=session)

dp = Dispatcher()

db = DataBase()

os.makedirs("downloads", exist_ok=True)


async def send_analytics(user_id, chat_type, action_name):
    params = {
        'client_id': str(user_id),
        'user_id': str(user_id),
        'events': [{
            'name': action_name,
            'params': {
                'chat_type': chat_type,
                "session_id": str(user_id),
                "engagement_time_msec": "1000"
            }
        }],
    }
    async with httpx.AsyncClient() as client:
        await client.post(
            f'https://www.google-analytics.com/mp/collect?measurement_id={MEASUREMENT_ID}&api_secret={API_SECRET}',
            json=params)


async def health_check(request):
    return web.Response(text="OK")


async def start_health_server():
    app = web.Application()
    app.router.add_get("/", health_check)
    runner = web.AppRunner(app)
    await runner.setup()
    site = web.TCPSite(runner, "0.0.0.0", PORT)
    await site.start()
    logging.info(f"Health check server running on port {PORT}")


async def main():
    import handlers
    import middlewares
    from handlers.admin import clear_downloads_and_notify

    if not os.path.exists(OUTPUT_DIR):
        os.makedirs(OUTPUT_DIR)

    dp.include_router(handlers.router)
    for middleware in middlewares.__all__:
        dp.message.outer_middleware(middleware())
        dp.callback_query.outer_middleware(middleware())
        dp.inline_query.outer_middleware(middleware())
    await bot.set_my_commands(commands=BOT_COMMANDS)
    await bot.delete_webhook(drop_pending_updates=True)

    crontab('0 0 * * *', func=clear_downloads_and_notify, start=True)

    await asyncio.gather(start_health_server(), dp.start_polling(bot))


if __name__ == "__main__":
    asyncio.run(main())
