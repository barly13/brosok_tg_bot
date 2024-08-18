from aiogram.types import BufferedInputFile
from io import BytesIO

from tg_bot.routers.reports.backend.brosok_reporter import BrosokReporter


async def get_excel_report():
    output = BytesIO()
    workbook = await BrosokReporter().generate_xls_staff_state_report()
    workbook.save(output)
    excel_report = BufferedInputFile(output.getvalue(), filename='Отчет_по_работе.xls')

    return excel_report
