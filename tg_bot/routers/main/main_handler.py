from aiogram import Router, F
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.types import Message

from tg_bot.functions import cleanup
from tg_bot.routers.main.keyboard import generate_reply_keyboard_for_main_menu
from tg_bot.routers.main.main_backend import init_jobs
from tg_bot.security import user_access

from tg_bot.static.emojis import Emoji

base_main_router = Router()


@base_main_router.message(Command('start'))
@base_main_router.message(cleanup(F.text).lower() == 'главное меню')
@user_access
async def main_menu_handler(message: Message, state: FSMContext):
    if message.text.lower() == '/start':
        await message.answer(f'{str(Emoji.Success)} Бот готов к использованию!',
                             reply_markup=generate_reply_keyboard_for_main_menu())
    else:
        await message.answer(f'Главное меню', reply_markup=generate_reply_keyboard_for_main_menu())

    await init_jobs()
    await state.clear()

