from aiogram.types import InlineKeyboardButton
from aiogram.utils.keyboard import InlineKeyboardBuilder

from tg_bot.static.emojis import Emoji


def generate_inline_kb_for_main_menu():
    main_menu_kb = InlineKeyboardBuilder()

    main_menu_kb.row(InlineKeyboardButton(text=f'{str(Emoji.PenEmoji)} Заполнить отчет',
                                          callback_data='fill_out_report'))
    main_menu_kb.row(InlineKeyboardButton(text=f'{str(Emoji.ReportMenu)} Получить отчет', callback_data='get_report'))
    main_menu_kb.row(InlineKeyboardButton(text=f'{str(Emoji.RobotEmoji)} Инструкция по использованию',
                                          callback_data='get_instructions'))

    return main_menu_kb.as_markup()
