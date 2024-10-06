import json

import re

from database.models.Employee import Employee
from database.models.ReportData import ReportData
from response import Response
from datetime import datetime, timedelta
from typing import List, Tuple, Dict, Any, Set, Optional

months = {
    'January': 'января', 'February': 'февраля', 'March': 'марта',
    'April': 'апреля', 'May': 'мая', 'June': 'июня',
    'July': 'июля', 'August': 'августа', 'September': 'сентября',
    'October': 'октября', 'November': 'ноября', 'December': 'декабря'
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


async def update_absence_period_or_dates_by_id(employee_id: int, absence_period_or_dates: Dict[str, Tuple]) -> Response:
    absence_period_or_dates_json = json.dumps(absence_period_or_dates)

    if Employee.update(object_id=employee_id, absence_period_or_dates=absence_period_or_dates_json):
        return Response(message='Даты или период отсутствия записаны')

    return Response(message='Не удалось обновить даты или период отсутствия!', error=True)


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


def create_date_range(start_date: datetime, end_date: datetime) -> List[datetime]:
    date_range = []
    current_date = start_date

    while current_date <= end_date:
        date_range.append(current_date)
        current_date += timedelta(days=1)

    return date_range


def get_current_work_period() -> Tuple[datetime, datetime]:
    today = datetime.today().replace(hour=0, minute=0, second=0, microsecond=0)

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

    for key, value in data.items():
        if key.endswith('_period') and type(value) is list:
            start_dates.append(min(value))
            end_dates.append(max(value))

    return start_dates, end_dates


def get_date_sets(start_date: datetime, end_date: datetime) -> Tuple[Set[datetime], Set[datetime]]:
    date_range_set = set(create_date_range(start_date, end_date))
    work_date_set = set(create_date_range(*get_current_work_period()))

    return date_range_set, work_date_set


def format_period(start_date: datetime, end_date: datetime):
    if start_date.year == end_date.year:
        start_text = format_date(start_date)

    else:
        start_text = format_date(start_date, is_same_year=False)

    end_text = format_date(end_date)

    return start_text, end_text


def format_date(date: datetime, is_same_year: bool = True) -> str:
    day = date.strftime('%d')
    month = months[date.strftime('%B')]

    if is_same_year:
        return f'"{day}" {month}'

    else:
        year = date.year
        return f'"{day}" {month} {year} г.'


def get_day_month_year(date: datetime) -> Tuple[str, str, int]:
    day = date.strftime('%d')
    month = months[date.strftime('%B')]
    year = date.year

    return day, month, year


def generate_dates_text_and_absence_dates(data: Dict[str, Any]) -> Tuple[str, str, List[datetime]]:
    absence_dates = [data['start_day_dates']]

    start_day, start_month, start_year = get_day_month_year(data['start_day_dates'])

    selected_days = f'{start_day} {start_month} {start_year} г.\n'
    formatted_days = f'"{start_day}" {start_month} {start_year} г. - (), '

    date_pattern = re.compile(r'^\d{2}\.\d{2}\.\d{4}$')

    for key in data.keys():
        if date_pattern.match(key):
            date = data[key]
            absence_dates.append(date)

            day, month, year = get_day_month_year(date)

            selected_days += f'{day} {month} {year} г.\n'
            formatted_days += f'"{day}" {month} {year} г. - (), '

    formatted_days = formatted_days[:len(formatted_days) - 2]
    return selected_days, formatted_days, absence_dates


def generate_period_text(start_dates: List[datetime], end_dates: List[datetime]) -> Tuple[str, str]:
    selected_period_list, formatted_period_list = [], []

    for start_date, end_date in zip(start_dates, end_dates):
        start_day, start_month, start_year = get_day_month_year(start_date)
        end_day, end_month, end_year = get_day_month_year(end_date)

        if start_date != end_date:
            selected_period = f'{start_day} {start_month} {start_year} г. - {end_day} {end_month} {end_year} г.'

            if start_year == end_year:
                formatted_period = f'() c "{start_day}" {start_month} по "{end_day}" {end_month} {end_year} г.'
            else:
                formatted_period = (f'() c "{start_day}" {start_month} {start_year} г. по '
                                    f'"{end_day}" {end_month} {end_year} г.')

        else:
            selected_period = f'{start_day} {start_month} {start_year} г.'
            formatted_period = f'() "{end_day}" {end_month} {start_year} г.'

        selected_period_list.append(selected_period)
        formatted_period_list.append(formatted_period)

    selected_periods = '\n'.join(selected_period_list)
    formatted_periods = ', '.join(formatted_period_list)

    return selected_periods, formatted_periods


def get_partial_end_date(end_date: datetime, work_date_range_set: Set[datetime]):
    return max(work_date_range_set) if end_date > max(work_date_range_set) else None


def get_partial_start_date(start_date: datetime, work_date_range_set: Set[datetime]):
    return min(work_date_range_set) if start_date < min(work_date_range_set) else None


def get_absence_date_sets(data: Dict[str, Any]):
    work_date_range_set = set(create_date_range(*get_current_work_period()))

    if 'absence_dates' in data:
        selected_dates_set = set(data['absence_dates'])
        return selected_dates_set, work_date_range_set

    elif 'absence_period' in data:
        selected_dates_set = set(create_date_range(data['absence_period'][0], data['absence_period'][1]))
        return selected_dates_set, work_date_range_set


def get_final_employee_info(data: Dict[str, Any]) -> str:
    employee_info = ''

    for key, value in data.items():
        if key != 'employee_id' and key in report_data_dict.keys():
            if key == 'absence_periods':
                for date_tuple in value:
                    start_date_period = date_tuple[0].strftime("%d.%m.%Y")
                    end_date_period = date_tuple[1].strftime("%d.%m.%Y")

                    employee_info += f'{report_data_dict[key]}: {start_date_period} - {end_date_period}\n'

            if key == 'absence_dates':
                absence_dates = ''

                for index in range(len(value)):
                    if index != len(value) - 1:
                        absence_dates += f'{value[index].strftime("%d.%m.%Y")}, '

                    else:
                        absence_dates += f'{value[index].strftime("%d.%m.%Y")}'

                employee_info += f'\n{report_data_dict[key]}: {absence_dates}\n'

            else:
                employee_info += f'\n{report_data_dict[key]}: {value}\n'

    return employee_info
