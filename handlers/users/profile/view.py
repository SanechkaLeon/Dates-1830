from aiogram.types import Message, InlineKeyboardMarkup, InputMedia, InputMediaPhoto, InputMediaVideo
from aiogram.types import ReplyKeyboardRemove, KeyboardButton
from data.text import Show_profile
from aiogram.fsm.context import FSMContext
from states.profile import ProfileStatesVerifier, ProfileStatesRefillancket
from keyboards.user_kb import buttons_show_profile, buttons_conf_or_no

from database.db import get_connection
from database.queries import render_profile

async def show_profile(message: Message, tg_id:int, state: FSMContext, show_verification: bool = True):

    result = await render_profile(message, tg_id)

    if result is None:
        return

    user, media = result

    if user['is_verifier']:
        await message.answer(Show_profile.text_with_ancket, reply_markup=buttons_show_profile())
        await state.update_data(is_verified_flow=True)
        await state.set_state(ProfileStatesRefillancket.waiting_for_choice)
    else:
        await message.answer("Но анкета не подтверждена, нашёл свою бауманскую почту?", reply_markup=buttons_conf_or_no())
        await state.set_state(ProfileStatesVerifier.waiting_for_choice)

