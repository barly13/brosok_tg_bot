from database.models.ReportData import ReportData
from database.models.Employee import Employee
from tg_bot.routers.reports.backend import get_report_backend
from tg_bot.routers.reports.backend.absence_reasons_enum import AbsenceReasons
from tg_bot.routers.reports.backend.filling_out_report_backend import get_employee_by_id, \
    get_earlier_absence_data_dict_from_desc, create_date_range, get_current_work_period
from tg_bot.settings import BOT, USERS_DICT_IDS

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
    employee_tg_id = USERS_DICT_IDS.get(employee_id)
    try:
        excel_report = await get_report_backend.get_excel_report()
        await BOT.send_document(employee_tg_id, excel_report, caption='Отчет')
    except Exception as exp:
        print(f'Ошибка в формировании отчета перед удалением: {exp}')

    ReportData.delete_all_data()
    Employee.update_all_absence_reasons()


def check_absence_reason(absence_reason: str) -> bool:
    if absence_reason.split('|')[0] in [absence_reason.desc for absence_reason in list(AbsenceReasons)]:
        return False

    work_range_set = set(create_date_range(*get_current_work_period()))
    dates_and_periods = tuple(get_earlier_absence_data_dict_from_desc(absence_reason).values())
    dates_and_periods_set = set()

    for date_or_period in dates_and_periods:
        if isinstance(date_or_period, list):
            period = create_date_range(date_or_period[0], date_or_period[1])
            for current_date in period:
                dates_and_periods_set.add(current_date)

        else:
            dates_and_periods_set.add(date_or_period)

    if dates_and_periods_set == work_range_set or work_range_set.issubset(dates_and_periods_set):
        return False

    return True


async def send_reminder_ro_all_employees():
    for employee_id, employee_tg_id in USERS_DICT_IDS.items():
        try:
            response = await get_employee_by_id(employee_id)
            if check_absence_reason(response.value.absence_reason):
                await BOT.send_message(
                    chat_id=employee_tg_id,
                    text=f'{str(Emoji.FourAndHalfPM)} Уведомление: {response.value.full_name}, '
                         f'заполните данные для отчета!'
                )
        except Exception as e:
            print(f'Ошибка отправки уведомления {employee_id}: {e}')
            continue


async def check_if_data_filled(employee_id: int):
    if ReportData.is_report_data_has_not_employee(employee_id):
        return False

    return True


async def send_reminder_to_incomplete_employees():
    for employee_id, employee_tg_id in USERS_DICT_IDS.items():
        try:
            is_data_filled = await check_if_data_filled(employee_id)
            response = await get_employee_by_id(employee_id)
            if check_absence_reason(response.value.absence_reason) and not is_data_filled:
                await BOT.send_message(chat_id=employee_tg_id,
                                       text=f'{str(Emoji.SixPM)} Повторное уведомление: {response.value.full_name}, '
                                            f'срочно заполните данные!')
        except Exception as e:
            print(f'Ошибка отправки уведомления {employee_id}: {e}')
            continue


async def send_reminder_to_reporter():
    employee_id = 12
    employee_tg_id = USERS_DICT_IDS.get(employee_id)
    response = await get_employee_by_id(employee_id)
    await BOT.send_message(chat_id=employee_tg_id, text=f'{str(Emoji.TwoPM)} '
                                                        f'Уведомление: {response.value.full_name}, сформируйте отчет!')


async def init_jobs():
    if not scheduler.running:
        scheduler.remove_all_jobs()

        # 1. Удаление всех данных в четверг в 00:00
        scheduler.add_job(delete_all_data, trigger=CronTrigger(day_of_week='thu', hour=22, minute=40),
                          misfire_grace_time=60)

        # 2. Отправка всем уведомлений во вторник в 16:30
        scheduler.add_job(send_reminder_ro_all_employees, trigger=CronTrigger(day_of_week='thu', hour=23, minute=55),
                          misfire_grace_time=60)

        # 3. Повторное уведомление во вторник в 18:00 тем, кто не заполнил данные
        scheduler.add_job(send_reminder_to_incomplete_employees,
                          trigger=CronTrigger(day_of_week='wed', hour=23, minute=3),
                          misfire_grace_time=60)

        # 4. Уведомление сотруднику, который составляет отчет, в среду в 14:00
        scheduler.add_job(send_reminder_to_reporter, trigger=CronTrigger(day_of_week='wed', hour=14, minute=0),
                          misfire_grace_time=60)

        scheduler.start()
