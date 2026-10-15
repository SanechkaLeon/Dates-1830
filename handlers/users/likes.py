from aiogram import Router, F, Bot
from aiogram.types import Message, InputMediaPhoto, InputMediaVideo, BackgroundTypeWallpaper
from aiogram.fsm.context import FSMContext
from datetime import datetime

from keyboards.user_kb import (
    buttons_no_candidates,
    buttons_reaction,
    buttons_waiting_match,
    buttons_liked_notice,
    buttons_show_profile,
)
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
    get_pending_liker,
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
        f"{user['name']}, {user['age']},"
        f" {user['grade']}{user['faculty']}{user['department']} - "
        f"{user['bio']}"
    )

async def _send_live_like_content(sender, message_type: str, message_text: str, message_file_id: str):
    """sender — либо message (для answer_*), либо (bot, chat_id) пара — см. вызовы ниже."""
    if message_type == "text":
        await sender(message_text)


async def _show_next_candidate(message: Message, state: FSMContext, viewer_id: int):
    data = await state.get_data()
    since_raw = data.get('rewatch_since')
    since = datetime.fromisoformat(since_raw) if since_raw else None

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

    await state.update_data(viewer_id=viewer_id, current_candidate=candidate['id'])

    await state.set_state(LikeStates.viewing)


async def _check_pending_like(message: Message, state: FSMContext, viewer_id: int) -> bool:
    conn = await get_connection()
    liker = await get_pending_liker(conn, viewer_id)
    await conn.close()

    if liker is None:
        return False

    await state.update_data(
        viewer_id=viewer_id,
        pending_liker_id=liker['id'],
        pending_liker_type=liker['type_attraction'],
        pending_liker_message_type=liker['message_type'],
        pending_liker_message_text=liker['message_text'],
        pending_liker_message_file_id=liker['message_file_id'],
    )

    if liker['type_attraction'] == 'live_like':
        text = "Тебе поставили живой лайк, посмотрим?\n\n1. Газ\n2. Не хочу никого искать"
    else:
        text = "Ты понравился одному человеку, показать?\n\n1. Показать\n2. Больше не хочу никого искать"

    await message.answer(text, reply_markup=buttons_liked_notice())
    await state.set_state(LikeStates.waiting_liked_notice_choice)
    return True


@router.message(ProfileStatesLike.go_date)
async def start_browsing(message: Message, state: FSMContext):
    viewer = await get_user_profile(message.from_user.id)
    if viewer is None:
        await message.answer("Анкета не найдена, заполни её через /start")
        return

    await state.update_data(rewatch_since=None)

    if await _check_pending_like(message, state, viewer['id']):
        return True

    await message.answer("Таки погнали сомтреть акнеты!", reply_markup=buttons_reaction())
    await _show_next_candidate(message, state, viewer['id'])


#Уведомление о лайк
@router.message(LikeStates.waiting_liked_notice_choice, F.text == "1")
async def show_pending_like(message: Message, state: FSMContext):
    data = await state.get_data()
    viewer_id = data["viewer_id"]
    liker_id = data["pending_liker_id"]
    msg_type = data.get("pending_liker_message_type")
    msg_text = data.get("pending_liker_message_text")
    msg_file_id = data.get("pending_liker_message_file_id")

    conn = await get_connection()
    liker = await get_user_by_id(conn, liker_id)
    media = await get_user_media(liker_id)
    await conn.close()

    album = _build_album(media, caption=_profile_caption(liker))
    if album:
        await message.answer_media_group(media=album)
    else:
        await message.answer(_profile_caption(liker))

    await message.answer("Ну чё как оно?", reply_markup=buttons_reaction())

    await state.update_data(current_candidate=liker_id)
    await state.set_state(LikeStates.viewing)

@router.message(LikeStates.waiting_liked_notice_choice, F.text == "2")
async def decline_pending_liker(message: Message, state: FSMContext):
    pass  # пока не обрабатываем

@router.message(LikeStates.waiting_liked_notice_choice)
async def handle_liked_notice_wrong_text(message: Message):
    await message.answer("Выбери один из вариантов на клавиатуре 🙏")




#Реакции на анкету
@router.message(LikeStates.viewing, F.text == "👎")
async def handle_dislike(message: Message, state: FSMContext):
    data = await state.get_data()
    viewer_id = data["viewer_id"]
    candidate_id = data["current_candidate"]

    conn = await get_connection()
    await save_reaction(conn, viewer_id, candidate_id, "dislike")
    await conn.close()

    await _show_next_candidate(message, state, viewer_id)



@router.message(LikeStates.viewing, F.text == "❤️")
async def handle_like(message: Message, state: FSMContext, bot: Bot):
    data = await state.get_data()
    viewer_id = data["viewer_id"]
    candidate_id = data["current_candidate"]

    conn = await get_connection()
    await save_reaction(conn, viewer_id, candidate_id, "like")
    mutual = await check_mutual_like(conn, viewer_id, candidate_id)

    if mutual:
        await create_match(conn, viewer_id, candidate_id)
        viewer = await get_user_by_id(conn, viewer_id)
        candidate = await get_user_by_id(conn,candidate_id)
        viewer_media = await get_user_media(viewer_id)
        candidate_media = await get_user_media(candidate_id)
        await conn.close()

        await message.answer("О май гад, это взаимно!")
        album = _build_album(candidate_media, caption=_profile_caption(candidate))

        if album:
            await message.answer_media_group(media=album)
        else:
            await message.answer(_profile_caption(candidate))

        try:
            await bot.send_message(candidate["tg_id"], "💘 Это взаимно! У тебя мэтч!")
            candidate_album = _build_album(candidate_media, caption=_profile_caption(viewer))

            if candidate_album:
                await bot.send_media_group(candidate["tg_id"], media=candidate_album)
            else:
                await bot.send_message(candidate['tg_id'], _profile_caption(viewer))

        except Exception:
            pass
    else:
        await conn.close()

    await _show_next_candidate(message, state, viewer_id)



@router.message(LikeStates.viewing, F.text == "💌📹🎤")
async def handle_live_like(message: Message, state: FSMContext):
    data = await state.get_data()
    candidate_id = data["current_candidate"]

    await state.update_data(live_like_target_id=candidate_id)

    await message.answer("Отправь текстовое, голосовое или видео-сообщение (до 15 секунд) — оно уйдёт вместе с лайком 🔥")
    await state.set_state(LikeStates.waiting_live_like_message)

@router.message(LikeStates.viewing, F.text == "💤")
async def handle_live_like(message: Message, state: FSMContext):
    await message.answer("Спокойной ночи! Возвращайся, когда захочешь посмотреть ещё анкеты 😴",
        reply_markup=buttons_show_profile()
                         )
    await message.answer(Show_profile.text_with_ancket)
    await state.set_state(ProfileStatesRefillancket.waiting_for_choice)


@router.message(LikeStates.viewing)
async def handle_viewing_wrong_text(message: Message):
    await message.answer("Выбери один из вариантов на клавиатуре 🙏")


async def _process_live_like(message: Message, state: FSMContext, bot: Bot,
                             message_type:str, message_text:str, message_file_id: str):
    data = await state.get_data()
    viewer_id = data["viewer_id"]
    candidate_id = data["live_like_target_id"]

    conn = await get_connection()
    await save_reaction(conn, viewer_id, candidate_id, "live_like",
                        message_type, message_text, message_file_id)
    mutual = await check_mutual_like(conn, viewer_id, candidate_id)

    viewer = await get_user_by_id(conn, viewer_id)
    candidate = await get_user_by_id(conn, candidate_id)
    viewer_media = await get_user_media(viewer_id)

    if mutual:
        await create_match(conn, viewer_id, candidate_id)
        viewer = await get_user_by_id(conn, viewer_id)
        candidate = await get_user_by_id(conn, candidate_id)
        viewer_media = await get_user_media(viewer_id)
        await conn.close()

    await conn.close()

    try:
        await bot.send_message(candidate["tg_id"], f"Тебе живой лайк от {viewer['name']}!")
        album = _build_album(viewer_media, caption=_profile_caption(viewer))

        if album:
            await bot.send_media_group(viewer["tg_id"], media=album)
        else:
            await bot.send_message(viewer['tg_id'], _profile_caption(viewer))

        if message_type == "text":
            await bot.send_message(candidate['tg_id'], message_text)
        elif message_type == "voice":
            await bot.send_voice(candidate['tg_id'], message_file_id)
        elif message_type == "video_note":
            await bot.send_video_note(candidate['tg_id'], message_file_id)
        elif message_type == "video":
            await bot.send_video(candidate['tg_id'], message_file_id)

    except Exception:
        pass

        await bot.send_message(candidate['tg_id'], "💘 Кстати, это взаимно — у тебя мэтч! 🎉")

    else:
        await conn.close()
        await message.answer("Живой лайк отправлен!")

    await _show_next_candidate(message, state, viewer_id)


@router.message(LikeStates.waiting_live_like_message, F.text)
async def handle_live_like_text(message: Message, state: FSMContext, bot: Bot):
    await _process_live_like(message, state, bot, "text", message.text, None)


@router.message(LikeStates.waiting_live_like_message, F.voice)
async def handle_live_like_voice(message: Message, state: FSMContext, bot: Bot):
    await _process_live_like(message, state, bot, "voice", None, message.voice.file_id)


@router.message(LikeStates.waiting_live_like_message, F.video_note)
async def handle_live_like_video_note(message: Message, state: FSMContext, bot: Bot):
    if message.video_note.duration and message.video_note.duration > 15:
        await message.answer("Кружок должен быть до 15 секунд, отправь другой")
        return
    await _process_live_like(message, state, bot, "video_note", None, message.video_note.file_id)


@router.message(LikeStates.waiting_live_like_message, F.video)
async def handle_live_like_video(message: Message, state: FSMContext, bot: Bot):
    if message.video.duration and message.video.duration > 15:
        await message.answer("Видео должно быть до 15 секунд, отправь другое")
        return
    await _process_live_like(message, state, bot, "video", None, message.video.file_id)


@router.message(LikeStates.waiting_live_like_message)
async def handle_live_like_wrong_type(message: Message):
    await message.answer("Пришли, пожалуйста, текст, голосовое или видео (до 15 секунд) 🙏")

#Анкеты закончились
@router.message(LikeStates.waiting_no_candidates_choice, F.text == "Заново")
async def restart_browsing(message: Message, state: FSMContext):
    data = await state.get_data()
    viewer_id = data["viewer_id"]

    conn = await get_connection()
    now = await conn.fetchval("SELECT NOW()::timestamp")

    await state.update_data(rewatch_since=now.isoformat())
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