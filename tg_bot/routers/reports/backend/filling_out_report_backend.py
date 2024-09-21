from database.models.Employee import Employee
from database.models.ReportData import ReportData
from response import Response


async def get_all_employees():
    try:
        return Response(value=Employee.get_all())
    except Exception as exp:
        return Response(message=f'Не удалось получить сотрудников для составление отчета: {exp}', error=True)


async def get_employee_by_id(id: int):
    try:
        return Response(value=Employee.get_by_id(id))
    except Exception as exp:
        return Response(message=f'Не удалось получить данные о сотруднике: {exp}', error=True)


async def update_employee_absence_reason_by_id(id: int, absence_reason: str):
    if Employee.update(object_id=id, absence_reason=absence_reason):
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
