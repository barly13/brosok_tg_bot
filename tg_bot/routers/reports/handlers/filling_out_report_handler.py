from datetime import datetime, timedelta
from typing import Set, Dict, Any

from aiogram import Router, F
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import StatesGroup, State
from aiogram.types import Message, CallbackQuery, ReplyKeyboardRemove

from tg_bot.functions import cleanup
from tg_bot.routers.main.main_handler import main_menu_handler
from tg_bot.routers.reports.backend.absence_reasons_enum import AbsenceReasons
from tg_bot.routers.reports.backend.filling_out_report_backend import get_all_employees, get_employee_by_id, \
    create_date_range, get_current_work_period, update_employee_absence_reason_by_id, add_report_data, \
    get_date_sets, format_period, get_partial_end_date, format_date, get_partial_start_date, \
    update_absence_period_or_dates_by_id, get_absence_date_sets, generate_dates_text_and_absence_dates, \
    generate_period_text, get_dates_range, get_final_employee_info
from tg_bot.routers.reports.keyboard import generate_inline_kb_for_employees_list, \
    generate_calendar_inline_kb, generate_obtained_result_inline_kb, generate_absence_reason_inline_kb, \
    generate_cancel_inline_kb, generate_final_inline_kb, generate_period_or_dates_inline_kb, \
    generate_fill_manual_inline_kb, generate_re_select_period_inline_kb
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
        await callback.message.answer(f'{str(Emoji.Error)} {response.message}')
        await main_menu_handler(callback.message, state)

    else:
        if not response.value:
            await callback.message.answer(f'{str(Emoji.Warning)} В базе данных нет ни одного сотрудника')
            await main_menu_handler(callback.message, state)

        else:
            data = await state.get_data()

            employees_list_inline_kb = generate_inline_kb_for_employees_list(response.value)

            if 'employee_id' in data:
                await callback.message.edit_text(text=f'{str(Emoji.EmployeeEmoji)} Смените сотрудника из списка:\n',
                                                 reply_markup=employees_list_inline_kb)
            else:
                await callback.message.edit_text(text=f'{str(Emoji.EmployeeEmoji)} Выберите сотрудника в списке:\n',
                                                 reply_markup=employees_list_inline_kb)


@filling_out_report_router.callback_query(F.data.split('_')[0] == 'employee')
@user_access
async def filling_out_employee_report(callback: CallbackQuery, state: FSMContext):
    # TODO Сделать проверку на даты или период из бд, чтобы человек заполнил

    employee_id = int(callback.data.split('_')[1])
    response = await get_employee_by_id(employee_id)

    if response.error:
        await callback.message.answer(text=f'{str(Emoji.Error)} {response.message}')
        await main_menu_handler(callback.message, state)

    else:
        data = await state.get_data()

        if 'employee_id' in data:
            await state.update_data(employee_id=employee_id)
            await get_final_result(callback.message, state)

        else:
            period_or_dates_inline_kb = generate_period_or_dates_inline_kb()

            await callback.message.edit_text(text=f'{str(Emoji.CheckMarkEmoji)} Выберите период, либо отдельные даты, '
                                                  f'когда {response.value.full_name} отсутствовал(а), или нажмите '
                                                  f'"Пропустить":',
                                             reply_markup=period_or_dates_inline_kb)

            await state.update_data(employee_id=employee_id)


@filling_out_report_router.callback_query(F.data == 'choose_periods')
@user_access
async def choose_periods_handler(callback: CallbackQuery, state: FSMContext):
    await state.update_data(choose_periods=True)

    today = datetime.today()
    calendar_markup = generate_calendar_inline_kb(today.year, today.month)

    await callback.message.edit_text(text=f'{str(Emoji.PeriodEmoji)} '
                                          f'Выберите период отсутствия или нажмите "Пропустить":',
                                     reply_markup=calendar_markup)


@filling_out_report_router.callback_query(F.data == 'choose_dates')
@user_access
async def choose_dates_handler(callback: CallbackQuery, state: FSMContext):
    await state.update_data(choose_dates=True)

    today = datetime.today()
    calendar_markup = generate_calendar_inline_kb(today.year, today.month, is_period=False)

    await callback.message.edit_text(text=f'{str(Emoji.CalendarEmoji)} '
                                          f'Выберите даты отсутствия или нажмите "Пропустить":',
                                     reply_markup=calendar_markup)


@filling_out_report_router.callback_query(F.data.split(':')[0] == 'day_period')
@user_access
async def select_days_period(callback: CallbackQuery, state: FSMContext):
    year, month, day = map(int, callback.data.split(':')[1:])
    work_dates_set = set(create_date_range(*get_current_work_period()))

    data = await state.get_data()

    period_count = sum(
        1 for key, value in data.items() if key.endswith('_period') and type(value) is list and len(value) == 2) + 1

    if f'{period_count}_period' in data:
        second_date = datetime(int(year), int(month), int(day))

        if second_date in work_dates_set or second_date > max(work_dates_set):
            data[f'{period_count}_period'].append(second_date)

            re_select_inline_kb = generate_re_select_period_inline_kb()
            await callback.message.edit_text(text=f'{str(Emoji.CheckMarkEmoji)} Выберите (при необходимости) '
                                                  f'еще период/даты отсутствия, либо, если вы уже выбрали '
                                                  f'нужный период нажмите "Продолжить:"',
                                             reply_markup=re_select_inline_kb)

        else:
            await callback.answer(text=f'{str(Emoji.Warning)} Вы выбрали дату до отчетного периода. Выберите дату, '
                                       f'находящуюся в отчетном периоде ({str(Emoji.CheckMarkEmoji)}) или после него!',
                                  show_alert=True)

    else:
        first_date = datetime(int(year), int(month), int(day))

        if first_date in work_dates_set or first_date > max(work_dates_set):
            await state.update_data({f'{period_count}_period': [first_date]})

        else:
            await callback.answer(text=f'{str(Emoji.Warning)} Вы выбрали дату до отчетного периода. Выберите дату, '
                                       f'находящуюся в отчетном периоде ({str(Emoji.CheckMarkEmoji)}) или после него!',
                                  show_alert=True)


@filling_out_report_router.callback_query(F.data.split(':')[0] == 'day_dates')
@user_access
async def select_days_dates(callback: CallbackQuery, state: FSMContext):
    year, month, day = map(int, callback.data.split(':')[1:])
    work_dates_set = set(create_date_range(*get_current_work_period()))

    data = await state.get_data()

    if 'start_day_dates' in data:
        next_day = datetime(int(year), int(month), int(day))

        if next_day in work_dates_set or next_day > max(work_dates_set):
            await state.update_data({f'{day}.{month}.{year}': next_day})

        else:
            await callback.answer(text=f'{str(Emoji.Warning)} Вы выбрали дату до отчетного периода. Выберите дату, '
                                       f'находящуюся в отчетном периоде ({str(Emoji.CheckMarkEmoji)}) или после него!',
                                  show_alert=True)

    else:
        start_date = datetime(int(year), int(month), int(day))

        if start_date in work_dates_set or start_date > max(work_dates_set):
            await state.update_data(start_day_dates=start_date)

            calendar_markup = generate_calendar_inline_kb(year, month, is_period=False, first_date_selected=True)
            await callback.message.edit_reply_markup(reply_markup=calendar_markup)

        else:
            await callback.answer(text=f'{str(Emoji.Warning)} Вы выбрали дату до отчетного периода. Выберите дату, '
                                       f'находящуюся в отчетном периоде ({str(Emoji.CheckMarkEmoji)}) или после него!',
                                  show_alert=True)


@filling_out_report_router.callback_query(F.data.split(':')[0] == 'prev_month_period')
@user_access
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
@user_access
async def prev_month_handler(callback: CallbackQuery, state: FSMContext):
    year, month = map(int, callback.data.split(':')[1:])

    if month == 1:
        month = 12
        year -= 1

    else:
        month -= 1

    data = await state.get_data()

    if 'start_day_dates' in data:
        new_calendar_markup = generate_calendar_inline_kb(year, month, is_period=False, first_date_selected=True)

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

    if 'start_day_dates' in data:
        new_calendar_markup = generate_calendar_inline_kb(year, month, is_period=False, first_date_selected=True)

    else:
        new_calendar_markup = generate_calendar_inline_kb(year, month, is_period=False)

    await callback.message.edit_reply_markup(reply_markup=new_calendar_markup)


@filling_out_report_router.callback_query(F.data == 'continue_filling_in')
@user_access
async def continue_filling_in_handler(callback: CallbackQuery, state: FSMContext):
    data = await state.get_data()

    if 'choose_dates' in data:
        fill_manual_inline_kb = generate_fill_manual_inline_kb()
        await callback.message.edit_text(text=f'Выберите "Заполнить вручную" или "Отмена":',
                                         reply_markup=fill_manual_inline_kb)

    elif 'choose_periods' in data:
        periods_count = 0

        for key in data.keys():
            if key.endswith('_period'):
                periods_count += 1

        if periods_count == 1:
            absence_reason_inline_kb = generate_absence_reason_inline_kb()
            await callback.message.edit_text(text=f'{str(Emoji.CheckMarkEmoji)} Выберите причину отсутствия: ',
                                             reply_markup=absence_reason_inline_kb)

        else:
            fill_manual_inline_kb = generate_fill_manual_inline_kb()
            await callback.message.edit_text(text=f'Выберите "Заполнить вручную" или "Отмена":',
                                             reply_markup=fill_manual_inline_kb)


@filling_out_report_router.callback_query(F.data == 'cancel_all')
@user_access
async def cancel_all_handler(callback: CallbackQuery, state: FSMContext):
    await main_menu_handler(callback.message, state)


@filling_out_report_router.callback_query(F.data == 'skip_absence')
@user_access
async def skip_absence_handler(callback: CallbackQuery, state: FSMContext):
    cancel_inline_kb = generate_cancel_inline_kb()
    await callback.message.edit_text(text=f'{str(Emoji.Note)} Введите фактически выполненные '
                                          f'работы за отчетный период:',
                                     reply_markup=cancel_inline_kb)
    await state.set_state(FillingOutReportStates.enter_actual_performance)


async def update_absence_reason_handler(callback: CallbackQuery, state: FSMContext, employee_id: int,
                                        absence_reason_desc: str, skip_absence: bool = False):
    response = await update_employee_absence_reason_by_id(employee_id, absence_reason_desc)

    if response.error:
        await callback.answer(text=f'{str(Emoji.Error)} {response.message}', show_alert=True)
        await main_menu_handler(callback.message, state)

    else:
        await callback.answer(text=f'{str(Emoji.Success)} {response.message}', show_alert=True)

        if skip_absence:
            await skip_absence_handler(callback, state)

        else:
            await main_menu_handler(callback.message, state)


async def partial_absence_handler(callback: CallbackQuery, state: FSMContext, employee_id: int,
                                  absence_reason_desc: str, start_date: datetime, end_date: datetime):
    start_period_text, end_period_text = format_period(start_date, end_date)

    absence_reason_desc += f' c {start_period_text} по {end_period_text}'
    await state.update_data(absence_periods=tuple((start_date, end_date)))

    await update_absence_reason_handler(callback, state, employee_id, absence_reason_desc, skip_absence=True)


async def update_absence_period_and_reason_handler(callback: CallbackQuery, state: FSMContext, employee_id: int,
                                                   absence_reason_desc: str, min_end_date: datetime,
                                                   start_date: datetime, end_date: datetime,
                                                   skip_absence: bool = False):
    response = await update_absence_period_or_dates_by_id(
        employee_id, absence_period_or_dates={'periods': tuple((min_end_date + timedelta(days=1), end_date))})

    if response.error:
        await callback.answer(text=f'{str(Emoji.Error)} {response.message}', show_alert=True)
        await main_menu_handler(callback.message, state)
        return

    else:
        await callback.answer(text=f'{str(Emoji.Success)} {response.message}', show_alert=True)

    if start_date.year == min_end_date.year:
        start_period_text = format_date(start_date)

    else:
        start_period_text = format_date(start_date, is_same_year=False)

    absence_reason_desc += f' с {start_period_text}'
    end_period_text = format_date(min_end_date, is_same_year=False)
    absence_reason_desc += f' по {end_period_text}'

    await update_absence_reason_handler(callback, state, employee_id, absence_reason_desc, skip_absence)


async def full_absence_handler(callback: CallbackQuery, state: FSMContext, employee_id: int,
                               absence_reason_desc: str, start_date: datetime, end_date: datetime,
                               work_date_range_set: Set[datetime]):
    min_end_date = max(work_date_range_set)

    await update_absence_period_and_reason_handler(callback, state, employee_id, absence_reason_desc,
                                                   min_end_date, start_date, end_date, True)


async def intersecting_absence_handler(callback: CallbackQuery, state: FSMContext, employee_id: int,
                                       absence_reason_desc: str, start_date: datetime, end_date: datetime,
                                       work_date_range_set: Set[datetime]):
    min_end_date = max(work_date_range_set)

    await state.update_data(absence_periods=tuple((start_date, min_end_date)))

    await update_absence_period_and_reason_handler(callback, state, employee_id, absence_reason_desc, min_end_date,
                                                   start_date, end_date)


async def out_of_range_absence_handler(callback: CallbackQuery, state: FSMContext, start_date: datetime,
                                       end_date: datetime):
    await state.update_data(absence_period=(start_date, end_date))
    await skip_absence_handler(callback, state)


async def update_manual_absence_reason_handler(message: Message, state: FSMContext, employee_id: int,
                                               absence_reason_desc: str, skip_absence: bool = True):
    response = await update_employee_absence_reason_by_id(employee_id, absence_reason_desc)
    if response.error:
        await message.answer(text=f'{str(Emoji.Error)} {response.message}')
        await main_menu_handler(message, state)

    else:
        await message.answer(text=f'{str(Emoji.Success)} {response.message}')

        if skip_absence:
            await main_menu_handler(message, state)

        else:
            cancel_inline_kb = generate_cancel_inline_kb()
            await message.edit_text(text=f'{str(Emoji.Note)} Введите фактически выполненные '
                                         f'работы за отчетный период:',
                                    reply_markup=cancel_inline_kb)
            await state.set_state(FillingOutReportStates.enter_actual_performance)


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
    date_range_period_set, work_date_range_period_set = get_date_sets(start_dates_period[0], end_dates_period[0])

    if date_range_period_set == work_date_range_period_set:
        await update_absence_reason_handler(callback, state, data['employee_id'], absence_reason_desc)

    elif date_range_period_set.issubset(work_date_range_period_set):
        await partial_absence_handler(callback, state, data['employee_id'], absence_reason_desc,
                                      start_dates_period[0], end_dates_period[0])

    elif work_date_range_period_set.issubset(date_range_period_set):
        await full_absence_handler(callback, state, data['employee_id'], absence_reason_desc, start_dates_period[0],
                                   end_dates_period[0], work_date_range_period_set)

    elif work_date_range_period_set.intersection(date_range_period_set):
        await intersecting_absence_handler(callback, state, data['employee_id'], absence_reason_desc,
                                           start_dates_period[0], end_dates_period[0], work_date_range_period_set)

    else:
        await out_of_range_absence_handler(callback, state, start_dates_period[0], end_dates_period[0])


async def choose_manual_dates_and_period_handler(message: Message, state: FSMContext, data: Dict[str, Any]):
    selected_days, formatted_days, absence_dates = generate_dates_text_and_absence_dates(data)
    await state.update_data(absence_dates=absence_dates)

    start_dates, end_dates = get_dates_range(data)
    await state.update_data(absence_periods=tuple(zip(start_dates, end_dates)))
    selected_periods, formatted_periods = generate_period_text(start_dates, end_dates)

    cancel_inline_kb = generate_cancel_inline_kb()

    await state.set_state(FillingOutReportStates.enter_absence_reason_manual)
    await message.answer(
        text=f'{str(Emoji.CalendarEmoji)} {str(Emoji.PeriodEmoji)} Вы выбрали следующие даты и период(ы):\n\n'
             f'{selected_days}\n{selected_periods}\n\nСкопируйте строчку ниже и введите причины отсутствия по отдельным '
             f'датам и периоду(ам) (запишите их вместо символов "()"):\n\n{formatted_days}, {formatted_periods}',
        reply_markup=cancel_inline_kb
    )


async def choose_manual_dates_handler(message: Message, state: FSMContext, data: Dict[str, Any]):
    selected_days, formatted_days, absence_dates = generate_dates_text_and_absence_dates(data)

    await state.update_data(absence_dates=absence_dates)

    cancel_inline_kb = generate_cancel_inline_kb()

    await state.set_state(FillingOutReportStates.enter_absence_reason_manual)
    await message.answer(
        text=f'{str(Emoji.CalendarEmoji)} Вы выбрали следующие даты:\n\n'
             f'{selected_days}\nСкопируйте строчку ниже и введите причину отсутствия по отдельным датам '
             f'(запишите ее вместо символов "()"):\n\n'
             f'{formatted_days}',
        reply_markup=cancel_inline_kb
    )


async def choose_manual_period_handler(message: Message, state: FSMContext, data: Dict[str, Any]):
    start_dates, end_dates = get_dates_range(data)
    await state.update_data(absence_periods=tuple(zip(start_dates, end_dates)))
    selected_periods, formatted_periods = generate_period_text(start_dates, end_dates)

    cancel_inline_kb = generate_cancel_inline_kb()

    await state.set_state(FillingOutReportStates.enter_absence_reason_manual)
    await message.answer(
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
        await choose_manual_dates_and_period_handler(message, state, data)

    elif 'choose_dates' in data:
        await choose_manual_dates_handler(message, state, data)

    elif 'choose_periods' in data:
        await choose_manual_period_handler(message, state, data)


async def enter_absence_reason_manual_dates_and_period_handler(message: Message, state: FSMContext,
                                                               data: Dict[str, Any]):
    print(data['absence_dates'], data['absence_periods'])


async def enter_absence_reason_manual_dates_handler(message: Message, state: FSMContext, data: Dict[str, Any]):
    absence_dates_set = set(data['absence_dates'])
    work_dates_set = set(create_date_range(*get_current_work_period()))

    



async def enter_absence_reason_manual_periods_handler(message: Message, state: FSMContext, data: Dict[str, Any]):
    print(data['absence_periods'])
    start_dates_period, end_dates_period = get_dates_range(data)


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

    if 'absence_dates' in data and 'absence_periods' in data:
        await enter_absence_reason_manual_dates_and_period_handler(message, state, data)

    elif 'absence_dates' in data:
        await enter_absence_reason_manual_dates_handler(message, state, data)

    elif 'absence_periods' in data:
        await enter_absence_reason_manual_periods_handler(message, state, data)


    date_range_period_set, work_date_range_period_set = get_date_sets(start_dates_period[0], end_dates_period[0])

    selected_set, work_date_range_period_set = get_absence_date_sets(data)

    if selected_set == work_date_range_period_set:
        await update_manual_absence_reason_handler(message, state, data['employee_id'], message.text)

    if max(selected_set) > max(work_date_range_period_set):
        if 'absence_period' in data:
            pass
        elif 'absence_dates' in data:
            pass
        await update_manual_absence_reason_handler(message, state, data['employee_id'], message.text,
                                                   skip_absence=False)

    elif 'employee_id' in data:
        if 'absence_dates' in data:
            selected_dates_set = set(data['selected_dates'])
            work_date_range_period_set = set(create_date_range(
                *get_current_work_period()))

            if selected_dates_set == work_date_range_period_set:
                pass

            elif selected_dates_set.issubset(work_date_range_period_set):
                pass

            elif work_date_range_period_set.issubset(selected_dates_set):
                pass

            elif work_date_range_period_set.intersection(selected_dates_set):
                pass

            else:
                pass

        elif 'absence_period' in data:
            absence_period_set = set(create_date_range(data['absence_period'][0],
                                                       data['absence_period'][1]))
            work_date_range_period_set = set(create_date_range(
                *get_current_work_period()))

            if absence_period_set == work_date_range_period_set:
                pass

            elif absence_period_set.issubset(work_date_range_period_set):
                pass

            elif work_date_range_period_set.issubset(absence_period_set):
                pass

            elif work_date_range_period_set.intersection(absence_period_set):
                pass

            else:
                pass

        response = await update_employee_absence_reason_by_id(data['employee_id'],
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

    else:
        employee_name = response.value.full_name
        employee_info = get_final_employee_info(data)

        final_inline_kb = generate_final_inline_kb()
        await message.edit_text(text=f'{str(Emoji.EmployeeEmoji)} Вы заполнили отчет за {employee_name}\n\n'
                                     f'{employee_info}', reply_markup=final_inline_kb)


# TODO
@filling_out_report_router.callback_query(F.data == 'save_data')
@user_access
async def save_data_handler(callback: CallbackQuery, state: FSMContext):
    data = await state.get_data()

    if 'employee_id' not in data:
        await callback.answer(text=f'{str(Emoji.Warning)} Вы не выбрали сотрудника!', show_alert=True)
        await filling_out_report_menu_handler(callback, state)
        return

    if {'actual_performance', 'obtained_result'}.issubset(set(data.keys())):
        response = await add_report_data(data['actual_performance'],
                                         data['obtained_result'],
                                         data['employee_id'])
        if response.error:
            await callback.answer(text=f'{str(Emoji.Error)} {response.message}', show_alert=True)
            await filling_out_report_menu_handler(callback, state)

        else:
            await callback.answer(text=f'{str(Emoji.Success)} {response.message}', show_alert=True)
            await main_menu_handler(callback.message, state)

    else:
        await callback.answer(text=f'{str(Emoji.Warning)} Информация не сохранилась, заполните еще раз!',
                              show_alert=True)
        await filling_out_report_menu_handler(callback, state)
