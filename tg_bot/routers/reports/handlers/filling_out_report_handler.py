from datetime import datetime

from aiogram import Router, F
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import StatesGroup, State
from aiogram.types import Message, ReplyKeyboardRemove, CallbackQuery

from tg_bot.functions import cleanup
from tg_bot.routers.main.main_handler import main_menu_handler
from tg_bot.routers.reports.backend import filling_out_report_backend
from tg_bot.routers.reports.backend.absence_reasons_enum import AbsenceReasons
from tg_bot.routers.reports.backend.filling_out_report_backend import update_employee_absence_reason_by_id
from tg_bot.routers.reports.keyboard import generate_inline_kb_for_employees_list, \
    generate_calendar_inline_kb, generate_obtained_result_inline_kb, generate_absence_reason_inline_kb, \
    generate_cancel_inline_kb, generate_note_inline_kb, generate_final_inline_kb, generate_period_or_dates_inline_kb
from tg_bot.security import user_access
from tg_bot.static.emojis import Emoji

filling_out_report_router = Router()

report_data_dict = {'actual_performance': '"Выполненные работы"',
                    'obtained_result': '"Полученный результат"', 'employee_id': '"ФИО"'}


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


@filling_out_report_router.callback_query(F.data.split(':')[0] == 'day')
async def select_date(callback: CallbackQuery, state: FSMContext):
    year, month, day = map(int, callback.data.split(':')[1:])

    data = await state.get_data()

    if 'start_date' in data:
        end_date = datetime(int(year), int(month), int(day))
        await state.update_data(end_date=end_date)

        absence_reason_inline_kb = generate_absence_reason_inline_kb()
        await callback.message.answer(text=f'{str(Emoji.CheckMarkEmoji)} Выберите причину отсутствия: ',
                                      reply_markup=absence_reason_inline_kb)
    else:
        start_date = datetime(int(year), int(month), int(day))
        await state.update_data(start_date=start_date)


@filling_out_report_router.callback_query(F.data.split(':')[0] == 'prev_month')
async def prev_month_handler(callback: CallbackQuery, state: FSMContext):
    year, month = map(int, callback.data.split(':')[1:])
    if month == 1:
        month = 12
        year -= 1
    else:
        month -= 1

    new_calendar_markup = generate_calendar_inline_kb(year, month)
    await callback.message.edit_reply_markup(reply_markup=new_calendar_markup)


@filling_out_report_router.callback_query(F.data.split(':')[0] == 'next_month')
async def next_month_handler(callback: CallbackQuery, state: FSMContext):
    year, month = map(int, callback.data.split(':')[1:])
    if month == 12:
        month = 1
        year += 1
    else:
        month += 1

    new_calendar_markup = generate_calendar_inline_kb(year, month)
    await callback.message.edit_reply_markup(reply_markup=new_calendar_markup)


@filling_out_report_router.callback_query(F.data == 'cancel_all')
async def cancel_all_handler(callback: CallbackQuery, state: FSMContext):
    await main_menu_handler(callback.message, state)


@filling_out_report_router.callback_query(F.data == 'skip_absence')
async def skip_absence_handler(callback: CallbackQuery, state: FSMContext):
    cancel_inline_kb = generate_cancel_inline_kb()
    await callback.message.answer(text=f'{str(Emoji.Note)} Введите фактически выполненные работы за отчетный период:',
                                  reply_markup=cancel_inline_kb)
    await state.set_state(FillingOutReportStates.enter_actual_performance)


# @filling_out_report_router.callback_query(F.data.split('__')[0] == 'absence_reason')
# async def filling_out_employee_report(callback: CallbackQuery, state: FSMContext):
#     absence_reason_num = int(callback.data.split('__')[1])
#     data = await state.get_data()
#     if 'employee_id' in data:
#         response = await update_employee_absence_reason_by_id(data['employee_id'], absence_reason_num)
#         if response.error:
#             await bot.send_message(chat_id=callback.message.chat.id, text=f'{str(Emoji.Error)} {response.message}')
#         else:
#             if absence_reason_num == AbsenceReasons.NoReason.num:
#                 await returning_employee_menu_handler(callback.message, state)
#             else:
#                 markup = ReplyKeyboardMarkup(keyboard=fill_out_report_kb, resize_keyboard=True)
#                 await bot.send_message(chat_id=callback.message.chat.id, text=f'{str(Emoji.Success)} {response.message}',
#                                        reply_markup=markup)
#                 await state.clear()
#     else:
#         markup = ReplyKeyboardMarkup(keyboard=fill_out_report_kb, resize_keyboard=True)
#         await bot.send_message(chat_id=callback.message.chat.id, text='Составление отчета', reply_markup=markup)
#         await state.clear()


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
            await state.set_state(FillingOutReportStates.enter_absence_reason_manual)
        else:
            absence_reason_desc = AbsenceReasons.NoReason.desc

        response = await update_employee_absence_reason_by_id(data['employee_id'], absence_reason_desc)

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


@filling_out_report_router.message(FillingOutReportStates.enter_actual_performance)
@user_access
async def filling_out_actual_performance(message: Message, state: FSMContext):
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
async def document_name_handler(message: Message, state: FSMContext):
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
    await main_menu_handler(callback.message, state)


@filling_out_report_router.callback_query(F.data == 'change_name')
async def change_name_handler(callback: CallbackQuery, state: FSMContext):
    await state.update_data(change_name=True)
    await filling_out_report_menu_handler(callback.message, state)