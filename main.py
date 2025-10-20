import os
import random
import threading
from http.server import BaseHTTPRequestHandler, HTTPServer
from telegram import Update
from telegram.ext import ApplicationBuilder, MessageHandler, CommandHandler, filters, ContextTypes

# Пользователи
TARGET_USERNAMES = ["Habib471"]  # Романтический пользователь

# Красивые романтические фразы
LOVE_PHRASES = [
    "Ты — лучик света в моём мире, который никогда не угасает 🌅",
    "Когда думаю о тебе, сердце наполняется теплом и радостью 💖",
    "С тобой каждый миг становится маленьким чудом ✨",
    "Твоя улыбка — моя любимая мелодия дня 🎶",
    "Ты словно мягкий ветер, который уносит все тревоги 🌸",
    "В твоих глазах я нахожу покой и вдохновение 🌌",
    "Ты — причина моего счастья и тихой радости 💞",
    "С тобой даже дождливый день становится светлым 🌧️☀️",
    "Ты — нежный свет, который ведёт меня через тьму 🌠",
    "Каждое твоё слово звучит как поэма для моей души 💫",
    "Ты — словно утренний рассвет, который согревает сердце 🌄",
    "С тобой мир кажется ярче, теплее и добрее ☀️",
    "Ты — тайна, которую хочется разгадывать снова и снова 💌",
    "В твоём присутствии растворяются все тревоги и сомнения 🌷",
    "Ты — дыхание счастья, что делает каждый день особенным 💗",
    "Твоя улыбка — это солнце, светящее в моей душе 🌞",
    "С тобой хочется мечтать, творить и просто жить ✨",
    "Ты — гармония в шумном мире, тихая и нежная 🌸",
    "С тобой каждое мгновение — как маленькая вселенная 💫",
    "Ты — радость, которую нельзя описать словами 💕",
    "С тобой даже молчание становится мелодией 🎵",
    "Ты — мягкий свет в холодные дни, тепло в сердце 🌹",
    "Твои глаза — как озёра спокойствия и вдохновения 🌊",
    "Ты — загадка, к которой хочется возвращаться снова и снова 🔮",
    "С тобой всё вокруг наполняется смыслом и красотой 🌺",
    "Ты — вдохновение каждой моей мысли и мечты 🌟",
    "Твоя доброта — как тёплый плед в зимнюю стужу ❄️",
    "Ты — мой маяк, что указывает путь в любой буре ⛵",
    "С тобой хочется смеяться, мечтать и любить бесконечно 💞",
    "Ты — музыка, что звучит в моей душе без слов 🎶",
    "С тобой каждый день похож на сказку, полную чудес ✨",
    "Ты — свет, что согревает сердце даже в ночи 🌙",
    "Твоя улыбка — мой личный источник радости и счастья 🌸",
    "С тобой легко дышать, мечтать и жить настоящим моментом 💗",
    "Ты — словно мягкий дождь весной, что омывает всё вокруг 🌧️",
    "Твои слова — словно нежные прикосновения к душе 💌",
    "Ты — чудо, которое хочется хранить и беречь каждый день 💖",
    "С тобой даже самый обычный день становится волшебным 🌞",
    "Ты — источник вдохновения и тепла для моего сердца ✨",
    "Твоя энергия делает мир ярче и радостнее 🌷",
    "С тобой каждый миг — это маленькое сокровище 💎",
    "Ты — тихая мелодия счастья, которая играет в сердце 🎵",
    "Твоя нежность словно мягкое покрывало в холодный вечер ❄️",
    "С тобой хочется летать, мечтать и смеяться без устали 💫",
    "Ты — гармония и уют в моём мире 🌺",
    "Твои глаза сияют ярче всех звёзд на небе 🌟",
    "С тобой мир становится мягким, тёплым и добрым ☀️",
    "Ты — поэзия, которую хочется читать снова и снова 🌹",
    "С тобой каждая минута — как сладкая мечта 💖",
    "Ты — вдохновение, которое заставляет сердце биться чаще 💗",
    "С тобой жизнь кажется лёгкой, красивой и наполненной смыслом 🌸",
    "Ты — нежность, которую хочется обнимать каждый день 💞",
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
        if username in TARGET_USERNAMES and random.random() < 0.3:  # 30% сообщений
            while True:
                phrase = random.choice(LOVE_PHRASES)
                if last_messages.get(username) != phrase:
                    last_messages[username] = phrase
                    break
        if phrase:
            response = phrase
            if random.random() < 0.3:  # 30% вероятность добавить подпись
                response += f"\n\n{random.choice(SIGNATURES)}"
            await message.reply_text(response, reply_to_message_id=message.message_id)

# Команда /love
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
    token = os.environ.get("TELEGRAM_TOKEN")  # В Render добавь переменную окружения TELEGRAM_TOKEN
    app = ApplicationBuilder().token(token).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("love", love_command))
    app.add_handler(MessageHandler(filters.TEXT & (~filters.COMMAND), handle_message))
    await app.run_polling()

if __name__ == "__main__":
    import asyncio
    asyncio.run(main())
