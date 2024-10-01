from aiogram.types import CallbackQuery, Message

from database.models.Employee import Employee
from database.models.ReportData import ReportData
from response import Response
from datetime import datetime, timedelta
from typing import List, Tuple, Dict


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


# async def update_absence_period_or_dates_by_id(employee_id: int, absence_period_or_dates: Dict[str, str]) -> Response:
#     # dict to json
#     if Employee.update(object_id=employee_id, absence_period_or_dates=absence_period_or_dates):
#         return Response(message='Даты или период отсутствия записаны')
#
#     return Response(message='Не удалось обновить даты или период отсутствия', error=True)


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
