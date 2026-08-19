from aiogram import Router, types, F
from aiogram.types import ReplyKeyboardRemove
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.types import FSInputFile

from keyboards.user_kb import buttons_support
from states.profile import ProfileStates
from states.profile import ProfileSatesSupport
from handlers.users.bug_report import send_bug_report

from data.text import Support

router = Router()

@router.message(Command('support'))
async def support(message: types.Message, state: FSMContext):
    await message.answer('Родной, что интересует?', reply_markup=types.ReplyKeyboardRemove())
    await message.answer(
        "1. Связь с разработчиком & Предложения по улчшению\n2. Как найти мою бауманскую почту?\n3. Частые вопросы\n4. Сообщить о баге\n5. Назад",
        reply_markup = buttons_support()
    )
    await state.set_state(ProfileSatesSupport.waiting_for_choice)


@router.message(ProfileSatesSupport.waiting_for_choice, ~F.text.startswith("/"))
async def waiting_for_choice(message: types.Message, state: FSMContext):
    choice = message.text

    if choice not in ["1", "2", "3", "4", "5"]:
        await message.answer("Поалуйста, выбери из предложенных вариантов")
        return

    if choice == "1":
        await message.answer(Support.Contact_the_developer)

    if choice == "2":
        await message.answer(Support.How_find_bmail, parse_mode="HTML")

    if choice == "3":
        file = FSInputFile(r"C:\Users\Alexander\PycharmProjects\dt1830\Dating_Bot\data\FAQ.docx")
        await message.answer("Вот ответы на вопросы, которые возникают чаще всего")
        await message.answer_document(file)

    if choice == "4":
        await message.answer("Опиши проблему как моно подробнее - а я передам её разработчику", reply_markup=ReplyKeyboardRemove())
        await state.set_state(ProfileSatesSupport.waiting_for_report_bug)
        return

    if choice == "5":
        await message.answer("Принял родной, если что обращайся - цифры те же", reply_markup = ReplyKeyboardRemove())
        await state.clear()


@router.message(ProfileSatesSupport.waiting_for_report_bug, ~F.text.startswith("/"))
async def process_report_bug(message: types.Message, state: FSMContext):
    bug_text = message.text.strip()

    try:
        send_bug_report(
            message.from_user.id,
            message.from_user.username,
            bug_text=bug_text,
        )
    except Exception as e:
        await message.answer("Не удалось отправить сообщение(")
        return

    await message.answer("Спасибо! Твоё сообщение передано разработчику!")
    await state.clear()