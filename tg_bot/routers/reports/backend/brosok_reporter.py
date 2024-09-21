import os
import xlwt
from io import BytesIO
from datetime import datetime, timedelta
import locale

from database.models.Employee import Employee
from database.models.ReportData import ReportData
from tg_bot.routers.reports.backend.absence_reasons_enum import AbsenceReasons


class BrosokReporter:
    def __init__(self):
        self.workbook = xlwt.Workbook()
        self.bytes_output = BytesIO()
        self.reporting_week = [3, 4, 5, 6, 0, 1, 2]
        self.months_translate = {
            'January': 'января', 'February': 'февраля', 'March': 'марта', 'April': 'апреля',
            'May': 'мая', 'June': 'июня', 'July': 'июля', 'August': 'августа',
            'September': 'сентября', 'October': 'октября', 'November': 'ноября', 'December': 'декабря'
        }

        self.center_alignment_style = xlwt.easyxf("align: horiz center, vert center, wrap on; font: height 220;")
        self.header_row_style = xlwt.easyxf('pattern: pattern solid, fore_colour light_green;'
                                            'font: bold on, height 220;'
                                            'align: horiz center, vert center, wrap on;')

        self.staff_state_columns = [
            {'header': '№ п/п', 'data_func': lambda data: data.id},
            {'header': 'Должность', 'data_func': lambda data: data.position},
            {'header': 'ФИО сотрудников', 'data_func': lambda data: data.full_name},
            {'header': 'Ставка по бюджету проекта', 'data_func': lambda data: data.working_rate},
            {'header': 'Статус', 'data_func': lambda data: self.__get_status(data.absence_reason)}
        ]

        self.scientific_research_work_columns = [
            {'header': 'ФИО сотрудника', 'data_func': lambda data: Employee.get_by_id(data.employee_id).full_name},
            {'header': 'Фактически выполненные работы за отчетный период', 'data_func':
                lambda data: data.actual_performance},
            {'header': 'Полученный результат (вид отчетности)', 'data_func': lambda data: data.obtained_result},
        ]

    @staticmethod
    def __set_column_width(worksheet, column_index, value):
        min_width, max_width = 3000, 10000
        column_width = len(str(value)) * 256
        column_width = max(min_width, min(column_width, max_width))

        if worksheet.col(column_index).width < column_width:
            worksheet.col(column_index).width = column_width

    def __write_xls_header_row(self, worksheet, columns):
        for column_index, column_info in enumerate(columns):
            column_name = column_info['header']
            worksheet.write(0, column_index, column_name, self.header_row_style)
            self.__set_column_width(worksheet, column_index, column_name)

    def __write_xls_data_row(self, worksheet, columns, row_index, data):
        for column_index, column_info in enumerate(columns):
            value = column_info['data_func'](data)
            worksheet.write(row_index, column_index, value, self.center_alignment_style)
            self.__set_column_width(worksheet, column_index, value)

    async def generate_report(self):
        self.__generate_xls_staff_state_report()
        self.__generate_xls_scientific_research_work_report()
        self.workbook.save(self.bytes_output)

        return self.bytes_output.getvalue()

    def __get_status(self, absence_reason_desc: str):
        if absence_reason_desc in [absence_reason.desc for absence_reason in list(AbsenceReasons)]:

            weekday = datetime.today().weekday()
            index = self.reporting_week.index(weekday)

            start_week = datetime.today() - timedelta(days=index)
            end_week = datetime.today() + timedelta(days=len(self.reporting_week) - 1 - index)

            start_month_en = start_week.strftime("%B")
            end_month_en = end_week.strftime("%B")

            start_month_ru = self.months_translate[start_month_en]
            end_month_ru = self.months_translate[end_month_en]

            status = (f'{absence_reason_desc} с "{start_week.strftime("%d")}" {start_month_ru} '
                      f'по "{end_week.strftime("%d")}" {end_month_ru} {end_week.strftime("%Y")} г.')
        else:
            status = ''

        return status

    def __generate_xls_staff_state_report(self):
        try:
            worksheet = self.workbook.add_sheet('Состояние кадрового обеспечения')

            list_of_employees = Employee.get_all()

            self.__write_xls_header_row(worksheet, self.staff_state_columns)

            for row_index, employee in enumerate(list_of_employees):
                self.__write_xls_data_row(worksheet, self.staff_state_columns, row_index + 1, employee)

        except Exception as exp:
            print(f'Ошибка в заполнении отчета по состоянию кадрового обеспечения: {exp}')

    def __generate_xls_scientific_research_work_report(self):
        try:
            worksheet = self.workbook.add_sheet('Выполненные работы')

            list_of_report_data = ReportData.get_all()

            self.__write_xls_header_row(worksheet, self.scientific_research_work_columns)

            for row_index, report_data in enumerate(list_of_report_data):
                self.__write_xls_data_row(worksheet, self.scientific_research_work_columns, row_index + 1, report_data)

        except Exception as exp:
            print(f'Ошибка в заполнении отчета по выполненным работам: {exp}')
