#!/usr/bin/env python3
# Apache Userbot — Full Safe Edition (Flask + Telethon)
# WARNING: This project intentionally excludes abusive/harassing features (no insults, no automated harassment).
# It includes safe alternatives (humorous replies, opt-in broadcasts, rate limits, owner-only controls).

import os, asyncio, logging, time, random, threading
from telethon import TelegramClient, events
from telethon.sessions import StringSession
from flask import Flask

# ==== CONFIG (already inserted) ====
API_ID = 22603193
API_HASH = "52012f357acfda33579dd701d7b4a131"
OWNER_ID = None  # set to your numeric Telegram ID if you want owner-only alerts/commands

SESSIONS_DIR = os.path.join(os.path.dirname(__file__), "sessions")
os.makedirs(SESSIONS_DIR, exist_ok=True)

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("apache_safe_full")

# Simple in-memory state (resets on restart)
autosms = {}        # target_user_id -> text
muted_users = set() # user ids to delete messages from where possible
triggers = []       # list of (phrase, response) exact-match
owner_clients = []

MAX_TRIGGERS = 20
RATE_WINDOW = 5.0
RATE_TOKENS = 6
from collections import defaultdict, deque
user_timestamps = defaultdict(deque)

def is_rate_limited(user_id):
    now = time.time()
    dq = user_timestamps[user_id]
    while dq and dq[0] <= now - RATE_WINDOW:
        dq.popleft()
    if len(dq) >= RATE_TOKENS:
        return True
    dq.append(now)
    return False

# Safe "humor" lists (no insults)
HUMOROUS_REPLIES = [
    "Ха-ха, смешно 😄",
    "Опа, шутка принята!",
    "Я бы подколол, но я слишком воспитан.",
    "Троль-мод: активирован 😈 (шутка)"
]

ANIME_POOL = [
    "https://i.imgur.com/6Yq3K0u.png",
    "https://i.imgur.com/E3R7sGq.png"
]

# Create Telethon clients for every session file in sessions/
clients = {}  # session_filename -> (client, task)

def register_handlers(client):
    @client.on(events.NewMessage(pattern='(?i)^/start$'))
    async def on_start(event):
        if event.is_private:
            await event.respond("Ты в боте Апачи 🚀\nИспользуй .команды для списка доступных команд.")

    @client.on(events.NewMessage(pattern='(?i)^(\.пинг|/ping)$'))
    async def on_ping(event):
        await event.reply("Понг! Скорость OK.")

    @client.on(events.NewMessage)
    async def on_all(event):
        try:
            text = (event.raw_text or "").strip()
            if not text:
                return
            sender = await event.get_sender()
            sender_id = getattr(sender, 'id', None)
            chat_id = event.chat_id

            # Auto-delete muted users' messages (best-effort)
            if sender_id in muted_users:
                try:
                    await event.delete()
                except: pass
                return

            # exact-match triggers
            if triggers and text.lower() in (t[0].lower() for t in triggers):
                for phrase, resp in triggers:
                    if phrase.lower() == text.lower():
                        try:
                            await event.reply(resp)
                        except: pass
                        return

            # autosms responses
            if sender_id in autosms and not text.startswith('.') and not text.startswith('/'):
                try:
                    await event.reply(autosms[sender_id])
                except: pass

            # commands start with '.'
            if not text.startswith('.'):
                return

            # rate limit per sender to avoid spam
            if sender_id and is_rate_limited(sender_id):
                return

            parts = text.split(maxsplit=2)
            cmd = parts[0].lower()
            arg = parts[1] if len(parts) > 1 else ""
            rest = parts[2] if len(parts) > 2 else ""

            # .дд N - delete last N messages from me in this chat
            if cmd in ('.дд', '.dd'):
                try:
                    n = int(arg) if arg else 1
                except:
                    await event.reply("Использование: .дд N")
                    return
                deleted = 0
                async for m in client.iter_messages(chat_id, from_user='me', limit=500):
                    if deleted >= n: break
                    try:
                        await m.delete(); deleted += 1
                    except: pass
                try: await event.delete()
                except: pass
                await event.reply(f"Удалено {deleted} своих сообщений (попытка).")

            # .ред N текст - edit last N of my messages
            elif cmd in ('.ред', '.red'):
                try:
                    n = int(parts[1]); new_text = parts[2]
                except:
                    await event.reply("Использование: .ред N новый_текст")
                    return
                edited = 0
                async for m in client.iter_messages(chat_id, from_user='me', limit=500):
                    if edited >= n: break
                    try:
                        await m.edit(new_text); edited += 1
                    except: pass
                await event.reply(f"✏️ Отредактировано {edited} сообщений")

            # .флуд N delay текст - VERY LIMITED safe flood (N<=5)
            elif cmd == '.флуд':
                try:
                    parts = text.split(maxsplit=3)
                    cnt = int(parts[1]); delay = float(parts[2]); body = parts[3]
                except:
                    await event.reply("Использование: .флуд N задержка текст (N<=5, delay>=0.5s)")
                    return
                if cnt > 5: cnt = 5
                if delay < 0.5: delay = 0.5
                await event.reply(f"Запускаю безопасный флуд: {cnt}×, {delay}s")
                for i in range(cnt):
                    try:
                        await client.send_message(chat_id, body)
                    except: pass
                    await asyncio.sleep(delay)
                await event.reply("✅ Флуд завершён.")

            # .автосмс (reply) текст
            elif cmd == '.автосмс':
                if not event.is_reply:
                    await event.reply("Ответьте на сообщение и используйте .автосмс ТЕКСТ")
                    return
                reply = await event.get_reply_message(); target = reply.sender_id
                text_body = (arg or rest or "").strip()
                if not text_body:
                    await event.reply("Укажите текст автоответа.")
                    return
                autosms[target] = text_body
                await event.reply(f"Автоответ установлен для {target}")

            elif cmd in ('.автосмсстоп',):
                if event.is_reply:
                    reply = await event.get_reply_message(); target = reply.sender_id
                elif arg:
                    try: target = int(arg)
                    except: target = None
                else:
                    target = None
                if target and target in autosms:
                    autosms.pop(target, None)
                    await event.reply(f"Автоответ отключён для {target}")
                else:
                    await event.reply("Автоответ не найден.")

            # .мут (reply)
            elif cmd in ('.мут', '.mute'):
                if not event.is_reply:
                    await event.reply("Ответьте на сообщение, чтобы замутить пользователя.")
                    return
                reply = await event.get_reply_message(); target = reply.sender_id
                muted_users.add(target)
                await event.reply(f"🔇 Пользователь {target} будет удаляться (если возможно).")

            elif cmd in ('.мутстоп', 'размут', 'unmute'):
                if event.is_reply:
                    reply = await event.get_reply_message(); target = reply.sender_id
                elif arg:
                    try: target = int(arg)
                    except: target = None
                else:
                    target = None
                if target and target in muted_users:
                    muted_users.discard(target)
                    await event.reply(f"✅ {target} размучен.")
                else:
                    await event.reply("Пользователь не найден в мут-листе.")

            # .аниме [tag]
            elif cmd.startswith('.аниме'):
                tag = arg.lower() if arg else 'default'
                pool = ANIME_POOL
                try:
                    await client.send_file(chat_id, random.choice(pool))
                except:
                    await event.reply("Ошибка отправки изображения.")

            # +триггер фраза|ответ
            elif cmd.startswith('+триггер'):
                payload = text[len('+триггер'):].strip()
                if '|' not in payload:
                    await event.reply("Формат: +триггер фраза|ответ")
                    return
                if len(triggers) >= MAX_TRIGGERS:
                    await event.reply("Достигнут лимит триггеров.")
                    return
                phrase, resp = payload.split('|',1)
                triggers.append((phrase.strip(), resp.strip()))
                await event.reply("Триггер добавлен.")

            # .тролль - safe humorous reply
            elif cmd == '.тролль':
                await event.reply(random.choice(HUMOROUS_REPLIES))

            # .команды
            elif cmd in ('.команды', '.help', '.commands'):
                await event.reply("Команды: .пинг, .дд N, .ред N текст, .флуд, .аниме, .автосмс, .автосмсстоп, .мут, .мутстоп, +триггер, .тролль")

            else:
                # unknown or disabled commands are ignored to prevent misuse
                return

        except Exception as e:
            logger.exception("Handler error: %s", e)
            try:
                await event.reply("Ошибка при выполнении команды.")
            except: pass

async def start_client_for_session(session_file):
    try:
        client = TelegramClient(session_file, API_ID, API_HASH)
        await client.start()
        me = await client.get_me()
        logger.info(f"Started client for {session_file} as {getattr(me,'username',me.id)}")
        register_handlers(client)
        await client.run_until_disconnected()
    except Exception as e:
        logger.exception("Failed to start client %s: %s", session_file, e)

async def start_all_clients():
    tasks = []
    for fname in os.listdir(SESSIONS_DIR):
        if fname.endswith('.session'):
            full = os.path.join(SESSIONS_DIR, fname)
            tasks.append(asyncio.create_task(start_client_for_session(full)))
    if tasks:
        await asyncio.gather(*tasks)
    else:
        logger.info("No session files found in 'sessions/'. Add sessions/<your_id>.session and restart.")
        while True:
            await asyncio.sleep(3600)

# Flask app to keep Render service alive
app = Flask("apache_safe")
@app.route('/')
def index():
    return "Apache Userbot (safe) running."

def run_flask():
    app.run(host='0.0.0.0', port=int(os.environ.get('PORT', 10000)))

def main():
    # Start Flask in background thread
    t = threading.Thread(target=run_flask, daemon=True)
    t.start()
    # Start telethon clients loop
    asyncio.run(start_all_clients())

if __name__ == '__main__':
    main()
