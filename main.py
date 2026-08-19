from config import BOT_TOKEN
from aiogram import Bot, Dispatcher
import asyncio

#импортирование роутеров
from handlers.users.start import router as start_router   #запуск бота
from handlers.users.profile.create import router as create_profile_router    #создание профиля

from handlers.commands.my_profile import router as my_profile_router
from handlers.users.profile.edit import router as edit_profile_router

from handlers.commands.fight_club_mode import router as fight_club_mode_router    #бойцовский клуб
from handlers.commands.safety import router as safety_router    #Безопасность
from handlers.commands.support import router as support_router    #Поддержка

async def main():
    bot = Bot(token=BOT_TOKEN)
    dp = Dispatcher()

    #подключение роутеров
    dp.include_router(start_router)    #запуск бота

    dp.include_router(create_profile_router)    #создание профиля

    dp.include_router(edit_profile_router)
    dp.include_router(my_profile_router)

    dp.include_router(fight_club_mode_router)    #бойцовский клуб
    dp.include_router(safety_router)    #безопасность
    dp.include_router(support_router)    #Поддержка


    print("Бот запущен!")
    await dp.start_polling(bot)
if __name__ == '__main__':
    asyncio.run(main())