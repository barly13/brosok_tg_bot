import json

import re

from database.models.Employee import Employee
from database.models.ReportData import ReportData
from response import Response
from datetime import datetime, timedelta
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


def get_new_date_and_work_dates_set(callback_data: str) -> Tuple[datetime, Set[datetime]]:
    year, month, day = map(int, callback_data.split(':')[1:])
    new_date = datetime(int(year), int(month), int(day))
    work_dates_set = set(create_date_range(*get_current_work_period()))

    return new_date, work_dates_set


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
    dates_range_set = set(create_date_range(start_date, end_date))
    work_dates_set = set(create_date_range(*get_current_work_period()))

    return dates_range_set, work_dates_set


def format_period(start_date: datetime, end_date: datetime):
    if start_date.year == end_date.year:
        start_text = format_date(start_date)

    else:
        start_text = format_date(start_date, is_same_year=False)

    end_text = format_date(end_date)

    return start_text, end_text


def format_date(date: datetime, is_same_year: bool = True) -> str:
    day = date.strftime('%d')
    month = english_to_russians_months[date.strftime('%B')]

    if is_same_year:
        return f'"{day}" {month}'

    else:
        year = date.year
        return f'"{day}" {month} {year} г.'


def get_day_month_year(date: datetime) -> Tuple[str, str, int]:
    day = date.strftime('%d')
    month = english_to_russians_months[date.strftime('%B')]
    year = date.year

    return day, month, year


def generate_dates_text(data: Dict[str, Any]) -> Tuple[str, str, List[datetime]]:
    start_day, start_month, start_year = get_day_month_year(data['start_day_dates'])
    formatted_dates = [data['start_day_dates']]

    selected_days = f'{start_day} {start_month} {start_year} г.\n'
    formatted_days = f'"{start_day}" {start_month} {start_year} г. - (), '

    date_pattern = re.compile(r'^\d{1,2}\.\d{1,2}\.\d{4}$')

    for key in data.keys():
        if date_pattern.match(key):
            date = data[key]
            day, month, year = get_day_month_year(date)

            selected_days += f'{day} {month} {year} г.\n'
            formatted_days += f'"{day}" {month} {year} г. - (), '
            formatted_dates.append(data[key])

    formatted_days = formatted_days.rstrip(', ')
    return selected_days, formatted_days, formatted_dates


def generate_absence_reason_full_desc(start_date: datetime, end_date: datetime, min_end_date: datetime,
                                      absence_reason_desc) -> str:
    if start_date == min_end_date:
        absence_reason_full_desc = absence_reason_desc + f' {format_date(start_date, is_same_year=False)}|'
        absence_after_work_period = False

    elif start_date < min_end_date:
        if start_date.year == min_end_date.year:
            start_period_text = format_date(start_date)

        else:
            start_period_text = format_date(start_date, is_same_year=False)

        absence_reason_full_desc = absence_reason_desc + f' с {start_period_text}'
        end_period_text = format_date(min_end_date, is_same_year=False)
        absence_reason_full_desc += f' по {end_period_text}|'
        absence_after_work_period = False

    else:
        absence_reason_full_desc = f'{AbsenceReasons.NoReason.desc}|'
        absence_after_work_period = True

    after_period_start_date = min_end_date + timedelta(days=1)

    while after_period_start_date <= end_date:
        if after_period_start_date == end_date:
            absence_reason_full_desc += absence_reason_desc + f' {format_date(after_period_start_date, 
                                                                              is_same_year=False)}|'
            break

        after_period_end_date = after_period_start_date + timedelta(days=6)
        if (start_date not in set(create_date_range(after_period_start_date, after_period_end_date))
                and absence_after_work_period):
            absence_reason_full_desc += f'{AbsenceReasons.NoReason.desc}|'
            after_period_start_date += timedelta(days=7)
            continue

        absence_after_work_period = False

        if after_period_end_date < end_date:
            if start_date in set(create_date_range(after_period_start_date, after_period_end_date)):
                if start_date.year == after_period_end_date.year:
                    after_period_start_text = format_date(start_date)

                else:
                    after_period_start_text = format_date(start_date, is_same_year=False)

            else:
                if after_period_start_date.year == after_period_end_date.year:
                    after_period_start_text = format_date(after_period_start_date)

                else:
                    after_period_start_text = format_date(after_period_start_date, is_same_year=False)

            absence_reason_full_desc += absence_reason_desc + f' с {after_period_start_text}'
            after_period_end_text = format_date(after_period_end_date, is_same_year=False)
            absence_reason_full_desc += f' по {after_period_end_text}|'

        else:
            if start_date in set(create_date_range(after_period_start_date, end_date)):
                if start_date.year == end_date.year:
                    after_period_start_text = format_date(start_date)

                else:
                    after_period_start_text = format_date(start_date, is_same_year=False)

            else:
                if after_period_start_date.year == end_date.year:
                    after_period_start_text = format_date(after_period_start_date)

                else:
                    after_period_start_text = format_date(after_period_start_date, is_same_year=False)

            absence_reason_full_desc += absence_reason_desc + f' с {after_period_start_text}'
            after_period_end_text = format_date(end_date, is_same_year=False)
            absence_reason_full_desc += f' по {after_period_end_text}|'
            break

        after_period_start_date += timedelta(days=7)

    return absence_reason_full_desc.rstrip('|')


def get_week_start(date: datetime) -> datetime:
    offset = (date.weekday() - 3) % 7
    return date - timedelta(days=offset)


def parse_absence_dates_and_periods(absence_dates_and_periods_str: str,
                                    formatted_dates_and_periods: List[Any]):
    min_end_date = max(set(create_date_range(*get_current_work_period())))
    dates_and_periods = []

    for absence_str_parts, formatted_item in zip(absence_dates_and_periods_str.split(', '),
                                                 formatted_dates_and_periods):
        if '-' in absence_str_parts:
            dates_and_periods.append((absence_str_parts.split('-')[1].strip(), formatted_item))
        else:
            dates_and_periods.append((absence_str_parts.split(' с ')[0].strip(), formatted_item))

    dates_and_periods.sort(key=lambda x: x[1] if isinstance(x[1], datetime) else x[1][1])

    current_week_start = None
    week_absences = []
    result_string = ''

    for date_or_period in dates_and_periods:
        if isinstance(date_or_period[1], tuple):
            start_date, end_date = date_or_period[1]
        else:
            start_date = date_or_period[1]
            end_date = start_date

        if current_week_start is None or get_week_start(start_date) != current_week_start:
            if week_absences:
                result_string += ", ".join(week_absences) + "|"
                week_absences = []

            current_week_start = get_week_start(start_date)

        if isinstance(date_or_period[1], tuple):
            absence_reason_full_desc = generate_absence_reason_full_desc(start_date, end_date,
                                                                         min_end_date if end_date >= min_end_date else
                                                                         end_date,
                                                                         date_or_period[0])

        else:
            absence_reason_full_desc = f'{format_date(date_or_period[1], is_same_year=False)} - {date_or_period[0]}'

        week_absences.append(absence_reason_full_desc)

    if week_absences:
        result_string += ", ".join(week_absences) + "|"

    print(result_string.rstrip('|'))

    # return result_string.rstrip('|')
        #     if end_date < min_end_date:
        #         absence_reason_full_desc = generate_absence_reason_full_desc(start_date, end_date,
        #                                                                      end_date, date_or_period[0])
        #     else:
        #         absence_reason_full_desc = generate_absence_reason_full_desc(start_date, end_date,
        #                                                                      min_end_date, date_or_period[0])
        #
        #     print(absence_reason_full_desc)
        #
        # else:
        #     absence_reason_full_desc = f'{format_date(date_or_period[1], is_same_year=False)} - {date_or_period[0]}'
        #     print(absence_reason_full_desc)

    # if '-' in absence_str_parts:
    #     print(absence_str_parts.split('-')[1].strip(), formatted_item)
    # else:
    #     start_date, end_date = formatted_item
    #     print(absence_str_parts.split(' с ')[0].strip(), start_date, end_date)
#
#     result_parts = []
#     for absence_str_parts in absence_dates_and_periods_str.split(', '):
#         if ' с ' in absence_str_parts:
#             period = absence_str_parts.split(' с ')[1]
#             start_date, end_date = parse_date_period(period)
#
#         else:
#             start_date = end_date = parse_single_date(absence_str_parts.split('-')[0])
#
#         current_part = ''
#         if start_date <= max(work_dates_set):
#             period_range = create_date_range(start_date, min(end_date, max(work_dates_set)))
#             if len(period_range) == 1:
#                 pass
#             else:
#                 current_part = absence_str_parts.split('-')[0] + ' с ' + period_range[]
#
#     absence_reason_full_desc = ''
#     for absence_str_parts in absence_dates_and_periods_str.split(', '):
#         if '-' in absence_str_parts:
#             for absence_str in absence_str_parts.split('-'):
#                 current_date = parse_single_date(absence_str[0])
#                 if current_date > max(work_dates_set):
#                     if max(work_dates_set) - current_date > timedelta(days=6):
#                         pass
#
#                 else:
#                     pass
#             print(parse_single_date([m.strip() for m in absence_str_parts.split('-')][0]))
#         else:
#             print(parse_date_period([m.strip() for m in absence_str_parts.split(' с ')][1]))


def generate_period_text(start_dates: List[datetime], end_dates: List[datetime],
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
                start_date_period = data['absence_periods'][0].strftime("%d.%m.%Y")
                end_date_period = data['absence_periods'][1].strftime("%d.%m.%Y")

                employee_info += f'{report_data_dict[key]}: {start_date_period} - {end_date_period}\n'

            if key == 'absence_dates':
                absence_dates = ''

                for index in range(len(value)):
                    if index != len(value) - 1:
                        absence_dates += f'{value[index].strftime("%d.%m.%Y")}, '

                    else:
                        absence_dates += f'{value[index].strftime("%d.%m.%Y")}'

                employee_info += f'\n{report_data_dict[key]}: {absence_dates}\n'

            if key != 'absence_periods' and key != 'absence_dates':
                employee_info += f'\n{report_data_dict[key]}: {value}\n'

    return employee_info
