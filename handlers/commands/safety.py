from aiogram import Router, types
from aiogram.types import ReplyKeyboardRemove
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext

from keyboards.user_kb import buttons_safety
from states.profile import ProfileStatesSafety

from data.text import Safety

router = Router()

@router.message(Command('safety'))
async def safety(message: types.Message, state: FSMContext):
    await message.answer('Родной, что интересует?', reply_markup=types.ReplyKeyboardRemove())
    await message.answer(
        "1. Защита данных\n2. Почему подтверждение именно по почте?\n3. Советы по безопасному общению\n4. Назад",
        reply_markup=buttons_safety()
    )
    await state.set_state(ProfileStatesSafety.waiting_for_choice)

@router.message(ProfileStatesSafety.waiting_for_choice)
async def process_safety_choice(message: types.Message, state: FSMContext):
    choice = message.text.strip()

    if choice not in ("1", "2", "3", "4"):
        await message.answer("Пожалуйста, Выбери один из предложенных вариантов")
        return

    if choice == "1":
        await message.answer(Safety.safety_rules)

    if choice == "2":
        await message.answer(Safety.why_conf_on_bmail)

    if choice == "3":
        await message.answer(Safety.tips_on_safe_communication)

    if choice == "4":
        await message.answer("Принял родной, если что обращайся - цифры те же", reply_markup=ReplyKeyboardRemove())
        await state.clear()
