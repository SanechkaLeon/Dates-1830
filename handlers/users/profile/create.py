import asyncio
from typing import Dict, Any

from aiogram import Router, F
from aiogram.types import Message
from aiogram.fsm.context import FSMContext
from aiogram.types import ReplyKeyboardRemove
from typing_inspection.typing_objects import is_self

from handlers.users.profile.edit import finish_full_refill
from states.profile import ProfileStates, ProfileStatesLike, ProfileStatesEdit

from keyboards.user_kb import choice_gender, bmail_or_support, buttons_conf_or_no, buttons_edit_after_bmail, buttons_keep_or_change
from keyboards.user_kb import choice_who_show, value_button
from data.faculties import UNIVERSITY_STRUCTURE
from data.grade import GRADE
from keyboards.user_kb import choice_grade
from keyboards.user_kb import choice_faculty
from keyboards.user_kb import choice_department
from keyboards.user_kb import all_good
from keyboards.user_kb import buttons_go_date

from data.text import Step_bmail, Show_profile

from handlers.users.profile.confirmation import send_email
from handlers.users.profile.view import render_profile, show_profile
from handlers.users.profile.media_collector import get_or_create_album, schedule_album_finalize

from database.db import get_connection
from database.queries import create_user, confirm_user_email, update_user_basic_info, update_user_academics, update_user_bio, update_user_media

router = Router()

#Нчало регистрации
@router.message(F.text == "Конечно!")
async def start_registration(message: Message, state: FSMContext):
    await state.set_state(ProfileStates.waiting_for_name)
    await message.answer("Как тебя называть?",
                         reply_markup = ReplyKeyboardRemove())


#запрос имени
@router.message(ProfileStates.waiting_for_name)
async def process_name(message: Message, state: FSMContext):
    data = await state.get_data()
    is_refill = data.get("is_refill", False)

    if not (is_refill and message.text.strip() == "Оставить текущее"):
        await state.update_data(name = message.text.strip())

    data =  await state.get_data()

    if is_refill:
        await message.answer("Скольео тебе лет?",
                             reply_markup = value_button(data["age"]))
    else:
        await message.answer("Сколько тебе лет?")
    await state.set_state(ProfileStates.waiting_for_age)


#запрос возраста
@router.message(ProfileStates.waiting_for_age)
async def process_age(message: Message, state: FSMContext):
    age = int(message.text)
    if (age < 16 and age > 100):
        await message.answer("Пожалуйста, введи корректный возраст")
        return
    await state.update_data(age=message.text)

    await state.set_state(ProfileStates.waiting_for_gender)
    await message.answer("Теперь определимся с полом:",
                         reply_markup = choice_gender())


#запрос пола
@router.message(ProfileStates.waiting_for_gender)
async def process_gender(message: Message, state: FSMContext):
    if (message.text not in ["Я парень", "Я девушка"]):
        await message.answer("Пожалуйста, выбери пол из предложенных вариантов")
        return
    await state.update_data(gender=message.text)

    await state.set_state(ProfileStates.waiting_for_who_show)
    data = await state.get_data()
    await message.answer("Кого показывать?",
                         reply_markup = choice_who_show(data["gender"]))


#Запрос кого показывать
@router.message(ProfileStates.waiting_for_who_show)
async def process_who_show(message: Message, state: FSMContext):
    data = await state.get_data()
    gender = data["gender"]

    if (message.text not in ["Девушек", "Парней", "Всё равно"]):
        await message.answer("Пожалуйста, выбери из предложенных вариантов")
        return
    await state.update_data(who_show=message.text)

    # Убираем старые кнопки и отправляем новые
    await message.answer(
        "На каком ты курсе?",
        reply_markup=choice_grade()  # Новая клавиатура с курсами
    )
    await state.set_state(ProfileStates.waiting_for_grade)


#Запрос курса
@router.message(ProfileStates.waiting_for_grade)
async def process_grade(message: Message, state: FSMContext):
    data = await state.get_data()
    grade = [data for data in GRADE.values()]

    if (message.text not in grade):
        await message.answer("Пожалуйста, выбери курс из предложенных вариантов")
        return

    await state.update_data(grade=int(message.text))

    await message.answer("На каком ты факультете?",
                         reply_markup = choice_faculty())
    await state.set_state(ProfileStates.waiting_for_faculty)


#запрос факультета
@router.message(ProfileStates.waiting_for_faculty)
async def process_faculty(message: Message, state: FSMContext):
    faculty_names = [data["name"] for data in  UNIVERSITY_STRUCTURE.values()]
    print("Хэндлер кафедры сработал")
    if (message.text not in faculty_names):
        await message.answer("Пожалуйста, выбери факультет из предложенных вариантов")
        return

    faculty_id = None
    faculty_name = message.text
    for f_id, data in UNIVERSITY_STRUCTURE.items():
        if (data["name"] == faculty_name):
            faculty_id = f_id
            break

    if not faculty_id:
        await message.answer("Пожалуйста, выбери факультет кнопкой")

    await state.update_data(
        faculty=message.text,
        faculty_id=faculty_id
    )

    data = await state.get_data()
    faculty_id = data["faculty_id"]

    await state.set_state(ProfileStates.waiting_for_department)
    await message.answer("Теперь выбери кафедру",
                         reply_markup=choice_department(faculty_id))


#Запрос кафедры
@router.message(ProfileStates.waiting_for_department)
async def process_department(message: Message, state: FSMContext):
    #получение списока с названиями кафедр
    data = await state.get_data()
    faculty_id = data["faculty_id"]
    departments = UNIVERSITY_STRUCTURE[faculty_id]["departments"]


    if (int(message.text) not in departments):
        await message.answer("Пожаулйста, выбери кафедру из предложенных вариантов")
        return

    department_id = None
    for d_id, dep_name in UNIVERSITY_STRUCTURE.items():
        if (dep_name == message.text):
            department_id = d_id
            break

    await state.update_data(
        department=message.text,
        department_id = department_id
    )

    data = await state.get_data()
    department_id = data["department_id"]

    await state.set_state(ProfileStates.waiting_for_text_about)
    await message.answer("Расскажи о себе и кого хочешь найти, чем предлагаешь заняться. Это поможет лучше подобрать тебе компанию)",
                         reply_markup = ReplyKeyboardRemove())


#Запрос текста о себе
@router.message(ProfileStates.waiting_for_text_about)
async def process_text_about(message: Message, state: FSMContext):
    data = await state.get_data()

    if data.get("is_refill") and message.text.strip() == "Оставить текущее":
        pass
    else:
        await state.update_data(text_about=message.text.strip())

    await message.answer("Пришли до трёх фото или запиши видео(до 15 сек). \nАнкеты, где видно лицо, собирают больше лайков❤️",reply_markup = buttons_keep_or_change())
    await state.set_state(ProfileStates.waiting_for_media)


@router.message(ProfileStates.waiting_for_media, F.text == "Оставить текущее")
async def keep_current_media(message: Message, state: FSMContext):
    data = await state.get_data()

    if not data.get("is_refill"):
        return

    await save_profile(message, state)


# ============================================================
# Обработка медиа (фото / видео / альбомы)
# ============================================================

# Максимум фото в анкете
MAX_PHOTOS = 3
# Максимальная длина видео в секундах
MAX_VIDEO_DURATION = 15

async def on_registration_media_ready(photos, videos, answer_msg, state: FSMContext):

    # Фото + видео в одном альбоме - запрещено. Не важно, сколько видео
    # и какой они длины - если в альбоме есть и фото, и видео, анкета
    # не сохраняется вообще.
    if photos and videos:
        await answer_msg.answer(
            "Нельзя смешивать фото и видео! Пришли до 3 фото или одно видео."
        )
        return

    # Только видео
    if videos:
        if len(videos) > 1:
            await answer_msg.answer(
                "Можно отправить только одно видео! Попробуй ещё раз."
            )
            return

        video = videos[0]
        if video["duration"] > MAX_VIDEO_DURATION:
            await answer_msg.answer(
                f"Длина видео максимум {MAX_VIDEO_DURATION} секунд! Попробуй ещё раз."
            )
            return

        await state.update_data(photos=[], video=video["file_id"])
        await save_profile(answer_msg, state)
        return

    # Только фото, но их больше 3
    if len(photos) > MAX_PHOTOS:
        await answer_msg.answer(
            f"Можно отправить максимум {MAX_PHOTOS} фото! Попробуй ещё раз."
        )
        return

    # 1-3 фото - сохраняем
    if photos:
        await state.update_data(photos=photos, video=None)
        await save_profile(answer_msg, state)
        return


@router.message(ProfileStates.waiting_for_media, F.photo)
async def process_photo(message: Message, state: FSMContext):
    # Одиночное фото (не альбом) - сохраняем сразу
    if not message.media_group_id:
        await state.update_data(photos=[message.photo[-1].file_id], video=None)
        await save_profile(message, state)
        return

    # Фото в составе альбома
    media_group_id = message.media_group_id
    album = get_or_create_album(media_group_id, message)
    album["photos"].append(message.photo[-1].file_id)
    album["message"] = message  # отвечаем на последнее сообщение альбома

    schedule_album_finalize(media_group_id, album, on_registration_media_ready, state)


@router.message(ProfileStates.waiting_for_media, F.video)
async def process_video(message: Message, state: FSMContext):
    # Одиночное видео (не альбом) - проверяем длину сразу и сохраняем
    if not message.media_group_id:
        if message.video.duration > MAX_VIDEO_DURATION:
            await message.answer(f"Длина видео максимум {MAX_VIDEO_DURATION} секунд! Попробуй ещё раз.")
            return

        await state.update_data(photos=[], video=message.video.file_id)
        await save_profile(message, state)
        return

    # Видео в составе альбома (например, отправлено вместе с фото).
    # Важно: регистрируем видео в альбоме независимо от его длины,
    # чтобы при финализации можно было корректно определить смешивание
    # фото и видео. Проверку длины откладываем до финализации альбома -
    # иначе слишком длинное видео "выпадает" из альбома и смешивание
    # с фото остаётся незамеченным.
    media_group_id = message.media_group_id
    album = get_or_create_album(media_group_id, message)
    album["videos"].append(message.video.file_id)
    if message.video.duration > MAX_VIDEO_DURATION:
        album["invalid_video"] = True
    album["message"] = message

    schedule_album_finalize(media_group_id, album, on_registration_media_ready, state)


async def save_profile(message: Message, state: FSMContext):
    data = await state.get_data()

    photos = data.get("photos", [])
    video = data.get("video")

    # Проверка на смешивание (на всякий случай)
    if photos and video:
        await message.answer("Нельзя смешивать фото и видео! Выбери что-то одно.")
        await state.update_data(photos=[], video=None)
        return

    # Проверка на наличие медиа
    if not photos and not video:
        await message.answer("Отправь хотя бы 1 фото или видео")
        return

    # Проверка на превышение лимита фото
    if len(photos) > MAX_PHOTOS:
        await message.answer(f"Можно отправить максимум {MAX_PHOTOS} фото! Отправь заново.")
        await state.update_data(photos=[])
        return

    # === ОТЛАДКА ===
    print("=== СОХРАНЕНИЕ ПРОФИЛЯ ===")
    print("data:", data)
    print("photos:", photos)
    print("video:", video)
    print("==========================")

    try:
        conn = await get_connection()

        if data.get("is_refill"):
            async with conn.transaction():
                await update_user_basic_info(
                    conn, tg_id=message.from_user.id,
                    name=data["name"], age=int(data["age"]),
                    gender=data["gender"], who_show=data["who_show"],
                )
                await update_user_academics(
                    conn, tg_id=message.from_user.id,
                    grade=data["grade"],
                    faculty=data["faculty"],
                    department=data["department"],
                )
                await update_user_bio(
                    conn, tg_id=message.from_user.id,
                    new_bio=data["text_about"],
                )
                await update_user_media(
                    conn, tg_id=message.from_user.id,
                    photos=photos, video=video,
                )

            await conn.close()
            await finish_full_refill(message, state)
            return

        await create_user(conn, {
            "tg_id": message.from_user.id,
            "name": data["name"],
            "age": data["age"],
            "gender": data["gender"],
            "who_show": data["who_show"],
            "grade": data["grade"],
            "faculty": data["faculty"],
            "department": data["department"],
            "text_about": data["text_about"],
            "photos": photos,
            "video": video,
            "role": "user"
        })

        await conn.close()

        await message.answer("Анкета создана! Всё верно?",
                             reply_markup=all_good())
        #Показ анкеты
        await render_profile(message, tg_id=message.from_user.id)

        await state.set_state(ProfileStates.waiting_for_all_good)

    except Exception as e:
        print(f"Ошибка при сохранении: {e}")
        await message.answer("Произошла ошибка при создании анкеты. Попробуй еще раз.")


@router.message(ProfileStates.waiting_for_all_good)
async def edit_after_bmail(message: Message, state: FSMContext):
    choice = message.text

    if choice not in ["Изменить анкету", "Да, газ знакомиться"]:
        await message.answer("Пожалуйста, выбери из предложенных вариантов")
        return

    if choice == "Да, газ знакомиться":
        await message.answer(Step_bmail.aft_conf_ancket,
                             reply_markup=ReplyKeyboardRemove())
        await message.answer(Step_bmail.bmail_or_support,
                             reply_markup=bmail_or_support())
        await state.set_state(ProfileStates.waiting_for_bmail_or_support)

    if choice == "Изменить анкету":
        await message.answer(Show_profile.text_edit_after_bmail,
                             reply_markup=buttons_edit_after_bmail())
        await state.set_state(ProfileStatesEdit.waiting_for_choice)

"""#Первичный показ анкеты
@router.message(ProfileStates.waiting_for_all_good, F.text == "Да, газ знакомиться")
async def process_first_show(message: Message, state: FSMContext):
    await message.answer(Step_bmail.aft_conf_ancket, reply_markup=ReplyKeyboardRemove())
    await message.answer(Step_bmail.bmail_or_support, reply_markup=bmail_or_support())
    await state.set_state(ProfileStates.waiting_for_bmail_or_support)"""



@router.message(ProfileStates.waiting_for_bmail_or_support, ~F.text.startswith("/"))
async def process_bmail_or_support(message: Message, state: FSMContext):

    choice = message.text

    if choice not in ["Да, знаю", "Воспользуюсь командой /support"]:
        await message.answer("Поалуйста, выбери из предложенных вариантов")
        return

    if choice == "Да, знаю":
        await message.answer("Найссс, тогда кидай почту",
                             reply_markup=ReplyKeyboardRemove())
        await state.set_state(ProfileStates.waiting_for_bmail)

    if choice == "Воспользуюсь командой /support":
        await message.answer("Окей, тогда как найдёшь почту, вспользуйся командой /myprofile, чтобы продолжить заполнение анкеты",
                             reply_markup=ReplyKeyboardRemove())
        await state.clear()


#Получение бауманской почты
@router.message(ProfileStates.waiting_for_bmail, ~F.text.startswith("/"))
async def process_confirm(message: Message, state: FSMContext):
    bmail = message.text.strip()

    if "@" not in bmail or not bmail.endswith("@student.bmstu.ru"):
        await message.answer("Пожалуйста, пришли корректную вузовскую почту\n(...@student.bmstu.ru)")
        return

    try:
        code = send_email(bmail)
    except Exception as e:
        print("Ошибка при отправке письма)")
        return

    await state.update_data(email=bmail, confirmation_code = code)

    await message.answer("Код отправлен на почту! Введи его сюда")
    await state.set_state(ProfileStates.waiting_for_conf_code)


@router.message(ProfileStates.waiting_for_conf_code, ~F.text.startswith("/"))
async def process_conf_code(message: Message, state: FSMContext):
    entered_code = message.text.strip()

    data = await state.get_data()
    correct_code = data["confirmation_code"]
    email = data.get("email")

    if entered_code != correct_code:
        await message.answer("Код неверный. Попробуй ещё раз")
        return

    confirm_data = {
        "tg_id": message.from_user.id,
        "email": email,
        "confirmation_code": correct_code,
        "is_verifier": True
    }

    print("confirm_data:", confirm_data)

    conn = await get_connection()
    await confirm_user_email(
        conn,
        tg_id=confirm_data["tg_id"],
        email=confirm_data["email"],
        confirmation_code=confirm_data["confirmation_code"],
        is_verifier=confirm_data["is_verifier"]
    )
    await conn.close()

    await message.answer("Почта подтверждена! Анкета опубликована! Таки идём знакомиться?",
                         reply_markup=buttons_go_date())
    await state.set_state(ProfileStatesLike.go_date)