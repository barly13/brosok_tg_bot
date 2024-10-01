from aiogram import Dispatcher, Router
from aiogram.fsm.storage.memory import MemoryStorage

from tg_bot.routers.main.main_handler import base_main_router
from tg_bot.routers.reports.router import base_report_router
from tg_bot.settings import BOT


async def start_bot():
    router = Router()
    router.include_routers(
        base_main_router,
        base_report_router
    )

    dp = Dispatcher(storage=MemoryStorage())
    dp.include_router(router=router)
    await BOT.delete_webhook(drop_pending_updates=True)
    await dp.start_polling(BOT, allowed_updates=dp.resolve_used_update_types())
