from aiogram.types import BufferedInputFile

from tg_bot.routers.reports.backend.brosok_reporter import BrosokReporter


async def get_excel_report():
    bytes_output = await BrosokReporter().generate_report()
    excel_report = BufferedInputFile(bytes_output, filename='Отчет_по_работе.xls')

    return excel_report

