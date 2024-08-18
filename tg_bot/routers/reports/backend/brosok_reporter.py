import os
import xlwt

from database.models.Employee import Employee


class BrosokReporter:
    def __init__(self):
        self.workbook = xlwt.Workbook()

        self.center_alignment_style = xlwt.easyxf("align: horiz center, vert center; font: height 220;")
        self.header_row_style = xlwt.easyxf('pattern: pattern solid, fore_colour light_green;'
                                            'font: bold on, height 220;'
                                            'align: horiz center, vert center;')

        self.staff_state_columns = [
            {'header': '№ п/п', 'data_func': lambda data: data.id},
            {'header': 'Должность', 'data_func': lambda data: data.position},
            {'header': 'ФИО сотрудников', 'data_func': lambda data: data.full_name},
            {'header': 'Ставка по бюджету проекта', 'data_func': lambda data: data.working_rate},
            {'header': 'Статус', 'data_func': lambda data: 'Работа с 30 мая'}
        ]

    @staticmethod
    def __set_column_width(worksheet, column_index, value):
        column_width = len(str(value)) * 300
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

    async def generate_xls_staff_state_report(self):
        try:
            worksheet = self.workbook.add_sheet('Состояние кадрового обеспечения')

            list_of_employees = Employee.get_all()

            self.__write_xls_header_row(worksheet, self.staff_state_columns)

            for row_index, employee in enumerate(list_of_employees):
                self.__write_xls_data_row(worksheet, self.staff_state_columns, row_index + 1, employee)

            return self.workbook

        except Exception:
            return None

