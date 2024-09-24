from datetime import datetime

from aiogram import Router, F
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import StatesGroup, State
from aiogram.types import Message, ReplyKeyboardRemove, CallbackQuery

from tg_bot.functions import cleanup
from tg_bot.routers.main.main_handler import main_menu_handler
from tg_bot.routers.reports.backend import filling_out_report_backend
from tg_bot.routers.reports.backend.absence_reasons_enum import AbsenceReasons
from tg_bot.routers.reports.keyboard import generate_inline_kb_for_employees_list, \
    generate_calendar_inline_kb, generate_obtained_result_inline_kb, generate_absence_reason_inline_kb, \
    generate_cancel_inline_kb, generate_final_inline_kb, generate_period_or_dates_inline_kb, \
    generate_fill_manual_inline_kb
from tg_bot.security import user_access
from tg_bot.static.emojis import Emoji

filling_out_report_router = Router()

report_data_dict = {'actual_performance': '"Выполненные работы"',
                    'obtained_result': '"Полученный результат"', 'employee_id': '"ФИО"'}

months = {
    'January': 'января', 'February': 'февраля', 'March': 'марта',
    'April': 'апреля', 'May': 'мая', 'June': 'июня',
    'July': 'июля', 'August': 'августа', 'September': 'сентября',
    'October': 'октября', 'November': 'ноября', 'December': 'декабря'
}


class FillingOutReportStates(StatesGroup):
    enter_actual_performance = State()
    enter_document_name = State()
    enter_absence_reason_manual = State()


@filling_out_report_router.message(cleanup(F.text).lower() == 'заполнить отчет')
@user_access
async def filling_out_report_menu_handler(message: Message, state: FSMContext):
    response = await filling_out_report_backend.get_all_employees()
    if response.error:
        await message.answer(f'{str(Emoji.Error)} {response.message}')
    else:
        if not response.value:
            await message.answer(f'{str(Emoji.Warning)} В базе данных нет ни одного сотрудника')
        else:
            data = await state.get_data()

            employees_list_inline_kb = generate_inline_kb_for_employees_list(response.value)

            if 'change_name' in data:
                await message.answer(f'Смените сотрудника из списка:\n', reply_markup=employees_list_inline_kb)
            else:
                await message.answer(f'Выберите сотрудника в списке:\n', reply_markup=employees_list_inline_kb)


@filling_out_report_router.callback_query(F.data.split('_')[0] == 'employee')
async def filling_out_employee_report(callback: CallbackQuery, state: FSMContext):
    employee_id = int(callback.data.split('_')[1])
    response = await filling_out_report_backend.get_employee_by_id(employee_id)
    if response.error:
        await callback.message.answer(text=f'{str(Emoji.Error)} {response.message}')
    else:
        data = await state.get_data()

        if 'change_name' in data:
            await state.update_data(employee_id=employee_id)
            await get_final_result(callback.message, state)
        else:
            period_or_dates_inline_kb = generate_period_or_dates_inline_kb()

            await callback.message.answer(text=f'{str(Emoji.Point)} Выберите период, либо отдельные даты, когда '
                                               f'{response.value.full_name} отсутствовал(а) или нажмите "Пропустить":',
                                          reply_markup=period_or_dates_inline_kb)

            await state.update_data(employee_id=employee_id)


@filling_out_report_router.callback_query(F.data == 'choose_period')
async def choose_period_handler(callback: CallbackQuery, state: FSMContext):
    await state.update_data(choose_period='')

    data = await state.get_data()

    if 'employee_id' in data:
        response = await filling_out_report_backend.get_employee_by_id(data['employee_id'])
        if response.error:
            await callback.message.answer(text=f'{str(Emoji.Error)} {response.message}')
        else:

            today = datetime.today()
            calendar_markup = generate_calendar_inline_kb(today.year, today.month)

            await callback.message.answer(text=f'Заполнение отчета за {response.value.full_name}',
                                          reply_markup=ReplyKeyboardRemove())

            await callback.message.answer(text=f'{str(Emoji.CalendarEmoji)} '
                                               f'Выберите период отсутствия или нажмите "Пропустить":',
                                          reply_markup=calendar_markup)

    else:
        await filling_out_report_menu_handler(callback.message, state)


@filling_out_report_router.callback_query(F.data == 'choose_dates')
async def choose_dates_handler(callback: CallbackQuery, state: FSMContext):
    await state.update_data(choose_dates='')

    data = await state.get_data()

    if 'employee_id' in data:
        response = await filling_out_report_backend.get_employee_by_id(data['employee_id'])
        if response.error:
            await callback.message.answer(text=f'{str(Emoji.Error)} {response.message}')
        else:
            today = datetime.today()
            calendar_markup = generate_calendar_inline_kb(today.year, today.month, is_period=False)

            await callback.message.answer(text=f'Заполнение отчета за {response.value.full_name}',
                                          reply_markup=ReplyKeyboardRemove())

            await callback.message.answer(text=f'{str(Emoji.CalendarEmoji)} '
                                               f'Выберите даты отсутствия или нажмите "Пропустить":',
                                          reply_markup=calendar_markup)

    else:
        await filling_out_report_menu_handler(callback.message, state)


@filling_out_report_router.callback_query(F.data.split(':')[0] == 'day_period')
async def select_days_period(callback: CallbackQuery, state: FSMContext):
    year, month, day = map(int, callback.data.split(':')[1:])

    data = await state.get_data()

    if 'start_day_period' in data:
        end_date = datetime(int(year), int(month), int(day))
        await state.update_data(end_day_period=end_date)

        absence_reason_inline_kb = generate_absence_reason_inline_kb()
        await callback.message.answer(text=f'{str(Emoji.CheckMarkEmoji)} Выберите причину отсутствия: ',
                                      reply_markup=absence_reason_inline_kb)
    else:
        start_date = datetime(int(year), int(month), int(day))
        await state.update_data(start_day_period=start_date)


@filling_out_report_router.callback_query(F.data.split(':')[0] == 'day_dates')
async def select_days_dates(callback: CallbackQuery, state: FSMContext):
    year, month, day = map(int, callback.data.split(':')[1:])

    data = await state.get_data()

    if 'start_day_dates' in data:
        next_day = datetime(int(year), int(month), int(day))
        await state.update_data({str(day): next_day})

    else:
        start_date = datetime(int(year), int(month), int(day))
        await state.update_data(start_day_dates=start_date)

        calendar_markup = generate_calendar_inline_kb(year, month, is_period=False, first_date_selected=True)
        await callback.message.edit_reply_markup(reply_markup=calendar_markup)


@filling_out_report_router.callback_query(F.data.split(':')[0] == 'prev_month_period')
async def prev_month_handler(callback: CallbackQuery, state: FSMContext):
    year, month = map(int, callback.data.split(':')[1:])
    if month == 1:
        month = 12
        year -= 1
    else:
        month -= 1

    new_calendar_markup = generate_calendar_inline_kb(year, month)
    await callback.message.edit_reply_markup(reply_markup=new_calendar_markup)


@filling_out_report_router.callback_query(F.data.split(':')[0] == 'prev_month_dates')
async def prev_month_handler(callback: CallbackQuery, state: FSMContext):
    year, month = map(int, callback.data.split(':')[1:])
    if month == 1:
        month = 12
        year -= 1
    else:
        month -= 1

    new_calendar_markup = generate_calendar_inline_kb(year, month, is_period=False)
    await callback.message.edit_reply_markup(reply_markup=new_calendar_markup)


@filling_out_report_router.callback_query(F.data.split(':')[0] == 'next_month_period')
async def next_month_handler(callback: CallbackQuery, state: FSMContext):
    year, month = map(int, callback.data.split(':')[1:])
    if month == 12:
        month = 1
        year += 1
    else:
        month += 1

    new_calendar_markup = generate_calendar_inline_kb(year, month)
    await callback.message.edit_reply_markup(reply_markup=new_calendar_markup)


@filling_out_report_router.callback_query(F.data.split(':')[0] == 'next_month_dates')
async def next_month_handler(callback: CallbackQuery, state: FSMContext):
    year, month = map(int, callback.data.split(':')[1:])
    if month == 12:
        month = 1
        year += 1
    else:
        month += 1

    new_calendar_markup = generate_calendar_inline_kb(year, month, is_period=False)
    await callback.message.edit_reply_markup(reply_markup=new_calendar_markup)


@filling_out_report_router.callback_query(F.data == 'continue_filling_in')
async def continue_filling_in_handler(callback: CallbackQuery, state: FSMContext):
    fill_manual_inline_kb = generate_fill_manual_inline_kb()

    await callback.message.answer(text=f'Выберите "Заполнить вручную" или "Отмена":',
                                  reply_markup=fill_manual_inline_kb)


@filling_out_report_router.callback_query(F.data == 'cancel_all')
async def cancel_all_handler(callback: CallbackQuery, state: FSMContext):
    await main_menu_handler(callback.message, state)


@filling_out_report_router.callback_query(F.data == 'skip_absence')
async def skip_absence_handler(callback: CallbackQuery, state: FSMContext):
    cancel_inline_kb = generate_cancel_inline_kb()
    await callback.message.answer(text=f'{str(Emoji.Note)} Введите фактически выполненные работы за отчетный период:',
                                  reply_markup=cancel_inline_kb)
    await state.set_state(FillingOutReportStates.enter_actual_performance)


@filling_out_report_router.callback_query(F.data.split(':')[0] == 'absence_reason')
async def absence_reason_handler(callback: CallbackQuery, state: FSMContext):
    _, absence_reason = callback.data.split(':')
    data = await state.get_data()

    if 'employee_id' in data:
        if absence_reason == 'business_trip':
            absence_reason_desc = AbsenceReasons.BusinessTrip.desc
        elif absence_reason == 'vacation':
            absence_reason_desc = AbsenceReasons.Vacation.desc
        elif absence_reason == 'sickness':
            absence_reason_desc = AbsenceReasons.Sickness.desc
        elif absence_reason == 'fill_manual':
            absence_reason_desc = 'вручную'
            await absence_reason_manual_handler(callback.message, state)
        else:
            absence_reason_desc = AbsenceReasons.NoReason.desc

        if absence_reason_desc in [absence_reason.desc for absence_reason in list(AbsenceReasons)]:
            response = await filling_out_report_backend.update_employee_absence_reason_by_id(data['employee_id'],
                                                                                             absence_reason_desc)

            if response.error:
                await callback.message.answer(text=f'{str(Emoji.Error)} {response.message}')
                await main_menu_handler(callback.message, state)

            else:
                if absence_reason_desc == AbsenceReasons.NoReason.desc:
                    await skip_absence_handler(callback, state)

                else:
                    await callback.message.answer(text=f'{str(Emoji.Success)} {response.message}')
                    await main_menu_handler(callback.message, state)

    else:
        await filling_out_report_menu_handler(callback.message, state)


@user_access
async def absence_reason_manual_handler(message: Message, state: FSMContext):
    data = await state.get_data()

    if 'choose_dates' in data:
        start_date = data['start_day_dates']

        start_day = start_date.strftime("%d")
        month_english = start_date.strftime("%B")
        month_russian = months[month_english]

        year = start_date.year

        selected_days = f'{start_day} {month_russian} {year} г.\n'

        for key in data.keys():
            if key.isdigit():
                date = data[key]

                day = date.strftime("%d")
                month_english = date.strftime("%B")
                month_russian = months[month_english]

                year = date.year

                selected_days += f'{day} {month_russian} {year} г.\n'

        cancel_inline_kb = generate_cancel_inline_kb()

        await state.set_state(FillingOutReportStates.enter_absence_reason_manual)
        await message.answer(text=f'{str(Emoji.CalendarEmoji)} Вы выбрали следующие даты:\n'
                                  f'{selected_days}\n Введите информацию по этим датам:',
                             reply_markup=cancel_inline_kb)

    elif 'choose_period' in data:
        start_date = data['start_day_period']

        start_day = start_date.strftime("%d")
        start_month_english = start_date.strftime("%B")
        start_month_russian = months[start_month_english]
        start_year = start_date.year

        end_date = data['end_day_period']
        end_day = end_date.strftime("%d")
        end_month_english = end_date.strftime("%B")
        end_month_russian = months[end_month_english]
        end_year = end_date.year

        if start_date > end_date:
            selected_period = (f'{start_day} {start_month_russian} {start_year} г. - '
                               f'{end_day} {end_month_russian} {end_year} г.')
        elif start_date < end_date:
            selected_period = (f'{end_day} {end_month_russian} {end_year} г. - '
                               f'{start_day} {start_month_russian} {start_year} г.')
        else:
            selected_period = f'{start_day} {start_month_russian} {start_year} г.'

        cancel_inline_kb = generate_cancel_inline_kb()

        await state.set_state(FillingOutReportStates.enter_absence_reason_manual)
        await message.answer(text=f'{str(Emoji.CalendarEmoji)} Вы выбрали следующий период:\n'
                                  f'{selected_period}\n Введите информацию по этому периоду:',
                             reply_markup=cancel_inline_kb)


@filling_out_report_router.message(FillingOutReportStates.enter_absence_reason_manual)
@user_access
async def enter_absence_reason_manual_handler(message: Message, state: FSMContext):
    data = await state.get_data()

    if message.text and cleanup(message.text).lower() == 'отмена':
        await main_menu_handler(message, state)

    elif 'employee_id' in data:
        response = await filling_out_report_backend.update_employee_absence_reason_by_id(data['employee_id'],
                                                                                         message.text)
        if response.error:
            await message.answer(text=f'{str(Emoji.Error)} {response.message}')
            await main_menu_handler(message, state)

        else:
            await message.answer(text=f'{str(Emoji.Success)} {response.message}')
            await main_menu_handler(message, state)


@filling_out_report_router.message(FillingOutReportStates.enter_actual_performance)
@user_access
async def enter_actual_performance_handler(message: Message, state: FSMContext):
    if message.text and cleanup(message.text).lower() == 'отмена':
        await main_menu_handler(message, state)
    else:
        await state.update_data(actual_performance=message.text)

        obtained_result_kb = generate_obtained_result_inline_kb()
        await message.answer(text=f'{str(Emoji.Success)} Выберите полученный результат:\n',
                             reply_markup=obtained_result_kb)


@filling_out_report_router.callback_query(F.data.split(':')[0] == 'obtained_result')
async def obtained_result_handler(callback: CallbackQuery, state: FSMContext):
    _, obtained_result = callback.data.split(':')
    if obtained_result == 'working_materials':
        await state.update_data(obtained_result='Рабочие материалы')
        await get_final_result(callback.message, state)

    elif obtained_result == 'documents':
        cancel_inline_kb = generate_cancel_inline_kb()
        await callback.message.answer(text=f'{str(Emoji.EditText)} Введите название документа:',
                                      reply_markup=cancel_inline_kb)
        await state.set_state(FillingOutReportStates.enter_document_name)
    else:
        await state.update_data(obtained_result='')


@filling_out_report_router.message(FillingOutReportStates.enter_document_name)
@user_access
async def enter_document_name_handler(message: Message, state: FSMContext):
    if message.text and cleanup(message.text).lower() == 'отмена':
        await main_menu_handler(message, state)
    else:
        await state.update_data(obtained_result=f'Документ "{message.text}"')
        await get_final_result(message, state)


async def get_final_result(message: Message, state: FSMContext):
    data = await state.get_data()

    if 'employee_id' in data:
        response = await filling_out_report_backend.get_employee_by_id(data['employee_id'])

        if response.error:
            await message.answer(text=f'{str(Emoji.Error)} {response.message}')
        else:
            employee_name = response.value.full_name

            employee_info = ''

            for key, value in data.items():
                if key != 'employee_id' and key in report_data_dict.keys():
                    employee_info += f'{report_data_dict[key]}: {value}\n'

            final_inline_kb = generate_final_inline_kb()
            await message.answer(text=f'{str(Emoji.EmployeeEmoji)} Вы заполнили отчет за {employee_name}\n\n'
                                      f'{employee_info}', reply_markup=final_inline_kb)

    else:
        await message.answer(text=f'{str(Emoji.Error)} Вы не выбрали сотрудника!')
        await filling_out_report_menu_handler(message, state)


@filling_out_report_router.callback_query(F.data == 'save_data')
async def save_data_handler(callback: CallbackQuery, state: FSMContext):
    data = await state.get_data()
    if 'employee_id' in data:
        if {'actual_performance', 'obtained_result'}.issubset(set(data.keys())):
            response = await filling_out_report_backend.add_report_data(data['actual_performance'],
                                                                        data['obtained_result'],
                                                                        data['employee_id'])
            if response.error:
                await callback.message.answer(text=f'{str(Emoji.Error)} {response.message}')
                await filling_out_report_menu_handler(callback.message, state)
            else:
                await callback.message.answer(text=f'{str(Emoji.Success)} {response.message}')
                await main_menu_handler(callback.message, state)
        else:
            await callback.message.answer(text=f'{str(Emoji.Warning)} Информация не сохранилась, заполните еще раз!')
            await filling_out_report_menu_handler(callback.message, state)
    else:
        await callback.message.answer(text=f'{str(Emoji.Warning)} Вы не выбрали сотрудника!')
        await filling_out_report_menu_handler(callback.message, state)


@filling_out_report_router.callback_query(F.data == 'change_name')
async def change_name_handler(callback: CallbackQuery, state: FSMContext):
    await state.update_data(change_name=True)
    await filling_out_report_menu_handler(callback.message, state)
