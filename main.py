import os
import threading
import asyncio
import random
import time
from http.server import BaseHTTPRequestHandler, HTTPServer
from telegram import Update
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

OWNER_ID = 8486672898
LOG_CHANNEL_ID = -1003107269526
bot_active = True
last_messages = {}

# ❤️ Романтические данные
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

# 💋 /kiss — страстные поцелуи
KISS_GIFS = [
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
    "https://media.giphy.com/media/11cT0zEoXgK1bO/giphy.gif",
    "https://media.giphy.com/media/3o6Zt6ML6BklcajjsA/giphy.gif",
    "https://media.giphy.com/media/l4pTfx2qLszoacZRS/giphy.gif",
]

# 🤗 /hug — страстные объятия
HUG_GIFS = [
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
    "https://media.giphy.com/media/l4pTfx2qLszoacZRS/giphy.gif",
    "https://media.giphy.com/media/26BRuo6sLetdllPAQ/giphy.gif",
    "https://media.giphy.com/media/3ohc1h8TbCac4z6l8Q/giphy.gif",
    "https://media.giphy.com/media/3o6Zt6ML6BklcajjsA/giphy.gif",
]

sent_kiss_gifs = set()
sent_hug_gifs = set()
last_action = None  # Для чередования kiss/hug

# 🎁 Подарки
GIFTS_ROMANTIC = [
    "💐 Букет слов и немного нежности",
    "🍫 Шоколад из чувства симпатии",
    "💎 Осколок звезды с небес"
]
GIFTS_FUNNY = [
    "🍕 Один кусочек любви и три крошки заботы",
    "🍟 Картошка с соусом симпатии",
    "☕ Чашка тепла и добрых чувств"
]

# -----------------------
# 🌐 Мини-вебсервер
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
    try:
        if "Conflict" in text:
            return  # Игнорируем ошибку конфликта
        if context and context.bot:
            await context.bot.send_message(chat_id=LOG_CHANNEL_ID, text=text)
    except Exception:
        print("LOG:", text)

# -----------------------
# 💾 Сохранение чатов
# -----------------------
async def save_chat(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_chat:
        last_messages[update.effective_chat.id] = update.effective_chat.id

# -----------------------
# ⚙️ Включение/выключение
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
# 💋 /kiss — страстные поцелуи и объятия
# -----------------------
async def kiss_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    global last_action
    await save_chat(update, context)
    if not bot_active or update.message is None:
        return

    args = update.message.text.split(maxsplit=1)
    if len(args) < 2:
        await update.message.reply_text("😘 Используй: /kiss @username")
        return

    sender = update.effective_user.username or update.effective_user.first_name
    target = args[1].replace("@", "")

    # Чередуем действия
    if last_action == "kiss":
        action = "hug"
    elif last_action == "hug":
        action = "kiss"
    else:
        action = random.choice(["kiss", "hug"])
    last_action = action

    if action == "kiss":
        gifs, sent_set, emoji, text = KISS_GIFS, sent_kiss_gifs, "💋", "поцелуй"
    else:
        gifs, sent_set, emoji, text = HUG_GIFS, sent_hug_gifs, "🤗", "объятие"

    available = list(set(gifs) - sent_set)
    if not available:
        sent_set.clear()
        available = gifs.copy()
    gif = random.choice(available)
    sent_set.add(gif)

    await update.message.reply_text(f"{emoji} @{sender} отправляет @{target} {text}...")
    await asyncio.sleep(0.5)
    await update.message.reply_animation(gif)
    await asyncio.sleep(0.5)
    phrase = random.choice([
        "💞 Между вами пробежала искра нежности!",
        "💖 Любовь витает в воздухе!",
        "🌸 Тепло и нежность переплелись вместе.",
        "💫 Пусть этот момент длится вечно!",
        "🔥 Сердца бьются в унисон.",
    ])
    await context.bot.send_message(chat_id=update.effective_chat.id, text=phrase)
    await send_log(context, f"/kiss: @{sender} -> @{target} ({text})")

# -----------------------
# 💘 /love — совместимость
# -----------------------
async def love_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await save_chat(update, context)
    if not bot_active or update.message is None:
        return
    args = update.message.text.split(maxsplit=1)
    if len(args) < 2:
        await update.message.reply_text("💘 Используй: /love @username")
        return

    target = args[1].replace("@", "")
    sender = update.effective_user.username or update.effective_user.first_name
    love_percent = random.randint(0, 100)
    level_text = next(text for low, high, text in LOVE_LEVELS if low <= love_percent <= high)
    phrase = random.choice(LOVE_PHRASES)
    msg = f"💖 Совместимость между @{sender} и @{target}: {love_percent}%\n{level_text}\n✨ {phrase}"
    await update.message.reply_text(msg)
    await send_log(context, f"/love: @{sender} ❤️ @{target} = {love_percent}%")

# -----------------------
# 🎁 /gift — подарки
# -----------------------
async def gift_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await save_chat(update, context)
    if not bot_active or update.message is None:
        return
    args = update.message.text.split(maxsplit=1)
    if len(args) < 2:
        await update.message.reply_text("🎁 Используй: /gift @username")
        return

    sender = update.effective_user.username or update.effective_user.first_name
    target = args[1].replace("@", "")
    gift = random.choice(GIFTS_ROMANTIC + GIFTS_FUNNY)
    await update.message.reply_text(f"🎁 @{sender} дарит @{target}: {gift}")
    await send_log(context, f"/gift: @{sender} 🎁 @{target}")

# -----------------------
# 🚀 /start
# -----------------------
async def start_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_chat.type != "private":
        return
    await update.message.reply_text(
        "💞 Привет! Я LoveBot 💖\n"
        "Команды:\n"
        "/love <@username>\n"
        "/gift <@username>\n"
        "/kiss <@username>\n"
        "/onbot /offbot\n"
    )

# -----------------------
# ⚠️ Ошибки
# -----------------------
async def error_handler(update: object, context: ContextTypes.DEFAULT_TYPE):
    err = str(context.error)
    if "Conflict" in err:
        return
    print(f"⚠️ Ошибка: {err}")
    try:
        await context.bot.send_message(chat_id=LOG_CHANNEL_ID, text=f"⚠️ Ошибка: {err}")
    except Exception:
        pass

# -----------------------
# 🚀 Запуск
# -----------------------
if __name__ == "__main__":
    app = ApplicationBuilder().token(TELEGRAM_TOKEN).build()

    app.add_handler(CommandHandler("start", start_cmd))
    app.add_handler(CommandHandler("onbot", onbot))
    app.add_handler(CommandHandler("offbot", offbot))
    app.add_handler(CommandHandler("kiss", kiss_cmd))
    app.add_handler(CommandHandler("love", love_cmd))
    app.add_handler(CommandHandler("gift", gift_cmd))
    app.add_handler(MessageHandler(filters.TEXT & (~filters.COMMAND), save_chat))
    app.add_error_handler(error_handler)

    print("✅ LoveBot готов к запуску!")
    app.run_polling()
