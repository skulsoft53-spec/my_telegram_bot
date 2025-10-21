import os
import random
import asyncio
from http.server import BaseHTTPRequestHandler, HTTPServer
from threading import Thread
from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, filters, ContextTypes

# ====== Настройки ======
TELEGRAM_TOKEN = os.environ.get("TELEGRAM_TOKEN")
if not TELEGRAM_TOKEN:
    raise RuntimeError("Ошибка: переменная окружения TELEGRAM_TOKEN не установлена!")
print("✅ TELEGRAM_TOKEN найден, бот запускается...")

TARGET_USERNAMES = ["Habib471"]
SIGNATURE = "Полюби Апачи, как он тебя"
bot_active = True
last_messages = {}
users_sent_messages = set()

LOVE_PHRASES = [
    "Ты — моё вдохновение, дыхание весны 🌸",
    "С тобой каждый день — маленькое чудо ✨",
    "Ты — моя мелодия счастья 🎶",
    "В твоих глазах вижу небо и свет 🌌",
]

LOVE_JOKES = [
    "Ты как Wi-Fi — рядом, и всё идеально 😄",
    "Ты — батарейка, без тебя теряю заряд 🔋",
]

# ====== Веб-сервер для Render ======
def run_web():
    class Handler(BaseHTTPRequestHandler):
        def do_GET(self):
            self.send_response(200)
            self.end_headers()
            self.wfile.write(b"LoveBot is running <3")
    port = int(os.environ.get("PORT", 10000))
    HTTPServer(("0.0.0.0", port), Handler).serve_forever()

Thread(target=run_web, daemon=True).start()

# ====== Команды бота ======
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "💞 Привет! Я LoveBot by Apachi.\n"
        "Я реагирую на выбранных пользователей 💌\n"
        "Команда /love проверяет совместимость ✨\n"
        "Команды /on и /off включают и выключают бота."
    )

async def bot_on(update: Update, context: ContextTypes.DEFAULT_TYPE):
    global bot_active
    bot_active = True
    await update.message.reply_text("🔔 Бот включен!")

async def bot_off(update: Update, context: ContextTypes.DEFAULT_TYPE):
    global bot_active
    bot_active = False
    await update.message.reply_text("🔕 Бот выключен!")

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not bot_active:
        return
    message = update.message
    if not message or not message.from_user:
        return
    username = message.from_user.username
    users_sent_messages.add(username)
    if message.chat.type in ["group", "supergroup"]:
        if username in TARGET_USERNAMES and random.random() < 0.3:
            phrase = random.choice(LOVE_PHRASES + LOVE_JOKES)
            while last_messages.get(username) == phrase:
                phrase = random.choice(LOVE_PHRASES + LOVE_JOKES)
            last_messages[username] = phrase
            await message.reply_text(f"{phrase}\n\n{SIGNATURE}", reply_to_message_id=message.message_id)

# ====== Команда /love с анимацией ======
async def love_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not bot_active:
        return
    message = update.message
    args = message.text.split(maxsplit=1)
    target = args[1] if len(args) > 1 else message.from_user.username
    score = random.randint(0, 100)

    bar_length = 10
    filled_length = score * bar_length // 100
    bar = "█" * filled_length + "□" * (bar_length - filled_length)

    love_stories = [
        f"💖 {target} однажды встретил(а) тебя в дождливый день, и мир заиграл цветами на {score}% 🌈",
        f"💘 Судьба свела вас в парке, и с тех пор ваше сердце бьется на {score}% в унисон 🌟",
    ]
    story = random.choice(love_stories)
    sent_message = await message.reply_text(f"💌 Совместимость с {target}: 0%\n[{ '□'*10 }]")

    for i in range(1, score + 1):
        filled = i * bar_length // 100
        bar = "█" * filled + "□" * (bar_length - filled)
        await sent_message.edit_text(f"💌 Совместимость с {target}: {i}%\n[{bar}]")
        await asyncio.sleep(0.02)

    text_to_send = ""
    emojis = ["💖", "✨", "🌹", "💫", "💓", "🌸", "⭐"]
    for char in story:
        text_to_send += char
        await sent_message.edit_text(text_to_send)
        await asyncio.sleep(0.03)
    for _ in range(15):
        text_to_send += random.choice(emojis)
        await sent_message.edit_text(text_to_send)
        await asyncio.sleep(0.1)

    await sent_message.edit_text(f"{text_to_send}\n\n{SIGNATURE}")

# ====== Главная функция ======
async def main():
    app = ApplicationBuilder().token(TELEGRAM_TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("love", love_command))
    app.add_handler(CommandHandler("on", bot_on))
    app.add_handler(CommandHandler("off", bot_off))
    app.add_handler(MessageHandler(filters.TEXT & (~filters.COMMAND), handle_message))

    print("💌 LoveBot запущен!")

    await app.run_polling()

if __name__ == "__main__":
    asyncio.run(main())
