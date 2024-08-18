from database.models.Employee import Employee
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

