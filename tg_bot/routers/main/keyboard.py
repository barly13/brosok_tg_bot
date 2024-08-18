from aiogram.types import KeyboardButton
from aiogram.utils.keyboard import ReplyKeyboardBuilder

from tg_bot.static.emojis import Emoji


def generate_reply_keyboard_for_main_menu():
    builder = ReplyKeyboardBuilder()
    builder.button(text=f'{str(Emoji.PenEmoji)} Заполнить отчет')
    builder.button(text=f'{str(Emoji.ReportMenu)} Получить отчет')
    builder.adjust(2, 1)
    return builder.as_markup(resize_keyboard=True)