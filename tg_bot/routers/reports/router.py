from aiogram import Router

from tg_bot.routers.reports.handlers.filling_out_report_handler import filling_out_report_router
from tg_bot.routers.reports.handlers.get_report_handler import get_report_router

base_report_router = Router()
base_report_router.include_routers(
    filling_out_report_router,
    get_report_router
)