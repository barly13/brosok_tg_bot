import typing

from aiogram.types import KeyboardButton
from aiogram.utils.keyboard import InlineKeyboardBuilder, ReplyKeyboardBuilder

from database.models.Employee import Employee
from tg_bot.routers.reports.backend.absence_reasons_enum import AbsenceReasons
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
        KeyboardButton(text=f'{str(Emoji.WrenchEmoji)} Фактически выполненные работы за отчетный период')
    ],
    [
        KeyboardButton(text=f'{str(Emoji.Success)} Полученный результат (вид отчетности)')
    ],
    [
        KeyboardButton(text=f'{str(Emoji.New)} План работ на следующую неделю')
    ],
    [
        KeyboardButton(text=f'{str(Emoji.Note)} Примечание (при необходимости)')
    ],
    [
        KeyboardButton(text=f'{str(Emoji.Cancel)} Причины отсутствия (при наличии)')
    ],
    [
        KeyboardButton(text=f'{str(Emoji.Start)} Загрузить данные')
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


def generate_inline_kb_for_absence_reasons():
    kb = InlineKeyboardBuilder()
    for absence_reason in AbsenceReasons:
        kb.button(text=f'{absence_reason.desc}', callback_data=f'absence_reason__{absence_reason.num}')

    kb.adjust(1)
    return kb