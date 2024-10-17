import json

import re

from database.models.Employee import Employee
from database.models.ReportData import ReportData
from response import Response
from datetime import datetime, timedelta, date
from typing import List, Tuple, Dict, Any, Set, Optional

from tg_bot.routers.reports.backend.absence_reasons_enum import AbsenceReasons

english_to_russians_months = {
    'January': 'января', 'February': 'февраля', 'March': 'марта',
    'April': 'апреля', 'May': 'мая', 'June': 'июня',
    'July': 'июля', 'August': 'августа', 'September': 'сентября',
    'October': 'октября', 'November': 'ноября', 'December': 'декабря'
}

russian_to_english_months = {
    'января': 'January', 'февраля': 'February', 'марта': 'March',
    'апреля': 'April', 'мая': 'May', 'июня': 'June', 'июля': 'July',
    'августа': 'August', 'сентября': 'September', 'октября': 'October',
    'ноября': 'November', 'декабря': 'December'
}

weekday_to_deltas = {
    3: 6, 4: 5, 5: 4, 6: 3, 0: 2, 1: 1, 2: 0
}

report_data_dict = {'actual_performance': '"Выполненные работы"', 'absence_periods': '"Период(ы) отсутствия"',
                    'absence_dates': '"Даты отсутствия"', 'obtained_result': '"Полученный результат"',
                    'employee_id': '"ФИО"'}


async def get_all_employees() -> Response:
    try:
        return Response(value=Employee.get_all())
    except Exception as exp:
        return Response(message=f'Не удалось получить сотрудников для составление отчета: {exp}', error=True)


async def get_employee_by_id(employee_id: int) -> Response:
    try:
        return Response(value=Employee.get_by_id(employee_id))
    except Exception as exp:
        return Response(message=f'Не удалось получить данные о сотруднике: {exp}', error=True)


async def update_employee_absence_reason_by_id(employee_id: int, absence_reason: str) -> Response:
    if Employee.update(object_id=employee_id, absence_reason=absence_reason):
        return Response(message='Причина отсутствия записана')

    return Response(message='Не удалось обновить причину отсутствия сотрудника', error=True)


async def get_all_report_data():
    try:
        return Response(value=ReportData.get_all())
    except Exception as exp:
        return Response(message=f'Не удалось получить данные для отчета: {exp}', error=True)


async def add_report_data(actual_performance: str, obtained_result: str, employee_id: int):
    try:
        ReportData.create(
            employee_id=employee_id,
            actual_performance=actual_performance,
            obtained_result=obtained_result,
        )
        return Response(message='Запись в отчет успешно создана')
    except Exception as exp:
        return Response(message=f'Не удалось сохранить данные для отчета: {exp}', error=True)


def get_date_from_desc(date_desc: str) -> date:
    for key, value in russian_to_english_months.items():
        if key in date_desc:
            date_desc = date_desc.replace(key, value)
            break

    current_date = datetime.strptime(date_desc, '"%d" %B %Y г.').date()

    return current_date


def get_period_from_desc(period_desc: str) -> List[date]:
    first_part, second_part = period_desc.split(' по ')

    second_date = get_date_from_desc(second_part)

    if 'г.' in first_part:
        first_date = get_date_from_desc(first_part)
    else:
        first_date = get_date_from_desc(f'{first_part} {second_date.year} г.')

    return [first_date, second_date]


def get_earlier_absence_data_dict_from_desc(absence_reason_full_desc: str) -> Dict[str, Any]:
    earlier_period_count = 1
    earlier_absence_data_dict = {}

    for absence_reason_desc in absence_reason_full_desc.split('|'):
        if absence_reason_desc in [absence_reason.desc for absence_reason in list(AbsenceReasons)]:
            if absence_reason_desc != AbsenceReasons.NoReason.desc:
                earlier_absence_data_dict[f'{earlier_period_count}_earlier_period'] = [*get_current_work_period()]
                earlier_period_count += 1
            continue

        for partial_absence_reason in absence_reason_desc.split(', '):
            if '-' in partial_absence_reason:
                current_date = get_date_from_desc(partial_absence_reason.split('-')[0].rstrip())

                if 'start_day_earlier_dates' in earlier_absence_data_dict:
                    earlier_absence_data_dict[f'earlier_{current_date.day}.{current_date.month}.{current_date.year}'] \
                        = current_date
                else:
                    earlier_absence_data_dict['start_day_earlier_dates'] = current_date

            elif ' с ' in partial_absence_reason:
                period = get_period_from_desc(partial_absence_reason.split(' с ')[1].rstrip())
                earlier_absence_data_dict[f'{earlier_period_count}_earlier_period'] = period
                earlier_period_count += 1

            else:
                current_date = get_date_from_desc(partial_absence_reason.split(' ', 1)[1])
                if 'start_day_earlier_dates' in earlier_absence_data_dict:
                    earlier_absence_data_dict[f'earlier_{current_date.day}.{current_date.month}.{current_date.year}'] \
                        = current_date
                else:
                    earlier_absence_data_dict['start_day_earlier_dates'] = current_date

    return earlier_absence_data_dict


def get_new_date_and_work_dates_set(callback_data: str) -> Tuple[date, Set[date]]:
    year, month, day = map(int, callback_data.split(':')[1:])
    new_date = date(int(year), int(month), int(day))
    work_dates_set = set(create_date_range(*get_current_work_period()))

    return new_date, work_dates_set


def create_date_range(start_date: date, end_date: date) -> List[date]:
    date_range = []
    current_date = start_date

    while current_date <= end_date:
        date_range.append(current_date)
        current_date += timedelta(days=1)

    return date_range


def get_current_work_period() -> Tuple[date, date]:
    today = datetime.today().date()

    today_weekday = today.weekday()
    if today_weekday > 2:
        start_date = today - timedelta(days=today_weekday - 3)
        end_date = today + timedelta(days=3 - today_weekday + 6)
    else:
        start_date = today + timedelta(days=2 - today_weekday - 6)
        end_date = today + timedelta(days=2 - today_weekday)

    return start_date, end_date


def get_dates_range(data: Dict[str, Any]):
    start_dates, end_dates = [], []

    pattern = re.compile(r'\d+_period$')

    for key, value in data.items():
        if pattern.match(key) and type(value) is list:
            start_dates.append(min(value))
            end_dates.append(max(value))

    return start_dates, end_dates


def get_date_sets(start_date: date, end_date: date, data: Dict[str, Any]) \
        -> Tuple[Set[date], Set[date], Set[date]]:
    dates_range_set = set(create_date_range(start_date, end_date))
    work_dates_set = set(create_date_range(*get_current_work_period()))
    periods_and_dates_set = update_periods_and_dates_set(data, dates_range_set)

    return dates_range_set, work_dates_set, periods_and_dates_set


def format_period(start_date: date, end_date: date):
    if start_date.year == end_date.year:
        start_text = format_date(start_date)

    else:
        start_text = format_date(start_date, is_same_year=False)

    end_text = format_date(end_date, is_same_year=False)

    return start_text, end_text


def format_date(current_date: date, is_same_year: bool = True) -> str:
    day = current_date.strftime('%d')
    month = english_to_russians_months[current_date.strftime('%B')]

    if is_same_year:
        return f'"{day}" {month}'

    else:
        year = current_date.year
        return f'"{day}" {month} {year} г.'


def get_day_month_year(current_date: date) -> Tuple[str, str, int]:
    day = current_date.strftime('%d')
    month = english_to_russians_months[current_date.strftime('%B')]
    year = current_date.year

    return day, month, year


def generate_dates_text(data: Dict[str, Any]) -> Tuple[str, str, List[date]]:
    start_day, start_month, start_year = get_day_month_year(data['start_day_dates'])
    formatted_dates = [data['start_day_dates']]

    selected_days = f'{start_day} {start_month} {start_year} г.\n'
    formatted_days = f'"{start_day}" {start_month} {start_year} г. - (), '

    date_pattern = re.compile(r'^\d{1,2}\.\d{1,2}\.\d{4}$')

    for key in data.keys():
        if date_pattern.match(key):
            current_date = data[key]
            day, month, year = get_day_month_year(current_date)

            selected_days += f'{day} {month} {year} г.\n'
            formatted_days += f'"{day}" {month} {year} г. - (), '
            formatted_dates.append(data[key])

    formatted_days = formatted_days.rstrip(', ')
    return selected_days, formatted_days, formatted_dates


def update_periods_and_dates_set(data: Dict[str, Any], periods_and_dates_set: Set[Any]) -> Set[Any]:
    if {'1_earlier_period', 'start_day_earlier_dates'}.intersection(data.keys()):
        if '1_earlier_period' in data:
            period_search_pattern = re.compile(r'\d+_earlier_period$')
            for key, value in data.items():
                if period_search_pattern.match(key):
                    earlier_range = create_date_range(value[0], value[1])
                    for earlier_date in earlier_range:
                        periods_and_dates_set.add(earlier_date)

        if 'start_day_earlier_dates' in data:
            periods_and_dates_set.add(data['start_day_earlier_dates'])
            dates_search_pattern = re.compile(r'earlier_\d{1,2}\.\d{1,2}\.\d{4}$')
            for key, value in data.items():
                if dates_search_pattern.match(key):
                    periods_and_dates_set.add(value)

    return periods_and_dates_set


def update_absence_reason(first_employee_absence_list: List[str], second_employee_absence_list: List[str]) -> str:
    for index in range(len(second_employee_absence_list)):
        if index < len(first_employee_absence_list):
            if (first_employee_absence_list[index] == AbsenceReasons.NoReason.desc
                    and second_employee_absence_list[index] != AbsenceReasons.NoReason.desc):
                first_employee_absence_list[index] = second_employee_absence_list[index]
            elif (first_employee_absence_list[index] not in [absence_reason.desc for absence_reason
                                                             in list(AbsenceReasons)]
                  and second_employee_absence_list[index] != AbsenceReasons.NoReason.desc):
                first_employee_absence_list[index] += f', {second_employee_absence_list[index]}'

    absence_reason_full_desc = '|'.join(first_employee_absence_list)
    return absence_reason_full_desc


def get_absence_reason_full_desc(employee_id: int, absence_reason_desc: str) -> str:
    employee_absence_reason_list = Employee.get_by_id(employee_id).absence_reason.split('|')
    split_absence_reason_desc = absence_reason_desc.split('|')

    if len(employee_absence_reason_list) >= len(split_absence_reason_desc):
        return update_absence_reason(employee_absence_reason_list, split_absence_reason_desc)

    else:
        return update_absence_reason(split_absence_reason_desc, employee_absence_reason_list)


def generate_absence_reason_full_desc(start_date: date, end_date: date, absence_reason_desc) -> str:
    work_range_set = set(create_date_range(*get_current_work_period()))

    start_work_period, end_work_period = min(work_range_set), max(work_range_set)
    absence_reason_full_desc = ''

    while start_work_period < start_date:
        if start_work_period == end_work_period:
            end_work_period += timedelta(days=7)
            absence_reason_full_desc += 'Работа|'

        start_work_period += timedelta(days=1)

    if start_date == end_date:
        absence_reason_full_desc += f'{absence_reason_desc} {format_date(start_date, is_same_year=False)}'

    elif end_date <= end_work_period:
        start_period_text, end_period_text = format_period(start_date, end_date)
        absence_reason_full_desc += f'{absence_reason_desc} с {start_period_text} по {end_period_text}'

    else:
        if start_date == end_work_period:
            absence_reason_full_desc += f'{absence_reason_desc} {format_date(start_date, is_same_year=False)}|'

        else:
            start_period_text, end_period_text = format_period(start_date, end_work_period)
            absence_reason_full_desc += f'{absence_reason_desc} с {start_period_text} по {end_period_text}|'

        start_work_period = end_work_period + timedelta(days=1)
        end_work_period += timedelta(days=7)

        while start_work_period < end_date:
            if abs(start_work_period - end_date) < timedelta(days=6):
                start_period_text, end_period_text = format_period(start_work_period, end_date)
                absence_reason_full_desc += f'{absence_reason_desc} с {start_period_text} по {end_period_text}'
                break

            start_period_text, end_period_text = format_period(start_work_period, end_work_period)
            absence_reason_full_desc += f'{absence_reason_desc} с {start_period_text} по {end_period_text}|'

            start_work_period = end_work_period + timedelta(days=1)
            end_work_period += timedelta(days=7)

        if start_work_period == end_date:
            absence_reason_full_desc += f'{absence_reason_desc} {format_date(start_work_period, is_same_year=False)}'

    return absence_reason_full_desc.rstrip('|')


def parse_absence_dates_and_periods(absence_dates_and_periods_str: str,
                                    formatted_dates_and_periods: List[Any]) -> str:
    work_range_set = set(create_date_range(*get_current_work_period()))

    start_work_period, end_work_period = min(work_range_set), max(work_range_set)

    dates_and_periods = []

    for absence_str_parts, formatted_item in zip(absence_dates_and_periods_str.split(', '),
                                                 formatted_dates_and_periods):
        if '-' in absence_str_parts:
            dates_and_periods.append((absence_str_parts.split('-')[1].strip(), formatted_item))
        else:
            dates_and_periods.append((absence_str_parts.split(' с ')[0].strip(), formatted_item))

    dates_and_periods.sort(key=lambda x: x[1] if isinstance(x[1], date) else x[1][1])

    week_absence_string = ''

    for index, date_or_period in enumerate(dates_and_periods):
        if isinstance(date_or_period[1], tuple):
            start_date, end_date = date_or_period[1]
            while start_work_period < start_date:
                if start_work_period == end_work_period:
                    end_work_period += timedelta(days=7)
                    week_absence_string += 'Работа|'

                start_work_period += timedelta(days=1)

            if start_date == end_date:
                week_absence_string += f'{date_or_period[0]} {format_date(start_date, is_same_year=False)}'

            elif end_date <= end_work_period:
                start_period_text, end_period_text = format_period(start_date, end_date)
                week_absence_string += f'{date_or_period[0]} с {start_period_text} по {end_period_text}'

            else:
                if start_date == end_work_period:
                    week_absence_string += f'{date_or_period[0]} {format_date(start_date, is_same_year=False)}|'

                else:
                    start_period_text, end_period_text = format_period(start_date, end_work_period)
                    week_absence_string += f'{date_or_period[0]} с {start_period_text} по {end_period_text}|'

                start_work_period = end_work_period + timedelta(days=1)
                end_work_period += timedelta(days=7)

                while start_work_period < end_date:
                    if abs(start_work_period - end_date) < timedelta(days=6):
                        start_period_text, end_period_text = format_period(start_work_period, end_date)
                        week_absence_string += f'{date_or_period[0]} с {start_period_text} по {end_period_text}'
                        break

                    start_period_text, end_period_text = format_period(start_work_period, end_work_period)
                    week_absence_string += f'{date_or_period[0]} с {start_period_text} по {end_period_text}|'

                    start_work_period = end_work_period + timedelta(days=1)
                    end_work_period += timedelta(days=7)

                if start_work_period == end_date:
                    week_absence_string += f'{date_or_period[0]} {format_date(start_work_period, is_same_year=False)}'

        else:
            current_date = date_or_period[1]
            while current_date > end_work_period:
                if current_date - end_work_period >= timedelta(days=1):
                    week_absence_string += 'Работа|'

                end_work_period += timedelta(days=7)

            week_absence_string += f'{format_date(current_date, is_same_year=False)} - {date_or_period[0]}'

        if index + 1 < len(dates_and_periods):
            next_date_or_period = dates_and_periods[index + 1]
            if isinstance(next_date_or_period[1], tuple):
                next_date = next_date_or_period[1][0]

            else:
                next_date = next_date_or_period[1]

            if next_date > end_work_period:
                if not week_absence_string.endswith('|'):
                    week_absence_string += '|'

                start_work_period = end_work_period + timedelta(days=1)
                end_work_period += timedelta(days=7)

            else:
                week_absence_string += ', '

    return week_absence_string


def generate_period_text(start_dates: List[date], end_dates: List[date],
                         formatted_periods: List[Any] | None = None) -> Tuple[str, str, List[Any]]:
    selected_period_list, formatted_period_list = [], []
    formatted_periods_and_dates = formatted_periods if formatted_periods else []

    for start_date, end_date in zip(start_dates, end_dates):
        start_day, start_month, start_year = get_day_month_year(start_date)
        end_day, end_month, end_year = get_day_month_year(end_date)

        if start_date != end_date:
            selected_period = f'{start_day} {start_month} {start_year} г. - {end_day} {end_month} {end_year} г.'

            if start_year == end_year:
                formatted_period = f'() с "{start_day}" {start_month} по "{end_day}" {end_month} {end_year} г.'
            else:
                formatted_period = (f'() с "{start_day}" {start_month} {start_year} г. по '
                                    f'"{end_day}" {end_month} {end_year} г.')

        else:
            selected_period = f'{start_day} {start_month} {start_year} г.'
            formatted_period = f'() "{end_day}" {end_month} {start_year} г.'

        formatted_periods_and_dates.append((start_date, end_date))
        selected_period_list.append(selected_period)
        formatted_period_list.append(formatted_period)

    selected_periods = '\n'.join(selected_period_list)
    formatted_periods = ', '.join(formatted_period_list)

    return selected_periods, formatted_periods, formatted_periods_and_dates


def get_final_employee_info(data: Dict[str, Any]) -> str:
    employee_info = ''

    for key, value in data.items():
        if key != 'employee_id' and key in report_data_dict.keys():
            if key == 'absence_periods':
                absence_periods = ''

                for absence_period in value:
                    start_date_period = absence_period[0].strftime("%d.%m.%Y")
                    end_date_period = absence_period[1].strftime("%d.%m.%Y")
                    absence_periods += f'{start_date_period} - {end_date_period}\n'

                employee_info += f'{report_data_dict[key]}:\n\n{absence_periods}\n'

            if key == 'absence_dates':
                absence_dates = ''

                for index in range(len(value)):
                    if index != len(value) - 1:
                        absence_dates += f'{value[index].strftime("%d.%m.%Y")}, '

                    else:
                        absence_dates += f'{value[index].strftime("%d.%m.%Y")}'

                employee_info += f'{report_data_dict[key]}: {absence_dates}\n'

            if key != 'absence_periods' and key != 'absence_dates':
                employee_info += f'\n{report_data_dict[key]}: {value}\n'

    return employee_info
