import os

from aiogram import Router, F
from aiogram.fsm.context import FSMContext
from aiogram.types import FSInputFile, CallbackQuery

from tg_bot.routers.reports.backend import get_report_backend
from tg_bot.security import user_access
from tg_bot.settings import MAKER_CONTACT

get_report_router = Router()


@get_report_router.callback_query(F.data == 'get_report')
@user_access
async def get_excel_report_handler(callback: CallbackQuery, state: FSMContext):
    excel_report = await get_report_backend.get_excel_report()
    await callback.message.answer_document(excel_report, caption='Отчет')


@get_report_router.callback_query(F.data == 'get_instructions')
@user_access
async def get_instruction_handler(callback: CallbackQuery, state: FSMContext):
    instruction_docx = FSInputFile(path=os.path.join(os.getcwd(), 'Инструкция ТГ-бота.docx'),
                                   filename='Инструкция ТГ-бота.docx')
    await callback.message.answer_document(instruction_docx, caption='Инструкция')


@get_report_router.callback_query(F.data == 'get_maker_contact')
@user_access
async def get_maker_contact_handler(callback: CallbackQuery, state: FSMContext):
    await callback.message.answer_contact(
        phone_number=MAKER_CONTACT['phone_number'],
        first_name=MAKER_CONTACT['first_name'],
        last_name=MAKER_CONTACT['last_name'],
    )
