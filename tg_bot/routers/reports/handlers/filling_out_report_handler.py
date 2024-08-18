from aiogram import Router, F
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import StatesGroup, State
from aiogram.types import Message, ReplyKeyboardMarkup, CallbackQuery

from tg_bot.functions import cleanup
from tg_bot.routers.reports.backend import filling_out_report_backend
from tg_bot.routers.reports.keyboard import fill_out_report_kb, generate_inline_kb_for_employees_list, \
    fill_out_employee_report_kb
from tg_bot.security import user_access
from tg_bot.settings import bot
from tg_bot.static.emojis import Emoji

filling_out_report_router = Router()


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
    employee_id = data['employee_id']
    response = await filling_out_report_backend.get_employee_by_id(employee_id)
    markup = ReplyKeyboardMarkup(keyboard=fill_out_employee_report_kb, resize_keyboard=True)
    await message.answer(f'{response.value.full_name}, заполните информацию:', reply_markup=markup)


@filling_out_report_router.message(cleanup(F.text).lower() == 'наименование работ в соответствии с тз')
@user_access
async def filling_out_employee_work_name(message: Message, state: FSMContext):
    await message.answer('Введите наименование работ в соответствии с тз / Отмена')
    await state.set_state(FillingOutReportStates.enter_work_name)


@filling_out_report_router.message(cleanup(F.text).lower() == 'фактическое выполнение работы за отчетный период')
@user_access
async def filling_out_employee_actual_performance(message: Message, state: FSMContext):
    await message.answer('Введите фактическое выполнение работы за отчетный период / Отмена')
    await state.set_state(FillingOutReportStates.enter_actual_performance)


@filling_out_report_router.message(cleanup(F.text).lower() == 'полученный результат (вид отчетности)')
@user_access
async def filling_out_employee_obtained_result(message: Message, state: FSMContext):
    await message.answer('Введите полученный результат (вид отчетности) / Отмена')
    await state.set_state(FillingOutReportStates.enter_obtained_result)


@filling_out_report_router.message(cleanup(F.text).lower() == 'план работ на следующую неделю')
@user_access
async def filling_out_employee_work_plan(message: Message, state: FSMContext):
    await message.answer('Введите план работ на следующую неделю / Отмена')
    await state.set_state(FillingOutReportStates.enter_work_plan)


@filling_out_report_router.message(cleanup(F.text).lower() == 'примечание')
@user_access
async def filling_out_employee_note(message: Message, state: FSMContext):
    await message.answer('Введите примечание / Отмена')
    await state.set_state(FillingOutReportStates.enter_note)


@filling_out_report_router.message(FillingOutReportStates.enter_work_name)
@user_access
async def filling_out_work_name(message: Message, state: FSMContext):
    data = await state.get_data()
    employee_id = data['employee_id']
    if message.text and cleanup(message.text).lower() == 'отмена':
        await returning_employee_menu_handler(message, state)
    else:
        # response = ''
        # if response.error:
        #     await message.answer(f'{str(Emoji.Error)} {response.message}')
        # else:

        await returning_employee_menu_handler(message, state)
        await message.answer(f'{employee_id} наименование работ')


@filling_out_report_router.message(FillingOutReportStates.enter_actual_performance)
@user_access
async def filling_out_actual_performance(message: Message, state: FSMContext):
    data = await state.get_data()
    employee_id = data['employee_id']
    if message.text and cleanup(message.text).lower() == 'отмена':
        await returning_employee_menu_handler(message, state)
    else:
        # response = ''
        # if response.error:
        #     await message.answer(f'{str(Emoji.Error)} {response.message}')
        # else:

        await returning_employee_menu_handler(message, state)
        await message.answer(f'{employee_id} фактическое выполнение')


@filling_out_report_router.message(FillingOutReportStates.enter_obtained_result)
@user_access
async def filling_out_obtained_result(message: Message, state: FSMContext):
    data = await state.get_data()
    employee_id = data['employee_id']
    if message.text and cleanup(message.text).lower() == 'отмена':
        await returning_employee_menu_handler(message, state)
    else:
        # response = ''
        # if response.error:
        #     await message.answer(f'{str(Emoji.Error)} {response.message}')
        # else:

        await returning_employee_menu_handler(message, state)
        await message.answer(f'{employee_id} полученный результат')


@filling_out_report_router.message(FillingOutReportStates.enter_work_plan)
@user_access
async def filling_out_work_plan(message: Message, state: FSMContext):
    data = await state.get_data()
    employee_id = data['employee_id']
    if message.text and cleanup(message.text).lower() == 'отмена':
        await returning_employee_menu_handler(message, state)
    else:
        # response = ''
        # if response.error:
        #     await message.answer(f'{str(Emoji.Error)} {response.message}')
        # else:

        await returning_employee_menu_handler(message, state)
        await message.answer(f'{employee_id} план работ')


@filling_out_report_router.message(FillingOutReportStates.enter_note)
@user_access
async def filling_out_note(message: Message, state: FSMContext):
    data = await state.get_data()
    employee_id = data['employee_id']
    if message.text and cleanup(message.text).lower() == 'отмена':
        await returning_employee_menu_handler(message, state)
    else:
        # response = ''
        # if response.error:
        #     await message.answer(f'{str(Emoji.Error)} {response.message}')
        # else:

        await returning_employee_menu_handler(message, state)
        await message.answer(f'{employee_id} примечание')

