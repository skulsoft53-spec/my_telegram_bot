import os
import random
import threading
from http.server import BaseHTTPRequestHandler, HTTPServer
from telegram import Update
from telegram.ext import ApplicationBuilder, MessageHandler, CommandHandler, filters, ContextTypes

# Получение токена из переменной окружения
TELEGRAM_TOKEN = os.environ.get("TELEGRAM_TOKEN")

# Пользователи, на которых бот отвечает
TARGET_USERNAMES = ["Habib471"]
SIGNATURE = "Полюби Апачи, как он тебя"

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

# Последнее сообщение для пользователя, чтобы не повторялось
last_messages = {}

# 140 романтических фраз
LOVE_PHRASES = [
# вставь сюда все 140 фраз, как в предыдущем сообщении
]

# Маленькие шутки
LOVE_JOKES = [
"Ты как Wi-Fi — когда тебя рядом, всё работает идеально 😄",
"Ты — моя батарейка, без тебя я теряю заряд ❤️",
"Если бы ты был кофе, я бы никогда не просыпался без тебя ☕",
"Ты как пароль: сложный, но без тебя жизнь невозможна 🔑",
"Ты — моя любимая песня, которую я хочу слушать на повторе 🎶",
"С тобой даже понедельник становится весёлым 😆",
"Ты как солнечный день в дождливую погоду 🌞",
"Ты делаешь мою жизнь как хороший сериал — невозможно оторваться 🎬",
"Ты — моя любимая ошибка, о которой я никогда не пожалел 😍",
"Если бы любовь была кодом, я бы тебя компилировал снова и снова 💻"
]

# /start
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "💞 Привет! Я LoveBot by Apachi.\n"
        "Я отвечаю на сообщения выбранных пользователей 💌\n"
        "Командой /love <имя> можно проверить совместимость!"
    )

# Обработка сообщений
async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    message = update.message
    if not message or not message.from_user:
        return
    username = message.from_user.username
    if message.chat.type in ["group", "supergroup"]:
        if username in TARGET_USERNAMES and random.random() < 0.3:
            if random.random() < 0.2:
                while True:
                    phrase = random.choice(LOVE_JOKES)
                    if last_messages.get(username) != phrase:
                        last_messages[username] = phrase
                        break
            else:
                while True:
                    phrase = random.choice(LOVE_PHRASES)
                    if last_messages.get(username) != phrase:
                        last_messages[username] = phrase
                        break
            response = phrase + f"\n\n{SIGNATURE}"
            await message.reply_text(response, reply_to_message_id=message.message_id)

# Команда /love
async def love_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    message = update.message
    if not message or not message.text:
        return
    args = message.text.split(maxsplit=1)
    target = args[1] if len(args) > 1 else message.from_user.username
    score = random.randint(0, 100)
    await message.reply_text(f"💞 Совместимость с {target}: {score}%")

# Основной запуск бота
async def main():
    if not TELEGRAM_TOKEN:
        raise RuntimeError("❌ Ошибка: переменная окружения TELEGRAM_TOKEN не установлена!")
    app = ApplicationBuilder().token(TELEGRAM_TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("love", love_command))
    app.add_handler(MessageHandler(filters.TEXT & (~filters.COMMAND), handle_message))
    await app.run_polling()

if __name__ == "__main__":
    import asyncio
    asyncio.run(main())
