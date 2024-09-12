from aiogram.fsm.context import FSMContext
from aiogram.types import Message

from tg_bot.settings import users_dict_ids


def user_access(function):
    async def wrapper(message: Message, state: FSMContext):
        if message.chat.id in users_dict_ids.values():
            await function(message, state)
        else:
            await message.answer('Доступ к боту вам запрещен')

    return wrapper
