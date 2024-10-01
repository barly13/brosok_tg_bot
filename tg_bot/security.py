from aiogram.fsm.context import FSMContext
from aiogram.types import Message, CallbackQuery

from tg_bot.settings import USERS_DICT_IDS


def user_access(function):
    async def wrapper(event, state: FSMContext):
        if isinstance(event, Message):
            chat_id = event.chat.id
        elif isinstance(event, CallbackQuery):
            chat_id = event.message.chat.id
        else:
            return

        if chat_id in USERS_DICT_IDS.values():
            await function(event, state)
        else:
            if isinstance(event, Message):
                await event.answer('Доступ к боту вам запрещен')
            elif isinstance(event, CallbackQuery):
                await event.message.answer('Доступ к боту вам запрещен')

    return wrapper
