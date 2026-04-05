import aiosqlite
import asyncio
from datetime import datetime

DB_PATH = "usta_bot.db"

class Database:
    def __init__(self):
        self.db_path = DB_PATH

    async def init(self):
        async with aiosqlite.connect(self.db_path) as conn:
            await conn.executescript("""
                CREATE TABLE IF NOT EXISTS ustalar (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    telegram_id INTEGER UNIQUE,
                    ism TEXT NOT NULL,
                    telefon TEXT NOT NULL,
                    kategoriya TEXT NOT NULL,
                    tuman TEXT NOT NULL,
                    tajriba INTEGER DEFAULT 0,
                    reyting REAL DEFAULT 5.0,
                    baholashlar INTEGER DEFAULT 0,
                    faol INTEGER DEFAULT 1,
                    obuna_tugash TEXT,
                    qoshilgan TEXT DEFAULT CURRENT_TIMESTAMP
                );

                CREATE TABLE IF NOT EXISTS buyurtmalar (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    mijoz_id INTEGER NOT NULL,
                    mijoz_ism TEXT,
                    mijoz_tel TEXT,
                    usta_id INTEGER,
                    kategoriya TEXT NOT NULL,
                    tuman TEXT NOT NULL,
                    tavsif TEXT,
                    holat TEXT DEFAULT 'yangi',
                    yaratilgan TEXT DEFAULT CURRENT_TIMESTAMP,
                    tugagan TEXT
                );

                CREATE TABLE IF NOT EXISTS reytinglar (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    buyurtma_id INTEGER,
                    usta_id INTEGER,
                    mijoz_id INTEGER,
                    baho INTEGER,
                    izoh TEXT,
                    vaqt TEXT DEFAULT CURRENT_TIMESTAMP
                );

                CREATE TABLE IF NOT EXISTS foydalanuvchilar (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    telegram_id INTEGER UNIQUE,
                    ism TEXT,
                    telefon TEXT,
                    rol TEXT DEFAULT 'mijoz',
                    qoshilgan TEXT DEFAULT CURRENT_TIMESTAMP
                );
            """)
            await conn.commit()
        print("Database tayyor!")

    # ========== USTALAR ==========

    async def usta_qoshish(self, telegram_id, ism, telefon, kategoriya, tuman, tajriba):
        async with aiosqlite.connect(self.db_path) as conn:
            try:
                await conn.execute("""
                    INSERT INTO ustalar (telegram_id, ism, telefon, kategoriya, tuman, tajriba)
                    VALUES (?, ?, ?, ?, ?, ?)
                """, (telegram_id, ism, telefon, kategoriya, tuman, tajriba))
                await conn.commit()
                return True
            except aiosqlite.IntegrityError:
                return False

    async def usta_olish(self, telegram_id):
        async with aiosqlite.connect(self.db_path) as conn:
            conn.row_factory = aiosqlite.Row
            async with conn.execute(
                "SELECT * FROM ustalar WHERE telegram_id = ?", (telegram_id,)
            ) as cursor:
                return await cursor.fetchone()

    async def ustalar_topish(self, kategoriya, tuman):
        async with aiosqlite.connect(self.db_path) as conn:
            conn.row_factory = aiosqlite.Row
            async with conn.execute("""
                SELECT * FROM ustalar
                WHERE kategoriya = ? AND tuman = ? AND faol = 1
                ORDER BY reyting DESC, baholashlar DESC
                LIMIT 5
            """, (kategoriya, tuman)) as cursor:
                return await cursor.fetchall()

    async def barcha_ustalar(self):
        async with aiosqlite.connect(self.db_path) as conn:
            conn.row_factory = aiosqlite.Row
            async with conn.execute(
                "SELECT * FROM ustalar ORDER BY reyting DESC"
            ) as cursor:
                return await cursor.fetchall()

    async def usta_reyting_yangilash(self, usta_id, yangi_baho):
        async with aiosqlite.connect(self.db_path) as conn:
            conn.row_factory = aiosqlite.Row
            async with conn.execute(
                "SELECT reyting, baholashlar FROM ustalar WHERE id = ?", (usta_id,)
            ) as cursor:
                usta = await cursor.fetchone()
            if usta:
                jami = usta["reyting"] * usta["baholashlar"] + yangi_baho
                yangi_soni = usta["baholashlar"] + 1
                yangi_reyting = round(jami / yangi_soni, 1)
                await conn.execute("""
                    UPDATE ustalar SET reyting = ?, baholashlar = ? WHERE id = ?
                """, (yangi_reyting, yangi_soni, usta_id))
                await conn.commit()

    # ========== BUYURTMALAR ==========

    async def buyurtma_qoshish(self, mijoz_id, mijoz_ism, kategoriya, tuman, tavsif):
        async with aiosqlite.connect(self.db_path) as conn:
            cursor = await conn.execute("""
                INSERT INTO buyurtmalar (mijoz_id, mijoz_ism, kategoriya, tuman, tavsif)
                VALUES (?, ?, ?, ?, ?)
            """, (mijoz_id, mijoz_ism, kategoriya, tuman, tavsif))
            await conn.commit()
            return cursor.lastrowid

    async def buyurtma_olish(self, buyurtma_id):
        async with aiosqlite.connect(self.db_path) as conn:
            conn.row_factory = aiosqlite.Row
            async with conn.execute(
                "SELECT * FROM buyurtmalar WHERE id = ?", (buyurtma_id,)
            ) as cursor:
                return await cursor.fetchone()

    async def buyurtma_yangilash(self, buyurtma_id, usta_id, holat):
        async with aiosqlite.connect(self.db_path) as conn:
            await conn.execute("""
                UPDATE buyurtmalar SET usta_id = ?, holat = ? WHERE id = ?
            """, (usta_id, holat, buyurtma_id))
            await conn.commit()

    async def mijoz_buyurtmalari(self, mijoz_id):
        async with aiosqlite.connect(self.db_path) as conn:
            conn.row_factory = aiosqlite.Row
            async with conn.execute("""
                SELECT * FROM buyurtmalar WHERE mijoz_id = ?
                ORDER BY yaratilgan DESC LIMIT 10
            """, (mijoz_id,)) as cursor:
                return await cursor.fetchall()

    # ========== FOYDALANUVCHILAR ==========

    async def foydalanuvchi_qoshish(self, telegram_id, ism):
        async with aiosqlite.connect(self.db_path) as conn:
            try:
                await conn.execute("""
                    INSERT OR IGNORE INTO foydalanuvchilar (telegram_id, ism)
                    VALUES (?, ?)
                """, (telegram_id, ism))
                await conn.commit()
            except Exception:
                pass

    # ========== STATISTIKA ==========

    async def statistika(self):
        async with aiosqlite.connect(self.db_path) as conn:
            async with conn.execute("SELECT COUNT(*) FROM ustalar WHERE faol=1") as c:
                ustalar_soni = (await c.fetchone())[0]
            async with conn.execute("SELECT COUNT(*) FROM buyurtmalar") as c:
                buyurtmalar_soni = (await c.fetchone())[0]
            async with conn.execute("SELECT COUNT(*) FROM foydalanuvchilar") as c:
                foydalanuvchilar_soni = (await c.fetchone())[0]
            return {
                "ustalar": ustalar_soni,
                "buyurtmalar": buyurtmalar_soni,
                "foydalanuvchilar": foydalanuvchilar_soni,
            }

db = Database()
