from aiogram import Router, F, Bot
from aiogram.types import Message, InputMediaPhoto, InputMediaVideo, BackgroundTypeWallpaper
from aiogram.fsm.context import FSMContext

from keyboards.user_kb import buttons_no_candidates, buttons_reaction, buttons_waiting_match
from states.profile import (
    ProfileStatesLike,
    ProfileStatesRefillancket,
    ProfileStatesWaitingMatch,
    LikeStates,
)

from database.db import get_connection
from database.queries import (
    get_next_candidate,
    get_user_by_id,
    get_user_media,
    save_reaction,
    check_mutual_like,
    create_match,
    get_user_profile,
)
from data.text import Show_profile, WaitingMatch
from handlers.users.profile.view import show_profile

router = Router()


def _build_album(media, caption: str = None):
    album = []
    for item in media:
        if item["file_type"] == "photo":
            album.append(InputMediaPhoto(media=item['file_id']))
        else:
            album.append(InputMediaVideo(media=item['file_id']))
    if not album:
        return None
    if caption:
        album[0].caption = caption
    return album


def _profile_caption(user) -> str:
    return(
        f"{user['name']}, {user['age']}\n"
        f"{user['grade']} курс, {user['faculty']}{user['department']}\n\n"
        f"{user['bio']}"
    )


async def _show_next_candidate(message: Message, state: FSMContext, viewer_id: int):
    conn = await get_connection()
    candidate = await get_next_candidate(conn, viewer_id)

    if candidate is None:
        await conn.close()
        await state.update_data(viewer_id=viewer_id)
        await message.answer("Анкеты закончились( Начнёшь смотреть заново или заглянешь попозже?",
                             reply_markup=buttons_no_candidates())
        await state.set_state(LikeStates.waiting_no_candidates_choice)
        return

    media = await get_user_media(candidate['id'])
    await conn.close()

    album = _build_album(media, caption=_profile_caption(candidate))
    if album:
        await message.answer_media_group(media=album)
    else:
        await message.answer(_profile_caption(candidate))

    await message.answer("Что скажешь?", reply_markup=buttons_reaction())

    await state.update_data(viewer_id=viewer_id, current_candidate=candidate['id'])

    await state.set_state(LikeStates.viewing)


@router.message(ProfileStatesLike.go_date)
async def start_browsing(message: Message, state: FSMContext):
    viewer = await get_user_profile(message.from_user.id)
    if viewer is None:
        await message.answer("Анкета не найдена, заполни её через /start")
        return

    await message.answer("Таки погнали сомтреть акнеты!")
    await _show_next_candidate(message, state, viewer['id'])






#Анкеты закончились
@router.message(LikeStates.waiting_no_candidates_choice, F.text == "Заново")
async def restart_browsing(message: Message, state: FSMContext):
    data = await state.get_data()
    viewer_id = data["viewer_id"]
    await _show_next_candidate(message, state, viewer_id)

@router.message(LikeStates.waiting_no_candidates_choice, F.text == "Попозже")
async def postpone_browsing(message: Message, state: FSMContext):
    await message.answer("Окей, подождём. пока твою анкету кто-то увидит",
                         reply_markup=buttons_waiting_match())
    await message.answer(WaitingMatch.text_menu)
    await state.set_state(ProfileStatesWaitingMatch.waiting_for_choice)

@router.message(LikeStates.waiting_no_candidates_choice)
async def handle_no_candidates(message: Message, state: FSMContext):
    await message.answer("Выбери один из вариантов на клавиатуре 🙏")



#Ожидание метча
@router.message(ProfileStatesWaitingMatch.waiting_for_choice, F.text == "1")
async def waiting_match_browse_again(message: Message, state: FSMContext):
    data = await state.get_data()
    viewer_id = data.get("viewer_id")
    if viewer_id is None:
        viewer = await get_user_profile(message.from_user.id)
        viewer_id = viewer['id']
    await _show_next_candidate(message, state, viewer_id)


@router.message(ProfileStatesWaitingMatch.waiting_for_choice, F.text == "2")
async def waiting_match_show_profile(message: Message, state: FSMContext):
    await show_profile(message, tg_id=message.from_user.id, state=state, show_verification=True)


@router.message(ProfileStatesWaitingMatch.waiting_for_choice, F.text == "3")
async def waiting_choice(message: Message, state: FSMContext):
    pass