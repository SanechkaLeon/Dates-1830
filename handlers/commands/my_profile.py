from aiogram import Router, types, F
from aiogram.types import Message, ReplyKeyboardRemove
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext

from data.text import Show_profile
from handlers.users.profile.view import show_profile
from states.profile import ProfileStates, ProfileStatesLike, ProfileStatesVerifier, ProfileStatesRefillancket
from states.profile import ProfileStatesVerifier


from keyboards.user_kb import choice_grade, buttons_taki_no_edit_after_support, buttons_no_edit_bio
from keyboards.user_kb import buttons_show_profile


router = Router()

@router.message(Command('myprofile'))
async def my_profile(message: Message, state: FSMContext):
    await message.answer("Так выглядит твоя анкета:")
    await show_profile(message, tg_id=message.from_user.id, state=state, show_verification=True)


@router.message(ProfileStatesVerifier.waiting_for_choice)
async def waiting_for_choice(message: types.Message, state: FSMContext):
    choice = message.text.strip()

    if choice not in ["Нашёл, го подтверждать", "Нет, подтвердим потом"]:
        await message.answer("Поалуйста, выбери из предложенных вариантов")
        return

    if choice == "Нашёл, го подтверждать":
        await message.answer("Найсс, таки кидай почту", reply_markup=ReplyKeyboardRemove())
        await state.set_state(ProfileStates.waiting_for_bmail)

    if choice == "Нет, подтвердим потом":
        await message.answer("Услышал родной. Если что, продолжить подтверждение всё также по команде /myprofile", reply_markup = ReplyKeyboardRemove())
        await state.clear()