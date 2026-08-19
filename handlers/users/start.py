from aiogram import Router, types
from aiogram.types import Message
from aiogram.filters import Command

from keyboards.user_kb import bef_cr_pr
router = Router()

#обработка команды старт
@router.message(Command('start'))
async def cmnd_start(message: Message):
    user_id = message.from_user.id
    user_name = message.from_user.username

    welcom_text = (
        f"Привет! \n"
        f"Это бот знакомств для бомонки. Тут ты можешь найти новых друзей или вторую половинку)\n"
        f"Заполним анкету?"

    )

    await message.answer(welcom_text,  reply_markup = bef_cr_pr())