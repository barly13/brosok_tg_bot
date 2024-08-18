from aiogram import Router, F
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import StatesGroup, State
from aiogram.types import Message, ReplyKeyboardMarkup, URLInputFile

from tg_bot.functions import cleanup
from tg_bot.routers.reports.backend import get_report_backend
from tg_bot.routers.reports.keyboard import get_report_kb
from tg_bot.security import user_access
from tg_bot.settings import bot
from tg_bot.static.emojis import Emoji

get_report_router = Router()


@get_report_router.message(cleanup(F.text).lower() == 'получить отчет')
@user_access
async def get_report_menu_handler(message: Message, state: FSMContext):
    markup = ReplyKeyboardMarkup(keyboard=get_report_kb, resize_keyboard=True)
    await message.answer('Получение отчета', reply_markup=markup)


@get_report_router.message(cleanup(F.text).lower() == 'составить excel-таблицу')
@user_access
async def get_excel_report(message: Message, state: FSMContext):
    excel_report = await get_report_backend.get_excel_report()

    mes = 'Отчет'

    await bot.send_document(message.from_user.id, excel_report, caption=mes)
