from aiogram.types import ReplyKeyboardMarkup, KeyboardButton, InlineKeyboardMarkup
from aiogram.types import ReplyKeyboardRemove
from aiogram.utils import keyboard

from data.faculties import  UNIVERSITY_STRUCTURE
from data.grade import GRADE

#перед заполнением анкеты
def bef_cr_pr():
    return ReplyKeyboardMarkup(
        keyboard=[  [KeyboardButton(text = "Конечно!")]  ],
        resize_keyboard=True
    )

# кнопка выбор пола
def choice_gender():
    return ReplyKeyboardMarkup(
        keyboard= [
            [KeyboardButton(text = "Я парень"),
             KeyboardButton(text = "Я девушка") ]
        ],
        resize_keyboard=True
    )

def choice_who_show(gender: str):
    if (gender == "Я парень"):
        return ReplyKeyboardMarkup(
            keyboard=[
                [KeyboardButton(text="Девушек"),
                 KeyboardButton(text="Парней"),
                 KeyboardButton(text="Всё равно")]
            ],
            resize_keyboard=True
        )
    else:
        return ReplyKeyboardMarkup(
            keyboard=[
                [KeyboardButton(text="Парней"),
                 KeyboardButton(text="Девушек"),
                 KeyboardButton(text="Всё равно")]
            ],
            resize_keyboard=True
        )

def choice_grade():
    buttons = []
    row = []

    for i, data in enumerate(GRADE.values(), start=1):
        row.append(KeyboardButton(text = data))
        if (i % 3 == 0):
            buttons.append(row)
            row = []

    if row:
        buttons.append(row)

    return ReplyKeyboardMarkup(
        keyboard = buttons,
        resize_keyboard=True
    )

# кнопка выбор факультета
def choice_faculty():
    buttons = []
    row = []

    for i, data in enumerate(UNIVERSITY_STRUCTURE.values(), start=1):
        row.append(KeyboardButton(text = data["name"]))

        if (i % 3 == 0):
            buttons.append(row)
            row = []

    return ReplyKeyboardMarkup(
        keyboard = buttons,
        resize_keyboard=True
    )

#кнопка выбора кафедры
def choice_department(faculty_id: int):
    buttons = []
    row = []

    departments = UNIVERSITY_STRUCTURE[faculty_id]["departments"]

    for i, dept in enumerate(departments, start=1):
        row.append(KeyboardButton(text = str(dept)))

        if (i % 4 == 0):
            buttons.append(row)
            row = []

    return ReplyKeyboardMarkup(
        keyboard = buttons,
        resize_keyboard=True
    )


def all_good():
    return ReplyKeyboardMarkup(
        keyboard= [
            [KeyboardButton(text = "Да, газ знакомиться")],
            [KeyboardButton(text = "Изменить анкету")]
        ],
        resize_keyboard = True
    )

def bmail_or_support():
    return ReplyKeyboardMarkup(
        keyboard= [
            [KeyboardButton(text = "Да, знаю")], [KeyboardButton(text = "Воспользуюсь командой /support")],
        ],
        resize_keyboard=True
    )

def buttons_safety():
    return ReplyKeyboardMarkup(
        keyboard= [
            [KeyboardButton(text = "1"), KeyboardButton(text = "2"), KeyboardButton(text = "3"), KeyboardButton(text = "4")],
        ],
        resize_keyboard=True
    )

def buttons_support():
    return ReplyKeyboardMarkup(
        keyboard= [
        [KeyboardButton(text = "1"), KeyboardButton(text = "2"), KeyboardButton(text = "3"), KeyboardButton(text = "4"),],
        [KeyboardButton(text = "5")],
        ],
        resize_keyboard=True
    )


def buttons_show_profile():
    return ReplyKeyboardMarkup(
        keyboard= [
            [KeyboardButton(text = "1🚀"), KeyboardButton(text = "2"), KeyboardButton(text = "3"), KeyboardButton(text = "4"), KeyboardButton(text = "5")],
        ],
        resize_keyboard=True
    )

def buttons_conf_or_no():
    return ReplyKeyboardMarkup(
        keyboard= [
            [KeyboardButton(text = "Нашёл, го подтверждать")],
            [KeyboardButton(text = "Нет, подтвердим потом")],
        ],
        resize_keyboard=True
    )

def buttons_go_date():
    return ReplyKeyboardMarkup(
        keyboard= [
            [KeyboardButton(text = "Таки да!")],
        ],
        resize_keyboard=True
    )

def buttons_keep_or_change():
    return ReplyKeyboardMarkup(
        keyboard= [
            [KeyboardButton(text="Оставить текущее")]
        ],
        resize_keyboard=True
    )

def value_button(current_value):
    return ReplyKeyboardMarkup(
        keyboard= [
            [KeyboardButton(text=str(current_value))],
        ],
        resize_keyboard=True
    )

def buttons_edit_after_bmail():
    return ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="1"), KeyboardButton(text="2"), KeyboardButton(text="3"), KeyboardButton(text="4"), ],
            [KeyboardButton(text="5")],
        ],
        resize_keyboard=True
    )

def buttons_taki_no_edit_after_support():
    return ReplyKeyboardMarkup(
        keyboard= [
            [KeyboardButton(text="Оставить текущее")]
        ],
        resize_keyboard=True
    )

def buttons_no_edit_bio():
    return ReplyKeyboardMarkup(
        keyboard= [
            [KeyboardButton(text="Назад")]
        ],
        resize_keyboard=True
    )
