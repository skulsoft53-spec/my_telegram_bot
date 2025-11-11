# userbot_templates.py
import asyncio
import json
import os
import random
from telethon import TelegramClient, events

# === НАСТРОЙКИ ===
api_id = 22603193
api_hash = "52012f357acfda33579dd701d7b4a131"
session_name = "userbot_templates"

client = TelegramClient(session_name, api_id, api_hash)

ALIASES_FILE = "aliases.json"
AUTOSMS_FILE = "autosms.json"
FLOOD_FILE = "flood.txt"
TEMPLATES_FILE = "templates.json"

BAD_WORDS = {"блять", "сука", "хуй", "пидор", "ублюдок"}
safe_mode = True

if os.path.exists(ALIASES_FILE):
    with open(ALIASES_FILE, "r", encoding="utf-8") as f:
        aliases = json.load(f)
else:
    aliases = {"ред": {}, "дд": {}}

if os.path.exists(TEMPLATES_FILE):
    with open(TEMPLATES_FILE, "r", encoding="utf-8") as f:
        templates = json.load(f)
else:
    templates = {}

autosms_target = None
autosms_text = None

def save_aliases():
    with open(ALIASES_FILE, "w", encoding="utf-8") as f:
        json.dump(aliases, f, ensure_ascii=False, indent=2)

def save_templates():
    with open(TEMPLATES_FILE, "w", encoding="utf-8") as f:
        json.dump(templates, f, ensure_ascii=False, indent=2)

def contains_bad_word(text: str) -> bool:
    low = text.lower()
    for w in BAD_WORDS:
        if w in low:
            return True
    return False

# ------------------ шаблоны ------------------
@client.on(events.NewMessage(pattern=r"^\.tmpl add (\S+)$"))
async def tmpl_add(event):
    name = event.pattern_match.group(1).strip()
    if not event.is_reply:
        await event.reply("❗ Ответь на сообщение или файл, который нужно сохранить как шаблон.")
        return
    reply = await event.get_reply_message()
    text = ""
    if reply.media:
        path = await reply.download_media()
        try:
            with open(path, "r", encoding="utf-8", errors="ignore") as f:
                text = f.read().strip()
        except Exception:
            os.remove(path)
            await event.reply("❌ Невозможно прочитать файл как текст.")
            return
        os.remove(path)
    else:
        text = reply.message or ""
    if not text:
        await event.reply("⚠️ Шаблон пустой — отмена.")
        return
    if len(text.encode("utf-8")) > 200 * 1024:
        await event.reply("❌ Шаблон превышает 200КБ.")
        return
    templates[name] = text
    save_templates()
    await event.reply(f"✅ Шаблон `{name}` сохранён ({len(text)} символов).")

@client.on(events.NewMessage(pattern=r"^\.tmpl del (\S+)$"))
async def tmpl_del(event):
    name = event.pattern_match.group(1).strip()
    if name in templates:
        del templates[name]
        save_templates()
        await event.reply(f"🗑️ Шаблон `{name}` удалён.")
    else:
        await event.reply("⚠️ Шаблон не найден.")

@client.on(events.NewMessage(pattern=r"^\.tmpl list$"))
async def tmpl_list(event):
    if not templates:
        await event.reply("📭 Список шаблонов пуст.")
        return
    lines = [f"- `{k}` ({len(v)} simb)" for k, v in templates.items()]
    text = "📚 Шаблоны:\n" + "\n".join(lines)
    await event.reply(text)

@client.on(events.NewMessage(pattern=r"^\.tmpl safe (on|off)$"))
async def tmpl_safe(event):
    global safe_mode
    arg = event.pattern_match.group(1)
    safe_mode = (arg == "on")
    await event.reply(f"🔒 Safe mode {'ON' if safe_mode else 'OFF'}.")

# ------------------ .флуд ------------------
@client.on(events.NewMessage(pattern=r"^\.флуд (.+)$"))
async def flood_handler(event):
    args = event.pattern_match.group(1).strip()
    if args == "-":
        if os.path.exists(FLOOD_FILE):
            os.remove(FLOOD_FILE)
            await event.reply("🗑️ Файл для флуд-сообщений удалён.")
        else:
            await event.reply("⚠️ Файл не найден.")
        return

    parts = args.split(" ", 2)
    if len(parts) < 2:
        await event.reply("❌ Используй: `.флуд [кол-во] [задержка] [имя_шаблона(опц.)]` или прикрепи файл.")
        return

    try:
        count = int(parts[0])
        delay = float(parts[1])
    except:
        await event.reply("❌ Неправильные параметры: `.флуд <кол-во> <задержка> [шаблон]`")
        return

    text = None
    tpl_name = parts[2].strip() if len(parts) >= 3 else None

    if tpl_name:
        if tpl_name not in templates:
            await event.reply("⚠️ Шаблон с таким именем не найден.")
            return
        text = templates[tpl_name]
    elif event.message.media:
        path = await event.message.download_media(FLOOD_FILE)
        try:
            with open(path, "r", encoding="utf-8", errors="ignore") as f:
                text = f.read().strip()
        except Exception:
            if os.path.exists(path):
                os.remove(path)
            await event.reply("❌ Невозможно прочитать вложенный файл как текст.")
            return
        if os.path.exists(path):
            os.remove(path)
    elif os.path.exists(FLOOD_FILE):
        with open(FLOOD_FILE, "r", encoding="utf-8", errors="ignore") as f:
            text = f.read().strip()
    else:
        await event.reply("⚠️ Нет шаблона и нет прикреплённого файла.")
        return

    if not text:
        await event.reply("⚠️ Шаблон пустой.")
        return
    if len(text.encode("utf-8")) > 200 * 1024:
        await event.reply("❌ Текст превышает 200КБ.")
        return
    if safe_mode and contains_bad_word(text):
        await event.reply("🚫 В шаблоне найдены запрещённые слова — действие запрещено (safe mode).")
        return

    await event.delete()
    for i in range(count):
        await event.respond(text)
        await asyncio.sleep(delay)

# ------------------ .байт (по 3 слова) ------------------
@client.on(events.NewMessage(pattern=r"^\.байт(?: (.+))?$"))
async def bite_handler(event):
    if event.pattern_match.group(1) is None:
        await event.reply("⚠️ Используй: `.байт <имя_шаблона>`")
        return

    tpl_name = event.pattern_match.group(1).strip()
    if tpl_name not in templates:
        await event.reply("⚠️ Шаблон не найден.")
        return

    text_source = templates[tpl_name]
    if safe_mode and contains_bad_word(text_source):
        await event.reply("🚫 Шаблон содержит запрещённые слова — действие запрещено (safe mode).")
        return

    if not event.is_reply:
        await event.reply("⚠️ Ответь командой на сообщение пользователя, которого нужно 'байтить'.")
        return

    target_msg = await event.get_reply_message()
    await event.delete()

    words = text_source.split()
    chunks = [" ".join(words[i:i+3]) for i in range(0, len(words), 3)]

    for chunk in chunks:
        await client.send_message(event.chat_id, chunk, reply_to=target_msg.id)
        await asyncio.sleep(1)

# ------------------ Мут пользователя ------------------
muted_users = {}  # {chat_id: set(user_id)}

@client.on(events.NewMessage(pattern=r"^\.(мут|mute|мут\+|mute\+)$"))
async def mute_user(event):
    if not event.is_reply:
        await event.reply("⚠️ Ответьте на сообщение пользователя, которого нужно мутить.")
        return
    reply = await event.get_reply_message()
    chat = event.chat_id
    user = reply.sender_id

    if chat not in muted_users:
        muted_users[chat] = set()
    muted_users[chat].add(user)
    await event.reply(f"🔇 Пользователь {reply.sender_id} замучен в этом чате.")

@client.on(events.NewMessage(pattern=r"^\.(мутстоп|мут-|размут|unmute)"))
async def unmute_user(event):
    args = event.raw_text.strip().split(" ", 1)
    if len(args) < 2:
        await event.reply("⚠️ Укажи ID или ник пользователя: `.мутстоп @username`")
        return
    chat = event.chat_id
    target = args[1].strip()
    try:
        target_id = int(target)
    except:
        target_id = target
    if chat in muted_users and target_id in muted_users[chat]:
        muted_users[chat].remove(target_id)
        await event.reply(f"🔊 Мут снят с пользователя {target}")
    else:
        await event.reply("⚠️ Этот пользователь не был замучен.")

@client.on(events.NewMessage)
async def delete_muted(event):
    chat = event.chat_id
    if chat in muted_users and event.sender_id in muted_users[chat]:
        await event.delete()

# ------------------ автосмс ------------------
@client.on(events.NewMessage(pattern=r"^\.автосмс (.+)$"))
async def autosms_start(event):
    global autosms_target, autosms_text
    autosms_text = event.pattern_match.group(1)
    if event.is_reply:
        reply = await event.get_reply_message()
        autosms_target = reply.sender_id
        with open(AUTOSMS_FILE, "w") as f:
            json.dump({"target": autosms_target, "text": autosms_text}, f)
        await event.reply(f"🤖 Автоответ активирован для пользователя ID {autosms_target}")
    else:
        await event.reply("Ответь на сообщение пользователя, чтобы включить автоответ.")

@client.on(events.NewMessage(pattern=r"^\.автосмсстоп$"))
async def autosms_stop(event):
    global autosms_target, autosms_text
    autosms_target = None
    autosms_text = None
    if os.path.exists(AUTOSMS_FILE):
        os.remove(AUTOSMS_FILE)
    await event.reply("🛑 Автоответ остановлен.")

@client.on(events.NewMessage)
async def autosms_react(event):
    global autosms_target, autosms_text
    if autosms_target and autosms_text and event.sender_id == autosms_target:
        await event.reply(autosms_text)

# ------------------ ред/дд/тук ------------------
@client.on(events.NewMessage(pattern=r"^\.ред (\d+) (.+)$"))
async def edit_messages(event):
    count = int(event.pattern_match.group(1))
    new_text = event.pattern_match.group(2)
    async for msg in client.iter_messages(event.chat_id, from_user="me", limit=count + 1):
        if msg.id != event.message.id:
            await msg.edit(new_text)
    await event.delete()

@client.on(events.NewMessage(pattern=r"^\.дд (\d+)$"))
async def delete_messages(event):
    count = int(event.pattern_match.group(1))
    msgs_to_del = []
    async for msg in client.iter_messages(event.chat_id, from_user="me", limit=count + 1):
        msgs_to_del.append(msg.id)
    await client.delete_messages(event.chat_id, msgs_to_del)
    await event.delete()

@client.on(events.NewMessage(pattern=r"^\.тук ред (.+)$"))
async def add_edit_alias(event):
    args = event.pattern_match.group(1).strip()
    if args == "-":
        aliases["ред"].clear()
        save_aliases()
        await event.reply("✅ Алиасы редактирования сброшены.")
        return
    parts = args.split(" ", 2)
    if len(parts) < 3:
        await event.reply("❌ Используй: `.тук ред [алиас] [кол-во] [текст]`")
        return
    alias, count, text = parts[0], parts[1], parts[2]
    aliases["ред"][alias] = {"count": int(count), "text": text}
    save_aliases()
    await event.reply(f"✅ Алиас `{alias}` создан: редактировать {count} сообщений на «{text}»")

@client.on(events.NewMessage(pattern=r"^\.тук дд (.+)$"))
async def add_delete_alias(event):
    args = event.pattern_match.group(1).strip()
    if args == "-":
        aliases["дд"].clear()
        save_aliases()
        await event.reply("✅ Алиасы удаления сброшены.")
        return
    parts = args.split(" ")
    if len(parts) < 2:
        await event.reply("❌ Используй: `.тук дд [алиас] [кол-во]`")
        return
    alias, count = parts[0], int(parts[1])
    aliases["дд"][alias] = {"count": count}
    save_aliases()
    await event.reply(f"✅ Алиас `{alias}` создан: удалять {count} сообщений.")

@client.on(events.NewMessage)
async def handle_aliases(event):
    text = event.raw_text.strip()
    for alias, data in aliases["ред"].items():
        if text.startswith(alias):
            count = data["count"]
            new_text = data["text"]
            async for msg in client.iter_messages(event.chat_id, from_user="me", limit=count + 1):
                if msg.id != event.message.id:
                    await msg.edit(new_text)
            await event.delete()
            return
    for alias, data in aliases["дд"].items():
        if text.startswith(alias):
            count = data["count"]
            msgs_to_del = []
            async for msg in client.iter_messages(event.chat_id, from_user="me", limit=count + 1):
                msgs_to_del.append(msg.id)
            await client.delete_messages(event.chat_id, msgs_to_del)
            await event.delete()
            return

# ------------------ запуск ------------------
async def main():
    global autosms_target, autosms_text
    if os.path.exists(AUTOSMS_FILE):
        with open(AUTOSMS_FILE, "r") as f:
            data = json.load(f)
            autosms_target = data.get("target")
            autosms_text = data.get("text")
    print("🚀 Userbot запущен!")
    await client.start()
    me = await client.get_me()
    print(f"✅ Авторизован как {me.first_name} (@{me.username})")
    print("Команды: .ред, .дд, .тук, .флуд, .автосмс, .автосмсстоп, .tmpl, .байт, .мут, .мутстоп")
    await client.run_until_disconnected()

if __name__ == "__main__":
    with client:
        client.loop.run_until_complete(main())