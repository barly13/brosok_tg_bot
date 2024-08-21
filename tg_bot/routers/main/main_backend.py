from database.models.ReportData import ReportData
from database.models.Employee import Employee
from tg_bot.routers.reports.backend.filling_out_report_backend import get_employee_by_id
from tg_bot.settings import bot, user_test_dict_ids

from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger

from tg_bot.static.emojis import Emoji

future = None

executor = {
    'apscheduler.executors.default': {
        'class': 'apscheduler.executors.asyncio:AsyncIOExecutor',
        'max_workers': '1'
    }
}

scheduler = AsyncIOScheduler(executor=executor)


async def delete_all_data():
    ReportData.delete_all_data()
    Employee.update_all_absence_reasons()


async def send_reminder_ro_all_employees():
    for employee_id, employee_tg_id in user_test_dict_ids.items():
        response = await get_employee_by_id(employee_id)
        await bot.send_message(chat_id=employee_tg_id,
                               text=f'{str(Emoji.Waiting)} Уведомление: {response.value.full_name}, '
                                    f'заполните данные для отчета!')


async def check_if_data_filled(employee_id: int):
    if ReportData.is_report_data_has_not_employee(employee_id):
        return False

    return True


async def send_reminder_to_incomplete_employees():
    for employee_id, employee_tg_id in user_test_dict_ids.items():
        is_data_filled = await check_if_data_filled(employee_id)
        if not is_data_filled:
            response = await get_employee_by_id(employee_id)
            await bot.send_message(chat_id=employee_tg_id,
                                   text=f'{str(Emoji.Waiting)} Повторное уведомление: {response.value.full_name}, '
                                        f'срочно заполните данные!')


async def send_reminder_to_reporter():
    employee_id = 13    # 12
    employee_tg_id = user_test_dict_ids.get(employee_id)
    response = await get_employee_by_id(employee_id)
    await bot.send_message(chat_id=employee_tg_id, text=f'{str(Emoji.Waiting)} '
                                                        f'Уведомление: {response.value.full_name}, сформируйте отчет!')


async def init_jobs():
    if not scheduler.running:
        scheduler.remove_all_jobs()

        # 1. Удаление всех данных в четверг в 00:00
        scheduler.add_job(delete_all_data, trigger=CronTrigger(day_of_week='thu', hour=0, minute=0))

        # 2. Отправка всем уведомлений во вторник в 16:45
        scheduler.add_job(send_reminder_ro_all_employees, trigger=CronTrigger(day_of_week='tue', hour=16, minute=45))

        # 3. Повторное уведомление во вторник в 18:00 тем, кто не заполнил данные
        scheduler.add_job(send_reminder_to_incomplete_employees,
                          trigger=CronTrigger(day_of_week='tue', hour=18, minute=0))

        # 4. Уведомление сотруднику, который составляет отчет, в среду в 14:00
        scheduler.add_job(send_reminder_to_reporter, trigger=CronTrigger(day_of_week='wed', hour=14, minute=0))

        scheduler.start()


