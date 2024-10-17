import re
from datetime import datetime, date
from typing import Set, Dict, Any, Tuple, List

from aiogram import Router, F
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import StatesGroup, State
from aiogram.types import Message, CallbackQuery, ReplyKeyboardRemove

from database.models.Employee import Employee
from tg_bot.functions import cleanup
from tg_bot.routers.main.main_handler import main_menu_handler
from tg_bot.routers.reports.backend.absence_reasons_enum import AbsenceReasons
from tg_bot.routers.reports.backend.filling_out_report_backend import get_all_employees, get_employee_by_id, \
    create_date_range, get_current_work_period, update_employee_absence_reason_by_id, add_report_data, \
    get_date_sets, format_period, generate_dates_text, \
    generate_period_text, get_dates_range, get_final_employee_info, get_new_date_and_work_dates_set, \
    generate_absence_reason_full_desc, parse_absence_dates_and_periods, get_earlier_absence_data_dict_from_desc, \
    get_absence_reason_full_desc, update_periods_and_dates_set
from tg_bot.routers.reports.keyboard import generate_inline_kb_for_employees_list, \
    generate_calendar_inline_kb, generate_obtained_result_inline_kb, generate_absence_reason_inline_kb, \
    generate_cancel_inline_kb, generate_final_inline_kb, generate_period_or_dates_inline_kb, \
    generate_fill_manual_inline_kb, generate_re_select_period_inline_kb, \
    generate_earlier_filled_absence_reason_inline_kb
from tg_bot.security import user_access
from tg_bot.static.emojis import Emoji

filling_out_report_router = Router()


class FillingOutReportStates(StatesGroup):
    enter_actual_performance = State()
    enter_document_name = State()
    enter_absence_reason_manual = State()


@filling_out_report_router.callback_query(lambda callback: callback.data in ['fill_out_report', 'change_name'])
@user_access
async def filling_out_report_menu_handler(callback: CallbackQuery, state: FSMContext):
    response = await get_all_employees()

    if response.error:
        await callback.answer(f'{str(Emoji.Error)} {response.message}', show_alert=True)
        await main_menu_handler(callback.message, state)

    else:
        if not response.value:
            await callback.answer(f'{str(Emoji.Warning)} В базе данных нет ни одного сотрудника', show_alert=True)
            await main_menu_handler(callback.message, state)

        else:
            data = await state.get_data()

            employees_list_inline_kb = generate_inline_kb_for_employees_list(response.value)

            if 'employee_id' in data:
                await callback.message.edit_text(text=f'{str(Emoji.EmployeeEmoji)} Смените сотрудника из списка:',
                                                 reply_markup=employees_list_inline_kb)
            else:
                await callback.message.edit_text(text=f'{str(Emoji.EmployeeEmoji)} Выберите сотрудника в списке:',
                                                 reply_markup=employees_list_inline_kb)


@filling_out_report_router.callback_query(F.data.split('_')[0] == 'employee')
@user_access
async def filling_out_employee_report(callback: CallbackQuery, state: FSMContext):
    employee_id = int(callback.data.split('_')[1])
    response = await get_employee_by_id(employee_id)

    if response.error:
        await callback.answer(text=f'{str(Emoji.Error)} {response.message}', show_alert=True)
        await main_menu_handler(callback.message, state)
        return

    data = await state.get_data()

    if 'employee_id' in data:
        await state.update_data(employee_id=employee_id)
        await get_final_result(callback.message, state)
        return

    absence_reason_full_desc = response.value.absence_reason

    earlier_filled_absence_data = ''

    for absence_reason_desc in absence_reason_full_desc.split('|'):
        if absence_reason_desc not in [absence_reason.desc for absence_reason in list(AbsenceReasons)]:
            earlier_filled_absence_data += f'{absence_reason_desc}\n'

        elif absence_reason_desc in [absence_reason.desc for absence_reason in list(AbsenceReasons)
                                     if absence_reason != AbsenceReasons.NoReason]:
            start_text_period, end_text_period = format_period(*get_current_work_period())
            earlier_filled_absence_data += f'{absence_reason_desc} с {start_text_period} по {end_text_period}\n'

    if earlier_filled_absence_data:
        earlier_filled_absence_reason_inline_kb = generate_earlier_filled_absence_reason_inline_kb()

        await callback.message.edit_text(text=f'{str(Emoji.CheckMarkEmoji)} На текущий период существует '
                                              f'следующая информацию, когда {response.value.full_name} '
                                              f'отсутствовал:\n\n{earlier_filled_absence_data}',
                                         reply_markup=earlier_filled_absence_reason_inline_kb)

    else:
        period_or_dates_inline_kb = generate_period_or_dates_inline_kb()

        await callback.message.edit_text(text=f'{str(Emoji.CheckMarkEmoji)} Выберите период, либо '
                                              f'отдельные даты, когда {response.value.full_name} '
                                              f'отсутствовал(а), или нажмите "Пропустить":',
                                         reply_markup=period_or_dates_inline_kb)

    await state.update_data(employee_id=employee_id)


@filling_out_report_router.callback_query(F.data.split(':')[0] == 'earlier_filled')
@user_access
async def earlier_filled_absence_reason_handler(callback: CallbackQuery, state: FSMContext):
    earlier_filled_action = callback.data.split(':')[1]

    if earlier_filled_action == 'another':
        await state.update_data(another_absence_reason=True)

    if earlier_filled_action == 'more':
        await state.update_data(more_absence_reason=True)

    data = await state.get_data()

    if 'employee_id' not in data:
        await callback.answer(text=f'{str(Emoji.Warning)} Вы не выбрали сотрудника!', show_alert=True)
        await filling_out_report_menu_handler(callback, state)
        return

    response = await get_employee_by_id(data['employee_id'])

    if response.error:
        await callback.answer(text=f'{str(Emoji.Error)} {response.message}', show_alert=True)
        await main_menu_handler(callback.message, state)
        return

    period_or_dates_inline_kb = generate_period_or_dates_inline_kb()

    await callback.message.edit_text(text=f'{str(Emoji.CheckMarkEmoji)} Выберите период, либо '
                                          f'отдельные даты, когда {response.value.full_name} '
                                          f'отсутствовал(а), или нажмите "Пропустить":',
                                     reply_markup=period_or_dates_inline_kb)


async def check_earlier_absence_data(callback: CallbackQuery, state: FSMContext) -> bool:
    data = await state.get_data()

    if 'employee_id' not in data:
        await callback.answer(text=f'{str(Emoji.Warning)} Вы не выбрали сотрудника!', show_alert=True)
        await filling_out_report_menu_handler(callback, state)
        return True

    if 'more_absence_reason' in data:
        response = await get_employee_by_id(data['employee_id'])

        if response.error:
            await callback.answer(text=f'{str(Emoji.Error)} {response.message}', show_alert=True)
            await main_menu_handler(callback.message, state)
            return True

        earlier_absence_data_dict = get_earlier_absence_data_dict_from_desc(response.value.absence_reason)
        await state.update_data(earlier_absence_data_dict)

    return False


@filling_out_report_router.callback_query(F.data == 'choose_periods')
@user_access
async def choose_periods_handler(callback: CallbackQuery, state: FSMContext):
    await state.update_data(choose_periods=True)

    if await check_earlier_absence_data(callback, state):
        return

    data = await state.get_data()

    today = datetime.today().date()
    if {'start_day_dates', '1_period', '1_earlier_period', 'start_day_earlier_dates'}.intersection(data.keys()):
        calendar_markup = generate_calendar_inline_kb(today.year, today.month, first_date_or_period_selected=True)
        await callback.message.edit_text(text=f'{str(Emoji.PeriodEmoji)} '
                                              f'Выберите период отсутствия или нажмите "Продолжить":',
                                         reply_markup=calendar_markup)

    else:
        calendar_markup = generate_calendar_inline_kb(today.year, today.month)
        await callback.message.edit_text(text=f'{str(Emoji.PeriodEmoji)} '
                                              f'Выберите период отсутствия или нажмите "Пропустить":',
                                         reply_markup=calendar_markup)


@filling_out_report_router.callback_query(F.data == 'choose_dates')
@user_access
async def choose_dates_handler(callback: CallbackQuery, state: FSMContext):
    await state.update_data(choose_dates=True)

    if await check_earlier_absence_data(callback, state):
        return

    data = await state.get_data()

    today = datetime.today().date()
    if {'start_day_dates', '1_period', '1_earlier_period', 'start_day_earlier_dates'}.intersection(data.keys()):
        calendar_markup = generate_calendar_inline_kb(today.year, today.month, is_period=False,
                                                      first_date_or_period_selected=True)
        await callback.message.edit_text(text=f'{str(Emoji.CalendarEmoji)} '
                                              f'Выберите даты отсутствия или нажмите "Продолжить":',
                                         reply_markup=calendar_markup)
    else:
        calendar_markup = generate_calendar_inline_kb(today.year, today.month, is_period=False)
        await callback.message.edit_text(text=f'{str(Emoji.CalendarEmoji)} '
                                              f'Выберите даты отсутствия или нажмите "Пропустить":',
                                         reply_markup=calendar_markup)


@filling_out_report_router.callback_query(F.data == 'fill_more')
async def re_select_periods_or_dates_handler(callback: CallbackQuery, state: FSMContext):
    data = await state.get_data()

    if await check_fullness_of_period(callback, data):
        return

    re_select_inline_kb = generate_re_select_period_inline_kb()

    await callback.message.edit_text(text=f'{str(Emoji.CheckMarkEmoji)} Выберите (при необходимости) '
                                          f'еще период/даты отсутствия, либо, если вы уже выбрали '
                                          f'нужный период нажмите "Продолжить:"',
                                     reply_markup=re_select_inline_kb)


async def check_fullness_of_period(callback: CallbackQuery, data: Dict[str, Any]) -> bool:
    for key, value in data.items():
        if key.endswith('_period') and isinstance(value, list) and len(value) == 1:
            await callback.answer(text=f'{str(Emoji.Warning)} Вы не до конца заполнили период отсутствия. '
                                       f'Выберите дату окончания периода!',
                                  show_alert=True)

            return True

    return False


async def check_any_dates_or_period(callback: CallbackQuery, data: Dict[str, Any]) -> bool:
    if 'start_day_dates' not in data and '1_period' not in data:
        await callback.answer(text=f'{str(Emoji.Warning)} Вы не выбрали ни одного периода, ни одной даты! '
                                   f'Выберите даты или период отсутствия.',
                              show_alert=True)
        return True

    return False


async def check_date_is_before_work_dates(callback: CallbackQuery, new_date: date, work_dates_set: Set[date]) \
        -> bool:
    if new_date < min(work_dates_set):
        await callback.answer(text=f'{str(Emoji.Warning)} Вы выбрали дату до отчетного периода. Выберите дату, '
                                   f'находящуюся в отчетном периоде ({str(Emoji.CheckMarkEmoji)}) или после него!',
                              show_alert=True)
        return True

    return False


async def check_date_is_in_period(callback: CallbackQuery, new_date: date, data: Dict[str, Any]) -> bool:
    for key, value in data.items():
        if key.endswith('_period') and isinstance(value, list) and len(value) == 2:
            start_date, end_date = value
            if start_date <= new_date <= end_date:
                await callback.answer(text=f'{str(Emoji.Warning)} Вы выбрали дату, которая уже включена '
                                           f'в другой период. Выберите другую дату!',
                                      show_alert=True)
                return True

    return False


async def check_date_is_in_dates(callback: CallbackQuery, new_date: date, data: Dict[str, Any]) -> bool:
    for value in data.values():
        if isinstance(value, date) and value == new_date:
            await callback.answer(
                text=f'{str(Emoji.Warning)} Вы выбрали дату, которая уже включена в список выбранных дат. '
                     f'Выберите другую дату!',
                show_alert=True)
            return True

    return False


async def check_some_dates_is_in_period(callback: CallbackQuery, new_date: date, required_period: str,
                                        data: Dict[str, Any]) -> bool:
    selected_dates_set = set()

    for key, value in data.items():
        if key.endswith('_period') and isinstance(value, list) and len(value) == 2:
            selected_dates_set.add(value[0])
            selected_dates_set.add(value[1])

        elif isinstance(value, date):
            selected_dates_set.add(value)

    if selected_dates_set.intersection(set(create_date_range(data[required_period][0], new_date))):
        await callback.answer(f'{str(Emoji.Warning)} Вы выбрали период, в котором уже находятся другие даты. '
                              f'Выберите другой период или другие даты!',
                              show_alert=True)
        return True

    else:
        return False


@filling_out_report_router.callback_query(F.data.split(':')[0] == 'day_period')
@user_access
async def select_days_period(callback: CallbackQuery, state: FSMContext):
    new_date, work_dates_set = get_new_date_and_work_dates_set(callback.data)

    data = await state.get_data()

    pattern = re.compile(r'\d+_period$')

    period_count = sum(
        1 for key, value in data.items() if pattern.search(key) and isinstance(value, list) and len(value) == 2) + 1

    if f'{period_count}_period' in data:
        if await check_date_is_before_work_dates(callback, new_date, work_dates_set):
            return

        elif (await check_date_is_in_period(callback, new_date, data) or
              await check_date_is_in_dates(callback, new_date, data)):
            return

        if await check_some_dates_is_in_period(callback, new_date, f'{period_count}_period', data):
            await state.set_data({key: value for key, value in data.items() if key != f'{period_count}_period'})

            await re_select_periods_or_dates_handler(callback, state)
            return

        data[f'{period_count}_period'].append(new_date)

        await re_select_periods_or_dates_handler(callback, state)

    else:
        if await check_date_is_before_work_dates(callback, new_date, work_dates_set):
            return

        elif (await check_date_is_in_period(callback, new_date, data) or
              await check_date_is_in_dates(callback, new_date, data)):
            return

        await state.update_data({f'{period_count}_period': [new_date]})


@filling_out_report_router.callback_query(F.data.split(':')[0] == 'day_dates')
@user_access
async def select_days_dates(callback: CallbackQuery, state: FSMContext):
    new_date, work_dates_set = get_new_date_and_work_dates_set(callback.data)

    data = await state.get_data()

    if 'start_day_dates' in data:
        if await check_date_is_before_work_dates(callback, new_date, work_dates_set):
            return

        elif (await check_date_is_in_period(callback, new_date, data) or
              await check_date_is_in_dates(callback, new_date, data)):
            return

        await state.update_data({f'{new_date.day}.{new_date.month}.{new_date.year}': new_date})

    else:
        if await check_date_is_before_work_dates(callback, new_date, work_dates_set):
            return

        elif (await check_date_is_in_period(callback, new_date, data) or
              await check_date_is_in_dates(callback, new_date, data)):
            return

        await state.update_data(start_day_dates=new_date)

        calendar_markup = generate_calendar_inline_kb(new_date.year, new_date.month, is_period=False,
                                                      first_date_or_period_selected=True)

        try:
            await callback.message.edit_reply_markup(reply_markup=calendar_markup)
        except:
            pass


@filling_out_report_router.callback_query(F.data.split(':')[0] == 'prev_month_period')
@user_access
async def prev_month_handler(callback: CallbackQuery, state: FSMContext):
    year, month = map(int, callback.data.split(':')[1:])

    if month == 1:
        month = 12
        year -= 1

    else:
        month -= 1

    data = await state.get_data()

    if {'start_day_dates', '1_period', '1_earlier_period', 'start_day_earlier_dates'}.intersection(data.keys()):
        new_calendar_markup = generate_calendar_inline_kb(year, month, first_date_or_period_selected=True)

    else:
        new_calendar_markup = generate_calendar_inline_kb(year, month)

    await callback.message.edit_reply_markup(reply_markup=new_calendar_markup)


@filling_out_report_router.callback_query(F.data.split(':')[0] == 'prev_month_dates')
@user_access
async def prev_month_handler(callback: CallbackQuery, state: FSMContext):
    year, month = map(int, callback.data.split(':')[1:])

    if month == 1:
        month = 12
        year -= 1

    else:
        month -= 1

    data = await state.get_data()

    if {'start_day_dates', '1_period', '1_earlier_period', 'start_day_earlier_dates'}.intersection(data.keys()):
        new_calendar_markup = generate_calendar_inline_kb(year, month, is_period=False,
                                                          first_date_or_period_selected=True)

    else:
        new_calendar_markup = generate_calendar_inline_kb(year, month, is_period=False)

    await callback.message.edit_reply_markup(reply_markup=new_calendar_markup)


@filling_out_report_router.callback_query(F.data.split(':')[0] == 'next_month_period')
@user_access
async def next_month_handler(callback: CallbackQuery, state: FSMContext):
    year, month = map(int, callback.data.split(':')[1:])

    if month == 12:
        month = 1
        year += 1

    else:
        month += 1

    data = await state.get_data()

    if {'start_day_dates', '1_period', '1_earlier_period', 'start_day_earlier_dates'}.intersection(data.keys()):
        new_calendar_markup = generate_calendar_inline_kb(year, month, first_date_or_period_selected=True)

    else:
        new_calendar_markup = generate_calendar_inline_kb(year, month)

    await callback.message.edit_reply_markup(reply_markup=new_calendar_markup)


@filling_out_report_router.callback_query(F.data.split(':')[0] == 'next_month_dates')
@user_access
async def next_month_handler(callback: CallbackQuery, state: FSMContext):
    year, month = map(int, callback.data.split(':')[1:])

    if month == 12:
        month = 1
        year += 1

    else:
        month += 1

    data = await state.get_data()

    if {'start_day_dates', '1_period', '1_earlier_period', 'start_day_earlier_dates'}.intersection(data.keys()):
        new_calendar_markup = generate_calendar_inline_kb(year, month, is_period=False,
                                                          first_date_or_period_selected=True)

    else:
        new_calendar_markup = generate_calendar_inline_kb(year, month, is_period=False)

    await callback.message.edit_reply_markup(reply_markup=new_calendar_markup)


@filling_out_report_router.callback_query(F.data == 'continue_filling_in')
@user_access
async def continue_filling_in_handler(callback: CallbackQuery, state: FSMContext):
    data = await state.get_data()

    if await check_fullness_of_period(callback, data):
        return

    if await check_any_dates_or_period(callback, data):
        return

    if {'choose_dates', 'start_day_dates'}.issubset(data.keys()):
        await state.update_data(absence_dates=[data['start_day_dates']])

        data = await state.get_data()

        date_pattern = re.compile(r'^\d{1,2}\.\d{1,2}\.\d{4}$')
        for key, value in data.items():
            if date_pattern.match(key):
                data['absence_dates'].append(value)

        periods_count = 0
        period_pattern = re.compile(r'\d+_period$')

        for key in data.keys():
            if period_pattern.search(key):
                periods_count += 1

        if periods_count >= 1:
            await state.update_data(absence_periods=[data[f'{period_count}_period']
                                                     for period_count in range(1, periods_count + 1)])

        fill_manual_inline_kb = generate_fill_manual_inline_kb()
        await callback.message.edit_text(text=f'Выберите "Заполнить вручную" или "Отмена":',
                                         reply_markup=fill_manual_inline_kb)

    elif 'choose_periods' in data:
        periods_count = 0
        pattern = re.compile(r'\d+_period$')

        for key in data.keys():
            if pattern.search(key):
                periods_count += 1

        if periods_count == 1:
            absence_reason_inline_kb = generate_absence_reason_inline_kb()

            await state.update_data(absence_periods=[data['1_period']])

            await callback.message.edit_text(text=f'{str(Emoji.CheckMarkEmoji)} Выберите причину отсутствия: ',
                                             reply_markup=absence_reason_inline_kb)

        else:
            await state.update_data(absence_periods=[data[f'{period_count}_period']
                                                     for period_count in range(1, periods_count + 1)])

            fill_manual_inline_kb = generate_fill_manual_inline_kb()
            await callback.message.edit_text(text=f'Выберите "Заполнить вручную" или "Отмена":',
                                             reply_markup=fill_manual_inline_kb)


async def update_absence_reason_handler(callback: CallbackQuery, state: FSMContext, employee_id: int,
                                        absence_reason_desc: str, skip_absence: bool = False):
    data = await state.get_data()

    if 'another_absence_reason' in data:
        absence_reason_full_desc = absence_reason_desc

    else:
        absence_reason_full_desc = get_absence_reason_full_desc(employee_id, absence_reason_desc)

    await state.update_data(absence_reason_full_desc=absence_reason_full_desc)

    if skip_absence:
        await skip_absence_handler(callback, state)

    else:
        await get_final_result(callback.message, state)


async def partial_absence_handler(callback: CallbackQuery, state: FSMContext, employee_id: int,
                                  absence_reason_desc: str, start_date: date, end_date: date,
                                  work_date_range_set: Set[date], periods_and_dates_set: Set[date]):
    start_period_text, end_period_text = format_period(start_date, end_date)

    absence_reason_desc += f' с {start_period_text} по {end_period_text}'

    if work_date_range_set == periods_and_dates_set or work_date_range_set.issubset(periods_and_dates_set):
        await update_absence_reason_handler(callback, state, employee_id, absence_reason_desc)
    else:
        await update_absence_reason_handler(callback, state, employee_id, absence_reason_desc, skip_absence=True)


async def update_absence_period_and_reason_handler(callback: CallbackQuery, state: FSMContext, employee_id: int,
                                                   absence_reason_desc: str, start_date: date, end_date: date,
                                                   skip_absence: bool = False):
    absence_reason_full_desc = generate_absence_reason_full_desc(start_date, end_date,
                                                                 absence_reason_desc)

    await update_absence_reason_handler(callback, state, employee_id, absence_reason_full_desc, skip_absence)


async def intersecting_and_out_of_range_absence_handler(callback: CallbackQuery, state: FSMContext, employee_id: int,
                                                        absence_reason_desc: str, start_date: date,
                                                        end_date: date, work_date_range_set: Set[date],
                                                        periods_and_dates_set: Set[date]):
    if work_date_range_set == periods_and_dates_set or work_date_range_set.issubset(periods_and_dates_set):
        await update_absence_period_and_reason_handler(callback, state, employee_id, absence_reason_desc, start_date,
                                                       end_date)
    else:
        await update_absence_period_and_reason_handler(callback, state, employee_id, absence_reason_desc, start_date,
                                                       end_date, True)


async def update_manual_absence_reason_handler(message: Message, state: FSMContext, employee_id: int,
                                               week_absence_string: str, skip_absence: bool = False):
    data = await state.get_data()

    if 'another_absence_reason' in data:
        absence_reason_full_desc = week_absence_string

    else:
        absence_reason_full_desc = get_absence_reason_full_desc(employee_id, week_absence_string)

    await state.update_data(absence_reason_full_desc=absence_reason_full_desc)

    if skip_absence:
        cancel_inline_kb = generate_cancel_inline_kb()
        await message.answer(text=f'{str(Emoji.Note)} Введите фактически выполненные '
                                  f'работы за отчетный период:',
                             reply_markup=cancel_inline_kb)
        await state.set_state(FillingOutReportStates.enter_actual_performance)

    else:
        await get_final_result(message, state)


@filling_out_report_router.callback_query(F.data.split(':')[0] == 'absence_reason')
@user_access
async def absence_reason_handler(callback: CallbackQuery, state: FSMContext):
    _, absence_reason = callback.data.split(':')
    data = await state.get_data()

    if 'employee_id' not in data:
        await callback.answer(text=f'{str(Emoji.Warning)} Вы не выбрали сотрудника!', show_alert=True)
        await filling_out_report_menu_handler(callback, state)
        return

    if absence_reason == 'fill_manual':
        await absence_reason_manual_handler(callback.message, state)
        return

    absence_reason_desc = AbsenceReasons.get_description_from_callback_info(absence_reason)

    if absence_reason_desc is AbsenceReasons.NoReason.desc:
        await callback.answer(text=f'{str(Emoji.Error)} Неизвестная причина отсутствия!', show_alert=True)
        await select_days_period(callback, state)
        return

    start_dates_period, end_dates_period = get_dates_range(data)
    date_range_period_set, work_date_range_period_set, periods_and_dates_set = (
        get_date_sets(start_dates_period[0], end_dates_period[0], data))

    if date_range_period_set == work_date_range_period_set:
        await update_absence_reason_handler(callback, state, data['employee_id'], absence_reason_desc)

    elif date_range_period_set.issubset(work_date_range_period_set):
        await partial_absence_handler(callback, state, data['employee_id'], absence_reason_desc,
                                      start_dates_period[0], end_dates_period[0], work_date_range_period_set,
                                      periods_and_dates_set)

    elif work_date_range_period_set.issubset(date_range_period_set):
        await update_absence_period_and_reason_handler(callback, state, data['employee_id'], absence_reason_desc,
                                                       start_dates_period[0], end_dates_period[0])

    else:
        await intersecting_and_out_of_range_absence_handler(callback, state, data['employee_id'], absence_reason_desc,
                                                            start_dates_period[0], end_dates_period[0],
                                                            work_date_range_period_set, periods_and_dates_set)


async def choose_manual_dates_and_period_handler(message: Message, state: FSMContext, data: Dict[str, Any]):
    selected_days, formatted_days, formatted_dates = generate_dates_text(data)

    start_dates, end_dates = get_dates_range(data)
    selected_periods, formatted_periods, formatted_dates_and_periods = (
        generate_period_text(start_dates, end_dates, formatted_dates))

    periods_and_dates_set = set()
    for period_or_date in formatted_dates_and_periods:
        if isinstance(period_or_date, tuple):
            date_range = create_date_range(period_or_date[0], period_or_date[1])
            for current_date in date_range:
                periods_and_dates_set.add(current_date)

        else:
            periods_and_dates_set.add(period_or_date)

    periods_and_dates_set = update_periods_and_dates_set(data, periods_and_dates_set)

    await state.update_data({'formatted_dates_and_periods': formatted_dates_and_periods,
                             'periods_and_dates_set': periods_and_dates_set})

    cancel_inline_kb = generate_cancel_inline_kb()

    await state.set_state(FillingOutReportStates.enter_absence_reason_manual)
    await message.edit_text(
        text=f'{str(Emoji.CalendarEmoji)} {str(Emoji.PeriodEmoji)} Вы выбрали следующие даты и период(ы):\n\n'
             f'{selected_days}\n{selected_periods}\n\nСкопируйте строчку ниже и введите причины отсутствия по отдельным '
             f'датам и периоду(ам) (запишите их вместо символов "()"):\n\n{formatted_days}, {formatted_periods}',
        reply_markup=cancel_inline_kb
    )


async def choose_manual_dates_handler(message: Message, state: FSMContext, data: Dict[str, Any]):
    selected_days, formatted_days, formatted_dates = generate_dates_text(data)

    dates_set = {current_date for current_date in formatted_dates}

    dates_set = update_periods_and_dates_set(data, dates_set)

    await state.update_data({'formatted_dates_and_periods': formatted_dates,
                             'periods_and_dates_set': dates_set})

    cancel_inline_kb = generate_cancel_inline_kb()

    await state.set_state(FillingOutReportStates.enter_absence_reason_manual)
    await message.edit_text(
        text=f'{str(Emoji.CalendarEmoji)} Вы выбрали следующие даты:\n\n'
             f'{selected_days}\nСкопируйте строчку ниже и введите причину отсутствия по отдельным датам '
             f'(запишите ее вместо символов "()"):\n\n'
             f'{formatted_days}',
        reply_markup=cancel_inline_kb
    )


async def choose_manual_period_handler(message: Message, state: FSMContext, data: Dict[str, Any]):
    start_dates, end_dates = get_dates_range(data)

    selected_periods, formatted_periods, formatted_periods_and_dates = generate_period_text(start_dates, end_dates)

    periods_set = set()
    for period in formatted_periods_and_dates:
        date_range = create_date_range(period[0], period[1])
        for current_date in date_range:
            periods_set.add(current_date)

    periods_set = update_periods_and_dates_set(data, periods_set)

    await state.update_data({'formatted_dates_and_periods': formatted_periods_and_dates,
                             'periods_and_dates_set': periods_set})

    cancel_inline_kb = generate_cancel_inline_kb()

    await state.set_state(FillingOutReportStates.enter_absence_reason_manual)
    await message.edit_text(
        text=f'{str(Emoji.PeriodEmoji)} Вы выбрали следующий период(ы):\n\n'
             f'{selected_periods}\n\nСкопируйте строчку ниже и введите причину(ы) отсутствия по выбранному периоду(ам) '
             f'(запишите ее(их) вместо символов "()"):\n\n'
             f'{formatted_periods}',
        reply_markup=cancel_inline_kb
    )


@user_access
async def absence_reason_manual_handler(message: Message, state: FSMContext):
    data = await state.get_data()

    if 'choose_dates' in data and 'choose_periods' in data:
        if 'start_day_dates' not in data:
            await choose_manual_period_handler(message, state, data)
        else:
            await choose_manual_dates_and_period_handler(message, state, data)

    elif 'choose_dates' in data:
        await choose_manual_dates_handler(message, state, data)

    elif 'choose_periods' in data:
        await choose_manual_period_handler(message, state, data)


async def comparison_absence_dates_or_periods(message: Message, state: FSMContext, employee_id: int,
                                              absence_dates_or_period_set: Set[date], work_range_set: Set[date],
                                              week_absence_string: str):
    if absence_dates_or_period_set == work_range_set or work_range_set.issubset(absence_dates_or_period_set):
        await update_manual_absence_reason_handler(message, state, employee_id, week_absence_string)

    else:
        await update_manual_absence_reason_handler(message, state, employee_id, week_absence_string, skip_absence=True)


@filling_out_report_router.message(FillingOutReportStates.enter_absence_reason_manual)
@user_access
async def enter_absence_reason_manual_handler(message: Message, state: FSMContext):
    data = await state.get_data()

    if message.text and cleanup(message.text).lower() == 'отмена':
        await main_menu_handler(message, state)
        return

    if 'employee_id' not in data:
        await main_menu_handler(message, state)
        return

    if 'periods_and_dates_set' in data:
        work_range_set = set(create_date_range(*get_current_work_period()))
        week_absence_string = parse_absence_dates_and_periods(message.text, data['formatted_dates_and_periods'])

        await comparison_absence_dates_or_periods(message, state, data['employee_id'], data['periods_and_dates_set'],
                                                  work_range_set, week_absence_string)


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
@user_access
async def obtained_result_handler(callback: CallbackQuery, state: FSMContext):
    _, obtained_result = callback.data.split(':')

    if obtained_result == 'working_materials':
        await state.update_data(obtained_result='Рабочие материалы')
        await get_final_result(callback.message, state)

    elif obtained_result == 'documents':
        cancel_inline_kb = generate_cancel_inline_kb()
        await callback.message.edit_text(text=f'{str(Emoji.EditText)} Введите название документа:',
                                         reply_markup=cancel_inline_kb)
        await state.set_state(FillingOutReportStates.enter_document_name)

    else:
        obtained_result_kb = generate_obtained_result_inline_kb()
        await callback.message.answer(text=f'{str(Emoji.Warning)} Выберите полученный результат еще раз:\n',
                                      reply_markup=obtained_result_kb)


@filling_out_report_router.message(FillingOutReportStates.enter_document_name)
@user_access
async def enter_document_name_handler(message: Message, state: FSMContext):
    if message.text and cleanup(message.text).lower() == 'отмена':
        await main_menu_handler(message, state)

    else:
        await state.update_data(obtained_result=f'Документ "{message.text}"')
        await get_final_result(message, state)


@filling_out_report_router.callback_query(F.data == 'cancel_all')
@user_access
async def cancel_all_handler(callback: CallbackQuery, state: FSMContext):
    await main_menu_handler(callback.message, state)


@filling_out_report_router.callback_query(F.data == 'skip_absence')
@user_access
async def skip_absence_handler(callback: CallbackQuery, state: FSMContext):
    data = await state.get_data()

    if await check_fullness_of_period(callback, data):
        return

    if 'employee_id' not in data:
        await callback.answer(text=f'{str(Emoji.Warning)} Вы не выбрали сотрудника!', show_alert=True)
        await filling_out_report_menu_handler(callback, state)
        return

    response = await get_employee_by_id(data['employee_id'])

    if response.error:
        await callback.answer(text=f'{str(Emoji.Error)} {response.message}', show_alert=True)
        await main_menu_handler(callback.message, state)
        return

    work_range_set = set(create_date_range(*get_current_work_period()))
    periods_and_dates = tuple(get_earlier_absence_data_dict_from_desc(response.value.absence_reason).values())
    periods_and_dates_set = set()

    for period_or_date in periods_and_dates:
        if isinstance(period_or_date, list):
            period = create_date_range(*period_or_date)
            for current_date in period:
                periods_and_dates_set.add(current_date)

        else:
            periods_and_dates_set.add(period_or_date)

    if work_range_set == periods_and_dates_set or work_range_set.issubset(periods_and_dates_set):
        await main_menu_handler(callback.message, state)
        return

    cancel_inline_kb = generate_cancel_inline_kb()
    await callback.message.edit_text(text=f'{str(Emoji.Note)} Введите фактически выполненные '
                                          f'работы за отчетный период:',
                                     reply_markup=cancel_inline_kb)
    await state.set_state(FillingOutReportStates.enter_actual_performance)


@user_access
async def get_final_result(message: Message, state: FSMContext):
    data = await state.get_data()

    if 'employee_id' not in data:
        await message.answer(text=f'{str(Emoji.Error)} Вы не выбрали сотрудника!')
        await main_menu_handler(message, state)
        return

    response = await get_employee_by_id(data['employee_id'])
    if response.error:
        await message.answer(text=f'{str(Emoji.Error)} {response.message}')
        await main_menu_handler(message, state)
        return

    employee_name = response.value.full_name
    employee_info = get_final_employee_info(data)

    final_inline_kb = generate_final_inline_kb()
    await message.answer(text=f'{str(Emoji.EmployeeEmoji)} Вы заполнили отчет за {employee_name}\n'
                              f'{employee_info}', reply_markup=final_inline_kb)


@filling_out_report_router.callback_query(F.data == 'save_data')
@user_access
async def save_data_handler(callback: CallbackQuery, state: FSMContext):
    data = await state.get_data()

    if 'employee_id' not in data:
        await callback.answer(text=f'{str(Emoji.Warning)} Вы не выбрали сотрудника!', show_alert=True)
        await filling_out_report_menu_handler(callback, state)
        return

    if not {'actual_performance', 'obtained_result', 'absence_reason_full_desc'}.intersection(data.keys()):
        await callback.answer(text=f'{str(Emoji.Warning)} Информация не сохранилась, заполните еще раз!',
                              show_alert=True)
        await filling_out_report_menu_handler(callback, state)

        return

    if {'actual_performance', 'obtained_result'}.issubset(data.keys()):
        response = await add_report_data(data['actual_performance'],
                                         data['obtained_result'],
                                         data['employee_id'])
        if response.error:
            await callback.answer(text=f'{str(Emoji.Error)} {response.message}', show_alert=True)
            await filling_out_report_menu_handler(callback, state)
            return

        await callback.answer(text=f'{str(Emoji.Success)} {response.message}', show_alert=True)

    if 'absence_reason_full_desc' in data:
        response = await update_employee_absence_reason_by_id(data['employee_id'], data['absence_reason_full_desc'])

        if response.error:
            await callback.answer(text=f'{str(Emoji.Error)} {response.message}', show_alert=True)
            await main_menu_handler(callback.message, state)
            return

        await callback.answer(text=f'{str(Emoji.Success)} {response.message}', show_alert=True)

    await main_menu_handler(callback.message, state)

