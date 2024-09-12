from aiogram import Router, F
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import StatesGroup, State
from aiogram.types import Message, ReplyKeyboardMarkup, CallbackQuery

from tg_bot.functions import cleanup
from tg_bot.routers.reports.backend import filling_out_report_backend
from tg_bot.routers.reports.backend.absence_reasons_enum import AbsenceReasons
from tg_bot.routers.reports.backend.filling_out_report_backend import update_employee_absence_reason_by_id
from tg_bot.routers.reports.keyboard import fill_out_report_kb, generate_inline_kb_for_employees_list, \
    fill_out_employee_report_kb, generate_inline_kb_for_absence_reasons
from tg_bot.security import user_access
from tg_bot.settings import bot
from tg_bot.static.emojis import Emoji

filling_out_report_router = Router()


report_data_dict = {'work_name': '"Наименование работ"', 'actual_performance': '"Выполненные работы"',
                    'obtained_result': '"Полученный результат"', 'employee_id': '"ФИО"', 'work_plan': '"План работ"'}


class FillingOutReportStates(StatesGroup):
    enter_work_name = State()
    enter_actual_performance = State()
    enter_obtained_result = State()
    enter_work_plan = State()
    enter_note = State()


@filling_out_report_router.message(cleanup(F.text).lower() == 'заполнить отчет')
@user_access
async def filling_out_report_menu_handler(message: Message, state: FSMContext):
    markup = ReplyKeyboardMarkup(keyboard=fill_out_report_kb, resize_keyboard=True)
    await message.answer('Составление отчета', reply_markup=markup)
    await state.clear()


@filling_out_report_router.message(cleanup(F.text).lower() == 'выбрать сотрудника')
@user_access
async def choose_employee_to_make_report(message: Message, state: FSMContext):
    response = await filling_out_report_backend.get_all_employees()
    if response.error:
        await message.answer(f'{str(Emoji.Error)} {response.message}')
    else:
        if not response.value:
            await message.answer(f'{str(Emoji.Warning)} В базе данных нет ни одного сотрудника')
        else:
            inline_kb = generate_inline_kb_for_employees_list(response.value)
            await message.answer(f'Выберите сотрудника в списке:\n', reply_markup=inline_kb.as_markup())


@filling_out_report_router.callback_query(F.data.split('_')[0] == 'employee')
async def filling_out_employee_report(callback: CallbackQuery, state: FSMContext):
    employee_id = int(callback.data.split('_')[1])
    response = await filling_out_report_backend.get_employee_by_id(employee_id)
    if response.error:
        await bot.send_message(chat_id=callback.message.chat.id, text=f'{str(Emoji.Error)} {response.message}')
    else:
        markup = ReplyKeyboardMarkup(keyboard=fill_out_employee_report_kb, resize_keyboard=True)

        await bot.send_message(chat_id=callback.message.chat.id,
                               text=f'{response.value.full_name}, заполните информацию:', reply_markup=markup)

    await state.update_data(employee_id=employee_id)


@user_access
async def returning_employee_menu_handler(message: Message, state: FSMContext):
    data = await state.get_data()
    print(data)
    employee_id = data['employee_id']
    response = await filling_out_report_backend.get_employee_by_id(employee_id)
    markup = ReplyKeyboardMarkup(keyboard=fill_out_employee_report_kb, resize_keyboard=True)
    await message.answer(f'{response.value.full_name}, заполните информацию:', reply_markup=markup)


@filling_out_report_router.message(cleanup(F.text).lower() == 'наименование работ в соответствии с тз')
@user_access
async def filling_out_employee_work_name(message: Message, state: FSMContext):
    await message.answer('Введите наименование работ в соответствии с тз / Отмена:')
    await state.set_state(FillingOutReportStates.enter_work_name)


@filling_out_report_router.message(cleanup(F.text).lower() == 'фактически выполненные работы за отчетный период')
@user_access
async def filling_out_employee_actual_performance(message: Message, state: FSMContext):
    await message.answer('Введите фактически выполненные работы за отчетный период / Отмена:')
    await state.set_state(FillingOutReportStates.enter_actual_performance)


@filling_out_report_router.message(cleanup(F.text).lower() == 'полученный результат (вид отчетности)')
@user_access
async def filling_out_employee_obtained_result(message: Message, state: FSMContext):
    await message.answer('Введите полученный результат (вид отчетности) / Отмена:')
    await state.set_state(FillingOutReportStates.enter_obtained_result)


@filling_out_report_router.message(cleanup(F.text).lower() == 'план работ на следующую неделю')
@user_access
async def filling_out_employee_work_plan(message: Message, state: FSMContext):
    await message.answer('Введите план работ на следующую неделю / Отмена:')
    await state.set_state(FillingOutReportStates.enter_work_plan)


@filling_out_report_router.message(cleanup(F.text).lower() == 'примечание (при необходимости)')
@user_access
async def filling_out_employee_note(message: Message, state: FSMContext):
    await message.answer('Введите примечание / Отмена')
    await state.set_state(FillingOutReportStates.enter_note)


@filling_out_report_router.message(cleanup(F.text).lower() == 'причины отсутствия (при наличии)')
@user_access
async def choose_absence_reasons(message: Message, state: FSMContext):
    inline_kb = generate_inline_kb_for_absence_reasons()
    await message.answer(f'Выберите причину отсутствия в списке (Для отмены выберите "Работа"):\n',
                         reply_markup=inline_kb.as_markup())


@filling_out_report_router.callback_query(F.data.split('__')[0] == 'absence_reason')
async def filling_out_employee_report(callback: CallbackQuery, state: FSMContext):
    absence_reason_num = int(callback.data.split('__')[1])
    data = await state.get_data()
    if 'employee_id' in data:
        response = await update_employee_absence_reason_by_id(data['employee_id'], absence_reason_num)
        if response.error:
            await bot.send_message(chat_id=callback.message.chat.id, text=f'{str(Emoji.Error)} {response.message}')
        else:
            if absence_reason_num == AbsenceReasons.NoReason.num:
                await returning_employee_menu_handler(callback.message, state)
            else:
                markup = ReplyKeyboardMarkup(keyboard=fill_out_report_kb, resize_keyboard=True)
                await bot.send_message(chat_id=callback.message.chat.id, text=f'{str(Emoji.Success)} {response.message}',
                                       reply_markup=markup)
                await state.clear()
    else:
        markup = ReplyKeyboardMarkup(keyboard=fill_out_report_kb, resize_keyboard=True)
        await bot.send_message(chat_id=callback.message.chat.id, text='Составление отчета', reply_markup=markup)
        await state.clear()


@filling_out_report_router.message(cleanup(F.text).lower() == 'загрузить данные')
@user_access
async def upload_employee_data(message: Message, state: FSMContext):
    data = await state.get_data()
    set_data = set(data)
    set_data.discard('note')
    set_report_data = set(report_data_dict)

    if set_data != set_report_data:
        message_list = []
        for element in set_report_data.difference(set_data):
            message_list.append(report_data_dict[element])

        await message.answer(f'{str(Emoji.Warning)} Заполните данные по:\n' + '\n'.join(message_list))

    else:
        response = await filling_out_report_backend.add_report_data(**data)
        if response.error:
            await message.answer(f'{str(Emoji.Error)} {response.message}')

        else:
            await filling_out_report_menu_handler(message, state)


@filling_out_report_router.message(FillingOutReportStates.enter_work_name)
@user_access
async def filling_out_work_name(message: Message, state: FSMContext):
    if message.text and cleanup(message.text).lower() == 'отмена':
        await returning_employee_menu_handler(message, state)
    else:
        await state.update_data(work_name=message.text)
        await returning_employee_menu_handler(message, state)


@filling_out_report_router.message(FillingOutReportStates.enter_actual_performance)
@user_access
async def filling_out_actual_performance(message: Message, state: FSMContext):
    if message.text and cleanup(message.text).lower() == 'отмена':
        await returning_employee_menu_handler(message, state)
    else:
        await state.update_data(actual_performance=message.text)
        await returning_employee_menu_handler(message, state)


@filling_out_report_router.message(FillingOutReportStates.enter_obtained_result)
@user_access
async def filling_out_obtained_result(message: Message, state: FSMContext):
    if message.text and cleanup(message.text).lower() == 'отмена':
        await returning_employee_menu_handler(message, state)
    else:
        await state.update_data(obtained_result=message.text)
        await returning_employee_menu_handler(message, state)


@filling_out_report_router.message(FillingOutReportStates.enter_work_plan)
@user_access
async def filling_out_work_plan(message: Message, state: FSMContext):
    if message.text and cleanup(message.text).lower() == 'отмена':
        await returning_employee_menu_handler(message, state)
    else:
        await state.update_data(work_plan=message.text)
        await returning_employee_menu_handler(message, state)


@filling_out_report_router.message(FillingOutReportStates.enter_note)
@user_access
async def filling_out_note(message: Message, state: FSMContext):
    if message.text and cleanup(message.text).lower() == 'отмена':
        await returning_employee_menu_handler(message, state)
    else:
        await state.update_data(note=message.text)
        await returning_employee_menu_handler(message, state)

