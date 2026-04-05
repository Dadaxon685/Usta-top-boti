# Usta Topish Bot 🔧

O'zbekiston uchun usta topish Telegram boti. Santexnik, elektrik, duradgor va boshqa ustalarni tez toping!

## O'rnatish

### 1. Kutubxonalarni o'rnatish
```bash
pip install -r requirements.txt
```

### 2. Bot tokenini olish
1. Telegramda @BotFather ga yozing
2. /newbot buyrug'ini yuboring
3. Bot nomini kiriting
4. Token oling

### 3. config.py ni tahrirlash
```python
BOT_TOKEN = "bu_yerga_tokeningizni_qoying"
ADMIN_ID = 123456789  # Sizning Telegram ID'ingiz
```
Telegram ID'ingizni bilish uchun @userinfobot ga /start yuboring.

### 4. Botni ishga tushirish
```bash
python bot.py
```

## Railway'ga deploy qilish

1. GitHub'ga push qiling
2. Railway.app da yangi project oching
3. GitHub repo'ni ulang
4. Environment variable qo'shing: `BOT_TOKEN=tokeningiz`
5. Deploy!

## Fayllar tuzilmasi

```
usta_bot/
├── bot.py          # Asosiy fayl
├── config.py       # Sozlamalar
├── database.py     # SQLite baza
├── handlers.py     # Barcha handlerlar
├── keyboards.py    # Tugmalar
└── requirements.txt
```

## Imkoniyatlar

- ✅ Usta ro'yxatdan o'tish
- ✅ Kategoriya bo'yicha qidirish (8 ta)
- ✅ Tuman bo'yicha qidirish (8 ta)
- ✅ Reyting tizimi (1-5 yulduz)
- ✅ Buyurtma tarixi
- ✅ Admin panel (/admin)
- ✅ Ustaga avtomatik xabar

## Daromad modeli

- Har buyurtmadan 7% komissiya (config.py da o'zgartiring)
- Yoki ustadan oylik obuna: 50,000-100,000 so'm

## Kengaytirish

- Yangi tuman qo'shish: `config.py` → `REGIONS`
- Yangi kategoriya: `config.py` → `CATEGORIES`
- Komissiya o'zgartirish: `config.py` → `COMMISSION_PERCENT`
