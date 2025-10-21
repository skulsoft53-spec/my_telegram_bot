import os
import random
import threading
import asyncio
from http.server import BaseHTTPRequestHandler, HTTPServer
from telegram import Update
from telegram.ext import (
    ApplicationBuilder,
    CommandHandler,
    MessageHandler,
    filters,
    ContextTypes
)

# Токен из переменной окружения
TELEGRAM_TOKEN = os.environ.get("TELEGRAM_TOKEN")
if not TELEGRAM_TOKEN:
    raise RuntimeError("Ошибка: переменная окружения TELEGRAM_TOKEN не установлена!")
print("✅ TELEGRAM_TOKEN найден, бот запускается...")

# Настройки
TARGET_USERNAMES = ["Habib471"]
SIGNATURE = "Полюби Апачи, как он тебя"
bot_active = True
last_messages = {}
users_sent_messages = set()

# Списки фраз
LOVE_PHRASES = [
    "Ты — моё вдохновение, дыхание весны 🌸",
    "С тобой каждый день — маленькое чудо ✨",
    "Ты — моя мелодия счастья 🎶",
    "В твоих глазах вижу небо и свет 🌌",
    "Каждое слово твоё — ветерок в душе 🍃",
    "С тобой тишина звучит как музыка 🎵",
    "Ты — дыхание света в сердце 💖",
    "Когда ты рядом, мир мягче 🌈",
    "Ты — утренний луч, озаряющий душу ☀️",
    "С тобой каждый момент — страница сказки 📖",
    # ... добавь остальные фразы
]

LOVE_JOKES = [
    "Ты как Wi-Fi — рядом, и всё идеально 😄",
    "Ты — батарейка, без тебя теряю заряд 🔋",
    "Если бы ты был кофе, не просыпался бы без тебя ☕",
    "Ты как пароль: сложный, но жизнь без тебя невозможна 🔑",
    "Ты — любимая песня на повторе 🎶",
]

# Веб-сервер для Render
def run_web():
    class Handler(BaseHTTPRequestHandler):
        def do_GET(self):
            self.send_response(200)
            self.end_headers()
            self.wfile.write(b"LoveBot is running <3")
    port = int(os.environ.get("PORT", 10000))
    HTTPServer(("0.0.0.0", port), Handler).serve_forever()

threading.Thread(target=run_web, daemon=True).start()

# Команды бота
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

# Команда /love
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
        f"💞 На {score}% вы — как две половинки одного пазла 🧩💓",
        f"💓 Ваши души переплелись на {score}% и вместе создают маленькие чудеса ✨🌸",
        f"🌹 {target} приносит в твою жизнь {score}% счастья и бесконечную нежность 💫",
        f"✨ Вы словно магниты на {score}% притягиваете друг друга 💞💖",
        f"💫 Каждое мгновение с {target} наполняет твою жизнь радостью на {score}% 🌈",
    ]
    story = random.choice(love_stories)

    sent_message = await message.reply_text(f"💌 Совместимость с {target}: 0%\n[{ '□'*10 }]")

    # Анимация прогресса
    for i in range(1, score+1):
        filled = i * bar_length // 100
        bar = "█" * filled + "□" * (bar_length - filled)
        await sent_message.edit_text(f"💌 Совместимость с {target}: {i}%\n[{bar}]")
        await asyncio.sleep(0.02)

    # Анимация текста
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

# Уведомление при старте
async def notify_start(app):
    try:
        updates = await app.bot.get_updates(limit=100)
        chats = set()
        for u in updates:
            if u.message:
                chats.add(u.message.chat.id)
        for chat_id in chats:
            try:
                await app.bot.send_message(chat_id=chat_id, text="💌 LoveBot запущен и онлайн!")
            except:
                pass
        for username in users_sent_messages:
            try:
                user = await app.bot.get_chat(username)
                await user.send_message("💌 LoveBot запущен и онлайн!")
            except:
                pass
    except Exception as e:
        print("Ошибка уведомления при старте:", e)

# Главная функция
async def main():
    app = ApplicationBuilder().token(TELEGRAM_TOKEN).build()
    
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("love", love_command))
    app.add_handler(CommandHandler("on", bot_on))
    app.add_handler(CommandHandler("off", bot_off))
    app.add_handler(MessageHandler(filters.TEXT & (~filters.COMMAND), handle_message))

    await app.initialize()
    await app.start()
    asyncio.create_task(notify_start(app))
    await app.updater.start_polling()
    await app.idle()
    await app.stop()
    await app.shutdown()

if __name__ == "__main__":
    asyncio.run(main())
