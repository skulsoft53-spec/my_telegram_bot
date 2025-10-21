import os
import threading
import time
import re
from http.server import BaseHTTPRequestHandler, HTTPServer
from telegram import Update
from telegram.ext import (
    ApplicationBuilder, MessageHandler, CommandHandler,
    filters, ContextTypes
)
import random

TELEGRAM_TOKEN = os.environ.get("TELEGRAM_TOKEN")
if not TELEGRAM_TOKEN:
    raise RuntimeError("Ошибка: TELEGRAM_TOKEN не установлен!")

TARGET_USERNAMES = ["Habib471"]
SIGNATURE_USER = "Habib471"
SIGNATURE_TEXT = "Полюби Апачи, как он тебя 💞"
OWNER_USERNAME = "bxuwy"

bot_active = True
last_messages = {}
muted_users = {}

LOVE_PHRASES = [
    "Ты мне дорог", "Я рад, что ты есть", "Ты особенная", "Ты мой человек",
    "Ты мой уют", "Ты просто счастье", "Ты делаешь день лучше", "Ты мой свет",
    "Ты делаешь меня лучше", "Ты моя радость", "Ты моё вдохновение",
    "Ты — мой дом", "Ты — мой смысл", "Ты — моё всё", "Ты — мой человек",
    "Ты — человек, которого хочется беречь", "Ты — мой нежный свет",
    "Ты — человек, которого я не хочу терять", "Ты — дыхание моей души",
    "Ты — человек, который делает мир красивее"
]

SPECIAL_PHRASES = [
    "С тобой даже тишина звучит красиво 💫",
    "Ты — причина улыбки Апачи 💖",
    "Когда ты рядом, весь мир добрее 🌸",
    "Ты — вдохновение Апачи 💞",
    "Ты — свет, в котором он живёт ☀️",
    "Полюби Апачи, как он тебя 💞"
]

LOVE_JOKES = [
    "Ты как Wi-Fi — рядом, и всё идеально 😄",
    "Ты — батарейка, без тебя теряю заряд 🔋",
    "Ты — любимая песня на повторе 🎶"
]

LOVE_LEVELS = [
    (0, 10, "💔 Лёд между сердцами..."),
    (11, 25, "🌧️ Искра только рождается."),
    (26, 45, "💫 Симпатия растёт."),
    (46, 65, "💞 Нежное притяжение."),
    (66, 80, "💖 Сердца бьются в унисон."),
    (81, 95, "💘 Это почти любовь."),
    (96, 100, "💍 Любовь навсегда.")
]

def run_web():
    class Handler(BaseHTTPRequestHandler):
        def do_GET(self):
            self.send_response(200)
            self.end_headers()
            self.wfile.write(b"LoveBot is running <3")
    port = int(os.environ.get("PORT", 10000))
    HTTPServer(("0.0.0.0", port), Handler).serve_forever()

threading.Thread(target=run_web, daemon=True).start()

def parse_duration(duration_str):
    match = re.match(r"(\d+)([smhd])", duration_str)
    if not match:
        return None
    value, unit = int(match.group(1)), match.group(2)
    return {"s": value, "m": value * 60, "h": value * 3600, "d": value * 86400}[unit]

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "💞 Привет! Я LoveBot by Apachi.\n"
        "Команда /love покажет процент любви 💌\n"
        "Команды /mute и /unmute доступны только создателю бота."
    )

async def mute_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.message.from_user.username != OWNER_USERNAME:
        return await update.message.reply_text("🚫 Только создатель может использовать эту команду.")
    if len(context.args) == 0:
        return await update.message.reply_text("⚠️ Используй: /mute @username [время, напр. 10m]")

    username = context.args[0].replace("@", "")
    duration = None
    if len(context.args) > 1:
        duration = parse_duration(context.args[1])

    unmute_time = time.time() + duration if duration else None
    muted_users[username] = unmute_time

    msg = f"🔇 Пользователь @{username} получил мут"
    if duration:
        msg += f" на {context.args[1]}"
    else:
        msg += " навсегда"
    await update.message.reply_text(msg)

async def unmute_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.message.from_user.username != OWNER_USERNAME:
        return await update.message.reply_text("🚫 Только создатель может использовать эту команду.")
    if len(context.args) == 0:
        return await update.message.reply_text("⚠️ Используй: /unmute @username")

    username = context.args[0].replace("@", "")
    if username in muted_users:
        del muted_users[username]
        await update.message.reply_text(f"🔊 @{username} теперь может писать снова.")
    else:
        await update.message.reply_text(f"ℹ️ @{username} не был в муте.")

async def love_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not bot_active:
        return
    message = update.message
    args = message.text.split(maxsplit=1)
    target = args[1].replace("@", "") if len(args) > 1 else message.from_user.username

    score = random.randint(0, 100)
    phrase = random.choice(SPECIAL_PHRASES if target.lower() == SIGNATURE_USER.lower() else LOVE_PHRASES + LOVE_JOKES)
    category = next((label for (low, high, label) in LOVE_LEVELS if low <= score <= high), "💞")
    emojis = "".join(random.choices(["💖", "✨", "🌹", "💫", "💓", "🌸"], k=3))

    text_to_send = (
        f"💞 Проверяем совместимость между @{message.from_user.username} и @{target}...\n"
        f"🎯 Результат: {score}%\n\n{phrase}\n\nКатегория: {category} {emojis}"
    )
    if target.lower() == SIGNATURE_USER.lower():
        text_to_send += f"\n\n{SIGNATURE_TEXT}"
    await message.reply_text(text_to_send)

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    message = update.message
    if not message or not message.from_user:
        return
    username = message.from_user.username
    if not username:
        return

    if username in muted_users:
        if muted_users[username] and time.time() > muted_users[username]:
            del muted_users[username]
        else:
            try:
                await message.delete()
            except:
                pass
            return

    if message.chat.type in ["group", "supergroup"] and username in TARGET_USERNAMES:
        phrase = random.choice(SPECIAL_PHRASES)
        while last_messages.get(username) == phrase:
            phrase = random.choice(SPECIAL_PHRASES)
        last_messages[username] = phrase
        await message.reply_text(f"{phrase}\n\n{SIGNATURE_TEXT}", reply_to_message_id=message.message_id)

def main():
    app = ApplicationBuilder().token(TELEGRAM_TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("love", love_command))
    app.add_handler(CommandHandler("mute", mute_command))
    app.add_handler(CommandHandler("unmute", unmute_command))
    app.add_handler(MessageHandler(filters.TEXT & (~filters.COMMAND), handle_message))

    print("💘 LoveBot запущен!")
    app.run_polling()

if __name__ == "__main__":
    main()
