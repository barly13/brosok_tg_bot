import typing

from aiogram.types import KeyboardButton
from aiogram.utils.keyboard import InlineKeyboardBuilder, ReplyKeyboardBuilder

from database.models.Employee import Employee
from tg_bot.static.emojis import Emoji

fill_out_report_kb = [
    [
        KeyboardButton(text=f'{str(Emoji.EmployeeEmoji)} Выбрать сотрудника')
    ],
    [
        KeyboardButton(text=f'{str(Emoji.MainMenu)} Главное меню')
    ]
]

get_report_kb = [
    [
        KeyboardButton(text=f'{str(Emoji.ReportMenu)} Составить Excel-таблицу')
    ],
    [
        KeyboardButton(text=f'{str(Emoji.MainMenu)} Главное меню')
    ]
]


fill_out_employee_report_kb = [
    [
        KeyboardButton(text=f'{str(Emoji.TechnicalSpecification)} Наименование работ в соответствии с ТЗ')
    ],
    [
        KeyboardButton(text=f'{str(Emoji.WrenchEmoji)} Фактическое выполнение работы за отчетный период')
    ],
    [
        KeyboardButton(text=f'{str(Emoji.Success)} Полученный результат (вид отчетности)')
    ],
    [
        KeyboardButton(text=f'{str(Emoji.New)} План работ на следующую неделю')
    ],
    [
        KeyboardButton(text=f'{str(Emoji.Note)} Примечание')
    ],
    [
        KeyboardButton(text=f'{str(Emoji.MainMenu)} Главное меню')
    ]
]


def generate_inline_kb_for_employees_list(employees: typing.List[Employee]) -> InlineKeyboardBuilder:
    kb = InlineKeyboardBuilder()
    for employee in employees:
        kb.button(text=f'{employee.full_name}', callback_data=f'employee_{employee.id}')

    kb.adjust(1)
    return kb