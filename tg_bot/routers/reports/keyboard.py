import typing

from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.utils.keyboard import InlineKeyboardBuilder, ReplyKeyboardBuilder

from database.models.Employee import Employee
from tg_bot.routers.reports.backend.absence_reasons_enum import AbsenceReasons
from datetime import datetime, timedelta

from tg_bot.routers.reports.backend.filling_out_report_backend import get_current_work_period
from tg_bot.static.emojis import Emoji


def generate_inline_kb_for_employees_list(employees: typing.List[Employee]):
    employees_list_kb = InlineKeyboardBuilder()

    for employee in employees:
        employees_list_kb.button(text=f'{employee.full_name}', callback_data=f'employee_{employee.id}')

    employees_list_kb.adjust(1)
    return employees_list_kb.as_markup()


def generate_inline_kb_for_absence_reasons():
    absence_reasons_kb = InlineKeyboardBuilder()

    for absence_reason in AbsenceReasons:
        absence_reasons_kb.button(text=f'{absence_reason.desc}', callback_data=f'absence_reason__{absence_reason.num}')

    absence_reasons_kb.adjust(1)
    return absence_reasons_kb.as_markup()


def bold_numbers(number):
    bold_digits = {
        '0': '𝟎', '1': '𝟏', '2': '𝟐', '3': '𝟑', '4': '𝟒',
        '5': '𝟓', '6': '𝟔', '7': '𝟕', '8': '𝟖', '9': '𝟗'
    }
    return str(Emoji.CheckMarkEmoji) + ''.join(bold_digits.get(digit, digit) for digit in str(number))


def generate_period_or_dates_inline_kb():
    period_or_dates_kb = InlineKeyboardBuilder()

    period_or_dates_kb.row(InlineKeyboardButton(text=f'{str(Emoji.CalendarEmoji)} - {str(Emoji.CalendarEmoji)} '
                                                     f'Выбрать период отсутствия.',
                                                callback_data='choose_period'))
    period_or_dates_kb.row(InlineKeyboardButton(text=f'{str(Emoji.CalendarEmoji)} Выбрать отдельные даты',
                                                callback_data='choose_dates'))
    period_or_dates_kb.row(InlineKeyboardButton(text=f'{str(Emoji.RightArrowEmoji)} Пропустить',
                                                callback_data='skip_absence'))
    period_or_dates_kb.row(InlineKeyboardButton(text=f'{str(Emoji.Error)} Отмена', callback_data='cancel_all'))

    return period_or_dates_kb.as_markup()


def generate_calendar_inline_kb(year: int, month: int, is_period: bool = True, first_date_selected: bool = False):
    months_dict = {1: 'Январь', 2: 'Февраль', 3: 'Март', 4: 'Апрель', 5: 'Май', 6: 'Июнь', 7: 'Июль', 8: 'Август',
                   9: 'Сентябрь', 10: 'Октябрь', 11: 'Ноябрь', 12: 'Декабрь'}

    days_of_week = ['Пн', 'Вт', 'Ср', 'Чт', 'Пт', 'Сб', 'Вс']

    start_date, end_date = get_current_work_period()

    calendar_keyboard_builder = InlineKeyboardBuilder()

    calendar_keyboard_builder.row(
        InlineKeyboardButton(text=str(months_dict[month]), callback_data='ignore'),
        InlineKeyboardButton(text=str(year), callback_data='ignore')
    )

    calendar_keyboard_builder.row(*[InlineKeyboardButton(text=week_day, callback_data='ignore')
                                    for week_day in days_of_week])

    first_date = datetime(year, month, 1)
    first_day = first_date.weekday()
    start_empty_buttons = [InlineKeyboardButton(text=' ', callback_data='ignore') for _ in range(first_day)]

    days_in_month = (first_date.replace(month=month % 12 + 1) - timedelta(days=1)).day
    last_date = datetime(year, month, days_in_month)
    last_day = last_date.weekday()

    calendar_days = []
    for day in range(1, days_in_month + 1):
        current_date = datetime(year, month, day)

        if start_date <= current_date <= end_date:
            if is_period:
                calendar_days.append(InlineKeyboardButton(
                    text=bold_numbers(day), callback_data=f'day_period:{year}:{month}:{day}'
                ))
            else:
                calendar_days.append(InlineKeyboardButton(
                    text=bold_numbers(day), callback_data=f'day_dates:{year}:{month}:{day}'
                ))
        else:
            if is_period:
                calendar_days.append(InlineKeyboardButton(
                    text=str(day), callback_data=f'day_period:{year}:{month}:{day}'
                ))
            else:
                calendar_days.append(InlineKeyboardButton(
                    text=str(day), callback_data=f'day_dates:{year}:{month}:{day}'
                ))

    last_empty_buttons = [InlineKeyboardButton(text=' ', callback_data='ignore') for _ in range(last_day, 6)]

    calendar_buttons = start_empty_buttons + calendar_days + last_empty_buttons

    for i in range(0, len(calendar_buttons), 7):
        calendar_keyboard_builder.row(*calendar_buttons[i:i + 7])

    if is_period:
        calendar_keyboard_builder.row(
            InlineKeyboardButton(text='<<', callback_data=f'prev_month_period:{year}:{month}'),
            InlineKeyboardButton(text='>>', callback_data=f'next_month_period:{year}:{month}')
        )
    else:
        calendar_keyboard_builder.row(
            InlineKeyboardButton(text='<<', callback_data=f'prev_month_dates:{year}:{month}'),
            InlineKeyboardButton(text='>>', callback_data=f'next_month_dates:{year}:{month}')
        )

    if not is_period and first_date_selected:
        calendar_keyboard_builder.row(InlineKeyboardButton(text=f'{str(Emoji.DownArrowEmoji)} Продолжить',
                                                           callback_data='continue_filling_in'))

    calendar_keyboard_builder.row(
        InlineKeyboardButton(text=f'{str(Emoji.Error)} Отмена', callback_data=f'cancel_all'),
        InlineKeyboardButton(text=f'{str(Emoji.RightArrowEmoji)} Пропустить', callback_data=f'skip_absence')
    )

    return calendar_keyboard_builder.as_markup()


def generate_obtained_result_inline_kb():
    obtained_result_kb = InlineKeyboardBuilder()
    obtained_result_kb.row(
        InlineKeyboardButton(text=f'{Emoji.WrenchEmoji} Рабочие материалы',
                             callback_data='obtained_result:working_materials'),
        InlineKeyboardButton(text=f'{Emoji.TechnicalSpecification} Документы',
                             callback_data='obtained_result:documents')
    )

    obtained_result_kb.row(
        InlineKeyboardButton(text=f'{Emoji.Error} Отмена', callback_data='cancel_all')
    )
    return obtained_result_kb.as_markup()


def generate_absence_reason_inline_kb():
    absence_reason_inline_kb = InlineKeyboardBuilder()

    absence_reason_inline_kb.row(InlineKeyboardButton(text=f'{str(Emoji.BusinessTripEmoji)} Командировка',
                                                      callback_data='absence_reason:business_trip'))
    absence_reason_inline_kb.row(
        InlineKeyboardButton(text=f'{str(Emoji.VacationEmoji)} Отпуск', callback_data='absence_reason:vacation'))
    absence_reason_inline_kb.row(InlineKeyboardButton(text=f'{str(Emoji.SicknessEmoji)} Больничный',
                                                      callback_data='absence_reason:sickness'))
    absence_reason_inline_kb.row(InlineKeyboardButton(text=f'{str(Emoji.PenEmoji)} Заполнить вручную',
                                                      callback_data='absence_reason:fill_manual'))

    absence_reason_inline_kb.row(InlineKeyboardButton(text=f'{Emoji.Error} Отмена', callback_data='cancel_all'))

    return absence_reason_inline_kb.as_markup()


def generate_final_inline_kb():
    final_inline_kb = InlineKeyboardBuilder()

    final_inline_kb.row(InlineKeyboardButton(text=f'{str(Emoji.Success)} Сохранить', callback_data='save_data'))
    final_inline_kb.row(InlineKeyboardButton(text=f'{str(Emoji.EmployeeEmoji)} Сменить ФИО',
                                             callback_data='change_name'))
    final_inline_kb.row(InlineKeyboardButton(text=f'{str(Emoji.Error)} Отмена', callback_data='cancel_all'))

    return final_inline_kb.as_markup()


def generate_fill_manual_inline_kb():
    fill_manual_kb = InlineKeyboardBuilder()

    fill_manual_kb.row(InlineKeyboardButton(text=f'{str(Emoji.PenEmoji)} Заполнить вручную',
                                            callback_data='absence_reason:fill_manual'))

    fill_manual_kb.row(InlineKeyboardButton(text=f'{Emoji.Error} Отмена', callback_data='cancel_all'))

    return fill_manual_kb.as_markup()


def generate_cancel_inline_kb():
    cancel_inline_kb = InlineKeyboardBuilder()

    cancel_inline_kb.button(text=f'{str(Emoji.Error)} Отмена', callback_data='cancel_all')

    return cancel_inline_kb.as_markup()

