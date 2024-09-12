from database.models.ReportData import ReportData
from database.models.Employee import Employee
from tg_bot.routers.reports.backend import get_report_backend
from tg_bot.routers.reports.backend.absence_reasons_enum import AbsenceReasons
from tg_bot.routers.reports.backend.filling_out_report_backend import get_employee_by_id
from tg_bot.settings import bot, users_dict_ids

from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger

from tg_bot.static.emojis import Emoji

executor = {
    'apscheduler.executors.default': {
        'class': 'apscheduler.executors.asyncio:AsyncIOExecutor',
        'max_workers': '1'
    }
}

scheduler = AsyncIOScheduler(executor=executor)


async def delete_all_data():
    employee_id = 13
    employee_tg_id = users_dict_ids.get(employee_id)
    try:
        excel_report = await get_report_backend.get_excel_report()
        await bot.send_document(employee_tg_id, excel_report, caption='Отчет')
    except Exception as exp:
        print(f'Ошибка в формировании отчета перед удалением: {exp}')

    ReportData.delete_all_data()
    Employee.update_all_absence_reasons()


async def send_reminder_ro_all_employees():
    for employee_id, employee_tg_id in users_dict_ids.items():
        try:
            response = await get_employee_by_id(employee_id)
            await bot.send_message(
                chat_id=employee_tg_id,
                text=f'{str(Emoji.Waiting)} Уведомление: {response.value.full_name}, '
                     f'заполните данные для отчета!'
            )
        except Exception as e:
            print(f'Ошибка отправки уведомления {employee_id}: {e}')
            continue


async def check_if_data_filled(employee_id: int):
    response = await get_employee_by_id(employee_id)
    if (ReportData.is_report_data_has_not_employee(employee_id)
            and response.value.absence_reason == AbsenceReasons.NoReason.num):
        return False

    return True


async def send_reminder_to_incomplete_employees():
    for employee_id, employee_tg_id in users_dict_ids.items():
        try:
            is_data_filled = await check_if_data_filled(employee_id)
            if not is_data_filled:
                response = await get_employee_by_id(employee_id)
                await bot.send_message(chat_id=employee_tg_id,
                                       text=f'{str(Emoji.Waiting)} Повторное уведомление: {response.value.full_name}, '
                                            f'срочно заполните данные!')
        except Exception as e:
            print(f'Ошибка отправки уведомления {employee_id}: {e}')
            continue


async def send_reminder_to_reporter():
    employee_id = 12
    employee_tg_id = users_dict_ids.get(employee_id)
    response = await get_employee_by_id(employee_id)
    await bot.send_message(chat_id=employee_tg_id, text=f'{str(Emoji.Waiting)} '
                                                        f'Уведомление: {response.value.full_name}, сформируйте отчет!')


async def init_jobs():
    if not scheduler.running:
        scheduler.remove_all_jobs()

        # 1. Удаление всех данных в четверг в 00:00
        scheduler.add_job(delete_all_data, trigger=CronTrigger(day_of_week='thu', hour=14, minute=21),
                          misfire_grace_time=60)

        # 2. Отправка всем уведомлений во вторник в 16:45
        scheduler.add_job(send_reminder_ro_all_employees, trigger=CronTrigger(day_of_week='tue', hour=16, minute=45),
                          misfire_grace_time=60)

        # 3. Повторное уведомление во вторник в 18:00 тем, кто не заполнил данные
        scheduler.add_job(send_reminder_to_incomplete_employees,
                          trigger=CronTrigger(day_of_week='tue', hour=18, minute=0),
                          misfire_grace_time=60)

        # 4. Уведомление сотруднику, который составляет отчет, в среду в 14:00
        scheduler.add_job(send_reminder_to_reporter, trigger=CronTrigger(day_of_week='wed', hour=16, minute=15),
                          misfire_grace_time=60)

        scheduler.start()
