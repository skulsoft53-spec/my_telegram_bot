# bot.py
# Aiogram auth-bot + Telethon userbot launcher
# Вставлены твои данные (API_TOKEN, API_ID, API_HASH, OWNER_ID).
# Требует: aiogram, telethon, aiosqlite

import logging
import asyncio
import time
import traceback
from datetime import datetime

import aiosqlite
from aiogram import Bot, Dispatcher, executor, types
from aiogram.utils.exceptions import TelegramAPIError
from telethon import TelegramClient, events
from telethon.sessions import StringSession

# -----------------------------
# ДАННЫЕ
# -----------------------------
API_ID = 22603193
API_HASH = "52012f357acfda33579dd701d7b4a131"
API_TOKEN = "7998020401:AAH4baYgBZa758FBdghdI0gI9NYs-Woffh4"
OWNER_ID = 8486672898

DB_PATH = "sessions.db"
SESSION_TTL = 3 * 3600     # 3 часа
RESTART_DELAY = 5

# -----------------------------
# ЛОГИ
# -----------------------------
logging.basicConfig(level=logging.INFO, format='[%(asctime)s] %(levelname)s: %(message)s')
logger = logging.getLogger("multiownerbot")

# -----------------------------
# Aiogram init
# -----------------------------
bot = Bot(token=API_TOKEN)
dp = Dispatcher(bot)

# -----------------------------
# Временное хранилище авторизации
# -----------------------------
auth_tmp = {}

# -----------------------------
# Активные Telethon-клиенты
# -----------------------------
user_clients = {}  # user_id -> dict(client, task, created_at)

# -----------------------------
# DB helpers
# -----------------------------
async def init_db():
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute("""
            CREATE TABLE IF NOT EXISTS sessions (
                user_id INTEGER PRIMARY KEY,
                phone TEXT,
                session_str TEXT,
                created_at REAL
            )
        """)
        await db.commit()

async def save_session_db(user_id: int, phone: str, session_str: str):
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute("INSERT OR REPLACE INTO sessions(user_id,phone,session_str,created_at) VALUES(?,?,?,?)",
                         (user_id, phone, session_str, time.time()))
        await db.commit()

async def load_session(user_id: int):
    async with aiosqlite.connect(DB_PATH) as db:
        async with db.execute("SELECT phone,session_str,created_at FROM sessions WHERE user_id=?", (user_id,)) as cur:
            row = await cur.fetchone()
            return row if row else None

async def remove_session_db(user_id: int):
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute("DELETE FROM sessions WHERE user_id=?", (user_id,))
        await db.commit()

# -----------------------------
# Telethon client запуск
# -----------------------------
async def start_user_client(user_id: int, session_str: str):
    if user_id in user_clients:
        return True
    try:
        client = TelegramClient(StringSession(session_str), API_ID, API_HASH)
        await client.connect()
        if not await client.is_user_authorized():
            await client.disconnect()
            return False

        @client.on(events.NewMessage)
        async def _on_new_message(event):
            if event.out:
                return
            if event.raw_text.strip().lower() in [".пинг", ".ping"]:
                try:
                    await event.reply("Понг! (от userbot)")
                except Exception:
                    pass

        task = asyncio.create_task(client.run_until_disconnected())
        user_clients[user_id] = {"client": client, "task": task, "created_at": time.time()}
        return True
    except Exception as e:
        logger.exception("start_user_client error: %s", e)
        return False

async def stop_user_client(user_id: int):
    info = user_clients.get(user_id)
    if not info:
        return
    client = info["client"]
    task = info["task"]
    try:
        await client.log_out()
    except Exception:
        pass
    try:
        await client.disconnect()
    except Exception:
        pass
    try:
        task.cancel()
    except Exception:
        pass
    user_clients.pop(user_id, None)
    await remove_session_db(user_id)

# -----------------------------
# Aiogram handlers
# -----------------------------
@dp.message_handler(commands=["start"])
async def cmd_start(message: types.Message):
    if message.from_user.id == OWNER_ID:
        await message.reply("Добро пожаловать! Используй /connect чтобы подключить аккаунт.")
    else:
        await message.reply("⛔ Этот бот доступен только владельцу.")

@dp.message_handler(commands=["connect"])
async def cmd_connect(message: types.Message):
    if message.from_user.id != OWNER_ID:
        return await message.reply("⛔ Только владелец.")
    auth_tmp[message.from_user.id] = {"stage": "phone"}
    await message.reply("Введите номер телефона в формате +71234567890")

@dp.message_handler(commands=["cancel"])
async def cmd_cancel(message: types.Message):
    auth_tmp.pop(message.from_user.id, None)
    await message.reply("Операция отменена.")

@dp.message_handler(commands=["code"])
async def cmd_code(message: types.Message):
    uid = message.from_user.id
    tmp = auth_tmp.get(uid)
    if not tmp or tmp.get("stage") != "code_sent":
        return await message.reply("Сначала /connect и ввод номера.")
    parts = message.text.split()
    if len(parts) < 2:
        return await message.reply("Использование: /code <код>")
    code = parts[1]
    phone = tmp["phone"]
    saved = tmp.get("temp_session")
    try:
        client = TelegramClient(StringSession(saved), API_ID, API_HASH)
        await client.connect()
        try:
            await client.sign_in(phone=phone, code=code)
        except Exception as e:
            if "PASSWORD" in str(e).upper():
                auth_tmp[uid]["stage"] = "password_needed"
                auth_tmp[uid]["client_temp"] = client.session.save()
                return await message.reply("Введите /password <ваш пароль>")
            else:
                return await message.reply("Ошибка: неверный код.")
        session_str = client.session.save()
        await save_session_db(uid, phone, session_str)
        await start_user_client(uid, session_str)
        await message.reply("✅ Аккаунт подключён.")
        await client.disconnect()
        auth_tmp.pop(uid, None)
    except Exception as e:
        logger.exception("cmd_code error: %s", e)
        await message.reply("Ошибка при авторизации.")

@dp.message_handler(commands=["password"])
async def cmd_password(message: types.Message):
    uid = message.from_user.id
    tmp = auth_tmp.get(uid)
    if not tmp or tmp.get("stage") != "password_needed":
        return await message.reply("Нет запроса пароля.")
    parts = message.text.split(maxsplit=1)
    if len(parts) < 2:
        return await message.reply("Использование: /password <пароль>")
    pwd = parts[1]
    saved = tmp["client_temp"]
    phone = tmp["phone"]
    try:
        client = TelegramClient(StringSession(saved), API_ID, API_HASH)
        await client.connect()
        await client.sign_in(password=pwd)
        session_str = client.session.save()
        await save_session_db(uid, phone, session_str)
        await start_user_client(uid, session_str)
        await message.reply("✅ Подключено с 2FA.")
        await client.disconnect()
        auth_tmp.pop(uid, None)
    except Exception as e:
        logger.exception("password error: %s", e)
        await message.reply("Ошибка при вводе пароля.")

@dp.message_handler(commands=["logout"])
async def cmd_logout(message: types.Message):
    if message.from_user.id != OWNER_ID:
        return await message.reply("⛔ Только владелец.")
    await stop_user_client(message.from_user.id)
    await message.reply("✅ Сессия удалена.")

@dp.message_handler(commands=["status"])
async def cmd_status(message: types.Message):
    if message.from_user.id != OWNER_ID:
        return
    row = await load_session(message.from_user.id)
    if row:
        phone, _, created_at = row
        ts = datetime.fromtimestamp(created_at).isoformat()
        await message.reply(f"✅ Подключён номер {phone}, время: {ts}")
    else:
        await message.reply("❌ Нет активной сессии.")

@dp.message_handler(commands=["ping"])
async def cmd_ping(message: types.Message):
    if message.from_user.id == OWNER_ID:
        await message.reply("Pong!")

@dp.message_handler(commands=["help"])
async def cmd_help(message: types.Message):
    if message.from_user.id == OWNER_ID:
        await message.reply("/connect → /code → /password\n/status\n/logout\n/ping\n/help")

# -----------------------------
# Ошибки
# -----------------------------
@dp.errors_handler()
async def errors_handler(update, exception):
    tb = "".join(traceback.format_exception(type(exception), exception, exception.__traceback__))
    try:
        await bot.send_message(OWNER_ID, f"⚠️ Ошибка:\n{tb[:3000]}")
    except TelegramAPIError:
        logger.exception("Failed to send error to owner")
    return True

# -----------------------------
# TTL watcher
# -----------------------------
async def session_ttl_watcher():
    while True:
        now = time.time()
        async with aiosqlite.connect(DB_PATH) as db:
            async with db.execute("SELECT user_id,created_at FROM sessions") as cur:
                rows = await cur.fetchall()
        for user_id, created_at in rows:
            if now - created_at > SESSION_TTL:
                await stop_user_client(user_id)
        await asyncio.sleep(60)

# -----------------------------
# Автоперезапуск
# -----------------------------
def start_polling_with_restart():
    while True:
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        try:
            loop.run_until_complete(init_db())
            loop.create_task(session_ttl_watcher())
            executor.start_polling(dp, skip_updates=True)
        except Exception as e:
            logger.exception("Bot crashed: %s", e)
            time.sleep(RESTART_DELAY)
            continue
        finally:
            if loop.is_running():
                loop.stop()
        break

if __name__ == "__main__":
    logger.info("Starting auth-bot...")
    start_polling_with_restart()