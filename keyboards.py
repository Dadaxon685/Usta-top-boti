from aiogram.types import (
    ReplyKeyboardMarkup, KeyboardButton,
    InlineKeyboardMarkup, InlineKeyboardButton
)
from config import CATEGORIES, REGIONS


def main_menu_kb():
    return ReplyKeyboardMarkup(keyboard=[
        [KeyboardButton(text="🔍 Usta topish")],
        [KeyboardButton(text="📋 Mening buyurtmalarim")],
        [KeyboardButton(text="👷 Usta sifatida ro'yxatdan o'tish")],
        [KeyboardButton(text="ℹ️ Yordam")],
    ], resize_keyboard=True)


def usta_menu_kb():
    return ReplyKeyboardMarkup(keyboard=[
        [KeyboardButton(text="📊 Mening profilim")],
        [KeyboardButton(text="📬 Yangi buyurtmalar")],
        [KeyboardButton(text="🔍 Usta topish")],
        [KeyboardButton(text="ℹ️ Yordam")],
    ], resize_keyboard=True)


def category_kb():
    buttons = []
    row = []
    for key, val in CATEGORIES.items():
        row.append(InlineKeyboardButton(text=val, callback_data=f"cat_{key}"))
        if len(row) == 2:
            buttons.append(row)
            row = []
    if row:
        buttons.append(row)
    return InlineKeyboardMarkup(inline_keyboard=buttons)


def region_kb(prefix="reg"):
    buttons = []
    row = []
    for key, val in REGIONS.items():
        row.append(InlineKeyboardButton(text=val, callback_data=f"{prefix}_{key}"))
        if len(row) == 2:
            buttons.append(row)
            row = []
    if row:
        buttons.append(row)
    return InlineKeyboardMarkup(inline_keyboard=buttons)


def ustalar_kb(ustalar):
    buttons = []
    for u in ustalar:
        yulduz = "⭐" * int(u["reyting"])
        buttons.append([InlineKeyboardButton(
            text=f"{u['ism']} — {yulduz} ({u['reyting']})",
            callback_data=f"usta_{u['id']}"
        )])
    buttons.append([InlineKeyboardButton(text="🔙 Orqaga", callback_data="back_main")])
    return InlineKeyboardMarkup(inline_keyboard=buttons)


def usta_detail_kb(usta_id, buyurtma_id):
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(
            text="✅ Shu ustani chaqirish",
            callback_data=f"chaqir_{usta_id}_{buyurtma_id}"
        )],
        [InlineKeyboardButton(text="🔙 Boshqa ustalar", callback_data="back_ustalar")],
    ])


def rating_kb(usta_id, buyurtma_id):
    buttons = [[
        InlineKeyboardButton(text=str(i), callback_data=f"baho_{usta_id}_{buyurtma_id}_{i}")
        for i in range(1, 6)
    ]]
    return InlineKeyboardMarkup(inline_keyboard=buttons)


def confirm_kb(prefix):
    return InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text="✅ Ha", callback_data=f"{prefix}_ha"),
            InlineKeyboardButton(text="❌ Yo'q", callback_data=f"{prefix}_yoq"),
        ]
    ])
