from aiogram import Router, F
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.types import Message, ReplyKeyboardRemove

from tg_bot.functions import cleanup
from tg_bot.routers.main.keyboard import generate_inline_kb_for_main_menu
from tg_bot.routers.main.main_backend import init_jobs
from tg_bot.security import user_access

from tg_bot.static.emojis import Emoji

base_main_router = Router()


@base_main_router.message(Command('start'))
@user_access
async def main_menu_handler(message: Message, state: FSMContext):
    if message.text.lower() == '/start':
        await message.answer('',
                             reply_markup=ReplyKeyboardRemove())

    await message.answer(f'Главное меню', reply_markup=generate_inline_kb_for_main_menu())

    await init_jobs()
    await state.clear()

