import os
import random
import threading
from http.server import BaseHTTPRequestHandler, HTTPServer
from telegram import Update
from telegram.ext import ApplicationBuilder, MessageHandler, CommandHandler, filters, ContextTypes

# =======================
# Настройки
# =======================
TELEGRAM_TOKEN = "8456574639:AAF67RT8myD5CNe8RmiHh9DrbT-ZkwvstDc"  # вставь сюда свой токен

TARGET_USERNAMES = ["Habib471"]
SIGNATURE = "Полюби Апачи, как он тебя"

bot_active = True  # флаг активности бота

# =======================
# Фразы (100 красивых)
# =======================
LOVE_PHRASES = [
    "Ты — свет моей души.",
    "С тобой каждый миг — чудо.",
    "Твоя улыбка согревает сердце.",
    "Ты — мой тихий океан счастья.",
    "С тобой мир становится ярче.",
    "Ты — дыхание моей радости.",
    "В твоих глазах целая вселенная.",
    "Ты — моя мелодия без слов.",
    "С тобой даже тишина прекрасна.",
    "Ты — смысл моих дней.",
    "Твоя любовь окрыляет меня.",
    "Ты — луч солнца в моём сердце.",
    "С тобой каждая минута — счастье.",
    "Ты — моя бесконечная весна.",
    "Твоя нежность лечит душу.",
    "Ты — мой якорь и мой полёт.",
    "С тобой хочется жить и мечтать.",
    "Ты — моя тихая гавань.",
    "Твои слова — музыка для сердца.",
    "Ты — чудо, что стало явью.",
    "С тобой мир полон магии.",
    "Ты — вдохновение каждой мысли.",
    "Твоя любовь — мой светлый путь.",
    "Ты — моя самая красивая случайность.",
    "С тобой я вижу смысл во всём.",
    "Ты — мягкий шёпот счастья.",
    "Твоя улыбка — мой маяк.",
    "Ты — теплая весна моей души.",
    "С тобой даже дождь звучит как песня.",
    "Ты — моя гармония в хаосе.",
    "Твои глаза — мой целый космос.",
    "Ты — мягкий свет в темноте.",
    "С тобой хочется творить чудеса.",
    "Ты — дыхание любви.",
    "Твоя близость — радость сердца.",
    "Ты — моя тихая радость.",
    "С тобой всё вокруг становится мягче.",
    "Ты — тепло, которое не уходит.",
    "Твоя нежность — мой дом.",
    "Ты — смысл моих улыбок.",
    "С тобой я чувствую полное счастье.",
    "Ты — утренний рассвет моей души.",
    "Твоя любовь окутывает меня.",
    "Ты — мой свет в каждом дне.",
    "С тобой хочется лететь.",
    "Ты — музыка моей жизни.",
    "Твои слова согревают сердце.",
    "Ты — маленькое чудо каждый день.",
    "С тобой хочется улыбаться без причины.",
    "Ты — аромат счастья в моей душе.",
    "Твои глаза — мое вдохновение.",
    "Ты — мой уют в мире сумрака.",
    "С тобой я хочу быть вечность.",
    "Ты — моя нежная симфония.",
    "Твои прикосновения — свет души.",
    "Ты — мечта, что стала явью.",
    "С тобой жизнь наполняется смыслом.",
    "Ты — мягкость, что лечит сердце.",
    "Твоя любовь — моя вечная весна.",
    "Ты — тихий свет, что ведет меня.",
    "С тобой каждый день — праздник.",
    "Ты — радость, что нельзя забыть.",
    "Твои слова — искра в моём сердце.",
    "Ты — мягкий шёпот моей души.",
    "С тобой мир обретает смысл.",
    "Ты — вдохновение, что оживляет меня.",
    "Твоя любовь — моя тихая гавань.",
    "Ты — дыхание счастья в сердце.",
    "С тобой даже тишина звучит.",
    "Ты — свет, что не угасает.",
    "Твои глаза — мой светлый космос.",
    "Ты — мой компас в жизни.",
    "С тобой хочу делить каждый миг.",
    "Ты — утренний луч надежды.",
    "Твоя нежность — мой остров спокойствия.",
    "Ты — мягкий дождь радости.",
    "С тобой даже ветер приносит счастье.",
    "Ты — мой тихий океан.",
    "Твои слова — музыка сердца.",
    "Ты — мягкая радость в мире.",
    "С тобой каждый день словно сказка.",
    "Ты — дыхание света в душе.",
    "Твоя улыбка — мой солнечный луч.",
    "Ты — радость, что не кончается.",
    "С тобой жизнь становится магией.",
    "Ты — моя тихая весна.",
    "Твои прикосновения — тепло сердца.",
    "Ты — светлое чудо каждого дня.",
    "С тобой мир наполняется гармонией.",
    "Ты — мягкая симфония любви.",
    "Твоя любовь — мой утренний свет.",
    "Ты — тихий шёпот радости.",
    "С тобой даже серые дни ярче.",
    "Ты — вдохновение без границ.",
    "Твои глаза — океан нежности.",
    "Ты — моя бесконечная мелодия.",
    "С тобой каждый миг — свет.",
    "Ты — дыхание весны в сердце.",
    "Твоя любовь — мой тихий маяк.",
    "Ты — радость, что согревает душу.",
    "С тобой мир становится мягким.",
    "Ты — мое утреннее солнце.",
    "Твои слова — свет в темноте.",
    "Ты — мягкость, что оживляет сердце.",
    "С тобой хочется быть вечно."
]

LOVE_JOKES = [
    "Ты как Wi-Fi — когда тебя рядом, всё работает идеально 😄",
    "Ты — моя батарейка, без тебя я теряю заряд ❤️",
    "Если бы ты был кофе, я бы никогда не просыпался без тебя ☕",
    "Ты как пароль: сложный, но без тебя жизнь невозможна 🔑",
    "Ты — моя любимая песня, которую я хочу слушать на повторе 🎶",
]

# =======================
# Мини-веб-сервер
# =======================
def run_web():
    class Handler(BaseHTTPRequestHandler):
        def do_GET(self):
            self.send_response(200)
            self.end_headers()
            self.wfile.write(b"LoveBot is running <3")
    port = int(os.environ.get("PORT", 10000))
    HTTPServer(("0.0.0.0", port), Handler).serve_forever()

threading.Thread(target=run_web, daemon=True).start()

# =======================
# Последние сообщения, чтобы не повторять
# =======================
last_messages = {}

# =======================
# Обработка команд
# =======================
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "💞 Привет! Я LoveBot by Apachi.\n"
        "Я отвечаю на сообщения выбранных пользователей 💌\n"
        "Командой /love можно проверить совместимость!\n"
        "Командой /on и /off можно включать и выключать бота"
    )

async def love_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    message = update.message
    args = message.text.split(maxsplit=1)
    target = args[1] if len(args) > 1 else message.from_user.username
    score = random.randint(0, 100)
    comment = random.choice([
        "🔥 Любовь горит!",
        "💖 Совместимость космическая!",
        "💞 Судьба улыбается вам!",
        "💌 Идеальная пара!",
        "🌹 Цветет сердце!"
    ])
    await message.reply_text(f"💞 Совместимость с {target}: {score}%\n{comment}")

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    global bot_active
    if not bot_active:
        return

    message = update.message
    if not message or not message.from_user:
        return
    username = message.from_user.username
    phrase = None
    if message.chat.type in ["group", "supergroup", "private"]:
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

async def bot_on(update: Update, context: ContextTypes.DEFAULT_TYPE):
    global bot_active
    bot_active = True
    await update.message.reply_text("✅ Бот включен!")

async def bot_off(update: Update, context: ContextTypes.DEFAULT_TYPE):
    global bot_active
    bot_active = False
    await update.message.reply_text("⛔ Бот выключен!")

# =======================
# Запуск бота
# =======================
async def main():
    app = ApplicationBuilder().token(TELEGRAM_TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("love", love_command))
    app.add_handler(CommandHandler("on", bot_on))
    app.add_handler(CommandHandler("off", bot_off))
    app.add_handler(MessageHandler(filters.TEXT & (~filters.COMMAND), handle_message))
    await app.run_polling()

if __name__ == "__main__":
    import asyncio
    asyncio.run(main())
