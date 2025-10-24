#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import os
import threading
import asyncio
import random
import time
from datetime import datetime
from http.server import BaseHTTPRequestHandler, HTTPServer
from typing import Dict, Set

from telegram import Update, ChatPermissions
from telegram.ext import (
    ApplicationBuilder,
    CommandHandler,
    MessageHandler,
    filters,
    ContextTypes
)

# -----------------------
# 🔑 Конфигурация
# -----------------------
TELEGRAM_TOKEN = os.environ.get("TELEGRAM_TOKEN")
if not TELEGRAM_TOKEN:
    raise RuntimeError("Ошибка: TELEGRAM_TOKEN не установлен!")

# Задай своё
OWNER_ID = int(os.environ.get("OWNER_ID", "8486672898"))
LOG_CHANNEL_ID = int(os.environ.get("LOG_CHANNEL_ID", "-1003107269526"))

bot_active = True

# Словарь для хранения чатов и состояния (в памяти)
last_messages: Dict[int, int] = {}          # chat_id -> chat_id (simple set)
warnings: Dict[int, Dict[int, int]] = {}    # chat_id -> {user_id: warnings_count}
banned_users: Dict[int, Set[int]] = {}      # chat_id -> set(user_ids)
greetings: Dict[int, str] = {}              # chat_id -> greeting text
rules: Dict[int, str] = {}                  # chat_id -> rules text

# -----------------------
# ❤️ Тексты и данные
# -----------------------
LOVE_PHRASES = [
    "Ты мне дорог", "Я рад, что ты есть", "Ты особенная",
    "Ты мой человек", "Ты делаешь день лучше", "Ты просто счастье",
    "Ты как свет в тумане", "Ты вдохновляешь", "Ты важна для меня",
    "Ты мое чудо", "Ты наполняешь день теплом", "Ты моя радость",
    "С тобой спокойно", "Ты просто невероятна", "Ты мой уют", "Ты моё всё"
]

LOVE_LEVELS = [
    (0, 10, "💔 Лёд между сердцами..."),
    (11, 25, "🌧️ Едва заметная искра."),
    (26, 45, "💫 Симпатия растёт."),
    (46, 65, "💞 Нежное притяжение."),
    (66, 80, "💖 Сердца бьются в унисон."),
    (81, 95, "💘 Это почти любовь."),
    (96, 100, "💍 Судьба связала вас навсегда."),
]

GIFTS_ROMANTIC = [
    "💐 Букет слов и немного нежности",
    "🍫 Шоколад из чувства симпатии",
    "💎 Осколок звезды с небес",
]
GIFTS_FUNNY = [
    "🍕 Один кусочек любви и три крошки заботы",
    "🍟 Картошка с соусом симпатии",
    "☕ Чашка тепла и добрых чувств",
]

# -----------------------
# 💋 Страстные поцелуи и объятия (много ссылок)
#    — убрал любые неявные NSFW, но все — явные романтические GIF
# -----------------------
KISS_GIFS = [
    # 20+ gif ссылок для поцелуев
    "https://media.giphy.com/media/l0MYC0LajbaPoEADu/giphy.gif",
    "https://media.giphy.com/media/MDJ9IbxxvDUQM/giphy.gif",
    "https://media.giphy.com/media/ZqlvCTNHpqrio/giphy.gif",
    "https://media.giphy.com/media/wnsgren9NtITS/giphy.gif",
    "https://media.giphy.com/media/12VXIxKaIEarL2/giphy.gif",
    "https://media.giphy.com/media/FqBTvSNjNzeZG/giphy.gif",
    "https://media.giphy.com/media/3oz8xAFtqoOUUrsh7W/giphy.gif",
    "https://media.giphy.com/media/3ohc1h8TbCac4z6l8Q/giphy.gif",
    "https://media.giphy.com/media/26BRuo6sLetdllPAQ/giphy.gif",
    "https://media.giphy.com/media/3o7qDEq2bMbcbPRQ2c/giphy.gif",
    "https://media.giphy.com/media/l0HlvtIPzPdt2usKs/giphy.gif",
    "https://media.giphy.com/media/xUPGcgtKxm4XlPZy7y/giphy.gif",
    "https://media.giphy.com/media/3o7aD6N0CvlV8xBkqQ/giphy.gif",
    "https://media.giphy.com/media/l41YtZOb9EUABnuqA/giphy.gif",
    "https://media.giphy.com/media/3oz8xIQDfxaB8V1bAA/giphy.gif",
    "https://media.giphy.com/media/3o7aD2saalBwwftBIY/giphy.gif",
    "https://media.giphy.com/media/l0ExncehJzexFpRHq/giphy.gif",
    "https://media.giphy.com/media/3o6Zt6ML6BklcajjsA/giphy.gif",
    "https://media.giphy.com/media/11cT0zEoXgK1bO/giphy.gif",
    "https://media.giphy.com/media/l4pTfx2qLszoacZRS/giphy.gif",
    "https://media.giphy.com/media/3o6gbbuLW76jkt8vIc/giphy.gif",
    "https://media.giphy.com/media/5GoVLqeAOo6PK/giphy.gif",
    "https://media.giphy.com/media/TdfyKrN7HGTIY/giphy.gif",
]

HUG_GIFS = [
    # 20+ gif ссылок для объятий
    "https://media.giphy.com/media/sUIZWMnfd4Mb6/giphy.gif",
    "https://media.giphy.com/media/od5H3PmEG5EVq/giphy.gif",
    "https://media.giphy.com/media/l2QDM9Jnim1YVILXa/giphy.gif",
    "https://media.giphy.com/media/143vPc6b08locw/giphy.gif",
    "https://media.giphy.com/media/3bqtLDeiDtwhq/giphy.gif",
    "https://media.giphy.com/media/XpgOZHuDfIkoM/giphy.gif",
    "https://media.giphy.com/media/3o6Zt481isNVuQI1l6/giphy.gif",
    "https://media.giphy.com/media/l0MYt5jPR6QX5pnqM/giphy.gif",
    "https://media.giphy.com/media/3oz8xAf8hGqJwzN1hG/giphy.gif",
    "https://media.giphy.com/media/xT9IgIc0lryrxvqVGM/giphy.gif",
    "https://media.giphy.com/media/3o7aD5tv1ogNBtDhDi/giphy.gif",
    "https://media.giphy.com/media/26BRuo6sLetdllPAQ/giphy.gif",
    "https://media.giphy.com/media/3o6Zt6ML6BklcajjsA/giphy.gif",
    "https://media.giphy.com/media/3o7aD6N0CvlV8xBkqQ/giphy.gif",
    "https://media.giphy.com/media/11sBLVxNs7v6w/giphy.gif",
    "https://media.giphy.com/media/3o6vXT8s7b6GZPqQsg/giphy.gif",
    "https://media.giphy.com/media/3o85xI5X4j7a4iUBsE/giphy.gif",
    "https://media.giphy.com/media/3oEduSbSGpGaRX2Vri/giphy.gif",
    "https://media.giphy.com/media/l2JJH3pQ8i3sK/giphy.gif",
    "https://media.giphy.com/media/l49JZ0kJmZSTy/giphy.gif",
]

# Сеты для отслеживания отправленных гифов по чату
sent_kiss_gifs_per_chat: Dict[int, Set[str]] = {}
sent_hug_gifs_per_chat: Dict[int, Set[str]] = {}
last_action_per_chat: Dict[int, str] = {}  # chat_id -> "kiss" or "hug"

# -----------------------
# 🌐 Мини-вебсервер (ping endpoint для Render/Heroku и т.д.)
# -----------------------
def run_web():
    class Handler(BaseHTTPRequestHandler):
        def do_GET(self):
            self.send_response(200)
            self.end_headers()
            self.wfile.write("LoveBot is alive 💖".encode("utf-8"))

    port = int(os.environ.get("PORT", 10000))
    HTTPServer(("0.0.0.0", port), Handler).serve_forever()

threading.Thread(target=run_web, daemon=True).start()

# -----------------------
# 📜 Логирование
# -----------------------
async def send_log(context: ContextTypes.DEFAULT_TYPE, text: str):
    # Не спамим логом конфликтные сообщения
    if "Conflict" in text:
        return
    try:
        if context and context.bot:
            await context.bot.send_message(chat_id=LOG_CHANNEL_ID, text=text)
    except Exception:
        # Если лог не уходит — печатаем в STDOUT (Render покажет)
        print("LOG:", text)

# -----------------------
# 💾 Хелпер — сохраняем чат (используется как handler тоже)
# -----------------------
async def save_chat(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_chat:
        last_messages[update.effective_chat.id] = update.effective_chat.id

# -----------------------
# ⚙️ Включение / выключение бота (только владелец)
# -----------------------
async def onbot(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await save_chat(update, context)
    global bot_active
    if update.effective_user.id != OWNER_ID:
        await update.message.reply_text("🚫 Только владелец может включить бота.")
        return
    bot_active = True
    await update.message.reply_text("🔔 Бот снова активен!")
    await send_log(context, "Бот включён.")

async def offbot(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await save_chat(update, context)
    global bot_active
    if update.effective_user.id != OWNER_ID:
        await update.message.reply_text("🚫 Только владелец может выключить бота.")
        return
    bot_active = False
    await update.message.reply_text("⚠️ Бот отключён.")
    await send_log(context, "Бот отключён.")

# -----------------------
# /start
# -----------------------
async def start_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await save_chat(update, context)
    if update.effective_chat and update.effective_chat.type == "private":
        await update.message.reply_text(
            "💞 Привет! Я LoveBot 💖\n"
            "Команды:\n"
            "/love <@username> — проверить совместимость 💘\n"
            "/gift <@username> — отправить подарок 🎁\n"
            "/kiss <@username> — страстный поцелуй/объятие 💋\n"
            "/warn /ban /kick — модерация (только админы)\n"
            "/onbot /offbot — включить/выключить бота (только владелец)\n"
            "/all <текст> — рассылка всем (только владелец)\n"
            "/profile /id — информация о юзере\n"
        )

# -----------------------
# 💘 /love — как было раньше
# -----------------------
async def love_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await save_chat(update, context)
    if not bot_active or update.message is None:
        return
    args = update.message.text.split(maxsplit=1)
    initiator = update.effective_user.username or update.effective_user.first_name
    target = args[1].replace("@", "") if len(args) > 1 else initiator

    score = random.randint(0, 100)
    bar_len = 20
    filled = score * bar_len // 100
    hearts = "❤️" * (filled // 2)
    bars = hearts + "🖤" * (bar_len - len(hearts))

    await update.message.reply_text("💘 Определяем уровень любви...")
    await asyncio.sleep(0.5)
    atmosphere = random.choice([
        "✨ Судьба соединяет сердца...",
        "💞 Любовь витает в воздухе...",
        "🌹 Сердца бьются всё чаще...",
        "🔥 Между вами искра...",
    ])
    await context.bot.send_message(chat_id=update.effective_chat.id, text=atmosphere)
    await asyncio.sleep(0.7)
    result_text = f"💞 @{initiator} 💖 @{target}\n💘 Совместимость: {score}%\n[{bars}]"
    await context.bot.send_message(chat_id=update.effective_chat.id, text=result_text)
    await asyncio.sleep(0.5)
    category = next((lbl for (lo, hi, lbl) in LOVE_LEVELS if lo <= score <= hi), "💞 Нежные чувства")
    phrase = random.choice(LOVE_PHRASES)
    final_text = f"💖 {category}\n🌸 {phrase}\n💬 Истинная любовь всегда найдёт путь 💫"
    await context.bot.send_message(chat_id=update.effective_chat.id, text=final_text)
    await send_log(context, f"/love: @{initiator} -> @{target} = {score}%")

# -----------------------
# 🎁 /gift — простой
# -----------------------
async def gift_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await save_chat(update, context)
    if not bot_active or update.message is None:
        return
    args = update.message.text.split(maxsplit=1)
    if len(args) < 2:
        await update.message.reply_text("🎁 Используй: /gift @username")
        return
    giver = update.effective_user.username or update.effective_user.first_name
    target = args[1].replace("@", "")
    gift = random.choice(GIFTS_ROMANTIC + GIFTS_FUNNY)
    await update.message.reply_text(f"🎁 @{giver} дарит @{target}: {gift}")
    await send_log(context, f"/gift: @{giver} -> @{target} ({gift})")

# -----------------------
# 💋 /kiss — только страстные поцелуи и объятия, без повторов, чередование
# -----------------------
async def kiss_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await save_chat(update, context)
    if not bot_active or update.message is None:
        return

    chat_id = update.effective_chat.id
    args = update.message.text.split(maxsplit=1)
    if len(args) < 2:
        await update.message.reply_text("😘 Используй: /kiss @username")
        return

    sender = update.effective_user.username or update.effective_user.first_name
    target = args[1].replace("@", "")

    # Чередование kiss/hug по чату, чтобы не было подряд одного и того же
    last = last_action_per_chat.get(chat_id)
    if last == "kiss":
        action = "hug"
    elif last == "hug":
        action = "kiss"
    else:
        action = random.choice(["kiss", "hug"])
    last_action_per_chat[chat_id] = action

    if action == "kiss":
        gifs = KISS_GIFS
        sent_set = sent_kiss_gifs_per_chat.setdefault(chat_id, set())
        emoji = "💋"
        verb = "поцелуй"
    else:
        gifs = HUG_GIFS
        sent_set = sent_hug_gifs_per_chat.setdefault(chat_id, set())
        emoji = "🤗"
        verb = "объятие"

    # Выбираем неиспользованную гифку в этом чате
    available = list(set(gifs) - sent_set)
    if not available:
        # если исчерпали — сбрасываем историю для этого типа в чате
        sent_set.clear()
        available = gifs.copy()
    gif = random.choice(available)
    sent_set.add(gif)

    await update.message.reply_text(f"{emoji} @{sender} отправляет @{target} {verb}...")
    await asyncio.sleep(0.4)
    try:
        await update.message.reply_animation(gif)
    except Exception:
        # fallback: отправить ссылку
        await update.message.reply_text(gif)
    await asyncio.sleep(0.4)
    phrase = random.choice([
        "💞 Между вами пробежала искра нежности!",
        "💖 Любовь витает в воздухе!",
        "🌸 Тепло и нежность переплелись вместе.",
        "💫 Пусть этот момент длится вечно!",
        "🔥 Сердца бьются в унисон.",
    ])
    await context.bot.send_message(chat_id=chat_id, text=phrase)
    await send_log(context, f"/kiss: @{sender} -> @{target} ({verb})")

# -----------------------
# /all — рассылка (только владелец)
# -----------------------
async def all_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await save_chat(update, context)
    if update.effective_user.id != OWNER_ID:
        await update.message.reply_text("🚫 Только владелец может использовать /all")
        return
    text = update.message.text.partition(" ")[2].strip()
    if not text:
        await update.message.reply_text("❌ Введи текст: /all <текст>")
        return
    count = 0
    for chat_id in list(last_messages.keys()):
        try:
            await context.bot.send_message(chat_id=chat_id, text=text)
            count += 1
            await asyncio.sleep(0.05)
        except Exception:
            continue
    await update.message.reply_text(f"✅ Рассылка завершена, отправлено в ~{count} чатов.")
    await send_log(context, f"/all: отправлено в {count} чатов.")

# -----------------------
# Модерирование: warn, ban, unban, kick, purge
# -----------------------
async def warn_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await save_chat(update, context)
    if not update.message.reply_to_message:
        await update.message.reply_text("Используй команду в ответ на сообщение пользователя, которого хочешь предупредить.")
        return
    chat_id = update.effective_chat.id
    actor = update.effective_user
    # проверка прав (простая) — можно улучшить
    try:
        member = await context.bot.get_chat_member(chat_id, actor.id)
        if not (member.status in ("administrator", "creator") or actor.id == OWNER_ID):
            await update.message.reply_text("🚫 Только администраторы могут выдавать предупреждения.")
            return
    except Exception:
        pass

    target = update.message.reply_to_message.from_user
    warns = warnings.setdefault(chat_id, {})
    warns[target.id] = warns.get(target.id, 0) + 1
    await update.message.reply_text(f"⚠️ @{target.username or target.full_name} получил предупреждение. Теперь: {warns[target.id]}")

async def ban_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await save_chat(update, context)
    if not update.message.reply_to_message:
        await update.message.reply_text("Используй команду в ответ на сообщение пользователя, которого хочешь забанить.")
        return
    chat_id = update.effective_chat.id
    actor = update.effective_user
    try:
        member = await context.bot.get_chat_member(chat_id, actor.id)
        if not (member.status in ("administrator", "creator") or actor.id == OWNER_ID):
            await update.message.reply_text("🚫 Только администраторы могут банить.")
            return
    except Exception:
        pass

    target = update.message.reply_to_message.from_user
    try:
        await context.bot.ban_chat_member(chat_id=chat_id, user_id=target.id)
        banned_users.setdefault(chat_id, set()).add(target.id)
        await update.message.reply_text(f"🔨 @{target.username or target.full_name} забанен.")
        await send_log(context, f"/ban: @{target.username or target.full_name} ({target.id}) в {chat_id}")
    except Exception as e:
        await update.message.reply_text(f"Ошибка при бане: {e}")

async def unban_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await save_chat(update, context)
    if not update.message.reply_to_message:
        await update.message.reply_text("Используй команду в ответ на сообщение (или 'unban <id>').")
        return
    chat_id = update.effective_chat.id
    actor = update.effective_user
    try:
        member = await context.bot.get_chat_member(chat_id, actor.id)
        if not (member.status in ("administrator", "creator") or actor.id == OWNER_ID):
            await update.message.reply_text("🚫 Только администраторы могут разбанивать.")
            return
    except Exception:
        pass

    target = update.message.reply_to_message.from_user
    try:
        await context.bot.unban_chat_member(chat_id=chat_id, user_id=target.id)
        banned_users.get(chat_id, set()).discard(target.id)
        await update.message.reply_text(f"✅ @{target.username or target.full_name} разбанен.")
        await send_log(context, f"/unban: @{target.username or target.full_name} ({target.id}) в {chat_id}")
    except Exception as e:
        await update.message.reply_text(f"Ошибка при разбане: {e}")

async def kick_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await save_chat(update, context)
    if not update.message.reply_to_message:
        await update.message.reply_text("Используй команду в ответ на сообщение пользователя, которого хочешь кикнуть.")
        return
    chat_id = update.effective_chat.id
    actor = update.effective_user
    try:
        member = await context.bot.get_chat_member(chat_id, actor.id)
        if not (member.status in ("administrator", "creator") or actor.id == OWNER_ID):
            await update.message.reply_text("🚫 Только администраторы могут кикать.")
            return
    except Exception:
        pass

    target = update.message.reply_to_message.from_user
    try:
        await context.bot.ban_chat_member(chat_id=chat_id, user_id=target.id, until_date=int(time.time()) + 5)
        await context.bot.unban_chat_member(chat_id=chat_id, user_id=target.id)  # чтобы это был kick, не перманент
        await update.message.reply_text(f"👢 @{target.username or target.full_name} кикнут(а).")
        await send_log(context, f"/kick: @{target.username or target.full_name} ({target.id}) в {chat_id}")
    except Exception as e:
        await update.message.reply_text(f"Ошибка при кике: {e}")

async def purge_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await save_chat(update, context)
    # простая реализация: удаляет N сообщений выше команды (если бот имеет право)
    chat_id = update.effective_chat.id
    actor = update.effective_user
    try:
        member = await context.bot.get_chat_member(chat_id, actor.id)
        if not (member.status in ("administrator", "creator") or actor.id == OWNER_ID):
            await update.message.reply_text("🚫 Только администраторы могут чистить чат.")
            return
    except Exception:
        pass

    args = context.args
    if not args or not args[0].isdigit():
        await update.message.reply_text("Используй: /purge <количество>")
        return
    n = int(args[0])
    # Удаляем n сообщений сверху (бот удаляет только те, на которые у него есть права)
    try:
        # Получаем последние n+1 сообщений (включая команду)
        async for msg in context.bot.get_chat(chat_id).get_history(limit=n+1):
            try:
                await context.bot.delete_message(chat_id=chat_id, message_id=msg.message_id)
            except Exception:
                pass
        await update.message.reply_text(f"🧹 Попытка удалить {n} сообщений (по ограничениям Telegram).")
    except Exception as e:
        await update.message.reply_text(f"Ошибка при очистке: {e}")

# -----------------------
# Профили / id / profile
# -----------------------
async def id_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await save_chat(update, context)
    # если в ответ на сообщение — инфа по тому, иначе по вызывающему
    target = update.message.reply_to_message.from_user if update.message.reply_to_message else update.effective_user
    uid = target.id
    name = target.full_name
    username = f"@{target.username}" if target.username else "-"
    await update.message.reply_text(f"Информация:\nID: {uid}\nИмя: {name}\nЮзернейм: {username}")

async def profile_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await save_chat(update, context)
    # простой профиль — мы не имеем доступа к рег. дате из API без сторонних сервисов
    target = update.message.reply_to_message.from_user if update.message.reply_to_message else update.effective_user
    uid = target.id
    name = target.full_name
    username = f"@{target.username}" if target.username else "-"
    # демонстрационный профиль (локальный)
    warns = warnings.get(update.effective_chat.id, {}).get(uid, 0)
    is_banned = uid in banned_users.get(update.effective_chat.id, set())
    await update.message.reply_text(
        f"Профиль {username} ({name}):\n"
        f"ID: {uid}\n"
        f"Предупреждений: {warns}\n"
        f"В бане: {'Да' if is_banned else 'Нет'}"
    )

# -----------------------
# Настройка приветствия и правил (простой storage в памяти)
# -----------------------
async def set_greeting_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await save_chat(update, context)
    actor = update.effective_user
    try:
        member = await context.bot.get_chat_member(update.effective_chat.id, actor.id)
        if not (member.status in ("administrator", "creator") or actor.id == OWNER_ID):
            await update.message.reply_text("🚫 Только админы могут устанавливать приветствие.")
            return
    except Exception:
        pass

    text = update.message.text.partition(" ")[2].strip()
    if not text:
        await update.message.reply_text("Используй: /setgreeting <текст на новой строке>")
        return
    greetings[update.effective_chat.id] = text
    await update.message.reply_text("✅ Приветствие установлено.")

async def set_rules_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await save_chat(update, context)
    actor = update.effective_user
    try:
        member = await context.bot.get_chat_member(update.effective_chat.id, actor.id)
        if not (member.status in ("administrator", "creator") or actor.id == OWNER_ID):
            await update.message.reply_text("🚫 Только админы могут устанавливать правила.")
            return
    except Exception:
        pass

    text = update.message.text.partition(" ")[2].strip()
    if not text:
        await update.message.reply_text("Используй: /setrules <текст на новой строке>")
        return
    rules[update.effective_chat.id] = text
    await update.message.reply_text("✅ Правила установлены.")

async def show_rules_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await save_chat(update, context)
    text = rules.get(update.effective_chat.id)
    if not text:
        await update.message.reply_text("Правила не установлены.")
    else:
        await update.message.reply_text(f"📜 Правила чата:\n{text}")

# -----------------------
# Обработчик ошибок — игнорируем Conflict и не шлём их в логи
# -----------------------
async def error_handler(update: object, context: ContextTypes.DEFAULT_TYPE):
    err_text = str(context.error)
    # Не спамим логом конфликтного сообщения (обычно возникает при одновременном использовании getUpdates/webhook)
    if "Conflict" in err_text or "terminated by other getUpdates request" in err_text:
        print("Игнорируем Conflict:", err_text)
        return
    print(f"⚠️ Ошибка: {err_text}")
    try:
        if context and context.bot:
            await context.bot.send_message(chat_id=LOG_CHANNEL_ID, text=f"⚠️ Ошибка: {err_text}")
    except Exception:
        pass

# -----------------------
# Фоновая задача: очистка старых сохранений (опционально)
# -----------------------
def background_cleanup():
    while True:
        # простой РАМЕНОВСКИЙ "периодический" таск — чистим старые записи (если нужно)
        try:
            # Nothing heavy for now — sleep and continue
            time.sleep(3600)
        except Exception:
            time.sleep(60)

threading.Thread(target=background_cleanup, daemon=True).start()

# -----------------------
# 🚀 Запуск бота
# -----------------------
if __name__ == "__main__":
    app = ApplicationBuilder().token(TELEGRAM_TOKEN).build()

    # Команды
    app.add_handler(CommandHandler("start", start_cmd))
    app.add_handler(CommandHandler("onbot", onbot))
    app.add_handler(CommandHandler("offbot", offbot))

    app.add_handler(CommandHandler("love", love_cmd))
    app.add_handler(CommandHandler("gift", gift_cmd))
    app.add_handler(CommandHandler("kiss", kiss_cmd))

    app.add_handler(CommandHandler("all", all_cmd))

    # Модерация
    app.add_handler(CommandHandler("warn", warn_cmd))
    app.add_handler(CommandHandler("ban", ban_cmd))
    app.add_handler(CommandHandler("unban", unban_cmd))
    app.add_handler(CommandHandler("kick", kick_cmd))
    app.add_handler(CommandHandler("purge", purge_cmd))

    # Профили / info
    app.add_handler(CommandHandler("id", id_cmd))
    app.add_handler(CommandHandler("profile", profile_cmd))

    # Настройки чата
    app.add_handler(CommandHandler("setgreeting", set_greeting_cmd))
    app.add_handler(CommandHandler("setrules", set_rules_cmd))
    app.add_handler(CommandHandler("rules", show_rules_cmd))

    # Сохраняем чаты при любых текстовых сообщениях
    app.add_handler(MessageHandler(filters.TEXT & (~filters.COMMAND), save_chat))

    app.add_error_handler(error_handler)

    print("✅ LoveBot запущен и готов к романтике 💞")
    app.run_polling()
