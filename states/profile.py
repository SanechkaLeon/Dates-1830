from aiogram.fsm.state import State, StatesGroup

#fsm для создания профиля
class ProfileStates(StatesGroup):
    waiting_for_name = State() #Шаг имени
    waiting_for_age = State()  # Шаг возраста

    waiting_for_gender = State() #Шаг выбора пола
    waiting_for_who_show = State() #Шаг кого показывать

    waiting_for_grade = State() #Шаг курса
    waiting_for_faculty = State() #Шаг факультета
    waiting_for_department = State() #Шаг кафедры

    waiting_for_text_about = State() #Шаг текста о себе
    waiting_for_media = State() #Шаг медиа

    waiting_for_all_good = State()

    waiting_for_bmail_or_support = State() #Шаг почту или поддержки

    waiting_for_bmail = State() #Шаг бимейла
    waiting_for_conf_code = State() #Шаг подтвержждения кода

class ProfileStatesSafety(StatesGroup):
    waiting_for_choice = State() #Шаг выбора

class ProfileSatesSupport(StatesGroup):
    waiting_for_choice = State() #Шаг выбора ответа
    waiting_for_report_bug = State()

class ProfileStatesVerifier(StatesGroup):
    waiting_for_choice = State()

class ProfileStatesLike(StatesGroup):
    go_date = State()

class ProfileStatesEdit(StatesGroup):
    waiting_for_choice = State()

class ProfileStatesRefillancket(StatesGroup):
    """ПЕРЕЗАПОЛНЕНИЕ АНКЕТЫ"""
    waiting_for_name = State()  # Шаг имени
    waiting_for_age = State()  # Шаг возраста

    waiting_for_gender = State()  # Шаг выбора пола
    waiting_for_who_show = State()  # Шаг кого показывать

    waiting_for_grade = State()  # Шаг курса
    waiting_for_faculty = State()  # Шаг факультета
    waiting_for_department = State()  # Шаг кафедры

    waiting_for_text_about = State()  # Шаг текста о себе
    waiting_for_media_replace = State()  # Шаг медиа
    """ПЕРЕЗАПОЛНЕНИЕ АНКЕТЫ"""

    waiting_for_choice = State()

    waiting_for_all_good = State()
    waiting_for_new_bio = State()
    waiting_for_grade = State()