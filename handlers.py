from aiogram import Router, F, Bot
from aiogram.types import Message, CallbackQuery
from aiogram.filters import CommandStart, Command
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup

from config import CATEGORIES, REGIONS, ADMIN_ID
from database import db
from keyboards import (
    main_menu_kb, usta_menu_kb, category_kb,
    region_kb, ustalar_kb, usta_detail_kb,
    rating_kb, confirm_kb
)

router = Router()


# ========== STATES ==========

class UstaRoyxat(StatesGroup):
    ism = State()
    telefon = State()
    kategoriya = State()
    tuman = State()
    tajriba = State()

class BuyurtmaState(StatesGroup):
    kategoriya = State()
    tuman = State()
    tavsif = State()


# ========== START ==========

@router.message(CommandStart())
async def start(message: Message, state: FSMContext):
    await state.clear()
    await db.foydalanuvchi_qoshish(message.from_user.id, message.from_user.full_name)
    
    usta = await db.usta_olish(message.from_user.id)
    
    if usta:
        await message.answer(
            f"Xush kelibsiz, usta {usta['ism']}! 👷\n"
            f"Reytingiz: ⭐ {usta['reyting']} ({usta['baholashlar']} baho)\n"
            f"Tumaningiz: {REGIONS.get(usta['tuman'], usta['tuman'])}",
            reply_markup=usta_menu_kb()
        )
    else:
        await message.answer(
            "Assalomu alaykum! 👋\n\n"
            "Men <b>Usta Topish</b> botiman.\n"
            "Santexnik, elektrik, duradgor va boshqa ustalarni tez toping!\n\n"
            "Quyidagi tugmalardan birini tanlang:",
            reply_markup=main_menu_kb(),
            parse_mode="HTML"
        )


# ========== USTA TOPISH ==========

@router.message(F.text == "🔍 Usta topish")
async def usta_topish(message: Message, state: FSMContext):
    await state.set_state(BuyurtmaState.kategoriya)
    await message.answer(
        "Qanday usta kerak? Kategoriyani tanlang:",
        reply_markup=category_kb()
    )


@router.callback_query(F.data.startswith("cat_"), BuyurtmaState.kategoriya)
async def kategoriya_tanlandi(callback: CallbackQuery, state: FSMContext):
    kategoriya = callback.data.replace("cat_", "")
    await state.update_data(kategoriya=kategoriya)
    await state.set_state(BuyurtmaState.tuman)
    await callback.message.edit_text(
        f"Tanlandi: {CATEGORIES[kategoriya]}\n\nQaysi tumanda? Tumanni tanlang:",
        reply_markup=region_kb("reg")
    )


@router.callback_query(F.data.startswith("reg_"), BuyurtmaState.tuman)
async def tuman_tanlandi(callback: CallbackQuery, state: FSMContext):
    tuman = callback.data.replace("reg_", "")
    await state.update_data(tuman=tuman)
    await state.set_state(BuyurtmaState.tavsif)
    await callback.message.edit_text(
        f"Tuman: {REGIONS[tuman]}\n\n"
        "Muammoni qisqacha yozing:\n"
        "(masalan: 'Kranlar suv o'tkazmayapti' yoki 'Rozetka almashtirilsin')"
    )


@router.message(BuyurtmaState.tavsif)
async def tavsif_kiritildi(message: Message, state: FSMContext, bot: Bot):
    data = await state.get_data()
    kategoriya = data["kategoriya"]
    tuman = data["tuman"]
    tavsif = message.text

    ustalar = await db.ustalar_topish(kategoriya, tuman)

    if not ustalar:
        await state.clear()
        await message.answer(
            f"❌ Afsuski, {REGIONS[tuman]} da {CATEGORIES[kategoriya]} topilmadi.\n\n"
            "Tez orada qo'shamiz! Admin bilan bog'laning: @admin_username",
            reply_markup=main_menu_kb()
        )
        return

    buyurtma_id = await db.buyurtma_qoshish(
        message.from_user.id,
        message.from_user.full_name,
        kategoriya, tuman, tavsif
    )
    await state.update_data(buyurtma_id=buyurtma_id)

    matn = f"✅ {len(ustalar)} ta usta topildi!\n\nBaho bo'yicha saralangan:\n\n"
    for u in ustalar:
        yulduz = "⭐" * int(u["reyting"])
        matn += f"👷 <b>{u['ism']}</b>\n"
        matn += f"   {yulduz} {u['reyting']} baho | {u['tajriba']} yil tajriba\n\n"

    await message.answer(matn, reply_markup=ustalar_kb(ustalar), parse_mode="HTML")
    await state.set_state(None)


@router.callback_query(F.data.startswith("usta_"))
async def usta_tanlandi(callback: CallbackQuery, state: FSMContext):
    usta_id = int(callback.data.replace("usta_", ""))
    data = await state.get_data()
    buyurtma_id = data.get("buyurtma_id", 0)

    ustalar = await db.barcha_ustalar()
    usta = next((u for u in ustalar if u["id"] == usta_id), None)

    if not usta:
        await callback.answer("Usta topilmadi!")
        return

    matn = (
        f"👷 <b>{usta['ism']}</b>\n\n"
        f"📱 Telefon: <code>{usta['telefon']}</code>\n"
        f"🔧 Mutaxassislik: {CATEGORIES.get(usta['kategoriya'], usta['kategoriya'])}\n"
        f"📍 Tuman: {REGIONS.get(usta['tuman'], usta['tuman'])}\n"
        f"⭐ Reyting: {usta['reyting']} ({usta['baholashlar']} baho)\n"
        f"💼 Tajriba: {usta['tajriba']} yil\n\n"
        "Shu ustani chaqirasizmi?"
    )
    await callback.message.edit_text(
        matn,
        reply_markup=usta_detail_kb(usta_id, buyurtma_id),
        parse_mode="HTML"
    )


@router.callback_query(F.data.startswith("chaqir_"))
async def usta_chaqirildi(callback: CallbackQuery, bot: Bot):
    parts = callback.data.split("_")
    usta_id = int(parts[1])
    buyurtma_id = int(parts[2]) if len(parts) > 2 else 0

    ustalar = await db.barcha_ustalar()
    usta = next((u for u in ustalar if u["id"] == usta_id), None)

    if not usta:
        await callback.answer("Xatolik!")
        return

    await db.buyurtma_yangilash(buyurtma_id, usta_id, "qabul_qilindi")

    # Ustaga xabar yuborish
    try:
        buyurtma = await db.buyurtma_olish(buyurtma_id)
        if buyurtma:
            await bot.send_message(
                usta["telegram_id"],
                f"🔔 <b>Yangi buyurtma!</b>\n\n"
                f"👤 Mijoz: {buyurtma['mijoz_ism']}\n"
                f"📋 Muammo: {buyurtma['tavsif']}\n"
                f"📍 Tuman: {REGIONS.get(buyurtma['tuman'], buyurtma['tuman'])}\n\n"
                f"Mijoz siz bilan bog'lanadi!",
                parse_mode="HTML"
            )
    except Exception:
        pass

    await callback.message.edit_text(
        f"✅ Zo'r! {usta['ism']} usta bilan bog'laning:\n\n"
        f"📱 <code>{usta['telefon']}</code>\n\n"
        f"Ish tugagandan so'ng ustani baholashni unutmang! 🌟",
        parse_mode="HTML"
    )

    # 1 soatdan so'ng baho so'rash (oddiy variant)
    await callback.message.answer(
        "Ish tugadimi? Ustani baholang:",
        reply_markup=rating_kb(usta_id, buyurtma_id)
    )


# ========== BAHO BERISH ==========

@router.callback_query(F.data.startswith("baho_"))
async def baho_berildi(callback: CallbackQuery, bot: Bot):
    parts = callback.data.split("_")
    usta_id = int(parts[1])
    buyurtma_id = int(parts[2])
    baho = int(parts[3])

    await db.usta_reyting_yangilash(usta_id, baho)
    await db.buyurtma_yangilash(buyurtma_id, usta_id, "bajarildi")

    yulduz = "⭐" * baho
    await callback.message.edit_text(
        f"Rahmat! Sizning bahoyingiz: {yulduz}\n\n"
        "Usta reytingi yangilandi! 🙏"
    )

    # Ustaga ham xabar
    ustalar = await db.barcha_ustalar()
    usta = next((u for u in ustalar if u["id"] == usta_id), None)
    if usta:
        try:
            await bot.send_message(
                usta["telegram_id"],
                f"🌟 Mijoz sizga {baho}/5 baho berdi! {yulduz}\n"
                f"Yangi reytingiz ko'rilmoqda..."
            )
        except Exception:
            pass


# ========== USTA RO'YXATDAN O'TISH ==========

@router.message(F.text == "👷 Usta sifatida ro'yxatdan o'tish")
async def usta_royxat_boshlash(message: Message, state: FSMContext):
    mavjud = await db.usta_olish(message.from_user.id)
    if mavjud:
        await message.answer(
            "Siz allaqachon usta sifatida ro'yxatdansiz! ✅",
            reply_markup=usta_menu_kb()
        )
        return
    await state.set_state(UstaRoyxat.ism)
    await message.answer(
        "Usta sifatida ro'yxatdan o'tish!\n\n"
        "Ismingizni kiriting (to'liq ism):"
    )


@router.message(UstaRoyxat.ism)
async def usta_ism(message: Message, state: FSMContext):
    await state.update_data(ism=message.text)
    await state.set_state(UstaRoyxat.telefon)
    await message.answer("📱 Telefon raqamingizni kiriting:\n(Misol: +998901234567)")


@router.message(UstaRoyxat.telefon)
async def usta_telefon(message: Message, state: FSMContext):
    await state.update_data(telefon=message.text)
    await state.set_state(UstaRoyxat.kategoriya)
    await message.answer(
        "🔧 Mutaxassisligingizni tanlang:",
        reply_markup=category_kb()
    )


@router.callback_query(F.data.startswith("cat_"), UstaRoyxat.kategoriya)
async def usta_kategoriya(callback: CallbackQuery, state: FSMContext):
    kategoriya = callback.data.replace("cat_", "")
    await state.update_data(kategoriya=kategoriya)
    await state.set_state(UstaRoyxat.tuman)
    await callback.message.edit_text(
        f"Tanlandi: {CATEGORIES[kategoriya]}\n\nQaysi tumanda ishlaysiz?",
        reply_markup=region_kb("ureg")
    )


@router.callback_query(F.data.startswith("ureg_"), UstaRoyxat.tuman)
async def usta_tuman(callback: CallbackQuery, state: FSMContext):
    tuman = callback.data.replace("ureg_", "")
    await state.update_data(tuman=tuman)
    await state.set_state(UstaRoyxat.tajriba)
    await callback.message.edit_text(
        f"Tuman: {REGIONS[tuman]}\n\nNecha yil tajribangiz bor? (faqat raqam):"
    )


@router.message(UstaRoyxat.tajriba)
async def usta_tajriba(message: Message, state: FSMContext, bot: Bot):
    if not message.text.isdigit():
        await message.answer("Iltimos, faqat raqam kiriting!")
        return

    data = await state.get_data()
    tajriba = int(message.text)

    muvaffaqiyat = await db.usta_qoshish(
        message.from_user.id,
        data["ism"], data["telefon"],
        data["kategoriya"], data["tuman"], tajriba
    )

    await state.clear()

    if muvaffaqiyat:
        await message.answer(
            f"✅ Tabriklaymiz, {data['ism']}!\n\n"
            f"Siz ro'yxatdan o'tdingiz:\n"
            f"🔧 {CATEGORIES[data['kategoriya']]}\n"
            f"📍 {REGIONS[data['tuman']]}\n"
            f"💼 {tajriba} yil tajriba\n\n"
            "Buyurtmalar kelganda xabar beramiz! 🔔",
            reply_markup=usta_menu_kb()
        )
        # Adminga xabar
        try:
            await bot.send_message(
                ADMIN_ID,
                f"👷 Yangi usta ro'yxatdan o'tdi!\n\n"
                f"Ism: {data['ism']}\n"
                f"Tel: {data['telefon']}\n"
                f"Mutaxassislik: {CATEGORIES[data['kategoriya']]}\n"
                f"Tuman: {REGIONS[data['tuman']]}\n"
                f"Tajriba: {tajriba} yil"
            )
        except Exception:
            pass
    else:
        await message.answer(
            "Siz allaqachon ro'yxatdansiz!",
            reply_markup=usta_menu_kb()
        )


# ========== PROFIL ==========

@router.message(F.text == "📊 Mening profilim")
async def profil(message: Message):
    usta = await db.usta_olish(message.from_user.id)
    if not usta:
        await message.answer("Siz usta sifatida ro'yxatdan o'tmagansiz!")
        return

    yulduz = "⭐" * int(usta["reyting"])
    await message.answer(
        f"👷 <b>Sizning profilingiz</b>\n\n"
        f"Ism: {usta['ism']}\n"
        f"📱 Telefon: {usta['telefon']}\n"
        f"🔧 Mutaxassislik: {CATEGORIES.get(usta['kategoriya'], '-')}\n"
        f"📍 Tuman: {REGIONS.get(usta['tuman'], '-')}\n"
        f"💼 Tajriba: {usta['tajriba']} yil\n"
        f"⭐ Reyting: {usta['reyting']} {yulduz}\n"
        f"📊 Baholashlar soni: {usta['baholashlar']}",
        parse_mode="HTML"
    )


# ========== BUYURTMALAR TARIXI ==========

@router.message(F.text == "📋 Mening buyurtmalarim")
async def buyurtmalar_tarixi(message: Message):
    buyurtmalar = await db.mijoz_buyurtmalari(message.from_user.id)
    if not buyurtmalar:
        await message.answer(
            "Sizda hali buyurtma yo'q.\n"
            "Usta topish uchun '🔍 Usta topish' tugmasini bosing!",
            reply_markup=main_menu_kb()
        )
        return

    matn = "📋 <b>Sizning buyurtmalaringiz:</b>\n\n"
    for b in buyurtmalar:
        holat_emoji = {"yangi": "🆕", "qabul_qilindi": "✅", "bajarildi": "🏁"}.get(b["holat"], "❓")
        matn += (
            f"{holat_emoji} {CATEGORIES.get(b['kategoriya'], b['kategoriya'])}\n"
            f"   📍 {REGIONS.get(b['tuman'], b['tuman'])}\n"
            f"   📝 {b['tavsif'][:40]}...\n\n"
        )
    await message.answer(matn, parse_mode="HTML")


# ========== ADMIN ==========

@router.message(Command("admin"))
async def admin_panel(message: Message):
    if message.from_user.id != ADMIN_ID:
        return
    stat = await db.statistika()
    await message.answer(
        f"👑 <b>Admin panel</b>\n\n"
        f"👷 Ustalar: {stat['ustalar']}\n"
        f"📋 Buyurtmalar: {stat['buyurtmalar']}\n"
        f"👤 Foydalanuvchilar: {stat['foydalanuvchilar']}",
        parse_mode="HTML"
    )


# ========== YORDAM ==========

@router.message(F.text == "ℹ️ Yordam")
async def yordam(message: Message):
    await message.answer(
        "ℹ️ <b>Qo'llanma</b>\n\n"
        "🔍 <b>Usta topish</b> — Kerakli ustani toping\n"
        "👷 <b>Ro'yxatdan o'tish</b> — Usta sifatida qo'shiling\n"
        "📋 <b>Buyurtmalarim</b> — Tariхingizni ko'ring\n\n"
        "Muammo bo'lsa admin bilan bog'laning: @admin_username",
        parse_mode="HTML"
    )
