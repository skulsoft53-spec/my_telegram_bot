import os
import random
import threading
from http.server import BaseHTTPRequestHandler, HTTPServer
from telegram import Update
from telegram.ext import ApplicationBuilder, MessageHandler, CommandHandler, filters, ContextTypes

# Пользователи, для которых будут романтические ответы
TARGET_USERNAMES = ["Habib471"]  

# Красивые романтические фразы 💞
LOVE_PHRASES = [
    "Ты — моё вдохновение, нежное как дыхание весны 🌷",
    "С тобой всё вокруг наполняется смыслом 💫",
    "Ты — моя мелодия счастья, тихая и вечная 🎶",
    "В каждом луче солнца я вижу твой свет ☀️",
    "Ты — шёпот нежности в шуме мира 🌸",
    "Каждая мысль о тебе — как утренний рассвет 🌅",
    "С тобой даже тишина звучит прекраснее 💞",
    "Ты — дыхание света в моём сердце ✨",
    "В твоих глазах спрятано небо и тепло 🌌",
    "Ты — мечта, которая стала реальностью 💗",
    "С тобой даже ветер дышит любовью 🌬️",
    "Ты — причина улыбаться без причины 💕",
    "Твоё имя звучит как нежная песня 💖",
    "Ты — светлая мысль во всех моих днях 🌤️",
    "Когда ты рядом, всё остальное теряет значение 🌺",
    "Ты — мой дом, где покой и тепло 🕊️",
    "Каждая встреча с тобой — маленькое чудо ✨",
    "Ты — утренний луч в моём сердце 🌞",
    "С тобой даже звёзды сияют ярче 🌟",
    "Ты — капля любви в океане жизни 💧",
    "Ты — вдох, без которого не дышу 💫",
    "Ты — отклик сердца на зов любви 💌",
    "Ты — нежный огонь в холодном мире 🔥",
    "Ты — моя самая красивая случайность 💫",
    "Ты — свет в каждом взгляде 💖",
    "Ты — утро, которое не хочется отпускать 🌅",
    "Ты — причина моего вдоха и улыбки 💞",
    "Ты — мягкость в этом мире 💖",
    "Ты — музыка в моих мыслях 🎶",
    "Ты — счастье, что стало реальностью 💞",
    "С тобой мир светлее и радостнее ☀️",
]

# Подписи к романтическим сообщениям
SIGNATURES = [
    "Апачи тебя любит ❤️",
    "Ты в сердце Апачи навсегда 💗",
    "Полюби Апачи, как он тебя 🌙",
    "От Апачи с теплом 💌",
]

# Мини-веб-сервер для Render/Heroku
def run_web():
    class Handler(BaseHTTPRequestHandler):
        def do_GET(self):
            self.send_response(200)
            self.end_headers()
            self.wfile.write(b"LoveBot is running <3")
    port = int(os.environ.get("PORT", 10000))
    HTTPServer(("0.0.0.0", port), Handler).serve_forever()

threading.Thread(target=run_web, daemon=True).start()

# Последнее сообщение для каждого пользователя, чтобы не повторялось
last_messages = {}

# /start
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "💞 Привет! Я LoveBot by Apachi.\n"
        "Я отвечаю на сообщения выбранных пользователей 💌\n"
        "Командой /love можно проверить совместимость!"
    )

# Обработка сообщений
async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    message = update.message
    if not message or not message.from_user:
        return
    username = message.from_user.username
    phrase = None
    if message.chat.type in ["group", "supergroup"]:
        # Только романтический пользователь
        if username in TARGET_USERNAMES and random.random() < 0.3:  # 30% вероятность ответа
            while True:
                phrase = random.choice(LOVE_PHRASES)
                if last_messages.get(username) != phrase:
                    last_messages[username] = phrase
                    break
        if phrase:
            response = phrase
            # Подпись к романтическим сообщениям с вероятностью 30%
            if username in TARGET_USERNAMES and random.random() < 0.3:
                response += f"\n\n{random.choice(SIGNATURES)}"
            await message.reply_text(response, reply_to_message_id=message.message_id)

# Команда /love для всех пользователей
async def love_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    message = update.message
    if not message or not message.text:
        return
    args = message.text.split(maxsplit=1)
    target = args[1] if len(args) > 1 else message.from_user.username
    score = random.randint(50, 100)
    await message.reply_text(f"💞 Совместимость с {target}: {score}%")

# Запуск бота
async def main():
    token = "8456574639:AAF67RT8myD5CNe8RmiHh9DrbT-ZkwvstDc"  # Вставлен напрямую
    app = ApplicationBuilder().token(token).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("love", love_command))
    app.add_handler(MessageHandler(filters.TEXT & (~filters.COMMAND), handle_message))
    await app.run_polling()

if __name__ == "__main__":
    import asyncio
    asyncio.run(main())
