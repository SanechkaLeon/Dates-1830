from aiogram import Router, types
from aiogram.types import Message
from aiogram.filters import Command

router = Router()

@router.message(Command('fight_club_mode'))
async def fight_club_mode(message: types.Message):
    await message.answer('Режим fight club ещё в разработке..')