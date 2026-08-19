from aiogram import Router, types, F
from aiogram.types import ReplyKeyboardRemove, user
from aiogram.types import Message
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.types import FSInputFile

from states.profile import ProfileStatesLike

from data.faculties import UNIVERSITY_STRUCTURE
from data.grade import GRADE

from handlers.users.profile.view import render_profile
from keyboards.user_kb import all_good,  buttons_taki_no_edit_after_support, buttons_edit_after_bmail, buttons_no_edit_bio
from keyboards.user_kb import choice_grade, choice_faculty, choice_department, buttons_show_profile, buttons_keep_or_change, value_button
from states.profile import ProfileStates, ProfileStatesEdit, ProfileStatesRefillancket
from handlers.users.profile.media_collector import get_or_create_album, schedule_album_finalize

from data.text import Show_profile

from database.db import get_connection
from database.queries import create_user, update_user_media, update_user_bio, update_user_academics, get_user_profile


router = Router()


async def start_full_refill(message: Message, state: FSMContext):
    user = await get_user_profile(message.from_user.id)

    await state.update_data(
        name = user['name'],
        age = user['age'],
        gender = user['gender'],
        who_show = user['who_show'],
        grade = user['grade'],
        faculty = user['faculty'],
        department = user['department'],
        text_about = user['bio'],
        is_refill = True
    )

    await message.answer("Как тебя называть?", reply_markup=value_button(user['name']))
    await state.set_state(ProfileStates.waiting_for_name)

async def finish_full_refill(message: Message, state: FSMContext):
    data = await state.get_data()

    if data.get("is_verified_flow"):
        #анкета подтверждена
        await message.answer("Анкета обновлена!")
        await render_profile(message, tg_id=message.from_user.id)
        await message.answer(Show_profile.text_with_ancket, reply_markup=buttons_show_profile())
        await state.set_state(ProfileStatesRefillancket.waiting_for_choice)
    else:
        #анкета не подтверждена
        await message.answer("Анкета обновлена, всё верно?", reply_markup=all_good())
        await render_profile(message, tg_id=message.from_user.id)
        await state.set_state(ProfileStates.waiting_for_all_good)

async def go_to_confirmation_or_finish(message: Message, state: FSMContext, updated_text: str):
    """Решает, куда вести пользователя после сохранения правки:
    - если это редактирование УЖЕ подтверждённой анкеты (флаг is_verified_flow) -
      просто сообщаем об обновлении и возвращаем в обычное меню /myprofile,
      без повторного запроса почты.
    - если это часть первичной регистрации (флаг не стоит) - как и раньше,
      ведём в ProfileStates.waiting_for_all_good -> цепочка подтверждения почты."""
    data = await state.get_data()

    if data.get("is_verified_flow"):
        #анкета подтверждена
        await message.answer(f"{updated_text}!", reply_markup=buttons_show_profile())
        await render_profile(message, tg_id=message.from_user.id)
        await message.answer(Show_profile.text_with_ancket, reply_markup=buttons_show_profile())

        await state.set_state(ProfileStatesRefillancket.waiting_for_choice)
    else:
        #анкета не подтверждена
        await message.answer(f"{updated_text} всё верно?", reply_markup=all_good())
        await render_profile(message, tg_id=message.from_user.id)

        await state.set_state(ProfileStates.waiting_for_all_good)



@router.message(ProfileStatesEdit.waiting_for_choice, ~F.text.startswith("/"))
async def edit_after_bmail(message: Message, state: FSMContext):
    choice = message.text.strip()

    if choice == "1":
        await start_full_refill(message, state)

    if choice == "2":
        await message.answer("На каком ты курсе?",
                             reply_markup=choice_grade())
        await state.set_state(ProfileStatesRefillancket.waiting_for_grade)

    if choice == "3":
        await message.answer("Пришли до 3 фото или видео до 15 секунд",
                             reply_markup=buttons_taki_no_edit_after_support())
        await state.set_state(ProfileStatesRefillancket.waiting_for_media_replace)

    if choice == "4":
        await message.answer("Расскажи о себе и кого хочешь найти, чем предлагаешь заняться. Это поможет лучше подобрать тебе компанию", reply_markup=buttons_no_edit_bio())
        await state.set_state(ProfileStatesRefillancket.waiting_for_new_bio)

    if choice == "5":
        await message.answer("Анкета создана, всё верно?",
                             reply_markup=all_good())
        await render_profile(message, tg_id=message.from_user.id)
        await state.set_state(ProfileStates.waiting_for_all_good)


@router.message(ProfileStatesRefillancket.waiting_for_choice)
async def edit(message: Message, state: FSMContext):
    choice = message.text

    if choice == "1":
        await state.set_state(ProfileStatesLike.go_date)

    if choice == "2":
        await start_full_refill(message, state)

    if choice == "3":
        await message.answer("На каком ты курсе?",
                             reply_markup=choice_grade())
        await state.set_state(ProfileStatesRefillancket.waiting_for_grade)

    if choice == "4":
        await message.answer("Пришли до 3 фото или видео до 15 секунд",
                             reply_markup=buttons_taki_no_edit_after_support())
        await state.set_state(ProfileStatesRefillancket.waiting_for_media_replace)

    if choice == "5":
        await message.answer(
            "Расскажи о себе и кого хочешь найти, чем предлагаешь заняться. Это поможет лучше подобрать тебе компанию",
            reply_markup=buttons_no_edit_bio())
        await state.set_state(ProfileStatesRefillancket.waiting_for_new_bio)




@router.message(ProfileStatesRefillancket.waiting_for_grade, F.text)
async def replace_grade(message: Message, state: FSMContext):
    grade_values = [str(i) for i in range(1, 7)]
    if message.text not in grade_values:
        await message.answer("Пожалуйста, выбери курс из предложенных вариантов")
        return

    await state.update_data(grade=int(message.text))

    await message.answer("На каком ты факультете?",
                         reply_markup = choice_faculty())
    await state.set_state(ProfileStatesRefillancket.waiting_for_faculty)

#запрос факультета
@router.message(ProfileStatesRefillancket.waiting_for_faculty)
async def process_faculty(message: Message, state: FSMContext):
    faculty_names = [data["name"] for data in  UNIVERSITY_STRUCTURE.values()]

    if message.text not in faculty_names:
        await message.answer("Пожалуйста, выбери факультет из предложенных вариантов")
        return

    faculty_id = None
    for f_id, data in UNIVERSITY_STRUCTURE.items():
        if data["name"] == message.text:
            faculty_id = f_id
            break

    await state.update_data(
        faculty=message.text,
        faculty_id=faculty_id
    )

    await message.answer("Теперь выбери кафедру",
                         reply_markup=choice_department(faculty_id))
    await state.set_state(ProfileStatesRefillancket.waiting_for_department)

#Запрос кафедры
@router.message(ProfileStatesRefillancket.waiting_for_department, F.text)
async def process_department(message: Message, state: FSMContext):
    data = await state.get_data()
    faculty_id = data["faculty_id"]
    departments = UNIVERSITY_STRUCTURE[faculty_id]["departments"]


    if (int(message.text) not in departments):
        await message.answer("Пожаулйста, выбери кафедру из предложенных вариантов")
        return

    await state.update_data(department=message.text)
    await save_academics_only(message, state)

async def save_academics_only(message: Message, state: FSMContext):
    data = await state.get_data()

    try:
        conn = await get_connection()
        await update_user_academics(
            conn,
            tg_id=message.from_user.id,
            grade=data["grade"],
            faculty=data["faculty"],
            department=data["department"]
        )
        await conn.close()

        await go_to_confirmation_or_finish(message, state, 'Анкета обновлена')

    except Exception as e:
        await message.answer("Произошла ошибка, попроюуй ещё раз")

@router.message(ProfileStatesRefillancket.waiting_for_new_bio, F.text)
async def replace_bio(message: Message, state: FSMContext):
    new_bio = message.text.strip()

    if len(new_bio) < 10:
        await message.answer("Текст должен быть не короче 10 символов.")
        return

    try:
        conn = await get_connection()
        await update_user_bio(
            conn,
            tg_id=message.from_user.id,
            new_bio=new_bio
        )
        await conn.close()

        await go_to_confirmation_or_finish(message, state, 'Анкета обновлена')

    except Exception as e:
        await message.answer("Произошла ошибка, попробуй ещё раз(")




"""ИЗМЕНЕНИЕ МЕДИА"""
MAX_PHOTOS = 3
# Максимальная длина видео в секундах
MAX_VIDEO_DURATION = 15

async def save_media_only(message: Message, state: FSMContext):
    data = await state.get_data()

    photos = data.get("photos", [])
    video = data.get("video")

    if not photos and not video:
        await message.answer("Отпарвь хотя бы 1 фото или видео")
        return

    if len(photos) > MAX_PHOTOS:
        await message.answer(f"можно отправить максимум {MAX_PHOTOS} фото")
        await state.update_data(photos=[])
        return

    try:
        conn = await get_connection()
        await update_user_media(
            conn,
            tg_id=message.from_user.id,
            photos=photos,
            video=video
        )
        await conn.close()

        await go_to_confirmation_or_finish(message, state, 'Анкета обновлена')

    except Exception as e:
        print("Ошибка при отправке медиа")
        await message.answer("Ошибка при оправке медиа, попррбуй ещё раз")


"""ИЗМЕНЕНИЕ МЕДИА"""
@router.message(ProfileStatesRefillancket.waiting_for_media_replace, F.text)
async def replace_media_text(message: Message, state: FSMContext):
    choice = message.text.strip()
    if choice == "Оставить текущее":
        await go_to_confirmation_or_finish(message, state, 'Анкета обновлена, ')
        return

    await message.answer("Пожалуйста, отправь фото или видео, или нажми 'Оставить текущее'")

@router.message(ProfileStatesRefillancket.waiting_for_media_replace, F.photo)
async def replace_photo(message: Message, state: FSMContext):
    # Одиночное фото (не альбом) - сохраняем сразу
    data = await state.get_data()
    if data.get("video"):
        await message.answer("Нельзя смешивать фото и видео(")
        await state.update_data(photos=[], video=None)
        return

    if not message.media_group_id:
        await state.update_data(photos=[message.photo[-1].file_id], video=None)
        await save_media_only(message, state)
        return

    # Фото в составе альбома
    media_group_id = message.media_group_id
    album = get_or_create_album(media_group_id, message)
    album["photos"].append(message.photo[-1].file_id)
    album["message"] = message  # отвечаем на последнее сообщение альбома

    schedule_album_finalize(media_group_id, album, on_edit_media_ready, state)

@router.message(ProfileStatesRefillancket.waiting_for_media_replace, F.video)
async def replace_video(message: Message, state: FSMContext):
    data = await state.get_data()
    if data.get("photos"):
        await message.answer("Нельзя смешивать фото и видео(")
        await state.update_data(photos=[], video=None)
        return

    if message.video.duration > MAX_VIDEO_DURATION:
        await message.answer(f"Длина видео максимум {MAX_VIDEO_DURATION} секунд(")
        return

    if not message.media_group_id:
        await state.update_data(photos=[], video=message.video.file_id)
        await save_media_only(message, state)
        return

    media_group_id = message.media_group_id
    album= get_or_create_album(media_group_id, message)
    album["videos"].append({
        "file_id": message.video.file_id,
        "duration": message.video.duration
    })
    album["message"] = message
    schedule_album_finalize(media_group_id, album, on_edit_media_ready, state)

async def on_edit_media_ready(photos, videos, answer_msg, state: FSMContext):
    print(f"🔵 on_edit_media_ready: photos={len(photos)}, videos={len(videos)}")  # ← добавить

    if photos and videos:
        await answer_msg.answer("Нельзя смешивать фото и видео( Выбери что-то одно")
        await state.update_data(photos=photos, video=None)
        return

    if videos:
        if len(videos) > 1:
            await answer_msg.answer("Можно отправить только 1 видео")
            return

        video = videos[0]
        if video["duration"] > MAX_VIDEO_DURATION:
            await answer_msg.answer("Длина видео максимум 15 секунд(")
            return

        await state.update_data(photos=[], video=video["file_id"])
        await save_media_only(answer_msg, state)
        return

    if len(photos) > MAX_PHOTOS:
        await answer_msg.answer("Можно отправить максимум 3 фото")
        return

    if photos:
        await state.update_data(photos=photos, video=None)
        await save_media_only(answer_msg, state)
        return
"""ИЗМЕНЕНИЕ МЕДИА"""