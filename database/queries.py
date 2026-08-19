from aiogram.types import Message, InlineKeyboardMarkup, InputMedia, InputMediaPhoto, InputMediaVideo
from database.db import get_connection

async def create_user(conn, data: dict):
    print("=== СОЗДАНИЕ ПОЛЬЗОВАТЕЛЯ ===")
    print("data:", data)
    print("==============================")


    user = await conn.fetchrow(
        """
        INSERT INTO users(
            id, tg_id, name, age, gender, who_show, grade, faculty, department, 
            bio, mail, is_verifier, code_verification, code_expires, role
        )
        VALUES (DEFAULT, $1, $2, $3, $4, $5, $6, $7, $8, $9, $10, $11, $12, $13, $14)
        RETURNING id
        """,
        data["tg_id"],
        data['name'],
        int(data['age']),
        data['gender'],
        data['who_show'],
        data['grade'],
        data['faculty'],
        data['department'],
        data['text_about'],
        None,   # mail
        False,  # is_verifier
        None,   # code_verification
        None,   # code_expires
        data['role']
    )

    user_id = user['id']

    if data.get("photos"):
        for photo_id in data['photos']:
            await conn.execute(
                "INSERT INTO media(user_id, file_id, file_type) VALUES ($1, $2, 'photo')",
                user_id, photo_id
    )

    if data.get("video"):
        await conn.execute(
            "INSERT INTO media(user_id, file_id, file_type) VALUES ($1, $2, 'video')",
            user_id, data['video']
        )


async def confirm_user_email(conn, tg_id, email, confirmation_code: str, is_verifier: bool):

    print("=== СОЗДАНИЕ ПОЛЬЗОВАТЕЛЯ ===")
    print("подтверждение анкеты", tg_id, email, confirmation_code, is_verifier)
    print("==============================")

    await conn.execute(
        """
        UPDATE users 
        SET mail = $1, code_verification = $2, is_verifier = $3 
        WHERE tg_id = $4
        """,
        email, confirmation_code, is_verifier, tg_id
    )


async def get_user_profile(tg_id: int):
    conn = await get_connection()

    user = await conn.fetchrow(
        """
        SELECT id, tg_id, name, age, gender, who_show, grade, 
        faculty, department, bio, mail, is_verifier, role
        FROM users
        WHERE tg_id = $1    
        """,
        tg_id
    )
    await conn.close()
    return user


async def get_user_media(user_id: int):
    conn = await get_connection()

    media = await conn.fetch(
        """
            SELECT id, file_id, file_type
            FROM media 
            WHERE user_id = $1
            
        """,
        user_id
    )
    await conn.close()
    return media


async def render_profile(message: Message, tg_id: int):
    conn = await get_connection()

    user = await conn.fetchrow(
        """
        SELECT id, tg_id, name, age, gender, who_show,
        grade, faculty, department,
        bio,
        mail, is_verifier,role
        FROM users
        WHERE tg_id = $1
        """,
        tg_id
    )

    if not user:
        await message.answer("Твоя анкета не найдена. Заполни её через команду /start")
        await conn.close()
        return

    media = await conn.fetch(
        """
        SELECT id, file_id, file_type
        FROM media
        WHERE user_id = $1
        ORDER BY id ASC 
        """,
        user['id']
    )

    await conn.close()

    profile_text = (
        f"{user['name']}, {user['age']}, "
        f"{user['grade']}{user['faculty']}{user['department']} - {user['bio']}"
    )

    if media:
        album = []
        for item in media:
            if item['file_type'] == 'photo':
                album.append(InputMediaPhoto(media=item['file_id']))
            else:
                album.append(InputMediaVideo(media=item['file_id']))

        if album:
            album[0].caption = profile_text

            await message.answer_media_group(media=album)

    return user, media


async def replace_user_media(conn, user_id: int, photos: list, video: str):
    await conn.execute("DELETE FROM media WHERE user_id = $1", user_id)

    if photos:
        for photo_id in photos:
            await conn.execute(
                "INSERT INTO media(user_id, file_id, file_type) VALUES ($1, $2, 'photo')",
                user_id, photo_id
            )

    if video:
        await conn.execute(
            "INSERT INTO media(user_id, file_id, file_type) VALUES ($1, $2, 'video')",
            user_id, video
        )

async def update_user_media(conn, tg_id: int, photos: list, video: str = None):
    user = await conn.fetchrow(
        "SELECT id FROM users WHERE tg_id = $1",
        tg_id
    )

    if not user:
        raise ValueError(f"Пользователь {tg_id} не найден")

    user_id = user['id']

    await conn.execute(
        "DELETE FROM media WHERE user_id = $1 ",
        user_id
    )

    if photos:
        for photo_id in photos:
            await conn.execute(
                "INSERT INTO media(user_id, file_id, file_type) VALUES ($1, $2, 'photo')",
                user_id, photo_id
            )
    if video:
        await conn.execute(
            "INSERT INTO media(user_id, file_id, file_type) VALUES ($1, $2, 'video')",
            user_id, video
        )

    return user


async def update_user_bio(conn, tg_id:int , new_bio: str):
    await conn.execute(
        """
        UPDATE users 
        SET bio = $1 
        WHERE tg_id = $2
        """,
        new_bio, tg_id
    )

async def update_user_academics(conn, tg_id:int, grade: int, faculty: str, department: str):
    await conn.execute(
        """
        UPDATE users 
        SET grade = $1, faculty = $2, department = $3
        WHERE tg_id = $4
        """,
        grade, faculty, department, tg_id
    )

async def update_user_basic_info(conn, tg_id:int, name:str, age:int, gender:str, who_show:str):
    await conn.execute(
        """
        UPDATE users 
        SET name = $1, age = $2, gender = $3, who_show = $4
        WHERE tg_id = $5
        """,
        name, age, gender, who_show, tg_id
    )