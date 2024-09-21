import os

from aiogram import Router, F
from aiogram.fsm.context import FSMContext
from aiogram.types import Message, ReplyKeyboardMarkup, FSInputFile

from tg_bot.functions import cleanup
from tg_bot.routers.reports.backend import get_report_backend
from tg_bot.security import user_access
from tg_bot.settings import bot

get_report_router = Router()


@get_report_router.message(cleanup(F.text).lower() == 'получить отчет')
@user_access
async def get_excel_report(message: Message, state: FSMContext):
    excel_report = await get_report_backend.get_excel_report()
    await bot.send_document(message.from_user.id, excel_report, caption='Отчет')


@get_report_router.message(cleanup(F.text).lower() == 'инструкция по использованию')
@user_access
async def get_instruction(message: Message, state: FSMContext):
    instruction_docx = FSInputFile(path=os.path.join(os.getcwd(), 'Инструкция ТГ-бота.docx'),
                                   filename='Инструкция ТГ-бота.docx')

    await bot.send_document(message.from_user.id, instruction_docx, caption='Инструкция')
