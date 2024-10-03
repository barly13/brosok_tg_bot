from aiogram import Router
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.types import Message

from tg_bot.routers.main.keyboard import generate_inline_kb_for_main_menu
from tg_bot.routers.main.main_backend import init_jobs
from tg_bot.security import user_access

base_main_router = Router()


@base_main_router.message(Command('start'))
@user_access
async def main_menu_handler(message: Message, state: FSMContext):
    await message.answer(f'Главное меню', reply_markup=generate_inline_kb_for_main_menu())

    await init_jobs()
    await state.clear()

