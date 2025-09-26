# main.py
    # Safe Apache-style Telegram bot (aiogram v2) with numeric keyboard and template storage (SQLite).
    import logging
    import asyncio
    import aiosqlite
    import os
    from aiogram import Bot, Dispatcher, types
    from aiogram.utils import executor
    from aiogram.types import ReplyKeyboardMarkup, KeyboardButton, InlineKeyboardMarkup, InlineKeyboardButton

    # Configuration via environment variables
    BOT_TOKEN = os.environ.get("7998020401:AAG3D2cB4YTdxh7i2kjFXCT85wp16UV3lNU")
    OWNER_ID = 8486672898 int(os.environ.get("OWNER_ID", "0"))
    DB_PATH = os.environ.get("DB_PATH", "data.db")

    logging.basicConfig(level=logging.INFO, format='[%(asctime)s] %(levelname)s: %(message)s')
    logger = logging.getLogger(__name__)

    if not BOT_TOKEN:
        logger.error("BOT_TOKEN not set in env. Set BOT_TOKEN before running.")
        raise SystemExit("BOT_TOKEN not set")

    bot = Bot(token=BOT_TOKEN)
    dp = Dispatcher(bot)

    # --- DB helpers ---
    async def init_db():
        async with aiosqlite.connect(DB_PATH) as db:
            await db.execute("""CREATE TABLE IF NOT EXISTS templates (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT UNIQUE,
                text TEXT
            )""")
            await db.execute("""CREATE TABLE IF NOT EXISTS rate_limits (
                user_id INTEGER PRIMARY KEY,
                last_repeat_at REAL
            )""")
            await db.commit()

    async def add_template(name: str, text: str):
        try:
            async with aiosqlite.connect(DB_PATH) as db:
                await db.execute("INSERT OR REPLACE INTO templates(name,text) VALUES(?,?)", (name, text))
                await db.commit()
            return True
        except Exception:
            logger.exception("add_template")
            return False

    async def list_templates():
        out = []
        async with aiosqlite.connect(DB_PATH) as db:
            async with db.execute("SELECT name FROM templates ORDER BY name") as cur:
                async for row in cur:
                    out.append(row[0])
        return out

    async def get_template(name: str):
        async with aiosqlite.connect(DB_PATH) as db:
            async with db.execute("SELECT text FROM templates WHERE name=?", (name,)) as cur:
                row = await cur.fetchone()
                return row[0] if row else None

    # --- Keyboards ---
    def main_keyboard():
        kb = ReplyKeyboardMarkup(resize_keyboard=True)
        kb.add(KeyboardButton("Поделиться номером", request_contact=True))
        kb.add("/help", "/templates")
        return kb

    def numeric_inline():
        kb = InlineKeyboardMarkup(row_width=3)
        buttons = [InlineKeyboardButton(text=str(i), callback_data=f"num:{i}") for i in range(1,10)]
        buttons.append(InlineKeyboardButton(text="0", callback_data="num:0"))
        kb.add(*buttons)
        kb.add(InlineKeyboardButton("Отмена", callback_data="num:cancel"))
        return kb

    # --- Handlers ---
    @dp.message_handler(commands=["start"])
    async def cmd_start(message: types.Message):
        try:
            await message.answer("👋 Ты в боте Апачи. Используй /help для списка команд.", reply_markup=main_keyboard())
        except Exception:
            logger.exception("start")

    @dp.message_handler(commands=["help"])
    async def cmd_help(message: types.Message):
        txt = (
            "📚 Команды:
"
            "/start — приветствие
"
            "/help — это сообщение
"
            "/ping — проверить отклик
"
            "/templates — список шаблонов
"
            "/addtemplate name|text — добавить шаблон
"
            "/sendtemplate name — отправить шаблон в чат
"
            "/repeat template_name count speed — безопасный повтор (ограничен)
"
            "/num — открыть цифровую клавиатуру
"
            "/stopbot — остановить бота (владелец)
"
        )
        await message.reply(txt)

    @dp.message_handler(commands=["ping"])
    async def cmd_ping(message: types.Message):
        await message.reply("Понг ✅")

    @dp.message_handler(commands=["addtemplate"])
    async def cmd_addtemplate(message: types.Message):
        args = message.get_args()
        if not args or "|" not in args:
            await message.reply("Использование: /addtemplate имя|текст")
            return
        name, text = args.split("|",1)
        name = name.strip()
        text = text.strip()
        ok = await add_template(name, text)
        if ok:
            await message.reply(f"Шаблон '{name}' сохранён.")
        else:
            await message.reply("Ошибка при сохранении шаблона.")

    @dp.message_handler(commands=["templates"])
    async def cmd_templates(message: types.Message):
        templ = await list_templates()
        if not templ:
            await message.reply("Нет шаблонов.")
            return
        await message.reply("\n".join(templ))

    @dp.message_handler(commands=["sendtemplate"])
    async def cmd_sendtemplate(message: types.Message):
        name = message.get_args().strip()
        if not name:
            await message.reply("Использование: /sendtemplate имя")
            return
        text = await get_template(name)
        if not text:
            await message.reply("Шаблон не найден.")
            return
        await message.reply(text)

    # Safe repeat: limited to 10 messages and rate-limited per user
    import time
    async def can_repeat(user_id: int, cooldown: int = 10):
        now = time.time()
        async with aiosqlite.connect(DB_PATH) as db:
            async with db.execute("SELECT last_repeat_at FROM rate_limits WHERE user_id=?", (user_id,)) as cur:
                row = await cur.fetchone()
            last = row[0] if row else 0
            if now - last < cooldown:
                return False, int(cooldown - (now-last))
            await db.execute("INSERT OR REPLACE INTO rate_limits(user_id,last_repeat_at) VALUES(?,?)", (user_id, now))
            await db.commit()
            return True, 0

    @dp.message_handler(commands=["repeat"])
    async def cmd_repeat(message: types.Message):
        # /repeat template_name count speed
        # speed: fast/medium/slow -> delays 0.2 / 0.7 / 1.5
        args = message.get_args().split()
        if len(args) < 3:
            await message.reply("Использование: /repeat имя_шаблона количество скорость(fast/med/slow). Ограничение: до 10 сообщений.")
            return
        name = args[0]
        try:
            cnt = int(args[1])
        except:
            await message.reply("Неверное количество.")
            return
        speed = args[2].lower()
        if cnt <= 0 or cnt > 10:
            await message.reply("Количество должно быть 1..10.")
            return
        delays = {"fast":0.2, "med":0.7, "slow":1.5, "medium":0.7}
        delay = delays.get(speed, 0.7)
        ok, wait = await can_repeat(message.from_user.id, cooldown=8)
        if not ok:
            await message.reply(f"Подождите ещё {wait}s перед повтором.")
            return
        text = await get_template(name)
        if not text:
            await message.reply("Шаблон не найден.")
            return
        await message.reply(f"Запускаю безопасный repeat: {cnt}×")
        for i in range(cnt):
            try:
                await message.reply(text)
            except Exception:
                logger.exception("sending repeat")
            await asyncio.sleep(delay)
        await message.reply("Готово ✅")

    @dp.message_handler(commands=["num"])
    async def cmd_num(message: types.Message):
        await message.reply("Выберите цифру", reply_markup=numeric_inline())

    @dp.callback_query_handler(lambda c: c.data and c.data.startswith("num:"))
    async def cb_num(query: types.CallbackQuery):
        data = query.data.split(":",1)[1]
        if data == "cancel":
            await query.message.edit_text("Ввод отменён.")
        else:
            await query.answer(f"Нажата: {data}")
            # example: append to message or store in DB if needed

    @dp.message_handler(commands=["stopbot","стопбот"])
    async def cmd_stop(message: types.Message):
        if OWNER_ID and message.from_user.id == OWNER_ID:
            await message.reply("Останавливаю бота...")
            logger.info("Owner requested shutdown.")
            await bot.close()
            asyncio.get_event_loop().stop()
        else:
            await message.reply("Только владелец может выполнить эту команду.")

    @dp.message_handler(content_types=types.ContentType.CONTACT)
    async def contact(message: types.Message):
        c = message.contact
        await message.reply(f"Спасибо! Номер: {c.phone_number}. Этот бот не сохраняет чужие сессии.")

    @dp.message_handler()
    async def fallback(message: types.Message):
        logger.info("Fallback from %s: %s", message.from_user.id, (message.text or "")[:200])
        await message.reply("Не понимаю. /help для списка команд.")

    async def on_startup(_dp):
        logger.info("Starting up...")
        await init_db()

    async def on_shutdown(_dp):
        logger.info("Shutting down...")
        await bot.close()

    if __name__ == "__main__":
        executor.start_polling(dp, on_startup=on_startup, on_shutdown=on_shutdown, skip_updates=True)