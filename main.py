#!/usr/bin/env python3
# Apache Userbot (safe edition)
# Contains only non-abusive, non-spammy features.
# - start /help /ping
# - delete own last N messages (.дд)
# - edit own last N messages (.ред)
# - autosms (auto-reply to a user) (.автосмс / .автосмсстоп)
# - mute (delete messages from a user in chats where this account can delete) (.мут / .мутстоп)
# - anime (send a random safe image) (.аниме)
# - simple trigger (exact match only) (+триггер) limited to 10 triggers
# Sessions are stored in sessions/<user_id>.session files.
import os, asyncio, logging, time, random
from collections import deque, defaultdict
from telethon import TelegramClient, events
from telethon.sessions import StringSession

# === CONFIG (already inserted) ===
API_ID = 22603193
API_HASH = "52012f357acfda33579dd701d7b4a131"

SESSIONS_DIR = "sessions"
os.makedirs(SESSIONS_DIR, exist_ok=True)

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("apache_safe")

# simple rate limits to avoid abuse
CMD_WINDOW = 5.0
CMD_TOKENS = 5
user_timestamps = defaultdict(deque)

def is_rate_limited(user_id):
    now = time.time()
    dq = user_timestamps[user_id]
    while dq and dq[0] <= now - CMD_WINDOW:
        dq.popleft()
    if len(dq) >= CMD_TOKENS:
        return True
    dq.append(now)
    return False

# in-memory state (resets on restart)
autosms = {}        # target_user_id -> text
muted_users = set() # user_ids to delete messages from (best-effort, only where permitted)
triggers = []       # list of (phrase, response) exact-match, max 10

MAX_TRIGGERS = 10

# helper to pick session file for this process (single user session file recommended)
# If a sessions/<id>.session exists, start clients for each file. Otherwise, instruct user to create one locally.
async def start_clients():
    tasks = []
    for fname in os.listdir(SESSIONS_DIR):
        if not fname.endswith(".session"):
            continue
        path = os.path.join(SESSIONS_DIR, fname)
        # Use filename (without .session) as identifier; attempt to start a client
        try:
            client = TelegramClient(path, API_ID, API_HASH)
            await client.connect()
            if not await client.is_user_authorized():
                await client.disconnect()
                logger.info("Session %s not authorized; skip.", fname)
                continue
            logger.info("Started client for %s", fname)
            register_handlers(client)
            tasks.append(asyncio.create_task(client.run_until_disconnected()))
        except Exception as e:
            logger.exception("Failed to start client %s: %s", fname, e)
    return tasks

def register_handlers(client):
    @client.on(events.NewMessage(pattern='(?i)^/start$'))
    async def on_start(event):
        # only respond in private chats
        if not event.is_private:
            return
        # send welcome message and simple buttons (buttons ignored on some clients)
        text = "👋 Приветствую тебя в боте Apache (safe edition).\nКол-во подключённых аккаунтов - 1\n\nДоступные команды: .пинг, .дд, .ред, .аниме, .автосмс, .автосмсстоп, .мут, .мутстоп, +триггер, .команды"
        await event.respond(text)

    @client.on(events.NewMessage(pattern='(?i)^/help$'))
    async def on_help(event):
        await event.respond("Команды: .пинг, .дд N, .ред N текст, .аниме [tag], .автосмс (reply) текст, .автосмсстоп (reply), .мут (reply), .мутстоп (reply or id), +триггер phrase|response")

    @client.on(events.NewMessage(pattern='(?i)^(\.пинг|/ping)$'))
    async def on_ping(event):
        await event.respond("Понг!")

    @client.on(events.NewMessage)
    async def on_all(event):
        # ignore messages without text
        text = (event.raw_text or "").strip()
        if not text:
            return
        sender = await event.get_sender()
        sender_id = getattr(sender, 'id', None)

        # triggers (exact match)
        if triggers and text.lower() in (t[0].lower() for t in triggers):
            for phrase, resp in triggers:
                if phrase.lower() == text.lower():
                    try:
                        await event.reply(resp)
                    except: pass
                    return

        # autosms: when a message arrives from a target, auto-reply
        if sender_id in autosms and not text.startswith('.') and not text.startswith('/'):
            try:
                await event.reply(autosms[sender_id])
            except: pass

        # mute: best-effort delete messages from muted users in chats where this account can delete
        if sender_id in muted_users:
            try:
                await event.delete()
            except:
                pass

        # commands begin with '.'
        if not text.startswith('.'):
            return

        # basic rate limit per sender to avoid abuse
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
                await event.respond("Использование: .дд N")
                return
            deleted = 0
            async for m in client.iter_messages(event.chat_id, from_user='me', limit=500):
                if deleted >= n:
                    break
                try:
                    await m.delete(); deleted += 1
                except: pass
            try:
                await event.delete()
            except: pass
            await event.respond(f"Удалено {deleted} своих сообщений (попытка).")

        # .ред N text - edit last N of my messages
        elif cmd in ('.ред', '.red'):
            try:
                n = int(parts[1]); new_text = parts[2]
            except:
                await event.respond("Использование: .ред N новый_текст")
                return
            edited = 0
            async for m in client.iter_messages(event.chat_id, from_user='me', limit=500):
                if edited >= n: break
                try:
                    await m.edit(new_text); edited += 1
                except: pass
            await event.respond(f"✏️ Отредактировано {edited} сообщений")

        # .аниме [tag]
        elif cmd.startswith('.аниме'):
            tag = arg.lower() if arg else 'default'
            pools = {
                'neko': ['https://i.imgur.com/6Yq3K0u.png'],
                'waifu': ['https://i.imgur.com/E3R7sGq.png'],
                'default': ['https://i.imgur.com/6Yq3K0u.png']
            }
            imgs = pools.get(tag, pools['default'])
            try:
                await client.send_file(event.chat_id, random.choice(imgs))
            except:
                await event.respond("Не удалось отправить картинку.")

        # .автосмс (reply) text
        elif cmd == '.автосмс':
            if not event.is_reply:
                await event.respond("Ответьте на сообщение пользователя и используйте .автосмс ТЕКСТ")
                return
            reply = await event.get_reply_message()
            target = reply.sender_id
            text_body = arg or rest or ""
            if not text_body:
                await event.respond("Укажите текст автоответа после команды.")
                return
            autosms[target] = text_body
            await event.respond(f"Автоответ установлен для {target}")

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
                await event.respond(f"Автоответ отключён для {target}")
            else:
                await event.respond("Автоответ не найден для указанного пользователя.")

        # .мут (reply) - add to muted set (best-effort)
        elif cmd in ('.мут', '.mute'):
            if not event.is_reply:
                await event.respond("Ответьте на сообщение пользователя, чтобы замутить его.")
                return
            reply = await event.get_reply_message(); target = reply.sender_id
            muted_users.add(target)
            await event.respond(f"🔇 Пользователь {target} будет удаляться (если это возможно).")

        # .мутстоп (reply or id)
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
                await event.respond(f"✅ {target} размучен.")
            else:
                await event.respond("Пользователь не найден в мут-листе.")

        # +триггер phrase|response  (exact match only)
        elif cmd.startswith('+триггер'):
            payload = text[len('+триггер'):].strip()
            if '|' not in payload:
                await event.respond("Формат: +триггер фраза|ответ")
                return
            if len(triggers) >= MAX_TRIGGERS:
                await event.respond("Достигнут лимит триггеров.")
                return
            phrase, resp = payload.split('|', 1)
            triggers.append((phrase.strip(), resp.strip()))
            await event.respond("Триггер добавлен.")

        # .команды
        elif cmd in ('.команды', '.help', '.commands'):
            await event.respond("Команды: .пинг, .дд N, .ред N текст, .аниме [tag], .автосмс (reply) текст, .автосмсстоп, .мут, .мутстоп, +триггер")

        else:
            # unknown/disabled commands (spam, baiting, mass-messaging, DDoS tools are disabled here)
            pass

async def main():
    tasks = await start_clients()
    if tasks:
        await asyncio.gather(*tasks)
    else:
        logger.info("No sessions found in 'sessions/' - add your <id>.session files and restart. This process will idle.")
        while True:
            await asyncio.sleep(3600)

if __name__ == '__main__':
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        pass
