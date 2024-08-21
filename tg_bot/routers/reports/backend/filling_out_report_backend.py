from database.models.Employee import Employee
from database.models.ReportData import ReportData
from response import Response


async def get_all_employees():
    try:
        return Response(value=Employee.get_all())
    except Exception:
        return Response(message='Не удалось получить сотрудников для составление отчета', error=True)


async def get_employee_by_id(id: int):
    try:
        return Response(value=Employee.get_by_id(id))
    except Exception:
        return Response(message='Не удалось получить данные о сотруднике', error=True)


async def update_employee_absence_reason_by_id(id: int, absence_reason: int):
    if Employee.update(object_id=id, absence_reason=absence_reason):
        return Response(message='Причина отсутствия записана')

    return Response(message='Не удалось обновить причину отсутствия сотрудника', error=True)


async def get_all_report_data():
    try:
        return Response(value=ReportData.get_all())
    except Exception:
        return Response(message='Не удалось получить данные для отчета', error=True)


async def add_report_data(work_name: str, actual_performance: str, obtained_result: str, employee_id: int,
                          work_plan: str, note: str = ''):
    try:
        ReportData.create(
            work_name=work_name,
            actual_performance=actual_performance,
            obtained_result=obtained_result,
            employee_id=employee_id,
            work_plan=work_plan,
            note=note
        )
        return Response(message='Запись в отчет успешно создана')
    except Exception:
        return Response(message='Не удалось сохранить данные для отчета', error=True)